"""
OpenAI兼容API提供者实现
支持OpenAI、Azure OpenAI以及其他兼容OpenAI API的服务
"""
from typing import Optional
import logging

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .base import BaseAIProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseAIProvider):
    """OpenAI兼容API提供者"""

    # 支持的模型列表
    AVAILABLE_MODELS = [
        "gpt-4",
        "gpt-4-turbo",
        "gpt-4o",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k"
    ]

    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo",
                 base_url: Optional[str] = None, **kwargs):
        """
        初始化OpenAI提供者

        Args:
            api_key: OpenAI API密钥
            model: 模型名称
            base_url: 自定义API地址（用于兼容API）
            **kwargs: 其他配置参数
        """
        super().__init__(api_key, model, **kwargs)

        if not OPENAI_AVAILABLE:
            raise ImportError(
                "openai包未安装，请运行: pip install openai"
            )

        try:
            client_kwargs = {"api_key": api_key}
            if base_url:
                client_kwargs["base_url"] = base_url

            self.client = openai.OpenAI(**client_kwargs)
            logger.info(f"OpenAI客户端初始化成功，使用模型: {model}")
        except Exception as e:
            logger.error(f"OpenAI客户端初始化失败: {e}")
            raise

    def generate(self, prompt: str, temperature: float = 0.7,
                 max_tokens: int = 4000, top_p: float = 0.9,
                 **kwargs) -> str:
        """
        生成文本

        Args:
            prompt: 提示词
            temperature: 温度参数
            max_tokens: 最大token数
            top_p: 核采样参数
            **kwargs: 其他参数

        Returns:
            生成的文本内容
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                **kwargs
            )

            content = response.choices[0].message.content
            logger.debug(f"OpenAI生成成功，token使用: "
                        f"{response.usage.total_tokens}")
            return content

        except Exception as e:
            logger.error(f"OpenAI生成失败: {e}")
            raise

    def generate_note(self, topic: str, language: str = "中文",
                      style: str = "详细教程", **kwargs) -> str:
        """生成学习笔记"""
        prompt = self._build_note_prompt(topic, language, style)

        try:
            content = self.generate(
                prompt=prompt,
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 4000)
            )

            logger.info(f"成功生成主题 '{topic}' 的笔记")
            return content

        except Exception as e:
            logger.error(f"生成笔记失败: {e}")
            raise

    def test_connection(self) -> bool:
        """测试API连接"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            logger.info("OpenAI连接测试成功")
            return True
        except Exception as e:
            logger.error(f"OpenAI连接测试失败: {e}")
            return False
