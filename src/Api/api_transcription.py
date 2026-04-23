"""
Http requests for bb_backend_transcription
Sends request to bb_backend_transcription whisperX and creates transcription

TODO statt unendlichem timeout regelmäßig (z.B. alle 10 sekunden) eine request an der server senden um zu überprüfen ob noch transkribiert wird.
"""
from datetime import datetime, timedelta
import wave

import fastapi.responses
from fastapi import APIRouter, Form, UploadFile
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
import httpx
from pydantic import BaseModel
from typing import List, Dict, Any
from uuid import UUID
import tempfile
import os
import json
import logging
import asyncio

from Client.client_db import client_db_project_estimations_set, client_db_project_audio_length_set
from Schemes.api_schemes import ProjectAudioLengthRequestWrite
from Utils.utils_estimations import get_estimations_from_file, get_audio_duration_seconds, calculate_estimations
from src.Api.api_db import project_status_get, project_status_set, protocol_template_status_get, protocol_template_status_set
from src.Api.api_llm import llm_summarize
from src.Client.client_db import client_db_refresh_access_token
from src.Schemes.api_schemes import ProtocolTemplateStatus, ProtocolTemplateStatusWrite, ProjectStatus, \
    ProjectStatusRequestWrite, ProjectStatusRequestRead, ProjectRequestReadTranscribe, Token, \
    ProtocolTemplateStatusRead, ProjectEstimationRequestWrite

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

router = APIRouter()


class TranscriptionRequest(BaseModel):
    transcription_json: List[Dict]

class ProjectRequestWriteDict(BaseModel):
    project_id: UUID
    data: dict

class ProjectRequestWriteListDict(BaseModel):
    project_id: UUID
    data: list[dict]

class ProjectRequestRead(BaseModel):
    project_id: UUID

async def check_start_summarization(request: ProjectStatusRequestRead, refresh_token: Token):
    # Updates the project status. Transcribing is finished.
    await project_status_set(ProjectStatusRequestWrite(access_token=request.access_token, project_id=request.project_id, project_status=ProjectStatus.TRANSCRIBED))

    # protocol_template_status: ProtocolTemplateStatus = await protocol_template_status_get(request)
    protocol_template_status: ProtocolTemplateStatus = await protocol_template_status_get(ProtocolTemplateStatusRead(access_token=request.access_token, project_id=request.project_id))

    # wenn project_tempalte_status approved ist, dann wird das ProtocolTemplate gelocked und die summarization gestartet
    if protocol_template_status == ProtocolTemplateStatus.approved:
        await protocol_template_status_set(ProtocolTemplateStatusWrite(access_token=request.access_token, project_id=request.project_id, protocol_template_status=ProtocolTemplateStatus.locked))
        asyncio.create_task(llm_summarize(ProjectRequestRead(project_id=request.project_id), refresh_token))

@router.post("/transcribe_start")
async def transcribe_start(request: ProjectRequestReadTranscribe):
    logger.info(f"Transcription request received for project_id {request.project_id}")

    refresh_token: Token = Token(token=request.refresh_token)
    access_token: Token = client_db_refresh_access_token(refresh_token)

    # print("BLAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
    # protocol_template_status: ProtocolTemplateStatus = await protocol_template_status_get(ProtocolTemplateStatusRead(access_token=access_token.token, project_id=request.project_id))

    # Überprüfung des Projektstatus
    project_status: str = await project_status_get(ProjectStatusRequestRead(access_token=access_token.token, project_id = request.project_id))
    if not project_status == ProjectStatus.INITIAL:
        error_str = f"Error: Cannot transcribe because project has wrong status. Project should have status {ProjectStatus.INITIAL} but instead has status {str(project_status)}"
        logger.error(error_str)
        raise HTTPException(status_code=500, detail=error_str)

    # Updates the project status. Transcribing is BEGINNING
    await project_status_set(ProjectStatusRequestWrite(access_token=access_token.token, project_id=request.project_id, project_status=ProjectStatus.IS_TRANSCRIBING))

    # Starte transcribe im Hintergrund
    asyncio.create_task(transcribe(request))
    return {"message": "Successfully transcribed", "status_code": 200}

