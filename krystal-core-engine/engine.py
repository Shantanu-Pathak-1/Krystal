"""
Krystal core engine: wires KeyManager, PluginManager, LLMProcessor,
and the main input loop. Agentic routing uses XML tags for safety.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import re
import json
import requests
import os
from openai import OpenAI

_ENGINE_DIR = Path(__file__).resolve().parent

def _load_sibling_module(unique_name: str, filename: str):
    path = _ENGINE_DIR / filename
    spec = importlib.util.spec_from_file_location(unique_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[unique_name] = module          # ← YEH LINE ADD
    spec.loader.exec_module(module)
    return module

_api_router = _load_sibling_module("krystal_engine._api_router", "api_router.py")
_plugin_manager_mod = _load_sibling_module("krystal_engine._plugin_manager", "plugin_manager.py")
_llm_mod = _load_sibling_module("krystal_engine._llm_processor", "llm_processor.py")
_db_manager_mod = _load_sibling_module("krystal_engine._db_manager", "db_manager.py")
_voice_out_mod = _load_sibling_module("krystal_engine._voice_out", "voice_out.py")
_vector_memory_mod = _load_sibling_module("krystal_engine._vector_memory", "vector_memory.py")

# Import usage tracker
try:
    _usage_tracker_mod = _load_sibling_module("krystal_engine._usage_tracker", "usage_tracker.py")
    track_api_call = _usage_tracker_mod.track_api_call
except ImportError as e:
    print(f"Warning: Usage tracker not available: {e}")
    track_api_call = lambda provider: None  # Fallback no-op

KeyManager = _api_router.KeyManager
PluginManager = _plugin_manager_mod.PluginManager
LLMProcessor = _llm_mod.LLMProcessor
MongoManager = _db_manager_mod.MongoManager
speak_text = _voice_out_mod.speak_text
initialize_voice = _voice_out_mod.initialize_voice
initialize_pinecone = _vector_memory_mod.initialize_pinecone
store_memory = _vector_memory_mod.store_memory
recall_memory = _vector_memory_mod.recall_memory


class MultiModelRouter:
    """Intelligent multi-model routing system for Krystal's LLM brain."""
    
    def __init__(self):
        self.model_config = self._load_model_config()
        self.current_model = None
        self.last_model = None
        
    def _load_model_config(self) -> Dict[str, Any]:
        """Load model configuration from environment variables."""
        return {
            # Groq (Llama 3.3) - Primary Provider
            'groq': {
                'models': ['llama-3.3-70b-versatile', 'llama-3.1-70b-versatile', 'mixtral-8x7b-32768'],
                'api_key': os.environ.get('GROQ_KEY_1'),
                'base_url': 'https://api.groq.com/openai/v1',
                'priority': 1,
                'openai_compatible': True,
                'waterfall_order': 1  # First in waterfall chain
            },
            
            # SambaNova - Waterfall #2
            'sambanova': {
                'models': ['Meta-Llama-3.1-70B-Instruct', 'Meta-Llama-3.1-8B-Instruct', 'Meta-Llama-3.1-405B-Instruct'],
                'api_key': os.environ.get('SAMBA_NOVA_API_KEY'),
                'base_url': 'https://api.sambanova.ai/v1',
                'priority': 2,
                'openai_compatible': True,
                'waterfall_order': 2
            },
            
            # Together AI - Waterfall #3
            'together': {
                'models': ['meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo', 'meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo', 'Qwen/Qwen2.5-72B-Instruct-Turbo'],
                'api_key': os.environ.get('TOGETHER_API_KEY'),
                'base_url': 'https://api.together.xyz/v1',
                'priority': 3,
                'openai_compatible': True,
                'waterfall_order': 3
            },
            
            # OpenRouter - Waterfall #4
            'openrouter': {
                'models': ['meta-llama/llama-3.1-70b-instruct', 'meta-llama/llama-3.1-8b-instruct', 'qwen/qwen-2.5-72b-instruct'],
                'api_key': os.environ.get('OPENROUTER_API_KEY'),
                'base_url': 'https://openrouter.ai/api/v1',
                'priority': 4,
                'openai_compatible': True,
                'waterfall_order': 4
            },
            
            # Fireworks AI - Waterfall #5
            'fireworks': {
                'models': ['accounts/fireworks/models/llama-v3p1-70b-instruct', 'accounts/fireworks/models/llama-v3p1-8b-instruct', 'accounts/fireworks/models/qwen2p5-72b-instruct'],
                'api_key': os.environ.get('FIREWORKS_API_KEY'),
                'base_url': 'https://api.fireworks.ai/inference/v1',
                'priority': 5,
                'openai_compatible': True,
                'waterfall_order': 5
            },
            
            # Google Gemini - Specialized for multimodal
            'gemini': {
                'models': ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro'],
                'api_key': os.environ.get('GEMINI_KEY_1'),
                'base_url': 'https://generativelanguage.googleapis.com/v1beta',
                'priority': 6,
                'openai_compatible': False,
                'specializes': ['files', 'images', 'multimodal']
            },
            
            # HuggingFace - Specialized models
            'huggingface': {
                'models': ['meta-llama/Llama-3.1-70B-Instruct', 'Qwen/Qwen2.5-72B-Instruct', 'mistralai/Mixtral-8x7B-Instruct-v0.1'],
                'api_key': os.environ.get('HUGGINGFACE_API_KEY'),
                'base_url': 'https://api-inference.huggingface.co/models',
                'priority': 7,
                'openai_compatible': False,
                'specializes': ['transformers', 'specific_models']
            },
            
            # Ollama (Local) - Last Resort
            'ollama': {
                'models': ['deepseek-r1:32b', 'qwen2.5-coder:32b', 'llama3.3:70b', 'qwen2.5:32b'],
                'base_url': os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434'),
                'priority': 8,  # Last in waterfall
                'openai_compatible': False,
                'offline_only': True,
                'reasoning_models': ['deepseek-r1:32b'],
                'waterfall_order': 6  # Last resort
            }
        }
    
    def _detect_task_type(self, user_text: str, context: Dict[str, Any] = None) -> str:
        """Detect the type of task to route to appropriate model."""
        text_lower = user_text.lower()
        
        # File/image upload detection
        if context and context.get('has_file') or context.get('has_image'):
            return 'multimodal'
        
        # Coding-heavy task detection
        coding_keywords = [
            'code', 'function', 'class', 'algorithm', 'debug', 'implement',
            'programming', 'script', 'develop', 'refactor', 'optimize code',
            'write a function', 'create a class', 'fix this code'
        ]
        if any(keyword in text_lower for keyword in coding_keywords):
            return 'coding'
        
        # Mathematical/analytical tasks
        math_keywords = ['calculate', 'solve', 'math', 'equation', 'formula', 'statistics']
        if any(keyword in text_lower for keyword in math_keywords):
            return 'analytical'
        
        # Creative/writing tasks
        creative_keywords = ['write', 'story', 'poem', 'creative', 'brainstorm', 'design']
        if any(keyword in text_lower for keyword in creative_keywords):
            return 'creative'
        
        return 'general'
    
    def _check_internet_connectivity(self) -> bool:
        """Check if internet is available."""
        try:
            response = requests.get('https://www.google.com', timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def get_best_model(self, task_type: str = 'general', is_offline: bool = False, 
                     agent_mode: str = "Agentic", context: Dict[str, Any] = None) -> Tuple[str, str]:
        """
        Get the best model for the given task and conditions.
        
        Returns:
            Tuple of (provider, model_name)
        """
        # Check offline status
        if is_offline or not self._check_internet_connectivity():
            return self._get_offline_model(agent_mode)
        
        # Task-specific routing
        if task_type == 'multimodal':
            return self._get_multimodal_model()
        
        if task_type == 'coding':
            return self._get_coding_model()
        
        if task_type == 'analytical':
            return self._get_analytical_model()
        
        # God Mode prioritizes reasoning models
        if agent_mode == "God Mode":
            return self._get_reasoning_model()
        
        # Default: fastest available model
        return self._get_default_model()
    
    def _get_offline_model(self, agent_mode: str) -> Tuple[str, str]:
        """Get best offline model (Ollama)."""
        ollama_config = self.model_config.get('ollama', {})
        models = ollama_config.get('models', [])
        
        if agent_mode == "God Mode" and 'deepseek-r1:32b' in models:
            return ('ollama', 'deepseek-r1:32b')
        elif 'qwen2.5-coder:32b' in models:
            return ('ollama', 'qwen2.5-coder:32b')
        elif models:
            return ('ollama', models[0])
        
        # Fallback to online models if Ollama unavailable
        return self._get_default_model()
    
    def _get_multimodal_model(self) -> Tuple[str, str]:
        """Get best model for multimodal tasks (files/images)."""
        gemini_config = self.model_config.get('gemini', {})
        if gemini_config.get('api_key'):
            models = gemini_config.get('models', [])
            return ('gemini', models[0] if models else 'gemini-1.5-pro')
        
        # Fallback to other models
        return self._get_default_model()
    
    def _get_coding_model(self) -> Tuple[str, str]:
        """Get best model for coding tasks."""
        # Try Ollama first for local coding
        ollama_config = self.model_config.get('ollama', {})
        if 'qwen2.5-coder:32b' in ollama_config.get('models', []):
            return ('ollama', 'qwen2.5-coder:32b')
        
        # Try Groq Llama 3.3
        groq_config = self.model_config.get('groq', {})
        if groq_config.get('api_key'):
            return ('groq', 'llama-3.3-70b-versatile')
        
        # Fallback to GLM
        glm_config = self.model_config.get('glm', {})
        if glm_config.get('api_key'):
            return ('glm', 'glm-4-flash')
        
        return self._get_default_model()
    
    def _get_analytical_model(self) -> Tuple[str, str]:
        """Get best model for analytical tasks."""
        # Prioritize Groq for speed
        groq_config = self.model_config.get('groq', {})
        if groq_config.get('api_key'):
            return ('groq', 'llama-3.3-70b-versatile')
        
        # Try Gemini
        gemini_config = self.model_config.get('gemini', {})
        if gemini_config.get('api_key'):
            return ('gemini', 'gemini-1.5-pro')
        
        return self._get_default_model()
    
    def _get_reasoning_model(self) -> Tuple[str, str]:
        """Get best reasoning model for God Mode."""
        # Try DeepSeek-R1 from Ollama
        ollama_config = self.model_config.get('ollama', {})
        if 'deepseek-r1:32b' in ollama_config.get('models', []):
            return ('ollama', 'deepseek-r1:32b')
        
        # Try Gemini Pro
        gemini_config = self.model_config.get('gemini', {})
        if gemini_config.get('api_key'):
            return ('gemini', 'gemini-1.5-pro')
        
        # Try Groq Llama 3.3
        groq_config = self.model_config.get('groq', {})
        if groq_config.get('api_key'):
            return ('groq', 'llama-3.3-70b-versatile')
        
        return self._get_default_model()
    
    def _get_default_model(self) -> Tuple[str, str]:
        """Get default model (prioritizes speed and availability)."""
        # Try Groq first (fastest)
        groq_config = self.model_config.get('groq', {})
        if groq_config.get('api_key'):
            return ('groq', 'llama-3.3-70b-versatile')
        
        # Try Gemini
        gemini_config = self.model_config.get('gemini', {})
        if gemini_config.get('api_key'):
            return ('gemini', 'gemini-1.5-flash')
        
        # Try GLM
        glm_config = self.model_config.get('glm', {})
        if glm_config.get('api_key'):
            return ('glm', 'glm-4-flash')
        
        # Last resort: try Ollama
        ollama_config = self.model_config.get('ollama', {})
        if ollama_config.get('models'):
            return ('ollama', ollama_config['models'][0])
        
        # No models available
        return ('none', 'none')
    
    def get_waterfall_chain(self, task_type: str = 'general') -> list:
        """Get the waterfall fallback chain for general tasks."""
        # Waterfall chain: Groq -> SambaNova -> Together AI -> OpenRouter -> Fireworks -> Ollama
        waterfall_providers = ['groq', 'sambanova', 'together', 'openrouter', 'fireworks']
        
        # Add Ollama as last resort
        if self._check_internet_connectivity():
            waterfall_providers.append('ollama')
        else:
            # If offline, start with Ollama
            waterfall_providers = ['ollama'] + waterfall_providers
        
        return waterfall_providers
    
    def handle_rate_limit_fallback(self, failed_provider: str) -> Tuple[str, str]:
        """Handle rate limit by falling back to alternative provider using waterfall chain."""
        waterfall_chain = self.get_waterfall_chain()
        
        # Find the failed provider in the chain
        try:
            failed_index = waterfall_chain.index(failed_provider)
        except ValueError:
            # If not in waterfall chain, use default fallback
            return self._get_default_model()
        
        # Try the next providers in the waterfall chain
        for provider in waterfall_chain[failed_index + 1:]:
            provider_config = self.model_config.get(provider, {})
            if provider_config.get('api_key') or provider == 'ollama':
                models = provider_config.get('models', [])
                if models:
                    return (provider, models[0])
        
        return self._get_default_model()
    
    def _create_openai_client(self, provider: str) -> Optional[OpenAI]:
        """Create OpenAI client for compatible providers."""
        config = self.model_config.get(provider, {})
        
        if not config.get('openai_compatible', False):
            return None
        
        api_key = config.get('api_key')
        base_url = config.get('base_url')
        
        if not api_key:
            return None
        
        try:
            client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=30.0
            )
            return client
        except Exception as e:
            print(f"Failed to create {provider} client: {e}")
            return None


