from src.Api.api_db import project_status_get, protocol_template_status_set
from src.Api.api_llm import llm_summarize
from src.Schemes.api_schemes import ProjectRequestRead, ProjectStatus, ProtocolTemplateStatus, \
    ProjectStatusRequestWrite, ProtocolTemplateStatusRead, ProtocolTemplateStatusWrite, ProjectStatusRequestRead, \
    Approve
from fastapi import APIRouter, HTTPException, Depends
import httpx
import logging
import asyncio
from pydantic import BaseModel
from src.Client.client_db import client_db_refresh_access_token
from src.Schemes.api_schemes import Token, Unapprove

router = APIRouter()

# Logging einrichten
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")




@router.post("/protocol_template/approve")
async def protocol_template_approve(request: Approve = Depends(Approve.from_request)):
    """
    protocol_template_approve und protocol_template_unapprove:

    Es ist sinnvoll im Frontend vor diesem API Aufruf das protocol_template zu speichern. Es ist intuitiver, das aktuelle editierte Protokoll beim entgültigen bestätigen zu verwenden bzw. zu speichern.

    Diese 2 Funktionen sorgen dafür, dass die Zusammenfassung automatisch eingeleitet wird, sobald die Transkribierung fertig ist UND das ProtokollTemplate vom User fertig erstellt wurde.
    Dabei kann der User den Zustand des ProtokollTemplate (solange die Zusammenfassung noch nicht gestartet wurde) zwischen true und false wechseln und damit mögliche Fehler korrigieren. Wenn dann die Transkribierung fertig ist wird die Zusammenfassung gestartet und die Bearbeitung verboten.
    Es ist performant, weil diese Überprüfung lediglich in den 2 unteren API Funktionen durchgeführt werden:
        1. Wenn der User den ProjectTemplate status auf true (fertiggestellt) setzt (1. Funktion)
        2. wenn die Transkribierung fertig ist (2. Funktion)
    """
    from src.Api.api_db import protocol_template_status_get

    logger.info("protocol_template should be approved")


    refresh_token: Token = Token(token=request.refresh_token)
    access_token: Token = client_db_refresh_access_token(refresh_token)

    # Um das ProjectTemplate zu approven, muss es unapproved sein. Denn man kann/SOLL ES NICHT 2 mal hintereinander approven.
    # TODO wegen dem 2 mal hintereinander approven muss noch ein schutz eingebaut werden, damit nicht 2 LLM Zusammenfassungsanfragen geschickt werden
    project_template_status: ProjectStatus = await protocol_template_status_get(ProtocolTemplateStatusRead(project_id=request.project_id, access_token=access_token.token))

    # 1. Wenn project_template_status bereits approved ist dann soll es nicht nochmal approved werden
    # 2. Wenn project_template_status locked ist dann darf es nicht approved werden
    if project_template_status == ProtocolTemplateStatus.approved or project_template_status == ProtocolTemplateStatus.locked:
        error_str = f"Error: Cannot approve ProtocolTemplate. ProtocolTemplate status should have status {ProtocolTemplateStatus.unapproved} to call this method but instead has status {project_template_status}"
        logger.error(error_str)
        raise HTTPException(status_code=409, detail=error_str)

    # Falls Projektstatus noch nicht in der Zusammenfassung ist bzw. noch nicht zusammengefasst wurde: Das ProtocolTemplate kann noch bearbeitet werden
    project_status: ProjectStatus = await project_status_get(ProjectStatusRequestRead(access_token=access_token.token, project_id=request.project_id))
    if not(project_status == ProjectStatus.INITIAL or project_status == ProjectStatus.IS_TRANSCRIBING or project_status == ProjectStatus.TRANSCRIBED):
        error_str = f"Error: Cannot approve ProtocolTemplate project has wrong status. Project should have status {ProjectStatus.INITIAL} or {ProjectStatus.IS_TRANSCRIBING} or {ProjectStatus.TRANSCRIBED} but instead has status {project_status}"
        logger.error(error_str)
        raise HTTPException(status_code=409, detail=error_str)



    # Starte die Zusammenfassung asynchron im Hintergrund
    if project_status == ProjectStatus.TRANSCRIBED:
        # ProjectTemplateStatus LOCKEN damit es nicht mehr bearbeitet werden kann
        await protocol_template_status_set(ProtocolTemplateStatusWrite(access_token=access_token.token, project_id=request.project_id, protocol_template_status=ProtocolTemplateStatus.locked))
        asyncio.create_task(llm_summarize(ProjectRequestRead(project_id=request.project_id), refresh_token))
        return {"message": "ProtocolTemplate approved. Summarization will be started asynchronously.", "status_code": 200}


    await protocol_template_status_set(ProtocolTemplateStatusWrite(access_token=access_token.token, project_id=request.project_id, protocol_template_status=ProtocolTemplateStatus.approved))
    return {"message": "ProtocolTemplate approved. When the transcription finishes in future, the summarization will be started.", "status_code": 200}



