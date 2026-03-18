from __future__ import annotations

def run(input_data: dict | None = None) -> dict:
    if input_data is None or 'email' not in input_data:
        return {
            'success': False,
            'error': 'Missing email input'
        }
    email = input_data['email']
    if '@' not in email:
        return {
            'success': False,
            'error': 'Invalid email format: missing @'
        }
    parts = email.split('@', 1)
    if len(parts) != 2:
        return {
            'success': False,
            'error': 'Invalid email format: multiple @'
        }
    local_part, domain = parts
    return {
        'success': True,
        'domain': domain,
        'local_part': local_part,
        'input_email': email
    }
