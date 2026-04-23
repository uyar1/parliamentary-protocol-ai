"""
API and API with Http requests for bb_backend_db
This API receives requests and sends them to bb_backend_db PstgreSQL and interact with its database

"""

from fastapi import APIRouter, Form, File, UploadFile, HTTPException, Depends
import httpx
from fastapi.responses import StreamingResponse
from io import BytesIO
import logging

from Schemes.api_schemes import ProjectEstimationRequestWrite
from src.Schemes.api_schemes import ProjectRequestRead, ProjectRequestWriteDict, ProtocolTemplateStatusRead, \
    ProjectStatusRequestRead, User, ProjectStatusRequestWrite, ProtocolTemplateStatusWrite

# Logging einrichten
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
router = APIRouter()




@router.post("/protocol_template/protocol_template_status_get")
async def protocol_template_status_get(request: ProtocolTemplateStatusRead = Depends(ProtocolTemplateStatusRead.from_request)):
    url_protocol_template_status_get = "http://127.0.0.1:8010/projects/protocol_template_status_get"
    logger.info("Neue Anfrage empfangen für /protocol_template/protocol_template_status_get")

    # Den Authorization-Header aus der Pydantic-Anfrage lesen
    token = request.access_token
    if token:
        token = token if token.startswith("Bearer ") else f"Bearer {token}"
    headers = {"Authorization": token} if token else {}

    logger.info(f"Authorization-Header gefunden und weitergeleitet: {token}")

    # Status des Protokoll-Templates aus der Anfrage
    logger.info(f"Protokoll-Template-Status: {request.project_id}")

    # Anfrage an den Datenbank-Server weiterleiten
    try:
        async with httpx.AsyncClient() as client:
            json_data = {"project_id": str(request.project_id)}
            logger.info(f"Sende Anfrage an {url_protocol_template_status_get} mit Body: {json_data}")
            response = await client.post(url_protocol_template_status_get, json=json_data, headers=headers)

        logger.info(f"Antwort vom DB-Server erhalten: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Fehlgeschlagene Antwort: {response.text}")
            raise HTTPException(status_code=response.status_code, detail=response.text)

        protocol_template_status = response.json().get('protocol_template_status')
        return protocol_template_status

    except httpx.RequestError as e:
        logger.error(f"HTTP-Fehler beim Anfragen des DB-Servers: {str(e)}")
        # raise HTTPException(status_code=500, detail="Interner Serverfehler beim Kontaktieren des Datenbank-Servers")
        raise e

    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {str(e)}")
        raise HTTPException(status_code=500, detail="Unbekannter Fehler")


@router.post("/protocol_template/protocol_template_status_set")
async def protocol_template_status_set(request: ProtocolTemplateStatusWrite = Depends(ProtocolTemplateStatusWrite.from_request)):
    url_protocol_template_status_set = "http://127.0.0.1:8010/projects/protocol_template_status_set"
    logger.info("Neue Anfrage empfangen für /protocol_template/protocol_template_status_set")

    # Den Authorization-Header aus der Pydantic-Anfrage lesen
    token = request.access_token
    if token:
        token = token if token.startswith("Bearer ") else f"Bearer {token}"
    headers = {"Authorization": token} if token else {}

    logger.info(f"Authorization-Header gefunden und weitergeleitet: {token}")
    logger.info(f"Protokoll-Template-Status: {request.protocol_template_status}")

    # Anfrage an den Datenbank-Server weiterleiten
    try:
        async with httpx.AsyncClient() as client:
            json_data = {"project_id": str(request.project_id), "protocol_template_status": str(request.protocol_template_status)}
            logger.info(f"Sende Anfrage an {url_protocol_template_status_set} mit Body: {json_data}")
            response = await client.post(url_protocol_template_status_set, json=json_data, headers=headers)

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




