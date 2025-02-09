import os

# Konfiguracja PostgreSQL
DB_CONFIG = {
    "dbname": "inverter_data",
    "user": os.environ.get("POSTGRES_USER"),
    "password": os.environ.get("POSTGRES_PASSWORD"),
    "host": "localhost",
    "port": 5432
}
