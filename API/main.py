import assemblyai as aai
import re
from fastapi import FastAPI, File, UploadFile, Query, HTTPException
from pydantic import BaseModel

app = FastAPI()

aai.settings.api_key = "edd915cdc8014f9db7190b8a38c0ff28"
headers = {"authorization": "edd915cdc8014f9db7190b8a38c0ff28"}

# Define a Pydantic model for the request body
class TranscriptionRequest(BaseModel):
    audio_url: str
    pii_redaction: bool = False
    speaker_labels: bool = False
    dual_channel: bool = False
    filter_profanity: bool = False
    model_type: str = "nano"  # Default to 'nano'
    language_code: str = "auto"  # Default to 'auto'

class ParseRequest(BaseModel):
    audio_url: str
    summarization: bool = False
    iab_categories: bool = False
    auto_chapters: bool = False
    content_safety: bool = False
    auto_highlights: bool = False
    sentiment_analysis: bool = False
    entity_detection: bool = False


@app.post("/")
async def root(request: TranscriptionRequest):
    transcriber = aai.Transcriber()

    # Determine the speech model based on the user's selection
    speech_model = aai.SpeechModel.best if request.model_type == "best" else aai.SpeechModel.nano

    # Set language detection to False if a specific language code is provided
    language_detection = request.language_code == "auto"

    # Initialize the transcription configuration
    config = aai.TranscriptionConfig(
        speech_model=speech_model,
        language_detection=language_detection,
        speaker_labels=request.speaker_labels,
        dual_channel=request.dual_channel,
        filter_profanity=request.filter_profanity,
        language_code=request.language_code if not language_detection else None
    )

    # Apply PII redaction if requested
    if request.pii_redaction:
        config.set_redact_pii(
            policies=[
                aai.PIIRedactionPolicy.medical_condition,
                aai.PIIRedactionPolicy.email_address,
                aai.PIIRedactionPolicy.phone_number,
                aai.PIIRedactionPolicy.banking_information,
                aai.PIIRedactionPolicy.credit_card_number,
                aai.PIIRedactionPolicy.credit_card_cvv,
                aai.PIIRedactionPolicy.date_of_birth,
                aai.PIIRedactionPolicy.person_name  
            ],
            substitution=aai.PIISubstitutionPolicy.hash
        )

    try:
        # Transcribe the audio using the provided configuration
        transcript = transcriber.transcribe(request.audio_url, config)

        # Format the transcript based on speaker labels or dual-channel
        if request.speaker_labels or request.dual_channel:
            result = ""
            for utterance in transcript.utterances:
                result += f"**Speaker {utterance.speaker}:** {utterance.text}\n\n"
            return {"transcript": result}

        # Return the plain transcript
        return {"transcript": transcript.text}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/parse")
async def parse(request: ParseRequest):
    topics = []
    chapters = []
    content = []
    key_phrases = []
    # Khởi tạo biến đếm
    count_positive = 0
    count_neutral = 0
    count_negative = 0
    # Khởi tạo dictionary để lưu các loại thực thể
    entities = {
        "Location": [],
        "Person_name": [],
        "Occupation": [],
        "Organization": [],
        "Nationality": [],
        "Duration": [],
        "Medical_condition": []
    }    
    
    if request.summarization:
        request.auto_chapters = False
    elif request.auto_chapters:
        request.summarization = False
        
    config = aai.TranscriptionConfig(
        summary_model=aai.SummarizationModel.informative,
        summary_type=aai.SummarizationType.bullets,
        summarization=request.summarization,
        iab_categories=request.iab_categories,
        auto_chapters=request.auto_chapters,
        content_safety=request.content_safety,
        auto_highlights=request.auto_highlights,
        sentiment_analysis=request.sentiment_analysis,
        entity_detection=request.entity_detection
        )

    transcript = aai.Transcriber().transcribe(request.audio_url, config)
    
    if request.iab_categories:   
        for topic, relevance in transcript.iab_categories.summary.items():
            if relevance > 0.8:
                refined_topic = ' '.join(re.split('(?=[A-Z])', topic.split('>')[-1])).strip()
                topics.append(refined_topic)

        topics_str = " \n - ".join(topics)
        topics_str = f"- {topics_str}"
    
    if request.auto_chapters:
        for chapter in transcript.chapters:
            refined_chapter = f"- {chapter.headline}"
            chapters.append(refined_chapter)
        
        chapter_str = " \n ".join(chapters)
    
    if request.content_safety:
        for result in transcript.content_safety.results:
            for label in result.labels:
                result_text = f"**{label.label}**\n{result.text}"
                content.append(result_text)

        content_str = "\n\n".join(content)
    
    if request.auto_highlights:
        for result in transcript.auto_highlights.results:
            phrase_text = result.text
            key_phrases.append(phrase_text)
        phrase_str = "\n\n".join(key_phrases)
    
    if request.sentiment_analysis:
        for sentiment_result in transcript.sentiment_analysis:
            if sentiment_result.sentiment == "POSITIVE":
                count_positive += 1
            elif sentiment_result.sentiment == "NEUTRAL":
                count_neutral += 1
            elif sentiment_result.sentiment == "NEGATIVE":
                count_negative += 1
            sentiment_str = f"We identified **{count_positive}** positive sentences, and **{count_negative}** negative ones."
    
    if request.entity_detection:
        for entity in transcript.entities:
            entity_text = entity.text.strip()
            entity_type = entity.entity_type.value

            if entity_type == "location":
                entities["Location"].append(entity_text)
            elif entity_type == "person_name":
                entities["Person_name"].append(entity_text)
            elif entity_type == "occupation":
                entities["Occupation"].append(entity_text)
            elif entity_type == "organization":
                entities["Organization"].append(entity_text)
            elif entity_type == "nationality":
                entities["Nationality"].append(entity_text)
            elif entity_type == "duration":
                entities["Duration"].append(entity_text)
            elif entity_type == "medical_condition":
                entities["Medical_condition"].append(entity_text)
        entity_str = ""
        for entity_type, entity_list in entities.items():
            entity_str += f"**{entity_type}:**\n {', '.join(entity_list)}\n\n"     
            
    return {"summary": transcript.summary ,
            "topic": topics_str if request.iab_categories else "", 
            "chapter": chapter_str if request.auto_chapters else "",
            "content": content_str if request.content_safety else "",
            "phrases": phrase_str if request.auto_highlights else "",
            "sentiment": sentiment_str if request.sentiment_analysis else "",
            "entity": entity_str if request.entity_detection else ""}

