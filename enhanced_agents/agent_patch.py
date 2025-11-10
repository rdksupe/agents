"""
Monkey patch for LiveKit Agent interruption logic to support filler word filtering.
"""

import time
from livekit.agents.voice import agent_activity
from .filler_words import count_non_filler_words

# Store original function
_original_interrupt_by_audio_activity = None


def _patched_interrupt_by_audio_activity(self):
    """
    Patched version of _interrupt_by_audio_activity that includes filler word filtering.
    """
    opt = self._session.options
    use_pause = opt.resume_false_interruption and opt.false_interruption_timeout is not None

    # Check if using realtime model with turn detection
    from livekit.agents import llm
    if isinstance(self.llm, llm.RealtimeModel) and self.llm.capabilities.turn_detection:
        return

    # Check if there's a speech to interrupt (moved before transcript check)
    if (
        self._current_speech is None 
        or self._current_speech.interrupted 
        or not self._current_speech.allow_interruptions
    ):
        return

    # Check transcript and apply filler word filtering
    if self.stt is not None and self._audio_recognition is not None:
        text = self._audio_recognition.current_transcript
        
        # Get configuration from session options
        ignore_fillers = getattr(opt, 'ignore_filler_words_interruption', False)
        min_words = getattr(opt, 'min_interruption_words', 0)
        
        if min_words > 0 or ignore_fillers:
            language = (
                self._audio_recognition._last_language 
                if hasattr(self._audio_recognition, '_last_language') 
                else None
            )
            
            # Count meaningful words (excluding fillers if enabled)
            if ignore_fillers:
                from .filler_words import count_non_filler_words
                custom_fillers = getattr(opt, 'custom_filler_words', None)
                case_sensitive = getattr(opt, 'filler_words_case_sensitive', False)
                
                meaningful_words = count_non_filler_words(
                    text,
                    language=language,
                    custom_filler_words=custom_fillers,
                    case_sensitive=case_sensitive
                )
            else:
                # Fall back to original word splitting
                from livekit.agents.utils import split_words
                meaningful_words = len(split_words(text, split_character=True))
            
            if meaningful_words < min_words:
                # Throttle logging to reduce spam
                now = time.time()
                if not hasattr(self, '_last_insufficient_log_time'):
                    self._last_insufficient_log_time = 0
                    self._last_insufficient_transcript = ""
                
                if (now - self._last_insufficient_log_time > 1.0 or 
                    text != self._last_insufficient_transcript):
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.debug(
                        "not interrupting - insufficient meaningful words",
                        extra={
                            "transcript": text,
                            "transcript_type": "interim",
                            "meaningful_words": meaningful_words,
                            "required": min_words
                        }
                    )
                    self._last_insufficient_log_time = now
                    self._last_insufficient_transcript = text
                return

    # Perform interruption
    if self._rt_session is not None:
        self._rt_session.start_user_activity()

    # Check again if already interrupted (race condition)
    if self._current_speech.interrupted:
        return

    # Log interruption once
    if not hasattr(self, '_interruption_logged') or not self._interruption_logged:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            "interrupting agent - meaningful content detected",
            extra={
                "transcript": text if 'text' in locals() else "",
                "transcript_type": "interim",
                "meaningful_words": meaningful_words if 'meaningful_words' in locals() else 0,
            }
        )
        self._interruption_logged = True

    self._paused_speech = self._current_speech

    if self._false_interruption_timer:
        self._false_interruption_timer.cancel()
        self._false_interruption_timer = None

    if use_pause and self._session.output.audio and self._session.output.audio.can_pause:
        self._session.output.audio.pause()
        self._session._update_agent_state("listening")
    else:
        if self._rt_session is not None:
            self._rt_session.interrupt()
        self._current_speech.interrupt()
    
    # Reset flag for next speech
    self._interruption_logged = False


def apply_patch():
    """
    Apply the monkey patch to enable filler word filtering.
    """
    global _original_interrupt_by_audio_activity
    
    if _original_interrupt_by_audio_activity is not None:
        # Already patched
        return
    
    # Save original function
    _original_interrupt_by_audio_activity = agent_activity.AgentActivity._interrupt_by_audio_activity
    
    # Apply patch
    agent_activity.AgentActivity._interrupt_by_audio_activity = _patched_interrupt_by_audio_activity
    
    print("✓ Applied filler word interruption patch")


def remove_patch():
    """
    Remove the monkey patch and restore original behavior.
    """
    global _original_interrupt_by_audio_activity
    
    if _original_interrupt_by_audio_activity is None:
        # Not patched
        return
    
    # Restore original function
    agent_activity.AgentActivity._interrupt_by_audio_activity = _original_interrupt_by_audio_activity
    _original_interrupt_by_audio_activity = None
    
    print("✓ Removed filler word interruption patch")