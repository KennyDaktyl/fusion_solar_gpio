import time
import logging
import os
import sys
from get_current_power import get_realtime_data
from auth import login
from utils import send_email_with_logs, get_current_time, disable_heater
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

    if log_date == current_log_date:
        return  

    current_log_date = log_date
    log_file = os.path.join(LOG_DIR, f"log_{log_date}.log")

    handler = logging.FileHandler(log_file)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.addHandler(handler)
    logging.info(f"Logowanie skonfigurowane na plik: {log_file}")

# Zmienne globalne
is_heater_on = False
start_time = None
operation_times = []
logged_in = False
email_sent = False

def main():
    global is_heater_on, start_time, logged_in, operation_times, email_sent, failed_login_attempts

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
                is_heater_on = disable_heater(GPIO, RELAY_PIN, is_heater_on, operation_times, start_time)
                logging.warning("Brak danych z API. Wyłączam grzałkę.")
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
            else:
                if 6 <= now.hour < 22:
                    logging.info(f"Aktualna produkcja mocy: {power} kW")
                print(f"{now.strftime('%H:%M:%S')} - Moc: {power} kW")
                
            # Reset licznika nieudanych prób, jeśli dane są dostępne
            failed_login_attempts = 0

            # Logika sterowania grzałką
            if power is not None and power > min_power:
                if not is_heater_on:
                    GPIO.output(RELAY_PIN, GPIO.HIGH)
                    is_heater_on = True
                    start_time = now.strftime('%H:%M')
                    logging.info(f"Moc {power} kW. Włączanie grzałki...")
                    print(f"{now.strftime('%H:%M:%S')} - Włączanie grzałki...")
            elif is_heater_on:
                is_heater_on = disable_heater(GPIO, RELAY_PIN, is_heater_on, operation_times, start_time)

            if now.hour >= 22 and not email_sent:
                send_email_with_logs(operation_times)
                email_sent = True  # Oznacz, że e-mail został wysłany
                operation_times = []

            if now.hour < 22:
                email_sent = False  # Reset flagi po północy

            time.sleep(180)  # Czekaj 3 minuty przed kolejną iteracją

        except KeyboardInterrupt:
            logging.info("Program zakończony przez użytkownika.")
            break
        except Exception as e:
            is_heater_on = disable_heater(GPIO, RELAY_PIN, is_heater_on, operation_times, start_time)
            logging.error(f"Nieoczekiwany błąd: {e}")
            logging.warning("Wyłączam grzałkę i oczekuję 60 sekund przed kolejną próbą.")
            time.sleep(60)  # Krótsza przerwa w razie awarii

    # Sprzątanie zasobów przed zamknięciem programu
    GPIO.output(RELAY_PIN, GPIO.LOW)
    GPIO.cleanup()
    sys.exit(0)

if __name__ == "__main__":
    main()