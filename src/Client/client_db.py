"""
Client Http requests for bb_backend_db.
This client sends HTTP requests to bb_backend_db and receives replies.
Put every bb_backend_db related HTTP request here.
"""

import httpx
import logging
from fastapi import HTTPException

from Schemes.api_schemes import ProjectAudioLengthRequestWrite, ProjectAudioLengthRequestRead
from src.Schemes.api_schemes import Token, ProjectEstimationRequestWrite

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

async def client_db_project_audio_length_get(request: ProjectAudioLengthRequestRead):
    url = "http://127.0.0.1:8010/projects/audio_length_get"

    # Den Authorization-Header aus der Pydantic-Anfrage lesen
    token = request.access_token
    if token:
        token = token if token.startswith("Bearer ") else f"Bearer {token}"
    headers = {"Authorization": token} if token else {}

    logger.info(f"Authorization-Header gefunden und weitergeleitet: {token}")

    # Status des Protokoll-Templates aus der Anfrage
    logger.info(f"Projekt-ID: {request.project_id}")

    # Anfrage an den Datenbank-Server weiterleiten
    try:
        async with httpx.AsyncClient() as client:
            json_data = {"project_id": str(request.project_id)}
            logger.info(f"Sende Anfrage an {url} mit Body: {json_data}")
            response = await client.post(url, json=json_data, headers=headers)

        logger.info(f"Antwort vom DB-Server erhalten: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Fehlgeschlagene Antwort: {response.text}")
            raise HTTPException(status_code=response.status_code, detail=response.text)

        project_audio_length = response.json().get('project_audio_length')
        return project_audio_length

    except httpx.RequestError as e:
        logger.error(f"HTTP-Fehler beim Anfragen des DB-Servers: {str(e)}")
        raise HTTPException(status_code=500, detail="Interner Serverfehler beim Kontaktieren des Datenbank-Servers")

    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {str(e)}")
        raise HTTPException(status_code=500, detail="Unbekannter Fehler")

async def client_db_project_audio_length_set(request: ProjectAudioLengthRequestWrite):
    url = "http://127.0.0.1:8010/projects/audio_length_set"

    # Den Authorization-Header aus der Pydantic-Anfrage lesen
    token = request.access_token
    if token:
        token = token if token.startswith("Bearer ") else f"Bearer {token}"
    headers = {"Authorization": token} if token else {}

    logger.info(f"Authorization-Header gefunden und weitergeleitet: {token}")

    # Status des Protokoll-Templates aus der Anfrage
    logger.info(f"Projekt-ID: {request.project_id}")

    # Anfrage an den Datenbank-Server weiterleiten
    try:
        async with httpx.AsyncClient() as client:
            json_data = {"project_id": str(request.project_id),"project_audio_length": str(request.project_audio_length)}
            logger.info(f"Sende Anfrage an {url} mit Body: {json_data}")
            response = await client.post(url, json=json_data, headers=headers)

        logger.info(f"Antwort vom DB-Server erhalten: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Fehlgeschlagene Antwort: {response.text}")
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return

    except httpx.RequestError as e:
        logger.error(f"HTTP-Fehler beim Anfragen des DB-Servers: {str(e)}")
        raise HTTPException(status_code=500, detail="Interner Serverfehler beim Kontaktieren des Datenbank-Servers")

    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {str(e)}")
        raise HTTPException(status_code=500, detail="Unbekannter Fehler")

