from __future__ import annotations

def run(input_data: dict | None = None) -> dict:
    if input_data is None:
        return {}
    text = input_data.get('text', '')
    digits = 0
    non_digits = 0
    for char in text:
        if char.isdigit():
            digits += 1
        else:
            non_digits += 1
    return {
        'total_digits': digits,
        'total_characters': len(text),
        'non_digits_count': non_digits,
        'input_text': text,
        'status': 'success'
    }
