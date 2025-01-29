import logging
import json
import time
from auth import session, login, BASE_URL

def get_realtime_data(device_id):
    """
    Pobranie danych w czasie rzeczywistym dla urządzenia (inwertera).
    Jeśli sesja wygasa, ponawia logowanie i próbuje ponownie.
    """
    url = f"{BASE_URL}/getDevRealKpi"
    payload = {
        "devTypeId": "1",
        "devIds": device_id
    }

    while True:
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
                
                elif result.get("message") == "USER_MUST_RELOGIN":
                    logging.warning("Sesja wygasła. Próba ponownego logowania...")
                    if login():
                        continue  # Po zalogowaniu spróbuj ponownie pobrać dane
                    else:
                        logging.error("Nie udało się ponownie zalogować. Odczekam 5 minut.")
                        return None  # `main.py` sam ponowi próbę logowania
                    
                else:
                    logging.error(f"Błąd API: {result.get('message')}")
                    return None

            else:
                logging.error(f"Błąd HTTP {response.status_code}: {response.text}")
                return None

        except Exception as e:
            logging.error(f"Wyjątek podczas pobierania danych produkcji: {e}")
            logging.info("Odczekam 60 sekund przed kolejną próbą.")
            time.sleep(60)  # Krótsze oczekiwanie w przypadku awarii
