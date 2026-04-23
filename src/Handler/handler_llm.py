import json
import re
import random
from pydantic import BaseModel
from typing import List, Dict
from uuid import UUID

from src.Classes.protocol import Protocol, Table
from src.Classes.transcript_evalator import TranscriptEvaluator
# from src.Classes.protocol import TableOfContents
from src.Classes.transcript_mini import TranscriptMini, SpeakerTranscript, Sentence, Topic, Chapter, \
    topic_list_contains_chapter_title

debug = False

class ProjectRequestRead(BaseModel):
    project_id: UUID

class ProjectRequestWriteDict(BaseModel):
    project_id: UUID
    data: dict

class TranscriptionRequest(BaseModel):
    transcript_mini_json: List[Dict]


topics_string = """
TOPICS:
1. Genehmigung der Tagesordnung
2. Wissenschaft
2.1. Auflösung der im Haushalt des Landes veranschlagten globalen Minderausgabe – Teil IIsowie Auflösung unabweisbarer dezentraler Budget- und Liquiditätsrisiken im Haushaltsvollzug 2023 (VL 21/1130)
2.2. Handlungsfeld Klimaschutz - Mittelabflussprognose und Abrechnung zum 31. Dezember 2023 (VL 21/1131)
2.3. Verschiedenes
3. Medien
3.1. Verschiedenes
4. Datenschutz
4.1. Auflösung der veranschlagten globalen Minderausgaben –Teil II sowie Auflösung unabweisbarer dezentraler Budget- und Liquiditätsrisiken im Haushaltsvollzug 2023hier: Beteiligung des Produktplans 06 (Datenschutz und Informationsfreiheit) (VL 21/1129)
4.2. Verschiedenes
5. Informationsfreiheit
5.1. Verschiedenes
6. Digitalisierung
6.1. Verschiedenes
"""


async def timestamps_add(summarization: str, speaker_transcript: SpeakerTranscript, prompt_summarize_template) -> str:
    from Api.api_llm import llm_get_chat_reply

    timestamps_prompt = prompt_summarize_template.copy()

    text_content: str = "Transkript:\n"
    text_content += "\n".join([
        f"({sentence.start:.3f}) {speaker_transcript.get_speaker()}: {sentence.text}"
        for sentence in speaker_transcript.get_sentences()
    ])
    text_content += "\n\nZusammenfassung:\n"
    text_content += summarization


    timestamps_new_entry = {"role": "user", "content": text_content}
    timestamps_prompt.append(timestamps_new_entry)

    llm_reply = await llm_get_chat_reply(timestamps_prompt)
    llm_reply_string: str = llm_reply['response']
    return llm_reply_string

async def llm_summarization_correction(summarization: str, prompt_summarization_correction_template) -> str:
    from Api.api_llm import llm_get_chat_reply

    prompt_summarization_correction = prompt_summarization_correction_template.copy()

    prompt_summarization_correction_new_entry = {"role": "user", "content": summarization}
    prompt_summarization_correction.append(prompt_summarization_correction_new_entry)

    llm_reply = await llm_get_chat_reply(prompt_summarization_correction)
    llm_reply_string: str = llm_reply['response']
    return llm_reply_string


