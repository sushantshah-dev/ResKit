from pydantic import BaseModel
from typing import Optional, Type
from sqlalchemy import DateTime, ForeignKey, Table, Column, String, MetaData
import sqlalchemy
import uuid
from datetime import datetime

from ..database import get_db

def File(baseModel: Type[BaseModel], metadata: MetaData):
    class File(baseModel):
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
            table = 'file'
            with get_db() as db:
                rows = db.execute(sqlalchemy.text(f"SELECT * FROM {table} WHERE owner_id = :owner_id"), {"owner_id": owner_id}).fetchall()
                if rows:
                    return [cls(id=row[0], name=row[1], comments=row[2] or [], owner_id=row[3], date_uploaded=row[4], data=row[5]) for row in rows]
                return []
            
        @classmethod
        def get(cls, id: str, user_id: Optional[str] = None) -> Optional['File']:
            table = 'file'
            with get_db() as db:
                row = db.execute(sqlalchemy.text(f"SELECT * FROM {table} WHERE id = :id"), {"id": id}).fetchone()
                if row:
                    if user_id and row[3] != user_id:
                        raise UnauthorizedFileAccess(id, user_id)
                    return cls(id=row[0], name=row[1], comments=row[2] or [], owner_id=row[3], date_uploaded=row[4], data=row[5])  # Updated
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
            table = cls.__name__.lower()
            with get_db() as db:
                rows = db.execute(sqlalchemy.text(f"SELECT * FROM {table}")).fetchall()
                if rows:
                    return [cls(id=row[0], name=row[1], comments=row[2] or [], owner_id=row[3], date_uploaded=row[4], data=row[5]) for row in rows]
                return []

    class FileComment(baseModel):
        id: Optional[str] = None
        file_id: str
        comment: str
        user_id: str

        class Config:
            orm_mode = True
            
        @classmethod
        def get_all_by_file(cls: Type['FileComment'], file_id: str) -> list['FileComment']:
            table = 'file_comment'
            with get_db() as db:
                rows = db.execute(sqlalchemy.text(f"SELECT * FROM {table} WHERE file_id = :file_id"), {"file_id": file_id}).fetchall()
                if rows:
                    return [cls(id=row[0], file_id=row[1], comment=row[2], user_id=row[3]) for row in rows]
                return []

    file_table = Table(
        'file',
        metadata,
        Column('id', String, primary_key=True, autoincrement=True, default=lambda: str(uuid.uuid4())),
        Column('name', String, nullable=False),
        Column('comments', String),  # Storing JSON as string
        Column('owner_id', String, ForeignKey('user.id'), nullable=False),
        Column('date_uploaded', DateTime, default=datetime.utcnow),
        Column('data', sqlalchemy.LargeBinary),  # Storing file data as binary
    )
    
    file_comment_table = Table(
        'file_comment',
        metadata,
        Column('id', String, primary_key=True, default=lambda: str(uuid.uuid4())),
        Column('file_id', String, ForeignKey('file.id', ondelete='CASCADE'), nullable=False),
        Column('comment', String, nullable=False),
        Column('user_id', String, ForeignKey('user.id', ondelete='SET NULL'), nullable=False),
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