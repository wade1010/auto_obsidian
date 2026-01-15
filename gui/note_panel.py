"""
笔记生成面板模块
用于手动生成笔记
"""
import logging
from typing import List

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QGroupBox, QTextEdit,
    QComboBox, QMessageBox, QProgressDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)


class GenerateThread(QThread):
    """笔记生成线程"""

    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    stream_chunk = pyqtSignal(str)  # 流式输出信号，每次传递生成的文本块

    def __init__(self, note_generator, topic: str,
                 language: str, style: str, use_stream: bool = True):
        super().__init__()
        self.note_generator = note_generator
        self.topic = topic
        self.language = language
        self.style = style
        self.use_stream = use_stream  # 是否使用流式输出

    def run(self):
        """执行生成"""
        try:
            logger.info(f"[GenerateThread] 线程启动，开始生成: {self.topic}")
            self.progress.emit(f"正在生成 '{self.topic}' 的笔记...")

            if self.use_stream:
                # 流式生成模式
                logger.info(f"[GenerateThread] 使用流式生成模式")
                full_content = ""

                # 调用 AI 生成器的流式接口
                stream_generator = self.note_generator.ai_provider.generate(
                    prompt=self.note_generator.ai_provider._build_note_prompt(
                        self.topic, self.language, self.style
                    ),
                    temperature=0.7,
                    max_tokens=4000,
                    stream=True
                )

                # 逐块接收并发送内容
                for chunk in stream_generator:
                    full_content += chunk
                    self.stream_chunk.emit(chunk)

                # 构建结果字典
                result = {
                    "topic": self.topic,
                    "language": self.language,
                    "style": self.style,
                    "model": self.note_generator.model,
                    "content": full_content,
                    "success": True,
                    "word_count": len(full_content)
                }

                logger.info(f"[GenerateThread] 流式生成完成，字数: {len(full_content)}")
                self.finished.emit(result)

            else:
                # 非流式模式（原有逻辑）
                logger.info(f"[GenerateThread] 调用 note_generator.generate()...")
                result = self.note_generator.generate(
                    topic=self.topic,
                    language=self.language,
                    style=self.style
                )

                logger.info(f"[GenerateThread] 生成完成，success={result.get('success')}")
                self.finished.emit(result)

        except Exception as e:
            logger.error(f"[GenerateThread] 生成失败: {e}")
            self.error.emit(str(e))


