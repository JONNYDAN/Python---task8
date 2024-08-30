import streamlit as st
import os
from execute import fetch_data, get_transcript, get_transcript_options
import tempfile
    

def save_uploaded_file(uploaded_file):
    """Save the uploaded file to a temporary file and return its path."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        tmp_file.write(uploaded_file.read())
        return tmp_file.name
    
def generate_transcript_html(transcript_words):
    html = '<div>'
    html += ''
    for word_data in transcript_words:
        html += f'<span id="word-{word_data["start"]/1000}" class="word">{word_data["text"]} </span>'
    html += '</div>'
    return html

custom_css = """
<style>
.word {
    position: relative;
    padding: 2px 4px;
    border-radius: 4px;
    transition: background-color 0.1s ease;
    display: inline-block;
}
.highlight {
    background-color: #2545d3;
    color: white;
}
.container-transcript{
    max-height : 600px;
    overflow-y: auto;
}
</style>
"""

# Add JavaScript to handle audio playback and highlight the current word
custom_js = """
<script>
console.log("abc")
function highlightCurrentWord(audio) {
    const words = document.querySelectorAll('.word');
    let currentWordIndex = 0;

    audio.addEventListener('timeupdate', () => {
        const currentTime = audio.currentTime;
        console.log(currentTime);
        // Remove highlight from all words
        words.forEach(word => word.classList.remove('highlight'));

        // Highlight the current word
        for (let i = 0; i < words.length; i++) {
            const wordElement = words[i];
            const startTime = parseFloat(wordElement.id.split('-')[1]);
            const endTime = (i < words.length - 1) ? parseFloat(words[i + 1].id.split('-')[1]) : audio.duration;

            if (currentTime >= startTime && currentTime < endTime) {
                wordElement.classList.add('highlight');
                break;
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const audio = document.getElementsByTagName("audio");
    console.log("123")
    console.log(audio[0])
    highlightCurrentWord(audio[0]);
});
</script>
"""

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
        # Determine column layout based on selected options
        optional_selected = [activated_sum, activated_topic, activated_auto_chapters, activated_content,
                             activated_phrases, activated_sentiment, activated_entity, activated_pii, 
                             activated_speaker, activated_dual, activated_filter]
        
        if any(optional_selected):
            # If any of the optional capabilities are selected except for the specific ones
            left_paper, right_paper = st.columns([7, 3])
        else:
            # Default layout
            left_paper = st.container()
            right_paper = None
        
        with st.spinner('We’re running your file through our models. Please wait for a couple of minutes...'):
            
            file_url = save_uploaded_file(uploaded_file)
            data, err = fetch_data(file_url,
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
            print(data.get("transcript_words"))
            
            if right_paper:
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
            else:
                with left_paper:
                    # st.divider()
                    # st.audio(uploaded_file, format="audio/mpeg")
                    # st.divider()

                    if data:
                        # transcript = get_transcript(data)
                        # st.write(transcript)
                        
                        transcript_html = generate_transcript_html(data.get("transcript_words"))
                        full_html = f"""
                        {custom_css}
                        <audio controls>
                        <source src="{file_url}" type="audio/wav">
                        Your browser does not support the audio element.
                        </audio>
                        <div class="container-transcript" style="font-size: 18px;">
                            {transcript_html}
                        </div>
                        {custom_js}
                        """
                        # Display the transcript in Streamlit
                        st.components.v1.html(full_html, height=1000)
                    
    else:   
        st.write(
            "<h1 style='color: #2545d3;'>Try AssemblyAI's API in seconds</h1>",
            unsafe_allow_html=True
        )
        st.write("Access production-ready Speech AI models for speech recognition, speaker detection, audio summarization, and more. Test our API yourself with a pre-loaded audio file, or upload your own.")
