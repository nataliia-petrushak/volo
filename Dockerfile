FROM python:3.12.0-slim

WORKDIR /code

COPY volo_backend/requirements.txt .

RUN apt-get update &&  \
    apt-get install -y mpv &&\
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY volo_backend .

CMD ["python", "main.py"]
