"""Token 计数器

使用 tiktoken 进行准确的 token 计数
参考: task1.md P3-01, requirements1.md 5.4节
"""

from typing import List, Union
import tiktoken


class TokenCounter:
    """Token 计数器

    使用 tiktoken 库进行准确的 token 计数
    支持 GPT-4 等模型的分词
    """

    def __init__(self, model: str = "gpt-4"):
        """
        初始化计数器

        Args:
            model: 模型名称 (用于选择正确的编码器)
        """
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # 如果模型不支持，使用 cl100k_base (GPT-4 默认)
            self.encoding = tiktoken.get_encoding("cl100k_base")

        self.model = model

    def count(self, text: str) -> int:
        """
        计算文本的 token 数

        Args:
            text: 输入文本

        Returns:
            token 数量
        """
        if not text:
            return 0
        return len(self.encoding.encode(text))

    def count_messages(self, messages: List[dict]) -> int:
        """
        计算 messages 列表的总 token 数

        Args:
            messages: OpenAI 消息格式列表

        Returns:
            总 token 数
        """
        total = 0
        for msg in messages:
            # 每条消息有固定开销
            total += 4  # <|im_start|>role<|im_sep|>...<|im_end|>

            content = msg.get("content", "")
            if isinstance(content, str):
                total += self.count(content)
            elif isinstance(content, list):
                # 多模态消息
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        total += self.count(item.get("text", ""))

            # role 的 token 数
            total += self.count(msg.get("role", ""))

        # 最终有固定开销
        total += 2  # <|im_start|>assistant

        return total

    def count_dict(self, data: dict) -> int:
        """
        计算字典序列化后的 token 数

        Args:
            data: 字典数据

        Returns:
            token 数量
        """
        import json
        text = json.dumps(data, ensure_ascii=False)
        return self.count(text)

    def truncate_to_limit(self, text: str, max_tokens: int) -> str:
        """
        将文本截断到指定 token 数

        Args:
            text: 输入文本
            max_tokens: 最大 token 数

        Returns:
            截断后的文本
        """
        tokens = self.encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text

        truncated_tokens = tokens[:max_tokens]
        return self.encoding.decode(truncated_tokens)

    def estimate_from_chars(self, char_count: int, lang: str = "mixed") -> int:
        """
        基于字符数估算 token 数 (快速估算)

        Args:
            char_count: 字符数
            lang: 语言类型 ("zh", "en", "mixed")

        Returns:
            估算的 token 数
        """
        ratios = {
            "zh": 0.5,    # 中文约 2 字符/token
            "en": 0.25,   # 英文约 4 字符/token
            "mixed": 0.4  # 混合约 2.5 字符/token
        }
        ratio = ratios.get(lang, 0.4)
        return int(char_count * ratio)

    def get_encoding_name(self) -> str:
        """获取编码器名称"""
        return self.encoding.name
