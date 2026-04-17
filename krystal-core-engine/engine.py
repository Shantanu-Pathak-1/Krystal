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
import logging

# Setup logger
logger = logging.getLogger("Krystal.engine")

_ENGINE_DIR = Path(__file__).resolve().parent


class IntentClassifier:
    """
    Gatekeeper Intent Classifier using Groq for fast classification.
    Determines if user input requires ACTION (tools) or CHAT (conversation).
    """
    
    def __init__(self, key_manager: KeyManager):
        self.key_manager = key_manager
        self.classification_system_prompt = """You are Krystal's core router. Analyze the user's input. Return ONLY a JSON object: {"intent": "CHAT" | "ACTION" | "WRITE_CODE"}.
Rules: 
- If it's a greeting, question, or general talk (e.g., 'hello', 'how are you'), return CHAT.
- If it's a command requiring external tools like playing media, trading, or system tasks, return ACTION.
- If it's a request to create, write, modify, or delete code/files (e.g., 'create a file', 'write code', 'modify the file', 'add function'), return WRITE_CODE."""
    
    def classify(self, user_text: str, history_context: str = "") -> str:
        """
        Classify user intent as CHAT, ACTION, or WRITE_CODE using Groq.
        
        Args:
            user_text: The user's input message
            history_context: Optional conversation history context
            
        Returns:
            "CHAT" for conversation, "ACTION" for tool execution
        """
        try:
            # Build classification prompt
            prompt = f"{self.classification_system_prompt}\n\n"
            if history_context:
                prompt += f"{history_context}\n\n"
            prompt += f"User input: {user_text}\n\n"
            prompt += "Return ONLY the JSON object. No other text."
            
            # Use Groq for fast classification
            groq_key = self.key_manager.get_next_groq_key() if self.key_manager.has_groq_keys() else None
            
            if not groq_key:
                # Fallback: simple keyword-based classification
                return self._fallback_classify(user_text)
            
            # Create OpenAI client for Groq
            client = OpenAI(
                api_key=groq_key,
                base_url="https://api.groq.com/openai/v1",
                timeout=10.0
            )
            
            # Track the API call
            track_api_call("groq")
            
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.1,  # Low temperature for consistent classification
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                import json
                result = json.loads(result_text)
                intent = result.get("intent", "CHAT").upper()
                return intent if intent in ["CHAT", "ACTION"] else "CHAT"
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                # If JSON parsing fails, fallback to keyword classification
                logger.warning(f"[IntentClassifier] Classification failed: {e}, using fallback")
                return self._fallback_classify(user_text)
            except Exception as e:
                logger.error(f"[IntentClassifier] Unexpected error: {e}, using fallback")
                return self._fallback_classify(user_text)
                
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"[IntentClassifier] Classification failed: {e}, using fallback")
            return self._fallback_classify(user_text)
        except Exception as e:
            logger.error(f"[IntentClassifier] Unexpected error: {e}, using fallback")
            return self._fallback_classify(user_text)
    
    def _fallback_classify(self, user_text: str) -> str:
        """
        Fallback keyword-based classification when LLM is unavailable.
        """
        text_lower = user_text.lower()
        
        # Code writing keywords
        code_keywords = [
            'create', 'write', 'make', 'add', 'file', 'function', 'class',
            'component', 'modify', 'edit', 'update', 'change', 'delete', 'remove',
            'code', 'script', 'react', 'python', 'typescript', 'javascript'
        ]
        
        # Action keywords that indicate tool usage
        action_keywords = [
            'play', 'pause', 'stop', 'next', 'previous', 'lock',
            'search', 'execute', 'run', 'launch', 'start', 'close',
            'trade', 'buy', 'sell', 'market', 'stock', 'crypto'
        ]
        
        # Check if it's a direct command
        if user_text.startswith('/'):
            return "ACTION"
        
        # Check for code writing keywords
        for keyword in code_keywords:
            if keyword in text_lower:
                return "WRITE_CODE"
        
        # Check for action keywords at the start of the message
        first_word = text_lower.split()[0] if text_lower.split() else ""
        if first_word in action_keywords:
            return "ACTION"
        
        # Default to CHAT for safety
        return "CHAT"


