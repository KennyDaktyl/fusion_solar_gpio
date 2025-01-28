# Użyj lekkiego obrazu Python jako bazy
FROM python:3.12-slim

# Ustaw katalog roboczy w kontenerze
WORKDIR /app

# Skopiuj pliki projektu do obrazu
COPY . .

# Zainstaluj wymagane zależności
RUN pip install --no-cache-dir -r requirements.txt

# Ustaw zmienne środowiskowe
ENV PYTHONUNBUFFERED=1

# Uruchom aplikację
CMD ["python", "main.py"]
