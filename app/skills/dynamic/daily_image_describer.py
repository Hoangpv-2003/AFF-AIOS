from __future__ import annotations
from typing import Any, Dict, Optional
import os
import httpx


def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    
    try:
        image_metadata: dict = input_data.get("image_metadata", {})
        
        if not image_metadata:
            raise ValueError("'image_metadata' is required in input_data")
        
        description: str = ""
        # This implementation uses a placeholder function to generate the description.
        # The actual implementation may require more complex natural language processing (NLP) techniques
        # or machine learning models to accurately describe the images based on their metadata.
        if "title" in image_metadata:
            description += f"The image is titled '{image_metadata['title']}'. "
        if "description" in image_metadata:
            description += f"It has a description: '{image_metadata['description']}'"
        
        return {
            "status": "success",
            "image_description": description,
            "summary": f"Generated short description for the image metadata.",
        }
    except Exception as exc:
        return {"status": "error", "image_description": "", "summary": str(exc)}
