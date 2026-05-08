from __future__ import annotations
"""生育期检测器

基于图像的生育期预判（Q7）
参考: task1.md P2-08, requirements1.md 8.2节
"""

from typing import Tuple, Literal, Optional
from pathlib import Path
import base64


GrowthStage = Literal["vegetative", "flowering", "fruiting", "mixed"]


class GrowthStageDetector:
    """生育期检测器

    调用 GPT-5.2 视觉模型分析图像，判断当前生育期:
    - vegetative: 主要可见叶片，无明显花朵/果实
    - flowering: 可见黄色花朵，可能有小果
    - fruiting: 可见发育中的果实（黄瓜）
    - mixed: 多种生育期特征并存
    """

    # 生育期检索查询模板
    QUERY_TEMPLATES = {
        "vegetative": "cucumber vegetative stage Kc leaf growth water requirement",
        "flowering": "cucumber flowering stage Kc flower development water stress",
        "fruiting": "cucumber fruiting stage Kc fruit development irrigation",
        "mixed": "cucumber transition growth stage Kc adjustment"
    }

    # 生育期判断提示词
    DETECTION_PROMPT = """请分析这张温室黄瓜植株图片，判断当前的生育期。

判断依据:
- vegetative (营养期): 主要可见叶片，无明显花朵或果实
- flowering (开花期): 可见黄色花朵，可能有小果
- fruiting (结果期): 可见发育中的果实（黄瓜）
- mixed (混合期): 多种生育期特征并存

请返回 JSON 格式:
{
    "growth_stage": "vegetative|flowering|fruiting|mixed",
    "confidence": 0.0-1.0,
    "evidence": "判断依据说明"
}"""

    def __init__(self, llm_service, config: dict):
        """
        初始化检测器

        Args:
            llm_service: LLM 服务实例 (支持视觉)
            config: knowledge_enhancement.yaml 配置
        """
        self.llm = llm_service
        self.confidence_threshold = config.get(
            'growth_stage_detection', {}
        ).get('confidence_threshold', 0.7)

    def detect(self, image_path: str) -> Tuple[GrowthStage, float, str]:
        """
        检测生育期

        Args:
            image_path: 图像路径

        Returns:
            (生育期, 置信度, 证据说明)
        """
        # 验证图像存在
        if not Path(image_path).exists():
            raise FileNotFoundError(f"图像不存在: {image_path}")

        # 读取图像并编码
        image_base64 = self._encode_image(image_path)

        # 调用 LLM 视觉模型
        result = self._call_vision_model(image_base64)

        # 解析结果
        growth_stage = result.get("growth_stage", "mixed")
        confidence = float(result.get("confidence", 0.5))
        evidence = result.get("evidence", "")

        # 如果置信度低于阈值，标记为 mixed
        if confidence < self.confidence_threshold:
            growth_stage = "mixed"

        return growth_stage, confidence, evidence

    def _encode_image(self, image_path: str) -> str:
        """将图像编码为 base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _call_vision_model(self, image_base64: str) -> dict:
        """调用视觉模型"""
        try:
            # 构建消息
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": self.DETECTION_PROMPT
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ]

            # 调用 LLM
            response = self.llm.chat(messages, response_format="json")

            # 解析响应
            import json
            if isinstance(response, str):
                return json.loads(response)
            return response

        except Exception as e:
            # 出错时返回默认值
            return {
                "growth_stage": "mixed",
                "confidence": 0.0,
                "evidence": f"检测失败: {str(e)}"
            }

    def get_retrieval_query(self, stage: GrowthStage) -> str:
        """
        根据生育期生成检索查询

        Args:
            stage: 生育期

        Returns:
            RAG 检索查询字符串
        """
        return self.QUERY_TEMPLATES.get(stage, self.QUERY_TEMPLATES["mixed"])

    def get_multi_stage_queries(self, stage: GrowthStage, confidence: float) -> list[str]:
        """
        当置信度较低时，生成多个生育期的查询

        Args:
            stage: 主要生育期
            confidence: 置信度

        Returns:
            查询列表
        """
        if confidence >= self.confidence_threshold:
            return [self.get_retrieval_query(stage)]

        # 低置信度时查询相邻生育期
        queries = [self.get_retrieval_query(stage)]

        adjacent_stages = {
            "vegetative": ["flowering"],
            "flowering": ["vegetative", "fruiting"],
            "fruiting": ["flowering"],
            "mixed": ["vegetative", "flowering", "fruiting"]
        }

        for adj_stage in adjacent_stages.get(stage, []):
            queries.append(self.get_retrieval_query(adj_stage))

        return queries

    def detect_from_yolo_metrics(
        self,
        flower_count: float,
        fruit_mask: float,
        leaf_count: float
    ) -> Tuple[GrowthStage, float]:
        """
        基于 YOLO 指标的快速生育期判断 (备选方法)

        Args:
            flower_count: 花朵数量
            fruit_mask: 果实掩码面积
            leaf_count: 叶片数量

        Returns:
            (生育期, 置信度)
        """
        # 简单规则判断
        if fruit_mask > 1000:
            return "fruiting", 0.8
        elif flower_count > 0.5:
            return "flowering", 0.75
        elif leaf_count > 3:
            return "vegetative", 0.7
        else:
            return "mixed", 0.5
