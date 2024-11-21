import asyncio
from app.core.database import init_db
from app.core.logger import setup_logger

logger = setup_logger(__name__)

async def initialize_database():
    """异步初始化数据库"""
    try:
        # 在事件循环中执行同步的数据库初始化
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, init_db)
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(initialize_database()) 