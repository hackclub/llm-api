from sqlmodel import create_engine, Session, select
from models import ChatRecord, ChatRecord
import os

PG_DATABASE_URL = os.environ["PG_DATABASE_URL"]
pg_engine = create_engine(PG_DATABASE_URL)

def main():
    with Session(pg_engine) as session:
        # select(ChatRecord).where(ChatRecord.session_id == )
        pass