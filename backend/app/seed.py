import argparse
from sqlalchemy import select
from .database import Base, engine, SessionLocal
from .models import User, UserRole
from .security import hash_password

def main():
    p=argparse.ArgumentParser(); p.add_argument("--email",required=True); p.add_argument("--password",required=True); p.add_argument("--name",default="Makwande Gcora"); a=p.parse_args()
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        existing=db.scalar(select(User).where(User.email==a.email.lower()))
        if existing:
            existing.full_name=a.name; existing.password_hash=hash_password(a.password); existing.role=UserRole.CEO.value; existing.is_active=True; existing.must_change_password=True
        else:
            db.add(User(full_name=a.name,email=a.email.lower(),password_hash=hash_password(a.password),role=UserRole.CEO.value,job_title="Founder & Chief Executive Officer",must_change_password=True))
        db.commit(); print(f"CEO account ready: {a.email.lower()}")
if __name__=="__main__": main()
