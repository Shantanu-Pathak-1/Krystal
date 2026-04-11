"""
Krystal core engine: wires KeyManager, PluginManager, LLMProcessor,
and the main input loop. Agentic routing uses XML tags for safety.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any
import re

_ENGINE_DIR = Path(__file__).resolve().parent

def _load_sibling_module(unique_name: str, filename: str):
    path = _ENGINE_DIR / filename
    spec = importlib.util.spec_from_file_location(unique_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

_api_router = _load_sibling_module("krystal_engine._api_router", "api_router.py")
_plugin_manager_mod = _load_sibling_module("krystal_engine._plugin_manager", "plugin_manager.py")
_llm_mod = _load_sibling_module("krystal_engine._llm_processor", "llm_processor.py")
_db_manager_mod = _load_sibling_module("krystal_engine._db_manager", "db_manager.py")
_voice_out_mod = _load_sibling_module("krystal_engine._voice_out", "voice_out.py")
_vector_memory_mod = _load_sibling_module("krystal_engine._vector_memory", "vector_memory.py")

KeyManager = _api_router.KeyManager
PluginManager = _plugin_manager_mod.PluginManager
LLMProcessor = _llm_mod.LLMProcessor
MongoManager = _db_manager_mod.MongoManager
speak_text = _voice_out_mod.speak_text
initialize_voice = _voice_out_mod.initialize_voice
initialize_pinecone = _vector_memory_mod.initialize_pinecone
store_memory = _vector_memory_mod.store_memory
recall_memory = _vector_memory_mod.recall_memory

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
        initialize_voice()
        initialize_pinecone()

    def process_input(self, user_text: str, **plugin_kwargs: Any) -> str:
        if user_text.startswith('/'):
            return self._handle_direct_command(user_text, **plugin_kwargs)
        
        recent_history = []
        if hasattr(self.db, 'is_connected') and self.db.is_connected:
             recent_history = self.db.get_recent_logs(limit=3)
             
        history_context = ""
        if recent_history:
            history_context = "\n\nRecent chat history:\n"
            for i, log in enumerate(recent_history, 1):
                history_context += f"{i}. User: {log.get('user_input', '')}\n"
                if log.get('response'):
                    history_context += f"   Krystal: {log.get('response')}\n"
            history_context += "\nUse this history to resolve references like 'that song' or 'it' before generating commands."
        
        routing_decision = self._agentic_route(user_text, history_context)
        
        if routing_decision != "CHAT":
            return self._handle_direct_command(routing_decision, **plugin_kwargs)
        
        return self._handle_conversation(user_text, **plugin_kwargs)

    def _agentic_route(self, user_text: str, history_context: str = "") -> str:
        plugin_descriptions = self._get_plugin_descriptions()
        
        routing_prompt = f"""You are Krystal's routing brain. Read the user's input and determine the action.

Available plugins:
{plugin_descriptions}

{history_context}

User input: {user_text}

Analyze the request. You can think out loud and explain your reasoning, BUT your FINAL absolute command MUST be wrapped exactly inside <cmd> and </cmd> tags.
If it requires a plugin, output the exact slash command. If it's a normal conversation, output CHAT.

IMPORTANT MEDIA RULES:
- If user wants to play a song/video: <cmd>/os play [song name]</cmd>
- If user wants to pause/stop music: <cmd>/os pause</cmd>
- If user wants next song: <cmd>/os next</cmd>

HINGLESH VOLUME COMMANDS: 'full kar do' = 100, 'tez karo' = +10, 'aadhi' = 50, 'mute' = 0.
Format: <cmd>/sys volume 100</cmd>

Examples of REQUIRED output format:
<cmd>/os play Agar Tum Sath Ho</cmd>
<cmd>/sys volume 100</cmd>
<cmd>CHAT</cmd>
"""
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

    def _handle_conversation(self, user_text: str, **plugin_kwargs: Any) -> str:
        recent_logs = self.db.get_recent_logs(limit=5) if (hasattr(self.db, 'is_connected') and self.db.is_connected) else []
        short_term_context = ""
        if recent_logs:
            short_term_context = "\n\nRecent conversation context:\n"
            for log in reversed(recent_logs):
                short_term_context += f"User: {log.get('user_input', '')}\nKrystal: {log.get('response', '')[:150]}...\n\n"
        
        semantic_memories = recall_memory(user_text, top_k=3)
        long_term_context = ""
        if semantic_memories:
            long_term_context = "\n\nRelevant past memories:\n"
            for i, memory in enumerate(semantic_memories, 1):
                long_term_context += f"{i}. {memory['text'][:200]}...\n"
            long_term_context += "\nUse these memories as context for your response:"
        
        context_prompt = f"{short_term_context}{long_term_context}" if (short_term_context or long_term_context) else ""
        enhanced_prompt = f"{context_prompt}\n\nUser: {user_text}" if context_prompt else user_text
        response = self.llm.generate_response(enhanced_prompt)
        
        if hasattr(self.db, 'is_connected') and self.db.is_connected:
            self.db.log_interaction(user_text, response, plugin_used=None)
        
        personal_fact_prompt = f"""Analyze this interaction and determine if the user shared a personal fact, a goal, or a deep emotion.
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