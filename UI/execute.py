import requests
import streamlit as st
from constants import API_URL

def fetch_data(audio_str,
               pii_redaction,
               speaker_labels,
               dual_channel,
               filter_profanity,
               model_type,
               language_code,
               summarization, 
               iab_categories, 
               auto_chapters, 
               content_safety, 
               auto_highlights, 
               sentiment_analysis,
               entity_detection
               ):
    response = requests.post(
        f"{API_URL}/parse", 
        json={
            "audio_url": audio_str,
            "pii_redaction": pii_redaction,
            "speaker_labels": speaker_labels,
            "dual_channel": dual_channel,
            "filter_profanity": filter_profanity,
            "model_type": model_type,
            "language_code": language_code,
            "summarization": summarization,
            "iab_categories": iab_categories,
            "auto_chapters": auto_chapters,
            "content_safety": content_safety,
            "auto_highlights": auto_highlights,
            "sentiment_analysis": sentiment_analysis,
            "entity_detection": entity_detection
        }
    )
    
    try:
        response.raise_for_status()
        data = response.json()
        return data, None
    except Exception as err:
        return None, err


def get_transcript(data):
    # Extract transcript from the data dictionary
    transcript = data.get("transcript", "No transcript available.")
    return transcript

def get_transcript_options(data, option):
    if data is None:
        return "No data available."
    
    # Sử dụng phương thức get để tránh lỗi KeyError
    transcript = data.get(option, "No options available.")
    return transcript