# @router.post("/transcribe")
async def transcribe(request: ProjectRequestReadTranscribe):
    """
    nimmt eine ProjectRequestRead entgegen (enthält project_id).
    Liest aus der Datenbank aus der project_id das transcript_mini_json.
    Fässt es dann mithilfe des LLM zusammen.
    Die Zusammenfassung wird wieder in der Datenbank gespeichert.
    """
    from src.Api.api_db import transcript_write

    refresh_token: Token = Token(token=request.refresh_token)



    try:
        # Empfängt die Audio-Datei von einem anderen Server mit httpx
        url = "http://127.0.0.1:8010/audio_read"
        json_data = {"project_id": str(request.project_id)}  # UUID wird zu einem String umgewandelt

        # Sende die Anfrage mit httpx, um die Audio-Datei zu empfangen
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=json_data, timeout=None)

            # Falls der Antwort-Statuscode nicht OK ist, raise Exception
            response.raise_for_status()

            # Hier wird angenommen, dass die Antwort die Audio-Datei enthält
            audio_content = response.content

            # Speichert die Datei temporär auf der RAM-Disk
            with tempfile.NamedTemporaryFile(delete=True, dir='/mnt/ramdisk') as temp_file:
                temp_file.write(audio_content)
                temp_filename = temp_file.name

                # --- Audio-Länge berechnen ---
                duration_seconds = get_audio_duration_seconds(temp_filename)

                # --- Estimations berechnen ---
                transcription_eta, summarization_eta = calculate_estimations(duration_seconds)

                # --- Zugriffstoken laden ---
                access_token: Token = client_db_refresh_access_token(refresh_token)

                # --- Audio-Länge speichern ---
                await client_db_project_audio_length_set(
                    ProjectAudioLengthRequestWrite(
                        project_id=request.project_id,
                        project_audio_length=duration_seconds,
                        access_token=access_token.token
                    )
                )

                # --- Estimations speichern ---
                await client_db_project_estimations_set(
                    ProjectEstimationRequestWrite(
                        project_id=request.project_id,
                        project_transcription_estimation=transcription_eta,
                        project_summarization_estimation=summarization_eta,
                        access_token=access_token.token
                    )
                )

                min_speakers = request.min_speakers
                max_speakers = request.max_speakers
                transcribe_url = "http://127.0.0.1:8001/transcribe/"

                # Bereite die Multipart-Daten vor
                files = {"file": (os.path.basename(temp_filename), open(temp_filename, "rb"), "audio/wav")}
                data = {"min_speakers": min_speakers, "max_speakers": max_speakers}

                # Sende die Audio-Datei zur Transkription
                async with httpx.AsyncClient() as client:
                    response = await client.post(transcribe_url, files=files, data=data, timeout=None)

                # Überprüfe den Statuscode der Antwort und hole die Transkription
                response.raise_for_status()
                response_json = response.json()
                body_data = json.loads(response_json['response']['body'])

                # Now you can access the 'result' key
                transcript_json = body_data['result']

                # merges segments of each consecutive speakers in transcript into same segment
                transcript_merged_json = transcription_transcript_json_merge(transcript_json=transcript_json)

                # Speichert die merged Zusammenfassung in der Datenbank
                await transcript_write(ProjectRequestWriteDict(project_id=request.project_id, data=transcript_merged_json))

                # converts transcript to transcript_mini and saves it in database
                await transcription_transcript_mini_json(ProjectRequestRead(project_id=request.project_id), transcript_json=transcript_json)

                # neuen access token anfordern
                access_token: Token = client_db_refresh_access_token(refresh_token)

                # Updates the project status. Transcribing is FINISHED
                await project_status_set(ProjectStatusRequestWrite(access_token=access_token.token, project_id=request.project_id, project_status=ProjectStatus.TRANSCRIBED))

                # project_status setzen und danach project_template_status überprüfen. Falls approved, dann wird die summarization gestartet.
                await check_start_summarization(ProjectStatusRequestRead(access_token=access_token.token, project_id=request.project_id), refresh_token)

                logger.info("Successfully transcribed")
                # return {"message": "Successfully transcribed", "status_code": 200}
                return

    except HTTPException as e:
        # setzt Status auf INITIAL zurück, da Transkribierung fehlgeschlagen ist.
        await project_status_set(ProjectStatusRequestWrite(access_token=access_token.token, project_id=request.project_id, project_status=ProjectStatus.INITIAL))
        logger.error(f"HTTPException occurred to bb_backend_transcription: {str(e)}")  # Logge den Fehler detaillierter
        raise HTTPException(status_code=500, detail=f"HTTP error: {str(e)}")
    except Exception as e:
        # setzt Status auf INITIAL zurück, da Transkribierung fehlgeschlagen ist.
        await project_status_set(ProjectStatusRequestWrite(access_token=access_token.token, project_id=request.project_id, project_status=ProjectStatus.INITIAL))
        logger.exception(f"Internal server error: {e}")  # Loggt den Fehler mit Stacktrace
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


