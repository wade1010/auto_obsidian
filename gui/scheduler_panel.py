"""
定时任务面板模块
用于配置和管理定时任务
"""
import logging
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QGroupBox, QSpinBox,
    QTimeEdit, QTextEdit, QCheckBox, QMessageBox
)
from PyQt5.QtCore import Qt, QTime, QTimer
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)


class SchedulerPanel(QWidget):
    """定时任务面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scheduler = None
        self.topics = []

        # 自动刷新定时器
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._refresh_ui)

        self._init_ui()
        self._load_topics()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)

        # 定时设置组
        settings_group = self._create_settings_group()
        layout.addWidget(settings_group)

        # 主题配置组
        topic_group = self._create_topic_group()
        layout.addWidget(topic_group)

        # 任务控制组
        control_group = self._create_control_group()
        layout.addWidget(control_group)

        # 实时日志组
        log_group = self._create_log_group()
        layout.addWidget(log_group)

        # 执行记录组
        history_group = self._create_history_group()
        layout.addWidget(history_group)

        layout.addStretch()

        # 在所有UI创建完成后，连接信号
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        self.interval_unit_combo.currentTextChanged.connect(self._on_interval_unit_changed)

        # 初始化为"每天执行"模式，并手动调用一次设置状态
        # 使用 blockSignals 避免重复触发
        self.mode_combo.blockSignals(True)
        self.mode_combo.setCurrentIndex(0)
        self.mode_combo.blockSignals(False)
        # 手动调用设置初始状态
        self._on_mode_changed("每天执行")

    def _create_settings_group(self) -> QGroupBox:
        """创建定时设置组"""
        group = QGroupBox("定时设置")
        layout = QVBoxLayout()

        # 执行模式
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("执行模式:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["每天执行", "每小时执行", "自定义间隔"])
        mode_layout.addWidget(self.mode_combo)
        layout.addLayout(mode_layout)

        # 每天执行时间
        self.time_layout = QHBoxLayout()
        self.time_layout.addWidget(QLabel("执行时间:"))
        self.time_edit = QTimeEdit()
        # 默认设置为当前时间
        from datetime import datetime
        now = datetime.now()
        self.time_edit.setTime(QTime(now.hour, now.minute))
        self.time_layout.addWidget(self.time_edit)
        self.time_layout.addWidget(QLabel("(24小时间隔)"))
        layout.addLayout(self.time_layout)

        # 自定义间隔
        self.interval_layout = QHBoxLayout()
        self.interval_layout.addWidget(QLabel("间隔时间:"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setMinimum(1)
        self.interval_spin.setMaximum(168)
        self.interval_spin.setValue(2)
        self.interval_layout.addWidget(self.interval_spin)

        # 添加时间单位选择器
        self.interval_unit_combo = QComboBox()
        self.interval_unit_combo.addItems(["小时", "分钟"])
        self.interval_layout.addWidget(self.interval_unit_combo)

        layout.addLayout(self.interval_layout)

        # 每次生成数量
        batch_layout = QHBoxLayout()
        batch_layout.addWidget(QLabel("每次生成:"))
        self.batch_spin = QSpinBox()
        self.batch_spin.setMinimum(1)
        self.batch_spin.setMaximum(20)
        self.batch_spin.setValue(3)
        batch_layout.addWidget(self.batch_spin)
        batch_layout.addWidget(QLabel("篇"))
        layout.addLayout(batch_layout)

        group.setLayout(layout)
        return group

    def _create_topic_group(self) -> QGroupBox:
        """创建主题配置组"""
        group = QGroupBox("主题配置")
        layout = QVBoxLayout()

        # 主题来源
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("主题来源:"))
        self.topic_source_combo = QComboBox()
        self.topic_source_combo.addItems(["从预设列表随机", "从指定文件读取"])
        source_layout.addWidget(self.topic_source_combo)
        layout.addLayout(source_layout)

        # 可用主题数
        self.topic_count_label = QLabel("可用主题: 加载中...")
        layout.addWidget(self.topic_count_label)

        group.setLayout(layout)
        return group

    def _create_control_group(self) -> QGroupBox:
        """创建任务控制组"""
        group = QGroupBox("任务控制")
        layout = QVBoxLayout()

        # 任务状态
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("状态:"))
        self.status_label = QLabel("未启动")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)

        # 下次执行时间
        self.next_run_label = QLabel("下次执行: 未设置")
        layout.addWidget(self.next_run_label)

        # 统计信息
        stats_layout = QHBoxLayout()
        self.total_runs_label = QLabel("执行次数: 0")
        self.success_label = QLabel("成功: 0")
        self.failed_label = QLabel("失败: 0")
        stats_layout.addWidget(self.total_runs_label)
        stats_layout.addWidget(self.success_label)
        stats_layout.addWidget(self.failed_label)
        layout.addLayout(stats_layout)

        # 控制按钮
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("开始任务")
        self.start_btn.clicked.connect(self._start_scheduler)
        self.pause_btn = QPushButton("暂停任务")
        self.pause_btn.clicked.connect(self._pause_scheduler)
        self.pause_btn.setEnabled(False)
        self.execute_now_btn = QPushButton("立即执行")
        self.execute_now_btn.clicked.connect(self._execute_now)
        self.reset_btn = QPushButton("重置任务")
        self.reset_btn.clicked.connect(self._reset_scheduler)
        self.reset_btn.setStyleSheet("color: red;")

        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.pause_btn)
        btn_layout.addWidget(self.execute_now_btn)
        btn_layout.addWidget(self.reset_btn)
        layout.addLayout(btn_layout)

        group.setLayout(layout)
        return group

    def _create_log_group(self) -> QGroupBox:
        """创建实时日志组"""
        group = QGroupBox("实时执行日志")
        layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        self.log_text.setPlaceholderText("任务执行日志将实时显示在这里...")
        layout.addWidget(self.log_text)

        group.setLayout(layout)
        return group

    def _create_history_group(self) -> QGroupBox:
        """创建执行记录组"""
        group = QGroupBox("最近执行记录")
        layout = QVBoxLayout()

        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        self.history_text.setMaximumHeight(150)
        layout.addWidget(self.history_text)

        group.setLayout(layout)
        return group

    def _on_mode_changed(self, mode: str):
        """模式改变事件"""
        logger.info(f"模式切换为: {mode}")

        if mode == "每天执行":
            # 每天执行：只需要设置执行时间，间隔时间禁用
            self.time_layout.setEnabled(True)
            self.interval_layout.setEnabled(False)
            self.interval_spin.setEnabled(False)
            self.interval_unit_combo.setEnabled(False)
            logger.info("每天执行: 执行时间启用，间隔时间禁用")
        elif mode == "每小时执行":
            # 每小时执行：需要设置间隔时间（固定用小时）
            self.time_layout.setEnabled(False)
            self.interval_layout.setEnabled(True)
            self.interval_spin.setEnabled(True)
            self.interval_unit_combo.setEnabled(False)  # 禁用单位选择，固定用小时
            logger.info("每小时执行: 执行时间禁用，间隔时间启用，单位禁用")
        else:  # 自定义间隔
            # 自定义间隔：需要设置间隔时间和单位
            self.time_layout.setEnabled(False)
            self.interval_layout.setEnabled(True)
            self.interval_spin.setEnabled(True)
            self.interval_unit_combo.setEnabled(True)  # 启用单位选择
            logger.info("自定义间隔: 执行时间禁用，间隔时间和单位都启用")

    def _on_interval_unit_changed(self, unit: str):
        """间隔单位改变事件"""
        if unit == "分钟":
            # 分钟模式：最大1440分钟（24小时）
            self.interval_spin.setMinimum(1)
            self.interval_spin.setMaximum(1440)
            self.interval_spin.setValue(min(self.interval_spin.value(), 1440))
        else:
            # 小时模式：最大168小时（7天）
            self.interval_spin.setMinimum(1)
            self.interval_spin.setMaximum(168)

    def _load_topics(self):
        """加载主题列表"""
        try:
            import yaml

            topics_file = "config/topics.yaml"
            with open(topics_file, 'r', encoding='utf-8') as f:
                topics_data = yaml.safe_load(f)

            # 提取所有主题
            self.topics = []
            for category, topic_list in topics_data.items():
                self.topics.extend(topic_list)

            self.topic_count_label.setText(
                f"可用主题: {len(self.topics)} 个"
            )
            logger.info(f"已加载 {len(self.topics)} 个主题")

        except Exception as e:
            logger.error(f"加载主题失败: {e}")
            self.topic_count_label.setText("可用主题: 加载失败")

    def _start_scheduler(self):
        """启动定时任务"""
        if not self.topics:
            QMessageBox.warning(self, "警告", "主题列表为空，无法启动")
            return

        try:
            mode = self.mode_combo.currentText()
            batch_size = self.batch_spin.value()

            # 获取主窗口的调度器
            main_window = self._get_main_window()
            if not main_window or not main_window.scheduler:
                QMessageBox.warning(
                    self,
                    "警告",
                    "系统未初始化，请先检查配置"
                )
                return

            scheduler = main_window.scheduler

            # 根据模式设置调度
            if mode == "每天执行":
                time_str = self.time_edit.time().toString("HH:mm")
                success = scheduler.setup_daily_job(
                    time_str=time_str,
                    batch_size=batch_size,
                    topics=self.topics
                )
            elif mode == "每小时执行":
                success = scheduler.setup_interval_job(
                    hours=1,
                    batch_size=batch_size,
                    topics=self.topics
                )
            else:  # 自定义间隔
                interval_value = self.interval_spin.value()
                interval_unit = self.interval_unit_combo.currentText()

                # 如果是分钟，转换为小时
                if interval_unit == "分钟":
                    hours = interval_value / 60.0
                else:
                    hours = interval_value

                success = scheduler.setup_interval_job(
                    hours=hours,
                    batch_size=batch_size,
                    topics=self.topics
                )

            if success:
                self.status_label.setText("运行中")
                self.status_label.setStyleSheet("color: green; font-weight: bold;")
                self.start_btn.setEnabled(False)
                self.pause_btn.setEnabled(True)
                self._update_stats(scheduler.get_stats())

                # 启动自动刷新定时器（每5秒刷新一次）
                self.refresh_timer.start(5000)

                QMessageBox.information(self, "成功", "定时任务已启动")
            else:
                QMessageBox.critical(self, "错误", "启动定时任务失败")

        except Exception as e:
            QMessageBox.critical(
                self,
                "错误",
                f"启动任务出错:\n{str(e)}"
            )
            logger.error(f"启动调度器失败: {e}")

    def _pause_scheduler(self):
        """暂停定时任务"""
        try:
            main_window = self._get_main_window()
            if not main_window or not main_window.scheduler:
                return

            scheduler = main_window.scheduler
            scheduler.pause()

            self.status_label.setText("已暂停")
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")
            self.start_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)

            # 停止自动刷新定时器
            self.refresh_timer.stop()

            logger.info("定时任务已暂停")

        except Exception as e:
            logger.error(f"暂停任务失败: {e}")

    def _execute_now(self):
        """立即执行一次任务"""
        try:
            main_window = self._get_main_window()
            if not main_window or not main_window.scheduler:
                QMessageBox.warning(self, "警告", "系统未初始化")
                return

            batch_size = self.batch_spin.value()
            scheduler = main_window.scheduler

            self.status_label.setText("执行中...")
            scheduler.execute_now(batch_size)
            self._update_stats(scheduler.get_stats())
            self._update_history(scheduler.get_history())

            self.status_label.setText("运行中")
            QMessageBox.information(self, "完成", "任务执行完成")

        except Exception as e:
            QMessageBox.critical(
                self,
                "错误",
                f"执行任务出错:\n{str(e)}"
            )
            logger.error(f"执行任务失败: {e}")

    def _reset_scheduler(self):
        """重置定时任务"""
        try:
            main_window = self._get_main_window()
            if not main_window or not main_window.scheduler:
                QMessageBox.warning(self, "警告", "系统未初始化")
                return

            reply = QMessageBox.question(
                self,
                '确认重置',
                '确定要重置定时任务吗？\n当前任务将被停止，您可以重新设置。',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                scheduler = main_window.scheduler

                # 移除当前任务
                scheduler._remove_job()

                # 清空日志列表
                if hasattr(scheduler, 'log_messages'):
                    scheduler.log_messages.clear()

                # 重置状态
                self.status_label.setText("未启动")
                self.status_label.setStyleSheet("color: red; font-weight: bold;")
                self.start_btn.setEnabled(True)
                self.pause_btn.setEnabled(False)

                # 停止自动刷新定时器
                self.refresh_timer.stop()

                # 清空界面日志
                self.log_text.clear()
                self.log_text.append("[系统] 任务已重置，可以重新设置定时任务")

                # 清空统计显示（可选）
                # self.next_run_label.setText("下次执行: --")

                logger.info("定时任务已重置")

        except Exception as e:
            QMessageBox.critical(
                self,
                "错误",
                f"重置任务出错:\n{str(e)}"
            )
            logger.error(f"重置任务失败: {e}")

    def _update_stats(self, stats: dict):
        """更新统计信息"""
        stats_data = stats.get("stats", {})
        self.total_runs_label.setText(f"执行次数: {stats_data.get('total_runs', 0)}")
        self.success_label.setText(f"成功: {stats_data.get('success_count', 0)}")
        self.failed_label.setText(f"失败: {stats_data.get('failed_count', 0)}")

        next_run = stats_data.get('next_run')
        if next_run:
            self.next_run_label.setText(f"下次执行: {next_run}")

    def _update_history(self, history: list):
        """更新执行历史"""
        if not history:
            self.history_text.setText("暂无执行记录")
            return

        lines = []
        for record in reversed(history[-10:]):  # 显示最近10条
            time_str = record.get('time', '')
            topic = record.get('topic', '')
            status = record.get('status', '')
            status_symbol = "✓" if status == "success" else "✗"

            lines.append(f"[{time_str}] {topic} {status_symbol}")

        self.history_text.setText('\n'.join(lines))

    def set_scheduler(self, scheduler):
        """设置调度器实例"""
        self.scheduler = scheduler

    def _get_main_window(self):
        """获取主窗口对象"""
        try:
            # 方法1: 通过parent链
            parent = self.parent()
            if parent:
                main_window = parent.parent()
                if hasattr(main_window, 'scheduler'):
                    return main_window

            # 方法2: 通过QApplication
            from PyQt5.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                widgets = app.topLevelWidgets()
                for widget in widgets:
                    if hasattr(widget, 'scheduler'):
                        return widget

            return None
        except Exception as e:
            logger.error(f"获取main_window失败: {e}")
            return None

    def _refresh_ui(self):
        """自动刷新UI统计信息"""
        try:
            main_window = self._get_main_window()
            if not main_window or not main_window.scheduler:
                return

            scheduler = main_window.scheduler

            # 更新统计信息
            self._update_stats(scheduler.get_stats())

            # 更新执行历史
            self._update_history(scheduler.get_history())

            # 更新实时日志（只显示新增的日志）
            if hasattr(scheduler, 'log_messages'):
                current_log_count = len(self.log_text.toPlainText().split('\n')) if self.log_text.toPlainText() else 0
                new_logs = scheduler.log_messages[current_log_count:]
                for log in new_logs:
                    self.log_text.append(log)

                # 自动滚动到底部
                if new_logs:
                    cursor = self.log_text.textCursor()
                    cursor.movePosition(cursor.End)
                    self.log_text.setTextCursor(cursor)

            logger.debug("UI已自动刷新")

        except Exception as e:
            logger.error(f"自动刷新UI失败: {e}")

    def append_log(self, message: str):
        """追加日志到实时日志显示区域"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_line = f"[{timestamp}] {message}"
            self.log_text.append(log_line)
            # 自动滚动到底部
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.End)
            self.log_text.setTextCursor(cursor)
        except Exception as e:
            logger.error(f"追加日志失败: {e}")
