import time
import logging
import os
import sys
from datetime import datetime
from get_current_power import get_realtime_data
from auth import login
from utils import send_email_with_logs, get_current_time
from dotenv import load_dotenv

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

def setup_logging():
    """Konfiguracja logowania z dynamiczną zmianą plików logów po północy."""
    log_file = os.path.join(LOG_DIR, f"log_{get_current_time().strftime('%Y-%m-%d')}.log")

    # Tworzenie nowego handlera logów
    handler = logging.FileHandler(log_file)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    # Czyszczenie poprzednich handlerów, aby uniknąć duplikacji logów
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.addHandler(handler)
    logging.info("Konfiguracja logowania zakończona.")
    return log_file

LOG_FILE = setup_logging()

# Zmienne globalne
is_heater_on = False  # Stan grzałki
start_time = None  # Czas rozpoczęcia pracy grzałki
operation_times = []
logged_in = False
last_email_hour = None  # Przechowuje godzinę ostatniego wysłania e-maila

def main():
    global is_heater_on, start_time, logged_in, operation_times, last_email_hour, LOG_FILE

    device_id = os.getenv("DEVICE_ID")
    min_power = float(os.getenv("MIN_POWER_TO_ON", "5"))  # Domyślnie 5 kW, jeśli brak wartości w .env

    logging.info("Uruchamianie aplikacji. Program działa 24/7.")

    while True:
        try:
            now = get_current_time()

            # Zmiana pliku logów po północy
            current_log_file = os.path.join(LOG_DIR, f"log_{now.strftime('%Y-%m-%d')}.log")
            if logging.getLogger().handlers[0].baseFilename != current_log_file:
                logging.info("Zmiana daty. Przełączanie logów na nowy plik.")
                LOG_FILE = setup_logging()

            # Próba logowania co 5 minut, jeśli jest niezalogowany
            if not logged_in:
                logging.info("Próba logowania...")
                logged_in = login()
                if not logged_in:
                    logging.error("Logowanie nieudane. Ponowna próba za 5 minut.")
                    time.sleep(300)
                    continue  # Powrót na początek pętli, by ponowić logowanie

            # Pobranie mocy z API
            power = get_realtime_data(device_id)

            if power is not None:
                print(f"{now.strftime('%H:%M:%S')} - Moc: {power} kW")
                logging.info(f"Aktualna moc: {power} kW")
            else:
                logging.warning("Brak danych o mocy. Sprawdzam ponownie za 3 minuty.")

            # Logika sterowania grzałką
            if power is not None and power > min_power:
                if not is_heater_on:
                    GPIO.output(RELAY_PIN, GPIO.HIGH)
                    is_heater_on = True
                    start_time = now.strftime('%H:%M')
                    logging.info(f"Moc przekracza {min_power} kW. Włączanie grzałki...")
            else:
                if is_heater_on:
                    GPIO.output(RELAY_PIN, GPIO.LOW)
                    is_heater_on = False
                    end_time = now.strftime('%H:%M')
                    operation_times.append((start_time, end_time))
                    logging.info(f"Moc poniżej {min_power} kW. Wyłączanie grzałki...")

            # Wysyłanie e-maila co godzinę
            if last_email_hour is None or last_email_hour != now.hour:
                send_email_with_logs(operation_times)
                last_email_hour = now.hour
                operation_times = []  # Reset historii czasów działania

            time.sleep(180)  # Czekaj 3 minuty przed kolejną iteracją

        except KeyboardInterrupt:
            logging.info("Program zakończony przez użytkownika.")
            break
        except Exception as e:
            logging.error(f"Nieoczekiwany błąd: {e}")
            logging.info("Odczekam 60 sekund przed kolejną próbą.")
            time.sleep(60)  # Krótsza przerwa w razie awarii

    # Sprzątanie zasobów przed zamknięciem programu
    GPIO.output(RELAY_PIN, GPIO.LOW)
    GPIO.cleanup()
    sys.exit(0)

if __name__ == "__main__":
    main()