def transcription_transcript_json_merge(transcript_json: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Merges consecutive segments with the same speaker in a transcript JSON.
    Appends text and words lists for segments by the same speaker.

    Args:
        transcript_json: A dictionary containing the 'transcript_json' key, which maps to a list of transcript segments,
                    each a dict with keys 'start', 'end', 'text', 'words', and 'speaker'.

    Returns:
        A new dictionary with the merged transcript segments under the 'transcript_json' key.
    """
    transcript_json = transcript_json.get('transcript_json', [])

    if not transcript_json:
        return {"transcript_json": []}

    merged: List[Dict[str, Any]] = []
    # Initialize with the first segment
    current = transcript_json[0].copy()

    for segment in transcript_json[1:]:
        if segment.get('speaker') == current.get('speaker'):
            # Extend the current segment
            # Update end time to the later one
            current['end'] = segment.get('end', current['end'])
            # Append text (ensure spacing)
            current['text'] = current.get('text', '').rstrip() + ' ' + segment.get('text', '').lstrip()
            # Extend words list
            current['words'].extend(segment.get('words', []))
        else:
            # Different speaker: push current and start new
            merged.append(current)
            current = segment.copy()

    # Append the last segment
    merged.append(current)

    return {"transcript_json": merged}




@router.post("/transcription_transcript_mini_json")
async def transcription_transcript_mini_json(request: ProjectRequestRead, transcript_json: dict):
    """
    API to call function for transforming a transcript_json into a transcript_mini_json.
    Further for LLM summarization.
    This function takes directly a transcript_json, converts it into a TranscriptMini and saves it to the database.
    """
    from src.Api.api_db import transcript_mini_write
    from src.Classes.transcript_mini import TranscriptMini
    from src.Utils.class_dict import obj_to_dict

    # url = "http://127.0.0.1:8001/transcribe_mini/"

    transcript_mini: TranscriptMini = TranscriptMini()
    # transcript_mini.load_transcript_json(transcript_json)
    transcript_mini.load_transcript_json_limited(transcript_json, 2000)
    transcript_mini_json: dict = obj_to_dict(transcript_mini)

    # String für Tests erstellen
    test_string_with_timestamps = ""
    test_string_without_timestamps = ""

    # Durch alle geladenen SpeakerTranscripts iterieren und beide Methoden testen
    for transcript in transcript_mini.get_speaker_transcripts():  # Hier nehmen wir an, dass die geladenen Transkripte in 'transcripts' gespeichert sind
        # Test für to_string (mit Timestamps)
        test_string_with_timestamps += transcript.to_string() + "\n"

        # Test für to_string_no_timestamps (ohne Timestamps)
        test_string_without_timestamps += transcript.to_string_no_timestamps_no_linebreak() + "\n"

    # Jetzt kannst du die beiden Test-Strings ausgeben oder weiterverwenden
    print("Test mit Timestamps:")
    print(test_string_with_timestamps)

    print("\nTest ohne Timestamps:")
    print(test_string_without_timestamps)

    project_request_write_dict = ProjectRequestWriteDict(project_id=request.project_id, data=transcript_mini_json)
    await transcript_mini_write(project_request_write_dict)
    return {"status_code": 200}




@router.post("/transcription_transcript_mini_json")
async def transcription_transcript_mini_json_from_database(request: ProjectRequestRead):
    """
    API to call function for transforming a transcript_json into a transcript_mini_json.
    Further for LLM summarization.
    This function loads the transcription_json from the database, converts it to a TranscriptMini and saves it back into the database.
    """
    from src.Api.api_db import transcript_read
    from src.Api.api_db import transcript_mini_write
    from src.Classes.transcript_mini import TranscriptMini
    from src.Utils.class_dict import obj_to_dict

    respond = await transcript_read(request)
    transcript_json = respond['data']

    # url = "http://127.0.0.1:8001/transcribe_mini/"

    # payload = {"transcription_json": request.transcription_json}

    # print(transcript_json)
    # transcript_mini_json = transcript_json_to_transcript_mini(transcript_json)
    transcript_mini: TranscriptMini = TranscriptMini()
    transcript_mini.load_transcript_json(transcript_json)
    transcript_mini_json: dict = obj_to_dict(transcript_mini)

    project_request_write_dict = ProjectRequestWriteDict(project_id=request.project_id, data=transcript_mini_json)
    await transcript_mini_write(project_request_write_dict)
    return {"status_code": 200}




"""
Calls trancription api from bb_backend_transcription
"""
@router.post("/transcribe_old/")
async def transcribe_old(
    file: UploadFile,
    min_speakers: str = Form(...),
    max_speakers: str = Form(...)
):
    url = "http://0.0.0.0:8001/transcribe/"

    # Bereite die Multipart-Daten vor
    files = {"file": (file.filename, file.file, file.content_type)}
    data = {"min_speakers": min_speakers, "max_speakers": max_speakers}

    # Sende die Anfrage mit httpx
    async with httpx.AsyncClient() as client:
        response = await client.post(url, files=files, data=data, timeout=None)

    # Rückgabe der Antwort des Servers
    if response.status_code == 200:
        return response.json()
    else:
        return JSONResponse(status_code=response.status_code, content=response.json())