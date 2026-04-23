from fastapi import FastAPI
from src.Api.api_llm import router as api_llm_router
from src.Api.api_protocol import router as router_api_summary
from src.Api.api_transcription import router as api_transcription_router
from src.Api.api_db import router as api_db_router
from src.Api.api_protocol_template import router as api_protocol_template_router
import os
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
# import pydevd_pycharm


app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Erlaube alle Ursprünge (Testzweck)
    allow_credentials=True,
    allow_methods=["*"],  # Erlaube POST, GET, OPTIONS, usw.
    allow_headers=["*"],  # Erlaube alle Header
)
app.include_router(api_llm_router)
app.include_router(router_api_summary)
app.include_router(api_transcription_router)
app.include_router(api_db_router)
app.include_router(api_protocol_template_router)


print(os.getcwd())

if __name__ == '__main__':
    print("BLAAAAAAAAAAAAAAAAAA")
    uvicorn.run("src.main:app", host='0.0.0.0', port=8000, reload=True)
@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