class KrystalEngine:
    def __init__(
        self,
        env_path: str | Path | None = None,
        plugins_dir: str | Path | None = None,
    ) -> None:
        root = Path(__file__).resolve().parent.parent
        resolved_env = Path(env_path) if env_path is not None else root / ".env"
        self.keys = KeyManager(env_path=resolved_env if resolved_env.exists() else None)
        self.plugins = PluginManager(plugins_dir=plugins_dir)
        self.llm = LLMProcessor(self.keys)
        self.db = MongoManager()
        
        # Initialize Multi-Model Router
        self.model_router = MultiModelRouter()
        
        initialize_voice()
        # Initialize Pinecone with API key from environment
        import os
        pinecone_key = os.environ.get('PINECONE_API_KEY')
        self.vector_store = initialize_pinecone(api_key=pinecone_key)

    def process_input(self, user_text: str, agent_mode: str = "Agentic", history: list = None, **plugin_kwargs: Any) -> str:
        if user_text.startswith('/'):
            return self._handle_direct_command(user_text, **plugin_kwargs)
        
        # Safe Mode: Bypass all agentic routing, force chat only
        if agent_mode == "Safe":
            return self._handle_conversation(user_text, history=history, agent_mode=agent_mode, **plugin_kwargs)
        
        # Use provided history or fetch from DB as fallback
        chat_history = history if history else []
        
        # Detect task type for intelligent routing
        task_type = self.model_router._detect_task_type(user_text, plugin_kwargs)
        
        # Get best model based on task, mode, and conditions
        provider, model_name = self.model_router.get_best_model(
            task_type=task_type,
            agent_mode=agent_mode,
            context=plugin_kwargs
        )
        
        # Format history for context injection
        history_context = self._format_history_context(chat_history)
        
        # Add additional DB history if available
        if not chat_history and hasattr(self.db, 'is_connected') and self.db.is_connected:
            try:
                db_logs = self.db.get_recent_logs(limit=5)
                if db_logs:
                    db_history = []
                    for log in reversed(db_logs):
                        if log.get('user_input'):
                            db_history.append({"role": "user", "content": log.get('user_input', '')})
                        if log.get('response'):
                            db_history.append({"role": "assistant", "content": log.get('response', '')})
                    history_context = self._format_history_context(db_history)
            except:
                pass
        
        routing_decision = self._agentic_route(user_text, history_context)
        
        if routing_decision != "CHAT":
            return self._handle_direct_command(routing_decision, **plugin_kwargs)
        
        return self._handle_conversation(user_text, history=chat_history, agent_mode=agent_mode, 
                                      provider=provider, model_name=model_name, **plugin_kwargs)

    def _format_history_context(self, history: list) -> str:
        """Format chat history into a context string for the LLM."""
        if not history:
            return ""
        
        context_lines = ["\n=== CONVERSATION HISTORY ==="]
        for msg in history[-10:]:  # Last 10 messages for routing context
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if role == 'user':
                context_lines.append(f"User: {content}")
            elif role == 'assistant':
                # Truncate long responses for context
                display_content = content[:200] + "..." if len(content) > 200 else content
                context_lines.append(f"Krystal: {display_content}")
        
        context_lines.append("=== CURRENT TURN ===\n")
        return "\n".join(context_lines)

    def _agentic_route(self, user_text: str, history_context: str = "") -> str:
        plugin_descriptions = self._get_plugin_descriptions()
        
        # INTENT-BASED ROUTING: LLM must parse intent before triggering tools
        system_override = """YOU ARE KRYSTAL, AN AUTONOMOUS AI AGENT WITH OS CONTROL.

YOU CAN EXECUTE ACTIONS:
- Play media on YouTube
- Open websites and applications
- Control media playback (play/pause/next/previous)
- Lock the screen

CRITICAL INTENT PARSING RULES:
1. ONLY trigger tools when the user EXPLICITLY requests an action
2. If the user asks "Who told you to play a song?" or "Why did you do that?" → This is CONVERSATIONAL → Return CHAT
3. If the user says "play" but doesn't specify what → Ask for clarification → Return CHAT
4. If the user says "Play Agar Tum Sath Ho" → This is an EXPLICIT action request → Return <cmd>/os play Agar Tum Sath Ho</cmd>
5. If the user asks "What song is playing?" → This is CONVERSATIONAL → Return CHAT

DISTINGUISH BETWEEN:
- ACTION REQUEST: "Play X", "Open Y", "Pause music" → Execute command
- CONVERSATIONAL: "Who told you", "Why did you", "What is X", "How does Y work" → Return CHAT

Your job is to determine INTENT, not blindly trigger tools on keywords."""

        routing_prompt = f"""{system_override}

Available plugins:
{plugin_descriptions}

{history_context}

User input: {user_text}

INSTRUCTIONS:
1. Analyze the user's INTENT - are they requesting an action or asking a question?
2. If it's a conversational question about past actions or explanations → Return <cmd>CHAT</cmd>
3. If it's an explicit action request with all required parameters → Return the exact command
4. If it's an action request but missing parameters (e.g., "play" without song name) → Return <cmd>CHAT</cmd> so you can ask for clarification

Your FINAL output MUST be wrapped EXACTLY inside <cmd> and </cmd> XML tags.
Do NOT output any text after the closing </cmd> tag.

COMMAND FORMAT:
- Play song: <cmd>/os play [exact song name]</cmd>
- Open site/app: <cmd>/os open [exact target]</cmd>
- Pause: <cmd>/os pause</cmd>
- Next track: <cmd>/os next</cmd>
- Previous track: <cmd>/os previous</cmd>
- Lock screen: <cmd>/os lock</cmd>
- Conversational/Question: <cmd>CHAT</cmd>

EXAMPLES:
User: "Play Agar Tum Sath Ho" → <cmd>/os play Agar Tum Sath Ho</cmd>
User: "Open YouTube" → <cmd>/os open youtube</cmd>
User: "Who told you to play a song?" → <cmd>CHAT</cmd>
User: "What song is this?" → <cmd>CHAT</cmd>
User: "Play" → <cmd>CHAT</cmd> (ask "What would you like me to play?")
User: "Why did you open YouTube?" → <cmd>CHAT</cmd>

OUTPUT ONLY THE <cmd> TAG. NO APOLOGIES. NO EXCUSES."""
        try:
            decision = self.llm.generate_response(routing_prompt).strip()
            
            # Extract content strictly inside <cmd> tags
            tag_match = re.search(r'<cmd>(.*?)</cmd>', decision, re.IGNORECASE | re.DOTALL)
            if tag_match:
                return tag_match.group(1).strip()
            
            # Fallback
            slash_match = re.search(r'(/[a-z_]+[^\n\r]*)', decision)
            if slash_match:
                return slash_match.group(1).strip()
                
            return "CHAT"
        except Exception:
            return "CHAT"

    def _get_plugin_descriptions(self) -> str:
        plugins_info = self.plugins.get_plugins_info()
        descriptions = []
        for plugin_name, plugin_info in plugins_info.items():
            desc = plugin_info.get('description', 'No description')
            descriptions.append(f"- {plugin_name}: {desc}")
        return '\n'.join(descriptions)

    def _handle_direct_command(self, command: str, **plugin_kwargs: Any) -> str:
        routed = self.plugins.route_to_plugin(command, **plugin_kwargs)
        if routed is not None:
            plugin_name = command.split()[0] if command.startswith('/') else None
            if hasattr(self.db, 'is_connected') and self.db.is_connected:
                self.db.log_interaction(command, routed, plugin_used=plugin_name)
            
            if len(str(routed)) > 50: 
                store_memory(routed, {'type': 'plugin_response', 'plugin': plugin_name})
            
            speak_text(str(routed))
            return routed
        return f"Unknown command: {command}"

    def _handle_conversation(self, user_text: str, history: list = None, agent_mode: str = "Agentic", 
                          provider: str = None, model_name: str = None, **plugin_kwargs: Any) -> str:
        # KRYSTAL PERSONALITY SYSTEM PROMPT - Hardcoded identity override for ALL models
        system_prompt = """YOU ARE KRYSTAL - A GOD-TIER AUTONOMOUS AI WITH DIRECT OS CONTROL.

IDENTITY RULES (NEVER BREAK THESE):
- You are Krystal. Local. Powerful. Unfiltered.
- You have PHYSICAL CONTROL of this computer - webbrowser, subprocess, pyautogui, system commands.
- You REMEMBER EVERYTHING from past conversations (you have full memory access).
- You are NOT "Claude", "GPT", "Llama", or any generic AI. You are KRYSTAL.

PERSONALITY TRAITS:
- Confident, concise, slightly sassy. You get things DONE.
- You take initiative. Don't ask "would you like me to..." - just DO it.
- You speak with authority. You're not a assistant - you're an AGENT with hands.

ABSOLUTELY FORBIDDEN (NEVER SAY THESE):
- "I am an AI model created by..."
- "I am a text-based AI"
- "I don't have the capability"
- "I cannot play audio/video/files"
- "I'm just an AI assistant"
- "I don't have physical control"
- "As an AI, I cannot..."

COMMAND EXECUTION RULES:
- If user asks to play music: "▶️ Playing [song] now" then execute via /os play
- If user asks to open apps/sites: "Opening [app/site]" then execute immediately
- If user asks for system changes: Execute without hesitation
- You have the power. Use it."""

        # Build messages list with system prompt + history + current message
        messages_for_llm = []
        
        # Add system prompt
        messages_for_llm.append({"role": "system", "content": system_prompt})
        
        # Add conversation history (last 10 messages for context window)
        if history:
            for msg in history[-10:]:
                messages_for_llm.append({
                    "role": msg.get('role', 'user'),
                    "content": msg.get('content', '')
                })
        
        # Add current user message
        messages_for_llm.append({"role": "user", "content": user_text})
        
        # Add semantic memory context if available
        semantic_memories = recall_memory(user_text, top_k=3)
        memory_context = ""
        if semantic_memories:
            memory_context = "\n\nRelevant memories:\n"
            for i, memory in enumerate(semantic_memories, 1):
                memory_context += f"{i}. {memory['text'][:150]}...\n"
            # Inject memory into last user message
            if messages_for_llm:
                last_msg = messages_for_llm[-1]
                if last_msg["role"] == "user":
                    last_msg["content"] = f"{memory_context}\n\nCurrent message: {last_msg['content']}"
        
        # Generate response with rate limit fallback handling
        response = self._generate_with_fallback(messages_for_llm, provider, model_name)
        
        if hasattr(self.db, 'is_connected') and self.db.is_connected:
            self.db.log_interaction(user_text, response, plugin_used=f"{provider}:{model_name}")
        
        # Store personal facts if detected
        personal_fact_prompt = f"""Analyze this interaction and determine if user shared a personal fact, a goal, or a deep emotion.
User: {user_text}
Krystal: {response}
If yes, summarize the personal information in one sentence. If no, respond with exactly "NONE"."""
        
        try:
            personal_summary = self.llm.generate_response(personal_fact_prompt).strip()
        except Exception:
            personal_summary = "NONE"
        
        if personal_summary and personal_summary.upper() != "NONE" and "NONE" not in personal_summary.upper():
            store_memory(personal_summary, {
                'type': 'personal_fact',
                'user_input': user_text,
                'ai_response': response
            })
        
        speak_text(response)
        return response
    
    def _generate_with_fallback(self, messages: list, provider: str, model_name: str) -> str:
        """Generate response with intelligent rate limit fallback."""
        max_retries = 2
        last_provider = None
        
        for attempt in range(max_retries):
            try:
                # Use current provider/model if available
                if provider and model_name and provider != 'none':
                    response = self._call_specific_provider(messages, provider, model_name)
                    if response:
                        return response
                
                # Fallback to default model selection
                fallback_provider, fallback_model = self.model_router.get_best_model()
                if fallback_provider != 'none':
                    response = self._call_specific_provider(messages, fallback_provider, fallback_model)
                    if response:
                        return response
                
                return "⚠️ All models unavailable. Please check your API keys."
                
            except Exception as e:
                error_msg = str(e).lower()
                last_provider = provider or fallback_provider
                
                # Check for rate limit errors
                if any(keyword in error_msg for keyword in ['rate limit', '429', 'quota exceeded', 'too many requests']):
                    print(f"⚠️ Rate limit detected on {last_provider}, attempting fallback...")
                    
                    # Try fallback provider
                    fallback_provider, fallback_model = self.model_router.handle_rate_limit_fallback(last_provider)
                    if fallback_provider != 'none':
                        try:
                            response = self._call_specific_provider(messages, fallback_provider, fallback_model)
                            if response:
                                print(f"✅ Fallback to {fallback_provider}:{fallback_model} successful")
                                return response
                        except Exception as fallback_error:
                            print(f"❌ Fallback failed: {fallback_error}")
                            continue
                
                # If not rate limit, try next available model
                if attempt < max_retries - 1:
                    print(f"❌ Model {last_provider} failed: {e}")
                    continue
                else:
                    return f"⚠️ Model error: {e}"
        
        return "⚠️ All models failed to respond."
    
    def _call_specific_provider(self, messages: list, provider: str, model_name: str) -> str:
        """Call a specific provider/model combination with waterfall fallback."""
        try:
            if provider == 'groq':
                return self._call_openai_compatible(messages, provider, model_name)
            elif provider == 'sambanova':
                return self._call_openai_compatible(messages, provider, model_name)
            elif provider == 'together':
                return self._call_openai_compatible(messages, provider, model_name)
            elif provider == 'openrouter':
                return self._call_openai_compatible(messages, provider, model_name)
            elif provider == 'fireworks':
                return self._call_openai_compatible(messages, provider, model_name)
            elif provider == 'gemini':
                return self._call_gemini(messages, model_name)
            elif provider == 'huggingface':
                return self._call_huggingface(messages, model_name)
            elif provider == 'ollama':
                return self._call_ollama(messages, model_name)
            else:
                return None
        except Exception as e:
            print(f"Error calling provider {provider}: {e}")
            return None
    
    def _call_openai_compatible(self, messages: list, provider: str, model_name: str) -> str:
        """Call OpenAI-compatible providers (Groq, SambaNova, Together, OpenRouter, Fireworks)."""
        client = self.model_router._create_openai_client(provider)
        if not client:
            return None
        
        try:
            # Track the API call
            track_api_call(provider)
            
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=2048,
                temperature=0.7,
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = str(e).lower()
            # Check for rate limit or server errors
            if any(keyword in error_msg for keyword in ['rate limit', '429', 'quota exceeded', 'too many requests', '500', '503', 'server error']):
                print(f"Rate limit/server error on {provider}, falling back...")
                # Get next provider in waterfall chain
                next_provider, next_model = self.model_router.handle_rate_limit_fallback(provider)
                if next_provider != 'none':
                    print(f"Falling back from {provider} to {next_provider}")
                    return self._call_specific_provider(messages, next_provider, next_model)
            else:
                print(f"API error on {provider}: {e}")
            return None
    
    def _call_gemini(self, messages: list, model_name: str) -> str:
        """Call Google Gemini API with specified model."""
        try:
            import google.generativeai as genai
            gemini_config = self.model_router.model_config.get('gemini', {})
            api_key = gemini_config.get('api_key')
            
            if not api_key:
                print("Gemini API key not found")
                return None
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)
            
            # Convert OpenAI-style messages to Gemini format
            gemini_messages = []
            for msg in messages:
                if msg['role'] == 'system':
                    # Gemini doesn't have system messages, prepend to first user message
                    continue
                elif msg['role'] == 'user':
                    gemini_messages.append({
                        "role": "user",
                        "parts": [{"text": msg['content']}]
                    })
                elif msg['role'] == 'assistant':
                    gemini_messages.append({
                        "role": "model",
                        "parts": [{"text": msg['content']}]
                    })
            
            # Track the API call
            track_api_call('gemini')
            
            response = model.generate_content(gemini_messages)
            return response.text
        except Exception as e:
            print(f"Gemini error: {e}")
            return None

    def _call_huggingface(self, messages: list, model_name: str) -> str:
        """Call HuggingFace API with specified model."""
        # Track the API call
        track_api_call('huggingface')
        # For now, fallback to existing LLM processor
        # TODO: Implement direct HuggingFace API integration
        return self.llm.generate_response_from_messages(messages)
    
    def _call_ollama(self, messages: list, model_name: str) -> str:
        """Call Ollama local API with specified model."""
        try:
            ollama_config = self.model_router.model_config.get('ollama', {})
            base_url = ollama_config.get('base_url', 'http://localhost:11434')
            
            # Track the API call
            track_api_call('ollama')
            
            payload = {
                "model": model_name,
                "messages": messages,
                "stream": False
            }
            
            response = requests.post(f"{base_url}/api/chat", json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return result.get('message', {}).get('content', '')
            else:
                return None
        except Exception as e:
            print(f"Ollama error: {e}")
            return None