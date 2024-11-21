from app.core.database import init_db
from app.core.logger import setup_logger

logger = setup_logger(__name__)

def initialize_database():
    """初始化数据库"""
    try:
        init_db()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        raise

if __name__ == "__main__":
    initialize_database() 