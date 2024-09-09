import requests
import streamlit as st
import tempfile
import os
import time
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
    
def fetch_data_download(audio_str):
    response = requests.post(
        f"{API_URL}/download", 
        json={
            "audio_url": audio_str,
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

def save_uploaded_file(uploaded_file):
    """Save the uploaded file to a temporary file and return its path."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        tmp_file.write(uploaded_file.read())
        return tmp_file.name
    
def generate_transcript_html(transcript_words):
    html = '<div>'
    for word_data in transcript_words:
        start_time_sec = word_data["start"] / 1000
        html += f'<span id="word-{start_time_sec}" class="word">{word_data["text"]} </span>'
    html += '</div>'
    return html

def generate_transcript_html_speaker(utterance):
    html = '<div>'
    for speaker_data in utterance:
        html += f'<p><b> Speaker {speaker_data["speaker"]} </b></p>'
        for word_data in speaker_data["words"]:
            start_time_sec = word_data["start"] / 1000
            html += f'<span id="word-{start_time_sec}" class="word">{word_data["text"]} </span>'
    html += '</div>'
    return html

def generate_srt(srt_text):
    return srt_text

def generate_vtt(vtt_text):
    return vtt_text

def clean_files_after_setup_time(folder_path, setup_time_in_seconds):
    current_time = time.time()

    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)

        if os.path.isfile(file_path):
            file_mod_time = os.path.getmtime(file_path)

            if current_time - file_mod_time > setup_time_in_seconds:
                os.remove(file_path)


