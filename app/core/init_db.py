import asyncio
from app.db.base import Base, engine
from app.models.download import DownloadTask
from app.core.logger import setup_logger
import os
from app.core.config import settings

logger = setup_logger(__name__)

async def initialize_database():
    """初始化数据库"""
    try:
        # 确保数据目录存在
        os.makedirs(os.path.dirname(settings.DATABASE_URL.replace('sqlite:///', '')), exist_ok=True)
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(initialize_database()) 