import json
from src.Classes.transcript_mini import TranscriptMini, SpeakerTranscript, Topic, Chapter
# from src.Utils.class_dict import utils_dict_to_obj

debug: bool = False


class NestedEntry:
    """
    Repräsentiert ein einzelnes Kapitel oder Unterkapitel im Inhaltsverzeichnis.
    """
    def __init__(self, title: str, chapters: list, chapter_id_string: str = ""):
        self.title = title
        self.text: str = ""
        self.note: str = ""
        self.chapters: list = chapters
        self.chapter_id_string = chapter_id_string

    def add_chapter(self, chapter):
        self.chapters.append(chapter)

    def clear_chapters(self):
        self.chapters.clear()

    def get_title(self):
        return self.title

    def set_title(self, title):
        self.title = title

    def get_nested_entry(self, index: int):
        return self.chapters[index]

    def set_nested_entry(self, entry, index: int):
        self.chapters[index] = entry

    def get_nested_entries(self):
        return self.chapters
    def set_nested_entries(self, nested_entries):
        self.chapters = nested_entries
    def get_chapter_id_string(self):
        return self.chapter_id_string
    def set_nested_chapter_id_string(self, chapter_id_string):
        self.chapter_id_string = chapter_id_string
    def get_text(self):
        return self.text
    def set_text(self, text):
        self.text = text
    def add_text(self, text):
        self.text += text
    def get_note(self):
        return self.note
    def set_note(self, note):
        self.note = note



class Group:
    def __init__(self, members: list[str]):
        self.members = members

    # GETTER, SETTER
    def get_members(self):
        return self.members
    def set_members(self, members):
        self.members = members



class Table:
    def __init__(self, name: str, nested_entries: list[NestedEntry]):
        self.name: str = name
        self.nested_entries: list[NestedEntry] = nested_entries
        self.nested_entries_overview_text: str = ""
        self.nested_entries_overview: list[NestedEntry] = []

    def get_nested_entries(self):
        return self.nested_entries
    def set_nested_entries(self, table: list[NestedEntry]):
        self.nested_entries: list[NestedEntry] = table
    def get_nested_entries_overview(self):
        return self.nested_entries_overview
    def get_name(self):
        return self.name
    def set_name(self, name):
        self.name = name
    def get_nested_entries_overview_text(self):
        return self.nested_entries_overview_text

    def generate_nested_entries_overview_helper(self, nested_entries, parent_number=""):
        """
        Rekursive Generierung der Unterkapitel.
        """
        sub_table_string_list = []
        sublevel = 1

        nested_entry: NestedEntry
        for nested_entry in nested_entries:
            # Füge nur einen Punkt hinzu, wenn der parent_number nicht bereits mit einem Punkt endet
            chapter_id_string = f"{parent_number}.{sublevel}" if not parent_number.endswith('.') else f"{parent_number}{sublevel}"

            # Stelle sicher, dass die Kapitelnummer nur einen Punkt am Ende hat
            if chapter_id_string.startswith('.'):
                chapter_id_string = chapter_id_string[1:]
            if not chapter_id_string.endswith('.'):
                chapter_id_string += '.'

            entry = NestedEntry(nested_entry.get_title(), [], chapter_id_string)
            sub_table_string_list.append(entry)

            if nested_entry and len(nested_entry.chapters) > 0:
                sub_table_string_list.extend(self.generate_nested_entries_overview_helper(nested_entry.chapters, chapter_id_string))

            sublevel += 1

        return sub_table_string_list

    def generate_nested_entries_overview(self):
        self.nested_entries_overview = self.generate_nested_entries_overview_helper(self.nested_entries, "")

        self.nested_entries_overview_text = "TOPICS:\n" + "\n".join(
            "TOPIC " + nested_entry.get_chapter_id_string() + " " + nested_entry.title
            for nested_entry in self.nested_entries_overview
        )


    def has_chapter(self, chapter_id_string: str) -> bool:
        """
        Checks in overview by id_string if a certain chapter exists.
        """
        nested_entry: NestedEntry
        for nested_entry in self.nested_entries_overview:
            if nested_entry.get_chapter_id_string() == chapter_id_string: return True
        return False

