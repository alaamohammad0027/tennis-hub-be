#!/usr/bin/env python3

import os
import time
import psycopg2

# Wait for the database to be ready
while True:
    try:
        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST"),
            port=os.environ.get("DB_PORT", "5432"),
            user=os.environ.get("POSTGRES_USER"),
            password=os.environ.get("POSTGRES_PASSWORD"),
            database=os.environ.get("POSTGRES_DB"),
        )
        break
    except psycopg2.OperationalError as e:
        print(e)
        print("Waiting for database...")
        time.sleep(1)
