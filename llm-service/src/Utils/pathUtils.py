import os

"""
    Diese Funktion gibt den Pfad zum Projektstammverzeichnis zurück.
    Der Pfad wird relativ zum aktuellen Skript ermittelt.
    """
def get_project_path():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    return project_root
