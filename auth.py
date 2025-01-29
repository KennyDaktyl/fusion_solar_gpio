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
        response = session.post(url, data=json.dumps(payload), headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                logging.info("Logowanie udane.")
                session.headers.update({"XSRF-TOKEN": session.cookies.get("XSRF-TOKEN")})
                return True
            else:
                logging.warning(f"Błąd logowania: {result.get('message')}")
        
        else:
            logging.error(f"Błąd logowania HTTP {response.status_code}: {response.text}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Nie udało się połączyć z API: {e}")

    return False  # Zwróć False jeśli logowanie się nie udało