@router.post("/protocol_template/project_status_get")
async def project_status_get(request: ProjectStatusRequestRead = Depends(ProjectStatusRequestRead.from_request)):
    url_project_status_get = "http://127.0.0.1:8010/projects/project_status_get"
    logger.info("Neue Anfrage empfangen für /protocol_template/project_status_get")

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
            logger.info(f"Sende Anfrage an {url_project_status_get} mit Body: {json_data}")
            response = await client.post(url_project_status_get, json=json_data, headers=headers)

        logger.info(f"Antwort vom DB-Server erhalten: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Fehlgeschlagene Antwort: {response.text}")
            raise HTTPException(status_code=response.status_code, detail=response.text)

        project_status = response.json().get('project_status')
        return project_status

    except httpx.RequestError as e:
        logger.error(f"HTTP-Fehler beim Anfragen des DB-Servers: {str(e)}")
        raise HTTPException(status_code=500, detail="Interner Serverfehler beim Kontaktieren des Datenbank-Servers")

    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {str(e)}")
        raise HTTPException(status_code=500, detail="Unbekannter Fehler")


@router.post("/protocol_template/project_status_set")
async def project_status_set(request: ProjectStatusRequestWrite = Depends(ProjectStatusRequestWrite.from_request)):
    url_project_status_set = "http://127.0.0.1:8010/projects/project_status_set"
    logger.info("Neue Anfrage empfangen für /protocol_template/project_status_set")

    # Den Authorization-Header aus der Pydantic-Anfrage lesen
    token = request.access_token
    headers = {"Authorization": token} if token else {}

    logger.info(f"Authorization-Header gefunden und weitergeleitet: {token}")

    # Status des Protokoll-Templates aus der Anfrage
    logger.info(f"Protokoll-Template-Status: {request.project_status}")

    # Anfrage an den Datenbank-Server weiterleiten
    try:
        async with httpx.AsyncClient() as client:
            json_data = {"project_id": str(request.project_id), "project_status": request.project_status}
            logger.info(f"Sende Anfrage an {url_project_status_set} mit Body: {json_data}")
            response = await client.post(url_project_status_set, json=json_data, headers=headers)

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


'''
@router.post("/bb_backend_db/projects/project_template_status_set")
async def protocol_template_status_set(request: ProjectTemplateWriteRequestStatus):
    """
    Writes/updates a (new) status to the corresponding project in the database
    """
    project_id = request.project_id
    url = "http://127.0.0.1:8010/projects/status_set"
    json_data = {"project_id": str(project_id), "project_template_status": request.status}
    return await httpx_send_json(url, json=json_data)



@router.post("/bb_backend_db/projects/project_template_status_get")
async def protocol_template_status_get(request: ProjectRequestRead):
    """
    Reads the status from the corresponding project in the database
    """
    project_id = request.project_id
    url = "http://127.0.0.1:8010/projects/status_get"
    json_data = {"project_id": str(project_id)}
    response = await httpx_send_json(url, json=json_data)
    return response.get('status')

'''

'''
@router.post("/bb_backend_db/projects/project_status_set")
async def project_status_set(request: ProjectWriteRequestStatus):
    """
    Writes/updates a (new) status to the corresponding project in the database
    """
    project_id = request.project_id
    url = "http://127.0.0.1:8010/projects/project_status_set"
    json_data = {"project_id": str(project_id), "status": request.status}
    return await httpx_send_json(url, json=json_data)

@router.post("/bb_backend_db/projects/project_status_get")
async def project_status_get(request: ProjectRequestRead):
    """
    Reads the status from the corresponding project in the database
    """
    project_id = request.project_id
    url = "http://127.0.0.1:8010/projects/status_get"
    json_data = {"project_id": str(project_id)}
    response = await httpx_send_json(url, json=json_data)
    return response.get('status')

'''


@router.post("/bb_backend/db_create_user/")
async def db_create_user(user: User):
    data = user.model_dump()  # Pydantic-Daten in ein Dictionary umwandeln
    url = "http://127.0.0.1:8000/users"
    try:
        response = httpx.post(url, json=data, timeout=10)  # Timeout auf 10 Sekunden setzen
        response.raise_for_status()  # Überprüfe auf HTTP-Fehler
        return {"status_code": response.status_code}
    except httpx.RequestError as e:
        return {"error": f"Request failed: {e}"}
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error occurred: {e}"}

