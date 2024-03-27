from app.database.sqlite import database
from sqlalchemy import Boolean, Column, DateTime, Integer, String


class TokenDto(database.Model):
    __tablename__ = "tokens"
    id = Column("id", Integer, primary_key=True)
    created_by = Column(String(36))
    user_id = Column(String(36))
    session_id = Column(String(36), unique=True)
    created_on = Column(DateTime(timezone=True))
    id_token = Column(Boolean, default=False)
    expires_on = Column(DateTime(timezone=True))
    has_expiration = Column(Boolean, default=True)
    hash = Column(String(100))
    note = Column(String(100))
