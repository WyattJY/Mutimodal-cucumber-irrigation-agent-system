from __future__ import annotations
# LLM Service - OpenAI 对话服务
"""
LLM 对话服务 - 支持 GPT-4/GPT-5.2 等模型

功能:
1. 流式对话 (SSE)
2. 非流式对话
3. 图片分析 (Vision)
4. 动态配置切换
5. PlantResponse 生成 (对比分析/冷启动)
6. SanityCheck 合理性复核

模型分配:
- gpt-5.2-chat-latest: 纯文本对话
- gpt-5.2: 图片分析 (Vision)
"""

import json
import base64
from typing import AsyncGenerator, Optional, List, Union
from openai import AsyncOpenAI
from app.core.config import get_active_openai_config, settings
from app.models.schemas import (
    PlantResponseResult, SanityCheckResult, Evidence, Abnormalities,
    Comparison, TrendType, SeverityType, GrowthStageType
)


# 模型常量
MODEL_CHAT = "gpt-5.2-chat-latest"  # 纯文本对话
MODEL_VISION = "gpt-5.2"  # 图片分析


class LLMService:
    """LLM 对话服务"""

    SYSTEM_PROMPT = """你是 AGRI-COPILOT，一个专业的温室农业专家助手。

你擅长以下领域：
- 温室黄瓜种植技术与管理
- 灌溉调度与水分管理
- 作物需水量计算 (FAO56 Penman-Monteith)
- 病虫害识别与防治
- 环境调控 (温度、湿度、光照、CO2)
- 营养管理与施肥策略

回答规范：
1. 使用专业但易懂的语言
2. 提供具体可操作的建议
3. 必要时引用相关数据或公式
4. 如果不确定，请诚实说明

当前系统信息：
- 作物: 温室黄瓜
- 预测模型: TSMixer (时序预测)
- 视觉模型: YOLOv11-seg (实例分割)"""

    VISION_SYSTEM_PROMPT = """你是 AGRI-COPILOT，一个专业的温室农业视觉分析专家。

你的任务是分析温室黄瓜图像，识别并描述：
1. 叶片数量和健康状态
2. 果实发育阶段和数量
3. 花朵状态
4. 生长点 (terminal) 状态
5. 病虫害迹象
6. 整体植株健康评估

请结合YOLO实例分割结果，提供专业的农艺建议。"""

    def __init__(self):
        self._client: Optional[AsyncOpenAI] = None
        self._current_config: Optional[dict] = None

    def _get_client(self) -> AsyncOpenAI:
        """获取 OpenAI 客户端 (配置变化时自动刷新)"""
        config = get_active_openai_config()

        if self._client is None or self._current_config != config:
            self._client = AsyncOpenAI(
                api_key=config["api_key"],
                base_url=config["base_url"]
            )
            self._current_config = config.copy()

        return self._client

    @property
    def model(self) -> str:
        return MODEL_CHAT

    @property
    def vision_model(self) -> str:
        return MODEL_VISION

    async def chat(self, message: str, history: Optional[List[dict]] = None) -> str:
        client = self._get_client()
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": message})
        response = await client.chat.completions.create(model=MODEL_CHAT, messages=messages, temperature=0.7, max_tokens=2048)
        return response.choices[0].message.content or ""

    async def chat_stream(self, message: str, history: Optional[List[dict]] = None) -> AsyncGenerator[str, None]:
        client = self._get_client()
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": message})
        response = await client.chat.completions.create(model=MODEL_CHAT, messages=messages, temperature=0.7, max_tokens=2048, stream=True)
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def analyze_image(self, image_base64: str, prompt: Optional[str] = None, yolo_metrics: Optional[dict] = None) -> str:
        client = self._get_client()
        user_content = [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}]
        text_prompt = prompt or "请分析这张温室黄瓜图片，描述植株的健康状态和生长情况。"
        if yolo_metrics:
            text_prompt += "\n\nYOLO分割结果:\n"
            text_prompt += f"- 叶片数量: {yolo_metrics.get('leaf_instance_count', 'N/A')}\n"
        user_content.append({"type": "text", "text": text_prompt})
        messages = [{"role": "system", "content": self.VISION_SYSTEM_PROMPT}, {"role": "user", "content": user_content}]
        response = await client.chat.completions.create(model=MODEL_VISION, messages=messages, temperature=0.7, max_tokens=2048)
        return response.choices[0].message.content or ""

    async def analyze_image_stream(self, image_base64: str, prompt: Optional[str] = None, yolo_metrics: Optional[dict] = None) -> AsyncGenerator[str, None]:
        client = self._get_client()
        user_content = [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}]
        text_prompt = prompt or "请分析这张温室黄瓜图片，描述植株的健康状态和生长情况。"
        if yolo_metrics:
            text_prompt += "\n\nYOLO分割结果:\n"
            text_prompt += f"- 叶片数量: {yolo_metrics.get('leaf_instance_count', 'N/A')}\n"
        user_content.append({"type": "text", "text": text_prompt})
        messages = [{"role": "system", "content": self.VISION_SYSTEM_PROMPT}, {"role": "user", "content": user_content}]
        response = await client.chat.completions.create(model=MODEL_VISION, messages=messages, temperature=0.7, max_tokens=2048, stream=True)
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def test_connection(self) -> dict:
        try:
            client = self._get_client()
            response = await client.chat.completions.create(model=MODEL_CHAT, messages=[{"role": "user", "content": "Hi"}], max_tokens=5)
            return {"success": True, "message": "连接成功", "model_chat": MODEL_CHAT, "model_vision": MODEL_VISION, "response": response.choices[0].message.content}
        except Exception as e:
            return {"success": False, "message": f"连接失败: {str(e)}", "model_chat": MODEL_CHAT, "model_vision": MODEL_VISION}

    # =========================================================================
    # PlantResponse 生成
    # =========================================================================

    COMPARISON_SYSTEM_PROMPT = """你是一个温室黄瓜长势评估专家。

任务：对比分析昨日与今日的黄瓜植株图像，评估长势变化。

输入：
1. 昨日图像 + YOLO 指标
2. 今日图像 + YOLO 指标
3. 今日环境数据

输出格式 (JSON)：
{
  "trend": "better | same | worse",
  "confidence": 0.0-1.0,
  "evidence": {
    "leaf_observation": "叶片观察描述...",
    "flower_observation": "花朵观察描述...",
    "fruit_observation": "果实观察描述...",
    "terminal_bud_observation": "顶芽观察描述..."
  },
  "abnormalities": {
    "wilting": "none | mild | moderate | severe",
    "yellowing": "none | mild | moderate | severe",
    "pest_damage": "none | mild | moderate | severe",
    "other": null 或 "其他异常描述"
  },
  "growth_stage": "vegetative | flowering | fruiting | mixed",
  "comparison": {
    "leaf_area_change": "增加 | 减少 | 持平",
    "leaf_count_change": "增加 | 减少 | 持平",
    "flower_count_change": "增加 | 减少 | 持平",
    "fruit_count_change": "增加 | 减少 | 持平",
    "overall_vigor_change": "增加 | 减少 | 持平"
  }
}

判断规则：
- 有明显病害/萎蔫 → trend = "worse"
- 叶片 mask 增长率 > 5% → trend = "better"
- 叶片 mask 增长率在 ±5% → trend = "same"
- 叶片 mask 增长率 < -5% → trend = "worse"
- 花朵或果实数量明显增加 → 考虑 trend = "better"
- 综合多个指标做出判断，给出合理的 confidence"""

    COLD_START_SYSTEM_PROMPT = """你是一个温室黄瓜长势评估专家。

任务：分析单张黄瓜植株图像，描述当前状态。

注意：这是首次分析，没有历史对比数据，无法判断趋势。

输入：
1. 今日图像 + YOLO 指标
2. 今日环境数据

输出格式 (JSON)：
{
  "trend": null,
  "confidence": 0.0-1.0,
  "evidence": {
    "leaf_observation": "叶片观察描述...",
    "flower_observation": "花朵观察描述...",
    "fruit_observation": "果实观察描述...",
    "terminal_bud_observation": "顶芽观察描述..."
  },
  "abnormalities": {
    "wilting": "none | mild | moderate | severe",
    "yellowing": "none | mild | moderate | severe",
    "pest_damage": "none | mild | moderate | severe",
    "other": null 或 "其他异常描述"
  },
  "growth_stage": "vegetative | flowering | fruiting | mixed",
  "comparison": null,
  "is_cold_start": true,
  "current_state_summary": "当前植株整体状态描述..."
}

评估重点：
1. 仔细观察叶片颜色、大小、形态
2. 检查花朵开放情况和数量
3. 评估果实发育阶段
4. 识别任何病虫害迹象
5. 判断当前生育期"""

    async def generate_plant_response(
        self,
        image_today_b64: str,
        image_yesterday_b64: Optional[str],
        yolo_today: dict,
        yolo_yesterday: Optional[dict],
        env_data: Optional[dict] = None,
        is_cold_start: bool = False
    ) -> PlantResponseResult:
        """
        生成 PlantResponse

        Args:
            image_today_b64: 今日图片 Base64
            image_yesterday_b64: 昨日图片 Base64 (冷启动时为 None)
            yolo_today: 今日 YOLO 指标
            yolo_yesterday: 昨日 YOLO 指标 (冷启动时为 None)
            env_data: 环境数据
            is_cold_start: 是否为冷启动

        Returns:
            PlantResponseResult: 结构化的长势评估结果
        """
        if is_cold_start or image_yesterday_b64 is None:
            return await self._generate_cold_start_response(
                image_today_b64, yolo_today, env_data
            )
        else:
            return await self._generate_comparison_response(
                image_today_b64, image_yesterday_b64,
                yolo_today, yolo_yesterday, env_data
            )

    async def _generate_comparison_response(
        self,
        image_today_b64: str,
        image_yesterday_b64: str,
        yolo_today: dict,
        yolo_yesterday: dict,
        env_data: Optional[dict]
    ) -> PlantResponseResult:
        """生成对比分析 (今日 vs 昨日)"""
        client = self._get_client()

        user_prompt = self._build_comparison_user_prompt(
            yolo_today, yolo_yesterday, env_data
        )

        messages = [
            {"role": "system", "content": self.COMPARISON_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "## 昨日图像"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_yesterday_b64}"}},
                    {"type": "text", "text": "## 今日图像"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_today_b64}"}},
                    {"type": "text", "text": user_prompt}
                ]
            }
        ]

        try:
            response = await client.chat.completions.create(
                model=MODEL_VISION,
                messages=messages,
                temperature=0.3,
                max_tokens=2048,
                response_format={"type": "json_object"}
            )
            response_text = response.choices[0].message.content
            return self._parse_plant_response(response_text, is_cold_start=False)
        except Exception as e:
            # 返回默认值
            return self._get_default_plant_response(is_cold_start=False, error=str(e))

    async def _generate_cold_start_response(
        self,
        image_today_b64: str,
        yolo_today: dict,
        env_data: Optional[dict]
    ) -> PlantResponseResult:
        """生成单日分析 (冷启动)"""
        client = self._get_client()

        user_prompt = self._build_cold_start_user_prompt(yolo_today, env_data)

        messages = [
            {"role": "system", "content": self.COLD_START_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "## 今日图像"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_today_b64}"}},
                    {"type": "text", "text": user_prompt}
                ]
            }
        ]

        try:
            response = await client.chat.completions.create(
                model=MODEL_VISION,
                messages=messages,
                temperature=0.3,
                max_tokens=2048,
                response_format={"type": "json_object"}
            )
            response_text = response.choices[0].message.content
            return self._parse_plant_response(response_text, is_cold_start=True)
        except Exception as e:
            return self._get_default_plant_response(is_cold_start=True, error=str(e))

    def _build_comparison_user_prompt(
        self,
        yolo_today: dict,
        yolo_yesterday: dict,
        env_data: Optional[dict]
    ) -> str:
        """构建对比分析用户提示"""
        parts = [
            "## YOLO 指标对比",
            "### 昨日指标",
            f"```json\n{json.dumps(yolo_yesterday, ensure_ascii=False, indent=2)}\n```",
            "### 今日指标",
            f"```json\n{json.dumps(yolo_today, ensure_ascii=False, indent=2)}\n```"
        ]

        if env_data:
            parts.append("## 今日环境数据")
            parts.append(f"```json\n{json.dumps(env_data, ensure_ascii=False, indent=2)}\n```")

        parts.append("\n请对比分析两日图像和指标，输出 JSON 格式的长势评估结果。")

        return "\n".join(parts)

    def _build_cold_start_user_prompt(
        self,
        yolo_today: dict,
        env_data: Optional[dict]
    ) -> str:
        """构建冷启动用户提示"""
        parts = [
            "## YOLO 指标",
            f"```json\n{json.dumps(yolo_today, ensure_ascii=False, indent=2)}\n```"
        ]

        if env_data:
            parts.append("## 今日环境数据")
            parts.append(f"```json\n{json.dumps(env_data, ensure_ascii=False, indent=2)}\n```")

        parts.append("\n这是首次分析，没有历史数据。请分析当前植株状态，输出 JSON 格式的评估结果。")

        return "\n".join(parts)

    def _parse_plant_response(
        self,
        response_text: str,
        is_cold_start: bool
    ) -> PlantResponseResult:
        """解析 LLM 响应为 PlantResponseResult"""
        try:
            data = json.loads(response_text)

            # 解析 trend
            trend_val = data.get("trend")
            trend = None
            if trend_val and trend_val in ["better", "same", "worse"]:
                trend = TrendType(trend_val)

            # 解析 evidence
            evidence_data = data.get("evidence", {})
            evidence = Evidence(
                leaf_observation=evidence_data.get("leaf_observation", ""),
                flower_observation=evidence_data.get("flower_observation", ""),
                fruit_observation=evidence_data.get("fruit_observation", ""),
                terminal_bud_observation=evidence_data.get("terminal_bud_observation", "")
            )

            # 解析 abnormalities
            abnorm_data = data.get("abnormalities", {})
            abnormalities = Abnormalities(
                wilting=abnorm_data.get("wilting", "none"),
                yellowing=abnorm_data.get("yellowing", "none"),
                pest_damage=abnorm_data.get("pest_damage", "none"),
                other=abnorm_data.get("other", "")
            )

            # 解析 comparison
            comparison = None
            if not is_cold_start and data.get("comparison"):
                comp_data = data["comparison"]
                comparison = Comparison(
                    leaf_area_change=comp_data.get("leaf_area_change", "持平"),
                    leaf_count_change=comp_data.get("leaf_count_change", "持平"),
                    flower_count_change=comp_data.get("flower_count_change", "持平"),
                    fruit_count_change=comp_data.get("fruit_count_change", "持平"),
                    overall_vigor_change=comp_data.get("overall_vigor_change", "持平")
                )

            return PlantResponseResult(
                trend=trend,
                confidence=float(data.get("confidence", 0.7)),
                evidence=evidence,
                abnormalities=abnormalities,
                growth_stage=data.get("growth_stage", "mixed"),
                comparison=comparison,
                is_cold_start=is_cold_start,
                current_state_summary=data.get("current_state_summary")
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            return self._get_default_plant_response(is_cold_start, error=str(e))

    def _get_default_plant_response(
        self,
        is_cold_start: bool,
        error: str = ""
    ) -> PlantResponseResult:
        """获取默认的 PlantResponse"""
        return PlantResponseResult(
            trend=None if is_cold_start else TrendType.SAME,
            confidence=0.5,
            evidence=Evidence(
                leaf_observation="解析错误，无法提取观察结果" if error else "未能分析",
                flower_observation="",
                fruit_observation="",
                terminal_bud_observation=""
            ),
            abnormalities=Abnormalities(
                wilting="none",
                yellowing="none",
                pest_damage="none",
                other=error if error else ""
            ),
            growth_stage="mixed",
            comparison=None if is_cold_start else Comparison(
                leaf_area_change="持平",
                leaf_count_change="持平",
                flower_count_change="持平",
                fruit_count_change="持平",
                overall_vigor_change="持平"
            ),
            is_cold_start=is_cold_start,
            current_state_summary="分析过程中发生错误" if error else None
        )

    # =========================================================================
    # SanityCheck 合理性复核
    # =========================================================================

    SANITY_CHECK_SYSTEM_PROMPT = """你是一个温室黄瓜灌溉专家，负责验证机器学习模型的预测值是否与植物长势评估一致。

你需要根据以下信息判断预测值是否合理：
1. TSMixer 模型预测的灌水量
2. 长势评估结果 (trend, comparison, abnormalities)
3. 今日环境数据

输出格式 (JSON):
{
    "is_consistent": true/false,
    "confidence": 0.0-1.0,
    "adjusted_value": float,
    "reason": "string",
    "rag_used": true/false
}

判断规则：
- 如果长势 trend=worse 但预测灌水量较低(<4.5)，可能需要上调
- 如果长势 trend=better 但预测灌水量过高(>6.5)，可能需要下调
- 环境异常 (高温>32°C/高湿>85%/弱光<20000lux) 需要特殊处理
- 调整幅度通常在 ±20% 以内
- 如果一致，adjusted_value 应与原预测值相同"""

    async def sanity_check(
        self,
        tsmixer_prediction: float,
        plant_response: dict,
        env_data: dict,
        weekly_context: Optional[str] = None,
        rag_advice: Optional[str] = None
    ) -> SanityCheckResult:
        """
        执行 SanityCheck

        验证 TSMixer 预测值是否与长势评估一致

        Args:
            tsmixer_prediction: TSMixer 预测值
            plant_response: PlantResponse 数据
            env_data: 环境数据
            weekly_context: 周摘要上下文 (可选)
            rag_advice: RAG 检索建议 (可选)

        Returns:
            SanityCheckResult: 合理性复核结果
        """
        client = self._get_client()

        # 构建 System Prompt
        system_prompt = self.SANITY_CHECK_SYSTEM_PROMPT
        if weekly_context:
            system_prompt += f"\n\n<recent_experience>\n{weekly_context}\n</recent_experience>"

        # 构建 User Prompt
        user_prompt = self._build_sanity_check_user_prompt(
            tsmixer_prediction, plant_response, env_data, rag_advice
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = await client.chat.completions.create(
                model=MODEL_CHAT,
                messages=messages,
                temperature=0.3,
                max_tokens=1024,
                response_format={"type": "json_object"}
            )
            response_text = response.choices[0].message.content
            data = json.loads(response_text)

            return SanityCheckResult(
                is_consistent=data.get("is_consistent", True),
                confidence=float(data.get("confidence", 0.8)),
                adjusted_value=float(data.get("adjusted_value", tsmixer_prediction)),
                reason=data.get("reason", ""),
                rag_used=data.get("rag_used", rag_advice is not None)
            )
        except Exception as e:
            # 返回默认值（认为一致）
            return SanityCheckResult(
                is_consistent=True,
                confidence=0.5,
                adjusted_value=tsmixer_prediction,
                reason=f"SanityCheck 执行失败: {str(e)}",
                rag_used=False
            )

    def _build_sanity_check_user_prompt(
        self,
        tsmixer_prediction: float,
        plant_response: dict,
        env_data: dict,
        rag_advice: Optional[str]
    ) -> str:
        """构建 SanityCheck 用户提示"""
        parts = [
            f"## TSMixer 预测值\n{tsmixer_prediction:.2f} L/m²",
            f"\n## 长势评估\n```json\n{json.dumps(plant_response, ensure_ascii=False, indent=2)}\n```",
            f"\n## 今日环境数据\n```json\n{json.dumps(env_data, ensure_ascii=False, indent=2)}\n```"
        ]

        if rag_advice:
            parts.append(f"\n## 知识库参考\n{rag_advice}")

        parts.append("\n请判断预测值是否合理，如有需要请给出调整建议。")

        return "\n".join(parts)


llm_service = LLMService()
