from pydantic import BaseModel
from typing import Optional, Type
from sqlalchemy import Table, Column, String, Boolean, MetaData, select
from sqlalchemy.dialects.postgresql import ARRAY

import uuid

from ..database import get_db


def Project(baseModel: Type[BaseModel], metadata: MetaData) -> tuple[Type[BaseModel], Table]:
    class Project(baseModel):
        __tablename__ = 'project'
        id: Optional[str] = None
        name: str = ""
        chat_log: Optional[str] = None
        papers: Optional[str] = None
        graph: Optional[str] = None
        is_public: bool = False
        owner_id: str = ""
        members: Optional[list[str]] = None

        class Config:
            orm_mode = True

        @classmethod
        def get(cls: Type['Project'], id: str) -> Optional['Project']:
            with get_db() as db:
                row = db.execute(select(project_table).where(project_table.c.id == id)).fetchone()
                if row:
                    return cls(
                        id=row.id,
                        name=row.name,
                        chat_log=row.chat_log,
                        papers=row.papers,
                        graph=row.graph,
                        is_public=row.is_public or False,
                        owner_id=row.owner_id,
                        members=row.members
                    )
                return None

        @classmethod
        def all(cls: Type['Project']) -> list['Project']:
            with get_db() as db:
                rows = db.execute(select(project_table)).fetchall()
                if rows:
                    return [cls(id=row.id, name=row.name, chat_log=row.chat_log, papers=row.papers, graph=row.graph, is_public=row.is_public or False, owner_id=row.owner_id, members=row.members) for row in rows]
                return []



    project_table = Table(
        'project',
        metadata,
        Column('id', String, primary_key=True, default=str(uuid.uuid4())),
        Column('name', String, nullable=False),
        Column('chat_log', String, nullable=True),
        Column('papers', String, nullable=True),
        Column('graph', String, nullable=True),
        Column('is_public', Boolean, default=False),
        Column('owner_id', String, nullable=False),
        Column('members', ARRAY(String), nullable=True)
    )
    
    return Project, project_table

class ProjectNotFound(Exception):
    def __init__(self, project_id):
        self.project_id = project_id
        self.message = f"Project {project_id} not found"
        super().__init__(self.message)
        
class UnauthorizedProjectAccess(Exception):
    def __init__(self, user_id, project_id):
        self.user_id = user_id
        self.project_id = project_id
        self.message = f"User {user_id} is not authorized to access project {project_id}"
        super().__init__(self.message)
        
class UnauthorizedProjectModification(Exception):
    def __init__(self, user_id, project_id):
        self.user_id = user_id
        self.project_id = project_id
        self.message = f"User {user_id} is not authorized to modify project {project_id}"
        super().__init__(self.message)
        
class UnauthorizedProjectDeletion(Exception):
    def __init__(self, user_id, project_id):
        self.user_id = user_id
        self.project_id = project_id
        self.message = f"User {user_id} is not authorized to delete project {project_id}"
        super().__init__(self.message)