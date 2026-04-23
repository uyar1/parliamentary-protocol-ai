import asyncio
import logging
from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import JSONResponse

import src.Handler.handler_lmdeploy
from src.Handler import handler_lmdeploy

# Logging konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Router:
    """
    API-Klasse für das Verwalten der Endpunkte und Zugriffskontrolle.
    """
    def __init__(self):
        self.router = APIRouter()
        self.semaphore = asyncio.Semaphore(3)  # Maximal 3 parallele Anfragen, testweise 1

        # Endpunkte registrieren
        self.router.add_api_route("/get_reply/", self.get_reply, methods=["POST"])
        self.router.add_api_route("/get_chat_reply/", self.get_chat_reply, methods=["POST"])

    async def get_chat_reply(self, messages: list[dict]):
        """
        API-Endpoint für die Verarbeitung von Benutzereingaben in einer Konversation.
        :param messages: Liste von Benutzereingaben
        :return: Antworten des Modells
        """
        try:
            # Versuche, die Semaphore mit einem Timeout zu erwerben
            await asyncio.wait_for(self.semaphore.acquire(), timeout=0.1)
        except asyncio.TimeoutError:
            logger.warning("Too many requests: Semaphore is full.")
            return JSONResponse(
                status_code=429,
                content={"error": "Too many requests. Please try again later."}
            )

        try:
            # Anfrage verarbeiten
            logger.info("Processing request...")
            # Hier wird die Funktion get_replies aufgerufen, die die Liste von Nachrichten erwartet
            response = await src.Handler.handler_lmdeploy.llm_generate(messages=messages)

            if not response:
                raise HTTPException(status_code=500, detail="Failed to generate a response.")
            return {"response": response}

        except Exception as e:
            logger.error(f"Error occurred: {e}")
            raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

        finally:
            # Semaphore wieder freigeben
            self.semaphore.release()


    async def get_reply(self, message: str = Form(...)):
        """
        API-Endpoint für die Verarbeitung von Benutzereingaben.
        :param message: Benutzereingabe
        :return: Antwort des Modells
        """
        try:
            # Versuche, die Semaphore mit einem Timeout zu erwerben
            await asyncio.wait_for(self.semaphore.acquire(), timeout=0.1)
        except asyncio.TimeoutError:
            logger.warning("Too many requests: Semaphore is full.")
            return JSONResponse(
                status_code=429,
                content={"error": "Too many requests. Please try again later."}
            )

        try:
            # Anfrage verarbeiten
            logger.info("Processing request...")
            response = await handler_lmdeploy.get_reply(message_content=message)

            if not response:
                raise HTTPException(status_code=500, detail="Failed to generate a response.")
            return {"response": response}

        except Exception as e:
            logger.error(f"Error occurred: {e}")
            raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

        finally:
            # Semaphore wieder freigeben
            self.semaphore.release()
