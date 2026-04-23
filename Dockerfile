FROM python:3.12-slim

WORKDIR /app

RUN pip install uvicorn

RUN pip install fastapi

RUN pip install httpx

RUN pip install python-multipart

RUN pip install requests

RUN apt update

RUN apt install -y curl

RUN pip install pydevd-pycharm~=243.22562.68

# RUN pip install json5

EXPOSE 8000

# ENTRYPOINT ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]