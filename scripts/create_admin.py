from pathlib import Path
import sys, getpass
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.main import SessionLocal, User, pwd
db=SessionLocal(); name=input('Administrator name: '); email=input('Email: ').strip().lower(); password=getpass.getpass('Password (12+ characters): ')
if len(password)<12: raise SystemExit('Password must be at least 12 characters.')
if db.query(User).filter_by(email=email).first(): raise SystemExit('That email is already registered.')
db.add(User(name=name,email=email,role='Admin',department='Administration',password_hash=pwd.hash(password))); db.commit(); print('Administrator account created.')
