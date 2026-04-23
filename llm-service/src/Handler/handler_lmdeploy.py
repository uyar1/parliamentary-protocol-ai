import os
import json
import torch
from lmdeploy import pipeline, TurbomindEngineConfig, GenerationConfig, ChatTemplateConfig
from src.Utils.pathUtils import get_project_path
import logging
import asyncio
import nest_asyncio

nest_asyncio.apply()

# Logging-Konfiguration
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Torch CUDA Cache leeren
torch.cuda.empty_cache()

# CUDA max split size setzen
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:64"

# Backend-Konfiguration für Turbomind
# backend_config = TurbomindEngineConfig(tp=1, max_batch_size=1, max_context_token_num=16384, cache_max_entry_count=0.1, quant_policy=4, session_len=16384)
backend_config = TurbomindEngineConfig(tp=1, max_batch_size=1, max_context_token_num=16384, cache_max_entry_count=0.1, quant_policy=4, session_len=16384)

# GenerationConfig für TurboMind
# def __init__(self, top_p=0.9, top_k=50, temperature=0.7, max_new_tokens=32768):
gen_config = GenerationConfig(top_p=0.9,
                              top_k=50,
                              temperature=1.0,
                              max_new_tokens=8192)

gen_config2 = GenerationConfig(top_p=0.5,
                              top_k=5,
                              temperature=0.4,
                              max_new_tokens=8192)

# LLM Modell
# model = "neuralmagic/Meta-Llama-3.1-8B-Instruct-quantized.w8a16"
model = "Aaron2599/Meta-Llama-3.1-8B-Instruct-TurboMind-AWQ-4bit"
# model = "VAGOsolutions/Llama-3.1-SauerkrautLM-8b-Instruct-awq"
# model = "AMead10/SuperNova-Medius-AWQ"
# model = "PyrTools/Ministral-8B-Instruct-2410-AWQ"
# model = "fbaldassarri/meta-llama_Llama-3.2-3B-auto_awq-int4-gs128-sym"

# Pipeline initialisieren
pipe = pipeline(
    task="text-generation",
    model_path=model,
    backend_config=backend_config
)


"""
Verwendet llama3.1 Chat Template
Nimmt einen Chat in Form einer Liste entgegen und gibt eine Antwort zurück
"""
async def get_chat_reply_multi2(messages: list[str]) -> str:
    try:
        # System-Prompt definieren (erste Nachricht als System-Prompt verwenden)
        system_prompt = messages[0]
        prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}"

        # Abwechselnd 'user' und 'assistant' Nachrichten an das Prompt anhängen
        for i, message in enumerate(messages[1:], start=1):  # Ab dem zweiten Element in der Liste
            if i % 2 == 1:  # 'user' Nachrichten an ungeraden Indizes
                prompt += f"<|start_header_id|>user<|end_header_id|>\n\n{message}"
            else:  # 'assistant' Nachrichten an geraden Indizes
                prompt += f"<|start_header_id|>assistant<|end_header_id|>\n\n{message}"

        prompt += "<|eot_id|>"  # Endmarker

        response = await llm_generate(prompt)


        """
        print("Gesamte Konversation:")
        print("+" * 50)
        for msg in messages:  # Alle Nachrichten ausgeben
            print(msg + "\n\n")
        print(response + "\n\n")
        print("-" * 50)  # Trennlinie für bessere Lesbarkeit
        """

        return response



    except Exception as e:
        logger.error(f"An error occurred during text processing: {e}")
        return f"An error occurred: {e}"





async def llm_generate(messages: list[dict]) -> str:
    global pipe
    global gen_config
    response = pipe(messages, gen_config)

    if response:
        return response.text
    else:
        return "Error: No response generated."

async def llm_generate_by_text(prompt: str) -> str:
    # Antwort generieren
    global pipe
    global gen_config
    prompt = [{
        'role': 'user',
        'content': 'Hi, pls intro yourself'
    }]
    response = pipe(prompt, gen_config)
    # print("RESPONSE \n")
    # print(response.text)
    #response = await asyncio.to_thread(
    #    pipe,
    #    prompt,
    #    top_p=gen_config.top_p,
    #    top_k=gen_config.top_k,
    #    temperature=gen_config.temperature,
    #    max_new_tokens=gen_config.max_new_tokens,
    #)

    # Antwort prüfen
    if response:
        return response.text
    else:
        return "Error: No response generated."


async def get_reply(message_content: str) -> str:

    global pipe
    # Prompt definieren
    system_prompt = (
        "You are a helpful assistant. "
        "Always answer as helpfully as possible, while being safe. "
        "Your answers should not include any harmful, unethical, or illegal content."
    )
    prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n{system_prompt}\n" \
             f"<|start_header_id|>user<|end_header_id|>\n{message_content}<|eot_id|>"

    llm_generate(prompt)

async def save_result_to_json(result: dict):
    """
    Speichert ein Ergebnis als JSON-Datei im 'documents'-Verzeichnis (asynchron).
    """
    try:
        output_dir = os.path.join(get_project_path(), "documents")
        os.makedirs(output_dir, exist_ok=True)

        file_path = os.path.join(output_dir, "result.json")
        # Dateioperationen asynchron ausführen
        await asyncio.to_thread(
            lambda: json.dump(result, open(file_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=4)
        )
    except Exception as e:
        logger.error(f"Error while saving result to JSON: {e}")

