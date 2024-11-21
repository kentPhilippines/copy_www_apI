from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# 创建数据库引擎
# SQLite不支持连接池配置
if settings.DATABASE_URL.startswith('sqlite'):
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},  # SQLite需要这个配置来支持多线程
        echo=settings.DEBUG
    )
else:
    # 其他数据库（如MySQL）的配置
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
        pool_timeout=30,
        echo=settings.DEBUG
    )

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """初始化数据库"""
    try:
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        logger.info("数据库初始化成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        raise 