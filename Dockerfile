FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements-server.txt requirements.txt ./
RUN pip install --no-cache-dir -r requirements-server.txt

COPY app.py database.py parsers.py scheduler.py seed_demo.py ./
COPY templates ./templates
COPY ejemplos ./ejemplos
COPY src/UNESR.png ./src/UNESR.png

RUN mkdir -p uploads

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--worker-class", "gthread", "--threads", "4", "app:app"]
