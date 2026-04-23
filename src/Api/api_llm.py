"""
Http requests for bb_backend_llm
Sends request to bb_backend_llm large language model, calculates reply and return it to here
TODO statt unendlichem timeout regelmäßig (z.B. alle 10 sekunden) eine request an der server senden um zu überprüfen ob noch transkribiert wird.
"""
import re

from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
import httpx
import src.config
import os

from Client.client_db import client_db_project_audio_length_get
from Dicts.transcript_mini_evaluated import transcript_mini_evaluated_dict
from Dicts.transcript_mini_summarized import transcript_mini_summarized_dict
from Schemes.api_schemes import ProjectAudioLengthRequestRead
from Utils.utils_estimations import calculate_estimations
from src.Api.api_db import project_status_get, project_status_set
from src.Schemes.api_schemes import ProjectStatus, ProjectStatusRequestWrite, ProjectStatusRequestRead, \
    ProjectEstimationRequestWrite
from src.Handler.handler_llm import summarize_transcript_mini_json as handler_llm_summarize_transcript_mini_json, toipirize_transcript_mini_table, topirize_cleanup_transcript_mini_json
import json
from pydantic import BaseModel
from typing import List, Dict
from src.Schemes.api_schemes import ProjectRequestRead, ProjectRequestWriteDict, Token
import logging
from src.Client.client_db import client_db_refresh_access_token, client_db_project_estimations_set
import time
from datetime import datetime
router = APIRouter()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class TranscriptionRequest(BaseModel):
    transcript_mini_json: List[Dict]


