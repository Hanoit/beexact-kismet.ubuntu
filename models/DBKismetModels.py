from sqlalchemy import Column, String, Boolean, Text, ForeignKey, Index, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class MACVendorTable(Base):
    __tablename__ = 'mac_vendors'
    id = Column(String(8), primary_key=True)
    vendor_name = Column(String(100))
    last_consulted = Column(DateTime, default=datetime.utcnow)
    is_rate_limited = Column(Boolean, default=False)


class MACProviderTable(Base):
    __tablename__ = 'mac_providers'
    id = Column(String(10), primary_key=True)
    mac_sub_prefix = Column(String(8), nullable=False)  # Remove index here
    base_provider_id = Column(UUID(as_uuid=True), ForeignKey('mac_base_providers.id'))
    base_provider = relationship("MACBaseProviderTable", back_populates="providers")

    __table_args__ = (
        Index('idx_mac_sub_prefix', 'mac_sub_prefix'),
    )


class MACBaseProviderTable(Base):
    __tablename__ = 'mac_base_providers'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_name = Column(String(100))
    alias = Column(Text, nullable=False, default='[]')
    # Establish a back reference from MACBaseProviderTable to MACProviderTable
    providers = relationship("MACProviderTable", back_populates="base_provider")


class SSIDForbiddenTable(Base):
    __tablename__ = 'ssid_forbidden'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ssid_name = Column(String(100))


class ProcessedFileTable(Base):
    __tablename__ = 'processed_files'
    id = Column(String, primary_key=True)
    filename = Column(String, unique=True)
    status = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)


def get_base():
    return Base
