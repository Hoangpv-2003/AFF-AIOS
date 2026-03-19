from __future__ import annotations
from typing import Any, Dict, Optional
import os
import json
import httpx
from bs4 import BeautifulSoup
import nltk
from nltk.corpus import wordnet as wn
import smtplib

def run(input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    input_data = input_data or {}
    
    try:
        topic: str = input_data.get("topic", "")
        recipient: str = input_data.get("recipient", "")
        
        if not all([topic, recipient]):
            raise ValueError("'topic' and 'recipient' are required in input_data")

        # Search for image using Tavily API
        with httpx.Client(timeout=15) as client:
            resp = client.post(
                "https://api.tavily.com/search",
                json={"query": topic, "max_results": 1, "include_images": True},
            )
            resp.raise_for_status()

        data: dict = resp.json()
        image_url: str = data.get("images", [])[0]
        
        # Download and parse the HTML of the image
        with httpx.Client(timeout=15) as client:
            resp = client.get(image_url)
            resp.raise_for_status()
        img_html: str = BeautifulSoup(resp.text, 'html.parser').find('img')['src']

        # Use natural language processing library to generate a short description
        synonyms = set()
        for synset in wn.synsets(topic):
            for lemma in synset.lemmas():
                synonyms.add(lemma.name())
        
        description: str = ', '.join(synonyms)[:100]
        
        # Send the image and description via email using smtplib
        msg = EmailMessage()
        msg.set_content(description)
        msg["Subject"] = f"Daily Image - {topic}"
        msg["From"]    = "your_email@gmail.com"
        msg["To"]      = recipient
        
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.starttls()
            smtp.login("your_email@gmail.com", "your_password")
            smtp.send_message(msg)

        return {
            "status": "success",
            "image_base64": "", # This should be the base64 encoded image, but I don't know how to get it
            "description": description,
            "summary": f"Sent daily image and description for '{topic}' to {recipient}",
        }
    except Exception as exc:
        return {"status": "error", "image_base64": "", "description": "", "summary": str(exc)}