def clean_conversation_history(history: list) -> list:
    """
    Clean conversation history to remove tool execution artifacts and prevent context bleed.
    
    Removes:
    - <cmd> tags and their content
    - JSON tool calls and function calls
    - System output messages like "▶️ Playing song"
    - Tool execution results that could confuse the LLM
    - Command syntax and execution tags
    
    Args:
        history: List of message dicts with 'role' and 'content'
        
    Returns:
        Cleaned history list
    """
    if not history:
        return []
    
    cleaned = []
    
    for msg in history:
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        
        if not content:
            cleaned.append(msg)
            continue
        
        # Remove command syntax and tool calls from assistant messages
        if role == 'assistant':
            # Remove <cmd>...</cmd> blocks
            content = re.sub(r'<cmd>.*?</cmd>', '[Action executed in the past]', content, flags=re.DOTALL | re.IGNORECASE)
            
            # Remove JSON tool calls (function_call format)
            content = re.sub(r'\{"function_call":\s*\{[^}]*\}\}', '[Action executed in the past]', content, flags=re.DOTALL)
            
            # Remove function call blocks
            content = re.sub(r'function_calls?:\s*\[[^\]]*\]', '[Action executed in the past]', content, flags=re.DOTALL)
            
            # Remove tool call blocks
            content = re.sub(r'tool_calls?:\s*\[[^\]]*\]', '[Action executed in the past]', content, flags=re.DOTALL)
            
            # Remove command patterns like /os play, /os open, etc.
            content = re.sub(r'/[a-z_]+\s+[^\n]+', '[Action executed in the past]', content, flags=re.IGNORECASE)
            
            # Remove common tool execution artifacts
            artifacts_to_remove = [
                r'▶️ Playing.*',
                r'Opening.*',
                r'▶️.*',
                r'🎵.*',
                r'🔊.*',
                r'⏸️.*',
                r'⏭️.*',
                r'⏮️.*',
                r'🔒.*',
                r'Executing command.*',
                r'Command executed.*',
                r'Tool result.*',
                r'Plugin response.*',
                r'Called function.*',
                r'Function returned.*',
            ]
            
            for artifact in artifacts_to_remove:
                content = re.sub(artifact, '[Action executed in the past]', content, flags=re.IGNORECASE)
            
            # Clean up extra whitespace and multiple placeholders
            content = re.sub(r'\[Action executed in the past\]\s*\[Action executed in the past\]+', '[Action executed in the past]', content)
            content = content.strip()
            
            # If content is empty after cleaning, skip this message
            if not content:
                continue
        
        cleaned.append({'role': role, 'content': content})
    
    return cleaned

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
_guest_profiler_mod = _load_sibling_module("krystal_engine._guest_profiler", "guest_profiler.py")

# Import usage tracker
try:
    _usage_tracker_mod = _load_sibling_module("krystal_engine._usage_tracker", "usage_tracker.py")
    track_api_call = _usage_tracker_mod.track_api_call
except ImportError as e:
    logger.warning(f"Usage tracker not available: {e}")
    track_api_call = lambda provider: None  # Fallback no-op

KeyManager = _api_router.KeyManager
PluginManager = _plugin_manager_mod.PluginManager
LLMProcessor = _llm_mod.LLMProcessor
MongoManager = _db_manager_mod.MongoManager
speak_text = _voice_out_mod.speak_text
initialize_pinecone = _vector_memory_mod.initialize_pinecone
store_memory = _vector_memory_mod.store_memory
recall_memory = _vector_memory_mod.recall_memory
GuestProfiler = _guest_profiler_mod.GuestProfiler


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
        except (ConnectionError, TimeoutError) as e:
            logger.warning(f"[ModelRouter] Network error creating {provider} client: {e}")
            return None
        except Exception as e:
            logger.error(f"[ModelRouter] Failed to create {provider} client: {e}")
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
        self.profiler = GuestProfiler()
        
        # Initialize Multi-Model Router
        self.model_router = MultiModelRouter()
        
        # Initialize Intent Classifier (Gatekeeper)
        self.intent_classifier = IntentClassifier(self.keys)

        # Initialize Pinecone with API key from environment
        import os
        pinecone_key = os.environ.get('PINECONE_API_KEY')
        self.vector_store = initialize_pinecone(api_key=pinecone_key)