async def toipirize_transcript_mini_table(transcript_mini: TranscriptMini, table: Table):
    """
    TODO Themen dürfen nicht 2 mal zugeordnet werden bzw. es kann vorkommen dass das LLM denselben TOPIC mit denselbem timestamp im richtigen Format 2 mal in die Antwort einbaut. Das darf nicht passieren.
    Summarizes transcript_mini with LLM using the new TranscriptMini class structure.
    Args:
        transcript_mini: TranscriptMini object containing the transcripts
        table_of_contents: TableOfContents object containing the structure
    """
    from src.Api.api_llm import llm_get_chat_reply

    with open('src/Prompts/prompt_topics.txt', 'r', encoding='utf-8') as file:
        prompt_template = json.load(file, strict=False)

    # json_string = file.read()
    # json_string = json_string.replace('\n', '\\n').replace('\r', '\\n')
    # prompt_template = json.loads(json_string)

    # Create a new TranscriptMini for the result
    result_transcript_mini = TranscriptMini()
    transcript_entries = transcript_mini.get_speaker_transcripts()

    for speaker_transcript in transcript_entries:
        # Create text representation from sentences
        #text_content = "\n".join([f"{sentence.start}: {sentence.text}"
        #                          for sentence in speaker_transcript.get_sentences()])
        text_content = speaker_transcript.to_string()

        # Prepare and send prompt to LLM
        prompt = prompt_template.copy()
        # Convert TableOfContents to string using its string representation
        toc_string = table.get_nested_entries_overview_text()
        new_message = f"{toc_string}\n\n{text_content}"
        new_entry = {"role": "user", "content": new_message}
        prompt.append(new_entry)

        # print("PROMPT topirize_transcript_mini_json########################")
        # print(prompt)
        llm_reply = await llm_get_chat_reply(prompt)
        # llm_reply_json = json.loads(llm_reply['response'])
        # llm_reply_string = llm_reply_json["response"]
        llm_reply_string = llm_reply['response']
        print("TOIPIRIZING QUEST NEW USER MESSAGE ########################")
        print(new_message)
        print("TOIPIRIZING REPLY ########################")
        print(llm_reply_string)

        # Extract topics from LLM response
        topics = []
        topic_lines = llm_reply_string.strip().split("\n")
        for line in topic_lines:
            match = re.match(r"TOPIC ([^:]+):\s*(.+)", line)
            if match:
                chapter_title = match.group(1).strip()
                timestamp = match.group(2).strip()
                if timestamp != "not mentioned":
                    try:
                        chapter: Chapter = Chapter(chapter_title)  # Assuming Chapter is already defined
                    except Exception as e: # falls die Chapter Erstellung fehlschlägt (voraussichtlich Formatierungsfehler des LLMs)
                        continue
                    # if the topic list not already contains the topic, add it. Prevents that one TOPIC gets added more than one time.
                    if not topic_list_contains_chapter_title(topics, chapter_title):
                        # TODO es muss auf ungültige bzw. leere Timestamps überprüft werden
                        try:
                            topic = Topic(chapter, chapter_title, timestamp)
                            topics.append(topic)
                        except Exception as e:
                            continue # Fehler bei Erstellung der TOPIC. Das kann passieren wenn das LLM z.B. den Timestamp falsch formatiert hat

        # Create new SpeakerTranscript with updated topics
        new_speaker_transcript = SpeakerTranscript(
            speaker=speaker_transcript.get_speaker(),
            text="",
            sentences=speaker_transcript.get_sentences(),
            topics=topics
        )

        # Add to result transcript
        result_transcript_mini.append_speaker_transcript(new_speaker_transcript)

    return result_transcript_mini



"""
Sends a prompt template + user message to LLM, waits for reply and returns it.
"""
async def get_llm_reply(prompt: list, user_message: str):
    from src.Api.api_llm import llm_get_chat_reply

    # Erstelle eine Kopie von prompt und füge den neuen Eintrag hinzu
    new_prompt = prompt.copy()
    new_entry = {"role": "user", "content": user_message}
    new_prompt.append(new_entry)

    llm_reply = await llm_get_chat_reply(new_prompt)
    # llm_reply_json = json.loads(llm_reply['response'])
    llm_reply_string = llm_reply["response"]

    print(llm_reply_string)
    return llm_reply_string








async def tournament_style_evaluation(transcript_list, document_protocol: Protocol, specific_topic=None):
    """
    Evaluates a list of transcripts in a tournament style, reducing them
    through knockout rounds until only one transcript remains.

    Parameters:
        transcript_list (list): A list of transcripts to evaluate.
        specific_topic (str): The specific topic to evaluate (optional).

    Returns:
        SpeakerTranscript: The best transcript after tournament evaluation.
    """
    if debug: print("tournament_style_evaluation")
    with open('src/Prompts/prompt_topics_evaluate.txt', 'r', encoding='utf-8') as file:
        try:
            json_string = file.read()
            json_string = json_string.replace('\n', '\\n').replace('\r', '\\n')
            prompt_template = json.loads(json_string)

            # Mische die Transkripte zufällig
            random.shuffle(transcript_list)

            round_number = 1
            while len(transcript_list) > 1:
                if debug: print(f"Runde {round_number}: {len(transcript_list)} Transkripte übrig.")
                next_round = []
                for i in range(0, len(transcript_list), 2):
                    transcript1 = transcript_list[i]
                    # Falls eine ungerade Anzahl an Transkripten, das letzte Transkript kommt automatisch weiter
                    transcript2 = transcript_list[i+1] if i+1 < len(transcript_list) else transcript_list[i]

                    # Evaluate the transcripts for the specific topic
                    evaluator = TranscriptEvaluator(
                        transcript1=transcript1,
                        transcript2=transcript2,
                        prompt_template=prompt_template,
                        protocol=document_protocol,
                        specific_topic=specific_topic
                    )
                    # Checks if transcript1 and transcript2 are the same. If not, evaluate. Otherwise skip evaluation because they are the same.
                    if not transcript1 is transcript2:
                        better_transcript = await evaluator.evaluate()
                    else: better_transcript = transcript1
                    next_round.append(better_transcript)  # Add only the winner

                transcript_list = next_round
                round_number += 1

            # Das beste Transkript ist nun das einzige übrig gebliebene
            # return transcript_list[0]
            if transcript_list:
                return transcript_list[0]
            else:
                return None

        except json.decoder.JSONDecodeError as e:
            print(e)
            return e


