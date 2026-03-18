from __future__ import annotations

import re

def run(input_data: dict | None = None) -> dict:
    result = {
        'status': 'error',
        'standardized_email': '',
        'is_valid': False,
        'original_email': '',
        'error_message': ''
    }
    if input_data is None:
        result['error_message'] = 'No input data provided'
        return result
    email = input_data.get('email')
    if not email:
        result['error_message'] = 'Email not provided'
        return result
    standardized_email = email.replace(' ', '').lower()
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    is_valid = re.match(email_regex, standardized_email) is not None
    result['standardized_email'] = standardized_email
    result['is_valid'] = is_valid
    result['original_email'] = email
    result['error_message'] = 'Invalid email format' if not is_valid else ''
    result['status'] = 'success' if is_valid else 'error'
    return result
