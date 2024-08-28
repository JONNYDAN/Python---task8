import assemblyai as aai
import re
from fastapi import FastAPI, HTTPException
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
        language_code=request.language_code if not language_detection else None,
        summarization=request.summarization,
        iab_categories=request.iab_categories,
        auto_chapters=request.auto_chapters,
        content_safety=request.content_safety,
        auto_highlights=request.auto_highlights,
        sentiment_analysis=request.sentiment_analysis,
        entity_detection=request.entity_detection
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

    # Prevent both summarization and auto chapters from being active at the same time
    if request.summarization:
        request.auto_chapters = False
    elif request.auto_chapters:
        request.summarization = False

    try:
        # Transcribe the audio using the provided configuration
        transcript = transcriber.transcribe(request.audio_url, config)

        # Initialize result containers
        topics = []
        chapters = []
        content = []
        key_phrases = []
        count_positive = 0
        count_neutral = 0
        count_negative = 0
        entities = {entity_type: [] for entity_type in [
            "Location", "Person_name", "Occupation", "Organization", "Nationality", "Duration", 
            "Medical_condition", "Account_number", "Banking_information", "Blood_type", 
            "Credit_card_cvv", "Credit_card_expiration", "Credit_card_number", "Date", 
            "Date_interval", "Date_of_birth", "Drivers_license", "Drug", "Email_address", 
            "Event", "Filename", "Gender_sexuality", "Healthcare_number", "Injury", 
            "Ip_address", "Language", "Marital_status", "Medical_process", "Money_amount", 
            "Number_sequence", "Passport_number", "Password", "Person_age", "Phone_number", 
            "Physical_attribute", "Political_affiliation", "Religion", "Statistics", 
            "Time", "Url", "Us_social_security_number", "Username", "Vehicle_id"
        ]}

        # Process IAB categories
        if request.iab_categories:
            for topic, relevance in transcript.iab_categories.summary.items():
                if relevance > 0.8:
                    refined_topic = ' '.join(re.split('(?=[A-Z])', topic.split('>')[-1])).strip()
                    topics.append(refined_topic)
            topics_str = " \n ".join(topics)

        # Process auto chapters
        if request.auto_chapters:
            for chapter in transcript.chapters:
                chapters.append(f"- {chapter.headline}")
            chapter_str = " \n ".join(chapters)

        # Process content safety results
        if request.content_safety:
            for result in transcript.content_safety.results:
                for label in result.labels:
                    content.append(f"**{label.label}**\n{result.text}")
            content_str = "\n\n".join(content)

        # Process auto highlights
        if request.auto_highlights:
            for result in transcript.auto_highlights.results:
                key_phrases.append(result.text)
            phrase_str = "\n\n".join(key_phrases)

        # Process sentiment analysis
        if request.sentiment_analysis:
            for sentiment_result in transcript.sentiment_analysis:
                if sentiment_result.sentiment == "POSITIVE":
                    count_positive += 1
                elif sentiment_result.sentiment == "NEUTRAL":
                    count_neutral += 1
                elif sentiment_result.sentiment == "NEGATIVE":
                    count_negative += 1
            sentiment_str = f"We identified **{count_positive}** positive sentences, and **{count_negative}** negative ones."

        # Process entity detection
        if request.entity_detection:
            for entity in transcript.entities:
                entity_text = entity.text.strip()
                entity_type = entity.entity_type.value.capitalize()
                if entity_type in entities:
                    entities[entity_type].append(entity_text)
            entity_str = "\n\n".join(
                [f"**{entity_type}:**\n {', '.join(entity_list)}" for entity_type, entity_list in entities.items() if entity_list]
            )

        # Format the transcript based on speaker labels or dual-channel
        if request.speaker_labels or request.dual_channel:
            result = ""
            for utterance in transcript.utterances:
                result += f"**Speaker {utterance.speaker}:** {utterance.text}\n\n"
            return {
                "transcript": result,
                "summary": transcript.summary if request.summarization else "",
                "topic": topics_str if request.iab_categories else "",
                "chapter": chapter_str if request.auto_chapters else "",
                "content": content_str if request.content_safety else "",
                "phrases": phrase_str if request.auto_highlights else "",
                "sentiment": sentiment_str if request.sentiment_analysis else "",
                "entity": entity_str if request.entity_detection else ""
            }

        # Return the plain transcript with additional processing results
        return {
            "transcript": transcript.text,
            "summary": transcript.summary if request.summarization else "",
            "topic": topics_str if request.iab_categories else "",
            "chapter": chapter_str if request.auto_chapters else "",
            "content": content_str if request.content_safety else "",
            "phrases": phrase_str if request.auto_highlights else "",
            "sentiment": sentiment_str if request.sentiment_analysis else "",
            "entity": entity_str if request.entity_detection else ""
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
