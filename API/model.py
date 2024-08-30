from typing import Any
from pydantic import BaseModel

# Define a Pydantic model for the request body
class TranscriptionRequest(BaseModel):
    audio_url: str
    pii_redaction: bool = False
    speaker_labels: bool = False
    dual_channel: bool = False
    filter_profanity: bool = False
    model_type: str = "best"  # Default to 'best'
    language_code: str = "auto"  # Default to 'auto'
    summarization: bool = False
    iab_categories: bool = False
    auto_chapters: bool = False
    content_safety: bool = False
    auto_highlights: bool = False
    sentiment_analysis: bool = False
    entity_detection: bool = False
    
    