@router.post("/protocol_template/unapprove")
async def protocol_template_unapprove(request: Unapprove = Depends(ProtocolTemplateStatusRead.from_request)):
    """
    protocol_template_approve und protocol_template_unapprove:

    Diese 2 Funktionen sorgen dafür, dass die Zusammenfassung automatisch eingeleitet wird, sobald die Transkribierung fertig ist UND das ProtokollTemplate vom User fertig erstellt wurde.
    Dabei kann der User den Zustand des ProtokollTemplate (solange die Zusammenfassung noch nicht gestartet wurde) zwischen true und false wechseln und damit mögliche Fehler korrigieren. Wenn dann die Transkribierung fertig ist wird die Zusammenfassung gestartet und die Bearbeitung verboten.
    Es ist performant, weil diese Überprüfung lediglich in den 2 unteren API Funktionen durchgeführt werden:
        1. Wenn der User den ProjectTemplate status auf true (fertiggestellt) setzt (1. Funktion)
        2. wenn die Transkribierung fertig ist (2. Funktion)
    """
    from src.Api.api_db import protocol_template_status_get

    logger.info("protocol_template should be unapproved")


    # Um das ProjectTemplate zu unapproven, muss es approved sein.
    project_template_status: ProjectStatus = await protocol_template_status_get(request)

    # 1. Wenn project_template_status bereits unapproved ist dann soll es nicht nochmal unapproved werden
    # 2. Wenn project_template_status locked ist dann darf es nicht unapproved werden
    if project_template_status == ProtocolTemplateStatus.unapproved or project_template_status == ProtocolTemplateStatus.locked:
        error_str = f"Error: Cannot unapprove ProtocolTemplate. ProjectTemplate status should have status {ProtocolTemplateStatus.approved} to call this method but instead has status {project_template_status}"
        logger.error(error_str)
        raise HTTPException(status_code=409, detail=error_str)

    # Falls Projektstatus noch nicht in der Zusammenfassung ist bzw. noch nicht zusammengefasst wurde: Das ProtocolTemplate kann noch bearbeitet werden
    project_status: ProjectStatus = await project_status_get(ProjectStatusRequestRead(access_token=request.access_token, project_id=request.project_id))
    if not(project_status == ProjectStatus.INITIAL or project_status == ProjectStatus.IS_TRANSCRIBING):
        error_str = f"Error: Cannot unapprove ProjectTemplate because project has wrong status. Project should have status {ProjectStatus.INITIAL} or {ProjectStatus.IS_TRANSCRIBING} but instead has status {project_status}"
        logger.error(error_str)
        raise HTTPException(status_code=409, detail=error_str)


    await protocol_template_status_set(ProtocolTemplateStatusWrite(access_token=request.access_token, project_id=request.project_id, protocol_template_status=ProtocolTemplateStatus.unapproved))
    return {"message": "ProtocolTemplate unapproved. When the transcription finishes in future, the summarzation will only start AFTER the ProtocolTemplate has been approved.", "status_code": 200}