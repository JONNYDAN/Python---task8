import streamlit as st
import os
from core import fetch_data, fetch_data_download, get_transcript, get_transcript_options, save_uploaded_file, generate_transcript_html, generate_transcript_html_speaker, generate_srt, generate_vtt, update_summarization, update_auto_chapters, update_dual_channel, update_speaker_labels
from contextlib import nullcontext
import threading
from constants import API_URL, LANGUAGE_CODES, CUSTOM_CSS, CUSTOM_JS

URL_TEMP = "../API/temp"

data = None
err = None
data_down = None
err_down = None
cancel_event = threading.Event()

# Initialize session state variables
if 'retry_button' not in st.session_state:
    st.session_state.retry_button = False
if 'model_type' not in st.session_state:
    st.session_state.model_type = "best"
if 'activated_sum' not in st.session_state:
    st.session_state.activated_sum = False
if 'activated_auto_chapters' not in st.session_state:
    st.session_state.activated_auto_chapters = False
    
if 'data' not in st.session_state:
    st.session_state.data = None
if 'data_down' not in st.session_state:
    st.session_state.data_down = None
if 'download_clicked' not in st.session_state:
    st.session_state.download_clicked = False
if 'selected_features' not in st.session_state:
    st.session_state.selected_features = None
    
if 'activated_pii' not in st.session_state:
    st.session_state.activated_pii = False
if 'activated_speaker' not in st.session_state:
    st.session_state.activated_speaker = False
if 'activated_dual' not in st.session_state:
    st.session_state.activated_dual = False
if 'activated_filter' not in st.session_state:
    st.session_state.activated_filter = False

# Function to handle download button click
def on_download_click():
    st.session_state.download_clicked = True
    
def on_submit_button():
    st.session_state.data_down = None
    st.session_state.data = None
     
# clean_files_after_setup_time(URL_TEMP, 250) #Xét theo giây

