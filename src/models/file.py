from pydantic import BaseModel
from typing import Optional, Type
from sqlalchemy import DateTime, ForeignKey, Table, Column, String, MetaData, select
import sqlalchemy
from sqlalchemy.dialects.postgresql import ARRAY
import uuid
from datetime import datetime

from ..database import get_db

def File(baseModel: Type[BaseModel], metadata: MetaData):
    class File(baseModel):
        __tablename__ = 'file'
        id: Optional[str] = None
        name: str = ""
        owner_id: str = ""
        members: Optional[list[str]] = []
        date_uploaded: Optional[datetime] = None
        data: Optional[bytes] = None
        
        class Config:
            orm_mode = True
            
        @classmethod
        def get_all_by_owner(cls: Type['File'], owner_id: str) -> list['File']:
            with get_db() as db:
                rows = db.execute(select(file_table).where(file_table.c.owner_id == owner_id)).fetchall()
                if rows:
                    return [cls(id=row.id, name=row.name, comments=row.comments or [], owner_id=row.owner_id, date_uploaded=row.date_uploaded, data=row.data) for row in rows]
                return []
            
        @classmethod
        def get(cls, id: str, user_id: Optional[str] = None) -> Optional['File']:
            with get_db() as db:
                row = db.execute(select(file_table).where(file_table.c.id == id)).fetchone()
                if row:
                    if user_id and row.owner_id != user_id:
                        raise UnauthorizedFileAccess(id, user_id)
                    return cls(id=row.id, name=row.name, comments=row.comments or [], owner_id=row.owner_id, date_uploaded=row.date_uploaded, data=row.data)
                return None

        @classmethod
        def add_comment_(cls: Type['File'], file_id: str, comment: str, user_id: str) -> 'FileComment':
            file = cls.get(file_id, user_id)
            if not file:
                raise FileNotFound(file_id)
            comment = FileComment(file_id=file_id, comment=comment, user_id=user_id)
            comment.save()
            return comment

        def add_comment(self, comment: str, user_id: str) -> 'FileComment':
            return self.add_comment_(self.id, comment, user_id)

        @classmethod
        def all(cls) -> list['File']:
            with get_db() as db:
                rows = db.execute(select(file_table)).fetchall()
                if rows:
                    return [cls(id=row.id, name=row.name, comments=row.comments or [], owner_id=row.owner_id, date_uploaded=row.date_uploaded, data=row.data) for row in rows]
                return []

    class FileComment(baseModel):
        __tablename__ = 'file_comment'
        id: Optional[str] = None
        file_id: str
        comment: str
        user_id: str

        class Config:
            orm_mode = True
            
        @classmethod
        def get_all_by_file(cls: Type['FileComment'], file_id: str) -> list['FileComment']:
            with get_db() as db:
                rows = db.execute(select(file_comment_table).where(file_comment_table.c.file_id == file_id)).fetchall()
                if rows:
                    return [cls(id=row.id, file_id=row.file_id, comment=row.comment, user_id=row.user_id) for row in rows]
                return []

    file_table = Table(
        'file',
        metadata,
        Column('id', String, primary_key=True, default=lambda: str(uuid.uuid4())),
        Column('name', String, nullable=False),
        Column('comments', ARRAY(String), nullable=True),
        Column('owner_id', String, ForeignKey("'user'.id"), nullable=False),
        Column('date_uploaded', DateTime, default=datetime.utcnow),
        Column('data', sqlalchemy.LargeBinary),  # Storing file data as binary
    )
    
    file_comment_table = Table(
        'file_comment',
        metadata,
        Column('id', String, primary_key=True, default=lambda: str(uuid.uuid4())),
        Column('file_id', String, ForeignKey('file.id', ondelete='CASCADE'), nullable=False),
        Column('comment', String, nullable=False),
        Column('user_id', String, ForeignKey("'user'.id", ondelete='SET NULL'), nullable=False),
    )

    return File, FileComment, file_table, file_comment_table

class UnauthorizedFileAccess(Exception):
    def __init__(self, file_id, user_id):
        self.file_id = file_id
        self.user_id = user_id
        self.message = f"User {user_id} is not authorized to access file {file_id}"
        super().__init__(self.message)
        
class FileNotFound(Exception):
    def __init__(self, file_id):
        self.file_id = file_id
        self.message = f"File {file_id} not found"
        super().__init__(self.message)
        
class FileCommentNotFound(Exception):
    def __init__(self, comment_id):
        self.comment_id = comment_id
        self.message = f"File comment {comment_id} not found"
        super().__init__(self.message)