import streamlit as st
import os
from core import fetch_data, get_transcript, get_transcript_options, save_uploaded_file, generate_transcript_html, generate_transcript_html_speaker
from contextlib import nullcontext
import threading
from constants import API_URL, LANGUAGE_CODES, CUSTOM_CSS, CUSTOM_JS

data = None
err = None
cancel_event = threading.Event()

def process_request():
    global data, err
    data = None
    err = None
    cancel_event = threading.Event()

    def fetch_data_with_timeout():
        global data, err
        try:
            data, err = fetch_data(
                file_url,
                activated_pii,
                activated_speaker,
                activated_dual,
                activated_filter,
                model_type,
                language_code,
                activated_sum,
                activated_topic,
                activated_auto_chapters,
                activated_content,
                activated_phrases,
                activated_sentiment,
                activated_entity
            )
        except Exception as e:
            err = str(e)
        if cancel_event.is_set():
            data = None
            err = "Request đã bị hủy."

    request_thread = threading.Thread(target=fetch_data_with_timeout)
    request_thread.start()

    with st.spinner('We’re running your file through our models. Please wait for a couple of minutes...'):
        request_thread.join(timeout=120)

    if request_thread.is_alive():
        cancel_event.set()
        st.write("Request đã hết thời gian chờ.")   
        data = None
        err = "Timeout"

def display_results():
    global data, err, cancel_event

    if err:
        st.write(f"Lỗi khi gọi API: {err}")

        col1, col2 = st.columns([2, 2])
        with col1:
            if st.button("Cancel", use_container_width=True):
                st.write("Đã hủy yêu cầu.")
                cancel_event.set()
        with col2:
            st.button("Retry", key="retry_button", use_container_width=True)
                
    else:
        with left_paper:
            st.write(
                "<h5 style='color: #2545d3;'>Transcript</h5>",
                unsafe_allow_html=True
            )

            if data:
                if (activated_speaker or activated_dual) is not False:
                    transcript_html = generate_transcript_html_speaker(data.get("utterance"))
                    print (transcript_html)
                else:
                    transcript_html = generate_transcript_html(data.get("transcript_words"))
                    
                full_html = f"""
                {CUSTOM_CSS}
                <hr>
                <audio controls>
                    <source src="{audio_url}" type="audio/wav">
                </audio>
                <hr>
                
                <div class="container-transcript" style="font-size: 18px;">
                    {transcript_html}
                </div>
                {CUSTOM_JS}
                """
                st.components.v1.html(full_html, height=800)
                
        if right_paper:            
            with right_paper:
                if data:
                    if activated_sum:
                        summary = get_transcript_options(data, "summary")
                        with st.status("Summarization"):
                            st.write(summary)
                    if activated_topic:
                        topics = get_transcript_options(data, "topic")
                        with st.status("Topic Detection"):
                            st.write(topics)
                    if activated_auto_chapters:
                        chapters = get_transcript_options(data, "chapter")
                        with st.status("Auto Chapters"):
                            st.write(chapters)
                    if activated_content:
                        content = get_transcript_options(data, "content")
                        with st.status("Content Moderation"):
                            st.write(content)
                    if activated_phrases:
                        phrases = get_transcript_options(data, "phrases")
                        with st.status("Important Phrases"):
                            st.write(phrases)
                    if activated_sentiment:
                        sentiment = get_transcript_options(data, "sentiment")
                        with st.status("Sentiment Analysis"):
                            st.write(sentiment)
                    if activated_entity:
                        entity = get_transcript_options(data, "entity")
                        with st.status("Entity Detection"):
                            st.write(entity)

# Initialize session state variables
if 'retry_button' not in st.session_state:
    st.session_state.retry_button = False
if 'model_type' not in st.session_state:
    st.session_state.model_type = "best"
if 'activated_sum' not in st.session_state:
    st.session_state.activated_sum = False
if 'activated_auto_chapters' not in st.session_state:
    st.session_state.activated_auto_chapters = False
if 'activated_dual_channel' not in st.session_state:
    st.session_state.activated_dual_channel = False

st.set_page_config(page_title="Streamline Analyst", page_icon=":rocket:", layout="wide")
with open('styles.css', 'r', encoding='utf-8') as f:
    css = f.read()

st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

with st.sidebar:
    with st.container(border=True):
        st.write('<div class="paper">', unsafe_allow_html=True)
                
        # File uploader for MP4 or MP3
        uploaded_file = st.file_uploader("Upload audio file to transcribe (WAV/MP3):", 
                                         type=["wav", "mp3"], key="file_uploader", accept_multiple_files=False)
        if uploaded_file is not None:
            # Lưu file vào thư mục tạm thời
            file_path = os.path.join("../API/temp", uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Tạo URL cho file đã lưu
            audio_url = f"{API_URL}/temp/{uploaded_file.name}"
            
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
        
        
        selected_language = st.selectbox(
            "Upload audio file to transcribe:",
            LANGUAGE_CODES.keys(),
            key="method_language"
        )
        language_code = LANGUAGE_CODES[selected_language]
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
    if (submit_button or st.session_state.retry_button) and uploaded_file is not None:
        optional_selected = [activated_sum, activated_topic, activated_auto_chapters, activated_content,
                             activated_phrases, activated_sentiment, activated_entity]
        
        if any(optional_selected):
            left_paper, right_paper = st.columns([7, 3])
        else:
            left_paper = st.container()
            right_paper = None
            
        file_url = save_uploaded_file(uploaded_file)

        process_request()
        display_results()
    else:   
        st.write(
            "<h1 style='color: #2545d3;'>Try AssemblyAI's API in seconds</h1>",
            unsafe_allow_html=True
        )
        st.write("Access production-ready Speech AI models for speech recognition, speaker detection, audio summarization, and more. Test our API yourself with a pre-loaded audio file, or upload your own.")
