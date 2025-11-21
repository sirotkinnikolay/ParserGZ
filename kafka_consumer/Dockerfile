FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc curl netcat-openbsd \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY src /usr/src/app

EXPOSE 80
CMD ["python", "main.py"]
# Если FastApi то запускать его
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]

