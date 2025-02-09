import psycopg2
import logging
from config import DB_CONFIG

def get_db_connection():
    """Nawiązuje połączenie z bazą danych PostgreSQL."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        logging.error(f"Błąd połączenia z bazą danych: {e}")
        return None

def create_table():
    """Tworzy tabelę, jeśli nie istnieje."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS power_monitoring (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status BOOLEAN NOT NULL,
                        power NUMERIC(10,2) NULL
                    );
                """)
                conn.commit()
        except psycopg2.Error as e:
            logging.error(f"Błąd tworzenia tabeli: {e}")
        finally:
            conn.close()

def save_reading(status, power):
    """Zapisuje odczyt do bazy danych."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO power_monitoring (status, current_power) 
                    VALUES (%s, %s);
                """, (status, power))
                conn.commit()
        except psycopg2.Error as e:
            logging.error(f"Błąd zapisu do bazy: {e}")
        finally:
            conn.close()
