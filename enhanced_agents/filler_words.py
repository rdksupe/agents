
import re

# Exact match filler words
DEFAULT_FILLER_WORDS: dict[str, list[str]] = {
    "en": [
        # Conversational fillers (exact matches work fine)
        "like", "you know", "i mean", "well", "so", 
        "actually", "basically", "literally", "right",
        "kinda", "sorta", "kind of", "sort of",
        
        # Agreement/acknowledgment words
        "okay", "ok", "yeah", "yes", "yep", "yup", "sure",
        "alright", "alrighty", "gotcha", "got it",
    ],
    "es": [
        "este", "pues", "bueno", "entonces", "o sea",
        "como", "digamos", "vamos", "vale", "aja", "ajá"
    ],
    "fr": [
        "ben", "alors", "donc", "voilà", "quoi",
        "tu vois", "tu sais", "en fait", "hein", "ouais"
    ],
    "de": [
        "also", "halt", "irgendwie", "sozusagen",
        "gewissermaßen", "quasi", "ne", "naja"
    ],
}

# Pattern-based filler detection (for variations)
DEFAULT_FILLER_PATTERNS: dict[str, list[str]] = {
    "en": [
        # Um variations: um, umm, ummm, uhm
        r'^u+h*m+$',
        
        # Uh variations: uh, uhh, uhhh
        r'^u+h+$',
        
        # Ah variations: ah, ahh, ahhh
        r'^a+h+$',
        
        # Er/Err variations: er, err, errr
        r'^e+r+$',
        
        # Hmm variations: hm, hmm, hmmm, hmmmm
        r'^h+m+$',
        
        # Mhm variations: mhm, mhmm, mmm, mmhmm, mmmm
        r'^m+h*m+$',
        
        # Uh-huh variations: uh-huh, uhhuh, uh huh
        r'^u+h*[\s\-]*h+u+h*$',
        
        # Mm-hmm variations: mm-hmm, mmhmm, mm hmm
        r'^m+[\s\-]*h+m+$',
        
        # Eh variations: eh, ehh
        r'^e+h+$',
    ],
    "es": [
        r'^e+h+$',     # eh, ehh
        r'^m+$',       # mm, mmm
    ],
    "fr": [
        r'^e+u+h*$',   # euh, euuh
        r'^h+e+u+$',   # heu, heuu
    ],
    "de": [
        r'^ä+h*m*$',   # äh, ähm, ähmm
        r'^h+m+$',     # hm, hmm
    ],
}


def _normalize_language_code(language: str | None) -> str | None:
    """
    Normalize language code to base form.
    Examples: "en-US" → "en", "es-ES" → "es"
    """
    if not language:
        return None
    
    base_lang = language.split('-')[0].split('_')[0].lower()
    return base_lang


def _split_words(text: str) -> list[str]:
    """Simple word splitter."""
    return text.split()


def _matches_filler_pattern(word: str, patterns: list[str]) -> bool:
    """
    Check if a word matches any of the filler patterns.
    
    Args:
        word: The word to check (already cleaned and lowercased)
        patterns: List of regex patterns to match against
        
    Returns:
        True if word matches any pattern
    """
    for pattern in patterns:
        if re.match(pattern, word):
            return True
    return False


def _is_filler_word(
    word: str, 
    filler_set: set[str], 
    patterns: list[str] | None = None
) -> bool:
    """
    Check if a single word is a filler.
    
    Args:
        word: The word to check
        filler_set: Set of exact-match filler words
        patterns: List of regex patterns for flexible matching
        
    Returns:
        True if the word is a filler
    """
    # Check exact match first (faster)
    if word in filler_set:
        return True
    
    # Check pattern match
    if patterns and _matches_filler_pattern(word, patterns):
        return True
    
    return False


def is_only_filler_words(
    text: str,
    language: str | None = None,
    custom_filler_words: list[str] | None = None,
    case_sensitive: bool = False,
) -> bool:
    """
    Check if text contains only filler words.
    
    Args:
        text: The transcribed text to check
        language: Language code (e.g., "en", "en-US"). Will be normalized.
        custom_filler_words: Additional filler words to check
        case_sensitive: Whether to perform case-sensitive matching
        
    Returns:
        True if text contains only filler words, False otherwise
    """
    if not text or not text.strip():
        return True
    
    normalized_text = text if case_sensitive else text.lower()
    words = _split_words(normalized_text.strip())
    
    if not words:
        return True
    
    filler_set, patterns = _build_filler_set(language, custom_filler_words, case_sensitive)
    
    for word in words:
        # Strip punctuation
        clean_word = word.strip(".,!?;:'\"")
        
        if clean_word and not _is_filler_word(clean_word, filler_set, patterns):
            return False
    
    return True


def count_non_filler_words(
    text: str,
    language: str | None = None,
    custom_filler_words: list[str] | None = None,
    case_sensitive: bool = False,
) -> int:
    """
    Count meaningful words excluding fillers.
    
    Args:
        text: Text to analyze
        language: Language code (e.g., "en", "en-US"). Will be normalized.
        custom_filler_words: Additional filler words to exclude
        case_sensitive: Whether matching is case-sensitive
    
    Returns:
        Count of meaningful (non-filler) words
    """
    if not text or not text.strip():
        return 0
    
    words = _split_words(text)
    filler_set, patterns = _build_filler_set(language, custom_filler_words, case_sensitive)
    
    meaningful_count = 0
    for word in words:
        clean_word = word.strip(".,!?;:'\"")
        if not case_sensitive:
            clean_word = clean_word.lower()
        
        if clean_word and not _is_filler_word(clean_word, filler_set, patterns):
            meaningful_count += 1
    
    return meaningful_count


def _build_filler_set(
    language: str | None,
    custom_filler_words: list[str] | None,
    case_sensitive: bool,
) -> tuple[set[str], list[str] | None]:
    """
    Build the set of filler words and patterns based on language.
    
    Returns:
        Tuple of (filler_words_set, filler_patterns_list)
    """
    filler_set: set[str] = set()
    patterns: list[str] | None = None
    
    # Normalize language code: "en-US" → "en"
    base_language = _normalize_language_code(language)
    
    if base_language and base_language in DEFAULT_FILLER_WORDS:
        filler_set.update(DEFAULT_FILLER_WORDS[base_language])
        patterns = DEFAULT_FILLER_PATTERNS.get(base_language, [])
    elif not base_language:
        # No language specified, use all languages
        for lang_fillers in DEFAULT_FILLER_WORDS.values():
            filler_set.update(lang_fillers)
        # Combine all patterns
        all_patterns = []
        for lang_patterns in DEFAULT_FILLER_PATTERNS.values():
            all_patterns.extend(lang_patterns)
        patterns = all_patterns if all_patterns else None
    else:
        # Language not found, use all languages as fallback
        for lang_fillers in DEFAULT_FILLER_WORDS.values():
            filler_set.update(lang_fillers)
        all_patterns = []
        for lang_patterns in DEFAULT_FILLER_PATTERNS.values():
            all_patterns.extend(lang_patterns)
        patterns = all_patterns if all_patterns else None
    
    if custom_filler_words:
        filler_set.update(
            custom_filler_words if case_sensitive 
            else [w.lower() for w in custom_filler_words]
        )
    
    if not case_sensitive:
        filler_set = {w.lower() for w in filler_set}
    
    return filler_set, patterns