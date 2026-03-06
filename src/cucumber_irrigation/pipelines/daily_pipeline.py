"""每日决策管道

整合所有组件的完整每日决策流程
参考: task1.md P5-01, requirements1.md
"""

from typing import Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd
from loguru import logger

from ..core import (
    EnvInputHandler, ColdStartFiller, WindowBuilder,
    AnomalyDetector, GrowthStageDetector
)
from ..models import (
    EnvInput, PlantResponse, AnomalyResult, Episode,
    EpisodeInputs, EpisodePredictions, EpisodeAnomalies,
    FinalDecision, KnowledgeReference
)
from ..memory import (
    BudgetController, WorkingContextBuilder,
    EpisodeStore, WeeklySummaryStore, KnowledgeRetriever
)
from ..services import (
    DBService, TSMixerService, RAGService, LLMService
)


@dataclass
class DailyPipelineConfig:
    """管道配置"""
    # 数据路径
    reference_data_path: str = "data/csv/irrigation_pre.csv"
    user_data_path: Optional[str] = None

    # 服务配置
    enable_rag: bool = True
    enable_growth_stage_detection: bool = True
    enable_sanity_check: bool = True

    # 存储配置
    use_mongodb: bool = False
    json_storage_path: str = "data/storage"


@dataclass
class DailyPipelineResult:
    """管道输出结果"""
    date: str
    irrigation_amount: float
    source: str  # tsmixer | override | sanity_adjusted

    # 详细结果
    tsmixer_prediction: Optional[float] = None
    plant_response: Optional[PlantResponse] = None
    anomaly_result: Optional[AnomalyResult] = None
    sanity_check_result: Optional[dict] = None

    # 知识增强
    growth_stage: Optional[str] = None
    growth_stage_confidence: Optional[float] = None
    knowledge_references: List[dict] = field(default_factory=list)
    rag_advice: Optional[str] = None

    # 警告和建议
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    # Episode ID
    episode_id: Optional[str] = None