# ... (rest of the code remains the same)
    def process_input(self, user_text: str, agent_mode: str = "Agentic", history: list = None, **plugin_kwargs: Any) -> str:
        if user_text.startswith('/'):
            return self._handle_direct_command(user_text, **plugin_kwargs)
        
        # Safe Mode: Bypass all agentic routing, force chat only
        if agent_mode == "Safe":
            return self._handle_conversation(user_text, history=history, agent_mode=agent_mode, **plugin_kwargs)
        
        # Use provided history or fetch from DB as fallback
        chat_history = history if history else []
        
        # Format history for context injection (for Intent Classifier)
        history_context = self._format_history_context(chat_history)
        
        # === INTENT CLASSIFIER GATEKEEPER ===
        # Classify intent before any tool execution
        intent = self.intent_classifier.classify(user_text, history_context)
        
        logger.info(f"[IntentClassifier] Classified intent: {intent} for input: {user_text[:50]}...")
        
        if intent == "WRITE_CODE":
            # WRITE_CODE: Handle code writing requests
            return self._handle_code_writing(user_text, history=history, **plugin_kwargs)
        
        if intent == "CHAT":
            # CHAT: Clean history to prevent context bleed, route to conversation
            cleaned_history = clean_conversation_history(chat_history)
            
            # Detect task type for intelligent routing
            task_type = self.model_router._detect_task_type(user_text, plugin_kwargs)
            
            # Get best model based on task, mode, and conditions
            provider, model_name = self.model_router.get_best_model(
                task_type=task_type,
                agent_mode=agent_mode,
                context=plugin_kwargs
            )
            
            # Remove provider/model_name from plugin_kwargs to avoid duplicate argument error
            clean_kwargs = {k: v for k, v in plugin_kwargs.items() if k not in ('provider', 'model_name')}
            
            # Route directly to conversation, bypassing orchestrator
            return self._handle_conversation(user_text, history=cleaned_history, agent_mode=agent_mode, 
                                          provider=provider, model_name=model_name, **clean_kwargs)
        
        # ACTION: Pass through to existing routing logic (TaskPlanner/Orchestrator)
        # Detect task type for intelligent routing
        task_type = self.model_router._detect_task_type(user_text, plugin_kwargs)
        
        # Get best model based on task, mode, and conditions
        provider, model_name = self.model_router.get_best_model(
            task_type=task_type,
            agent_mode=agent_mode,
            context=plugin_kwargs
        )
        
        # Add additional DB history if available for action routing
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
        
        # If agentic route returns CHAT for ACTION intent, fall back to conversation
        sanitized_history = clean_conversation_history(chat_history)
        clean_kwargs = {k: v for k, v in plugin_kwargs.items() if k not in ('provider', 'model_name')}
        return self._handle_conversation(user_text, history=sanitized_history, agent_mode=agent_mode, 
                                      provider=provider, model_name=model_name, **clean_kwargs)

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
4. If the user asks "What song is playing?" → This is CONVERSATIONAL → Return CHAT

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
        except (ValueError, KeyError) as e:
            logger.warning(f"[IntentClassifier] Parse error: {e}, defaulting to CHAT")
            return "CHAT"
        except Exception as e:
            logger.error(f"[IntentClassifier] Unexpected error: {e}, defaulting to CHAT")
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

    def _handle_code_writing(self, user_text: str, history: list = None, **plugin_kwargs: Any) -> str:
        """
        Handle code writing requests by parsing the user's request and calling the appropriate file operations.
        
        Args:
            user_text: User's code writing request
            history: Conversation history
            **plugin_kwargs: Additional plugin arguments
            
        Returns:
            Response message with file operation results
        """
        try:
            # Import code_writer plugin
            from plugins.code_writer import get_code_writer
            code_writer = get_code_writer()
            
            # Use LLM to parse the user's request into structured commands
            parsing_prompt = f"""You are a code writing assistant. Parse the user's request and return a JSON object with the file operation details.

User request: {user_text}

Return ONLY a JSON object with this structure:
{{
    "operation": "create" | "modify" | "delete" | "read",
    "filepath": "relative/path/to/file.ext",
    "content": "file content (for create/modify)",
    "modify_operation": "append" | "replace" | "edit" (for modify),
    "search": "text to search (for edit operation)",
    "replace": "text to replace with (for edit operation)",
    "open_in_vscode": true (if file should be opened in VS Code)
}}

Rules:
- Infer the file path from the request (e.g., "create a React component for login" -> "src/components/Login.tsx")
- Generate appropriate code based on the request
- For modify operations, use "append" to add content, "replace" to replace entire file, "edit" for find-and-replace
- Set open_in_vscode to true for new files

Return ONLY the JSON object. No other text."""
            
            response = self.llm.generate_response(parsing_prompt)
            
            # Parse JSON response
            try:
                import json
                operation_data = json.loads(response)
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract JSON from the response
                import re
                json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
                if json_match:
                    operation_data = json.loads(json_match.group(0))
                else:
                    return " Could not parse your request. Please be more specific about the file operation."
            
            # Execute the operation
            operation = operation_data.get("operation", "create")
            filepath = operation_data.get("filepath", "")
            
            if not filepath:
                return " Please specify a file path."
            
            if operation == "create":
                content = operation_data.get("content", "")
                open_in_vscode = operation_data.get("open_in_vscode", True)
                result = code_writer.create_file(filepath, content, open_in_vscode)
                return result
            
            elif operation == "modify":
                modify_op = operation_data.get("modify_operation", "append")
                content = operation_data.get("content", "")
                search = operation_data.get("search", "")
                replace = operation_data.get("replace", "")
                result = code_writer.modify_file(filepath, modify_op, content, search, replace)
                return result
            
            elif operation == "delete":
                result = code_writer.delete_file(filepath)
                return result
            
            elif operation == "read":
                result = code_writer.read_file(filepath)
                return result
            
            else:
                return f" Unknown operation: {operation}"
                
        except ImportError as e:
            logger.error(f"[KrystalEngine] Code writer plugin not available: {e}")
            return " Code writing plugin not available. Please install the required dependencies."
        except Exception as e:
            logger.error(f"[KrystalEngine] Error handling code writing: {e}")
            return f" Error processing your request: {e}"

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
                
                return "[WARNING] All models unavailable. Please check your API keys."
                
            except Exception as e:
                error_msg = str(e).lower()
                last_provider = provider or fallback_provider
                
                # Check for rate limit errors
                if any(keyword in error_msg for keyword in ['rate limit', '429', 'quota exceeded', 'too many requests']):
                    logger.warning(f"[WARNING] Rate limit detected on {last_provider}, attempting fallback...")
                    
                    # Try fallback provider
                    fallback_provider, fallback_model = self.model_router.handle_rate_limit_fallback(last_provider)
                    if fallback_provider != 'none':
                        try:
                            response = self._call_specific_provider(messages, fallback_provider, fallback_model)
                            if response:
                                logger.info(f"[SUCCESS] Fallback to {fallback_provider}:{fallback_model} successful")
                                return response
                        except Exception as fallback_error:
                            logger.error(f"[ERROR] Fallback failed: {fallback_error}")
                            continue
                
                # If not rate limit, try next available model
                if attempt < max_retries - 1:
                    logger.error(f"[ERROR] Model {last_provider} failed: {e}")
                    continue
                else:
                    return f"[WARNING] Model error: {e}"
        return "[WARNING] All models failed to respond."
    
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
            logger.error(f"Error calling provider {provider}: {e}")
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
                logger.warning(f"Rate limit/server error on {provider}, falling back...")
                # Get next provider in waterfall chain
                next_provider, next_model = self.model_router.handle_rate_limit_fallback(provider)
                if next_provider != 'none':
                    logger.info(f"Falling back from {provider} to {next_provider}")
                    return self._call_specific_provider(messages, next_provider, next_model)
            else:
                logger.error(f"API error on {provider}: {e}")
            return None
    
    def _call_huggingface(self, messages: list, model_name: str) -> str:
        """Call HuggingFace API with specified model using Inference API."""
        try:
            import requests
            huggingface_config = self.model_router.model_config.get('huggingface', {})
            api_key = huggingface_config.get('api_key')

            if not api_key:
                logger.warning("HuggingFace API key not found")
                return None

            # Track the API call
            track_api_call('huggingface')

            # Convert OpenAI-style messages to HuggingFace format
            prompt = ""
            for msg in messages:
                if msg['role'] == 'system':
                    prompt += f"System: {msg['content']}\n"
                elif msg['role'] == 'user':
                    prompt += f"User: {msg['content']}\n"
                elif msg['role'] == 'assistant':
                    prompt += f"Assistant: {msg['content']}\n"

            # Use HuggingFace Inference API
            headers = {"Authorization": f"Bearer {api_key}"}
            API_URL = f"https://api-inference.huggingface.co/models/{model_name}"

            response = requests.post(API_URL, headers=headers, json={"inputs": prompt}, timeout=30)
            if response.status_code == 200:
                result = response.json()
                # Handle different response formats
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get('generated_text', '')
                elif isinstance(result, dict):
                    return result.get('generated_text', '')
                else:
                    return str(result)
            else:
                logger.error(f"HuggingFace API error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"HuggingFace error: {e}")
            return None
    
    def _call_gemini(self, messages: list, model_name: str) -> str:
        """Call Google Gemini API with specified model."""
        try:
            import google.generativeai as genai
            gemini_config = self.model_router.model_config.get('gemini', {})
            api_key = gemini_config.get('api_key')

            if not api_key:
                logger.warning("Gemini API key not found")
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
            logger.error(f"Gemini error: {e}")
            return None
    
    def _call_ollama(self, messages: list, model_name: str) -> str:
        """Call Ollama API with specified model."""
        try:
            import requests
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
            logger.error(f"Ollama error: {e}")
            return None