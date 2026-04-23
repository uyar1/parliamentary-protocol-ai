# utils_estimations.py

import wave
from datetime import datetime, timedelta
from typing import Tuple

def get_audio_duration_seconds(wav_path: str) -> int:
    """Bestimmt die Dauer einer .wav-Datei in Sekunden (ganzzahlig, abgerundet)."""
    with wave.open(wav_path, 'rb') as audio:
        frames = audio.getnframes()
        rate = audio.getframerate()
        return int(frames / float(rate))

def calculate_estimations(duration_seconds: float) -> Tuple[datetime, datetime]:
    """Berechnet ETA-Zeitpunkte auf Basis der Audiodauer."""
    now = datetime.now()
    transcription_eta = now + timedelta(seconds=duration_seconds / 20)

    summarization_duration = 1.0 * duration_seconds
    summarization_eta = now + timedelta(seconds=summarization_duration)

    return transcription_eta, summarization_eta


def get_estimations_from_file(wav_path: str) -> Tuple[datetime, datetime]:
    """
    Kombiniert Dauerermittlung und ETA-Berechnung in einem Schritt.
    Gibt Transkriptions-ETA und Zusammenfassungs-ETA zurück.
    """
    duration = get_audio_duration_seconds(wav_path)
    return calculate_estimations(duration)
