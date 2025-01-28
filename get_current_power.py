# get_power.py
import logging
import json
import time
from auth import session, login, BASE_URL

def get_realtime_data(device_id):
    """
    Pobranie danych w czasie rzeczywistym dla urządzenia (inwertera).
    """
    url = f"{BASE_URL}/getDevRealKpi"
    payload = {
        "devTypeId": "1",
        "devIds": device_id
    }

    try:
        response = session.post(url, data=json.dumps(payload))
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                data = result.get("data", [])
                if data:
                    current_power = data[0]["dataItemMap"].get("active_power", 0)
                    logging.info(f"Aktualna produkcja mocy: {current_power} kW")
                    return current_power
                else:
                    logging.warning("Brak danych dla podanego urządzenia.")
                    return None
            else:
                logging.error(f"Błąd podczas pobierania danych produkcji: {result.get('message')}")
                if result.get("message") == "USER_MUST_RELOGIN":
                    logging.info("Sesja wygasła. Logowanie ponowne...")
                    time.sleep(300)  # Odczekaj 5 minut i spróbuj ponownie
                    if login():
                        return get_realtime_data(device_id)
                return None
        else:
            logging.error(f"Błąd podczas pobierania danych produkcji: {response.json()}")
            return None
    except Exception as e:
        logging.error(f"Wyjątek podczas pobierania danych produkcji: {e}")
        return None
