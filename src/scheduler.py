"""
定时任务调度器模块
支持定时自动生成笔记
"""
import logging
import random
from typing import List, Callable, Optional, Dict, Any
from datetime import datetime, timedelta

try:
    from apscheduler.schedulers.qt import QtScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False

logger = logging.getLogger(__name__)


class NoteScheduler:
    """笔记定时任务调度器"""

    def __init__(self,
                 note_generator,
                 file_manager,
                 git_manager,
                 on_job_complete: Optional[Callable] = None):
        """
        初始化调度器

        Args:
            note_generator: 笔记生成器实例
            file_manager: 文件管理器实例
            git_manager: Git管理器实例
            on_job_complete: 任务完成回调函数
        """
        self.note_generator = note_generator
        self.file_manager = file_manager
        self.git_manager = git_manager
        self.on_job_complete = on_job_complete

        self.enabled = False
        self.job_id = None
        self.topics = []
        self.config = {}

        # 执行统计
        self.stats = {
            "total_runs": 0,
            "success_count": 0,
            "failed_count": 0,
            "last_run": None,
            "next_run": None
        }

        # 执行历史
        self.history = []

        # 实时日志（最多保留100条）
        self.log_messages = []

        if not SCHEDULER_AVAILABLE:
            logger.warning(
                "APScheduler未安装，定时任务功能不可用。"
                "请运行: pip install APScheduler"
            )
            self.scheduler = None
            return

        try:
            self.scheduler = QtScheduler()
            logger.info("定时任务调度器初始化成功")
        except Exception as e:
            logger.error(f"调度器初始化失败: {e}")
            self.scheduler = None

    def setup_daily_job(self, time_str: str, batch_size: int,
                       topics: List[str]):
        """
        设置每天定时任务（实际上是24小时间隔）

        Args:
            time_str: 时间字符串，格式 "HH:MM"
            batch_size: 每次生成篇数
            topics: 主题列表
        """
        if not self.scheduler:
            logger.warning("调度器未初始化")
            return False

        try:
            # 解析时间
            hour, minute = map(int, time_str.split(':'))

            # 获取当前时间
            now = datetime.now()
            scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

            # 如果设置的时间已过，设置为明天同一时间
            if scheduled_time < now:
                from datetime import timedelta
                scheduled_time += timedelta(days=1)

            # 移除旧任务
            self._remove_job()

            # 添加新任务：第一次在scheduled_time执行，之后每隔24小时执行一次
            job = self.scheduler.add_job(
                self._execute_batch,
                trigger=IntervalTrigger(hours=24, start_date=scheduled_time),
                args=[batch_size, topics],
                id='daily_note_generation',
                name=f'间隔笔记生成(24小时,首次{time_str})',
                replace_existing=True
            )
            self.job_id = job.id

            self.config = {
                "mode": "daily",
                "time": time_str,
                "batch_size": batch_size
            }
            self.topics = topics
            self.enabled = True

            # 启动调度器
            if not self.scheduler.running:
                self.scheduler.start()

            # 获取下次执行时间
            next_run = self.scheduler.get_job(self.job_id).next_run_time
            self.stats["next_run"] = next_run.isoformat() if next_run else None

            # 显示友好的下次执行时间
            if scheduled_time.date() == now.date():
                time_desc = f"今天 {time_str}"
            else:
                time_desc = f"明天 {time_str}"

            self._log(f"定时任务已设置: 首次执行时间 - {time_desc}, 之后每24小时执行一次")

            logger.info(
                f"已设置间隔定时任务: 首次{time_str}执行, 之后每24小时, "
                f"每次生成 {batch_size} 篇"
            )
            return True

        except Exception as e:
            logger.error(f"设置间隔定时任务失败: {e}")
            return False

    def setup_interval_job(self, hours: int, batch_size: int,
                          topics: List[str]):
        """
        设置间隔定时任务

        Args:
            hours: 间隔小时数
            batch_size: 每次生成篇数
            topics: 主题列表
        """
        if not self.scheduler:
            logger.warning("调度器未初始化")
            return False

        try:
            # 创建触发器
            trigger = IntervalTrigger(hours=hours)

            # 移除旧任务
            self._remove_job()

            # 添加新任务
            job = self.scheduler.add_job(
                self._execute_batch,
                trigger=trigger,
                args=[batch_size, topics],
                id='interval_note_generation',
                name=f'间隔笔记生成({hours}小时)',
                replace_existing=True
            )
            self.job_id = job.id  # 获取job ID字符串

            self.config = {
                "mode": "interval",
                "hours": hours,
                "batch_size": batch_size
            }
            self.topics = topics
            self.enabled = True

            # 启动调度器
            if not self.scheduler.running:
                self.scheduler.start()

            # 获取下次执行时间
            next_run = self.scheduler.get_job(self.job_id).next_run_time
            self.stats["next_run"] = next_run.isoformat() if next_run else None

            logger.info(
                f"已设置间隔定时任务: 每 {hours} 小时, "
                f"每次生成 {batch_size} 篇"
            )
            return True

        except Exception as e:
            logger.error(f"设置间隔定时任务失败: {e}")
            return False

    def pause(self):
        """暂停定时任务"""
        if not self.scheduler:
            return

        try:
            if self.job_id:
                self.scheduler.pause_job(self.job_id)
                self.enabled = False
                logger.info("定时任务已暂停")
        except Exception as e:
            logger.error(f"暂停任务失败: {e}")

    def resume(self):
        """恢复定时任务"""
        if not self.scheduler:
            return

        try:
            if self.job_id:
                self.scheduler.resume_job(self.job_id)
                self.enabled = True
                logger.info("定时任务已恢复")
        except Exception as e:
            logger.error(f"恢复任务失败: {e}")

    def _remove_job(self):
        """移除现有任务"""
        if self.job_id and self.scheduler:
            try:
                self.scheduler.remove_job(self.job_id)
                logger.debug(f"已移除旧任务: {self.job_id}")
            except Exception:
                pass

    def _log(self, message: str):
        """输出日志（记录到logger和内存列表）"""
        logger.info(message)
        # 添加到日志列表，供GUI读取
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_messages.append(log_entry)
        # 限制日志数量（最多保留100条）
        if len(self.log_messages) > 100:
            self.log_messages = self.log_messages[-100:]

    def _execute_batch(self, batch_size: int, topics: List[str]):
        """
        执行批量生成任务

        Args:
            batch_size: 生成数量
            topics: 主题列表
        """
        self._log(f"开始执行定时任务: 生成 {batch_size} 篇笔记")

        # 随机选择主题
        selected_topics = random.sample(
            topics,
            min(batch_size, len(topics))
        )

        self._log(f"已选择 {len(selected_topics)} 个主题")

        results = []

        for i, topic in enumerate(selected_topics, 1):
            try:
                self._log(f"[{i}/{len(selected_topics)}] 开始生成: {topic}")

                # 生成笔记
                gen_result = self.note_generator.generate(topic)

                if gen_result["success"]:
                    self._log(f"[{i}/{len(selected_topics)}] 生成成功，字数: {gen_result.get('word_count', 0)}")

                    # 保存文件
                    save_result = self.file_manager.save(
                        content=gen_result["content"],
                        topic=topic
                    )

                    if save_result["success"]:
                        self._log(f"[{i}/{len(selected_topics)}] 保存成功: {save_result.get('filepath')}")

                        # Git操作
                        if self.git_manager:
                            self._log(f"[{i}/{len(selected_topics)}] 正在提交到Git...")
                            git_result = self.git_manager.commit_and_push(
                                [save_result["filepath"]],
                                topic=topic,
                                count=1
                            )

                            if git_result.get("success"):
                                self._log(f"[{i}/{len(selected_topics)}] Git操作成功")
                            else:
                                self._log(f"[{i}/{len(selected_topics)}] Git操作失败: {git_result.get('error')}")

                        results.append({
                            "topic": topic,
                            "status": "success",
                            "time": datetime.now().isoformat()
                        })

                        self.stats["success_count"] += 1
                    else:
                        raise Exception(save_result.get("error", "保存失败"))
                else:
                    raise Exception(gen_result.get("error", "生成失败"))

            except Exception as e:
                error_msg = f"处理主题 '{topic}' 失败: {e}"
                self._log(error_msg)
                logger.error(error_msg)
                results.append({
                    "topic": topic,
                    "status": "failed",
                    "error": str(e),
                    "time": datetime.now().isoformat()
                })
                self.stats["failed_count"] += 1

        # 更新统计
        self.stats["total_runs"] += 1
        self.stats["last_run"] = datetime.now().isoformat()

        # 添加到历史
        self.history.extend(results)

        # 限制历史记录数量（最多保留100条）
        if len(self.history) > 100:
            self.history = self.history[-100:]

        # 更新下次执行时间
        if self.job_id:
            next_run = self.scheduler.get_job(self.job_id).next_run_time
            self.stats["next_run"] = next_run.isoformat() if next_run else None

        logger.info(
            f"定时任务执行完成: "
            f"成功 {self.stats['success_count']}, "
            f"失败 {self.stats['failed_count']}"
        )

        # 调用回调函数
        if self.on_job_complete:
            self.on_job_complete(results)

    def execute_now(self, batch_size: int = None):
        """
        立即执行一次任务

        Args:
            batch_size: 生成数量（不指定则使用配置）
        """
        if not batch_size:
            batch_size = self.config.get("batch_size", 1)

        logger.info(f"手动执行任务: 生成 {batch_size} 篇")
        self._execute_batch(batch_size, self.topics)

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        return {
            "enabled": self.enabled,
            "config": self.config,
            "stats": self.stats,
            "job_id": self.job_id,
            "topics_count": len(self.topics)
        }

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取执行历史

        Args:
            limit: 返回条数

        Returns:
            历史记录列表
        """
        return self.history[-limit:]

    def shutdown(self):
        """关闭调度器"""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("调度器已关闭")
