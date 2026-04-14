from Chat.ChatFilters import filter_words
import re

BANNED_WORDS = ['gooey']

def is_message_allowed(message: str) -> bool:
    # Check if the message is allowed (does not contain banned or curse words)
    lowered = message.lower()
    banned = any(banned in lowered for banned in BANNED_WORDS)
    filtered = any(curse in lowered for curse in filter_words.WORD_LIST)
    return not (banned or filtered)

def filter_message(message: str) -> str:
    """Return the message if allowed, else return an empty string (indicating deletion)."""
    return message if is_message_allowed(message) else ''

def remove_banned_words(message: str) -> str:
    """Remove all banned words from the message, preserving other text."""
    result = message
    all_banned = BANNED_WORDS + filter_words.WORD_LIST
    
    for word in all_banned:
        # Use word boundary to match whole words, case-insensitive
        pattern = r'\b' + re.escape(word) + r'\b'
        result = re.sub(pattern, '', result, flags=re.IGNORECASE)
    
    # Clean up extra spaces
    result = ' '.join(result.split())
    return result