def remove_chronologically_wrong_speaker_transcripts(topics_map: dict, transcript_mini: TranscriptMini,
                                                     current_speaker_transcript_map_index: int):
    """
    Removes chronologically wrong SpeakerTranscripts from the topics_map.

    Parameters:
    - topics_map: A dictionary where the key is an index, and the value is a list containing one or more SpeakerTranscripts.
    - transcript_mini: An instance of TranscriptMini to check the chronological order of SpeakerTranscripts.
    - current_speaker_transcript_map_index: The index whose SpeakerTranscript serves as the reference.

    Returns:
    - The updated topics_map with invalid SpeakerTranscripts removed.
    """

    # Get the key at the given index in the dictionary
    reference_topic_key = list(topics_map.keys())[current_speaker_transcript_map_index]

    # Reference SpeakerTranscript at the current index (first and only element in the list at this index)
    reference_speaker_transcript = topics_map[reference_topic_key][0]

    # Iterate over all indices in the topics_map after the current index
    for map_index in range(current_speaker_transcript_map_index + 1, len(topics_map)): # +1 because all next topics should be scanned, NOT THIS. len - 1 because index thing
        # Get the key at the current index in the dictionary
        current_topic_key = list(topics_map.keys())[map_index]

        # Get the list of SpeakerTranscripts at the current index
        current_speaker_transcripts = topics_map[current_topic_key]

        new_topics_list: list[SpeakerTranscript] = []

        # TODO improve performance of the index count. not create a new list but instead rework the index count so the list itself can be edited instead of creating an entire new list[SpeakerTranscript]
        # We need to iterate over each SpeakerTranscript in the list at this index
        for i, current_speaker_transcript in enumerate(current_speaker_transcripts):
            # Check if the current SpeakerTranscript is chronologically later than the reference
            # if it later it should be removed. So it gets NOT added to the new list. A new list is needed because otherwise the index is counted wrong.

            # NULL checks
            if current_speaker_transcript is None:
                continue
            if reference_speaker_transcript is None:
                new_topics_list.append(current_speaker_transcript)
                continue
            if not transcript_mini.first_is_later_speaker_transcript(reference_speaker_transcript, current_speaker_transcript):
                # Remove this chronologically incorrect SpeakerTranscript
                # topics_map[current_topic_key].pop(i)
                # add the current_speaker_trasncript from the iteration to the new list[SpeakerTranscript] BECAUSE it is valid.
                new_topics_list.append(current_speaker_transcript)

        topics_map[current_topic_key] = new_topics_list

    return topics_map



