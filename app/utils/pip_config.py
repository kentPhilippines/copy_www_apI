import os
from app.core.logger import setup_logger

logger = setup_logger(__name__)

PIP_MIRRORS = [
    "https://mirrors.aliyun.com/pypi/simple/",
    "https://pypi.tuna.tsinghua.edu.cn/simple",
    "https://mirrors.cloud.tencent.com/pypi/simple",
    "https://mirrors.huaweicloud.com/repository/pypi/simple",
    "https://pypi.org/simple"  # 官方源作为备选
]

async def configure_pip():
    """配置pip源"""
    try:
        # 创建pip配置目录
        pip_config_dir = os.path.expanduser("~/.pip")
        os.makedirs(pip_config_dir, exist_ok=True)
        
        # 生成配置文件内容
        config_content = """[global]
timeout = 60
index-url = https://mirrors.aliyun.com/pypi/simple/
extra-index-url = 
    https://pypi.tuna.tsinghua.edu.cn/simple
    https://mirrors.cloud.tencent.com/pypi/simple
    https://mirrors.huaweicloud.com/repository/pypi/simple

[install]
trusted-host =
    mirrors.aliyun.com
    pypi.tuna.tsinghua.edu.cn
    mirrors.cloud.tencent.com
    mirrors.huaweicloud.com
"""
        
        # 写入配置文件
        config_path = os.path.join(pip_config_dir, "pip.conf")
        with open(config_path, "w") as f:
            f.write(config_content)
            
        logger.info("pip源配置完成")
        return True
    except Exception as e:
        logger.error(f"配置pip源失败: {str(e)}")
        return False 