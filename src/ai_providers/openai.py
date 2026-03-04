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
        "gpt-4.5-preview",
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-4",
        "gpt-3.5-turbo"
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
                 stream: bool = False, **kwargs):
        """
        生成文本

        Args:
            prompt: 提示词
            temperature: 温度参数
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
                    try:
                        for chunk in response:
                            try:
                                if hasattr(chunk, 'choices') and chunk.choices and len(chunk.choices) > 0:
                                    choice = chunk.choices[0]
                                    if hasattr(choice, 'delta'):
                                        delta = choice.delta
                                        if hasattr(delta, 'content') and delta.content:
                                            content = delta.content
                                            full_content += content
                                            yield content
                            except Exception as chunk_err:
                                logger.warning(f"处理流式数据块时出错: {chunk_err}")
                                continue  # 跳过这个块，继续处理下一个
                        logger.debug(f"OpenAI流式生成完成，总字数: {len(full_content)}")
                    except Exception as stream_err:
                        logger.error(f"流式生成过程出错: {stream_err}", exc_info=True)
                        # 如果已经生成了一些内容，返回已生成的内容
                        if full_content:
                            logger.info(f"返回已生成的部分内容: {len(full_content)} 字")
                            yield full_content
                        else:
                            raise

                return stream_generator()
            else:
                # 非流式：直接返回完整内容
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
