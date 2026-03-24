from typing import Dict, Any, Optional
import os
import logging

logging.basicConfig(level=logging.INFO)

def run(input_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    input_data = input_data or {}
    directory_path = input_data.get('directory_path')
    locale = input_data.get('runtime_context', {}).get('locale', 'en-US')

    if not directory_path:
        return {
            'status': 'error',
            'summary': 'Missing directory path parameter',
            'error_reason': 'directory_path is required'
        }

    try:
        if not os.path.exists(directory_path):
            return {
                'status': 'error',
                'summary': 'Directory does not exist',
                'error_reason': f'Path {directory_path} not found'
            }
        if not os.access(directory_path, os.R_OK):
            return {
                'status': 'error',
                'summary': 'Permission denied to read directory',
                'error_reason': f'No read access for {directory_path}'
            }

        files = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
        txt_files = [f for f in files if f.endswith('.txt')]
        
        file_report = []
        total_size = 0
        
        for file_name in txt_files:
            file_path = os.path.join(directory_path, file_name)
            try:
                file_size = os.path.getsize(file_path)
                total_size += file_size
                file_report.append(f'{file_name} ({file_size} bytes)')
            except OSError as e:
                return {
                    'status': 'error',
                    'summary': 'Error accessing file details',
                    'error_reason': str(e)
                }

        if not txt_files:
            return {
                'status': 'success',
                'summary': 'No text files found in directory',
                'file_report': file_report
            }

        return {
            'status': 'success',
            'summary': f'Found {len(txt_files)} text files in directory',
            'file_report': file_report,
            'total_size': total_size
        }
    except Exception as e:
        return {
            'status': 'error',
            'summary': 'Unexpected error occurred',
            'error_reason': str(e)
        ]