import json

def save_string_to_file(content: str, file_path: str) -> None:
    """
    Speichert einen String in eine Datei.

    :param content: Der zu speichernde String.
    :param file_path: Der Pfad zur Zieldatei.
    """
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def read_file_to_string(file_path: str) -> str:
    """
    Liest den Inhalt einer Datei als reinen String.

    :param file_path: Der Pfad zur Datei.
    :return: Der Dateiinhalt als String.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()



def json_file_to_string(file_path: str) -> str:
    """
    Liest eine .json-Datei ein und konvertiert ihren Inhalt in einen String.

    :param file_path: Der Pfad zur .json-Datei.
    :return: Der JSON-Inhalt als String.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            # Lade die JSON-Daten und konvertiere sie in einen String
            data = json.load(file)
            return json.dumps(data, indent=4, ensure_ascii=False)
    except FileNotFoundError:
        raise FileNotFoundError(f"Die Datei '{file_path}' wurde nicht gefunden.")
    except json.JSONDecodeError:
        raise ValueError(f"Die Datei '{file_path}' enthält kein gültiges JSON.")
