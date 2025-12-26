FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir pyTelegramBotAPI==4.14.0

COPY main.py .

CMD ["python", "main.py"]
