"""Create the initial Render administrator from one-time deployment secrets."""
from pathlib import Path
import os, sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.main import SessionLocal, User, pwd

email=os.environ.get('INITIAL_ADMIN_EMAIL','').strip().lower()
password=os.environ.get('INITIAL_ADMIN_PASSWORD','')
name=os.environ.get('INITIAL_ADMIN_NAME','Portal Administrator').strip()
if not email or not password:
    print('No initial admin secrets supplied; create the first administrator at /setup using SECRET_KEY.')
    raise SystemExit(0)
if len(password)<12:
    raise SystemExit('INITIAL_ADMIN_PASSWORD must be at least 12 characters.')
db=SessionLocal()
try:
    if db.query(User).count()==0:
        db.add(User(name=name,email=email,role='Admin',department='Administration',password_hash=pwd.hash(password)))
        db.commit()
        print(f'Created initial administrator: {email}')
    else:
        print('User records already exist; no bootstrap account created.')
finally:
    db.close()
