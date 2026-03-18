from __future__ import annotations

from collections import Counter

def run(input_data: dict | None = None) -> dict:
    text = ""
    if input_data is not None and 'text' in input_data:
        text = input_data['text']
    
    words = text.split()
    total_words = len(words)
    total_characters = len(text)
    unique_words = len(set(words))
    word_freq = Counter(words)
    most_common_words = word_freq.most_common(5)
    has_duplicates = len(words) != len(set(words))
    
    return {
        "total_words": total_words,
        "total_characters": total_characters,
        "unique_words": unique_words,
        "word_frequency": dict(word_freq),
        "most_common_words": most_common_words,
        "has_duplicates": has_duplicates
    }
