from pydantic import BaseModel
from typing import Optional, Type, List
from sqlalchemy import Table, Column, String, Text, Boolean, DateTime, ForeignKey, MetaData
import sqlalchemy
import uuid
from datetime import datetime

from ..database import get_db

def Chat(baseModel: Type[BaseModel], metadata: MetaData):
    class Chat(baseModel):
        id: Optional[str] = None
        project_id: Optional[str] = None
        created_at: datetime = datetime.utcnow()
        members: Optional[List[str]] = []

        class Config:
            orm_mode = True

        @classmethod
        def get(cls: Type['Chat'], id: str):
            table = 'chat'
            with get_db() as db:
                row = db.execute(sqlalchemy.text(f"SELECT * FROM {table} WHERE id = :id"), {"id": id}).fetchone()
                if row:
                    return cls(id=row[0], project_id=row[1], created_at=row[2], members=row[3] or [])
                return None

        @classmethod
        def all(cls: Type['Chat']):
            table = 'chat'
            with get_db() as db:
                rows = db.execute(sqlalchemy.text(f"SELECT * FROM {table}")).fetchall()
                if rows:
                    return [cls(id=row[0], project_id=row[1], created_at=row[2], members=row[3] or []) for row in rows]
                return []

        @classmethod
        def by_project(cls: Type['Chat'], project_id: str):
            table = 'chat'
            with get_db() as db:
                rows = db.execute(sqlalchemy.text(f"SELECT * FROM {table} WHERE project_id = :project_id"), {"project_id": project_id}).fetchall()
                if rows:
                    return [cls(id=row[0], project_id=row[1], created_at=row[2], members=row[3] or []) for row in rows]
                return []

    class Message(baseModel):
        id: Optional[str] = None
        chat_id: str
        user_id: str
        content: str
        timestamp: datetime = datetime.utcnow()

        class Config:
            orm_mode = True

        @classmethod
        def get(cls: Type['Message'], id: str):
            table = 'message'
            with get_db() as db:
                row = db.execute(sqlalchemy.text(f"SELECT * FROM {table} WHERE id = :id"), {"id": id}).fetchone()
                if row:
                    return cls(id=row[0], chat_id=row[1], user_id=row[2], content=row[3], timestamp=row[4])
                return None
            
        @classmethod
        def get_all_by_chat(cls: Type['Message'], chat_id: str):
            table = 'message'
            with get_db() as db:
                rows = sorted(db.execute(sqlalchemy.text(f"SELECT * FROM {table} WHERE chat_id = :chat_id"), {"chat_id": chat_id}).fetchall(), key=lambda x: x[4])
                if rows:
                    return [cls(id=row[0], chat_id=row[1], user_id=row[2], content=row[3], timestamp=row[4]) for row in rows]
                return []

        @classmethod
        def all(cls: Type['Message']):
            table = 'message'
            with get_db() as db:
                rows = db.execute(sqlalchemy.text(f"SELECT * FROM {table}")).fetchall()
                if rows:
                    return [cls(id=row[0], chat_id=row[1], user_id=row[2], content=row[3], timestamp=row[4]) for row in rows]
                return []
            
        @classmethod
        def delete_(cls: Type['Message'], id: str, user_id: str):
            message = cls.get(id)
            if not message:
                return
            if message.user_id != user_id:
                raise UnauthorisedMessageError(user_id, message.chat_id)
            table = 'message'
            with get_db() as db:
                db.execute(sqlalchemy.text(f"DELETE FROM {table} WHERE id = :id"), {"id": id})
                db.commit()
                
        def delete(self, user_id: str):
            return self.delete_(self.id, user_id)



    chat_table = Table(
        'chat',
        metadata,
        Column('id', String, primary_key=True, default=lambda: str(uuid.uuid4())),
        Column('project_id', String, ForeignKey('project.id'), nullable=True),
        Column('created_at', DateTime, default=datetime.utcnow),
        Column('members', String, nullable=True),
    )

    message_table = Table(
        'message',
        metadata,
        Column('id', String, primary_key=True, default=lambda: str(uuid.uuid4())),
        Column('chat_id', String, ForeignKey('chat.id'), nullable=False),
        Column('user_id', String, ForeignKey('user.id'), nullable=False),
        Column('content', Text, nullable=False),
        Column('timestamp', DateTime, default=datetime.utcnow),
        Column('is_bot', Boolean, default=False),
    )

    return Chat, Message, chat_table, message_table

class UnauthorisedMessageError(Exception):
    def __init__(self, user_id: str = None, chat_id: str = None):
        self.user_id = user_id
        self.chat_id = chat_id
        self.message =  f"User {user_id} is not authorized to access chat {chat_id}"
        super().__init__(self.message)