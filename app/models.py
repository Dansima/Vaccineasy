"""
Vaccineasy v4.0 — Database Models (SQLAlchemy ORM)
Patient records, vaccine reference data, and vaccination history.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, Date, Text, ForeignKey,
    UniqueConstraint, create_engine
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Patient(Base):
    """A registered patient (child)."""
    __tablename__ = 'patients'

    id = Column(Integer, primary_key=True, autoincrement=True)
    cnp = Column(String(13), unique=True, nullable=False, index=True)
    nume = Column(String(200), nullable=False)
    telefon = Column(String(20), nullable=True)
    data_nasterii = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    vaccination_records = relationship("VaccinationRecord", back_populates="patient",
                                       cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Patient(id={self.id}, cnp='{self.cnp}', nume='{self.nume}')>"


class Vaccine(Base):
    """Reference table — vaccines in the national schedule."""
    __tablename__ = 'vaccines'

    id = Column(Integer, primary_key=True, autoincrement=True)
    cod = Column(String(20), unique=True, nullable=False)    # e.g. "Hexa_2"
    nume = Column(String(100), nullable=False)                # e.g. "Hexavalent (2 luni)"
    target_age_days = Column(Integer, nullable=False)         # e.g. 60
    description = Column(Text, nullable=True)

    # Relationships
    vaccination_records = relationship("VaccinationRecord", back_populates="vaccine")

    def __repr__(self):
        return f"<Vaccine(cod='{self.cod}', nume='{self.nume}')>"


class VaccinationRecord(Base):
    """Records when a vaccine was administered to a patient."""
    __tablename__ = 'vaccination_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    vaccine_id = Column(Integer, ForeignKey('vaccines.id'), nullable=False)
    date_administered = Column(Date, nullable=False)
    lot_number = Column(String(50), nullable=True)
    administered_by = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    patient = relationship("Patient", back_populates="vaccination_records")
    vaccine = relationship("Vaccine", back_populates="vaccination_records")

    # Prevent duplicate records for same patient + vaccine
    __table_args__ = (
        UniqueConstraint('patient_id', 'vaccine_id', name='uq_patient_vaccine'),
    )

    def __repr__(self):
        return f"<VaccinationRecord(patient={self.patient_id}, vaccine={self.vaccine_id}, date={self.date_administered})>"