async def client_db_project_estimations_set(request: ProjectEstimationRequestWrite):
    url = "http://127.0.0.1:8010/projects/project_estimations_set"

    # Den Authorization-Header aus der Pydantic-Anfrage lesen
    token = request.access_token
    if token:
        token = token if token.startswith("Bearer ") else f"Bearer {token}"
    headers = {"Authorization": token} if token else {}

    logger.info(f"Authorization-Header gefunden und weitergeleitet: {token}")

    # Status des Protokoll-Templates aus der Anfrage
    logger.info(f"Projekt-ID: {request.project_id}")

    # Anfrage an den Datenbank-Server weiterleiten
    try:
        async with httpx.AsyncClient() as client:
            json_data = {"project_id": str(request.project_id), "project_transcription_estimation": str(request.project_transcription_estimation), "project_summarization_estimation": str(request.project_summarization_estimation)}
            logger.info(f"Sende Anfrage an {url} mit Body: {json_data}")
            response = await client.post(url, json=json_data, headers=headers)

        logger.info(f"Antwort vom DB-Server erhalten: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Fehlgeschlagene Antwort: {response.text}")
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return

    except httpx.RequestError as e:
        logger.error(f"HTTP-Fehler beim Anfragen des DB-Servers: {str(e)}")
        raise HTTPException(status_code=500, detail="Interner Serverfehler beim Kontaktieren des Datenbank-Servers")

    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {str(e)}")
        raise HTTPException(status_code=500, detail="Unbekannter Fehler")



def client_db_refresh_access_token(refresh_token: Token) -> Token:
    """
    Sendet eine Anfrage an den Refresh-Token-Endpunkt des Servers,
    um einen neuen Access-Token zu erhalten und gibt diesen als Token-Objekt zurück.
    """
    url = "http://127.0.0.1:8010/tokens/tokens_access_server_get"  # Der korrekte Endpunkt
    headers = {"Content-Type": "application/json"}  # Setze den Content-Type-Header

    payload = {"refresh_token": refresh_token.token}  # Token im Body übergeben

    try:
        # HTTP POST-Anfrage an den Refresh-Endpunkt
        response = httpx.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Fehler werfen, falls der Statuscode nicht 2xx ist

        response_json = response.json()
        logger.info(f"Neuer Access-Token: {response_json['access_token']}")

        return Token(token=response_json["access_token"])  # Token als BaseModel zurückgeben
    except httpx.HTTPStatusError as e:
        logger.warning(f"Fehler beim Refresh-Token: {e.response.status_code} - {e.response.text}")
        raise RuntimeError(f"HTTP-Fehler beim Token-Refresh: {e.response.status_code}")
    except httpx.RequestError as e:
        logger.error(f"Netzwerkfehler beim Token-Refresh: {e}")
        raise RuntimeError("Netzwerkfehler beim Token-Refresh")
    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {e}")
        raise RuntimeError("Unerwarteter Fehler beim Token-Refresh")



def client_db_refresh_refresh_token(refresh_token: Token) -> Token:
    """
    Sendet eine Anfrage an den Refresh-Token-Endpunkt des Servers,
    um einen neuen refresh-Token zu erhalten und gibt diesen als Token-Objekt zurück.
    """
    url = "http://127.0.0.1:8010/tokens/tokens_access_server_get"
    headers = {"Content-Type": "application/json"}  # Setze den Content-Type-Header

    payload = {"refresh_token": refresh_token.token}  # Token im Body übergeben

    try:
        response = httpx.post(url, headers=headers, json=payload)  # Body mit json übergeben
        response.raise_for_status()  # Fehler werfen, falls der Statuscode nicht 2xx ist

        response_json = response.json()
        logger.info(f"Neuer Access-Token: {response_json['access_token']}")

        return Token(token=response_json["token"])
    except httpx.HTTPStatusError as e:
        logger.warning(f"Fehler beim Refresh-Token: {e.response.status_code} - {e.response.text}")
        raise RuntimeError(f"HTTP-Fehler beim Token-Refresh: {e.response.status_code}")
    except httpx.RequestError as e:
        logger.error(f"Netzwerkfehler beim Token-Refresh: {e}")
        raise RuntimeError("Netzwerkfehler beim Token-Refresh")
    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {e}")
        raise RuntimeError("Unerwarteter Fehler beim Token-Refresh")