import json
import re
from typing import List

from anyio import current_effective_deadline


# from src.Utils.class_dict import utils_dict_to_obj


class Sentence:
    def __init__(self, start, text, speaker):
        self.start: str = start  # Timestamp für den Satz
        self.text: str = text  # Der Text des Satzes
        self.speaker: str = speaker

    def __str__(self):
        return f"{self.start}: {self.text}"

    def to_string(self):
        return f"{self.start}: {self.text}"
    def get_speaker(self):
        return self.speaker
    def set_speaker(self, speaker: str):
        self.speaker = speaker
    def get_text(self):
        return self.text
    def set_text(self, text: str):
        self.text = text


def validate_and_clean_chapter_string(chapter_str: str) -> str | None:
    # Matches z. B. 5.1. oder 7.4.3.
    if re.fullmatch(r"\d+(\.\d+)*\.", chapter_str):
        return chapter_str
    # Matches z. B. 5.1 oder 7.4.3 → füge Punkt hinzu
    elif re.fullmatch(r"\d+(\.\d+)*", chapter_str):
        return chapter_str + "."
    else:
        return None


class Chapter:
    def chapter_string_to_chapter_path(self, chapter_string: str):
        chapter_path: list[int] = []  # chapter path, hierarchy path to chapter
        chapter_path_string = chapter_string.split(".")  # chapter string path string

        # Entfernen des letzten leeren Eintrags, falls leer
        if chapter_path_string[-1] == "":
            chapter_path_string = chapter_path_string[:-1]
        for x in chapter_path_string:
            try:
                chapter_path.append(int(x) - 1)
            except ValueError:
                break
        return chapter_path

    def chapter_path_to_chapter_string(self, chapter_path: list[int]):
        return '.'.join(map(str, chapter_path)) + '.'

    def __init__(self, chapter_input):
        if isinstance(chapter_input, list):
            self.chapter_path = chapter_input
            self.chapter_string: str = ""
        elif isinstance(chapter_input, str):
            cleaned = validate_and_clean_chapter_string(chapter_input)
            if cleaned is None:
                raise ValueError(f"Ungültiges Kapitel: {chapter_input}")
            self.chapter_string = cleaned
            self.chapter_path = self.chapter_string_to_chapter_path(self.chapter_string)
        else:
            raise TypeError("Input must be either a list of strings or a single string.")

    # GETTER and SETTER
    def get_chapter_string(self):
        return self.chapter_string
    def set_chapter_string(self, chapter_string: str):
        self.chapter_string = chapter_string
        self.chapter_path = self.chapter_string_to_chapter_path(self.chapter_string)
    def get_chapter_path(self):
        return self.chapter_path
    def set_chapter_path(self, chapter_path: list[int]):
        self.chapter_path = chapter_path
        self.chapter_string = self.chapter_string_to_chapter_path(self.chapter_string)

    def is_later_chapter(self, other_chapter):
        """
        Check if self is a later chapter than other_chapter.
        :param other_chapter: Chapter object to compare with
        :return: True if self is a later chapter, False otherwise
        """
        # Compare the chapter paths element by element
        for self_part, other_part in zip(self.chapter_path, other_chapter.get_chapter_path()):
            if self_part > other_part:
                return True
            elif self_part < other_part:
                return False

        # If all compared parts are equal, check if self has more levels (is more specific)
        return len(self.chapter_path) > len(other_chapter.get_chapter_path())



class Topic:
    def __init__(self, chapter: 'Chapter', title: str, timestamp: str):
        if not self._is_valid_timestamp(timestamp):
            raise ValueError(f"Ungültiger Timestamp: '{timestamp}'. Erwartet wird das Format ZAHL.ZAHL (z.B. '12.34').")
        self.chapter: Chapter = chapter
        self.title: str = title
        self.timestamp: str = timestamp

    @staticmethod
    def _is_valid_timestamp(timestamp: str) -> bool:
        return re.fullmatch(r'\d+\.\d+', timestamp) is not None

    # GETTER, SETTER, APPENDER, REMOVER
    def get_chapter(self):
        return self.chapter
    def set_chapter(self, chapter: Chapter):
        self.chapter = chapter
    def get_title(self):
        return self.title
    def set_title(self, title: str):
        self.title = title
    def get_timestamp(self):
        return self.timestamp
    def set_timestamp(self, timestamp: str):
        self.timestamp = timestamp
    def is_later_topic(self, other_topic):
        """
        returns if another topic is TOPIC wise later than this topic.
        """
        return self.get_chapter().is_later_chapter(other_topic.get_chapter())


