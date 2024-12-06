import asyncio
import aiohttp
import os
from typing import List, Set
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.download import DownloadTask
from app.core.logger import setup_logger
from app.utils.shell import run_command

logger = setup_logger(__name__)

class DownloadManager:
    def __init__(self, db: Session, max_concurrent: int = 5, max_retries: int = 3):
        self.db = db
        self.max_concurrent = max_concurrent
        self.max_retries = max_retries
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.session = None
        self.downloaded_urls: Set[str] = set()
        self.progress_callbacks = {}
        self.retry_delays = [5, 15, 30]  # 重试延迟时间（秒）
        self.loop = asyncio.get_event_loop()

    async def start(self):
        """启动下载管理器"""
        self.session = aiohttp.ClientSession()
        self.loop = asyncio.get_event_loop()

    async def stop(self):
        """停止下载管理器"""
        if self.session:
            await self.session.close()

    async def add_task(self, domain: str, url: str, target_path: str, depth: int = 0) -> DownloadTask:
        """添加下载任务"""
        try:
            task = DownloadTask(
                domain=domain,
                source_url=url,
                target_path=target_path,
                status="pending",
                depth=depth
            )
            self.db.add(task)
            self.db.commit()
            self.db.refresh(task)
            
            # 使用 ensure_future 替代 create_task
            asyncio.ensure_future(self.process_task(task), loop=self.loop)
            return task
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"添加下载任务失败: {str(e)}")
            raise

    async def process_task(self, task: DownloadTask):
        """处理下载任务"""
        retries = 0
        while retries <= self.max_retries:
            async with self.semaphore:
                try:
                    # 更新状态
                    task.status = "downloading"
                    task.retries = retries
                    self.db.commit()

                    # 检查是否是目录
                    if task.source_url.endswith('/'):
                        await self._handle_directory(task)
                        return

                    # 下载文���
                    async with self.session.get(task.source_url, verify_ssl=False, timeout=30) as response:
                        if response.status != 200:
                            raise Exception(f"下载失败: HTTP {response.status}")

                        # 获取文件信息
                        task.content_type = response.headers.get('content-type')
                        total_size = int(response.headers.get('content-length', 0))
                        task.file_size = total_size

                        # 准备保存路径
                        try:
                            # 确保目标目录存在
                            target_dir = os.path.dirname(task.target_path)
                            if os.path.exists(target_dir) and not os.path.isdir(target_dir):
                                # 如果存在同名文件，将其重命名
                                os.rename(target_dir, f"{target_dir}.file")
                            os.makedirs(target_dir, exist_ok=True)

                            # 如果目标路径是目录，在路径后添加文件名
                            if os.path.isdir(task.target_path):
                                filename = os.path.basename(task.source_url)
                                if not filename:
                                    filename = 'index.html'
                                task.target_path = os.path.join(task.target_path, filename)

                            # 保存文件，同时更新进度
                            downloaded_size = 0
                            with open(task.target_path, 'wb') as f:
                                async for chunk in response.content.iter_chunked(8192):
                                    f.write(chunk)
                                    downloaded_size += len(chunk)
                                    await self._update_progress(task, downloaded_size, total_size)

                            # 设置权限
                            await run_command(f"chown nginx:nginx {task.target_path}")

                            # 更新状态
                            task.status = "completed"
                            task.updated_at = datetime.utcnow()
                            task.progress = 100
                            self.downloaded_urls.add(task.source_url)
                            return

                        except IsADirectoryError:
                            # 如果目标路径是目录，在路径中添加文件名
                            filename = os.path.basename(task.source_url)
                            if not filename:
                                filename = 'index.html'
                            task.target_path = os.path.join(task.target_path, filename)
                            # 重试当前下载
                            continue

                except asyncio.TimeoutError:
                    logger.warning(f"下载超时 {task.source_url} (重试 {retries + 1}/{self.max_retries})")
                    if retries < self.max_retries:
                        await asyncio.sleep(self.retry_delays[retries])
                        retries += 1
                        continue
                    raise

                except Exception as e:
                    if retries < self.max_retries:
                        logger.warning(f"下载失败 {task.source_url}: {str(e)} (重试 {retries + 1}/{self.max_retries})")
                        await asyncio.sleep(self.retry_delays[retries])
                        retries += 1
                        continue
                    task.status = "failed"
                    task.error = str(e)
                    logger.error(f"下载失败 {task.source_url}: {str(e)}")
                    break

                finally:
                    self.db.commit()

    async def _update_progress(self, task: DownloadTask, downloaded: int, total: int):
        """更新下载进度"""
        if total > 0:
            progress = int((downloaded / total) * 100)
            if progress != task.progress:
                task.progress = progress
                task.bytes_downloaded = downloaded
                self.db.commit()
                
                # 调用进度回调
                if task.domain in self.progress_callbacks:
                    try:
                        await self.progress_callbacks[task.domain](task)
                    except Exception as e:
                        logger.error(f"进度回调错误: {str(e)}")

    def register_progress_callback(self, domain: str, callback):
        """注册进度回调函数"""
        self.progress_callbacks[domain] = callback

    def unregister_progress_callback(self, domain: str):
        """注销进度回调函数"""
        if domain in self.progress_callbacks:
            del self.progress_callbacks[domain]

    async def retry_failed_tasks(self, domain: str):
        """重试失败的任务"""
        failed_tasks = self.get_failed_tasks(domain)
        for task in failed_tasks:
            task.status = "pending"
            task.error = None
            task.retries = 0
            self.db.commit()
            # 使用 ensure_future
            asyncio.ensure_future(self.process_task(task), loop=self.loop)

    async def cancel_tasks(self, domain: str):
        """取消指定域名的所有任务"""
        tasks = self.db.query(DownloadTask).filter(
            DownloadTask.domain == domain,
            DownloadTask.status.in_(["pending", "downloading"])
        ).all()
        
        for task in tasks:
            task.status = "cancelled"
            task.error = "用户取消"
        self.db.commit()

    def get_task_progress(self, domain: str) -> dict:
        """获取下载进度详情"""
        stats = self.get_task_stats(domain)
        tasks = self.db.query(DownloadTask).filter(
            DownloadTask.domain == domain,
            DownloadTask.status == "downloading"
        ).all()
        
        current_tasks = []
        for task in tasks:
            current_tasks.append({
                "url": task.source_url,
                "progress": task.progress,
                "size": task.file_size,
                "downloaded": task.bytes_downloaded,
                "retries": task.retries
            })
        
        return {
            "stats": stats,
            "current_tasks": current_tasks,
            "overall_progress": self._calculate_overall_progress(domain)
        }

    def _calculate_overall_progress(self, domain: str) -> int:
        """计算总体进度"""
        tasks = self.db.query(DownloadTask).filter(
            DownloadTask.domain == domain
        ).all()
        
        if not tasks:
            return 0
            
        total_progress = 0
        for task in tasks:
            if task.status == "completed":
                total_progress += 100
            elif task.status == "downloading":
                total_progress += task.progress or 0
                
        return int(total_progress / len(tasks))

    async def _handle_directory(self, task: DownloadTask):
        """处理目录任务"""
        try:
            task.is_directory = True
            # 如果目标路径已存在且是文件，将其重命名
            if os.path.exists(task.target_path) and not os.path.isdir(task.target_path):
                os.rename(task.target_path, f"{task.target_path}.file")
            os.makedirs(task.target_path, exist_ok=True)
            await run_command(f"chown nginx:nginx {task.target_path}")
            task.status = "completed"
            self.downloaded_urls.add(task.source_url)
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
        finally:
            self.db.commit()

    def get_pending_tasks(self, domain: str) -> List[DownloadTask]:
        """获取待处理的任务"""
        return self.db.query(DownloadTask).filter(
            DownloadTask.domain == domain,
            DownloadTask.status == "pending"
        ).all()

    def get_failed_tasks(self, domain: str) -> List[DownloadTask]:
        """获取失败的任务"""
        return self.db.query(DownloadTask).filter(
            DownloadTask.domain == domain,
            DownloadTask.status == "failed"
        ).all()

    def get_task_stats(self, domain: str) -> dict:
        """获取任务统计信息"""
        stats = {
            "total": 0,
            "pending": 0,
            "downloading": 0,
            "completed": 0,
            "failed": 0,
            "total_size": 0
        }
        
        tasks = self.db.query(DownloadTask).filter(
            DownloadTask.domain == domain
        ).all()
        
        for task in tasks:
            stats["total"] += 1
            stats[task.status] += 1
            if task.file_size:
                stats["total_size"] += task.file_size
                
        return stats 