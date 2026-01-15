"""
主窗口模块
Auto Obsidian的主界面
"""
import sys
import logging
from pathlib import Path
from typing import Optional

# 优先使用 PyQt5（更稳定），如果没有则使用 PyQt6
PYQT_VERSION = None  # 默认值
PYQT_AVAILABLE = False

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout,
        QHBoxLayout, QTabWidget, QLabel, QPushButton,
        QMessageBox, QStatusBar
    )
    from PyQt5.QtCore import Qt, QThread, pyqtSignal
    from PyQt5.QtGui import QIcon, QFont
    PYQT_VERSION = 5
    PYQT_AVAILABLE = True
except ImportError:
    try:
        from PyQt6.QtWidgets import (
            QApplication, QMainWindow, QWidget, QVBoxLayout,
            QHBoxLayout, QTabWidget, QLabel, QPushButton,
            QMessageBox, QStatusBar
        )
        from PyQt6.QtCore import Qt, QThread, pyqtSignal
        from PyQt6.QtGui import QIcon, QFont
        PYQT_VERSION = 6
        PYQT_AVAILABLE = True
    except ImportError:
        pass

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """主窗口类"""

    def __init__(self):
        super().__init__()

        # 核心组件（稍后初始化）
        self.config = None
        self.note_generator = None
        self.file_manager = None
        self.git_manager = None
        self.scheduler = None
        self.notification_manager = None

        # 初始化UI
        self._init_ui()

        logger.info("主窗口初始化完成")

    def _init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("AI学习笔记自动生成器 v1.0")
        self.setGeometry(100, 100, 1000, 700)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)

        # 标题
        title_label = QLabel("AI学习笔记自动生成器")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # 创建选项卡
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

        # 加载各个面板（稍后实现）
        self._load_panels()

    def _load_panels(self):
        """加载各个功能面板"""
        try:
            # 确保项目根目录在sys.path中
            from pathlib import Path
            import sys
            project_root = Path(__file__).parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))

            # 使用绝对导入
            from gui.config_panel import ConfigPanel
            from gui.note_panel import NotePanel
            from gui.scheduler_panel import SchedulerPanel
            from gui.stats_panel import StatsPanel

            # 配置面板
            self.config_panel = ConfigPanel()
            self.tab_widget.addTab(self.config_panel, "配置")

            # 定时任务面板
            self.scheduler_panel = SchedulerPanel()
            self.tab_widget.addTab(self.scheduler_panel, "定时任务")

            # 笔记生成面板
            self.note_panel = NotePanel()
            self.tab_widget.addTab(self.note_panel, "生成笔记")

            # 数据统计面板
            self.stats_panel = StatsPanel()
            self.tab_widget.addTab(self.stats_panel, "数据统计")

            logger.info("所有面板加载完成")

        except Exception as e:
            logger.error(f"加载面板失败: {e}", exc_info=True)
            self._show_placeholder_panels()

    def _show_placeholder_panels(self):
        """显示占位面板（当面板未实现时）"""
        # 根据加载的版本导入
        if PYQT_VERSION == 5:
            from PyQt5.QtWidgets import QTextEdit
        else:
            from PyQt6.QtWidgets import QTextEdit

        placeholder = QTextEdit()
        placeholder.setReadOnly(True)
        placeholder.setText("面板加载中...")

        self.tab_widget.addTab(placeholder, "配置")
        self.tab_widget.addTab(placeholder, "定时任务")
        self.tab_widget.addTab(placeholder, "生成笔记")

    def initialize_managers(self, config):
        """
        初始化核心管理器

        Args:
            config: 配置字典
        """
        try:
            import yaml
            import sys
            from pathlib import Path

            # 添加项目根目录到路径
            project_root = Path(__file__).parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))

            from src.note_generator import NoteGenerator
            from src.file_manager import FileManager
            from src.git_manager import GitManager
            from src.scheduler import NoteScheduler
            from src.crypto_utils import get_crypto_manager
            from src.notification_manager import NotificationManager

            self.config = config

            # 初始化通知管理器
            self.notification_manager = NotificationManager(self)

            # 获取 AI 配置
            ai_config = config.get("ai", {})

            # 解密 API key
            encrypted_api_key = ai_config.get("api_key", "")
            crypto_manager = get_crypto_manager()
            api_key = crypto_manager.decrypt(encrypted_api_key)

            if not api_key:
                logger.warning("API Key 为空，系统可能无法正常工作")

            # 初始化笔记生成器
            self.note_generator = NoteGenerator(
                provider_name=ai_config.get("provider", "chatglm"),
                api_key=api_key,
                model=ai_config.get("model", "glm-4")
            )

            # 初始化文件管理器
            obsidian_config = config.get("obsidian", {})
            self.file_manager = FileManager(
                save_dir=obsidian_config.get("save_dir", "./notes"),
                filename_format=obsidian_config.get("filename_format", "{date}_{topic}")
            )

            # 初始化Git管理器
            git_config = config.get("git", {})
            self.git_manager = GitManager(
                repo_path=obsidian_config.get("save_dir", "./notes"),
                auto_commit=git_config.get("auto_commit", True),
                auto_push=git_config.get("auto_push", True),
                commit_message_template=git_config.get("commit_message", "")
            )

            # 初始化调度器
            self.scheduler = NoteScheduler(
                note_generator=self.note_generator,
                file_manager=self.file_manager,
                git_manager=self.git_manager
            )

            # 连接通知管理器到调度器
            self.scheduler.on_job_complete = self.notification_manager.notify_job_complete

            # 设置统计面板的调度器
            self.stats_panel.set_scheduler(self.scheduler)

            self.status_bar.showMessage("系统初始化完成")
            logger.info("所有管理器初始化完成")

        except Exception as e:
            logger.error(f"初始化管理器失败: {e}")
            QMessageBox.critical(
                self,
                "初始化错误",
                f"初始化系统时出错:\n{str(e)}"
            )

    def closeEvent(self, event):
        """窗口关闭事件"""
        # 隐藏到系统托盘而不是退出
        if self.notification_manager and self.notification_manager.tray_icon.isVisible():
            self.hide()
            self.status_bar.showMessage("程序已最小化到系统托盘")
            logger.info("窗口隐藏到系统托盘")
            event.ignore()
        else:
            # 如果系统托盘不可用，则确认退出
            reply = QMessageBox.question(
                self,
                '确认退出',
                '确定要退出吗？定时任务将被停止。',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # 停止调度器
                if self.scheduler:
                    self.scheduler.shutdown()

                logger.info("应用程序退出")
                event.accept()
            else:
                event.ignore()


def load_config(config_path: str = None) -> dict:
    """
    加载配置文件

    Args:
        config_path: 配置文件路径（已废弃，保留用于向后兼容）

    Returns:
        配置字典
    """
    try:
        import yaml
        from src.config_manager import get_config_path_manager

        # 使用配置路径管理器获取配置文件路径
        config_path_manager = get_config_path_manager()
        config_file = config_path_manager.get_config_file()

        if not config_file.exists():
            logger.warning(f"配置文件不存在: {config_file}")
            return {}

        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        logger.info(f"配置文件加载成功: {config_file}")
        return config

    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        return {}


def main():
    """主函数"""
    if not PYQT_AVAILABLE:
        print("错误: PyQt6未安装")
        print("请运行: pip install PyQt6")
        sys.exit(1)

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 创建应用
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 使用Fusion风格

    # 创建主窗口
    window = MainWindow()
    window.show()

    # 加载配置并初始化管理器
    config = load_config()
    if config:
        window.initialize_managers(config)

    # 运行应用
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
