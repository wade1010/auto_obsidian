"""
配置路径管理模块
统一管理配置文件的存储路径
"""
import os
import shutil
from pathlib import Path
import logging
import yaml

logger = logging.getLogger(__name__)


class ConfigPathManager:
    """配置路径管理器"""

    def __init__(self):
        """初始化配置路径管理器"""
        # 获取用户目录
        self.user_home = Path.home()
        # 配置目录
        self.config_dir = self.user_home / ".auto_obsidian"
        # 配置文件路径
        self.config_file = self.config_dir / "config.yaml"
        # topics 文件路径
        self.topics_file = self.config_dir / "topics.yaml"
        # 目录历史文件
        self.dir_history_file = self.config_dir / "dir_history.json"

        # 旧的配置目录（用于迁移）
        self.old_config_dir = Path.cwd() / "config"

        logger.info(f"配置目录: {self.config_dir}")

    def ensure_config_dir(self):
        """确保配置目录存在"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"配置目录已准备: {self.config_dir}")
            return True
        except Exception as e:
            logger.error(f"创建配置目录失败: {e}")
            return False

    def migrate_old_config(self):
        """迁移旧的配置文件到新位置"""
        try:
            # 检查旧配置目录是否存在
            if not self.old_config_dir.exists():
                logger.info("未找到旧配置目录，无需迁移")
                return False

            # 检查是否已经迁移过
            if self.config_file.exists():
                logger.info("新配置文件已存在，跳过迁移")
                return False

            # 确保新配置目录存在
            self.ensure_config_dir()

            # 迁移配置文件
            old_config_file = self.old_config_dir / "config.yaml"
            if old_config_file.exists():
                shutil.copy2(old_config_file, self.config_file)
                logger.info(f"已迁移配置文件: {old_config_file} -> {self.config_file}")

            # 迁移 topics 文件
            old_topics_file = self.old_config_dir / "topics.yaml"
            if old_topics_file.exists():
                shutil.copy2(old_topics_file, self.topics_file)
                logger.info(f"已迁移 topics 文件: {old_topics_file} -> {self.topics_file}")

            # 迁移历史记录文件
            old_history_file = self.old_config_dir / "dir_history.json"
            if old_history_file.exists():
                shutil.copy2(old_history_file, self.dir_history_file)
                logger.info(f"已迁移历史记录文件: {old_history_file} -> {self.dir_history_file}")

            logger.info("旧配置文件迁移完成")
            return True

        except Exception as e:
            logger.error(f"迁移配置文件失败: {e}")
            return False

    def create_default_topics(self):
        """创建默认的 topics.yaml 文件"""
        try:
            # 如果文件已存在，不覆盖
            if self.topics_file.exists():
                logger.info("topics.yaml 已存在，跳过创建")
                return False

            # 确保配置目录存在
            self.ensure_config_dir()

            # 默认的 AI 学习主题
            default_topics = {
                "机器学习基础": [
                    "监督学习与非监督学习",
                    "过拟合与欠拟合",
                    "交叉验证",
                    "偏差与方差",
                    "特征工程"
                ],
                "深度学习": [
                    "神经网络基础",
                    "反向传播算法",
                    "卷积神经网络 (CNN)",
                    "循环神经网络 (RNN)",
                    "Transformer 架构",
                    "注意力机制",
                    "BERT 模型",
                    "GPT 系列"
                ],
                "优化算法": [
                    "梯度下降 (SGD, Adam, AdamW)",
                    "学习率调度",
                    "正则化技术",
                    "批归一化"
                ],
                "强化学习": [
                    "Q-Learning",
                    "策略梯度",
                    "Actor-Critic",
                    "PPO (Proximal Policy Optimization)"
                ],
                "自然语言处理": [
                    "词嵌入 (Word Embeddings)",
                    "Seq2Seq 模型",
                    "注意力机制",
                    "预训练语言模型",
                    "文本生成",
                    "情感分析"
                ],
                "计算机视觉": [
                    "图像分类",
                    "目标检测",
                    "图像分割",
                    "风格迁移",
                    "图像生成 (GAN)"
                ],
                "大模型技术": [
                    "RLHF人类反馈强化学习",
                    "指令微调",
                    "思维链 (Chain of Thought)",
                    "模型量化",
                    "LoRA 微调"
                ],
                "MLOps": [
                    "模型部署",
                    "A/B 测试",
                    "模型监控",
                    "数据版本管理"
                ]
            }

            # 写入文件
            with open(self.topics_file, 'w', encoding='utf-8') as f:
                yaml.dump(default_topics, f, allow_unicode=True, sort_keys=False)

            logger.info(f"已创建默认 topics.yaml 文件: {self.topics_file}")
            return True

        except Exception as e:
            logger.error(f"创建默认 topics.yaml 失败: {e}")
            return False

    def initialize_on_first_run(self):
        """首次运行时初始化配置"""
        try:
            logger.info("首次运行，开始初始化配置...")

            # 1. 创建配置目录
            if not self.ensure_config_dir():
                logger.error("创建配置目录失败")
                return False

            # 2. 尝试迁移旧配置（如果存在）
            migrated = self.migrate_old_config()

            # 3. 如果没有迁移到 topics 文件，创建默认的
            if not migrated or not self.topics_file.exists():
                self.create_default_topics()

            # 注意：不创建默认的 config.yaml 和 dir_history.json
            # 这些文件应该由用户在配置时自动创建

            logger.info("首次运行初始化完成")
            return True

        except Exception as e:
            logger.error(f"首次运行初始化失败: {e}")
            return False

    def create_default_config(self):
        """创建默认配置文件"""
        try:
            default_config = {
                "obsidian": {
                    "save_dir": "",
                    "filename_format": "{date}_{topic}"
                },
                "ai": {
                    "provider": "chatglm",
                    "api_key": "",
                    "model": "glm-4.7",
                    "language": "中文",
                    "style": "详细教程"
                },
                "git": {
                    "auto_commit": True,
                    "auto_push": True,
                    "commit_message": "docs: 自动生成AI学习笔记 - {date}"
                }
            }

            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, allow_unicode=True)

            logger.info(f"已创建默认配置文件: {self.config_file}")
            return True

        except Exception as e:
            logger.error(f"创建默认配置文件失败: {e}")
            return False

    def get_config_file(self) -> Path:
        """获取配置文件路径"""
        return self.config_file

    def get_topics_file(self) -> Path:
        """获取 topics 文件路径"""
        return self.topics_file

    def get_dir_history_file(self) -> Path:
        """获取目录历史文件路径"""
        return self.dir_history_file

    def is_first_run(self) -> bool:
        """检查是否是首次运行"""
        return not self.config_file.exists()


# 全局单例
_config_path_manager = None


def get_config_path_manager() -> ConfigPathManager:
    """获取配置路径管理器单例"""
    global _config_path_manager
    if _config_path_manager is None:
        _config_path_manager = ConfigPathManager()
    return _config_path_manager
