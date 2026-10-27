"""Promote an existing registered user to admin: python create_admin.py email@example.com"""
import sys
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models import User

if len(sys.argv) != 2:
    sys.exit('Usage: python create_admin.py email@example.com')
with SessionLocal() as db:
    user = db.scalar(select(User).where(User.email == sys.argv[1].lower()))
    if user is None:
        sys.exit('User not found. Register via POST /auth/register first.')
    user.is_admin = True
    db.commit()
    print(f'Admin privileges granted: {user.email}')
