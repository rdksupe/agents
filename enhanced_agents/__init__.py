"""
Enhanced LiveKit Agents with filler word filtering support.
"""

from .filler_words import (
    is_only_filler_words,
    count_non_filler_words,
    DEFAULT_FILLER_WORDS,
)
from .config import FillerWordConfig
from .agent_patch import apply_patch, remove_patch

__all__ = [
    'is_only_filler_words',
    'count_non_filler_words',
    'DEFAULT_FILLER_WORDS',
    'FillerWordConfig',
    'setup_filler_filtering',
    'apply_patch',
    'remove_patch',
]


def setup_filler_filtering(config: FillerWordConfig = None):
    """
    Setup filler word filtering for LiveKit Agents.
    
    Args:
        config: Configuration object. If None, loads from environment.
    
    Returns:
        The configuration object used.
    """
    if config is None:
        config = FillerWordConfig()
    
    # Apply monkey patch
    apply_patch()
    
    print(f"Filler word filtering: {'enabled' if config.enabled else 'disabled'}")
    print(f"Minimum interruption words: {config.min_interruption_words}")
    if config.custom_filler_words:
        print(f"Custom filler words: {config.custom_filler_words}")
    
    return config