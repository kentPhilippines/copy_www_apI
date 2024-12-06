from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from app.db.base import Base
from datetime import datetime

class DownloadTask(Base):
    __tablename__ = "download_tasks"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(255), index=True)
    source_url = Column(String(1024))
    target_path = Column(String(1024))
    status = Column(String(50), default="pending")  # pending, downloading, completed, failed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    error = Column(Text, nullable=True)
    file_size = Column(Integer, default=0)
    bytes_downloaded = Column(Integer, default=0)
    progress = Column(Integer, default=0)
    is_directory = Column(Boolean, default=False)
    content_type = Column(String(255), nullable=True)
    depth = Column(Integer, default=0)
    retries = Column(Integer, default=0)
    priority = Column(Integer, default=0)
    checksum = Column(String(255), nullable=True)