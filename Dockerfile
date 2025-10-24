FROM python:3.7-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    postgresql-client \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

COPY . .

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

