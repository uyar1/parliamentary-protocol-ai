# Basis-Image mit Python 3.12
FROM python:3.12-slim


# Arbeitsverzeichnis setzen
WORKDIR /app
# WORKDIR /app
# WORKDIR /app/bb_backend

ENV PYTHONPATH=/app/src

# RUN pip install lmdeploy

RUN apt-get update

# FastAPI
RUN pip install --no-cache-dir fastapi

# Uvicorn
RUN pip install --no-cache-dir uvicorn

# apt install git

RUN pip install huggingface_hub


# curl und git nicht vergessen




RUN pip install --no-cache-dir python-multipart

RUN pip install lmdeploy

RUN pip install autoawq

RUN apt-get install -y build-essential

RUN pip install nest-asyncio

# Port freigeben (Standard für FastAPI und Uvicorn)
EXPOSE 8002

# Befehl zum Starten der Anwendung
# CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
CMD echo "Aktuelles Verzeichnis:" && ls -alh /app && echo "Starte Uvicorn..." && uvicorn src.main:app --host 0.0.0.0 --port 8002
