FROM python:3.8-slim-buster

WORKDIR /app

COPY server.py .

COPY requirements.txt .

RUN pip install -r requirements.txt 

CMD ["python", "server.py"]
