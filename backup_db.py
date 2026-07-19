import os
import json
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
BACKUP_DIR = "backups"
os.makedirs(BACKUP_DIR, exist_ok=True)

engine = create_engine(DATABASE_URL)

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
backup_file = os.path.join(BACKUP_DIR, f"gebeyabook_backup_{timestamp}.json")

with engine.connect() as conn:
    vendors = [dict(row._mapping) for row in conn.execute(text("SELECT * FROM vendors"))]
    transactions = [dict(row._mapping) for row in conn.execute(text("SELECT * FROM transactions"))]

def default(o):
    if hasattr(o, "isoformat"):
        return o.isoformat()
    return str(o)

backup_data = {"vendors": vendors, "transactions": transactions}

with open(backup_file, "w", encoding="utf-8") as f:
    json.dump(backup_data, f, ensure_ascii=False, indent=2, default=default)

print(f"Backup completed: {backup_file}")
print(f"  {len(vendors)} vendors, {len(transactions)} transactions")
