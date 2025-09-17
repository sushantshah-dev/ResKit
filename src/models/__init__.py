from pydantic import BaseModel as PydanticBaseModel
from ..database import get_db, sqlalchemy, metadata, engine

from sqlalchemy import delete, select, update, insert

from .user import User as UserModel
from .chat import Chat as ChatModel
from .file import File as FileModel
from .project import Project as ProjectModel

from .user import UserNotFound
from .chat import UnauthorizedChatAccess, UnauthorisedMessage, UnauthorizedMessageDeletion, ChatNotFound, MessageNotFound
from .file import UnauthorizedFileAccess, FileNotFound, FileCommentNotFound
from .project import UnauthorizedProjectAccess, UnauthorizedProjectModification, UnauthorizedProjectDeletion, ProjectNotFound

class BaseModel(PydanticBaseModel):
    class Config:
        orm_mode = True
        
    def to_dict(self):
        return self.model_dump()
    
    def save(self):
        table = metadata.tables.get(self.__tablename__)
        data = self.model_dump(exclude_unset=True)
        
        with get_db() as db:
            if hasattr(self, 'id') and self.id is not None and table is not None:
                result = db.execute(select(table).where(table.c.id == self.id)).first()
                if result:
                    db.execute(update(table).where(table.c.id == self.id).values(**{k: v for k, v in data.items() if k != 'id'}))
                    db.commit()
                    return self
            if table is not None:
                result = db.execute(insert(table).values(**data))
                try:
                    self.id = result.inserted_primary_key[0]
                except Exception:
                    self.id = getattr(result, 'lastrowid', None)
                db.commit()
        return self
    
    def delete(self):
        table = metadata.tables.get(self.__tablename__)
        
        if not hasattr(self, 'id') or self.id is None:
            raise ValueError("Instance does not have an id.")
        
        with get_db() as db:
            if table is not None:
                db.execute(delete(table).where(table.c.id == self.id))
                db.commit()
    
User, user_table = UserModel(BaseModel, metadata)
Chat, Message, chat_table, message_table = ChatModel(BaseModel, metadata)
File, FileComment, file_table, file_comment_table = FileModel(BaseModel, metadata)
Project, project_table = ProjectModel(BaseModel, metadata)

metadata.create_all(engine)

with get_db() as db:
    system_user = db.execute(select(user_table).where(user_table.c.id == 'system')).first()
    assistant_user = db.execute(select(user_table).where(user_table.c.id == 'assistant')).first()
    tool_user = db.execute(select(user_table).where(user_table.c.id == 'tool')).first()
    card_user = db.execute(select(user_table).where(user_table.c.id == 'card')).first()

    if not system_user:
        db.execute(insert(user_table).values(id='system', username='System', email='system@reskit.com', hashed_password='hashed_system_password'))
    if not assistant_user:
        db.execute(insert(user_table).values(id='assistant', username='Assistant', email='assistant@reskit.com', hashed_password='hashed_assistant_password'))
    if not tool_user:
        db.execute(insert(user_table).values(id='tool', username='Tool', email='tool@reskit.com', hashed_password='hashed_tool_password'))
    if not card_user:
        db.execute(insert(user_table).values(id='card', username='Card', email='card@reskit.com', hashed_password='hashed_card_password'))
    db.commit()