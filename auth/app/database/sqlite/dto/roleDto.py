from app.database.sqlite import database
from sqlalchemy import Column, Integer, String


class RoleDto(database.Model):
    __tablename__ = "roles"
    id = Column("id", Integer, primary_key=True)
    code = Column(String(50), unique=True)
    name = Column(String(50), unique=True)
    description = Column(String(500))
