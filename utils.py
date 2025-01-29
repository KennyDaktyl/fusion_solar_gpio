# utils.py
import os
import logging
import pytz
from datetime import datetime
from email.message import EmailMessage
import smtplib

LOG_DIR = "logs"

def send_email_with_logs(operation_times):
    """
    Wysyła logi z bieżącego dnia oraz zestawienie czasowe na podany e-mail.
    """
    email = os.getenv("EMAIL")
    email_password = os.getenv("EMAIL_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))

    log_file = os.path.join(LOG_DIR, f"log_{datetime.now().strftime('%Y-%m-%d')}.log")

    if not email or not email_password:
        logging.error("Brak konfiguracji e-mail w pliku .env")
        return

    try:
        with open(log_file, "r") as log_file:
            log_content = log_file.read()

        # Przygotowanie zestawienia czasowego
        operation_summary = "Zestawienie czasowe pracy grzałki:\n"
        for start, end in operation_times:
            operation_summary += f"Włączona od {start} do {end}\n"
        operation_summary += "\n\n"

        msg = EmailMessage()
        msg["Subject"] = f"Logi Raspberry Pi z dnia {datetime.now().strftime('%Y-%m-%d')}"
        msg["From"] = email
        msg["To"] = email
        msg.set_content(operation_summary + log_content)

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email, email_password)
            server.send_message(msg)
            logging.info("Logi i zestawienie czasowe wysłane na e-mail.")
    except Exception as e:
        logging.error(f"Błąd podczas wysyłania e-maila: {e}")


# Ustawienie strefy czasowej Warszawy
warsaw_tz = pytz.timezone("Europe/Warsaw")

def get_current_time():
    """Funkcja zwraca aktualny czas w strefie czasowej Warszawy."""
    return datetime.now(warsaw_tz)