class DailyPipeline:
    """每日决策管道

    完整流程:
    1. 获取输入 (图像、环境数据)
    2. 构建时序窗口
    3. TSMixer 预测
    4. 生育期预判 (Q7)
    5. 知识库检索 (Q7)
    6. 长势评估 (PlantResponse)
    7. 异常检测 (A1/A2/A3)
    8. RAG 辅助判断
    9. 构建 L1 Working Context
    10. 合理性复核 (SanityCheck)
    11. 存储 Episode
    12. 返回结果
    """

    def __init__(
        self,
        config: Optional[DailyPipelineConfig] = None,
        llm_service: Optional[LLMService] = None,
        db_service: Optional[DBService] = None
    ):
        """
        初始化管道

        Args:
            config: 管道配置
            llm_service: LLM 服务 (用于 PlantResponse 和 SanityCheck)
            db_service: 数据库服务
        """
        self.config = config or DailyPipelineConfig()
        self.llm_service = llm_service
        self.db_service = db_service

        # 初始化组件
        self._init_components()

    def _init_components(self):
        """初始化所有组件"""
        # 核心组件
        self.cold_start_filler = ColdStartFiller(
            reference_data_path=self.config.reference_data_path
        )
        self.window_builder = WindowBuilder(
            cold_start_filler=self.cold_start_filler
        )
        self.env_handler = EnvInputHandler()
        self.anomaly_detector = AnomalyDetector()

        # 服务
        self.tsmixer_service = TSMixerService()
        self.rag_service = RAGService() if self.config.enable_rag else None

        # 记忆组件
        self.budget_controller = BudgetController()
        self.context_builder = WorkingContextBuilder(
            budget_controller=self.budget_controller
        )

        # 存储
        if self.config.use_mongodb and self.db_service:
            self.episode_store = EpisodeStore(
                mongo_client=self.db_service.client
            )
            self.weekly_store = WeeklySummaryStore(
                mongo_client=self.db_service.client
            )
        else:
            import os
            self.episode_store = EpisodeStore(
                json_path=os.path.join(self.config.json_storage_path, "episodes.json")
            )
            self.weekly_store = WeeklySummaryStore(
                json_path=os.path.join(self.config.json_storage_path, "weekly_summaries.json")
            )

        # 生育期检测器 (需要 LLM)
        self.growth_stage_detector = None
        if self.config.enable_growth_stage_detection and self.llm_service:
            self.growth_stage_detector = GrowthStageDetector(
                llm_service=self.llm_service
            )

    def run(
        self,
        target_date: str,
        image_today_path: Optional[str] = None,
        image_yesterday_path: Optional[str] = None,
        env_data: Optional[dict] = None,
        user_data: Optional[pd.DataFrame] = None,
        override_value: Optional[float] = None,
        override_reason: Optional[str] = None
    ) -> DailyPipelineResult:
        """
        执行每日决策流程

        Args:
            target_date: 目标日期 (YYYY-MM-DD)
            image_today_path: 今日图像路径
            image_yesterday_path: 昨日图像路径
            env_data: 环境数据 {temperature, humidity, light, ...}
            user_data: 用户历史数据
            override_value: 人工覆盖值 (可选)
            override_reason: 覆盖原因

        Returns:
            DailyPipelineResult
        """
        logger.info(f"开始每日决策流程: {target_date}")
        result = DailyPipelineResult(
            date=target_date,
            irrigation_amount=0.0,
            source="tsmixer"
        )

        try:
            # Step 1: 处理环境输入
            env_input = self._process_env_input(target_date, env_data)
            logger.debug(f"环境数据: temp={env_input.temperature}, humidity={env_input.humidity}")

            # Step 2: 构建时序窗口
            window = self._build_window(target_date, env_input, user_data)
            logger.debug(f"时序窗口: shape={window.shape}")

            # Step 3: TSMixer 预测
            prediction, pred_confidence = self._run_tsmixer(window)
            result.tsmixer_prediction = prediction
            logger.info(f"TSMixer 预测: {prediction:.2f} L/m²")

            # Step 4: 生育期预判 (Q7)
            if self.growth_stage_detector and image_today_path:
                stage, stage_conf = self._detect_growth_stage(image_today_path)
                result.growth_stage = stage
                result.growth_stage_confidence = stage_conf
                logger.debug(f"生育期: {stage} (confidence={stage_conf:.2f})")

            # Step 5: 知识库检索 (Q7)
            knowledge_refs = []
            if self.rag_service and result.growth_stage:
                knowledge_refs = self._retrieve_knowledge(result.growth_stage)
                result.knowledge_references = [
                    {"doc_id": r.doc_id, "snippet": r.snippet[:100]}
                    for r in knowledge_refs
                ]

            # Step 6: 长势评估 (需要 LLM)
            plant_response = None
            if self.llm_service and image_today_path and image_yesterday_path:
                plant_response = self._generate_plant_response(
                    image_today_path, image_yesterday_path,
                    env_input, knowledge_refs
                )
                result.plant_response = plant_response
                logger.debug(f"长势评估: trend={plant_response.trend.value}")

            # Step 7: 异常检测
            env_history = self._get_env_history(target_date, user_data)
            yesterday_irrigation = self._get_yesterday_irrigation(target_date, user_data)

            if plant_response:
                anomaly_result = self.anomaly_detector.detect(
                    prediction=prediction,
                    yesterday_irrigation=yesterday_irrigation,
                    plant_response=plant_response,
                    env_history=env_history
                )
            else:
                # 只做范围检测
                out_of_range, _ = self.anomaly_detector.check_range_only(prediction)
                anomaly_result = AnomalyResult(out_of_range=out_of_range)

            result.anomaly_result = anomaly_result
            self._add_anomaly_warnings(result, anomaly_result)

            # Step 8: RAG 辅助 (如有异常)
            if anomaly_result.has_anomaly() and self.rag_service:
                rag_advice = self._get_rag_advice(anomaly_result, result.growth_stage)
                result.rag_advice = rag_advice

            # Step 9: 构建 Working Context
            weekly_context = self._get_weekly_context()
            context = self.context_builder.build(
                system_prompt=self._get_system_prompt(),
                today_input={
                    "date": target_date,
                    "temperature": env_input.temperature,
                    "humidity": env_input.humidity,
                    "light": env_input.light,
                    "prediction": prediction,
                    "growth_stage": result.growth_stage
                },
                weekly_context=weekly_context,
                retrieval_results=[r.snippet for r in knowledge_refs[:3]] if knowledge_refs else None
            )
            logger.debug(f"Working Context: {context.total_tokens} tokens")

            # Step 10: 合理性复核 (SanityCheck)
            final_value = prediction
            if self.config.enable_sanity_check and self.llm_service and plant_response:
                sanity_result = self._run_sanity_check(
                    prediction, plant_response, env_input,
                    weekly_context, result.rag_advice
                )
                result.sanity_check_result = sanity_result

                if not sanity_result.get("is_consistent", True):
                    adjusted = sanity_result.get("adjusted_value", prediction)
                    if abs(adjusted - prediction) > 0.1:
                        final_value = adjusted
                        result.source = "sanity_adjusted"
                        result.suggestions.append(
                            f"SanityCheck 调整: {prediction:.2f} → {adjusted:.2f}"
                        )

            # 处理人工覆盖
            if override_value is not None:
                final_value = override_value
                result.source = "override"
                logger.info(f"人工覆盖: {override_value:.2f} L/m², 原因: {override_reason}")

            result.irrigation_amount = final_value

            # Step 11: 存储 Episode
            episode = self._create_episode(target_date, result, env_input, override_reason)
            self.episode_store.save(episode)
            result.episode_id = episode.date
            logger.info(f"Episode 已存储: {episode.date}")

            # Step 12: 完成
            logger.info(f"每日决策完成: {final_value:.2f} L/m² ({result.source})")
            return result

        except Exception as e:
            logger.error(f"每日决策流程错误: {e}")
            result.warnings.append(f"流程错误: {str(e)}")
            result.irrigation_amount = 5.0  # 默认值
            result.source = "fallback"
            return result

    def _process_env_input(
        self,
        date: str,
        env_data: Optional[dict]
    ) -> EnvInput:
        """处理环境输入"""
        if env_data:
            return self.env_handler.from_frontend(
                date=date,
                temperature=env_data.get("temperature", 25.0),
                humidity=env_data.get("humidity", 70.0),
                light=env_data.get("light", 8000.0)
            )
        else:
            # 使用默认值
            return EnvInput(
                date=date,
                temperature=25.0,
                humidity=70.0,
                light=8000.0
            )

    def _build_window(
        self,
        target_date: str,
        env_input: EnvInput,
        user_data: Optional[pd.DataFrame]
    ) -> pd.DataFrame:
        """构建时序窗口"""
        today_data = {
            "temperature": env_input.temperature,
            "humidity": env_input.humidity,
            "light": env_input.light,
            "leaf Instance Count": getattr(env_input, "leaf_count", 0.0),
            "leaf average mask": 0.0,
            "flower Instance Count": getattr(env_input, "flower_count", 0.0),
            "flower Mask Pixel Count": 0.0,
            "terminal average Mask Pixel Count": 0.0,
            "fruit Mask average": 0.0,
            "all leaf mask": 0.0,
            "Target": 0.0
        }

        return self.window_builder.build(
            data=user_data if user_data is not None else pd.DataFrame(),
            target_date=target_date,
            today_data=today_data
        )

    def _run_tsmixer(self, window) -> Tuple[float, float]:
        """运行 TSMixer 预测"""
        if self.tsmixer_service.is_available():
            return self.tsmixer_service.predict(
                pd.DataFrame(window, columns=self.window_builder.feature_columns),
                return_confidence=True
            )
        else:
            # Mock 预测
            return 5.0, 0.7

    def _detect_growth_stage(self, image_path: str) -> Tuple[str, float]:
        """检测生育期"""
        if self.growth_stage_detector:
            return self.growth_stage_detector.detect(image_path)
        return "unknown", 0.5

    def _retrieve_knowledge(self, growth_stage: str) -> list:
        """检索知识"""
        if self.rag_service:
            return self.rag_service.search_for_growth_stage(growth_stage, top_k=3)
        return []

    def _generate_plant_response(
        self,
        image_today: str,
        image_yesterday: str,
        env_input: EnvInput,
        knowledge_refs: list
    ) -> Optional[PlantResponse]:
        """生成长势评估 (需要实际 LLM 调用)"""
        # TODO: 实现完整的 LLM 调用
        # 这里返回 None，由调用方处理
        return None

    def _get_env_history(
        self,
        target_date: str,
        user_data: Optional[pd.DataFrame]
    ) -> list:
        """获取环境历史"""
        # 简化实现：返回空列表
        # 实际应从 user_data 或 episode_store 获取
        return []

    def _get_yesterday_irrigation(
        self,
        target_date: str,
        user_data: Optional[pd.DataFrame]
    ) -> float:
        """获取昨日灌水量"""
        # 简化实现
        return 5.0

    def _add_anomaly_warnings(
        self,
        result: DailyPipelineResult,
        anomaly: AnomalyResult
    ):
        """添加异常警告"""
        if anomaly.out_of_range:
            result.warnings.append(
                f"预测值 {result.tsmixer_prediction:.2f} 超出历史范围 [0.1, 15.0]"
            )
        if anomaly.trend_conflict:
            result.warnings.append(
                f"长势-灌水矛盾: {anomaly.trend_conflict_severity.value}"
            )
        if anomaly.env_anomaly:
            result.warnings.append(
                f"环境异常: {anomaly.env_anomaly_type.value if anomaly.env_anomaly_type else 'unknown'}"
            )

    def _get_rag_advice(
        self,
        anomaly: AnomalyResult,
        growth_stage: Optional[str]
    ) -> str:
        """获取 RAG 建议"""
        if self.rag_service:
            anomaly_type = None
            if anomaly.env_anomaly and anomaly.env_anomaly_type:
                anomaly_type = anomaly.env_anomaly_type.value
            elif anomaly.trend_conflict:
                anomaly_type = "trend_conflict"

            if anomaly_type:
                return self.rag_service.build_rag_advice(
                    anomaly_type=anomaly_type,
                    growth_stage=growth_stage
                )
        return ""

    def _get_weekly_context(self) -> Optional[str]:
        """获取周摘要上下文"""
        latest = self.weekly_store.get_latest()
        if latest:
            return latest.prompt_block
        return None

    def _get_system_prompt(self) -> str:
        """获取系统提示"""
        return """你是一个温室黄瓜灌溉专家。
根据植物长势、环境数据和历史经验，评估模型预测的灌水量是否合理。
如发现矛盾或异常，请给出调整建议。"""

    def _run_sanity_check(
        self,
        prediction: float,
        plant_response: PlantResponse,
        env_input: EnvInput,
        weekly_context: Optional[str],
        rag_advice: Optional[str]
    ) -> dict:
        """运行合理性复核"""
        if self.llm_service:
            return self.llm_service.sanity_check(
                tsmixer_prediction=prediction,
                plant_response=plant_response.to_dict(),
                today_input={
                    "temperature": env_input.temperature,
                    "humidity": env_input.humidity,
                    "light": env_input.light
                },
                weekly_context=weekly_context,
                rag_advice=rag_advice
            )
        return {"is_consistent": True}

    def _create_episode(
        self,
        date: str,
        result: DailyPipelineResult,
        env_input: EnvInput,
        override_reason: Optional[str]
    ) -> Episode:
        """创建 Episode"""
        episode = Episode(date=date)

        # 输入
        episode.inputs = EpisodeInputs(
            environment={
                "temperature": env_input.temperature,
                "humidity": env_input.humidity,
                "light": env_input.light
            }
        )

        # 预测
        episode.predictions = EpisodePredictions(
            tsmixer_raw=result.tsmixer_prediction,
            growth_stage=result.growth_stage,
            growth_stage_confidence=result.growth_stage_confidence
        )

        # 异常
        if result.anomaly_result:
            episode.anomalies = EpisodeAnomalies(
                out_of_range=result.anomaly_result.out_of_range,
                trend_conflict=result.anomaly_result.trend_conflict,
                trend_conflict_severity=result.anomaly_result.trend_conflict_severity.value,
                env_anomaly=result.anomaly_result.env_anomaly,
                env_anomaly_type=result.anomaly_result.env_anomaly_type.value if result.anomaly_result.env_anomaly_type else None
            )

        # 最终决策
        episode.final_decision = FinalDecision(
            value=result.irrigation_amount,
            source=result.source,
            override_reason=override_reason
        )

        # 知识引用
        episode.knowledge_references = result.knowledge_references

        return episode
