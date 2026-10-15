"""Import the authoritative GZU student/staff identity roster.

CSV headers: identifier,full_name,identity_type,institutional_email
identity_type must be student or employee. Obtain this file from Registry/HR.
Run from Backend/: python import_identity_roster.py path/to/gzu_identity_roster.csv
"""
import csv
import sys
from database import SessionLocal, Base, engine
from models import InstitutionalIdentity, Voter

def main(path):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    count = 0
    try:
        with open(path, newline="", encoding="utf-8-sig") as stream:
            reader = csv.DictReader(stream)
            required = {"identifier", "full_name", "identity_type"}
            if not required.issubset(set(reader.fieldnames or [])):
                raise SystemExit("CSV must contain identifier,full_name,identity_type headers.")
            for row in reader:
                identifier = (row.get("identifier") or "").strip().upper()
                name = (row.get("full_name") or "").strip()
                kind = (row.get("identity_type") or "").strip().lower()
                email = (row.get("institutional_email") or "").strip() or None
                if not identifier or not name or kind not in {"student", "employee"}:
                    raise ValueError("Each row needs an identifier, full name, and identity_type student/employee.")
                identity = db.query(InstitutionalIdentity).filter_by(identifier=identifier).first()
                if identity is None:
                    identity = InstitutionalIdentity(identifier=identifier, full_name=name, identity_type=kind, institutional_email=email)
                    db.add(identity)
                else:
                    identity.full_name, identity.identity_type, identity.institutional_email = name, kind, email
                voter = db.query(Voter).filter_by(student_id=identifier).first()
                if voter is not None:
                    voter.full_name = name
                    voter.identity_type = kind
                count += 1
        db.commit()
        print(f"Imported/updated {count} official identity records.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python import_identity_roster.py gzu_identity_roster.csv")
    main(sys.argv[1])
