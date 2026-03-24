import os
import httpx
from typing import Optional, Dict, Any

def run(input_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    input_data = input_data or {}
    
    # Validate presence of required 'topic' key
    if 'topic' not in input_data:
        return {
            'status': 'error',
            'summary': 'Missing topic parameter',
            'error_reason': 'Input data missing required key "topic"'
        }
    
    topic = input_data['topic']
    
    # Retrieve API key from environment variable
    api_key = os.getenv('TAVILY_API_KEY')
    if not api_key:
        return {
            'status': 'error',
            'summary': 'Missing API key',
            'error_reason': 'Environment variable TAVILY_API_KEY is not set'
        }
    
    try:
        # Make a synchronous POST request using httpx
        with httpx.Client() as client:
            response = client.post(
                'https://api.tavily.com/search',
                json={'topic': topic},
                headers={'Authorization': f'Bearer {api_key}'}
            )
            response.raise_for_status()
            
            # Return the result
            return {
                'status': 'success',
                'summary': 'Weather data fetched successfully',
                'weather_data': response.json()
            }
    
    except httpx.RequestError as e:
        return {
            'status': 'error',
            'summary': 'Failed to fetch weather data',
            'error_reason': str(e)
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'summary': 'An unexpected error occurred',
            'error_reason': str(e)
        }