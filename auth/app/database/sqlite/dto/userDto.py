from app.database.sqlite import database
from sqlalchemy import Boolean, Column, Integer, String


class UserDto(database.Model):
    __tablename__ = "users"
    id = Column("id", Integer, primary_key=True)
    username = Column(String(50), unique=True)
    password = Column(String(100))
    enabled = Column(Boolean, default=True)
    user_id = Column(String(36), unique=True)
    role_id = Column(Integer)
    invitation_id = Column(Integer)