def topic_list_contains_chapter_title(list_topic: list[Topic], chapter_title: str) -> bool:
    """
    Checks if a list of Topics contains a chapter_title (chapter_string). If it contains, returns True. If not contains, return False.
    """

    # cleans chapter TOPIC at first. For instance makes TOPIC 3.3 to 3.3. or 4 to 4. to enshure correct comparision.
    # TODO I don't like this solution by "cleaning" a TOPIC string. There needs to be implemented a better solution.
    cleaned = validate_and_clean_chapter_string(chapter_title)
    if cleaned is None:
        raise ValueError(f"Ungültiges Kapitel: {chapter_title}")

    for topic in list_topic:
        if topic.get_chapter().get_chapter_string() == cleaned:
            return True
    return False


class SpeakerTranscript:
    def __init__(self, speaker: str, text: str, sentences: list[Sentence], topics: list[Topic]):
        self.speaker: str = speaker
        self.text: str = text
        self.sentences: list[Sentence] = sentences  # Liste von Sentence-Objekten
        self.topics: list[Topic] = topics

    def __str__(self):
        lines = []
        for sentence in self.sentences:
            speaker = sentence.get_speaker()
            start = float(sentence.start)  # Sicherstellen, dass der Startwert float ist
            text = sentence.get_text()
            lines.append(f"{speaker} {start:.3f}: {text}")
        return "\n".join(lines)

    def to_string(self):
        result = ""
        last_speaker = None
        for sentence in self.sentences:
            speaker = sentence.get_speaker()
            text = sentence.get_text()
            start = float(sentence.start)

            if speaker != last_speaker:
                if last_speaker is not None:  # Fügt eine Leerzeile nach dem letzten Sprecher hinzu
                    result += "\n"
                result += f"{speaker}:\n"  # Neuen Sprecher anzeigen
                last_speaker = speaker

            result += f"{start:.3f}: {text}\n"
        return result

    def to_string_no_timestamps(self):
        result = ""
        last_speaker = None
        for sentence in self.sentences:
            speaker = sentence.get_speaker()
            text = sentence.get_text()

            if speaker != last_speaker:
                if last_speaker is not None:  # Fügt eine Leerzeile nach dem letzten Sprecher hinzu
                    result += "\n"
                result += f"{speaker}:\n"  # Neuen Sprecher anzeigen
                last_speaker = speaker

            result += f"{text}\n"
        return result

    def to_string_no_timestamps_no_linebreak(self):
        result = ""
        last_speaker = None
        current_speaker_text = ""

        for sentence in self.sentences:
            speaker = sentence.get_speaker()
            text = sentence.get_text()

            if speaker != last_speaker:
                if last_speaker is not None:  # Fügt eine Leerzeile nach dem letzten Sprecher hinzu
                    result += f"{last_speaker}: {current_speaker_text}\n"
                current_speaker_text = text  # Beginnt einen neuen Sprecher
                last_speaker = speaker
            else:
                current_speaker_text += " " + text  # Fügt den Text des aktuellen Sprechers zur Zeile hinzu

        # Füge den Text des letzten Sprechers hinzu
        if last_speaker is not None:
            result += f"{last_speaker}: {current_speaker_text}\n"

        return result

    def get_text(self):
        return self.text

    def set_text(self, text: str):
        self.text = text

    # Getter-Methoden
    def get_speaker(self):
        return self.speaker

    def get_sentences(self):
        return self.sentences

    def get_topics(self):
        return self.topics

    # Setter-Methoden
    def set_speaker(self, speaker):
        self.speaker = speaker

    def set_sentences(self, sentences):
        self.sentences = sentences

    def set_topics(self, topics: list[Topic]):
        self.topics: list[Topic] = topics

    # Methode zum Hinzufügen eines neuen Eintrags zu den Topics
    def add_topic(self, topic: Topic):
        self.topics.append(topic)
    def remove_topic(self, topic: Topic):
        self.topics.remove(topic)

    def add_sentence(self, start, text, speaker):
        sentence = Sentence(start, text, speaker)
        self.sentences.append(sentence)

    """
    Returns all Sentences with timestamp and text with line break between each Sentence
    """
    def sentencesToString(self):

        result = "\n".join(sentence.to_string() for sentence in self.sentences)
        return result

    def remove_later_topics(self, other_topic):
        """
        Removes each TOPIC from this SpeakerTranscript that are chronologically later than other_topic.
        This is needed for the evaluation algorithm. After each TOPIC tournament, a winner SpeakerTranscript is decided.
        Every SpeakerTranscript that is chronologically before that SpeakerTranscript must get filtered out in all following TOPIC map entries so that chronology is ensured.

        ATTENTION: UNUSED AND NOT FINISHED
        """
        return False









