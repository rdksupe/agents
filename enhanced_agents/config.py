"""
Configuration extension for filler word filtering.
"""

import os
from typing import Set


class FillerWordConfig:
    """Configuration for filler word filtering."""
    
    def __init__(
        self,
        enabled: bool = None,
        min_interruption_words: int = None,
        custom_filler_words: Set[str] = None,
        case_sensitive: bool = None,
    ):
        # Load from environment if not provided
        self.enabled = enabled if enabled is not None else self._load_enabled()
        self.min_interruption_words = min_interruption_words if min_interruption_words is not None else self._load_min_words()
        self.custom_filler_words = custom_filler_words if custom_filler_words is not None else self._load_custom_words()
        self.case_sensitive = case_sensitive if case_sensitive is not None else self._load_case_sensitive()
    
    def _load_enabled(self) -> bool:
        return os.getenv("ENABLE_FILLER_FILTERING", "true").lower() == "true"
    
    def _load_min_words(self) -> int:
        return int(os.getenv("MIN_INTERRUPTION_WORDS", "2"))
    
    def _load_custom_words(self) -> Set[str]:
        words_str = os.getenv("CUSTOM_FILLER_WORDS", "")
        if not words_str:
            return set()
        return set(w.strip() for w in words_str.split(",") if w.strip())
    
    def _load_case_sensitive(self) -> bool:
        return os.getenv("FILLER_WORDS_CASE_SENSITIVE", "false").lower() == "true"
    
    def apply_to_options(self, options):
        """
        Apply configuration to VoiceOptions dynamically.
        This adds attributes without modifying the VoiceOptions class.
        """
        options.ignore_filler_words_interruption = self.enabled
        options.min_interruption_words = self.min_interruption_words
        options.custom_filler_words = self.custom_filler_words
        options.filler_words_case_sensitive = self.case_sensitive
        return options