# API URL
API_URL = "http://127.0.0.1:8000"

LANGUAGE_CODES = {
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

CUSTOM_CSS = """
<style>
p{
    font-family: 'Arial', sans-serif; /* Set your desired font family */
}
audio{
    width: 100%;
}
.word {
    position: relative;
    padding: 2px 4px;
    border-radius: 4px;
    transition: background-color 0.1s ease;
    display: inline-block;
    font-family: 'Arial', sans-serif; /* Set your desired font family */
    font-size: 16px; /* Set the font size */
    color: rgb(49, 51, 63);
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

CUSTOM_JS = """
<script>
function highlightCurrentWord(audio) {
    const words = document.querySelectorAll('.word');
    let currentWordIndex = 0;

    audio.addEventListener('timeupdate', () => {
        const currentTime = audio.currentTime;
        // Remove highlight from all words
        words.forEach(word => word.classList.remove('highlight'));

        // Highlight the current word
        for (let i = 0; i < words.length; i++) {
            const wordElement = words[i];
            const startTime = parseFloat(wordElement.id.split('-')[1]);
            const endTime = (i < words.length - 1) ? parseFloat(words[i + 1].id.split('-')[1]) : audio.duration;

            if (currentTime >= startTime && currentTime < endTime) {
                wordElement.classList.add('highlight');
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const audio = document.getElementsByTagName("audio");
    highlightCurrentWord(audio[0]);
});
</script>
"""