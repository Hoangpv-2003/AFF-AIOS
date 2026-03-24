from typing import Dict, Any, Optional
import re
import locale

locale.setlocale(locale.LC_TIME, ('en_US', 'UTF-8'))

def run(input_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    input_data = input_data or {}
    try:
        results = input_data.get('results')
        if not results or not isinstance(results, list):
            return {
                'status': 'error',
                'summary': 'No results provided for processing',
                'error_reason': 'Missing or invalid results data'
            }

        summary_parts = []
        currency_pattern = r'\$|€|£|¥|₹|₽'  # Handle common currency symbols
        for result in results:
            text = str(result.get('content', ''))
            
            # Extract numeric values with currency symbols and units
            matches = re.findall(r'(\d+\.?\d*)\s*(\$|€|£|¥|₹|₽|USD|EUR|GBP|JPY|INR|RUB)', text, re.IGNORECASE)
            for value, unit in matches:
                formatted_value = f'{value} {unit}'
                summary_parts.append(formatted_value)

        if not summary_parts:
            return {
                'status': 'error',
                'summary': 'No numeric data found in results',
                'error_reason': 'No valid revenue data extracted'
            }

        summary = ' '.join(summary_parts)
        return {
            'status': 'success',
            'summary': summary
        }
    except Exception as e:
        return {
            'status': 'error',
            'summary': f'Error processing data: {str(e)}',
            'error_reason': f'Uncaught exception: {str(e)}'
        }