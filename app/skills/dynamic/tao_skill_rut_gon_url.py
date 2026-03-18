from __future__ import annotations

def run(input_data: dict | None = None) -> dict:
    if input_data is None:
        return {
            'error': 'No input data provided',
            'status': 'error',
            'message': 'Input data is required'
        }
    if 'url' not in input_data:
        return {
            'error': 'Missing URL in input data',
            'status': 'error',
            'message': 'Input must contain a "url" key'
        }
    original_url = input_data['url']
    # Generate deterministic shortened URL using hash of original URL
    import hashlib
    short_hash = hashlib.sha256(original_url.encode()).hexdigest()[:8]
    shortened_url = f'http://short.url/{short_hash}'
    return {
        'original_url': original_url,
        'shortened_url': shortened_url,
        'status': 'success',
        'message': 'URL shortened successfully',
        'shortener_service': 'mock-service',
        'input_data': input_data
    }
