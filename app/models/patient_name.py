# app/models/patient_name.py - Local cache of HN/name from HosXP, synced nightly
from sqlalchemy import Column, String

from app.models.user import Base


class PatientName(Base):
    __tablename__ = "patient_names"

    hn = Column(String(7), primary_key=True)
    pname = Column(String(50))
    fname = Column(String(100))
    lname = Column(String(100))