class TranscriptMini:
    def __init__(self):
        self.speaker_transcripts: list[SpeakerTranscript] = []
        # if data:
        #     self.load_from_json(data)

    def __str__(self):
        result = "TranscriptMini:\n"
        for idx, entry in enumerate(self.speaker_transcripts):
            result += f"\nEntry {idx + 1}:\n"
            result += f"  Speaker: {entry.get_speaker()}\n"
            result += f"  text: {entry.get_text()}\n"
            result += f"  Sentences:\n"
            for sentence in entry.get_sentences():
                result += f"    Speaker: {sentence.get_speaker()} - {sentence.get_text()}\n"
            result += f"  Topics: {json.dumps(entry.get_topics(), indent=4)}\n"
        return result


    def remove_entries_not_in_protocol(self, protocol):
        """
        Entfernt Topics aus den Einträgen, deren Kapitel nicht im Protokoll enthalten sind,
        aber die Kapitelstruktur bleibt erhalten.
        """
        # Iteriere über alle SpeakerTranscripts
        for speaker_transcript in self.speaker_transcripts:
            topics = speaker_transcript.get_topics()

            # Erstelle eine Kopie der Topics, um sie während der Iteration zu ändern
            filtered_topics = []

            # Iteriere durch die Topics und behalte nur diejenigen, deren Kapitel im Protokoll enthalten sind
            for topic in topics:
                chapter_string = topic.get_chapter().get_chapter_string()  # Hole die eindeutige Kapitel-ID
                if protocol.has_chapter(chapter_string):  # Vergleiche anhand der Kapitel-ID
                    filtered_topics.append(topic)  # Behalte das Topic basierend auf der Kapitel-ID

            # Setze die gefilterten Topics
            speaker_transcript.set_topics(filtered_topics)

    def append_speaker_transcript(self, speaker_transcript: SpeakerTranscript):
        self.speaker_transcripts.append(speaker_transcript)

    def get_speaker_transcripts(self):
        return self.speaker_transcripts

    def get_speaker_transcript(self, index):
        return self.speaker_transcripts[index] if index < len(self.speaker_transcripts) else None

    def set_speaker_transcript(self, index: int, speaker: str, sentences: list[Sentence], topics: list[Topic]):
        if index < len(self.speaker_transcripts):
            self.speaker_transcripts[index].set_speaker(speaker)
            self.speaker_transcripts[index].set_sentences(sentences)
            self.speaker_transcripts[index].set_topics(topics)
        else:
            print("Index out of range.")

    def get_speakers(self):
        return [entry.get_speaker() for entry in self.speaker_transcripts]

    def get_sentences(self):
        return [entry.get_sentences() for entry in self.speaker_transcripts]

    def restructure_by_topics(self, start_index: int):
        """
        Restrukturiert die Einträge basierend auf den Topics.
        Startet ab dem gegebenen Index und teilt die Einträge auf, wenn neue Topics gefunden werden.

        Args:
            start_index (int): Der Index, ab dem die Restrukturierung beginnen soll.

        Returns:
            TranscriptMini: Ein neues restrukturiertes TranscriptMini-Objekt.
        """
        # Schritt 1: Initialisierung des neuen Transkripts und der Hilfsvariablen
        new_transcript = TranscriptMini()
        first_topic = None  # Das erste Topic, das in diesem Abschnitt gefunden wird
        found_first = False  # Flag, um festzustellen, ob das erste Topic gefunden wurde

        print("Starte Restrukturierung ab Index:", start_index)

        # Schritt 2: Iteration über die Einträge ab dem Startindex
        for i in range(start_index, len(self.speaker_transcripts)):
            speaker_transcript = self.get_speaker_transcript(i)
            print(f"Verarbeite Eintrag {i}: {speaker_transcript.get_speaker()}")

            # Schritt 3: Iteration über die Topics im aktuellen Eintrag
            for topic, start_time in speaker_transcript.get_topics().items():
                print(f"  Gefundenes Topic: {topic} mit Startzeit {start_time}")

                # Schritt 4: Iteration über die Sätze im aktuellen Eintrag
                for sentence in speaker_transcript.get_sentences():
                    if sentence.start == start_time:
                        print(f"    Satz mit passender Startzeit gefunden: {sentence}")

                        if found_first:
                            # Schritt 5: Aufteilen der Einträge, wenn das erste Topic schon gefunden wurde
                            next_entry = SpeakerTranscript(
                                speaker_transcript.get_speaker(),
                                speaker_transcript.get_sentences()[entry.get_sentences().index(sentence):],
                                {k: v for k, v in speaker_transcript.get_topics().items() if v >= start_time}
                            )
                            new_transcript.append_speaker_transcript(first_topic, current_sentences, current_topics)
                            new_transcript.append_speaker_transcript(next_entry)
                            new_transcript.speaker_transcripts.extend(self.speaker_transcripts[i + 1:])
                            print("  Aufteilung abgeschlossen. Rufe die Methode rekursiv auf.")
                            return new_transcript.restructure_by_topics(i + 1)

                        else:
                            # Schritt 6: Speichern des ersten Topics, wenn noch keins gefunden wurde
                            found_first = True
                            first_topic = topic
                            current_sentences = []
                            current_topics = {}

        # Schritt 7: Rückgabe des neuen Transkripts, wenn alle Einträge verarbeitet wurden
        print("Restrukturierung abgeschlossen.")
        return new_transcript

    """
    Resets all variables of this TranscriptMini object
    """
    def reset(self):
        self.speaker_transcripts = []

    """
    Creates a TranscriptMini from transcript_json
    """
    # TODO instead of creating a new TranscriptMini, clear all previous variables and load new content directly into self
    def load_transcript_json(self, input_json: dict):

        # rests all previous data of this TranscriptMini object
        self.reset()


        # TODO statt None muss es am besten direkt als String initialisiert werden
        current_speaker = None
        speaker = None

        transcript_entries = input_json.get("transcript_json", [])
        # transcript_mini: TranscriptMini = TranscriptMini()
        sentences: list[Sentence] = []

        for entry in transcript_entries:
            print(entry)
            speaker = entry.get("speaker", "SPEAKER_UNKNOWN")  # SPEAKER_UNKOWN, falls speaker nicht vorhanden ist
            start = entry["start"]
            text = entry["text"]
            # sentences: list[Sentence] = [Sentence(start, text)]

            if speaker != current_speaker:
                # Wenn der Sprecher wechselt, speichere die aktuelle Gruppe
                if current_speaker is not None:
                    self.append_speaker_transcript(SpeakerTranscript(speaker, "", sentences.copy(), []))
                # Setze den neuen Sprecher
                current_speaker = speaker
                current_text = []
                sentences = []

            # Füge den aktuellen Text hinzu
            sentences.append(Sentence(start, text, speaker))

        # Letzte Gruppe hinzufügen
        if current_speaker is not None:
            self.append_speaker_transcript(SpeakerTranscript(speaker, "", sentences.copy(), []))



    def first_is_later_speaker_transcript(self, first_speaker_transcript: SpeakerTranscript,
                                          second_speaker_transcript: SpeakerTranscript):
        """
        Checks if first_speaker_transcript is chronologically later than second_speaker_transcript.
        Assumes that the list[TranscriptMini] is perfectly chronologically ordered, as it ALWAYS should be.
        """

        try:
            first_index = self.speaker_transcripts.index(first_speaker_transcript)
            second_index = self.speaker_transcripts.index(second_speaker_transcript)
        except ValueError:
            raise ValueError(
                "One or both of the SpeakerTranscripts to compare were NOT found in the TranscriptMini. Both MUST be contained in the TranscriptMini for a rightful check.")

        return first_index > second_index # must be greater and not greater equal because it can be that one SENTENCE can contain multiple TOPICs.

    def test_first_is_later_speaker_transcript(self, first_speaker_transcript: SpeakerTranscript, second_speaker_transcript: SpeakerTranscript):
        """
        Checks if first_speaker_transcript is chronologically later than second_speaker_transcript.
        Chronologically just means, that the index in the list[TranscriptMini] is higher.
        Assumes that the list[TranscriptMini] is perfectly chronologically ordered, as it ALWAYS should be.
        """

        found_first_speaker_transcript: bool = False
        found_second_speaker_transcript: bool = False

        found_first_speaker_transcript_after_second_speaker_transcript: bool = False

        current_speaker_transcript: SpeakerTranscript
        for current_speaker_transcript in self.speaker_transcripts:
            if current_speaker_transcript == first_speaker_transcript:
                found_first_speaker_transcript = True

            if current_speaker_transcript == second_speaker_transcript:
                found_second_speaker_transcript = True

            if found_first_speaker_transcript is False and found_second_speaker_transcript is True:
                found_first_speaker_transcript_after_second_speaker_transcript = True  # False because second SpeakerTranscript not found yet, but first SpeakerTranscript found. This means that the second SpeakerTranscript either comes later or is not contained.
            elif found_first_speaker_transcript is True and found_second_speaker_transcript is False: # found first SpeakerTranscript at first which means that it is False
                found_first_speaker_transcript_after_second_speaker_transcript = False
            elif found_first_speaker_transcript is True and found_second_speaker_transcript is True:
                break   # this either means:    that both SpeakerTranscript are found at the same index. That means that the first SpeakerTranscript IS NOT later than the second SpeakerTranscript. The found_first_speaker_transcript_before_second_speaker_transcript variable does NOT get changed, it remains what it is. In this case False.
                        #                       that both SpeakerTrascnripts are finally found. Now a True or False gets returned. If one of them is not found an error gets raised because both SpeakerTranscripts must be contained in the TranscriptMini for check.

        if found_first_speaker_transcript and found_second_speaker_transcript:
            return not found_first_speaker_transcript_after_second_speaker_transcript # returns whether the first SpeakerTranscript is chronologically AFTER the second SpeakerTranscript.
        else: raise ValueError("One or both of the SpeakerTranscripts to compare were NOT found in the TranscriptMini. Both MUST be contained in the TranscriptMini for a rightful check.")

    '''
    async def summarize_transcript_mini_json(transcript_mini: TranscriptMini):
        from src.Api.api_llm import llm_get_chat_reply

        try:
            with open('src/Prompts/prompt_summarize.txt', 'r', encoding='utf-8') as file:
                try:
                    json_string = file.read()
                    json_string = json_string.replace('\n', '').replace('\r', '')
                    prompt_template = json.loads(json_string)
                    result = {"text": ""}

                    transcript_list = transcript_mini.get_speaker_transcripts()
                    response_parts = []

                    speaker_transcript: SpeakerTranscript
                    for speaker_transcript in transcript_list:
                        # Create text representation from sentences
                        text_content = speaker_transcript.get_speaker() + ":\n"
                        text_content += "\n".join([f"{sentence.start}: {sentence.text}"
                                                   for sentence in speaker_transcript.get_sentences()])

                        print("PROMPT USER MESSAGE######################")
                        print(text_content)
                        print("END######################################")

                        prompt = prompt_template.copy()
                        new_entry = {"role": "user", "content": text_content}
                        prompt.append(new_entry)

                        llm_reply = await llm_get_chat_reply(prompt)
                        llm_reply_json = json.loads(llm_reply['response'])
                        # response_parts.append(llm_reply_json["response"])

                        speaker_transcript.set_text(llm_reply_json["response"])
                        print("speaker_transcript#######################")
                        print(speaker_transcript.get_text())
                        print("END######################################")

                    # result["text"] = "\n\n".join(response_parts)
                    return transcript_mini

                except json.decoder.JSONDecodeError as e:
                    print(e)
                    raise e
        except FileNotFoundError as e:
            print(e)
            raise e
    '''

    # --- Schritt 1: Runs bilden (aufeinanderfolgende Sätze mit demselben Sprecher) ---
    def _group_into_runs(self, transcript_entries: List[dict]) -> List[dict]:
        runs = []
        current_run = None

        for entry in transcript_entries:
            speaker = entry.get("speaker", "SPEAKER_UNKNOWN")
            sentence = Sentence(entry["start"], entry["text"], speaker)

            if current_run is None or current_run["speaker"] != speaker:
                current_run = {"speaker": speaker, "sentences": [sentence]}
                runs.append(current_run)
            else:
                current_run["sentences"].append(sentence)
        return runs

    # --- Hilfsfunktion: Gesamtlänge eines Runs ermitteln ---
    def _run_length(self, run: dict) -> int:
        return sum(len(s.text) for s in run["sentences"])

    def _split_long_sentence(self, sentence: Sentence, maxCharLength: int) -> List[Sentence]:
        text = sentence.text
        chunks = []
        start_idx = 0

        while start_idx < len(text):
            remaining = len(text) - start_idx
            if remaining <= maxCharLength:
                chunk = text[start_idx:].strip()
                chunks.append(Sentence(sentence.start, chunk, sentence.speaker))
                break

            # Versuche zuerst, nach einem Punkt und Leerzeichen zu splitten
            candidate = text[start_idx:start_idx + maxCharLength]
            break_idx = candidate.rfind(". ")
            if break_idx != -1:
                chunk_end = start_idx + break_idx + 1
                chunk = text[start_idx:chunk_end].strip()
                chunks.append(Sentence(sentence.start, chunk, sentence.speaker))
                start_idx = chunk_end + 1
                continue

            # Falls kein Punkt gefunden wird, nach einem Komma suchen
            break_idx = candidate.rfind(", ")
            if break_idx != -1:
                chunk_end = start_idx + break_idx + 1
                chunk = text[start_idx:chunk_end].strip()
                chunks.append(Sentence(sentence.start, chunk, sentence.speaker))
                start_idx = chunk_end + 1
                continue

            # Falls kein Punkt oder Komma gefunden wird, nach dem letzten Leerzeichen suchen
            break_idx = candidate.rfind(" ")
            if break_idx != -1:
                chunk_end = start_idx + break_idx
            else:
                # Wenn keine Trennstelle gefunden wurde, mitten im Wort trennen
                chunk_end = start_idx + maxCharLength

            chunk = text[start_idx:chunk_end].strip()
            chunks.append(Sentence(sentence.start, chunk, sentence.speaker))
            start_idx = chunk_end

        return chunks



    # --- Schritt 2: Vorverarbeitung der Runs (aufteilen zu langer Runs) ---
    def _process_runs(self, runs: List[dict], max_char_length: int) -> List[dict]:
        processed_runs = []
        for run in runs:
            new_run = {"speaker": run["speaker"], "sentences": []}

            for sentence in run["sentences"]:
                if len(sentence.text) > max_char_length:
                    split_sentences = self._split_long_sentence(sentence, max_char_length)
                    new_run["sentences"].extend(split_sentences)
                else:
                    new_run["sentences"].append(sentence)

            processed_runs.append(new_run)
        return processed_runs

    # --- Schritt 3: Blockbildung aus Runs, sodass jeder Block insgesamt <= maxCharLength Zeichen enthält ---
    def load_transcript_json_limited(self, input_json: dict, max_char_length: int):
        self.reset()
        transcript_entries = input_json.get("transcript_json", [])
        runs = self._group_into_runs(transcript_entries)
        processed_runs = self._process_runs(runs, max_char_length)

        blocks = []  # Jeder Block wird als Liste von Sentence-Objekten gespeichert.
        current_block_sentences = []
        current_block_length = 0

        # Alle Sätze flach in einer Liste speichern, mit ihren Sprechern
        all_sentences = []
        for run in processed_runs:
            all_sentences.extend(run["sentences"])

        i = 0
        while i < len(all_sentences):
            current_sentence = all_sentences[i]
            sent_len = len(current_sentence.text)

            # Schaue voraus, um zu sehen, ob der nächste Satz vom gleichen Sprecher ist
            if i < len(all_sentences) - 1:
                next_sentence = all_sentences[i + 1]

                # Spezialfall: Wenn der aktuelle Satz in den Block passt, aber der nächste Satz
                # vom gleichen Sprecher ist und nicht mehr in den Block passt,
                # dann lasse beide Sätze zusammen und beginne einen neuen Block
                if (current_sentence.speaker == next_sentence.speaker and
                        current_block_length + sent_len <= max_char_length and
                        current_block_length + sent_len + len(next_sentence.text) > max_char_length and
                        current_block_sentences):

                    # Flush den aktuellen Block und starte einen neuen Block im nächsten Durchlauf
                    blocks.append(current_block_sentences)
                    current_block_sentences = []
                    current_block_length = 0
                    # Keine Inkrementierung von i, damit dieser Satz im nächsten Durchlauf verwendet wird
                    continue

            # Wenn der aktuelle Satz in den Block passt
            if current_block_length + sent_len <= max_char_length:
                current_block_sentences.append(current_sentence)
                current_block_length += sent_len
                i += 1
            else:
                # Wenn der Block nicht leer ist, flush ihn
                if current_block_sentences:
                    blocks.append(current_block_sentences)
                    current_block_sentences = []
                    current_block_length = 0

                # Wenn der Satz selbst zu lang ist für einen Block,
                # erstelle einen separaten Block nur für diesen Satz
                if sent_len > max_char_length:
                    split_sentences = self._split_long_sentence(current_sentence, max_char_length)
                    for split_sent in split_sentences:
                        split_len = len(split_sent.text)
                        if current_block_length + split_len > max_char_length and current_block_sentences:
                            blocks.append(current_block_sentences)
                            current_block_sentences = []
                            current_block_length = 0
                        current_block_sentences.append(split_sent)
                        current_block_length += split_len
                    i += 1
                # Sonst beginne einen neuen Block mit diesem Satz im nächsten Durchlauf

        # Den letzten Block hinzufügen, falls vorhanden
        if current_block_sentences:
            blocks.append(current_block_sentences)

        # Erzeuge SpeakerTranscripts
        for block in blocks:
            speakers = {s.speaker for s in block}
            block_speaker = block[0].speaker if len(speakers) == 1 else "MIXED"
            self.append_speaker_transcript(
                SpeakerTranscript(block_speaker, "", block, [])
            )




