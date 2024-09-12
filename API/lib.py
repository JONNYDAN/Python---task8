from model import TranscriptionRequest
import assemblyai as aai
import re 
import time
import os


def generate_config_from_request(request: TranscriptionRequest) -> aai.TranscriptionConfig:
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

    return config

def generate_response_download(transcript: aai.Transcript) -> dict:
    srt = transcript.export_subtitles_srt()

    vtt = transcript.export_subtitles_vtt()
    
    return {
        "srt": srt,
        "vtt": vtt,
    }

def generate_response(transcript: aai.Transcript, request: TranscriptionRequest) -> dict:
    # Initialize result containers
    topics = []
    chapters = []
    content = []
    key_phrases = []
    count_positive = 0
    count_neutral = 0
    count_negative = 0
    entities = {}

    # Process IAB categories
    if request.iab_categories:
        for topic, relevance in transcript.iab_categories.summary.items():
            if relevance > 0.8:
                refined_topic = ' '.join(re.split('(?=[A-Z])', topic.split('>')[-1])).strip()
                topics.append(refined_topic)
        topics_str = "\n\n".join(topics)

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
            
            if entity_type not in entities:
                entities[entity_type] = []
                
            entities[entity_type].append(entity_text)
            
        entity_str = "\n\n".join(
            [f"**{entity_type}:**\n {', '.join(entity_list)}" for entity_type, entity_list in entities.items() if entity_list]
        )

    # Format the transcript based on speaker labels or dual-channel
    transcript_text = str(transcript.text)
    
    # if request.speaker_labels or request.dual_channel:
    #     result = ""
    #     for utterance in transcript.utterances:
    #         result += f"**Speaker {utterance.speaker}:** {utterance.text}\n\n"
        
    #     transcript_text = result

    # Return the plain transcript with additional processing results
    return {
        "transcript": transcript_text,
        "transcript_words": transcript.words,
        "utterance": transcript.utterances,
        "summary": transcript.summary if request.summarization else "",
        "topic": topics_str if request.iab_categories else "",
        "chapter": chapter_str if request.auto_chapters else "",
        "content": content_str if request.content_safety else "",
        "phrases": phrase_str if request.auto_highlights else "",
        "sentiment": sentiment_str if request.sentiment_analysis else "",
        "entity": entity_str if request.entity_detection else "",
    }

def clean_files_after_setup_time(folder_path, setup_time_in_seconds):
    current_time = time.time()

    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)

        if os.path.isfile(file_path):
            file_mod_time = os.path.getmtime(file_path)

            if current_time - file_mod_time > setup_time_in_seconds:
                os.remove(file_path)  