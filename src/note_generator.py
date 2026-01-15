"""
笔记生成器模块
协调AI提供者生成学习笔记
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from .ai_providers import ChatGLMProvider, OpenAIProvider
from .ai_providers.base import BaseAIProvider

logger = logging.getLogger(__name__)


class NoteGenerator:
    """笔记生成器"""

    # 支持的AI提供者
    PROVIDERS = {
        "chatglm": ChatGLMProvider,
        "openai": OpenAIProvider,
    }

    def __init__(self, provider_name: str, api_key: str,
                 model: str, **config):
        """
        初始化笔记生成器

        Args:
            provider_name: AI提供者名称 (chatglm, openai)
            api_key: API密钥
            model: 模型名称
            **config: 其他配置参数
        """
        self.provider_name = provider_name
        self.api_key = api_key
        self.model = model
        self.config = config

        # 初始化AI提供者
        self.ai_provider = self._create_provider()

    def _create_provider(self) -> BaseAIProvider:
        """
        创建AI提供者实例

        Returns:
            AI提供者实例
        """
        provider_class = self.PROVIDERS.get(self.provider_name)

        if not provider_class:
            raise ValueError(
                f"不支持的AI提供者: {self.provider_name}，"
                f"支持的提供者: {', '.join(self.PROVIDERS.keys())}"
            )

        try:
            provider = provider_class(
                api_key=self.api_key,
                model=self.model,
                **self.config
            )
            logger.info(
                f"成功创建AI提供者: {self.provider_name} ({self.model})"
            )
            return provider

        except Exception as e:
            logger.error(f"创建AI提供者失败: {e}")
            raise

    def generate(self, topic: str,
                 language: str = "中文",
                 style: str = "详细教程",
                 **kwargs) -> Dict[str, Any]:
        """
        生成学习笔记

        Args:
            topic: 学习主题
            language: 笔记语言
            style: 笔记风格
            **kwargs: 其他参数

        Returns:
            包含生成结果和元数据的字典
            {
                "content": "笔记内容",
                "topic": "主题",
                "language": "语言",
                "style": "风格",
                "model": "使用的模型",
                "timestamp": "生成时间",
                "success": True/False,
                "error": "错误信息(如果失败)"
            }
        """
        result = {
            "topic": topic,
            "language": language,
            "style": style,
            "model": self.model,
            "timestamp": datetime.now().isoformat(),
            "success": False
        }

        try:
            logger.info(f"开始生成笔记: {topic}")

            # 调用AI提供者生成笔记
            content = self.ai_provider.generate_note(
                topic=topic,
                language=language,
                style=style,
                **kwargs
            )

            result["content"] = content
            result["success"] = True
            result["word_count"] = len(content)

            logger.info(
                f"笔记生成成功: {topic} "
                f"({result['word_count']} 字)"
            )

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"笔记生成失败: {topic}, 错误: {e}")

        return result

    def generate_batch(self, topics: list,
                       language: str = "中文",
                       style: str = "详细教程",
                       **kwargs) -> list:
        """
        批量生成学习笔记

        Args:
            topics: 主题列表
            language: 笔记语言
            style: 笔记风格
            **kwargs: 其他参数

        Returns:
            生成结果列表
        """
        results = []

        logger.info(f"开始批量生成 {len(topics)} 篇笔记")

        for i, topic in enumerate(topics, 1):
            logger.info(f"进度: {i}/{len(topics)} - {topic}")

            result = self.generate(
                topic=topic,
                language=language,
                style=style,
                **kwargs
            )

            results.append(result)

        # 统计结果
        success_count = sum(1 for r in results if r["success"])
        logger.info(
            f"批量生成完成: 成功 {success_count}/{len(topics)}"
        )

        return results

    def test_connection(self) -> bool:
        """
        测试AI服务连接

        Returns:
            连接是否成功
        """
        try:
            if hasattr(self.ai_provider, 'test_connection'):
                return self.ai_provider.test_connection()

            # 如果提供者没有test_connection方法，使用简单测试
            test_result = self.ai_provider.generate(
                prompt="测试连接",
                max_tokens=10
            )
            return bool(test_result)

        except Exception as e:
            logger.error(f"连接测试失败: {e}")
            return False

    def update_config(self, **kwargs):
        """
        更新配置

        Args:
            **kwargs: 要更新的配置参数
        """
        for key, value in kwargs.items():
            if key == "api_key":
                self.api_key = value
            elif key == "model":
                self.model = value
            elif key == "provider":
                self.provider_name = value
                # 重新创建AI提供者
                self.ai_provider = self._create_provider()

        logger.info(f"配置已更新: {kwargs}")
