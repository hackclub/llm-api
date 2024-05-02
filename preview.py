from sqlmodel import create_engine, Session, select
from models import ChatRecord, ChatSession
from dotenv import load_dotenv
import os

load_dotenv()

PG_DATABASE_URL = os.environ["PG_DATABASE_URL"]

pg_engine = create_engine(PG_DATABASE_URL)

def main():
    with Session(pg_engine) as session:
        chat_records = session.exec(select(ChatRecord)).all()
        chat_sessions = session.exec(select(ChatSession)).all()

        for chat_session in chat_sessions:
            print(chat_session)
            chat_records = session.exec(select(ChatRecord).where(ChatRecord.session_id == chat_session.id).order_by(ChatRecord.timestamp)).all()
            for chat_record in chat_records:
                print(chat_record)
                print()
            print("------------")
            
main()