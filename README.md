# Parliamentary Protocol AI

An AI-powered system that automatically transcribes and summarizes parliamentary sessions for the **Bremen Parliament** (Bremische Bürgerschaft). Built as a university project at the University of Bremen (2024–2025).

The system turns raw audio recordings of parliamentary sessions into structured, topic-organized protocol documents — reducing hours of manual work to minutes.

## How It Works

```
                         ┌──────────────────┐
                         │   Audio Upload    │
                         │   (WAV file)      │
                         └────────┬─────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │   Speech-to-Text Service    │
                    │   (WhisperX + Speaker       │
                    │    Diarization)              │
                    └─────────────┬──────────────┘
                                  │
              ┌───────────────────▼───────────────────┐
              │         Orchestration Backend          │
              │                                        │
              │  1. Topic Assignment                   │
              │     LLM maps agenda items to           │
              │     transcript sections                │
              │                                        │
              │  2. Tournament Evaluation              │
              │     Multiple LLM passes compete;       │
              │     best topic assignments win         │
              │                                        │
              │  3. Chronological Cleanup              │
              │     Remove out-of-order assignments    │
              │                                        │
              │  4. Summarization Pipeline             │
              │     LLM summarizes each section        │
              │     → Grammar correction pass          │
              │     → Timestamp reinsertion pass       │
              │                                        │
              └───────────────────┬───────────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │    Structured Protocol      │
                    │    (DOCX export with        │
                    │     timestamps & topics)    │
                    └────────────────────────────┘
```

## Architecture

The system consists of five microservices communicating via REST APIs:

| Service | Port | Purpose | Tech |
|---------|------|---------|------|
| **Frontend** | 3000 | Web UI for parliament staff | React |
| **Backend** (this repo) | 8000 | Orchestration, LLM pipeline, business logic | FastAPI, Python |
| **LLM Service** | 8002 | Local LLM inference | lmdeploy, TurboMind, Llama 3.1 8B AWQ |
| **Transcription Service** | 8001 | Speech-to-text | WhisperX |
| **Database Service** | 8010 | Data persistence, auth, DOCX generation | FastAPI, PostgreSQL |

All services are containerized with **Docker** and use **NVIDIA GPU acceleration** for inference.

## Key Technical Decisions

**Tournament-style evaluation for topic assignment:**
Rather than relying on a single LLM pass (which is error-prone), the system runs multiple topic assignment passes and uses a tournament bracket to select the best assignment for each agenda item. An LLM acts as judge, comparing pairs of assignments on context and accuracy.

**Multi-stage summarization pipeline:**
Raw LLM summaries often have grammar issues and lose timestamp references. The pipeline runs three sequential LLM passes: summarization → grammar correction → timestamp reinsertion. This consistently produces higher-quality output than a single-pass approach.

**State machine for workflow coordination:**
Project status transitions (`INITIAL → IS_TRANSCRIBING → TRANSCRIBED → IS_SUMMARIZING → COMPLETED`) prevent race conditions between transcription and summarization. The protocol template must be approved before summarization begins, but the user can still edit it while transcription runs.

**Async background processing:**
Long-running tasks (transcription, summarization) run as background tasks via `asyncio.create_task()`, so the API remains responsive. Token refresh is handled automatically for long-running operations.

## My Role

I developed the **entire backend** of this project:

- Designed and implemented the multi-service architecture
- Built the orchestration layer that coordinates transcription, topic assignment, evaluation, and summarization
- Implemented the LLM inference service with quantized model serving via lmdeploy/TurboMind
- Developed the tournament-style evaluation algorithm for topic assignment quality
- Created the multi-stage summarization pipeline with grammar correction and timestamp handling
- Set up Docker containerization with GPU passthrough for all AI services
- Integrated WhisperX for speaker-diarized transcription

## Tech Stack

- **Python 3.12** — Core language across all backend services
- **FastAPI** — Async REST API framework
- **lmdeploy (TurboMind)** — High-performance LLM inference engine
- **Llama 3.1 8B (AWQ 4-bit)** / **DeepSeek-R1-Distill-Qwen-32B** — Quantized language models
- **WhisperX** — Speech-to-text with speaker diarization
- **PostgreSQL** — Data persistence
- **Docker + NVIDIA CUDA** — Containerized GPU inference
- **httpx** — Async HTTP client for inter-service communication
- **Pydantic** — Request/response validation

## Project Structure

```
├── src/
│   ├── main.py                        # FastAPI application entry point
│   ├── config.py                      # Environment configuration
│   │
│   ├── Api/
│   │   ├── api_llm.py                 # LLM orchestration (topicize → evaluate → summarize)
│   │   ├── api_transcription.py       # Transcription workflow coordination
│   │   ├── api_protocol.py            # Protocol generation endpoints
│   │   ├── api_protocol_template.py   # Template approval state machine
│   │   └── api_db.py                  # Database proxy layer
│   │
│   ├── Handler/
│   │   └── handler_llm.py             # LLM pipeline logic (tournament eval, summarization)
│   │
│   ├── Client/
│   │   └── client_db.py               # HTTP client for database service
│   │
│   ├── Classes/
│   │   ├── protocol.py                # Protocol, Table, NestedEntry (table of contents)
│   │   ├── transcript_mini.py         # TranscriptMini, SpeakerTranscript, Topic, Chapter
│   │   └── transcript_evaluator.py    # Tournament-style transcript comparison
│   │
│   ├── Schemes/
│   │   └── api_schemes.py             # Pydantic request/response models
│   │
│   ├── Prompts/
│   │   ├── prompt_topics.txt           # Topic assignment prompt template
│   │   ├── prompt_topics_evaluate.txt  # Topic evaluation prompt template
│   │   ├── prompt_summarize.txt        # Summarization prompt template
│   │   ├── prompt_summarization_correction.txt
│   │   └── prompt_timestamps_add.txt   # Timestamp reinsertion prompt
│   │
│   └── Utils/
│       ├── fileUtils.py               # File I/O helpers
│       ├── pathUtils.py               # Path resolution
│       ├── class_dict.py              # Object ↔ dict serialization
│       └── utils_estimations.py       # ETA calculations for processing
│
├── llm-service/                       # Standalone LLM inference server
│   ├── src/
│   │   ├── main.py
│   │   ├── api/api_lmdeploy.py
│   │   ├── handler/handler_lmdeploy.py
│   │   └── utils/
│   ├── Dockerfile
│   └── requirements.txt
│
├── Dockerfile
├── requirements.txt
├── docker-compose.yml
└── README.md
```

## Running Locally

### Prerequisites

- NVIDIA GPU with CUDA support (16+ GB VRAM recommended)
- Docker with NVIDIA Container Toolkit
- Python 3.12

### Quick Start

```bash
# Clone the repo
git clone https://github.com/uyar1/parliamentary-protocol-ai.git
cd parliamentary-protocol-ai

# Start the LLM service (requires GPU)
cd llm-service
docker build -t bb-llm-service .
docker run --gpus all -p 8002:8002 \
  -v $(pwd)/models:/root/.cache/huggingface \
  bb-llm-service

# Start the orchestration backend
cd ..
pip install -r requirements.txt
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## Context

This project was developed as part of a university software engineering course at the **University of Bremen** in collaboration with the **Bremische Bürgerschaft** (Bremen State Parliament). The goal was to reduce the manual effort of creating parliamentary session protocols by automating transcription and summarization while keeping human editors in the loop for final review.

## License

University project — developed at the University of Bremen, 2024–2025.
