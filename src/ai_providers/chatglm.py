"""
ChatGLM AI提供者实现
使用智谱AI的GLM系列模型
"""
from typing import Optional
import logging

try:
    from zhipuai import ZhipuAI
    CHATGLM_AVAILABLE = True
except ImportError:
    CHATGLM_AVAILABLE = False

from .base import BaseAIProvider

logger = logging.getLogger(__name__)


class ChatGLMProvider(BaseAIProvider):
    """ChatGLM (智谱AI) 提供者"""

    # 支持的模型列表
    AVAILABLE_MODELS = [
        "glm-4",
        "glm-4.7",
        "glm-4-plus",
        "glm-4-flash",
        "glm-4-air",
        "glm-3-turbo"
    ]

    def __init__(self, api_key: str, model: str = "glm-4", **kwargs):
        """
        初始化ChatGLM提供者

        Args:
            api_key: 智谱AI的API密钥
            model: 模型名称，默认glm-4
            **kwargs: 其他配置参数
        """
        super().__init__(api_key, model, **kwargs)

        if not CHATGLM_AVAILABLE:
            raise ImportError(
                "zhipuai包未安装，请运行: pip install zhipuai"
            )

        if model not in self.AVAILABLE_MODELS:
            logger.warning(
                f"模型 {model} 不在已知列表中，"
                f"支持的模型: {', '.join(self.AVAILABLE_MODELS)}"
            )

        try:
            self.client = ZhipuAI(api_key=api_key)
            logger.info(f"ChatGLM客户端初始化成功，使用模型: {model}")
        except Exception as e:
            logger.error(f"ChatGLM客户端初始化失败: {e}")
            raise

    def generate(self, prompt: str, temperature: float = 0.7,
                 max_tokens: int = 4000, top_p: float = 0.9,
                 stream: bool = False, **kwargs):
        """
        生成文本

        Args:
            prompt: 提示词
            temperature: 温度参数，控制随机性
            max_tokens: 最大token数
            top_p: 核采样参数
            stream: 是否使用流式输出
            **kwargs: 其他参数

        Returns:
            如果stream=False，返回生成的文本内容
            如果stream=True，返回生成器，yield每个文本块
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
                stream=stream,
                **kwargs
            )

            if stream:
                # 流式输出：返回生成器
                def stream_generator():
                    full_content = ""
                    for chunk in response:
                        if chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            full_content += content
                            yield content
                    logger.debug(f"ChatGLM流式生成完成，总token数: {len(full_content)}")

                return stream_generator()
            else:
                # 非流式：直接返回完整内容
                content = response.choices[0].message.content
                logger.debug(f"ChatGLM生成成功，token使用: "
                            f"{response.usage.total_tokens}")
                return content

        except Exception as e:
            logger.error(f"ChatGLM生成失败: {e}")
            raise

    def generate_note(self, topic: str, language: str = "中文",
                      style: str = "详细教程", **kwargs) -> str:
        """
        生成学习笔记

        Args:
            topic: 学习主题
            language: 笔记语言
            style: 笔记风格
            **kwargs: 其他参数

        Returns:
            Markdown格式的笔记内容
        """
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
        """
        测试API连接是否正常

        Returns:
            连接是否成功
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            logger.info("ChatGLM连接测试成功")
            return True
        except Exception as e:
            logger.error(f"ChatGLM连接测试失败: {e}")
            return False