# TODO add a function to the map loop. E.g. after TOPIC 1.1. is assigned, delete all other TOPICS like 1.2.1. and 2.1. in that SpeakerTranscript and all previous SpeakerTranscripts. This way CHRONOLOGY is preserved.
async def topirize_cleanup_transcript_mini_json(transcript_mini: TranscriptMini, document_protocol: Protocol):
    """
    Let LLM evaluate the best topics for each transcript piece. The best gets chosen based on context.
    Summarizes transcript_mini_json with LLM, resolving duplicate topics.
    """
    print("topirize_cleanup_transcript_mini_json")

    # Retrieve transcripts from the TranscriptMini instance
    speaker_transcripts: list[SpeakerTranscript] = transcript_mini.get_speaker_transcripts()

    # Step 1: Group transcripts by topics. Jedem TOPIC werden alle SpeakerTranscripts hinzugemappt, die dem zugeordnet sind. Sie werden später pro TOPIC evaluiert. Der beste Kandidat wird genommen.
    topics_map = {}

    for index, speaker_transcript in enumerate(speaker_transcripts):
        for topic in speaker_transcript.get_topics():
            # Get the unique chapter string for this topic
            chapter_string = topic.get_chapter().get_chapter_string()

            if chapter_string not in topics_map:
                topics_map[chapter_string] = []

            # Append the entire SpeakerTranscript object under the topic key
            topics_map[chapter_string].append(speaker_transcript)

    # Step 2: Iterative evaluation in tournament style with specific topics
    # Holen des Indexes für jeden topic_key basierend auf der Reihenfolge in der Map
    for index, (topic_key, transcripts) in enumerate(topics_map.items()):
        # Select the best transcript for this topic based on the tournament evaluation
        best_transcript: SpeakerTranscript = await tournament_style_evaluation(transcripts, document_protocol, specific_topic=topic_key)

        # Update the topics_map with the best transcript
        topics_map[topic_key] = [best_transcript]

        # Now remove chronologically wrong SpeakerTranscripts
        # Pass the current index as the reference index
        topics_map = remove_chronologically_wrong_speaker_transcripts(topics_map, transcript_mini, current_speaker_transcript_map_index=index)
    # TODO bis hierhin alles richtig. Folgenden Code + restructure_by_topics Methode überprüfen

    # Step 3: Create the updated transcripts based on the evaluated topics
    updated_transcripts = []

    for speaker_transcript in speaker_transcripts:
        filtered_topics = []

        for topic in speaker_transcript.get_topics():
            topic_key = topic.get_chapter().get_chapter_string()

            if topic_key in topics_map and topics_map[topic_key]:
                first_entry = topics_map[topic_key][0]

                # Ensure the transcript is the best choice based on its index
                if first_entry == speaker_transcript:
                    filtered_topics.append(topic)

            # Check if the chapter exists in the table of contents
            if not document_protocol.chapter_exists(topic_key):
                continue

        # Create a new updated speaker transcript with the filtered topics and sentences
        updated_transcripts.append(SpeakerTranscript(
            speaker=speaker_transcript.get_speaker(),
            text=speaker_transcript.get_text(),
            sentences=speaker_transcript.get_sentences(),
            topics=filtered_topics
        ))

    # Create a new TranscriptMini object with the updated transcripts
    updated_transcript_mini = TranscriptMini()

    # Append each updated speaker transcript to the new TranscriptMini
    for entry in updated_transcripts:
        updated_transcript_mini.append_speaker_transcript(entry)

    return updated_transcript_mini


class ProjectRequestWrite(BaseModel):
    project_id: UUID
    data: dict


def check_type(obj, expected_type):
    """
    Überprüft, ob ein Objekt vom erwarteten Typ ist.

    Args:
        obj: Das zu überprüfende Objekt.
        expected_type: Der erwartete Typ (oder ein Tupel von Typen).

    Raises:
        TypeError: Wenn das Objekt nicht vom erwarteten Typ ist.
    """
    if not isinstance(obj, expected_type):
        raise TypeError(f"Das Objekt {repr(obj)} ist nicht vom Typ {expected_type.__name__}.")

def filter_latin_chars(text):
    # Erlaubte Zeichen: Buchstaben (inkl. äöüÄÖÜß), Ziffern, gängige Satzzeichen und Sonderzeichen
    allowed_pattern = r"[a-zA-ZäöüÄÖÜß0-9\s.,!?;:'\"(){}\[\]<>@#$%^&*+=\\|\-_/`~]"

    # Füge alle erlaubten Zeichen zusammen
    filtered = ''.join(re.findall(allowed_pattern, text))
    return filtered

