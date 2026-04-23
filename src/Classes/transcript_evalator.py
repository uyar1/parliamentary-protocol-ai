# Evaluierungsfunktion
# TODO andere Fehlerbehandlung falls das splitten fehlschlägt. Eventuell noch ca. 3 mal das LLM fragen
from src.Classes.protocol import Protocol
from src.Classes.transcript_mini import SpeakerTranscript



class TranscriptEvaluator:
    def __init__(self, transcript1: SpeakerTranscript, transcript2: SpeakerTranscript, prompt_template, protocol: Protocol, specific_topic=None):
        self.transcript1: SpeakerTranscript = transcript1
        self.transcript2: SpeakerTranscript = transcript2
        self.prompt_template = prompt_template
        self.protocol = protocol
        self.specific_topic = specific_topic

    def _get_text_from_sentences(self, speaker_transcript: SpeakerTranscript):
        text = ""
        for sentence in speaker_transcript.sentences:
            text += f"{sentence.start}: {sentence.text}\n"
        return text

    def _get_common_topics(self):
        try:
            topics1 = [topic.get_chapter().get_chapter_string() for topic in self.transcript1.get_topics()]
        except AttributeError:
            topics1 = []

        try:
            topics2 = [topic.get_chapter().get_chapter_string() for topic in self.transcript2.get_topics()]
        except AttributeError:
            topics2 = []

        if self.specific_topic:
            return {self.specific_topic} if self.specific_topic in topics1 and self.specific_topic in topics2 else set()

        return set(topics1) & set(topics2)


    #def _get_common_topics(self):
    #    if self.specific_topic:
    #        # Check if the specific topic exists in both transcripts
    #        return {self.specific_topic} if self.specific_topic in [topic.get_chapter().get_chapter_string() for topic in self.transcript1.get_topics()] and self.specific_topic in [topic.get_chapter().get_chapter_string() for topic in self.transcript2.get_topics()] else set()
    #    # Get the common topics between the two transcripts
    #    return set(topic.get_chapter().get_chapter_string() for topic in self.transcript1.get_topics()) & set(topic.get_chapter().get_chapter_string() for topic in self.transcript2.get_topics())


    # TODO for loop is inefficient because instead it can be searched for each topic in common topic first. Also I dont know if a map is more efficient here
    def topics_to_table(self, transcript: SpeakerTranscript, protocol: Protocol, section_name: str,
                        common_topics: set[str]) -> str:
        """
        Erzeugt eine tabellarische Darstellung der Topics eines Transkripts,
        gefiltert nach den Common Topics, unter Verwendung der Kapitelnamen und Timestamps aus dem Protocol.

        Parameters:
            transcript (SpeakerTranscript): Das Transkript, dessen Topics dargestellt werden sollen.
            protocol (Protocol): Das Protokoll, das die Tabellen mit den Kapitelnamen enthält.
            section_name (str): Der Name des Abschnitts (z. B. "Öffentlicher Teil").
            common_topics (set[str]): Die gemeinsamen Topics, die verglichen werden sollen.

        Returns:
            str: Eine strukturierte Darstellung der Topics mit Kapitel-Namen, Timestamps und Abschnittsnamen.
        """
        # Hole die Tabelle für den angegebenen Abschnitt
        table = protocol.public_table if section_name.lower() == "öffentlicher teil" else protocol.trusted_table
        if not table:
            return f"{section_name.upper()}\nKeine Einträge vorhanden.\n"

        # Erstelle eine Map für schnellen Zugriff: Kapitel-String -> Kapitel-Name
        chapter_name_map = {entry.get_chapter_id_string(): entry.get_title() for entry in
                            table.get_nested_entries_overview()}

        # Baue die Ausgabe basierend auf den Topics im Transkript und den Kapitelnamen
        result = f"{section_name.upper()}\nTOPICS:\n"
        for topic in transcript.get_topics():
            chapter_string = topic.get_chapter().get_chapter_string()
            if chapter_string in common_topics:
                chapter_name = chapter_name_map.get(chapter_string, "Unbekanntes Kapitel")
                result += f"TOPIC {chapter_string} {chapter_name}: {topic.get_timestamp()}\n"
        result += "\n"
        return result

    async def evaluate(self):
        from src.Handler.handler_llm import get_llm_reply

        common_topics = self._get_common_topics()
        if not common_topics:
            print("EVALUATION FAILED: No common topics to evaluate. Made transcript1 won automatically")
            # return transcript1 as winner because failed
            return self.transcript1
            # raise {"error": "No common topics to evaluate."}

        # transcript1_text = self._get_text_from_sentences(self.transcript1)
        # transcript2_text = self._get_text_from_sentences(self.transcript2)
        transcript1_text: str = self.transcript1.to_string()
        transcript2_text: str = self.transcript2.to_string()


        # Erzeuge strukturierte Topic-Abschnitte
        transcript1_topics_section = self.topics_to_table(self.transcript1, self.protocol, "Öffentlicher Teil", common_topics)
        transcript2_topics_section = self.topics_to_table(self.transcript2, self.protocol, "Öffentlicher Teil", common_topics)

        user_message = (
            f"Topics for comparison:\n\n"
            f"TOPIC evaluation from LLM1:\n{transcript1_topics_section}\n"
            f"Transcript from LLM1:\n{transcript1_text}\n\n"
            f"TOPIC evaluation from LLM2:\n{transcript2_topics_section}\n"
            f"Transcript from LLM2:\n{transcript2_text}"
        )

        llm_reply = await get_llm_reply(self.prompt_template, user_message)
        if not llm_reply or "TOPIC" not in llm_reply:
            return {"error": "Invalid LLM reply format"}

        lines = llm_reply.strip().split("\n")
        winner = None
        llm_id: str = "LLM1"
        for line in lines:
            if line.startswith("TOPIC") and "LLM" in line:
                try:
                    _, llm_id = line.split(":")
                    llm_id = llm_id.strip()
                except ValueError:
                    llm_id = "LLM1"

                if llm_id == "LLM1":
                    winner = self.transcript1
                elif llm_id == "LLM2":
                    winner = self.transcript2


        if winner is None:
            print("EVALUATION FAILED: LLM gave wrong output format at the end of the answer. Made transcript1 won automatically")
            winner = self.transcript1
        print("winner: ", llm_id)
        print("evaluated")

        return winner