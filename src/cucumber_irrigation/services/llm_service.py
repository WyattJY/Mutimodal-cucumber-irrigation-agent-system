from __future__ import annotations
"""LLM 调用服务

支持 Weekly Context 注入和 SanityCheck
参考: task1.md P4-04
"""

import time
import json
from typing import Optional, List

from openai import OpenAI
from loguru import logger

from ..services.image_service import ImageService
from ..memory.budget_controller import WorkingContext


class LLMService:
    """OpenAI 兼容 API 调用服务

    扩展功能:
    - Weekly Context 注入
    - SanityCheck 支持
    - RAG 结果注入
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://yunwu.ai/v1",
        model: str = "gpt-5.2",
        temperature: float = 0.3,
        max_tokens: int = 2000,
        timeout: int = 60
    ):
        """
        初始化 LLM 服务

        Args:
            api_key: API 密钥
            base_url: API 基础 URL
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数
            timeout: 超时时间（秒）
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate_plant_response(
        self,
        system_prompt: str,
        user_prompt: str,
        image_today_b64: str,
        image_yesterday_b64: str,
        examples: Optional[list[dict]] = None,
        retry_times: int = 3,
        retry_delay: int = 2
    ) -> str:
        """
        生成 PlantResponse

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            image_today_b64: 今日图像 Base64
            image_yesterday_b64: 昨日图像 Base64
            examples: Few-shot 示例
            retry_times: 重试次数
            retry_delay: 重试间隔（秒）

        Returns:
            LLM 响应的 JSON 字符串
        """
        messages = self._build_messages(
            system_prompt,
            user_prompt,
            image_today_b64,
            image_yesterday_b64,
            examples
        )

        last_error = None
        for attempt in range(retry_times):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    response_format={"type": "json_object"}
                )
                return response.choices[0].message.content

            except Exception as e:
                last_error = e
                logger.warning(f"LLM 调用失败 (尝试 {attempt + 1}/{retry_times}): {e}")
                if attempt < retry_times - 1:
                    time.sleep(retry_delay)

        raise RuntimeError(f"LLM 调用失败，已重试 {retry_times} 次: {last_error}")

    def _build_messages(
        self,
        system_prompt: str,
        user_prompt: str,
        image_today_b64: str,
        image_yesterday_b64: str,
        examples: Optional[list[dict]] = None
    ) -> list[dict]:
        """
        构建消息列表

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            image_today_b64: 今日图像 Base64
            image_yesterday_b64: 昨日图像 Base64
            examples: Few-shot 示例

        Returns:
            消息列表
        """
        messages = [{"role": "system", "content": system_prompt}]

        # 添加 few-shot 示例
        if examples:
            for ex in examples:
                if "user" in ex and "assistant" in ex:
                    messages.append({"role": "user", "content": ex["user"]})
                    messages.append({"role": "assistant", "content": ex["assistant"]})

        # 构建带图像的用户消息
        user_content = [
            {"type": "text", "text": user_prompt},
            {"type": "text", "text": "\n\n## 昨日图像"},
            {
                "type": "image_url",
                "image_url": {
                    "url": ImageService.get_image_url(image_yesterday_b64)
                }
            },
            {"type": "text", "text": "\n\n## 今日图像"},
            {
                "type": "image_url",
                "image_url": {
                    "url": ImageService.get_image_url(image_today_b64)
                }
            }
        ]

        messages.append({"role": "user", "content": user_content})

        return messages

    def generate_with_context(
        self,
        context: WorkingContext,
        image_today_b64: Optional[str] = None,
        image_yesterday_b64: Optional[str] = None,
        examples: Optional[list[dict]] = None,
        retry_times: int = 3,
        retry_delay: int = 2
    ) -> str:
        """
        使用 WorkingContext 生成响应

        自动注入 Weekly Context 和 RAG 结果

        Args:
            context: 工作上下文
            image_today_b64: 今日图像 Base64
            image_yesterday_b64: 昨日图像 Base64
            examples: Few-shot 示例
            retry_times: 重试次数
            retry_delay: 重试间隔

        Returns:
            LLM 响应的 JSON 字符串
        """
        messages = context.to_messages()

        # 添加 few-shot 示例
        if examples:
            for ex in examples:
                if "user" in ex and "assistant" in ex:
                    messages.append({"role": "user", "content": ex["user"]})
                    messages.append({"role": "assistant", "content": ex["assistant"]})

        # 添加图像 (如果提供)
        if image_today_b64 and image_yesterday_b64:
            image_content = [
                {"type": "text", "text": "\n\n## 昨日图像"},
                {
                    "type": "image_url",
                    "image_url": {"url": ImageService.get_image_url(image_yesterday_b64)}
                },
                {"type": "text", "text": "\n\n## 今日图像"},
                {
                    "type": "image_url",
                    "image_url": {"url": ImageService.get_image_url(image_today_b64)}
                }
            ]
            messages.append({"role": "user", "content": image_content})

        return self._call_api(messages, retry_times, retry_delay)

    def sanity_check(
        self,
        tsmixer_prediction: float,
        plant_response: dict,
        today_input: dict,
        weekly_context: Optional[str] = None,
        rag_advice: Optional[str] = None,
        retry_times: int = 3,
        retry_delay: int = 2
    ) -> dict:
        """
        执行 SanityCheck

        验证 TSMixer 预测值是否与长势评估一致

        Args:
            tsmixer_prediction: TSMixer 预测值
            plant_response: PlantResponse 数据
            today_input: 今日输入数据
            weekly_context: 周摘要 (可选)
            rag_advice: RAG 检索建议 (可选)
            retry_times: 重试次数
            retry_delay: 重试间隔

        Returns:
            SanityCheck 结果
        """
        # 构建 System Prompt
        system_prompt = self._build_sanity_check_system_prompt(weekly_context)

        # 构建 User Prompt
        user_prompt = self._build_sanity_check_user_prompt(
            tsmixer_prediction,
            plant_response,
            today_input,
            rag_advice
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = self._call_api(messages, retry_times, retry_delay)
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"SanityCheck 响应解析失败: {e}")
            return {
                "is_consistent": True,
                "confidence": 0.5,
                "adjusted_value": tsmixer_prediction,
                "reason": "解析错误，使用原始预测值"
            }

    def _build_sanity_check_system_prompt(self, weekly_context: Optional[str]) -> str:
        """构建 SanityCheck 系统提示"""
        prompt = """你是一个温室黄瓜灌溉专家，负责验证机器学习模型的预测值是否与植物长势评估一致。

你需要根据以下信息判断预测值是否合理：
1. TSMixer 模型预测的灌水量
2. 长势评估结果 (trend, comparison, abnormalities)
3. 今日环境数据

输出格式 (JSON):
{
    "is_consistent": true/false,  // 预测值是否与长势一致
    "confidence": 0.0-1.0,        // 判断置信度
    "adjusted_value": float,      // 调整后的建议值 (如一致则与原值相同)
    "reason": "string",           // 判断理由
    "rag_used": true/false        // 是否参考了知识库
}

判断规则：
- 如果长势 trend=worse 但预测灌水量较低，可能需要上调
- 如果长势 trend=better 但预测灌水量过高，可能需要下调
- 环境异常 (高温/高湿/弱光) 需要特殊处理
- 调整幅度通常在 ±20% 以内"""

        if weekly_context:
            prompt += f"\n\n<recent_experience>\n{weekly_context}\n</recent_experience>"

        return prompt

    def _build_sanity_check_user_prompt(
        self,
        tsmixer_prediction: float,
        plant_response: dict,
        today_input: dict,
        rag_advice: Optional[str]
    ) -> str:
        """构建 SanityCheck 用户提示"""
        parts = [
            f"## TSMixer 预测值\n{tsmixer_prediction:.2f} L/m²",
            f"\n## 长势评估\n```json\n{json.dumps(plant_response, ensure_ascii=False, indent=2)}\n```",
            f"\n## 今日环境数据\n```json\n{json.dumps(today_input, ensure_ascii=False, indent=2)}\n```"
        ]

        if rag_advice:
            parts.append(f"\n## 知识库参考\n{rag_advice}")

        parts.append("\n请判断预测值是否合理，如有需要请给出调整建议。")

        return "\n".join(parts)

    def _call_api(
        self,
        messages: list[dict],
        retry_times: int = 3,
        retry_delay: int = 2
    ) -> str:
        """调用 API"""
        last_error = None
        for attempt in range(retry_times):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    response_format={"type": "json_object"}
                )
                return response.choices[0].message.content

            except Exception as e:
                last_error = e
                logger.warning(f"LLM 调用失败 (尝试 {attempt + 1}/{retry_times}): {e}")
                if attempt < retry_times - 1:
                    time.sleep(retry_delay)

        raise RuntimeError(f"LLM 调用失败，已重试 {retry_times} 次: {last_error}")

    def generate_weekly_insights(
        self,
        episodes_summary: list[dict],
        trend_stats: dict,
        irrigation_stats: dict,
        anomaly_events: list[dict],
        knowledge_refs: list[dict] = None,
        retry_times: int = 3,
        retry_delay: int = 2
    ) -> list[str]:
        """
        生成周度关键洞察

        Args:
            episodes_summary: 本周 Episodes 摘要
            trend_stats: 趋势统计
            irrigation_stats: 灌溉统计
            anomaly_events: 异常事件列表
            knowledge_refs: 知识库引用 (可选)
            retry_times: 重试次数
            retry_delay: 重试间隔

        Returns:
            2-3 条关键洞察
        """
        system_prompt = """你是温室黄瓜灌溉专家，负责生成本周灌溉管理的关键洞察总结。

请根据以下信息生成 2-3 条简洁的中文洞察，每条不超过 50 个字。

输出格式 (JSON):
{
    "insights": [
        "洞察1: 简洁描述本周最重要的发现或趋势",
        "洞察2: 简洁描述需要关注的问题或建议",
        "洞察3: 可选的额外洞察"
    ]
}

洞察要求：
1. 基于数据说话，不要空泛
2. 结合长势趋势和灌水量变化
3. 如有异常，必须提及
4. 如有知识库参考，可引用（标注 [文献]）
5. 语言简洁专业，适合农业技术人员阅读"""

        # 构建用户提示
        user_parts = [
            f"## 趋势统计\n- 好转天数: {trend_stats.get('better_days', 0)}\n- 平稳天数: {trend_stats.get('same_days', 0)}\n- 下降天数: {trend_stats.get('worse_days', 0)}\n- 主导趋势: {trend_stats.get('dominant_trend', 'same')}",
            f"\n## 灌溉统计\n- 总量: {irrigation_stats.get('total', 0):.1f} L/m²\n- 日均: {irrigation_stats.get('daily_avg', 0):.2f} L/m²\n- 趋势: {irrigation_stats.get('trend', 'stable')}"
        ]

        if anomaly_events:
            anomaly_text = "\n".join([
                f"- {e.get('date', '')}: {e.get('anomaly_type', '')} ({e.get('severity', '')})"
                for e in anomaly_events[:5]
            ])
            user_parts.append(f"\n## 异常事件\n{anomaly_text}")

        if episodes_summary:
            ep_text = "\n".join([
                f"- {e.get('date', '')}: 灌水 {e.get('irrigation', 0):.1f} L/m², 长势 {e.get('trend', 'same')}"
                for e in episodes_summary[:7]
            ])
            user_parts.append(f"\n## 每日记录\n{ep_text}")

        if knowledge_refs:
            ref_text = "\n".join([
                f"- [{r.get('source', 'FAO56')}] {r.get('snippet', '')[:100]}"
                for r in knowledge_refs[:3]
            ])
            user_parts.append(f"\n## 知识库参考\n{ref_text}")

        user_parts.append("\n请生成 2-3 条关键洞察。")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "\n".join(user_parts)}
        ]

        try:
            response = self._call_api(messages, retry_times, retry_delay)
            result = json.loads(response)
            return result.get("insights", [])
        except json.JSONDecodeError as e:
            logger.error(f"周洞察解析失败: {e}")
            return self._fallback_insights(trend_stats, irrigation_stats)
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            return self._fallback_insights(trend_stats, irrigation_stats)

    def _fallback_insights(self, trend_stats: dict, irrigation_stats: dict) -> list[str]:
        """回退的简单洞察生成"""
        insights = []
        trend_map = {"better": "好转", "same": "平稳", "worse": "下降"}
        trend_cn = trend_map.get(trend_stats.get("dominant_trend", "same"), "未知")
        insights.append(f"本周长势{trend_cn}，日均灌水 {irrigation_stats.get('daily_avg', 0):.1f} L/m²")
        return insights