#TODO mehr Exceptions hinzufügen
@router.post("/llm_summarize/")
async def llm_summarize(request: ProjectRequestRead, refresh_token: Token):
    """
    nimmt eine ProjectRequestRead entgegen (enthält project_id).
    Liest aus der Datenbank aus der project_id das transcript_mini_json.
    Fässt es dann mithilfe des LLM zusammen.
    Die Zusammenfassung wird wieder in der Datenbank gespeichert.
    """
    from src.Api.api_db import transcript_mini_read, protocol_template_read, transcript_mini_write, protocol_write
    from src.Classes.protocol import Protocol, CLASS_MAPPING as protocol_CLASS_MAPPING
    from src.Classes.transcript_mini import TranscriptMini, restructure_by_topics, CLASS_MAPPING as transcript_mini_CLASS_MAPPING
    from src.Utils.class_dict import dict_to_obj, obj_to_dict

    # Überprüfung des Projektstatus
    #project_status: str = await project_status_get(ProjectStatusRequestRead(project_id=request.project_id))
    #if not project_status == ProjectStatus.TRANSCRIBED:
    #    error_str = f"Error: Cannot toipirize and summarize because project has wrong status. Project should have status {ProjectStatus.TRANSCRIBED} but instead has status {str(project_status)}"
    #    logger.error(error_str)
    #    raise HTTPException(status_code=500, detail=error_str)

    # Updates the project status. Transcribing is BEGINNING
    #await project_status_set(ProjectWriteRequestStatus(project_id=request.project_id, status=ProjectStatus.IS_SUMMARIZING))

    # access_token für LLM funktionen generieren
    # project_status auf is_summarizing setzen
    access_token: Token = client_db_refresh_access_token(refresh_token)
    await project_status_set(ProjectStatusRequestWrite(access_token=access_token.token, project_id=request.project_id, project_status=ProjectStatus.IS_SUMMARIZING))

    try:
        # audio länge aus der Datenbank lesen
        audio_length: int = await client_db_project_audio_length_get(ProjectAudioLengthRequestRead(project_id=request.project_id, access_token=access_token.token))

        # --- Estimations berechnen ---
        transcription_eta, summarization_eta = calculate_estimations(audio_length)

        # --- Estimations speichern ---
        await client_db_project_estimations_set(
            ProjectEstimationRequestWrite(
                project_id=request.project_id,
                project_transcription_estimation=datetime.now(),
                project_summarization_estimation=summarization_eta,
                access_token=access_token.token
            )
        )



        # read TranscriptMini from database
        transcript_mini_json = await transcript_mini_read(request)
        transcript_mini_data = transcript_mini_json['data']
        transcript_mini: TranscriptMini = dict_to_obj(transcript_mini_data, transcript_mini_CLASS_MAPPING)

        # read ProtocolTemplate from database
        protocol_template_json = await protocol_template_read(request)

        # Get Protocol dict from
        protocol_template_data = protocol_template_json['data']

        # Generate Protocol Template from dict
        protocol_template: Protocol = dict_to_obj(protocol_template_data, protocol_CLASS_MAPPING)

        # troubleshoots parsing and logic related issues regarding the protocol_template that got converted from the protocol_template_json()
        protocol_template.troubleshoot()

        # for Protocol generate table of contents
        protocol_template.generate_all_table_string_list()

        # LLM assigns topics to the TranscriptMini. Can assign one topic multiple times. They get filtered out later.
        transcript_mini_topirized: TranscriptMini = await toipirize_transcript_mini_table(transcript_mini, protocol_template.get_public_table())

        # automatically remove all topics in the TranscriptMini that do not exist in the original ProtocolTemplate
        transcript_mini_topirized.remove_entries_not_in_protocol(protocol_template)

        # LLM evaluates the best timestamps from previous assigned topics from the LLM.
        transcript_mini_evaluated: TranscriptMini = await topirize_cleanup_transcript_mini_json(transcript_mini_topirized, protocol_template)

        # THE FOLLOWING LINES WITHOUT EXTRA LINE BREAKS ARE DEBUG STUFF
        # access_token = client_db_refresh_access_token(refresh_token)
        # transcript_mini_write_request = ProjectRequestWriteDict(project_id=request.project_id, data=obj_to_dict(transcript_mini_evaluated))
        # await transcript_mini_write(transcript_mini_write_request)

        # for TESTING load already finished topic evaluated TranscriptMini
        # transcript_mini_evaluated: TranscriptMini = dict_to_obj(transcript_mini_evaluated_dict, transcript_mini_CLASS_MAPPING)

        # All SpeakerTranscripts from TranscriptMini gets restructured automatically so that in each SpeakerTranscript a topic is max assigned to one Sentence.
        transcript_mini_restructured: TranscriptMini = restructure_by_topics(transcript_mini_evaluated, 0)

        # LLM summarizes each SpeakerTranscript in TranscriptMini
        transcript_mini_summarization = await handler_llm_summarize_transcript_mini_json(transcript_mini_restructured)

        # THE FOLLOWING LINES WITHOUT EXTRA LINE BREAKS ARE DEBUG STUFF
        # access_token = client_db_refresh_access_token(refresh_token)
        # transcript_mini_write_request = ProjectRequestWriteDict(project_id=request.project_id, data=obj_to_dict(transcript_mini_summarization))
        # await transcript_mini_write(transcript_mini_write_request)

        # for TESTING load already finished topic evaluated TranscriptMini
        # transcript_mini_summarization: TranscriptMini = dict_to_obj(transcript_mini_summarized_dict, transcript_mini_CLASS_MAPPING)

        # Convert summarized TranscriptMini to Protocol and write it to the database
        protocol_template.process_transcript(transcript_mini_summarization)

        # refresh access_token because LLM needs some longer time (access_token could be expired)
        access_token = client_db_refresh_access_token(refresh_token)

        # builds a dict from protocol_template and saves it as protocol into the database
        project_request_write_dict = ProjectRequestWriteDict(project_id=request.project_id, data=obj_to_dict(protocol_template))
        await protocol_write(project_request_write_dict)

        # Updates the project status. Summarizing is finished.
        await project_status_set(ProjectStatusRequestWrite(access_token=access_token.token, project_id=request.project_id, project_status=ProjectStatus.COMPLETED))

        return {"status_code": 200}

    except HTTPException as e:
        # setzt Status auf TRANSCRIBED zurück, da summarizing fehlgeschlagen ist.
        await project_status_set(ProjectStatusRequestWrite(access_token=access_token.token, project_id=request.project_id, project_status=ProjectStatus.TRANSCRIBED))
        logger.error(f"HTTPException occurred: {str(e)}")  # Logge den Fehler detaillierter
        raise HTTPException(status_code=500, detail=f"HTTP error: {str(e)}")
    except Exception as e:
        # setzt Status auf TRANSCRIBED zurück, da summarizing fehlgeschlagen ist.
        await project_status_set(ProjectStatusRequestWrite(access_token=access_token.token, project_id=request.project_id, project_status=ProjectStatus.TRANSCRIBED))
        logger.exception(f"Internal server error: {e}")  # Loggt den Fehler mit Stacktrace
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")