def save_url_audio(uploaded_file):
    # Lưu file vào thư mục tạm thời
    file_path = os.path.join(URL_TEMP, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Tạo URL cho file đã lưu
    audio_url = f"{API_URL}/temp/{uploaded_file.name}"
    return audio_url

def fetch_data_with_timeout():
    global data, err, data_down, err_down
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
        data_down, err_down = fetch_data_download(
            file_url
        )
    except Exception as e:
        err = str(e)
    if cancel_event.is_set():
        data = None
        err = "Request đã bị hủy."
        
def process_request():
    global data, err, data_down, err_down
    data = None
    err = None
    data_down = None
    err_down = None
    cancel_event = threading.Event()

    request_thread = threading.Thread(target=fetch_data_with_timeout)
    request_thread.start()

    with st.spinner('We’re running your file through our models. Please wait for a couple of minutes...'):
        request_thread.join(timeout=250)

    if request_thread.is_alive():
        cancel_event.set()
        st.write("Request đã hết thời gian chờ.")   
        data = None
        err = "Timeout"

def display_results(with_optional=False):
    left_paper = st.container()
    right_paper = None
               
    global data, err, data_down, err_down, cancel_event
    if not st.session_state.data:
       st.session_state.data = data 
    if not st.session_state.data_down:
        st.session_state.data_down = data_down
    if err:
        st.write(f"Lỗi khi gọi API: {err}")

        col1, col2 = st.columns([2, 2])
        with col1:
            if st.button("Cancel", use_container_width=True):
                st.write("Đã hủy yêu cầu.")
                cancel_event.set()
        with col2:
            st.button("Retry", key="retry_button", use_container_width=True, on_click=on_submit_button)
            
    if with_optional:
        left_paper, right_paper = st.columns([7, 3])            
    with left_paper:
        st.write(
            "<h5 style='color: #2545d3;'>Transcript</h5>",
            unsafe_allow_html=True
        )
        if  st.session_state.data_down:
            left_down, right_down = st.columns([2, 8])
            with left_down:
                # Lựa chọn định dạng tải xuống
                selected_format = st.selectbox(
                    "Please select download format:",
                    ("SRT", "VTT"),
                    key="method_format"
                )

                # Giả sử bạn đã có các hàm để tạo nội dung SRT và VTT
                # if selected_format == "SRT":
                data_content = generate_srt(st.session_state.data_down.get("srt"))
                name_file = "subtitles.srt"
                
                if selected_format == "VTT":
                    data_content = generate_vtt(st.session_state.data_down.get("vtt"))
                    name_file = "subtitles.vtt"
                    
                # Tạo nút tải xuống với định dạng tương ứng
                st.download_button(
                    label="Download File",
                    data=data_content,
                    file_name=name_file,
                    mime="text/plain",
                    on_click=on_download_click,
                )
            with right_down:
                st.write("")
        
        if st.session_state.data:
            
            if (st.session_state.activated_speaker or st.session_state.activated_dual) is not False:
                transcript_html = generate_transcript_html_speaker( st.session_state.data.get("utterance"))
                print (transcript_html)
            else:
                transcript_html = generate_transcript_html( st.session_state.data.get("transcript_words"))
                
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
            
    if right_paper is not None:            
        with right_paper:
            if st.session_state.data:
                # Lấy danh sách các tính năng đã chọn từ session
                selected_features = st.session_state.selected_features

                # Kiểm tra nếu "Summarization" được chọn
                if selected_features[0]:
                    if "summary" not in st.session_state:
                        st.session_state.summary = get_transcript_options(st.session_state.data, "summary")
                    with st.status("Summarization"):
                        st.write(st.session_state.summary)

                # Kiểm tra nếu "Topic Detection" được chọn
                if selected_features[1]:
                    if "topics" not in st.session_state:
                        st.session_state.topics = get_transcript_options(st.session_state.data, "topic")
                    with st.status("Topic Detection"):
                        st.write(st.session_state.topics)

                # Kiểm tra nếu "Auto Chapters" được chọn
                if selected_features[2]:
                    if "chapters" not in st.session_state:
                        st.session_state.chapters = get_transcript_options(st.session_state.data, "chapter")
                    with st.status("Auto Chapters"):
                        st.write(st.session_state.chapters)

                # Kiểm tra nếu "Content Moderation" được chọn
                if selected_features[3]:
                    if "content" not in st.session_state:
                        st.session_state.content = get_transcript_options(st.session_state.data, "content")
                    with st.status("Content Moderation"):
                        st.write(st.session_state.content)

                # Kiểm tra nếu "Important Phrases" được chọn
                if selected_features[4]:
                    if "phrases" not in st.session_state:
                        st.session_state.phrases = get_transcript_options(st.session_state.data, "phrases")
                    with st.status("Important Phrases"):
                        st.write(st.session_state.phrases)

                # Kiểm tra nếu "Sentiment Analysis" được chọn
                if selected_features[5]:
                    if "sentiment" not in st.session_state:
                        st.session_state.sentiment = get_transcript_options(st.session_state.data, "sentiment")
                    with st.status("Sentiment Analysis"):
                        st.write(st.session_state.sentiment)

                # Kiểm tra nếu "Entity Detection" được chọn
                if selected_features[6]:
                    if "entity" not in st.session_state:
                        st.session_state.entity = get_transcript_options(st.session_state.data, "entity")
                    with st.status("Entity Detection"):
                        st.write(st.session_state.entity)

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
            audio_url = save_url_audio(uploaded_file)
            
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
            activated_speaker = st.toggle("Speaker Labels", value=st.session_state.activated_speaker, on_change=update_speaker_labels)
            st.divider()
            activated_dual = st.toggle("Dual Channel", value=st.session_state.activated_dual, on_change=update_dual_channel)
            st.divider()
            activated_filter = st.toggle("Profanity Filtering")
            
            st.write('</div>', unsafe_allow_html=True)
        
        with st.container():
            st.write('<div class="submit-container">', unsafe_allow_html=True)
            submit_button = st.button("Transcribe File", disabled=uploaded_file is None, on_click=on_submit_button)
            st.write('</div>', unsafe_allow_html=True)

# Main section
with st.container():
    st.session_state.optional_selected = [activated_sum, activated_topic, activated_auto_chapters, activated_content,
                            activated_phrases, activated_sentiment, activated_entity]
    if (submit_button or st.session_state.retry_button) and uploaded_file is not None :
      
            
        file_url = save_uploaded_file(uploaded_file)
        
        st.session_state.selected_features = st.session_state.optional_selected

        process_request()
        display_results(any(st.session_state.optional_selected))
        
    
    else:
        if st.session_state.get("selected_features"):
            display_results(any(st.session_state.selected_features))
        else:
            st.write(
                "<h1 style='color: #2545d3;'>Try AssemblyAI's API in seconds</h1>",
                unsafe_allow_html=True
            )
            st.write("Access production-ready Speech AI models for speech recognition, speaker detection, audio summarization, and more. Test our API yourself with a pre-loaded audio file, or upload your own.")
