import sqlalchemy
from contextlib import contextmanager
import os, dotenv

dotenv.load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///test.db')
engine = sqlalchemy.create_engine(DATABASE_URL)
metadata = sqlalchemy.MetaData()

@contextmanager
def get_db():
    connection = engine.connect()
    try:
        yield connection
    finally:
        connection.close()