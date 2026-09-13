FROM python:3.11-slim

# Installer LibreOffice (nécessaire pour Word → PDF)
RUN apt-get update && apt-get install -y libreoffice && apt-get clean

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Le port est fourni par Render via la variable $PORT
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
