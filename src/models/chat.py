
from email import message
from pydantic import BaseModel
from typing import Optional, Type, List
from sqlalchemy import CheckConstraint, Constraint, Table, Column, String, Text, DateTime, ForeignKey, MetaData, select
from sqlalchemy.dialects.postgresql import ARRAY
import uuid
from datetime import datetime

from ..database import get_db

def Chat(baseModel: Type[BaseModel], metadata: MetaData):
    class Chat(baseModel):
        __tablename__ = 'chat'
        id: Optional[str] = None
        project_id: Optional[str] = None
        created_at: datetime = datetime.utcnow()
        members: Optional[List[str]] = []

        class Config:
            orm_mode = True

        @classmethod
        def get(cls: Type['Chat'], id: str) -> Optional['Chat']:
            with get_db() as db:
                row = db.execute(select(chat_table).where(chat_table.c.id == id)).fetchone()
                if row:
                    return cls(id=row.id, project_id=row.project_id, created_at=row.created_at, members=row.members or [])
                return None

        @classmethod
        def all(cls: Type['Chat']) -> list['Chat']:
            with get_db() as db:
                rows = db.execute(select(chat_table)).fetchall()
                if rows:
                    return [cls(id=row.id, project_id=row.project_id, created_at=row.created_at, members=row.members or []) for row in rows]
                return []

        @classmethod
        def by_project(cls: Type['Chat'], project_id: str) -> list['Chat']:
            with get_db() as db:
                rows = db.execute(select(chat_table).where(chat_table.c.project_id == project_id)).fetchall()
                if rows:
                    print(rows)
                    return [cls(id=row.id, project_id=row.project_id, created_at=row.created_at, members=row.members or []) for row in rows]
                return []
            
        @classmethod
        def add_message_(cls: Type['Chat'], chat_id: str, user_id: str, content: str, attachments: Optional[List[str]] = []) -> 'Message':
            chat = cls.get(chat_id)
            if not chat:
                raise UnauthorisedMessage(user_id, chat_id)
            print(chat.members, user_id)
            if chat.members and user_id not in chat.members + ['system']:
                raise UnauthorisedMessage(user_id, chat_id)
            message = Message(chat_id=chat_id, user_id=user_id, content=content, attachments=attachments)
            message.save()
            return message
        
        def add_message(self, user_id: str, content: str, attachments: Optional[List[str]] = []) -> 'Message':
            return self.add_message_(self.id, user_id, content, attachments)

    class Message(baseModel):
        __tablename__ = 'message'
        id: Optional[str] = None
        chat_id: str
        user_id: str
        content: str
        attachments: Optional[List[str]] = []
        timestamp: datetime = datetime.utcnow()
        tool_calls: Optional[str] = ""

        class Config:
            orm_mode = True

        @classmethod
        def get(cls: Type['Message'], id: str) -> Optional['Message']:
            with get_db() as db:
                row = db.execute(select(message_table).where(message_table.c.id == id)).fetchone()
                if row:
                    row = row
                    return cls(id=row.id, chat_id=row.chat_id, user_id=row.user_id, content=row.content, attachments=row.attachments or [], timestamp=row.timestamp, tool_calls=row.tool_calls)
                return None

        @classmethod
        def get_all_by_chat(cls: Type['Message'], chat_id: str) -> list['Message']:
            with get_db() as db:
                rows = db.execute(select(message_table).where(message_table.c.chat_id == chat_id)).fetchall()
                if rows:
                    # Sort by timestamp
                    rows = sorted(rows, key=lambda x: x.timestamp)
                    return [cls(id=row.id, chat_id=row.chat_id, user_id=row.user_id, content=row.content, attachments=row.attachments or [], timestamp=row.timestamp, tool_calls=row.tool_calls) for row in rows]
                return []

        @classmethod
        def all(cls: Type['Message']) -> list['Message']:
            with get_db() as db:
                rows = db.execute(select(message_table)).fetchall()
                if rows:
                    return [cls(id=row.id, chat_id=row.chat_id, user_id=row.user_id, content=row.content, attachments=row.attachments or [], timestamp=row.timestamp, tool_calls=row.tool_calls) for row in rows]
                return []
            
        def delete(self, user_id: str):
            if self.user_id != user_id:
                raise UnauthorizedMessageDeletion(user_id, self.id)
            super().delete()



    chat_table = Table(
        'chat',
        metadata,
        Column('id', String, primary_key=True, default=lambda: str(uuid.uuid4())),
        Column('project_id', String, ForeignKey('project.id'), nullable=True),
        Column('created_at', DateTime, default=datetime.utcnow),
        Column('members', ARRAY(String), nullable=True)
    )

    message_table = Table(
        'message',
        metadata,
        Column('id', String, primary_key=True, default=lambda: str(uuid.uuid4())),
        Column('chat_id', String, ForeignKey('chat.id'), nullable=False),
        Column('user_id', String, ForeignKey("'user'.id"), nullable=False),
        Column('content', Text, nullable=False),
        Column('attachments', ARRAY(String), nullable=True),
        Column('timestamp', DateTime, default=datetime.utcnow),
        Column('tool_calls', String, nullable=True),
        CheckConstraint("tool_calls IS NULL OR user_id = 'system'", name='tool_calls_user_check')
    )

    return Chat, Message, chat_table, message_table

class UnauthorisedMessage(Exception):
    def __init__(self, user_id: str = None, chat_id: str = None):
        self.user_id = user_id
        self.chat_id = chat_id
        self.message =  f"User {user_id} is not authorized to access chat {chat_id}"
        super().__init__(self.message)

class UnauthorizedMessageDeletion(Exception):
    def __init__(self, user_id: str = None, message_id: str = None):
        self.user_id = user_id
        self.message_id = message_id
        self.message =  f"User {user_id} is not authorized to delete message {message_id}"
        super().__init__(self.message)
        
class ChatNotFound(Exception):
    def __init__(self, chat_id: str = None):
        self.chat_id = chat_id
        self.message =  f"Chat {chat_id} not found"
        super().__init__(self.message)
        
class MessageNotFound(Exception):
    def __init__(self, message_id: str = None):
        self.message_id = message_id
        self.message =  f"Message {message_id} not found"
        super().__init__(self.message)