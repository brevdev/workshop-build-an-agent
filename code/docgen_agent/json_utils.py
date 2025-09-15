"""
JSON parsing utilities for handling model responses in JSON mode.
"""

import json
import re
from typing import Type, TypeVar
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)


def extract_json_from_response(content: str) -> str:
    """
    Extract JSON content from model response that contains ```json blocks.
    
    Args:
        content: The raw content from the model response
        
    Returns:
        The extracted JSON string
        
    Raises:
        ValueError: If no JSON block is found or if JSON is invalid
    """
    # Look for ```json blocks (with various whitespace patterns)
    json_patterns = [
        r'```json\s*\n(.*?)\n```',  # Standard format
        r'```json\s*(.*?)```',      # Compact format
        r'```JSON\s*\n(.*?)\n```',  # Uppercase JSON
        r'```JSON\s*(.*?)```',      # Uppercase compact
    ]
    
    for pattern in json_patterns:
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            json_str = match.group(1).strip()
            # Validate that it's valid JSON
            try:
                json.loads(json_str)
                return json_str
            except json.JSONDecodeError as e:
                continue  # Try next pattern
    
    # Fallback 1: try to find JSON-like content between curly braces
    brace_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(brace_pattern, content, re.DOTALL)
    
    for match in matches:
        json_str = match.strip()
        try:
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError:
            continue
    
    # Fallback 2: more aggressive brace matching
    brace_pattern = r'\{.*\}'
    match = re.search(brace_pattern, content, re.DOTALL)
    
    if match:
        json_str = match.group(0).strip()
        try:
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON found in fallback search: {e}")
    
    raise ValueError(f"No JSON content found in response. Content: '{content[:200]}{'...' if len(content) > 200 else ''}'")


def parse_json_response(content: str, model_class: Type[T]) -> T:
    """
    Parse JSON response and create a Pydantic model instance.
    
    Args:
        content: The raw content from the model response
        model_class: The Pydantic model class to instantiate
        
    Returns:
        An instance of the model_class
        
    Raises:
        ValueError: If JSON parsing or model validation fails
    """
    json_str = extract_json_from_response(content)
    
    try:
        json_data = json.loads(json_str)
        return model_class(**json_data)
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        raise ValueError(f"Failed to parse JSON response into {model_class.__name__}: {e}")
