from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from enum import StrEnum
from fastapi import Header
from datetime import datetime

"""
Scheme for generating a request to the database to read something from it
"""
class ProjectRequestRead(BaseModel):
    project_id: UUID


# Modell für Tokens (Access- und Refresh-Tokens)
class Token(BaseModel):
    token: str            # Refresh-Token für das Erneuern von Access-Tokens

"""
Scheme for generating a request to the database to write a dict to it
"""
class ProjectRequestWriteDict(BaseModel):
    project_id: UUID
    data: dict

class User(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str


# Status-Enum für Projekte
class ProjectStatus(StrEnum):
    INITIAL = "initial"
    IS_TRANSCRIBING = "is_transcribing"
    TRANSCRIBED = "transcribed"
    IS_SUMMARIZING = "is_summarizing"
    COMPLETED = "completed"

class ProjectAudioLengthRequestRead(BaseModel):
    project_id: UUID
    access_token: str

    @classmethod
    def from_request(cls, request: dict, authorization: str = Header(...)):
        # Hier den Authorization-Header auslesen und in das Objekt einfügen
        return cls(**request, access_token=authorization)

class ProjectAudioLengthRequestWrite(BaseModel):
    project_id: UUID
    project_audio_length: int
    access_token: str

    @classmethod
    def from_request(cls, request: dict, authorization: str = Header(...)):
        # Hier den Authorization-Header auslesen und in das Objekt einfügen
        return cls(**request, access_token=authorization)

class ProjectEstimationRequestWrite(BaseModel):
    """Anfragemodell für die Änderung des Projektzugriffs."""
    project_id: UUID
    project_transcription_estimation: datetime
    project_summarization_estimation: datetime
    access_token: str

    @classmethod
    def from_request(cls, request: dict, authorization: str = Header(...)):
        # Hier den Authorization-Header auslesen und in das Objekt einfügen
        return cls(**request, access_token=authorization)

class ProjectStatusRequestWrite(BaseModel):
    """Anfragemodell für die Änderung des Projektzugriffs."""
    project_id: UUID
    project_status: ProjectStatus
    access_token: str

    @classmethod
    def from_request(cls, request: dict, authorization: str = Header(...)):
        # Hier den Authorization-Header auslesen und in das Objekt einfügen
        return cls(**request, access_token=authorization)

class ProjectStatusRequestRead(BaseModel):
    """Anfragemodell für die Überprüfung des Projektzugriffs."""
    project_id: UUID
    access_token: str

    @classmethod
    def from_request(cls, request: dict, authorization: str = Header(...)):
        # Hier den Authorization-Header auslesen und in das Objekt einfügen
        return cls(**request, access_token=authorization)

# Enum für den neuen Status
class ProtocolTemplateStatus(StrEnum):
    approved = 'approved'
    unapproved = 'unapproved'
    locked = 'locked'


class Approve(BaseModel):
    project_id: UUID
    refresh_token: str  # Hier den Authorization-Header hinzufügen

    @classmethod
    def from_request(cls, request: dict, authorization: str = Header(...)):
        # Hier den Authorization-Header auslesen und in das Objekt einfügen
        return cls(**request, refresh_token=authorization)

class Unapprove(BaseModel):
    project_id: UUID
    access_token: str  # Hier den Authorization-Header hinzufügen

    @classmethod
    def from_request(cls, request: dict, authorization: str = Header(...)):
        # Hier den Authorization-Header auslesen und in das Objekt einfügen
        return cls(**request, access_token=authorization)

class ProtocolTemplateStatusRead(BaseModel):
    project_id: UUID
    access_token: str  # Hier den Authorization-Header hinzufügen

    @classmethod
    def from_request(cls, request: dict, authorization: str = Header(...)):
        # Hier den Authorization-Header auslesen und in das Objekt einfügen
        return cls(**request, access_token=authorization)

# Die Pydantic-Klasse für den Request
class ProtocolTemplateStatusWrite(BaseModel):
    project_id: UUID
    protocol_template_status: ProtocolTemplateStatus
    access_token: str

    @classmethod
    def from_request(cls, request: dict, authorization: str = Header(...)):
        # Hier den Authorization-Header auslesen und in das Objekt einfügen
        return cls(**request, access_token=authorization)


# Transkription ausführen
# Request Token muss übergeben werden damit wenn der User ausgeloggt ist und die Transkription abschmiert ein neuer access_token generiert werden kann um eine erneute Transkription zu startem
class ProjectRequestReadTranscribe(BaseModel):
    project_id: UUID
    min_speakers: int
    max_speakers: int
    refresh_token: str

    @classmethod
    def from_request(cls, request: dict, authorization: str = Header(...)):
        # Hier den Authorization-Header auslesen und in das Objekt einfügen
        return cls(**request, refresh_token=authorization)