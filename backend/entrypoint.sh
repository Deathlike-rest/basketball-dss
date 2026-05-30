#!/usr/bin/env bash
set -e

echo "Ожидание готовности PostgreSQL…"
python - <<'PY'
import os, time
import psycopg2
url = os.environ.get("DATABASE_URL", "")
dsn = url.replace("postgresql+psycopg2://", "postgresql://")
for _ in range(30):
    try:
        psycopg2.connect(dsn).close()
        print("PostgreSQL готов.")
        break
    except Exception as e:
        print("…ждём БД:", e)
        time.sleep(2)
else:
    raise SystemExit("PostgreSQL недоступен")
PY

# Наполняем БД демо-данными, если игроков ещё нет.
python - <<'PY'
from app import create_app
from models import Player
app = create_app()
with app.app_context():
    from models import db
    db.create_all()
    if Player.query.count() == 0:
        print("База пуста — запускаю seed…")
        import seed
        seed.seed()
    else:
        print(f"В базе уже {Player.query.count()} игроков — seed пропущен.")
PY

echo "Запуск сервера приложения (Flask) на :5000"
exec python app.py
