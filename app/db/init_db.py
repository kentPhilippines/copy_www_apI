from app.db.base import Base, engine
from app.models.download import DownloadTask

def init_db():
    """初始化数据库"""
    # 创建所有表
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db() 