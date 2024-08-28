import streamlit as st
import os
from execute import fetch_data, get_transcript, fetch_data_options, get_transcript_options
import tempfile
    

def save_uploaded_file(uploaded_file):
    """Save the uploaded file to a temporary file and return its path."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        tmp_file.write(uploaded_file.read())
        return tmp_file.name

st.set_page_config(page_title="Streamline Analyst", page_icon=":rocket:", layout="wide")
with open('styles.css', 'r', encoding='utf-8') as f:
    css = f.read()

st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

# Directory to save uploaded files
UPLOAD_DIRECTORY = "media/"

# Ensure the upload directory exists
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

with st.sidebar:
    with st.container(border=True):
        st.write('<div class="paper">', unsafe_allow_html=True)
                
        # File uploader for MP4 or MP3
        uploaded_file = st.file_uploader("Upload audio file to transcribe (WAV/MP3):", 
                                         type=["wav", "mp3"], key="file_uploader", accept_multiple_files=False)
        
        st.write("Model Tier")
        
        left_model, right_model = st.columns([5, 5])
        if "model_type" not in st.session_state:
            st.session_state.model_type = "best"
            
        with left_model:
            best_button = st.button("Best", key="best_button", help="**Best**: Highest accuracy, most advanced capabilities.", use_container_width=True)
        with right_model:
            nano_button = st.button("Nano", key="nano_button", help="**Nano**: Lightweight, combination of accuracy and speed.", use_container_width=True)
        if best_button:
            st.session_state.model_type = "best"
        elif nano_button:
            st.session_state.model_type = "nano"
        # Kiểm tra kết quả
        st.write(f"Model type selected: **{st.session_state.model_type}**")
        model_type = st.session_state.model_type
        
        language_codes = {
            "Automatic Language Detection": "auto",
            "Global English": "en",
            "American English": "en_us",
            "Australian English": "en_au",
            "British English": "en_uk",
            "Chinese": "zh",
            "Dutch": "nl",
            "Finnish": "fi",
            "French": "fr",
            "German": "de",
            "Hindi": "hi",
            "Italian": "it",
            "Japanese": "ja",
            "Korean": "ko",
            "Polish": "pl",
            "Portuguese": "pt",
            "Russian": "ru",
            "Spanish": "es",
            "Turkish": "tr",
            "Ukrainian": "uk",
            "Vietnamese": "vi"
        }
        selected_language = st.selectbox(
            "Upload audio file to transcribe:",
            language_codes.keys(),
            key="method_language"
        )
        language_code = language_codes[selected_language]
        st.write(f"Selected language code: **{language_code}**")
        st.divider()
        
        st.write(
            "<span style='color: #2545d3;'>Select additional capabilities (optional)</span>",
            unsafe_allow_html=True
        )
        
        with st.container():
            st.write('<div class="toggle-container">', unsafe_allow_html=True)
            
            if 'activated_sum' not in st.session_state:
                st.session_state.activated_sum = False
            if 'activated_auto_chapters' not in st.session_state:
                st.session_state.activated_auto_chapters = False
            if 'activated_dual_channel' not in st.session_state:
                st.session_state.activated_dual_channel = False
            if 'activated_speaker_labels' not in st.session_state:
                st.session_state.activated_speaker_labels = False

            def update_summarization():
                st.session_state.activated_sum = not st.session_state.activated_sum
                if st.session_state.activated_sum:
                    st.session_state.activated_auto_chapters = False

            def update_auto_chapters():
                st.session_state.activated_auto_chapters = not st.session_state.activated_auto_chapters
                if st.session_state.activated_auto_chapters:
                    st.session_state.activated_sum = False
            def update_dual_channel():
                st.session_state.activated_dual_channel = not st.session_state.activated_dual_channel
                if st.session_state.activated_dual_channel:
                    st.session_state.activated_speaker_labels = False

            def update_speaker_labels():
                st.session_state.activated_speaker_labels = not st.session_state.activated_speaker_labels
                if st.session_state.activated_speaker_labels:
                    st.session_state.activated_dual_channel = False

            activated_sum = st.toggle("Summarization", value=st.session_state.activated_sum, on_change=update_summarization)
            st.divider()

            activated_topic = st.toggle("Topic Detection")
            st.divider()

            activated_auto_chapters = st.toggle("Auto Chapters", value=st.session_state.activated_auto_chapters, on_change=update_auto_chapters)
            st.divider()
            activated_content = st.toggle("Content Moderation")
            st.divider()
            activated_phrases = st.toggle("Important Phrases")
            st.divider()
            activated_sentiment = st.toggle("Sentiment Analysis")
            st.divider()
            activated_entity = st.toggle("Entity Detection")
            st.divider()
            activated_pii = st.toggle("PII Redaction")
            st.divider()
            activated_speaker = st.toggle("Speaker Labels", value=st.session_state.activated_speaker_labels, on_change=update_speaker_labels)
            st.divider()
            activated_dual = st.toggle("Dual Channel", value=st.session_state.activated_dual_channel, on_change=update_dual_channel)
            st.divider()
            activated_filter = st.toggle("Profanity Filtering")
            
            st.write('</div>', unsafe_allow_html=True)
        
        with st.container():
            st.write('<div class="submit-container">', unsafe_allow_html=True)
            submit_button = st.button("Transcribe File", disabled=uploaded_file is None)
            st.write('</div>', unsafe_allow_html=True)
# Main section
with st.container():
    if submit_button and uploaded_file is not None:
        left_paper, right_paper = st.columns([7, 3])
        with st.spinner('Processing...'):
            
            file_url = save_uploaded_file(uploaded_file)
            data, err = fetch_data(file_url,
                                   activated_pii,
                                   activated_speaker,
                                   activated_dual,
                                   activated_filter,
                                   model_type,
                                   language_code
                                   )
            data_options, err_options  = fetch_data_options(file_url, 
                                                   activated_sum, 
                                                   activated_topic, 
                                                   activated_auto_chapters, 
                                                   activated_content, 
                                                   activated_phrases,
                                                   activated_sentiment,
                                                   activated_entity
                                                   )
            
            if err:
                st.error(f"Error fetching data: {err}")
            
            if err_options:
                st.error(f"Error fetching data options: {err_options}")
            
            with left_paper:
                
                st.divider()
                st.audio(uploaded_file, format="audio/mpeg")
                st.divider()

                if data:
                    transcript = get_transcript(data)
                    st.write(transcript)
                else:
                    st.error(f"Error fetching data: {err}")
                    
            with right_paper:
                if activated_sum is not False:
                    summary = get_transcript_options(data_options, "summary")
                    with st.status("Summarization"):
                        st.write(summary)
                if activated_topic is not False:
                    topics = get_transcript_options(data_options, "topic")
                    with st.status("Topic Detection"):
                        st.write(topics)
                if activated_auto_chapters is not False:
                    chapters = get_transcript_options(data_options, "chapter")
                    with st.status("Auto Chapters"):
                        st.write(chapters)
                if activated_content is not False:
                    content = get_transcript_options(data_options, "content")
                    with st.status("Content Moderation"):
                        st.write(content)
                if activated_phrases is not False:
                    phrases = get_transcript_options(data_options, "phrases")
                    with st.status("Content Moderation"):
                        st.write(phrases)
                if activated_sentiment is not False:
                    sentiment = get_transcript_options(data_options, "sentiment")
                    with st.status("Sentiment Analysis"):
                        st.write(sentiment)
                if activated_entity is not False:
                    entity = get_transcript_options(data_options, "entity")
                    with st.status("Entity Detection"):
                        st.write(entity)
                    
    else:   
        st.write(
            "<h1 style='color: #2545d3;'>Try AssemblyAI's API in seconds</h1>",
            unsafe_allow_html=True
        )
        st.write("Access production-ready Speech AI models for speech recognition, speaker detection, audio summarization, and more. Test our API yourself with a pre-loaded audio file, or upload your own.")


                        
