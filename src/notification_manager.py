"""
通知管理器模块
管理系统托盘通知和弹窗通知
"""
import logging
from datetime import datetime
from PyQt5.QtWidgets import (
    QSystemTrayIcon, QMenu, QAction, QDialog, QVBoxLayout,
    QLabel, QWidget, QApplication
)
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont

logger = logging.getLogger(__name__)


class PopupNotificationDialog(QDialog):
    """自动关闭的弹窗通知对话框"""

    def __init__(self, title: str, message: str, notification_type: str = "info", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.notification_type = notification_type

        # 设置窗口属性
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Dialog
        )
        self.setModal(False)

        # 设置固定大小
        self.setFixedSize(350, 120)

        # 设置背景色根据通知类型
        if notification_type == "success":
            bg_color = "#d4edda"
            border_color = "#c3e6cb"
        elif notification_type == "error":
            bg_color = "#f8d7da"
            border_color = "#f5c6cb"
        else:
            bg_color = "#d1ecf1"
            border_color = "#bee5eb"

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 8px;
            }}
        """)

        # 创建UI
        self._init_ui(title, message)

        # 设置自动关闭定时器（5秒）
        self.auto_close_timer = QTimer()
        self.auto_close_timer.timeout.connect(self.accept)
        self.auto_close_timer.start(5000)

        # 鼠标是否悬停
        self.is_hovering = False

        logger.debug(f"创建弹窗通知: {title}")

    def _init_ui(self, title: str, message: str):
        """初始化UI"""
        layout = QVBoxLayout(self)

        # 标题
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title_label.setFont(title_font)

        # 根据类型设置图标
        if self.notification_type == "success":
            icon_text = "✓"
            icon_color = "#28a745"
        elif self.notification_type == "error":
            icon_text = "✗"
            icon_color = "#dc3545"
        else:
            icon_text = "ℹ"
            icon_color = "#17a2b8"

        icon_label = QLabel(icon_text)
        icon_label.setStyleSheet(f"font-size: 24px; color: {icon_color};")

        # 消息
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_font = QFont()
        message_font.setPointSize(9)
        message_label.setFont(message_font)

        # 添加到布局
        icon_title_layout = QVBoxLayout()
        icon_title_layout.addWidget(icon_label)
        icon_title_layout.addWidget(title_label)

        layout.addLayout(icon_title_layout)
        layout.addWidget(message_label)
        layout.addStretch()

        # 设置边距
        layout.setContentsMargins(15, 15, 15, 15)

    def enterEvent(self, event):
        """鼠标进入事件 - 暂停自动关闭"""
        self.is_hovering = True
        if self.auto_close_timer.isActive():
            self.auto_close_timer.stop()
            logger.debug("弹窗通知：鼠标悬停，暂停自动关闭")
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开事件 - 恢复自动关闭"""
        self.is_hovering = False
        if not self.auto_close_timer.isActive():
            # 重新启动定时器，但给用户3秒时间
            self.auto_close_timer.start(3000)
            logger.debug("弹窗通知：鼠标离开，恢复自动关闭")
        super().leaveEvent(event)

    def show_notification(self):
        """显示通知在屏幕右下角"""
        # 获取屏幕几何信息
        screen_geometry = QApplication.desktop().screenGeometry()
        x = screen_geometry.width() - self.width() - 20
        y = screen_geometry.height() - self.height() - 60

        self.move(x, y)
        self.show()
        logger.debug(f"弹窗通知显示在位置: ({x}, {y})")


