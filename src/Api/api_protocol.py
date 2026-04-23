from fastapi import APIRouter, Form
from src.Api.api_llm import llm_get_chat_reply
from src.Utils.fileUtils import read_file_to_string, save_string_to_file
import src.config
import os

router = APIRouter()

"""
@router.post("/get_protocol/")
async def get_reply(message: str = Form(...)):

    # print("Received message:", message)
    response = await get_reply(message)
    return response
"""

@router.post("/get_protocol/")
async def llm_generate_summary(transcript_mini_path = Form(...), protocol_path: str = Form(...)):
    # explanation = "Antworte präzise mit maximal 30 Wörtern, keine mehr. Fasse das Transkript ultra kurz und knapp als Fließtext in der dritten Person zusammen ohne Zitate in fast genau 30 Wörtern zusammen. Im Transkript steht in jeder Zeile zuerst die Zeitangabe, dann der Sprecher und zuletzt das Gesagte. Du musst unbedingt in der Zusammenfassung die Zeitangabe hinzufügen für alles was du zusammenfässt exakt in der Form {Zeit}, zum Beispiel {2.543}, mit geschweiften Klammern. Du musst unbedingt zeilenübergreifend zusammenfassen. Maximal 30 Wörter. Transkript:\n"
    # explanation = "Antworte präzise in maximal 30 Wörtern. Fasse das Transkript als Fließtext in der dritten Person zusammen. Füge Zeitangaben für alle zusammengefassten Inhalte exakt im Format {Zeit} als z.B. {2.631} in geschweiften Klammern vor dem jeweiligen Inhalt hinzu. Zeitangaben sind zwingend erforderlich. Zusammenfassung muss zeilenübergreifend und ohne Zitate erfolgen. Transkript:\n"
    # explanation = "Transkript eines Theaterstücks präzise zusammenfassen als Fließtext der dritter Person OHNE direkte Zitate in MAXIMAL DREIßIG Wörtern. Jeweils VORHERIGE Zeitangabe in der Zusammenfassung ZWINGEND in Form {Zeit} z.B. {01:20:14.634} einfügen. Transkript:\n"
    # explanation = "Transkript eines präzise zusammenfassen als Fließtext der dritter Person OHNE direkte Zitate in MAXIMAL DREIßIG Wörtern ZWINGEND mit codierten Zeitangaben der Form {Zeit} jeweils BEVOR dem zusammenfassendem Teil in MAXIMAL 30 dreißig Wörtern MIT Zeilenangaben der FOrm {ZEIT}."
    # explanation = "Transkript präzise zusammenfassen als Fließtext der dritter Person OHNE direkte Zitate in MAXIMAL DREIßIG Wörtern. ZWINGEND Zeitangaben der Form VOR dem zusammenfassenden Abschnitt angeben in der exakten Form:\n \"{hh:mm:ss}TEXT\"\n. Transkript:"
    explanation = "Generiere zu einem Transkript ein Inhaltsverzeichnis der wesentlichen Beratungsgegenstände des öffentlichen Teils und schreibe jeden Eintrag untereinander. In deiner Antwort dürfen nur die Inhaltsverzeichniseinträge ohne Spezialformatierung und ohne Nummerierung enthalten sein. Transkript:\n\n"

    transcript_mini = read_file_to_string(transcript_mini_path)
    prompt = explanation + transcript_mini
    print(prompt)
    llm_result = await llm_get_chat_reply(prompt)
    if llm_result["status_code"] == 200:
        llm_result_string = llm_result["message"].replace("\\n", "\n").replace('\\"', '\"') # TODO BITTE ANDERS FIXEN
        if llm_result_string.startswith('"') and llm_result_string.endswith('"'):
            llm_result_string = llm_result_string[1:-1]
        print(llm_result_string)
        save_string_to_file(llm_result_string, os.path.join(src.config.get_project_path(), "documents", "protocol.txt"))
        return 200
    else: return 500

    # url = "http://localhost:8002/get_reply"
    # data = {"message": message}
    # response = httpx.post(url, data=data)
    # return {"status_code": response.status_code, "message": response.text}