class NotePanel(QWidget):
    """笔记生成面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.topics = []
        self._init_ui()
        self._load_topics()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)

        # 生成模式组
        mode_group = self._create_mode_group()
        layout.addWidget(mode_group)

        # 预览组
        preview_group = self._create_preview_group()
        layout.addWidget(preview_group)

        # 操作按钮
        btn_layout = QHBoxLayout()
        self.generate_btn = QPushButton("生成笔记")
        self.generate_btn.clicked.connect(self._generate_note)
        self.save_btn = QPushButton("保存到Obsidian")
        self.save_btn.clicked.connect(self._save_note)
        self.save_btn.setEnabled(False)
        self.open_folder_btn = QPushButton("打开文件夹")
        self.open_folder_btn.clicked.connect(self._open_folder)

        btn_layout.addWidget(self.generate_btn)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.open_folder_btn)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)
        layout.addStretch()

        # 当前生成的笔记
        self.current_note = None

    def _create_mode_group(self) -> QGroupBox:
        """创建生成模式组"""
        group = QGroupBox("生成笔记")
        layout = QVBoxLayout()

        # 单主题生成
        single_layout = QHBoxLayout()
        single_layout.addWidget(QLabel("主题:"))
        self.topic_edit = QLineEdit()
        self.topic_edit.setPlaceholderText("输入AI技术主题，例如: Transformer架构")
        single_layout.addWidget(self.topic_edit)

        # 预设主题选择
        self.topic_combo = QComboBox()
        self.topic_combo.currentTextChanged.connect(self._on_topic_selected)
        self.topic_combo.setMinimumWidth(200)
        single_layout.addWidget(self.topic_combo)

        layout.addLayout(single_layout)

        # 语言和风格
        options_layout = QHBoxLayout()
        options_layout.addWidget(QLabel("语言:"))
        self.language_combo = QComboBox()
        self.language_combo.addItems(["中文", "English"])
        options_layout.addWidget(self.language_combo)

        options_layout.addWidget(QLabel("风格:"))
        self.style_combo = QComboBox()
        self.style_combo.addItems([
            "详细教程",
            "简洁概述",
            "深度解析",
            "实战指南"
        ])
        options_layout.addWidget(self.style_combo)
        options_layout.addStretch()

        layout.addLayout(options_layout)

        group.setLayout(layout)
        return group

    def _create_preview_group(self) -> QGroupBox:
        """创建预览组"""
        group = QGroupBox("生成预览")
        layout = QVBoxLayout()

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlaceholderText(
            "生成的笔记内容将显示在这里..."
        )
        layout.addWidget(self.preview_text)

        group.setLayout(layout)
        return group

    def _load_topics(self):
        """加载预设主题"""
        try:
            import yaml

            topics_file = "config/topics.yaml"
            with open(topics_file, 'r', encoding='utf-8') as f:
                topics_data = yaml.safe_load(f)

            # 提取所有主题
            all_topics = []
            for category, topic_list in topics_data.items():
                for topic in topic_list:
                    all_topics.append(f"[{category}] {topic}")

            self.topic_combo.clear()
            self.topic_combo.addItem("-- 选择预设主题 --")
            self.topic_combo.addItems(all_topics)

            self.topics = all_topics
            logger.info(f"已加载 {len(all_topics)} 个预设主题")

        except Exception as e:
            logger.error(f"加载主题失败: {e}")

    def _on_topic_selected(self, text: str):
        """主题选择改变事件"""
        if text.startswith("--"):
            return

        # 提取主题名称（去掉分类前缀）
        if "] " in text:
            topic = text.split("] ", 1)[1]
            self.topic_edit.setText(topic)

    def _generate_note(self):
        """生成笔记"""
        topic = self.topic_edit.text().strip()

        if not topic:
            QMessageBox.warning(self, "警告", "请输入或选择一个主题")
            return

        # 获取主窗口
        main_window = self._get_main_window()

        if not main_window:
            QMessageBox.warning(
                self,
                "警告",
                "无法访问主窗口，请重新启动程序"
            )
            logger.error("无法获取main_window对象")
            return

        if not main_window.note_generator:
            QMessageBox.warning(
                self,
                "警告",
                "系统未初始化，请先在配置面板中设置API Key"
            )
            return

        language = self.language_combo.currentText()
        style = self.style_combo.currentText()

        logger.info(f"[_generate_note] 准备生成笔记: topic={topic}, language={language}, style={style}")
        logger.info(f"[_generate_note] note_generator: {main_window.note_generator}")

        # 禁用生成按钮
        self.generate_btn.setEnabled(False)
        self.generate_btn.setText("生成中...")

        # 清空预览区域
        self.preview_text.clear()
        self.current_note = None
        self.save_btn.setEnabled(False)

        try:
            # 创建生成线程（使用流式输出）
            logger.info(f"[_generate_note] 创建 GenerateThread...")
            self.generate_thread = GenerateThread(
                main_window.note_generator,
                topic,
                language,
                style,
                use_stream=True  # 启用流式输出
            )

            logger.info(f"[_generate_note] 连接信号...")
            self.generate_thread.progress.connect(self._on_progress)
            self.generate_thread.finished.connect(self._on_finished)
            self.generate_thread.error.connect(self._on_error)
            self.generate_thread.stream_chunk.connect(self._on_stream_chunk)  # 连接流式信号

            logger.info(f"[_generate_note] 启动线程...")
            self.generate_thread.start()
            logger.info(f"[_generate_note] 线程已启动")

        except Exception as e:
            self.generate_btn.setEnabled(True)
            self.generate_btn.setText("生成笔记")
            QMessageBox.critical(
                self,
                "错误",
                f"启动生成线程失败:\n{str(e)}"
            )
            logger.error(f"启动生成线程失败: {e}")

    def _get_main_window(self):
        """获取主窗口对象"""
        try:
            # 方法1: 通过parent链
            parent = self.parent()
            if parent:
                main_window = parent.parent()
                if hasattr(main_window, 'note_generator'):
                    return main_window

            # 方法2: 通过QApplication
            from PyQt5.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                widgets = app.topLevelWidgets()
                for widget in widgets:
                    if hasattr(widget, 'note_generator'):
                        return widget

            return None
        except Exception as e:
            logger.error(f"获取main_window失败: {e}")
            return None

    def _on_progress(self, message: str):
        """生成进度更新"""
        logger.info(message)

    def _on_stream_chunk(self, chunk: str):
        """实时显示流式输出的文本块"""
        # 在预览区域追加内容
        cursor = self.preview_text.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(chunk)
        # 自动滚动到底部
        self.preview_text.setTextCursor(cursor)
        self.preview_text.ensureCursorVisible()

    def _on_finished(self, result: dict):
        """生成完成"""
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("生成笔记")

        if result.get("success"):
            # 流式模式下内容已经逐步显示，这里只需要保存结果
            content = result.get("content", "")
            # 如果是非流式模式，需要设置内容
            if not self.preview_text.toPlainText():
                self.preview_text.setPlainText(content)

            self.current_note = result
            self.save_btn.setEnabled(True)

            word_count = result.get("word_count", 0)
            QMessageBox.information(
                self,
                "成功",
                f"笔记生成成功！\n字数: {word_count}"
            )
            logger.info(f"笔记生成成功: {result.get('topic')}")
        else:
            error = result.get("error", "未知错误")
            QMessageBox.critical(
                self,
                "失败",
                f"笔记生成失败:\n{error}"
            )
            logger.error(f"笔记生成失败: {error}")

    def _on_error(self, error: str):
        """生成错误"""
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("生成笔记")

        QMessageBox.critical(
            self,
            "错误",
            f"生成过程出错:\n{error}"
        )
        logger.error(f"生成过程出错: {error}")

    def _save_note(self):
        """保存笔记"""
        if not self.current_note:
            QMessageBox.warning(self, "警告", "没有可保存的笔记")
            return

        main_window = self._get_main_window()

        if not main_window:
            QMessageBox.warning(self, "警告", "无法访问主窗口，请重新启动程序")
            logger.error("无法获取main_window对象")
            return

        if not main_window.file_manager:
            QMessageBox.warning(self, "警告", "文件管理器未初始化")
            return

        try:
            result = main_window.file_manager.save(
                content=self.current_note.get("content", ""),
                topic=self.current_note.get("topic", "未命名")
            )

            if result.get("success"):
                filepath = result.get("filepath")
                file_size = result.get("size", 0)

                # Git提交
                if main_window.git_manager:
                    git_result = main_window.git_manager.commit_and_push(
                        [filepath],
                        topic=self.current_note.get("topic", ""),
                        count=1
                    )

                    if git_result.get("success"):
                        QMessageBox.information(
                            self,
                            "成功",
                            f"笔记已保存并提交到Git！\n"
                            f"路径: {filepath}\n"
                            f"大小: {file_size} 字节"
                        )
                    else:
                        QMessageBox.warning(
                            self,
                            "部分成功",
                            f"笔记已保存，但Git操作失败\n"
                            f"路径: {filepath}\n"
                            f"错误: {git_result.get('error')}"
                        )
                else:
                    QMessageBox.information(
                        self,
                        "成功",
                        f"笔记已保存！\n路径: {filepath}"
                    )

                logger.info(f"笔记已保存: {filepath}")

            else:
                error = result.get("error", "未知错误")
                QMessageBox.critical(
                    self,
                    "失败",
                    f"保存笔记失败:\n{error}"
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "错误",
                f"保存过程出错:\n{str(e)}"
            )
            logger.error(f"保存笔记失败: {e}")

    def _open_folder(self):
        """打开保存文件夹"""
        main_window = self._get_main_window()

        if not main_window:
            QMessageBox.warning(self, "警告", "无法访问主窗口，请重新启动程序")
            logger.error("无法获取main_window对象")
            return

        if not main_window.file_manager:
            QMessageBox.warning(self, "警告", "文件管理器未初始化")
            return

        try:
            main_window.file_manager.open_directory()

        except Exception as e:
            QMessageBox.critical(
                self,
                "错误",
                f"打开文件夹失败:\n{str(e)}"
            )
            logger.error(f"打开文件夹失败: {e}")
