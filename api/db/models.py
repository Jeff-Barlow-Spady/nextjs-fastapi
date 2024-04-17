from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from db import engine


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True,)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    location = Column(Geography("POINT"), nullable=False)
    alerts = relationship("Alert", back_populates="user")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    alert_name = Column(String, nullable=False)
    threshold = Column(Integer, nullable=False)
    alert_method = Column(String, nullable=True)
    mobile_number = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    location = Column(Geography("POINT"), nullable=False)
    user = relationship("User", back_populates="alerts")


