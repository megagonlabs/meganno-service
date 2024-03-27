from app.database.sqlite import database
from sqlalchemy import Boolean, Column, DateTime, Integer, String


class InvitationDto(database.Model):
    __tablename__ = "invitations"
    id = Column("id", Integer, primary_key=True)
    code = Column(String(10), unique=True)
    invitation_code = Column(String(50), unique=True)
    single_use = Column(Boolean, default=True)
    created_on = Column(DateTime(timezone=True))
    expires_on = Column(DateTime(timezone=True))
    note = Column(String(100))
    role_id = Column(Integer)