class NotificationManager:
    """通知管理器"""

    def __init__(self, main_window):
        """初始化通知管理器

        Args:
            main_window: 主窗口对象
        """
        self.main_window = main_window
        self.tray_icon = None

        # 通知开关
        self.tray_notification_enabled = True
        self.popup_notification_enabled = True

        # 通知冷却时间（秒）
        self.notification_cooldown = 10
        self.last_notification_time = None

        # 设置系统托盘
        self.setup_system_tray()

        logger.info("通知管理器初始化完成")

    def setup_system_tray(self):
        """设置系统托盘图标"""
        try:
            # 创建托盘图标
            self.tray_icon = QSystemTrayIcon(self.main_window)

            # 使用QPainter绘制简单的图标
            pixmap = QPixmap(32, 32)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)

            # 绘制圆形背景
            painter.setBrush(QColor("#6c5ce7"))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(0, 0, 32, 32)

            # 绘制"AO"文字
            painter.setPen(QColor("#ffffff"))
            font = QFont("Arial", 10, QFont.Bold)
            painter.setFont(font)
            painter.drawText(pixmap.rect(), Qt.AlignCenter, "AO")

            painter.end()

            icon = QIcon(pixmap)
            self.tray_icon.setIcon(icon)

            # 创建托盘菜单
            tray_menu = QMenu()

            show_action = QAction("显示主窗口", self.main_window)
            show_action.triggered.connect(self._show_main_window)
            tray_menu.addAction(show_action)

            tray_menu.addSeparator()

            quit_action = QAction("退出", self.main_window)
            quit_action.triggered.connect(self._quit_application)
            tray_menu.addAction(quit_action)

            self.tray_icon.setContextMenu(tray_menu)

            # 双击托盘图标显示主窗口
            self.tray_icon.activated.connect(self._on_tray_icon_activated)

            # 显示托盘图标
            self.tray_icon.show()

            logger.info("系统托盘图标设置成功")

        except Exception as e:
            logger.error(f"设置系统托盘失败: {e}")

    def _show_main_window(self):
        """显示主窗口"""
        if self.main_window:
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()
            logger.info("从系统托盘显示主窗口")

    def _quit_application(self):
        """退出应用程序"""
        if self.main_window:
            QApplication.instance().quit()
            logger.info("从系统托盘退出应用程序")

    def _on_tray_icon_activated(self, reason):
        """托盘图标被激活"""
        if reason == QSystemTrayIcon.DoubleClick:
            self._show_main_window()

    def show_tray_notification(self, title: str, message: str, icon=QSystemTrayIcon.Information):
        """显示系统托盘通知

        Args:
            title: 通知标题
            message: 通知消息
            icon: 通知图标类型
        """
        if not self.tray_notification_enabled:
            logger.debug("系统托盘通知已禁用")
            return

        if not self.tray_icon or not self.tray_icon.supportsMessages():
            logger.warning("系统托盘不支持消息通知")
            return

        # 检查冷却时间
        if self._is_in_cooldown():
            logger.debug("通知冷却中，跳过本次通知")
            return

        try:
            self.tray_icon.showMessage(
                title,
                message,
                icon,
                3000  # 显示3秒
            )
            self._update_last_notification_time()
            logger.info(f"系统托盘通知已发送: {title}")

        except Exception as e:
            logger.error(f"发送系统托盘通知失败: {e}")

    def show_popup_notification(self, title: str, message: str, notification_type: str = "info"):
        """显示弹窗通知

        Args:
            title: 通知标题
            message: 通知消息
            notification_type: 通知类型 (info/success/error)
        """
        if not self.popup_notification_enabled:
            logger.debug("弹窗通知已禁用")
            return

        # 检查冷却时间
        if self._is_in_cooldown():
            logger.debug("通知冷却中，跳过本次通知")
            return

        try:
            dialog = PopupNotificationDialog(title, message, notification_type, self.main_window)
            dialog.show_notification()
            self._update_last_notification_time()
            logger.info(f"弹窗通知已发送: {title}")

        except Exception as e:
            logger.error(f"发送弹窗通知失败: {e}")

    def notify_job_complete(self, results: dict):
        """任务完成回调函数

        Args:
            results: 任务执行结果字典
                {
                    "total": int,        # 总数
                    "success": int,      # 成功数
                    "failed": int,       # 失败数
                    "errors": list       # 错误列表
                }
        """
        try:
            total = results.get("total", 0)
            success = results.get("success", 0)
            failed = results.get("failed", 0)
            errors = results.get("errors", [])

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if failed > 0:
                # 有失败的情况
                title = "任务执行完成（部分失败）"
                message = f"时间: {timestamp}\n总计: {total} 篇 | 成功: {success} 篇 | 失败: {failed} 篇"

                if errors:
                    first_error = errors[0] if isinstance(errors, list) else str(errors)
                    message += f"\n错误: {first_error}"

                self.show_tray_notification(title, message, QSystemTrayIcon.Warning)
                self.show_popup_notification(title, message, "error")

            else:
                # 全部成功
                title = "任务执行成功"
                message = f"时间: {timestamp}\n成功生成 {success} 篇笔记"

                self.show_tray_notification(title, message, QSystemTrayIcon.Information)
                self.show_popup_notification(title, message, "success")

            logger.info(f"任务完成通知已发送: 成功={success}, 失败={failed}")

        except Exception as e:
            logger.error(f"发送任务完成通知失败: {e}")

    def notify_job_failed(self, error_message: str):
        """任务失败通知

        Args:
            error_message: 错误消息
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            title = "任务执行失败"
            message = f"时间: {timestamp}\n{error_message}"

            self.show_tray_notification(title, message, QSystemTrayIcon.Critical)
            self.show_popup_notification(title, message, "error")

            logger.info(f"任务失败通知已发送: {error_message}")

        except Exception as e:
            logger.error(f"发送任务失败通知失败: {e}")

    def set_notifications_enabled(self, tray_enabled: bool, popup_enabled: bool):
        """设置通知开关

        Args:
            tray_enabled: 是否启用系统托盘通知
            popup_enabled: 是否启用弹窗通知
        """
        self.tray_notification_enabled = tray_enabled
        self.popup_notification_enabled = popup_enabled
        logger.info(f"通知设置已更新: 托盘={tray_enabled}, 弹窗={popup_enabled}")

    def _is_in_cooldown(self) -> bool:
        """检查是否在冷却期内"""
        if self.last_notification_time is None:
            return False

        current_time = datetime.now()
        time_diff = (current_time - self.last_notification_time).total_seconds()
        return time_diff < self.notification_cooldown

    def _update_last_notification_time(self):
        """更新最后通知时间"""
        self.last_notification_time = datetime.now()
