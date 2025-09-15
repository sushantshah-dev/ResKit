from pydantic import BaseModel as PydanticBaseModel
from ..database import get_db, sqlalchemy, metadata, engine

from .user import User as UserModel

class BaseModel(PydanticBaseModel):
    class Config:
        orm_mode = True
        
    def to_dict(self):
        return self.model_dump()
    
    def save(self):
        table = self.__class__.__name__.lower()
        data = self.model_dump(exclude_unset=True)
        with get_db() as db:
            if hasattr(self, 'id') and self.id is not None:
                if db.execute(sqlalchemy.text(f"SELECT 1 FROM {table} WHERE id = :id"), {"id": self.id}).fetchone():
                    stmt = sqlalchemy.text(f"UPDATE {table} SET " + ", ".join([f"{key} = :{key}" for key in data.keys() if key != 'id']) + " WHERE id = :id")
                    db.execute(stmt, data)
                    db.commit()
                    return self
            stmt = sqlalchemy.text(f"INSERT INTO {table} (" + ", ".join(data.keys()) + ") VALUES (" + ", ".join([f":{key}" for key in data.keys()]) + ")")
            result = db.execute(stmt, data)
            self.id = result.lastrowid
            db.commit()
        return self
    
    def delete(self):
        if not hasattr(self, 'id') or self.id is None:
            raise ValueError("Instance does not have an id.")
        table = self.__class__.__name__.lower()
        with get_db() as db:
            db.execute(sqlalchemy.text(f"DELETE FROM {table} WHERE id = :id"), {"id": self.id})
            db.commit()
    
User, user_table = UserModel(BaseModel, metadata)

metadata.create_all(engine)