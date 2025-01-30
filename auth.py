import requests
import json
import logging
from dotenv import load_dotenv
import os

load_dotenv()

BASE_URL = "https://eu5.fusionsolar.huawei.com/thirdData"
USERNAME = os.getenv("USERNAME_FUSION_ID")
PASSWORD = os.getenv("PASSWORD_FUSION")

# Tworzenie sesji
session = requests.Session()

def login():
    """
    Logowanie do API FusionSolar i uzyskanie tokena XSRF.
    """
    url = f"{BASE_URL}/login"
    payload = {
        "userName": USERNAME,
        "systemCode": PASSWORD
    }
    headers = {
        "Content-Type": "application/json"
    }

    try:
        logging.info("Próba logowania do API FusionSolar...")
        response = session.post(url, data=json.dumps(payload), headers=headers, timeout=10)
        response.raise_for_status()  # Rzuca wyjątek dla błędów HTTP (4xx, 5xx)
        
        result = response.json()
        if result.get("success"):
            logging.info("Logowanie udane.")
            session.headers.update({"XSRF-TOKEN": session.cookies.get("XSRF-TOKEN")})
            return True
        else:
            logging.warning(f"Błąd logowania: {result.get('message')}")
    
    except requests.exceptions.Timeout:
        logging.error("Przekroczono czas oczekiwania na logowanie do API.")
        return False
    except requests.exceptions.ConnectionError:
        logging.error("Brak połączenia z internetem! Nie można zalogować się do API.")
        return False
    except requests.exceptions.RequestException as e:
        logging.error(f"Błąd logowania: {e}")
        return False
    
    return False  # Zwróć False jeśli logowanie się nie udało