async def summarize_transcript_mini_json(transcript_mini: TranscriptMini):
    from src.Api.api_llm import llm_get_chat_reply

    with open('src/Prompts/prompt_summarize.txt', 'r', encoding='utf-8') as file:
        prompt_summarize_template = json.load(file, strict=False)

    with open('src/Prompts/prompt_summarization_correction.txt', 'r', encoding='utf-8') as file:
        prompt_summarization_correction_template = json.load(file, strict=False)

    with open('src/Prompts/prompt_timestamps_add.txt', 'r', encoding='utf-8') as file:
        prompt_timestamps_add_template = json.load(file, strict=False)

    # result = {"text": ""}

    transcript_list = transcript_mini.get_speaker_transcripts()

    speaker_transcript: SpeakerTranscript
    for speaker_transcript in transcript_list:
        # Create text representation from sentences
        #text_content = speaker_transcript.get_speaker() + ":\n"
        #text_content += "\n".join([f"{sentence.start}: {sentence.text}"
        #                           for sentence in speaker_transcript.get_sentences()])
        text_content = speaker_transcript.to_string_no_timestamps_no_linebreak()


        print("PROMPT USER MESSAGE######################")
        print(text_content)
        print("END######################################")

        summarization_prompt = prompt_summarize_template.copy()
        summarization_new_entry = {"role": "user", "content": text_content}
        summarization_prompt.append(summarization_new_entry)

        summarization_llm_reply = await llm_get_chat_reply(summarization_prompt)
        summarization_llm_reply_string: str = summarization_llm_reply['response']

        # let LLM correct the summarization to improve its grammar quality.
        summarization_correction_llm_reply_string: str = await llm_summarization_correction(summarization_llm_reply_string, prompt_summarization_correction_template)

        # let LLM put timestamps from transcript into the summarization
        summarization_timestamps_string: str = await timestamps_add(summarization_correction_llm_reply_string, speaker_transcript, prompt_timestamps_add_template)

        # filter non latin characters (e.g. emojis, chinese, hindu, cyrillic chars)
        filtered_latin_string: str = filter_latin_chars(summarization_timestamps_string)

        # convert timestamps to right format
        summarization_timestamps_converted: str = convert_timestamps(filtered_latin_string)



        speaker_transcript.set_text(summarization_timestamps_converted)
        print("speaker_transcript#######################")
        print(speaker_transcript.get_text())
        print("END######################################")

    return transcript_mini



def convert_timestamps(llm_summarization: str) -> str:
    """
    Konvertiert numerische Zeitstempel im Format (Sekunden.Millisekunden) innerhalb eines Textes
    in ein lesbares Zeitformat (MM:SS oder HH:MM:SS).

    Diese Funktion durchsucht den übergebenen Text nach Zeitstempeln, die in Klammern geschrieben
    sind und Sekunden als Gleitkommazahl enthalten, z. B. (123.456). Jeder gefundene Zeitstempel
    wird in ein Zeitformat umgewandelt:

    - Ist die Zeit >= 1 Stunde: Format HH:MM:SS
    - Ist die Zeit < 1 Stunde: Format MM:SS

    Millisekunden werden dabei verworfen (abgerundet auf die volle Sekunde).

    Beispiel:
        Input: "Das Ereignis passiert bei (75.3) und endet bei (3675.98)."
        Output: "Das Ereignis passiert bei 01:15 und endet bei 01:01:15."

    Parameter:
        llm_summarization (str): Ein Text, der Zeitstempel im Format (sss.mmm) enthalten kann.

    Rückgabewert:
        str: Der Text mit konvertierten Zeitstempeln im Format MM:SS oder HH:MM:SS.
    """
    def convert(match):
        # Extrahiere die Zeit als Float
        seconds = float(match.group(1))
        total_seconds = int(seconds)  # abrunden

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60

        if hours > 0:
            return f"{hours:02}:{minutes:02}:{secs:02}"
        else:
            return f"{minutes:02}:{secs:02}"

    # Regex sucht nach Zeitstempeln im Format (sss.msmsms)
    pattern = r"\((\d+(?:\.\d{1,3})?)\)"

    # Ersetze alle Timestamps im Text durch das neue Format
    return re.sub(pattern, convert, llm_summarization)



"""
async def create_protocol_json(title, subtitle, groups, chapters):
    
    # Verarbeitet die Kapitel als Liste von Strings oder Dictionaries.
    # Fügt für jedes Kapitel Lorem Ipsum-Inhalte ein.
    
    # Prüfen und anpassen der Struktur
    chapters_with_content = [
        {
            "chapter_title": chapter if isinstance(chapter, str) else chapter.get("name", f"Kapitel {index + 1}"),
            "content": f"Kapitel {index + 1}: Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
                       f"Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
        }
        for index, chapter in enumerate(chapters)
    ]

    return {
        "title": title,
        "subtitle": subtitle,
        "groups": groups,
        "chapters": chapters_with_content
    }
"""