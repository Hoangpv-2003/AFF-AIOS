from __future__ import annotations

def run(input_data: dict | None = None) -> dict:
    if input_data is None:
        return {
            'error': 'No input data provided',
            'mapped_keys': [],
            'value_mapping': {},
            'total_keys': 0,
            'input_type': 'NoneType'
        }
    try:
        mapped_keys = list(input_data.keys())
        value_mapping = {k: input_data[k] for k in mapped_keys}
        total_keys = len(mapped_keys)
        return {
            'mapped_keys': mapped_keys,
            'value_mapping': value_mapping,
            'total_keys': total_keys,
            'input_type': type(input_data).__name__,
            'is_valid': True
        }
    except Exception as e:
        return {
            'error': str(e),
            'mapped_keys': [],
            'value_mapping': {},
            'total_keys': 0,
            'input_type': type(input_data).__name__,
            'is_valid': False
        }