# BUGS
# Momentan werden SENTENCES entfernt, obwohl sie hinzugefügt werden sollen.
def restructure_by_topics(transcript_mini: TranscriptMini, start_index: int) -> TranscriptMini:
    """
    Restrukturiert die Einträge basierend auf den Topics.
    Startet ab dem gegebenen Index und teilt die Einträge auf, wenn neue Topics gefunden werden.

    Args:
        transcript_mini (TranscriptMini): Das ursprüngliche TranscriptMini-Objekt.
        start_index (int): Der Index, ab dem die Restrukturierung beginnen soll.

    Returns:
        TranscriptMini: Ein neues restrukturiertes TranscriptMini-Objekt.
    """
    # Schritt 1: Initialisierung des neuen Transkripts und der Hilfsvariablen
    new_transcript = TranscriptMini()
    last_found_topic: Topic or None = None
    found_first: bool = False

    # alle entries vor dem int start_index hinzufügen. die vorherigen wurden vorher schon in der Rekursion bearbeitet und müssen hier mit gespeichert werden als erstes, da sie sonst verloren gehen.
    if start_index >= 1:
        for i in range(start_index):
            speaker_transcript = transcript_mini.speaker_transcripts[i]
            new_speaker_transcript: SpeakerTranscript = SpeakerTranscript(
                speaker_transcript.get_speaker(),
                speaker_transcript.get_text(),
                speaker_transcript.get_sentences(),
                speaker_transcript.get_topics()
            )
            new_transcript.append_speaker_transcript(new_speaker_transcript)

    # first_topic = None  # Das erste Topic, das in diesem Abschnitt gefunden wird
    # found_first = False  # Flag, um festzustellen, ob das erste Topic gefunden wurde

    print("Starte Restrukturierung ab Index:", start_index)

    # Schritt 2: Iteration über die Einträge ab dem Startindex
    for i in range(start_index, len(transcript_mini.get_speaker_transcripts())):
        speaker_transcript: SpeakerTranscript = transcript_mini.get_speaker_transcript(i)
        # print(f"Verarbeite Eintrag {i}: {entry.get_speaker()}")
        # für alle topics im entry, dazu start_time als variable nehmen
        for topic in speaker_transcript.get_topics():
            # print(f"  Gefundenes Topic: {topic} mit Startzeit {start_time}")

            if topic.get_title() == "8.3":
                print("DEBUG test: Topic is 8.3")

            if topic.get_title() == "11.1":
                print("DEBUG test: Topic is 11.1")

            new_sentences: list[Sentence] = [] # Liste new_sentences leeren, da für jedes topic alle sentences durchiteriert werden. es gewährleistet, dass wenn weiter unten ein zweites passendes topic gefunden wurde, die richtigen new_sentences BIS zum passenden topic zeitstempel ausgewählt wurden
            for index, sentence in enumerate(speaker_transcript.get_sentences()):
                new_sentences.append(sentence) # fügt jeden neuen Satz hinzu
                if float(sentence.start) == float(topic.get_timestamp()): # Typumwandlung in float falls ich einen falschen Datentyp angegeben habe (ist blöd, hätte lieber Java verwendet)
                    # print(f"    Satz mit passender Startzeit gefunden: {sentence}")
                    topic_timestamp_to_check: str = topic.get_timestamp()
                    if index != 0: # Wenn es NICHT der erste Satz im SpeakerTranscript ist (wenn zuvor ein TOPIC gefunden wurde) DANN wird ein neues SpeakerTranscript erstellt.
                        # Schritt 5: Aufteilen der Einträge, wenn das erste Topic schon gefunden wurde

                        if last_found_topic is not None: new_topics = [last_found_topic]  # Eine Liste new_topics erstellen, die nur das first_topic (erstes gefundene Topic) enthält. Alle anderen Topics kommen später.
                        else: new_topics = [] # ansonsten leere Liste, da das TOPIC schon in einem vorherigen SpeakerTranscript benannt wurde

                        new_sentences.pop()  # Das letzte Element entfernen. Denn in new_sentences werden nur die vorherigen Sätze gespeichert, die im nächsten TranscriptMini gespeichert werden.

                        # Erstelle ein neues SpeakerTranscript für die neuen Sätze und Topics
                        new_speaker_transcript = SpeakerTranscript(
                            speaker_transcript.get_speaker(),
                            "",
                            new_sentences,
                            new_topics
                        )
                        # Füge den neuen SpeakerTranscript mit den neuen Topics und Sätzen hinzu falls Sentences vorhanden sind (keine leeren hinzufügen)
                        if new_speaker_transcript.get_sentences(): new_transcript.append_speaker_transcript(new_speaker_transcript)

                        # Erstelle ein weiteres SpeakerTranscript für die Sätze ab dem start_time und die verbleibenden Topics
                        remaining_topics = [
                            topic for topic in speaker_transcript.get_topics()
                            if topic.get_timestamp() >= topic_timestamp_to_check
                        ]
                        remaining_sentences = speaker_transcript.get_sentences()[
                                              speaker_transcript.get_sentences().index(sentence):]
                        new_speaker_transcript2 = SpeakerTranscript(
                            speaker_transcript.get_speaker(),
                            "",
                            remaining_sentences,
                            remaining_topics
                        )
                        # Füge den neuen SpeakerTranscript (mit den passenden Topics und Sätzen ab dem start_time) hinzu
                        new_transcript.append_speaker_transcript(new_speaker_transcript2)

                        # Füge die restlichen SpeakerTranscripts hinzu
                        new_transcript.speaker_transcripts.extend(
                            transcript_mini.get_speaker_transcripts()[i + 1:]
                        )
                        # Rekursive Umstrukturierung
                        return restructure_by_topics(new_transcript, i + 1) # True da erstes TOPIC schon gefunden wurde (wie bool found_first)


                    else:
                        # Schritt 6: Speichern des ersten Topics, wenn noch keins gefunden wurde
                        last_found_topic = topic

        new_transcript.append_speaker_transcript(speaker_transcript)


        last_found_topic = None

    # Schritt 7: Rückgabe des neuen Transkripts, wenn alle Einträge verarbeitet wurden
    return new_transcript



CLASS_MAPPING = {
    "Sentence": Sentence,
    "Chapter": Chapter,
    "Topic": Topic,
    "SpeakerTranscript": SpeakerTranscript,
    "TranscriptMini": TranscriptMini,
}

# def dict_to_obj(data):
#    return utils_dict_to_obj(data, CLASS_MAPPING)