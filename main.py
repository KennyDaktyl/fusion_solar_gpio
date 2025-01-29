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
RELAY_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.output(RELAY_PIN, GPIO.LOW)

# Konfiguracja logów
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

current_log_date = None  # Globalna zmienna dla daty logów
failed_login_attempts = 0  # Licznik nieudanych logowań

def setup_logging():
    """Konfiguracja logowania - przełączanie logów tylko raz na dobę."""
    global current_log_date

    now = get_current_time()
    log_date = now.strftime('%Y-%m-%d')

    # Przełączanie logów tylko jeśli zmieniła się data
    if log_date == current_log_date:
        return  

    current_log_date = log_date
    log_file = os.path.join(LOG_DIR, f"log_{log_date}.log")

    handler = logging.FileHandler(log_file)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Usunięcie poprzednich handlerów (zapobiega duplikacji logów)
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.addHandler(handler)
    logging.info(f"Logowanie skonfigurowane na plik: {log_file}")

# Zmienne globalne
is_heater_on = False
start_time = None
operation_times = []
logged_in = False
last_email_hour = None

def main():
    global is_heater_on, start_time, logged_in, operation_times, last_email_hour, failed_login_attempts

    device_id = os.getenv("DEVICE_ID")
    min_power = float(os.getenv("MIN_POWER_TO_ON", "5"))  # Domyślnie 5 kW, jeśli brak wartości w .env

    logging.info("Uruchamianie aplikacji. Program działa 24/7.")

    while True:
        try:
            now = get_current_time()
            setup_logging()  # Przełączanie logów tylko raz na dobę

            # Pobranie mocy z API
            power = get_realtime_data(device_id)

            if power is None:
                logging.warning("Brak danych z API. Możliwe, że sesja wygasła.")
                if not logged_in:
                    logging.info("Sesja wygasła. Próba ponownego logowania...")
                    logged_in = login()

                    if not logged_in:
                        failed_login_attempts += 1
                        logging.error(f"Logowanie nieudane. Próba {failed_login_attempts}/3. Czekam 5 minut.")
                        time.sleep(600 if failed_login_attempts >= 3 else 300)
                        continue

                    failed_login_attempts = 0  # Zresetowanie licznika, jeśli logowanie się powiodło
                    continue  # Powtarzamy iterację, aby pobrać dane po zalogowaniu

            # Reset licznika nieudanych prób, jeśli dane są dostępne
            failed_login_attempts = 0

            print(f"{now.strftime('%H:%M:%S')} - Moc: {power} kW")
            logging.info(f"Aktualna moc: {power} kW")

            # Logika sterowania grzałką
            if power > min_power:
                if not is_heater_on:
                    GPIO.output(RELAY_PIN, GPIO.HIGH)
                    is_heater_on = True
                    start_time = now.strftime('%H:%M')
                    logging.info(f"Moc {power} kW. Włączanie grzałki...")
                    print(f"{now.strftime('%H:%M:%S')} - Włączanie grzałki...")
            elif is_heater_on:
                GPIO.output(RELAY_PIN, GPIO.LOW)
                is_heater_on = False
                end_time = now.strftime('%H:%M')
                operation_times.append((start_time, end_time))
                logging.info(f"Moc spadła poniżej {min_power} kW. Wyłączanie grzałki.")
                print(f"{now.strftime('%H:%M:%S')} - Wyłączanie grzałki.")

            # Wysyłanie e-maila co godzinę
            if last_email_hour is None or last_email_hour != now.hour:
                send_email_with_logs(operation_times)
                last_email_hour = now.hour
                print(operation_times)
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
