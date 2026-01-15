"""
文件管理器模块
负责保存笔记到Obsidian目录
"""
import os
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


logger = logging.getLogger(__name__)


class FileManager:
    """文件管理器"""

    def __init__(self, save_dir: str,
                 filename_format: str = "{date}_{topic}"):
        """
        初始化文件管理器

        Args:
            save_dir: 保存目录（绝对路径）
            filename_format: 文件名格式模板
                可用变量: {date}, {topic}, {datetime}, {timestamp}
        """
        self.save_dir = Path(save_dir)
        self.filename_format = filename_format

        # 确保保存目录存在
        self._ensure_directory()

    def _ensure_directory(self):
        """确保保存目录存在"""
        try:
            self.save_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"保存目录已确认: {self.save_dir}")
        except Exception as e:
            logger.error(f"创建保存目录失败: {e}")
            raise

    def _sanitize_filename(self, filename: str) -> str:
        """
        清理文件名，移除不合法字符

        Args:
            filename: 原始文件名

        Returns:
            清理后的文件名
        """
        # 移除或替换不合法字符
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # 移除控制字符
        filename = re.sub(r'[\x00-\x1f\x7f]', '', filename)
        # 限制长度
        if len(filename) > 200:
            filename = filename[:200]

        return filename.strip()

    def _generate_filename(self, topic: str,
                          date_format: str = "%Y-%m-%d") -> str:
        """
        生成文件名

        Args:
            topic: 笔记主题
            date_format: 日期格式

        Returns:
            文件名（不含扩展名）
        """
        now = datetime.now()

        # 准备模板变量
        variables = {
            "date": now.strftime(date_format),
            "datetime": now.strftime("%Y%m%d_%H%M%S"),
            "timestamp": str(int(now.timestamp())),
            "topic": topic
        }

        # 应用文件名格式
        filename = self.filename_format.format(**variables)

        # 清理文件名
        filename = self._sanitize_filename(filename)

        return filename

    def _create_frontmatter(self, metadata: Dict[str, Any]) -> str:
        """
        创建Obsidian frontmatter（元数据）

        Args:
            metadata: 元数据字典

        Returns:
            YAML格式的frontmatter
        """
        lines = ["---"]

        for key, value in metadata.items():
            if isinstance(value, str):
                lines.append(f"{key}: \"{value}\"")
            elif isinstance(value, list):
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"  - {item}")
            elif isinstance(value, bool):
                lines.append(f"{key}: {str(value).lower()}")
            else:
                lines.append(f"{key}: {value}")

        lines.append("---")
        lines.append("")

        return "\n".join(lines)

    def save(self, content: str, topic: str,
             metadata: Optional[Dict[str, Any]] = None,
             create_frontmatter: bool = True) -> Dict[str, Any]:
        """
        保存笔记内容到文件

        Args:
            content: Markdown内容
            topic: 笔记主题
            metadata: 额外的元数据
            create_frontmatter: 是否创建frontmatter

        Returns:
            保存结果字典
            {
                "success": True/False,
                "filepath": "文件路径",
                "filename": "文件名",
                "size": 文件大小,
                "error": "错误信息(如果失败)"
            }
        """
        result = {
            "success": False,
            "topic": topic
        }

        try:
            # 生成文件名
            filename = self._generate_filename(topic)
            filepath = self.save_dir / f"{filename}.md"

            # 如果文件已存在，添加数字后缀
            counter = 1
            while filepath.exists():
                filepath = self.save_dir / f"{filename}_{counter}.md"
                counter += 1

            # 准备文件内容
            file_content = content

            if create_frontmatter:
                # 准备元数据
                frontmatter_data = {
                    "title": topic,
                    "created": datetime.now().isoformat(),
                    "tags": ["AI", "学习笔记", topic],
                    "category": "AI技术"
                }

                if metadata:
                    frontmatter_data.update(metadata)

                # 添加frontmatter
                frontmatter = self._create_frontmatter(frontmatter_data)
                file_content = frontmatter + "\n" + content

            # 写入文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(file_content)

            # 获取文件信息
            file_size = filepath.stat().st_size

            result.update({
                "success": True,
                "filepath": str(filepath),
                "filename": filepath.name,
                "size": file_size
            })

            logger.info(
                f"笔记已保存: {filepath} "
                f"({file_size} bytes)"
            )

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"保存笔记失败: {e}")

        return result

    def save_batch(self, notes: list) -> list:
        """
        批量保存笔记

        Args:
            notes: 笔记列表，每个元素是包含content和topic的字典

        Returns:
            保存结果列表
        """
        results = []

        logger.info(f"开始批量保存 {len(notes)} 篇笔记")

        for note in notes:
            result = self.save(
                content=note.get("content", ""),
                topic=note.get("topic", "未命名")
            )
            results.append(result)

        success_count = sum(1 for r in results if r["success"])
        logger.info(
            f"批量保存完成: 成功 {success_count}/{len(notes)}"
        )

        return results

    def list_notes(self) -> list:
        """
        列出目录中的所有笔记

        Returns:
            笔记文件列表
        """
        try:
            notes = list(self.save_dir.glob("*.md"))
            logger.info(f"找到 {len(notes)} 篇笔记")
            return notes
        except Exception as e:
            logger.error(f"列出笔记失败: {e}")
            return []

    def open_directory(self):
        """
        在文件管理器中打开保存目录
        """
        try:
            if os.name == 'nt':  # Windows
                os.startfile(str(self.save_dir))
            elif os.name == 'posix':  # macOS and Linux
                import subprocess
                opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
                subprocess.call([opener, str(self.save_dir)])

            logger.info(f"已打开目录: {self.save_dir}")

        except Exception as e:
            logger.error(f"打开目录失败: {e}")

    def update_save_dir(self, new_dir: str):
        """
        更新保存目录

        Args:
            new_dir: 新的保存目录路径
        """
        self.save_dir = Path(new_dir)
        self._ensure_directory()
        logger.info(f"保存目录已更新: {self.save_dir}")
