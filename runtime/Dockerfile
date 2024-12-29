FROM python:3.12.8-slim-bullseye

WORKDIR /app

COPY runtime.py /app/runtime.py

RUN mkdir -p /opt /tmp

# COPY requirements.txt /app/requirements.txt
# RUN pip install --no-cache-dir -r requirements.txt

# Comando para executar o runtime.py
CMD ["python", "/app/runtime.py"]
