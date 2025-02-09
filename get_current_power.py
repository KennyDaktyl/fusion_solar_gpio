import logging
import json
import requests  # Dodanie obsługi błędów HTTP
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
            response = session.post(url, data=json.dumps(payload), timeout=10)
            response.raise_for_status()  # Rzuci wyjątek dla błędów HTTP (4xx, 5xx)
            
            result = response.json()
            
            if result.get("success"):
                data = result.get("data", [])
                if data:
                    current_power = data[0]["dataItemMap"].get("active_power", 0)
                    if current_power is not None:
                        current_power = round(float((current_power) / 1000), 2)  # Przeliczenie na kW
                    return True, current_power
                else:
                    logging.warning("Brak danych dla podanego urządzenia.")
                    return False, None
            
            elif result.get("message") == "USER_MUST_RELOGIN":
                logging.warning("Sesja wygasła. Próba ponownego logowania...")
                if login():
                    continue  # Po zalogowaniu ponów próbę pobrania danych
                else:
                    logging.error("Nie udało się ponownie zalogować. Odczekam 5 minut.")
                    # time.sleep(300)  # 5 minut oczekiwania przed kolejną próbą
                    return False, None
            
            else:
                logging.error(f"Błąd API: {result.get('message')}")
                return False, None

        except requests.exceptions.Timeout:
            logging.error("Przekroczono czas oczekiwania na odpowiedź API.")
            # time.sleep(60)  # 1 minuta przerwy
            return False, None
        
        except requests.exceptions.ConnectionError:
            logging.error("Brak połączenia z internetem! Sprawdzam ponownie za 5 minut.")
            # time.sleep(300)  # 5 minut przerwy przed kolejną próbą
            return False, None
        
        except requests.exceptions.RequestException as e:
            logging.error(f"Błąd HTTP: {e}")
            # time.sleep(60)  # 1 minuta przerwy przed kolejną próbą
            return False, None
        
        except Exception as e:
            logging.error(f"Nieoczekiwany błąd: {e}")
            # logging.info("Odczekam 60 sekund przed kolejną próbą.")
            # time.sleep(60)  # Krótsze oczekiwanie w przypadku awarii
            return False, None
