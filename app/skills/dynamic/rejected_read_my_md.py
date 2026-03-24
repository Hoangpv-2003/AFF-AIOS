from typing import Dict, Any, Optional
import os

def run(input_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    input_data = input_data or {}
    file_path = input_data.get('file_path')
    if not file_path:
        return {
            'status': 'error',
            'summary': 'Missing file_path in input data',
            'error_reason': 'The required parameter "file_path" is missing.'
        }
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        return {
            'status': 'success',
            'summary': 'Markdown file read successfully',
            'content': content
        }
    except Exception as e:
        return {
            'status': 'error',
            'summary': f'Failed to read markdown file: {str(e)}',
            'error_reason': str(e)
        }