@router.post("/llm_summarize_transcript_mini_json/")
async def llm_summarize_transcript_mini_json(request: TranscriptionRequest):
    try:
        transcript_mini_json_summarization = await handler_llm_summarize_transcript_mini_json(request.transcript_mini_json)
        return JSONResponse(
            content={"result": transcript_mini_json_summarization},
            status_code=200
        )
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))

"""
Input is chat list with following strings: system_prompt, user, assistent, user, assistent, etc.
"""
@router.post("/llm_get_chat_reply_old2/")
async def llm_get_chat_reply_old2(messages: list[dict]):
    url = "http://127.0.0.1:23333/v1/chat/completions"

    request_data = {
        "model": "Valdemardi/DeepSeek-R1-Distill-Qwen-32B-AWQ",
        "messages": messages
    }

    response = httpx.post(url, json=request_data, timeout=None)
    response_json = response.json()

    # Extrahiere den Textinhalt
    content = response_json.get("choices", [{}])[0].get("message", {}).get("content", "")

    # Nur den Text nach </think> ausgeben
    cleaned_content = re.split(r"</think>", content, flags=re.IGNORECASE, maxsplit=1)
    cleaned_content = cleaned_content[1].strip() if len(cleaned_content) > 1 else content

    return {"status_code": response.status_code, "response": cleaned_content}

@router.post("/llm_get_chat_reply/")
async def llm_get_chat_reply(messages: list[dict]):
    # LMDeploy
    # url = "http://127.0.0.1:23333/v1/chat/completions"

    # VLLM
    url = "http://127.0.0.1:23333/v1/chat/completions"

    request_data = {
        "model": "Valdemardi/DeepSeek-R1-Distill-Qwen-32B-AWQ",
        "messages": messages
    }

    max_retries = 5
    for attempt in range(max_retries):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=request_data, timeout=120)
                response.raise_for_status()  # Löst Fehler aus, wenn HTTP-Status nicht 2xx ist
                break  # Bei Erfolg die Schleife verlassen
            except httpx.HTTPStatusError as http_err:
                logger.error(f"llm_get_chat_reply got HTTP error from LMDeploy (Attempt {attempt + 1}/{max_retries}): {http_err}")
            except httpx.RequestError as req_err:
                logger.error(f"llm_get_chat_reply got HTTP request error from LMDeploy (Attempt {attempt + 1}/{max_retries}): {req_err}")

            if attempt < max_retries - 1:
                # Warte vor dem nächsten Versuch
                time.sleep(2)  # Warte 2 Sekunden (kann angepasst werden)
            else:
                return {"status_code": 500, "error": "Maximum retry attempts reached", "response": ""}

    # Wenn wir hier sind, war der Request erfolgreich
    response_json = response.json()

    # Extrahiere den Textinhalt
    content = response_json.get("choices", [{}])[0].get("message", {}).get("content", "")

    # Nur den Text nach </think> ausgeben
    cleaned_content = re.split(r"</think>", content, flags=re.IGNORECASE, maxsplit=1)
    cleaned_content = cleaned_content[1].strip() if len(cleaned_content) > 1 else content

    return {"status_code": response.status_code, "response": cleaned_content}


"""
Input is chat list with following strings: system_prompt, user, assistent, user, assistent, etc.
"""
@router.post("/llm_get_chat_reply_old/")
async def llm_get_chat_reply_old(messages: list[dict]):
    url = "http://127.0.0.1:8002/get_chat_reply/"

    response = httpx.post(url, json=messages, timeout=None)
    return {"status_code": response.status_code, "response": response.text}




"""
# @router.post("/llm_create_protocol_json/")
async def llm_create_protocol_json(
    title: str = Form(...),
    subtitle: str = Form(...),
    groups: str = Form(...),
    chapter_titles: str = Form(...)
):
    try:
        # Prüfen, ob groups und chapter_titles bereits deserialisiert sind
        if isinstance(groups, str):
            groups = json.loads(groups)
        if isinstance(chapter_titles, str):
            chapter_titles = json.loads(chapter_titles)

        # Beispiel: Verarbeite die Daten weiter
        response = await src.Handler.handler_llm.create_protocol_json(title, subtitle, groups, chapter_titles)
        path = os.path.join(src.config.get_project_path(), "documents", "protocol.json")
        json.dump(response, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=4)
        return response

    except json.JSONDecodeError as e:
        return {"error": "Ungültige JSON-Daten", "details": str(e)}
"""