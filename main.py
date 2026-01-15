"""
Auto Obsidian - AI学习笔记自动生成器
主程序入口
"""
import sys
import logging
from pathlib import Path

# 配置日志
def setup_logging():
    """配置日志系统"""
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "auto_obsidian.log", encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def check_dependencies():
    """检查依赖包"""
    missing = []

    # 检查 PyQt5 或 PyQt6
    try:
        import PyQt5
    except ImportError:
        try:
            import PyQt6
        except ImportError:
            missing.append("PyQt5 or PyQt6")

    try:
        import yaml
    except ImportError:
        missing.append("PyYAML")

    try:
        import zhipuai
    except ImportError:
        missing.append("zhipuai")

    try:
        import git
    except ImportError:
        missing.append("GitPython")

    try:
        import apscheduler
    except ImportError:
        missing.append("APScheduler")

    if missing:
        print("错误: 缺少以下依赖包:")
        for pkg in missing:
            print(f"  - {pkg}")
        print("\n请运行: pip install -r requirements.txt")
        sys.exit(1)


def main():
    """主函数"""
    # 配置日志
    setup_logging()

    logger = logging.getLogger(__name__)
    logger.info("=" * 50)
    logger.info("Auto Obsidian 启动中...")
    logger.info("=" * 50)

    # 检查依赖
    check_dependencies()

    # 初始化配置路径管理器
    logger.info("正在初始化配置管理器...")
    from src.config_manager import get_config_path_manager

    config_path_manager = get_config_path_manager()

    # 检查是否首次运行
    if config_path_manager.is_first_run():
        logger.info("检测到首次运行，正在初始化配置...")
        config_path_manager.initialize_on_first_run()
        logger.info("首次运行初始化完成")
    else:
        # 尝试迁移旧配置
        config_path_manager.migrate_old_config()

    # 导入GUI模块
    try:
        # 优先使用 PyQt5
        try:
            from PyQt5.QtWidgets import QApplication
            from PyQt5.QtCore import Qt
        except ImportError:
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtCore import Qt

        from gui.main_window import MainWindow, load_config

        # 创建应用
        app = QApplication(sys.argv)
        app.setApplicationName("Auto Obsidian")
        app.setOrganizationName("Auto Obsidian")

        # 设置高DPI支持
        app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

        # 设置应用样式
        app.setStyle('Fusion')

        # 创建主窗口
        logger.info("正在创建主窗口...")
        window = MainWindow()
        window.show()

        # 加载配置并初始化管理器
        logger.info("正在加载配置...")
        config = load_config()

        if config:
            window.initialize_managers(config)
            logger.info("系统初始化完成")
        else:
            logger.warning("配置文件加载失败或为空，请先配置系统")

        # 运行应用
        logger.info("GUI应用已启动")
        sys.exit(app.exec())

    except ImportError as e:
        logger.error(f"导入模块失败: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"程序启动失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
