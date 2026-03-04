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


def global_exception_hook(exc_type, exc_value, exc_traceback):
    """全局异常捕获钩子"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger.critical("未处理的异常:", exc_info=(exc_type, exc_value, exc_traceback))
    
    # 尝试显示错误对话框
    try:
        from PyQt5.QtWidgets import QMessageBox
        error_msg = f"未处理的异常:\n{exc_type.__name__}: {exc_value}"
        QMessageBox.critical(None, "严重错误", error_msg)
    except:
        pass

def main():
    """主函数"""
    # 设置全局异常钩子
    sys.excepthook = global_exception_hook
    
    # 配置日志
    setup_logging()

    logger = logging.getLogger(__name__)
    logger.info("=" * 50)
    logger.info("Auto Obsidian 启动中...")
    logger.info("=" * 50)
    
    try:
        # 检查依赖
        logger.info("[STEP 1] 检查依赖包...")
        check_dependencies()
        logger.info("[STEP 1] 依赖检查完成")

        # 初始化配置路径管理器
        logger.info("[STEP 2] 正在初始化配置管理器...")
        from src.config_manager import get_config_path_manager
        logger.info("[STEP 2] 配置路径管理器导入成功")

        config_path_manager = get_config_path_manager()
        logger.info(f"[STEP 2] 配置路径管理器初始化成功，配置目录: {config_path_manager.config_dir}")

        # 检查是否首次运行
        logger.info("[STEP 3] 检查是否首次运行...")
        if config_path_manager.is_first_run():
            logger.info("[STEP 3] 检测到首次运行，正在初始化配置...")
            config_path_manager.initialize_on_first_run()
            logger.info("[STEP 3] 首次运行初始化完成")
        else:
            logger.info("[STEP 3] 非首次运行，尝试迁移旧配置...")
            config_path_manager.migrate_old_config()
            logger.info("[STEP 3] 旧配置迁移检查完成")

        # 导入GUI模块
        logger.info("[STEP 4] 导入GUI模块...")
        
        # 优先使用 PyQt5
        try:
            from PyQt5.QtWidgets import QApplication
            from PyQt5.QtCore import Qt
            logger.info("[STEP 4] PyQt5 导入成功")
        except ImportError as e:
            logger.warning(f"[STEP 4] PyQt5 导入失败: {e}，尝试 PyQt6")
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtCore import Qt
            logger.info("[STEP 4] PyQt6 导入成功")

        from gui.main_window import MainWindow, load_config
        logger.info("[STEP 4] MainWindow 和 load_config 导入成功")

        # 创建应用
        logger.info("[STEP 5] 创建QApplication...")
        app = QApplication(sys.argv)
        app.setApplicationName("Auto Obsidian")
        app.setOrganizationName("Auto Obsidian")
        logger.info("[STEP 5] QApplication 创建成功")

        # 设置高DPI支持
        logger.info("[STEP 6] 设置高DPI支持...")
        app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
        logger.info("[STEP 6] 高DPI支持设置完成")

        # 设置应用样式
        app.setStyle('Fusion')

        # 创建主窗口
        logger.info("[STEP 7] 创建主窗口...")
        window = MainWindow()
        logger.info("[STEP 7] 主窗口创建成功")
        
        window.show()
        logger.info("[STEP 7] 主窗口显示成功")

        # 加载配置并初始化管理器
        logger.info("[STEP 8] 加载配置...")
        config = load_config()
        
        if config:
            logger.info("[STEP 8] 配置加载成功，正在初始化管理器...")
            window.initialize_managers(config)
            logger.info("[STEP 8] 管理器初始化完成")
            logger.info("系统初始化完成")
        else:
            logger.warning("[STEP 8] 配置文件加载失败或为空，请先配置系统")

        # 运行应用
        logger.info("[STEP 9] 进入GUI事件循环...")
        exit_code = app.exec()
        logger.info(f"[STEP 9] GUI事件循环退出，退出码: {exit_code}")
        sys.exit(exit_code)
    
    except SystemExit as e:
        logger.info(f"程序正常退出，退出码: {e.code}")
        raise
    except KeyboardInterrupt:
        logger.warning("程序被用户中断")
        sys.exit(1)
    except ImportError as e:
        logger.error(f"导入模块失败: {e}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"程序启动失败: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
