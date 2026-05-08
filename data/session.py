#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""In-memory session management for the business analyst agent."""
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ChatSession:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    history: List[Dict[str, str]] = field(default_factory=list)
    data_source: Any = None          # DataSource instance
    model_provider: str = ""         # Selected LLM provider key
    # Token usage tracking
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    last_prompt_tokens: int = 0      # most recent call's prompt size (for context bar)

    def add_user(self, text: str):
        self.history.append({"role": "user", "content": text})

    def add_assistant(self, text: str):
        self.history.append({"role": "assistant", "content": text})

    def clear_history(self):
        self.history.clear()
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.last_prompt_tokens = 0

    def record_usage(self, prompt_tokens: int, completion_tokens: int):
        self.total_input_tokens += prompt_tokens
        self.total_output_tokens += completion_tokens
        self.last_prompt_tokens = prompt_tokens


class SessionManager:
    def __init__(self):
        self._store: Dict[str, ChatSession] = {}

    def create(self) -> ChatSession:
        s = ChatSession()
        self._store[s.session_id] = s
        return s

    def get(self, sid: str) -> Optional[ChatSession]:
        return self._store.get(sid)

    def get_or_create(self, sid: str) -> ChatSession:
        if sid and sid in self._store:
            return self._store[sid]
        s = ChatSession(session_id=sid) if sid else ChatSession()
        self._store[s.session_id] = s
        return s

    def remove(self, sid: str):
        self._store.pop(sid, None)
