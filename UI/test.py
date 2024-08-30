import streamlit as st
import time
import assemblyai as aai

aai.settings.api_key = "edd915cdc8014f9db7190b8a38c0ff28"

# Function to generate the HTML for the transcript
def generate_transcript_html(transcript_words):
    html = '<div>'
    html += ''
    for word_data in transcript_words:
        html += f'<span id="word-{word_data.start/1000}" class="word">{word_data.text} </span>'
    html += '</div>'
    return html

# Sample transcript data with timestamps

audio_url = "https://github.com/AssemblyAI-Community/audio-examples/raw/main/20230607_me_canadian_wildfires.mp3"
transcriber = aai.Transcriber()
transcript = transcriber.transcribe(audio_url)
# Generate the transcript HTML
print(transcript.words)
transcript_html = generate_transcript_html(transcript.words)

# Add custom CSS to highlight the current word
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

# Combine CSS and JS with transcript HTML
full_html = f"""
{custom_css}
<audio controls>
  <source src="{audio_url}" type="audio/wav">
  Your browser does not support the audio element.
</audio>
<div class="container-transcript" style="font-size: 18px;">
    {transcript_html}
</div>
{custom_js}
"""
# Display the transcript in Streamlit
st.components.v1.html(full_html, height=1000)