class Protocol:
    """
    Verwaltet separate Inhaltsverzeichnisse für öffentliche und vertrauliche Kapitel.
    """
    def __init__(self):
        self.public_table: Table = None
        self.trusted_table: Table = None

    def generate_all_table_string_list(self):
        self.public_table.generate_nested_entries_overview()
        self.trusted_table.generate_nested_entries_overview()

    def get_public_table(self):
        return self.public_table
    def get_trusted_table(self):
        return self.trusted_table


    def navigate_through_toc(self, nested_table_of_contents_type: str, path: list):
        """
        Navigiert durch das verschachtelte Inhaltsverzeichnis basierend auf dem gegebenen Pfad.
        :param nested_table_of_contents_type: Der Typ des Inhaltsverzeichnisses ('public' oder 'trusted')
        :param path: Der Pfad in Form einer Liste von Indizes (z.B. [1, 0, 3])
        :return: Das angeforderte Kapitel oder Unterkapitel (NestedEntry)
        """
        # Bestimme das entsprechende Inhaltsverzeichnis
        current_chapters: list[NestedEntry]
        if nested_table_of_contents_type == 'public':
            # nested_table_of_contents = self.nested_public_table_of_contents
            current_chapters: list[NestedEntry] = self.public_table.get_nested_entries()
        elif nested_table_of_contents_type == 'trusted':
            # nested_table_of_contents = self.nested_trusted_table_of_contents
            current_chapters: list[NestedEntry] = self.trusted_table.get_nested_entries()

        # Iteriere durch die 'path'-Liste, aber stoppe, wenn wir beim letzten Element angekommen sind
        for i, index in enumerate(path):
            # Debug-Ausgabe für den aktuellen Index und die verfügbaren Einträge
            print(f"Navigiere durch den Pfad: {path}, aktueller Index: {index}")
            print(f"Verfügbare Einträge an dieser Stelle: {[entry.get_title() for entry in current_chapters]}")

            # Überprüfe, ob der Index innerhalb der gültigen Grenzen liegt
            if index < 0 or index >= len(current_chapters):
                print(
                    f"Fehler: Der Index {index} ist außerhalb der gültigen Grenzen. Verfügbare Einträge: {len(current_chapters)}")
                raise IndexError(f"Ungültiger Index {index} beim Navigieren im Inhaltsverzeichnis.")

            # Wenn wir beim letzten Index in der Liste sind, greifen wir direkt auf das NestedEntry zu
            if i == len(path) - 1:
                return current_chapters[index]

            # von dem nächsten NestedEntry die NestedEntries nehmen um weiter zu navigieren
            current_chapters = current_chapters[index].get_nested_entries()

        # Falls der Pfad nicht korrekt war, gebe einen Fehler aus
        print(f"Fehler: Der Pfad {path} konnte nicht korrekt navigiert werden.")
        # return None  # Rückgabe von None im Fehlerfall, um anzuzeigen, dass der Pfad ungültig war
        raise IndexError
    def process_transcript(self, transcript_mini: TranscriptMini):
        """
        Verarbeitet das TranscriptMini-Objekt und fügt den Text in die verschachtelte Inhaltsstruktur ein,
        basierend auf den Topics, die im TranscriptMini gefunden werden.
        """

        topic: str = "1."
        new_topic : str = "1."
        topic_hierarchy_path:list[int] = [0]
        topic_path_new: list[int] = [0] # set the first TOPIC path to the first chapter as default. So all first SpeakerTranscripts WITHOUT any TOPIC assigned before gets automatically assigned to the first TOPIC.
        new_topic_text: str = ""
        nested_table_of_contents_type = "public"
        current_nested_entry: NestedEntry = self.navigate_through_toc(nested_table_of_contents_type, topic_hierarchy_path)


        # Iteriere über alle Einträge im TranscriptMini
        speaker_transcript: SpeakerTranscript
        for speaker_transcript in transcript_mini.get_speaker_transcripts():
            topics: list[Topic] = speaker_transcript.get_topics()

            # IF a TOPIC is there in index 0, update the chapter_new. Otherwise use the old chapter-
            if topics:
                chapter_new: Chapter = topics[0].get_chapter()
                topic_path_new: list[int] = chapter_new.get_chapter_path() # chapter path getten z.B. [1,2,1,1]

            try:
                # print("TOPIC HIERARCHY PATH: " + str(topic_hierarchy_path))

                if topic_hierarchy_path != topic_path_new: # FALLS ein neues topic beginnt
                    new_topic_text: str = ""  # den topic text zurücksetzen, FALLS ab jetzt ein neues TOPIC beginnt

                new_topic_text += speaker_transcript.get_text() + "\n\n" # text an das TOPIC anhängen
                # next_nested_entry: NestedEntry = self.navigate_through_toc(nested_table_of_contents_type, topic_path_new)
                current_nested_entry: NestedEntry = self.navigate_through_toc(nested_table_of_contents_type, topic_path_new)
                current_nested_entry.set_text(new_topic_text)  # Text des NestedEntry setzen


                topic_hierarchy_path = topic_path_new.copy() # den derzeitigen topic_hierarchy_path aktualisieren
            except IndexError:
                topic_hierarchy_path = topic_path_new.copy()  # den derzeitigen topic_hierarchy_path aktualisieren
                continue # weiter machen
        # new_topic_text: str = new_topic_text.strip("\n")
        # current_nested_entry.set_text(new_topic_text)

    def has_chapter(self, chapter_id_string):
        """
        Checks if a certain chapter id_string exists in given tables (should be all tables)
        """
        # if debug: print(f"Überprüfe Kapitel: {chapter_id_string}")  # Debugging: Kapitel, das überprüft wird

        # add all tables
        tables: list[Table] = [self.public_table, self.trusted_table]

        table: Table
        for table in tables:
            if table.has_chapter(chapter_id_string): return True
        return False

    def chapter_exists(self, chapter_number: str):
        """
        Überprüft, ob ein Kapitel in den öffentlichen oder vertraulichen Inhaltsverzeichnissen existiert.

        :param chapter_number: Die Kapitelnummer als String, z.B. "1.2" oder "2".
        :return: True, wenn das Kapitel existiert, andernfalls False.
        """
        return self.has_chapter(chapter_number)

    def get_public_toc(self):
        """
        Gibt das öffentliche Inhaltsverzeichnis zurück.
        """
        return self.public_toc

    def set_public_toc(self, chapters):
        """
        Setzt das öffentliche Inhaltsverzeichnis mit neuen Kapiteln.
        """
        self.public_toc = TableOfContents(chapters)

    def get_trusted_toc(self):
        """
        Gibt das vertrauliche Inhaltsverzeichnis zurück.
        """
        return self.trusted_toc

    def set_trusted_toc(self, chapters):
        """
        Setzt das vertrauliche Inhaltsverzeichnis mit neuen Kapiteln.
        """
        self.trusted_toc = TableOfContents(chapters)

    def print(self):
        """
        Gibt beide Inhaltsverzeichnisse aus.
        """
        if debug: print("\nÖffentliches Inhaltsverzeichnis:")
        self.public_toc.pretty_print()

        if debug: print("\nVertrauliches Inhaltsverzeichnis:")
        self.trusted_toc.pretty_print()

    def tablesToString(self):
        """
        Gibt beide Inhaltsverzeichnisse als formatierte Zeichenkette zurück.
        """
        #result = []
        #result.append("\nÖffentliches Inhaltsverzeichnis:")
        #for entry in self.public_toc.toc:
        #    result.append(str(entry))
#
        #result.append("\nVertrauliches Inhaltsverzeichnis:")
        #for entry in self.trusted_toc.toc:
        #    result.append(str(entry))
#
        #return "\n".join(result)
        tables: list[Table] = [self.public_table, self.trusted_table]
        text: str = ""
        for table in tables:
            text += table.get_name() + "\n" + table.nested_entries_overview_text + "\n"
        text += "\n"
        return text

    def troubleshoot(self):
        """
        TODO here are still many cases that needs to be fixed

        Troubleshoots parsing and logic related issues regarding the protocol_template that got converted from the protocol_template_json().
        This def must be executed after the Protocl got created from a dict.
        """

        # if public_table doesn't have any nested_entries
        if not self.public_table.get_nested_entries():
            self.public_table.nested_entries.append(NestedEntry(title="Protokoll", chapters=list()))

CLASS_MAPPING = {
    "Protocol": Protocol,
    "Group": Group,
    "Table": Table,
    "NestedEntry": NestedEntry
}

# def dict_to_obj(data):
#    return utils_dict_to_obj(data, CLASS_MAPPING)