# Addition of Filler Word Based Interruption in the Existing LiveKit SDK

## Current Architecture

The current LiveKit tooling for handling interruptions primarily depends on whether VAD is used or not. If a realtime LLM model is used, then there is no need for any such tooling. However, if VAD is used, a basic logic for interruption handling has been implemented which only counts the number of words a user speaks regardless of what those words are before interruption of the voice agent. Further, there is a false interruption resume logic which primarily resumes the agent if it has stopped due to some low confidence STT output.

### Original Interruption Logic

The original system implemented in `/agents/livekit-agents/livekit/agents/voice/agent_activity.py` used a simple word counting mechanism:

```python
def _interrupt_by_audio_activity(self) -> None:
    opt = self._session.options
    
    if isinstance(self.llm, llm.RealtimeModel) and self.llm.capabilities.turn_detection:
        return
    
    if self.stt is not None and self._audio_recognition is not None:
        text = self._audio_recognition.current_transcript
        
        if opt.min_interruption_words > 0:
            word_count = len(split_words(text, split_character=True))
            
            if word_count < opt.min_interruption_words:
                return
    
    if self._current_speech is not None and not self._current_speech.interrupted:
        self._current_speech.interrupt()
```

## My Modifications

### Live Demo of a running Voice Agent with the added filler word detection




https://github.com/user-attachments/assets/7f9a4b40-19e0-45ce-bd13-bd844e7657b2

Here I am using a publicly hosted LiveKit Meet Instance to converse with the agent and the livekit server itself is running locally on my laptop with Deepgram for STT and TTS and groq for LLM inference. 

## 1. Filler Words Module (`/agents/enhanced_agents/filler_words.py`)

This module implements the core filler word detection logic and serves as the foundation of the filtering system. The implementation consists of several key components:

### Filler Word Dictionaries

The module separates filler words into two categories for robust detection:

*   **`DEFAULT_FILLER_WORDS`**: Language-specific lists of common filler words for exact matching.
    *   **English:** `like`, `you know`, `i mean`, `well`, `so`, `actually`, `basically`, `literally`, `right`, `okay`, `yeah`, etc.
    *   **Spanish:** `este`, `pues`, `bueno`, `entonces`, `o sea`, `vale`, `aja`
    *   **French:** `ben`, `alors`, `donc`, `voilà`, `quoi`, `en fait`
    *   **German:** `also`, `halt`, `irgendwie`, `sozusagen`, `quasi`, `ne`

*   **`DEFAULT_FILLER_PATTERNS`**: Regex patterns to catch variations and repeated characters that exact matching would miss.
    *   `r'^u+h*m+$'` matches `um`, `umm`, `uhm`
    *   `r'^m+h*m+$'` captures `mhm`, `mhmm`, `mmm`
    *   `r'^u+h*[\s\-]*h+u+h*$'` covers `uh-huh`, `uh huh`, `uhhuh`

### Core Functions

*   **`is_only_filler_words()`**: Determines if a transcript contains exclusively filler words.
*   **`count_non_filler_words()`**: Counts meaningful words, excluding fillers.
*   **`_normalize_language_code()`**: Handles STT provider language code variants (e.g., "en-US" → "en").
*   **`_build_filler_set()`**: Constructs the complete set of fillers and patterns for a given language, merging custom words if provided.

Additionally, an environment-aware extension layer (see config section below) enables tuning filler lists without modifying code.

## 2. Runtime Interruption Patch (`/agents/enhanced_agents/agent_patch.py`)

This module monkey-patches `livekit.agents.voice.agent_activity.AgentActivity._interrupt_by_audio_activity`.

The wrapper:

*   Preserves the original guard clauses (LLM turn detection, existing interruption state, etc.).
*   Normalizes the STT language hint.
*   Checks `options.ignore_filler_words_interruption`.
*   If `True`, uses `count_non_filler_words()` before comparing to `min_interruption_words`.
*   If `False`, falls back to the SDK’s default word counting.
*   Only interrupts when the transcript contains enough meaningful words (excluding fillers).


## 3. Configuration Helpers (`/agents/enhanced_agents/config.py`)

This module provides the `FillerWordConfig` class for environment-based configuration. It supports the following environment variables:

| Variable                      | Default   | Description                                                 |
| ----------------------------- | --------- | ----------------------------------------------------------- |
| `ENABLE_FILLER_FILTERING`     | `true`    | Enables filler word filtering in interruptions              |
| `MIN_INTERRUPTION_WORDS`      | `2`       | Minimum number of meaningful words to trigger an interruption |
| `CUSTOM_FILLER_WORDS`         | `(empty)` | Comma-separated list of custom fillers to append or override  |
| `FILLER_WORDS_CASE_SENSITIVE` | `false`   | Enables case-sensitive comparison for fillers               |

Example usage:

```python
from enhanced_agents import FillerWordConfig

# This config will be loaded from environment variables
cfg = FillerWordConfig()

# In your agent setup:
# session = agents.AgentSession(...)
cfg.apply_to_options(session.options)
```

The configuration can also be combined with `.env` files using `python-dotenv` or other loaders.

## 4. Initialization and Setup (`/agents/enhanced_agents/__init__.py`)

A convenience wrapper `setup_filler_filtering()` is provided to load configuration and apply the patch automatically:

```python
from enhanced_agents import setup_filler_filtering

cfg = setup_filler_filtering()
```

This prints diagnostic info:

```
✓ Applied filler word interruption patch
Filler word filtering: enabled
Minimum interruption words: 2
Custom filler words: {'like', 'basically'}
```

## Installation and Usage

1.  **Clone the repository**

    ```bash
    git clone https://github.com/rdksupe/agents/
    git checkout feat/livekit-interrupt-handler-rishi
    cd livekit-agents
    ```

2.  **Start the LiveKit server via Docker**

    ```bash
    sudo docker run --rm --network host -p 7880:7880 -p 7881:7881 -p 7882:7882/udp \
        -e LIVEKIT_KEYS="devkey: secret" \
        livekit/livekit-server:latest --dev
    ```

3.  **Generate an access token with `livekit-cli`**

    ```bash
    livekit-cli create-token \
        --api-key devkey \
        --api-secret secret \
        --join \
        --room test-room \
        --identity test-user \
        --valid-for 24h
    ```

4. **Modify the .env.example with yoour relevant API Keys create a .env file**
    ```bash
    cp .env.example .env
    ```

4.  **Run the sample agent**

    ```bash
    python3 test_agent.py dev
    ```

## Usage

Refer to `test_agent.py` for an example of agent setup and interruption handling using the patched logic.

## Adding Custom Filler Words

Custom filler words can be added both ways:

### Via Environment Variables

Define `CUSTOM_FILLER_WORDS` before starting the process.

### Programmatically

```python
from agents.enhanced_agents import config as filler

custom_words = {"en": ["bro", "dude"], "es": ["ehh"]}
print(filler.count_non_filler_words("uh bro yeah dude", language="en", custom_filler_words=custom_words))
```


