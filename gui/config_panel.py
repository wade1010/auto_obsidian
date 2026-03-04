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

    # 各服务商预设模型
    PROVIDER_MODELS = {
        "chatglm": [
            "glm-4.7",
            "glm-4.7-flash",
            "glm-4-plus",
            "glm-4-flash",
            "glm-4-air",
            "glm-4-airx",
            "glm-4-long",
            "glm-3-turbo"
        ],
        "openai": [
            "gpt-4.5-preview",
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo"
        ],
        "volcengine": [
            "ark-code-latest",
            "doubao-seed-latest",
            "doubao-seed-2-5-251215",
            "doubao-pro-256k-vision",
            "doubao-pro-32k-vision",
            "doubao-pro-vision",
            "doubao-pro-256k",
            "doubao-pro-32k",
            "doubao-pro",
            "doubao-lite-vision",
            "doubao-lite-256k",
            "doubao-lite-32k",
            "doubao-lite",
            "doubao-turbo-vision",
            "doubao-turbo-256k",
            "doubao-turbo-32k",
            "doubao-turbo"
        ],
        "minimax": [
            "abab6.5s",
            "abab6.5g",
            "abab6.5t",
            "abab6.5",
            "abab6",
            "abab5.5s"
        ]
    }

    # 各服务商默认Base URL
    PROVIDER_DEFAULT_URLS = {
        "chatglm": "",
        "openai": "",
        "volcengine": "https://ark.cn-beijing.volces.com/api/v3",
        "minimax": "https://api.minimax.chat/v1"
    }

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
        self.provider_combo.addItems(["chatglm", "openai", "volcengine", "minimax"])
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
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

        # Base URL（可选）
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("Base URL:"))
        self.base_url_edit = QLineEdit()
        self.base_url_edit.setPlaceholderText("留空使用默认地址，或输入自定义API地址")
        url_layout.addWidget(self.base_url_edit)
        layout.addLayout(url_layout)

        # 模型选择（可编辑）
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("模型:"))
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)  # 允许手动输入
        self.model_combo.addItems(self.PROVIDER_MODELS["chatglm"])
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

    def _on_provider_changed(self, provider: str):
        """服务商切换时更新模型列表和默认Base URL"""
        logger.info(f"[_on_provider_changed] 服务商切换为: {provider}")
        try:
            # 更新模型列表
            current_model = self.model_combo.currentText()
            logger.info(f"[_on_provider_changed] 当前模型: {current_model}")
            
            self.model_combo.clear()
            models = self.PROVIDER_MODELS.get(provider, [])
            logger.info(f"[_on_provider_changed] 加载 {len(models)} 个模型")
            self.model_combo.addItems(models)
            
            # 如果当前模型在新列表中，保持选中；否则选择第一个
            if current_model in models:
                index = self.model_combo.findText(current_model)
                if index >= 0:
                    self.model_combo.setCurrentIndex(index)
                    logger.info(f"[_on_provider_changed] 保持选中模型: {current_model}")
            elif models:
                self.model_combo.setCurrentIndex(0)
                logger.info(f"[_on_provider_changed] 选中第一个模型: {models[0]}")
            
            # 如果Base URL为空，设置默认值
            if not self.base_url_edit.text().strip():
                default_url = self.PROVIDER_DEFAULT_URLS.get(provider, "")
                self.base_url_edit.setText(default_url)
                logger.info(f"[_on_provider_changed] 设置默认 base_url: {default_url}")
            else:
                logger.info(f"[_on_provider_changed] 保持用户自定义 base_url")
                
            logger.info(f"[_on_provider_changed] 服务商切换完成")
        except Exception as e:
            logger.error(f"[_on_provider_changed] 服务商切换出错: {e}", exc_info=True)
            raise
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
        logger.info("[_test_connection] 开始测试API连接")
        api_key = self.api_key_edit.text()
        provider = self.provider_combo.currentText()
        model = self.model_combo.currentText()
        base_url = self.base_url_edit.text().strip() or None  # 获取 base_url
        
        logger.info(f"[_test_connection] 参数 - provider: {provider}, model: {model}, base_url: {base_url}")

        if not api_key:
            logger.warning("[_test_connection] API Key为空")
            QMessageBox.warning(self, "警告", "请先输入API Key")
            return
        
        logger.info("[_test_connection] API Key已提供")

        try:
            logger.info("[_test_connection] 准备导入模块...")
            import sys
            from pathlib import Path

            # 添加项目根目录到路径
            project_root = Path(__file__).parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
            logger.info(f"[_test_connection] 项目根目录: {project_root}")

            logger.info("[_test_connection] 导入NoteGenerator...")
            from src.note_generator import NoteGenerator
            logger.info("[_test_connection] NoteGenerator导入成功")

            # 准备额外配置参数
            extra_config = {}
            if base_url:
                extra_config['base_url'] = base_url
                logger.info(f"[_test_connection] 使用自定义 base_url: {base_url}")
            
            logger.info("[_test_connection] 创建NoteGenerator实例...")
            # 创建临时生成器进行测试
            generator = NoteGenerator(
                provider_name=provider,
                api_key=api_key,
                model=model,
                **extra_config  # 传递 base_url
            )
            logger.info("[_test_connection] NoteGenerator创建成功")
            
            logger.info("[_test_connection] 开始连接测试...")
            if generator.test_connection():
                logger.info("[_test_connection] 连接测试成功")
                base_url_info = f"\nAPI地址: {base_url}" if base_url else ""
                QMessageBox.information(
                    self,
                    "成功",
                    f"连接测试成功！\n服务商: {provider}\n模型: {model}{base_url_info}"
                )
                logger.info("API连接测试成功")
            else:
                logger.warning("[_test_connection] 连接测试失败")
                QMessageBox.critical(
                    self,
                    "失败",
                    "连接测试失败，请检查API Key和网络连接"
                )
            
        except ImportError as e:
            logger.error(f"[_test_connection] 导入模块失败: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "错误",
                f"导入模块失败:\n{str(e)}"
            )
        except Exception as e:
            logger.error(f"[_test_connection] API连接测试失败: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "错误",
                f"连接测试出错:\n{str(e)}"
            )
    def _save_config(self):
        """保存配置"""
        try:
            import yaml
            import sys
            from pathlib import Path

            # 导入加密工具和配置路径管理器
            project_root = Path(__file__).parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))

            from src.crypto_utils import get_crypto_manager
            from src.config_manager import get_config_path_manager

            # ========== 验证必填字段 ==========
            errors = []

            # 1. 验证 API Key
            api_key = self.api_key_edit.text().strip()
            if not api_key:
                errors.append("API Key 不能为空")

            # 2. 验证保存目录
            save_dir = self.save_dir_edit.text().strip()
            if not save_dir:
                errors.append("保存目录不能为空")
            elif not Path(save_dir).exists():
                errors.append(f"保存目录不存在:\n{save_dir}")

            # 3. 验证文件名格式
            filename_format = self.filename_format_edit.text().strip()
            if not filename_format:
                errors.append("文件名格式不能为空")

            # 如果有错误，显示并返回
            if errors:
                QMessageBox.warning(
                    self,
                    "配置验证失败",
                    "以下配置项需要修正:\n\n" + "\n".join(f"• {error}" for error in errors)
                )
                logger.warning(f"配置验证失败: {errors}")
                return

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
                    "save_dir": save_dir,
                    "filename_format": filename_format
                },
                "ai": {
                    "provider": self.provider_combo.currentText(),
                    "api_key": encrypted_key,  # 保存加密后的 API key
                    "base_url": self.base_url_edit.text().strip() or None,  # 可选，空字符串则不保存
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

            # 获取配置文件路径并保存
            config_path_manager = get_config_path_manager()
            config_file = config_path_manager.get_config_file()
            config_file.parent.mkdir(parents=True, exist_ok=True)

            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, allow_unicode=True)

            # 将保存目录添加到历史记录
            self._add_to_history(save_dir)

            QMessageBox.information(self, "成功", "配置已保存\n(API Key 已加密)")
            logger.info(f"配置已保存到 {config_file}")

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

            # 导入加密工具和配置路径管理器
            project_root = Path(__file__).parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))

            from src.crypto_utils import get_crypto_manager
            from src.config_manager import get_config_path_manager

            # 获取配置文件路径
            config_path_manager = get_config_path_manager()
            config_file = config_path_manager.get_config_file()

            if not config_file.exists():
                QMessageBox.warning(self, "警告", f"配置文件不存在\n{config_file}")
                return

            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)

            # 更新UI - 注意：先禁用信号，避免触发_on_provider_changed
            obsidian_config = self.config.get("obsidian", {})
            self.save_dir_edit.setText(obsidian_config.get("save_dir", ""))
            self.filename_format_edit.setText(
                obsidian_config.get("filename_format", "{date}_{topic}")
            )

            ai_config = self.config.get("ai", {})
            provider = ai_config.get("provider", "chatglm")
            model = ai_config.get("model", "glm-4")
            base_url = ai_config.get("base_url", "")
            
            logger.info(f"[_reload_config] 从配置文件读取: provider={provider}, model={model}")
            
            # 先临时断开信号，避免重复触发
            try:
                self.provider_combo.currentTextChanged.disconnect(self._on_provider_changed)
            except:
                pass
            
            # 设置服务商
            index = self.provider_combo.findText(provider)
            if index >= 0:
                self.provider_combo.setCurrentIndex(index)
            
            # 手动更新模型列表
            self.model_combo.clear()
            models = self.PROVIDER_MODELS.get(provider, [])
            self.model_combo.addItems(models)
            logger.info(f"[_reload_config] 加载 {len(models)} 个模型")
            
            # 设置模型
            index = self.model_combo.findText(model)
            if index >= 0:
                self.model_combo.setCurrentIndex(index)
                logger.info(f"[_reload_config] 设置模型: {model}")
            else:
                self.model_combo.addItem(model)
                self.model_combo.setCurrentText(model)
                logger.info(f"[_reload_config] 添加并设置新模型: {model}")
            
            # 重新连接信号
            self.provider_combo.currentTextChanged.connect(self._on_provider_changed)

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

            # 加载 base_url（可选）
            self.base_url_edit.setText(base_url)
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
            from src.config_manager import get_config_path_manager

            # 获取历史记录文件路径
            config_path_manager = get_config_path_manager()
            history_file = config_path_manager.get_dir_history_file()

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
            from src.config_manager import get_config_path_manager

            # 获取历史记录文件路径
            config_path_manager = get_config_path_manager()
            history_file = config_path_manager.get_dir_history_file()

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

