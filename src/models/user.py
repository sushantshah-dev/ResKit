from pydantic import BaseModel, EmailStr
from typing import Optional, Type
from sqlalchemy import DateTime, Table, Column, String, Boolean, MetaData, select
import sqlalchemy
import uuid
from datetime import datetime

from ..database import get_db

def User(baseModel: Type[BaseModel], metadata: MetaData) -> tuple[Type[BaseModel], Table]:
    class User(baseModel):
        __tablename__ = "'user'"
        id: Optional[str] = None
        username: str = ""
        email: EmailStr = ""
        hashed_password: str = ""
        is_active: bool = True
        is_admin: bool = False
        created_at: datetime = datetime.utcnow()
        
        class Config:
            orm_mode = True
            
        @classmethod
        def get_by_email(cls: Type['User'], email: str) -> Optional['User']:
            with get_db() as db:
                row = db.execute(select(user_table).where(user_table.c.email == email)).fetchone()
                if row:
                    return cls(id=row.id, username=row.username, email=row.email, hashed_password=row.hashed_password, is_active=row.is_active or True, is_admin=row.is_admin or False, created_at=row.created_at or datetime.utcnow())
                return None
            
        @classmethod
        def get(cls: Type['User'], id: str) -> Optional['User']:
            with get_db() as db:
                row = db.execute(select(user_table).where(user_table.c.id == id)).fetchone()
                if row:
                    return cls(id=row.id, username=row.username, email=row.email, hashed_password=row.hashed_password, is_active=row.is_active or True, is_admin=row.is_admin or False, created_at=row.created_at or datetime.utcnow())
                return None
            
        @classmethod
        def all(cls: Type['User']) -> list['User']:
            with get_db() as db:
                rows = db.execute(select(user_table)).fetchall()
                if rows:
                    return [cls(id=row.id, username=row.username, email=row.email, hashed_password=row.hashed_password, is_active=row.is_active or True, is_admin=row.is_admin or False, created_at=row.created_at or datetime.utcnow()) for row in rows]
                return []
            
            
    
    user_table = Table(
        "'user'",
        metadata,
        Column('id', String, primary_key=True, default=str(uuid.uuid4())),
        Column('username', String, unique=True, nullable=False),
        Column('email', String, unique=True, nullable=False),
        Column('hashed_password', String, nullable=False),
        Column('is_active', Boolean, default=True),
        Column('is_admin', Boolean, default=False),
        Column('created_at', DateTime, default=datetime.utcnow),
    )

    return User, user_table