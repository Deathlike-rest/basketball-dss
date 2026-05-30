FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=app.py
EXPOSE 5000

# entrypoint ждёт БД, при необходимости наполняет демо-данными и запускает сервер.
RUN chmod +x entrypoint.sh
CMD ["./entrypoint.sh"]
