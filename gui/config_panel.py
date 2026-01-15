"""
配置面板模块
用于配置系统参数
"""
import logging
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QGroupBox,
    QFileDialog, QMessageBox, QSpinBox, QCheckBox
)
from PyQt5.QtCore import Qt

logger = logging.getLogger(__name__)


class ConfigPanel(QWidget):
    """配置面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = {}
        self.dir_history = []  # 目录历史记录
        self._init_ui()
        self._load_dir_history()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)

        # Obsidian配置组
        obsidian_group = self._create_obsidian_group()
        layout.addWidget(obsidian_group)

        # AI配置组
        ai_group = self._create_ai_group()
        layout.addWidget(ai_group)

        # Git配置组
        git_group = self._create_git_group()
        layout.addWidget(git_group)

        # 操作按钮
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("保存配置")
        self.save_btn.clicked.connect(self._save_config)
        self.reload_btn = QPushButton("重新加载")
        self.reload_btn.clicked.connect(self._reload_config)

        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.reload_btn)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)
        layout.addStretch()

    def _create_obsidian_group(self) -> QGroupBox:
        """创建Obsidian配置组"""
        group = QGroupBox("Obsidian配置")
        layout = QVBoxLayout()

        # 保存目录（第一行：输入框和浏览按钮）
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("保存目录:"))
        self.save_dir_edit = QLineEdit()
        self.save_dir_edit.setPlaceholderText("选择Obsidian笔记保存目录")
        dir_layout.addWidget(self.save_dir_edit)

        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._browse_directory)
        dir_layout.addWidget(browse_btn)

        layout.addLayout(dir_layout)

        # 历史记录（第二行：下拉框和删除按钮）
        history_layout = QHBoxLayout()
        history_layout.addWidget(QLabel("历史记录:"))
        self.dir_history_combo = QComboBox()
        self.dir_history_combo.currentTextChanged.connect(self._on_history_selected)
        history_layout.addWidget(self.dir_history_combo)

        delete_history_btn = QPushButton("删除")
        delete_history_btn.clicked.connect(self._delete_history)
        delete_history_btn.setMaximumWidth(60)
        history_layout.addWidget(delete_history_btn)

        clear_history_btn = QPushButton("清空")
        clear_history_btn.clicked.connect(self._clear_history)
        clear_history_btn.setMaximumWidth(60)
        history_layout.addWidget(clear_history_btn)

        layout.addLayout(history_layout)

        # 文件名格式
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("文件名格式:"))
        self.filename_format_edit = QLineEdit("{date}_{topic}")
        self.filename_format_edit.setPlaceholderText("例如: {date}_{topic}")
        name_layout.addWidget(self.filename_format_edit)
        layout.addLayout(name_layout)

        hint_label = QLabel("可用变量: {date}, {topic}, {datetime}, {timestamp}")
        hint_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(hint_label)

        group.setLayout(layout)
        return group

    def _create_ai_group(self) -> QGroupBox:
        """创建AI配置组"""
        group = QGroupBox("AI配置")
        layout = QVBoxLayout()

        # AI服务提供商
        provider_layout = QHBoxLayout()
        provider_layout.addWidget(QLabel("AI服务商:"))
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["chatglm", "openai"])
        provider_layout.addWidget(self.provider_combo)
        layout.addLayout(provider_layout)

        # API Key
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("API Key:"))
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("输入API密钥")
        key_layout.addWidget(self.api_key_edit)
        layout.addLayout(key_layout)

        # 模型选择
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("模型:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "glm-4",
            "glm-4.7",
            "glm-4-plus",
            "glm-4-flash",
            "glm-4-air",
            "glm-3-turbo"
        ])
        model_layout.addWidget(self.model_combo)
        layout.addLayout(model_layout)

        # 语言选择
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("笔记语言:"))
        self.language_combo = QComboBox()
        self.language_combo.addItems(["中文", "English"])
        lang_layout.addWidget(self.language_combo)
        layout.addLayout(lang_layout)

        # 风格选择
        style_layout = QHBoxLayout()
        style_layout.addWidget(QLabel("笔记风格:"))
        self.style_combo = QComboBox()
        self.style_combo.addItems([
            "详细教程",
            "简洁概述",
            "深度解析",
            "实战指南"
        ])
        style_layout.addWidget(self.style_combo)
        layout.addLayout(style_layout)

        # 测试连接按钮
        test_btn = QPushButton("测试API连接")
        test_btn.clicked.connect(self._test_connection)
        layout.addWidget(test_btn)

        group.setLayout(layout)
        return group

    def _create_git_group(self) -> QGroupBox:
        """创建Git配置组"""
        group = QGroupBox("Git配置")
        layout = QVBoxLayout()

        # 自动提交
        self.auto_commit_checkbox = QCheckBox("自动提交 (git commit)")
        self.auto_commit_checkbox.setChecked(True)
        layout.addWidget(self.auto_commit_checkbox)

        # 自动推送
        self.auto_push_checkbox = QCheckBox("自动推送 (git push)")
        self.auto_push_checkbox.setChecked(True)
        layout.addWidget(self.auto_push_checkbox)

        # 提交信息模板
        msg_layout = QHBoxLayout()
        msg_layout.addWidget(QLabel("提交信息:"))
        self.commit_msg_edit = QLineEdit("docs: 自动生成AI学习笔记 - {date}")
        msg_layout.addWidget(self.commit_msg_edit)
        layout.addLayout(msg_layout)

        group.setLayout(layout)
        return group

    def _browse_directory(self):
        """浏览选择目录"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择Obsidian保存目录",
            ""
        )

        if directory:
            self.save_dir_edit.setText(directory)
            self._add_to_history(directory)

    def _test_connection(self):
        """测试API连接"""
        api_key = self.api_key_edit.text()
        provider = self.provider_combo.currentText()
        model = self.model_combo.currentText()

        if not api_key:
            QMessageBox.warning(self, "警告", "请先输入API Key")
            return

        try:
            import sys
            from pathlib import Path

            # 添加项目根目录到路径
            project_root = Path(__file__).parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))

            from src.note_generator import NoteGenerator

            # 创建临时生成器进行测试
            generator = NoteGenerator(
                provider_name=provider,
                api_key=api_key,
                model=model
            )

            if generator.test_connection():
                QMessageBox.information(
                    self,
                    "成功",
                    f"连接测试成功！\n服务商: {provider}\n模型: {model}"
                )
                logger.info("API连接测试成功")
            else:
                QMessageBox.critical(
                    self,
                    "失败",
                    "连接测试失败，请检查API Key和网络连接"
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "错误",
                f"连接测试出错:\n{str(e)}"
            )
            logger.error(f"API连接测试失败: {e}")

    def _save_config(self):
        """保存配置"""
        try:
            import yaml
            import sys
            from pathlib import Path

            # 导入加密工具
            project_root = Path(__file__).parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))

            from src.crypto_utils import get_crypto_manager

            # 获取 API key
            api_key = self.api_key_edit.text()

            # 加密 API key
            crypto_manager = get_crypto_manager()
            encrypted_key = crypto_manager.encrypt(api_key)

            if crypto_manager.is_available():
                logger.info("API key 已加密保存")
            else:
                logger.warning("cryptography 库不可用，API key 使用 Base64 编码保存")

            # 收集配置
            self.config = {
                "obsidian": {
                    "save_dir": self.save_dir_edit.text(),
                    "filename_format": self.filename_format_edit.text()
                },
                "ai": {
                    "provider": self.provider_combo.currentText(),
                    "api_key": encrypted_key,  # 保存加密后的 API key
                    "model": self.model_combo.currentText(),
                    "language": self.language_combo.currentText(),
                    "style": self.style_combo.currentText()
                },
                "git": {
                    "auto_commit": self.auto_commit_checkbox.isChecked(),
                    "auto_push": self.auto_push_checkbox.isChecked(),
                    "commit_message": self.commit_msg_edit.text()
                }
            }

            # 保存到文件
            config_file = Path("config/config.yaml")
            config_file.parent.mkdir(parents=True, exist_ok=True)

            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, allow_unicode=True)

            # 将保存目录添加到历史记录
            save_dir = self.save_dir_edit.text()
            if save_dir:
                self._add_to_history(save_dir)

            QMessageBox.information(self, "成功", "配置已保存\n(API Key 已加密)")
            logger.info("配置已保存到 config/config.yaml")

        except Exception as e:
            QMessageBox.critical(
                self,
                "错误",
                f"保存配置失败:\n{str(e)}"
            )
            logger.error(f"保存配置失败: {e}")

    def _reload_config(self):
        """重新加载配置"""
        try:
            import yaml
            import sys
            from pathlib import Path

            config_file = Path("config/config.yaml")
            if not config_file.exists():
                QMessageBox.warning(self, "警告", "配置文件不存在")
                return

            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)

            # 导入加密工具
            project_root = Path(__file__).parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))

            from src.crypto_utils import get_crypto_manager

            # 更新UI
            obsidian_config = self.config.get("obsidian", {})
            self.save_dir_edit.setText(obsidian_config.get("save_dir", ""))
            self.filename_format_edit.setText(
                obsidian_config.get("filename_format", "{date}_{topic}")
            )

            ai_config = self.config.get("ai", {})
            provider = ai_config.get("provider", "chatglm")
            index = self.provider_combo.findText(provider)
            if index >= 0:
                self.provider_combo.setCurrentIndex(index)

            # 解密 API key
            encrypted_key = ai_config.get("api_key", "")
            crypto_manager = get_crypto_manager()
            decrypted_key = crypto_manager.decrypt(encrypted_key)
            self.api_key_edit.setText(decrypted_key)

            if encrypted_key and encrypted_key.startswith(("encrypted:", "encoded:")):
                if crypto_manager.is_available():
                    logger.info("API key 已解密")
                else:
                    logger.warning("API key 是加密的，但 cryptography 库不可用")

            model = ai_config.get("model", "glm-4")
            index = self.model_combo.findText(model)
            if index >= 0:
                self.model_combo.setCurrentIndex(index)

            language = ai_config.get("language", "中文")
            index = self.language_combo.findText(language)
            if index >= 0:
                self.language_combo.setCurrentIndex(index)

            style = ai_config.get("style", "详细教程")
            index = self.style_combo.findText(style)
            if index >= 0:
                self.style_combo.setCurrentIndex(index)

            git_config = self.config.get("git", {})
            self.auto_commit_checkbox.setChecked(
                git_config.get("auto_commit", True)
            )
            self.auto_push_checkbox.setChecked(
                git_config.get("auto_push", True)
            )
            self.commit_msg_edit.setText(
                git_config.get("commit_message", "")
            )

            QMessageBox.information(self, "成功", "配置已重新加载")
            logger.info("配置已重新加载")

        except Exception as e:
            QMessageBox.critical(
                self,
                "错误",
                f"加载配置失败:\n{str(e)}"
            )
            logger.error(f"加载配置失败: {e}")

    def get_config(self) -> dict:
        """获取当前配置"""
        return self.config

    # ========== 目录历史记录相关方法 ==========

    def _load_dir_history(self):
        """加载目录历史记录"""
        try:
            import sys
            from pathlib import Path

            project_root = Path(__file__).parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))

            import json

            history_file = project_root / "config" / "dir_history.json"

            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    self.dir_history = json.load(f)

                # 更新下拉框
                self._update_history_combo()

                logger.info(f"已加载 {len(self.dir_history)} 条历史记录")
        except Exception as e:
            logger.error(f"加载历史记录失败: {e}")
            self.dir_history = []

    def _save_dir_history(self):
        """保存目录历史记录"""
        try:
            import sys
            from pathlib import Path

            project_root = Path(__file__).parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))

            import json

            history_file = project_root / "config" / "dir_history.json"

            # 确保config目录存在
            history_file.parent.mkdir(parents=True, exist_ok=True)

            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.dir_history, f, ensure_ascii=False, indent=2)

            logger.debug(f"已保存 {len(self.dir_history)} 条历史记录")
        except Exception as e:
            logger.error(f"保存历史记录失败: {e}")

    def _add_to_history(self, directory: str):
        """添加到历史记录"""
        # 如果已存在，先删除（为了把最新的放到前面）
        if directory in self.dir_history:
            self.dir_history.remove(directory)

        # 添加到开头
        self.dir_history.insert(0, directory)

        # 只保留最近5条
        if len(self.dir_history) > 5:
            self.dir_history = self.dir_history[:5]

        # 更新UI和保存
        self._update_history_combo()
        self._save_dir_history()

    def _update_history_combo(self):
        """更新历史记录下拉框"""
        self.dir_history_combo.clear()
        self.dir_history_combo.addItem("-- 选择历史目录 --")

        for dir_path in self.dir_history:
            # 只显示目录名，完整路径在工具提示中
            dir_name = Path(dir_path).name
            self.dir_history_combo.addItem(dir_name, dir_path)

        # 设置工具提示
        for i in range(1, self.dir_history_combo.count()):
            self.dir_history_combo.setItemData(i, self.dir_history_combo.itemData(i), Qt.ItemDataRole.ToolTipRole)

    def _on_history_selected(self, text: str):
        """历史记录选择事件"""
        if text.startswith("--"):
            return

        # 获取完整路径
        current_data = self.dir_history_combo.currentData()
        if current_data:
            self.save_dir_edit.setText(current_data)

    def _delete_history(self):
        """删除选中的历史记录"""
        current_text = self.dir_history_combo.currentText()

        if current_text.startswith("--"):
            QMessageBox.information(self, "提示", "请先选择要删除的历史记录")
            return

        reply = QMessageBox.question(
            self,
            '确认删除',
            f'确定要删除历史记录 "{current_text}" 吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 从历史记录中删除
            current_data = self.dir_history_combo.currentData()
            if current_data in self.dir_history:
                self.dir_history.remove(current_data)

            # 更新UI和保存
            self._update_history_combo()
            self._save_dir_history()

            QMessageBox.information(self, "成功", "历史记录已删除")
            logger.info(f"已删除历史记录: {current_data}")

    def _clear_history(self):
        """清空所有历史记录"""
        if not self.dir_history:
            QMessageBox.information(self, "提示", "历史记录为空")
            return

        reply = QMessageBox.question(
            self,
            '确认清空',
            '确定要清空所有历史记录吗？此操作不可恢复。',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.dir_history = []
            self._update_history_combo()
            self._save_dir_history()

            QMessageBox.information(self, "成功", "所有历史记录已清空")
            logger.info("已清空所有历史记录")

