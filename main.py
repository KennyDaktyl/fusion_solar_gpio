import time
import logging
from datetime import datetime
from get_current_power import get_realtime_data
from auth import login
from utils import send_email_with_logs
from dotenv import load_dotenv
import os

# Sprawdzenie dostępności RPi.GPIO
try:
    import RPi.GPIO as GPIO
except (ImportError, RuntimeError):
    from mock_gpio import GPIO  # Import symulowanego modułu GPIO

load_dotenv()

# Konfiguracja GPIO
RELAY_PIN = 17  # GPIO pin sterujący
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.output(RELAY_PIN, GPIO.LOW)

# Konfiguracja logów
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def get_log_file():
    """Funkcja zwraca ścieżkę do pliku logów na podstawie aktualnej daty."""
    return os.path.join(LOG_DIR, f"log_{datetime.now().strftime('%Y-%m-%d')}.log")

def setup_logging():
    """Funkcja konfiguruje logowanie dla aktualnej daty."""
    log_file = get_log_file()
    logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    return log_file

# Ustawienie początkowego pliku logów
LOG_FILE = setup_logging()

is_heater_on = False  # Stan grzałki
start_time = None  # Czas rozpoczęcia pracy grzałki
operation_times = []
logged_in = False
last_email_hour = None  # Przechowuje godzinę ostatniego wysłania e-maila

def main():
    device_id = os.getenv("DEVICE_ID")

    logging.info("Rozpoczynanie pętli logowania i odpytywania...")
    try:
        global is_heater_on, start_time, logged_in, operation_times, last_email_hour, LOG_FILE

        while True:
            # Sprawdzenie, czy zmieniła się data i aktualizacja logów
            current_log_file = get_log_file()
            if current_log_file != LOG_FILE:
                logging.info("Zmiana daty. Zmieniamy plik logów.")
                LOG_FILE = current_log_file
                setup_logging()  # Re-konfiguracja logowania

            # Próba logowania
            if not logged_in:
                logged_in = login()
                if not logged_in:
                    logging.error("Nie udało się zalogować. Ponowna próba za 5 minut.")
                    time.sleep(300)
                    continue

            # Główna pętla odpytywania
            power = get_realtime_data(device_id)
            now = datetime.now()

            if power is not None and power > float(os.getenv("MIN_POWER_TO_ON")):
                if not is_heater_on:
                    GPIO.output(RELAY_PIN, GPIO.HIGH)
                    is_heater_on = True
                    start_time = now.strftime('%H:%M')
                    logging.info("Moc przekracza 5 kW. Włączanie grzałki...")
            else:
                if is_heater_on:
                    GPIO.output(RELAY_PIN, GPIO.LOW)
                    is_heater_on = False
                    end_time = now.strftime('%H:%M')
                    operation_times.append((start_time, end_time))
                    if power:
                        logging.info(f"Moc poniżej {os.getenv('MIN_POWER_TO_ON')} kW. Wyłączanie grzałki...")
                    else:
                        logging.warning("Brak danych mocy. Wyłączanie grzałki...")

            # Wysyłanie logów raz na godzinę
            current_hour = now.hour
            if last_email_hour != current_hour:
                send_email_with_logs(operation_times)
                last_email_hour = current_hour
                operation_times = []
                if os.path.exists(LOG_FILE):
                    os.remove(LOG_FILE)
                    logging.info(f"Plik logów {LOG_FILE} został usunięty.")

            time.sleep(180)  # Przerwa 3 minuty
    except KeyboardInterrupt:
        logging.info("Program zakończony przez użytkownika.")
    finally:
        GPIO.output(RELAY_PIN, GPIO.LOW)  # Upewnij się, że grzałka jest wyłączona
        GPIO.cleanup()

if __name__ == "__main__":
    main()