async def httpx_send_json(url: str, json: dict, timeout: int = 10):
    """
    send specific json request with httpx to specific url with specific timeout
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=json, timeout=timeout)
            response.raise_for_status()
        return response.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {e}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"HTTP error occurred: {e}")


@router.post("/bb_backend_db/transcript_read")
async def transcript_read(request: ProjectRequestRead):
    """
    Reads transcript json from project project_id from the backend for processing.
    Returns json from database.
    """
    project_id = request.project_id
    url = "http://127.0.0.1:8010/transcript_read"
    json_data = {"project_id": str(project_id)}
    return await httpx_send_json(url, json=json_data)

@router.post("/bb_backend_db/transcript_write")
async def transcript_write(request: ProjectRequestWriteDict):
    """
    Writes transcript json to project project_id to the backend for processing.
    """
    project_id = request.project_id
    url = "http://127.0.0.1:8010/transcript_write"
    json_data = {"project_id": str(project_id), "data": request.data}
    return await httpx_send_json(url, json=json_data)

@router.post("/bb_backend_db/transcript_mini_read")
async def transcript_mini_read(request: ProjectRequestRead):
    """
    Reads transcript_mini json from project project_id from the backend for processing.
    Returns json from database.
    """
    project_id = request.project_id
    url = "http://127.0.0.1:8010/transcript_mini_read"
    json_data = {"project_id": str(project_id)}
    return await httpx_send_json(url, json=json_data)

@router.post("/bb_backend_db/transcript_mini_write")
async def transcript_mini_write(request: ProjectRequestWriteDict):
    """
    Writes transcript json to project project_id to the backend for processing.
    """
    project_id = request.project_id
    url = "http://127.0.0.1:8010/transcript_mini_write"
    json_data = {"project_id": str(project_id), "data": request.data}
    return await httpx_send_json(url, json=json_data)

@router.post("/bb_backend_db/protocol_read")
async def protocol_read(request: ProjectRequestRead):
    """
    Reads transcript json from project project_id from the backend for processing.
    Returns json from database.
    """
    project_id = request.project_id
    url = "http://127.0.0.1:8010/protocol_read"
    json_data = {"project_id": str(project_id)}
    return await httpx_send_json(url, json=json_data)

@router.post("/bb_backend_db/protocol_write")
async def protocol_write(request: ProjectRequestWriteDict):
    """
    Writes transcript json to project project_id to the backend for processing.
    """
    project_id = request.project_id
    url = "http://127.0.0.1:8010/protocol_write"
    json_data = {"project_id": str(project_id), "data": request.data}
    return await httpx_send_json(url, json=json_data)

@router.post("/bb_backend_db/protocol_template_read")
async def protocol_template_read(request: ProjectRequestRead):
    """
    Reads transcript json from project project_id from the backend for processing.
    Returns json from database.
    """
    project_id = request.project_id
    url = "http://127.0.0.1:8010/protocol_template_read"
    json_data = {"project_id": str(project_id)}
    return await httpx_send_json(url, json=json_data)

@router.post("/bb_backend_db/protocol_template_write")
async def transcript_template_write(request: ProjectRequestWriteDict):
    """
    Writes transcript json to project project_id to the backend for processing.
    """
    project_id = request.project_id
    url = "http://127.0.0.1:8010/protocol_template_write"
    json_data = {"project_id": str(project_id), "data": request.data}
    return await httpx_send_json(url, json=json_data)







@router.post("/bb_backend_db/audio_read")
async def audio_read(request: ProjectRequestRead):
    """
    Liest die Audio-Datei aus der Datenbank anhand der project_id und gibt sie als Datei zurück.
    """
    project_id = request.project_id
    url = "http://127.0.0.1:8010/audio_read"
    json_data = {"project_id": str(project_id)}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=json_data, timeout=10)

            # Falls der Antwort-Statuscode nicht OK ist, raise Exception
            response.raise_for_status()

            # Hier wird angenommen, dass die Antwort eine Audio-Datei enthält.
            # Wir extrahieren den binären Inhalt der Antwort
            audio_content = response.content


            # Speichern der Datei im RAM
            audio_file = BytesIO(audio_content)

            audio_file.seek(0)

            # Gebe die Datei als FileResponse zurück, ohne sie auf der Festplatte zu speichern
            return StreamingResponse(audio_file,
                                headers={'Content-Disposition': 'attachment; filename="audio.wav"'})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/bb_backend_db/audio_read_stream")
async def audio_read_stream(request: ProjectRequestRead):
    """
    Liest die Audio-Datei aus der Datenbank anhand der project_id und gibt sie als Datei zurück.
    """
    project_id = request.project_id
    url = "http://127.0.0.1:8010/audio_read"
    json_data = {"project_id": str(project_id)}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=json_data, timeout=10)

            # Falls der Antwort-Statuscode nicht OK ist, raise Exception
            response.raise_for_status()

            # Hier wird angenommen, dass die Antwort eine Audio-Datei enthält.
            # Wir extrahieren den binären Inhalt der Antwort
            audio_content = response.content

            # Gebe den Inhalt direkt als StreamingResponse zurück
            content_type = response.headers.get('Content-Type', 'application/octet-stream')
            return StreamingResponse(BytesIO(audio_content), media_type=content_type,
                                     headers={'Content-Disposition': 'attachment; filename="audio.wav"'})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bb_backend_db/audio_write")
async def audio_write(
        project_id: str = Form(...),
        file: UploadFile = File(...),
):
    """
    Writes transcript json and the audio file to project project_id to the backend for processing.
    """
    url = "http://127.0.0.1:8010/audio_write"

    # Prepare the form data
    files = {'file': (file.filename, file.file, file.content_type)}
    form_data = {'project_id': project_id}

    try:
        # Make an async HTTP request with file and other data
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=form_data, files=files, timeout=10)
            response.raise_for_status()
        return response.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {e}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"HTTP error occurred: {e}")



@router.post("/bb_backend_db/docx_generate_read")
async def docx_generate_read(request: ProjectRequestRead):
    """
    Generiert die protocol.docx Datei von protocol.json aus der Cloud anhand der project_id und gibt sie als Datei zurück.
    """
    project_id = request.project_id
    url_generate = "http://127.0.0.1:8010/docx_generate"
    url_read = "http://127.0.0.1:8010/docx_read"
    json_data = {"project_id": str(project_id)}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url_generate, json=json_data, timeout=10)

            # Falls der Antwort-Statuscode nicht OK ist, raise Exception
            response.raise_for_status()

            # falls response nicht okay iist, zurückgeben
            if not response.status_code == 200:
                return response.json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url_read, json=json_data, timeout=10)

            # Falls der Antwort-Statuscode nicht OK ist, raise Exception
            response.raise_for_status()

            # Wir extrahieren den binären Inhalt der Antwort
            docx_content = response.content

            # Speichern der Datei im RAM
            docx_file = BytesIO(docx_content)

            docx_file.seek(0)

            # Gebe die Datei als FileResponse zurück, ohne sie auf der Festplatte zu speichern
            return StreamingResponse(docx_file,
                                headers={'Content-Disposition': 'attachment; filename="protocol.docx"'})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


router.post("/bb_backend_db/docx_read")
async def docx_read(request: ProjectRequestRead):
    """
    Liest die protocol.docx Datei aus der Cloud anhand der project_id und gibt sie als Datei zurück.
    """
    project_id = request.project_id
    url = "http://127.0.0.1:8010/docx_read"
    json_data = {"project_id": str(project_id)}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=json_data, timeout=10)

            # Falls der Antwort-Statuscode nicht OK ist, raise Exception
            response.raise_for_status()

            # Wir extrahieren den binären Inhalt der Antwort
            docx_content = response.content

            # Speichern der Datei im RAM
            docx_file = BytesIO(docx_content)

            docx_file.seek(0)

            # Gebe die Datei als FileResponse zurück, ohne sie auf der Festplatte zu speichern
            return StreamingResponse(docx_file,
                                headers={'Content-Disposition': 'attachment; filename="protocol.docx"'})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


router.post("/bb_backend_db/docx_generate")
async def docx_generate(request: ProjectRequestRead):
    """
    Generiert die protocol.docx von protocol.json
    """
    project_id = request.project_id
    url = "http://127.0.0.1:8010/docx_generate"
    json_data = {"project_id": str(project_id)}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=json_data, timeout=10)

            # Falls der Antwort-Statuscode nicht OK ist, raise Exception
            response.raise_for_status()

            # Gebe die Datei als FileResponse zurück, ohne sie auf der Festplatte zu speichern
            return response.json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))