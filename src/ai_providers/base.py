"""
AI提供者基类
所有AI服务提供商的接口定义
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional


class BaseAIProvider(ABC):
    """AI服务提供商基类"""

    def __init__(self, api_key: str, model: str, **kwargs):
        """
        初始化AI提供者

        Args:
            api_key: API密钥
            model: 模型名称
            **kwargs: 其他配置参数
        """
        self.api_key = api_key
        self.model = model
        self.config = kwargs

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """
        生成文本

        Args:
            prompt: 提示词
            **kwargs: 其他参数

        Returns:
            生成的文本内容
        """
        pass

    @abstractmethod
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
        pass

    def _build_note_prompt(self, topic: str, language: str,
                           style: str) -> str:
        """
        构建笔记生成的提示词

        Args:
            topic: 学习主题
            language: 笔记语言
            style: 笔记风格

        Returns:
            完整的提示词
        """
        style_descriptions = {
            "详细教程": "详细的教程式笔记，包含理论原理、代码示例、实践应用",
            "简洁概述": "简洁的概述性笔记，重点突出核心概念和关键信息",
            "深度解析": "深度技术解析，包含原理解析、技术细节、前沿发展",
            "实战指南": "实战导向的指南，包含使用方法、最佳实践、注意事项"
        }

        style_desc = style_descriptions.get(style, "详细教程")

        prompt = f"""请为"{topic}"这个AI技术主题生成{style_desc}的学习笔记。

要求：
1. 使用Markdown格式
2. 使用{language}撰写
3. 结构清晰，包含适当的标题层级
4. 包含代码示例（如果适用）
5. 突出重点概念和关键知识点
6. 添加适当的总结和思考题

笔记格式：
# {topic}

## 概述
[简要介绍该技术的背景、用途]

## 核心概念
[列出并解释核心概念]

## 技术原理
[详细解释技术原理]

## 代码示例
\`\`\`python
[提供代码示例]
\`\`\`

## 实际应用
[介绍实际应用场景]

## 总结与思考
[总结关键点，提出思考题]

## 参考资源
[列出相关学习资源]

请开始生成笔记："""

        return prompt

    def check_api_key(self) -> bool:
        """
        检查API密钥是否有效

        Returns:
            是否有效
        """
        if not self.api_key or self.api_key.strip() == "":
            return False
        return True
