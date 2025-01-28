# Użyj lekkiego obrazu Python jako bazy
FROM python:3.12-slim

# Ustaw katalog roboczy w kontenerze
WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*
    
# Skopiuj pliki projektu do obrazu
COPY . .

# Instalacja narzędzi kompilacji i zależności systemowych
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    python3-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*
    
# Zainstaluj wymagane zależności
RUN pip install --no-cache-dir -r requirements.txt

# Ustaw zmienne środowiskowe
ENV PYTHONUNBUFFERED=1

# Uruchom aplikację
CMD ["python", "main.py"]
