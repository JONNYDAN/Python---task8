import assemblyai as aai
import re
from fastapi import FastAPI, File, UploadFile, Query
import requests

app = FastAPI()

aai.settings.api_key = "edd915cdc8014f9db7190b8a38c0ff28"
# Upload the file to AssemblyAI or another service to get FILE_URL
url = "https://api.assemblyai.com/v2/upload"
headers = {"authorization": "edd915cdc8014f9db7190b8a38c0ff28"}

@app.get("/")
async def root(
    audio_url: str = Query(..., description="URL of the audio file"),
    pii_redaction: bool = Query(False, description="Enable PII redaction"),
    speaker_labels: bool = Query(False, description="Enable speaker labels"),
    dual_channel: bool = Query(False, description="Enable dual-channel transcription"),
    filter_profanity: bool = Query(False, description="Enable profanity filtering"),
    model_type: str = Query(..., description="Choose the model type (nano or best)"),
    language_code: str = Query("auto", description="Specify the language code or use 'auto' for automatic detection")
):
    transcriber = aai.Transcriber()

    # Determine the speech model based on the user's selection
    speech_model = aai.SpeechModel.best if model_type == "best" else aai.SpeechModel.nano

    # Set language detection to False if a specific language code is provided
    language_detection = language_code == "auto"

    # Initialize the transcription configuration
    config = aai.TranscriptionConfig(
        speech_model=speech_model,
        language_detection=language_detection,
        speaker_labels=speaker_labels,
        dual_channel=dual_channel,
        filter_profanity=filter_profanity,
        language_code=language_code if not language_detection else None
    )

    # Apply PII redaction if requested
    if pii_redaction:
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

    # Transcribe the audio using the provided configuration
    transcript = transcriber.transcribe(audio_url, config)

    # Format the transcript based on speaker labels or dual-channel
    if speaker_labels or dual_channel:
        result = ""
        for utterance in transcript.utterances:
            result += f"**Speaker {utterance.speaker}:** {utterance.text}\n\n"
        return {"transcript": result}

    # Return the plain transcript
    return {"transcript": transcript.text} 

@app.get("/parse")
async def parse(audio_url: str = Query(..., description="URL of the audio file"),
                summarization: bool = Query(False, description="Enable summarization"),
                iab_categories: bool = Query(False, description="Enable topic detection"),
                auto_chapters:bool = Query(False, description="Enable topic detection"),
                content_safety: bool = Query(False, description="Enable topic detection"),
                auto_highlights: bool = Query(False, description="Enable topic detection"),
                sentiment_analysis: bool = Query(False, description="Enable topic detection"),
                entity_detection: bool = Query(False, description="Enable topic detection"),
                ):
    # audio_url = "https://github.com/AssemblyAI-Community/audio-examples/raw/main/20230607_me_canadian_wildfires.mp3"
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
    
    if summarization:
        auto_chapters = False
    elif auto_chapters:
        summarization = False
        
    config = aai.TranscriptionConfig(
        summary_model=aai.SummarizationModel.informative,
        summary_type=aai.SummarizationType.bullets,
        summarization=summarization,
        iab_categories=iab_categories,
        auto_chapters=auto_chapters,
        content_safety=content_safety,
        auto_highlights=auto_highlights,
        sentiment_analysis=sentiment_analysis,
        entity_detection=entity_detection
        )

    transcript = aai.Transcriber().transcribe(audio_url, config)
    
    if iab_categories is not False:   
        for topic, relevance in transcript.iab_categories.summary.items():
            if relevance > 0.8:
                refined_topic = ' '.join(re.split('(?=[A-Z])', topic.split('>')[-1])).strip()
                topics.append(refined_topic)

        topics_str = " \n - ".join(topics)
        topics_str = f"- {topics_str}"
    
    if auto_chapters is not False:
        for chapter in transcript.chapters:
            refined_chapter = f"- {chapter.headline}"
            chapters.append(refined_chapter)
        
        chapter_str = " \n ".join(chapters)
    
    if content_safety is not False:
        for result in transcript.content_safety.results:
            for label in result.labels:
                result_text = f"**{label.label}**\n{result.text}"
                content.append(result_text)

        content_str = "\n\n".join(content)
    
    if auto_highlights is not False:
        for result in transcript.auto_highlights.results:
            phrase_text = result.text
            key_phrases.append(phrase_text)
        phrase_str = "\n\n".join(key_phrases)
    
    if sentiment_analysis is not False:
        for sentiment_result in transcript.sentiment_analysis:
            if sentiment_result.sentiment == "POSITIVE":
                count_positive += 1
            elif sentiment_result.sentiment == "NEUTRAL":
                count_neutral += 1
            elif sentiment_result.sentiment == "NEGATIVE":
                count_negative += 1
            sentiment_str = f"We identified **{count_positive}** positive sentences, and **{count_negative}** negative ones."
    
    if entity_detection is not False:
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
            "topic": topics_str if iab_categories else "", 
            "chapter": chapter_str if auto_chapters else "",
            "content": content_str if content_safety else "",
            "phrases": phrase_str if auto_highlights else "",
            "sentiment": sentiment_str if sentiment_analysis else "",
            "entity": entity_str if entity_detection else ""
            }