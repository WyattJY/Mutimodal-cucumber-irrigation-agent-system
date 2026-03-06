from __future__ import annotations
# Prediction Service - 预测编排服务
"""
每日预测编排服务

职责:
1. 协调 YOLO, TSMixer, LLM 服务
2. 处理冷启动情况
3. 构建 Working Context
4. 生成并保存 PlantResponse
5. 执行 SanityCheck
6. 创建 Episode
"""

import os
import sys
import json
import base64
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger

from app.models.schemas import (
    DailyPredictResult, PlantResponseResult, SanityCheckResult,
    PredictOptions, PredictionSource, RAGReference, YoloMetrics
)
from app.services.yolo_service import yolo_service
from app.services.tsmixer_service import tsmixer_service
from app.services.llm_service import llm_service
from app.services.memory_service import memory_service

# 项目路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
IMAGES_DIR = DATA_DIR / "images"
RESPONSES_DIR = OUTPUT_DIR / "responses"
YOLO_METRICS_DIR = OUTPUT_DIR / "yolo_metrics"

# 添加 src 到路径
SRC_DIR = PROJECT_ROOT.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# 尝试导入核心模块
try:
    from cucumber_irrigation.models.episode import (
        Episode, EpisodeInputs, EpisodePredictions,
        EpisodeAnomalies, FinalDecision
    )
    EPISODE_MODEL_AVAILABLE = True
except ImportError:
    EPISODE_MODEL_AVAILABLE = False
    logger.warning("Episode 模型导入失败，使用简化版本")

# 导入 RAG 服务
try:
    from cucumber_irrigation.services.local_rag_service import LocalRAGService, LocalRAGConfig
    _rag_service = LocalRAGService(config=LocalRAGConfig(top_k=3))
    RAG_AVAILABLE = _rag_service.is_available
    logger.info(f"[prediction_service] LocalRAGService 可用: {RAG_AVAILABLE}")
except Exception as e:
    _rag_service = None
    RAG_AVAILABLE = False
    logger.warning(f"[prediction_service] LocalRAGService 导入失败: {e}")


class PredictionService:
    """
    每日预测编排服务

    编排完整的预测流程:
    1. 保存/获取图片
    2. YOLO 推理
    3. 查找昨日图片 (冷启动检测)
    4. TSMixer 预测
    5. 生育期检测
    6. RAG 检索 (可选)
    7. 构建 Working Context
    8. 生成 PlantResponse
    9. SanityCheck (可选)
    10. 创建 Episode
    11. 保存结果
    """

    def __init__(self):
        """初始化预测服务"""
        # 确保目录存在
        RESPONSES_DIR.mkdir(parents=True, exist_ok=True)
        YOLO_METRICS_DIR.mkdir(parents=True, exist_ok=True)
        IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    async def predict_daily(
        self,
        date: str,
        image_path: Optional[str] = None,
        image_base64: Optional[str] = None,
        env_data: Optional[dict] = None,
        options: Optional[PredictOptions] = None
    ) -> DailyPredictResult:
        """
        执行完整的每日预测流程

        Args:
            date: 日期 (YYYY-MM-DD 或 MMDD 格式)
            image_path: 图片路径 (可选)
            image_base64: 图片 Base64 (可选)
            env_data: 环境数据 (可选)
            options: 预测选项

        Returns:
            DailyPredictResult: 完整的预测结果
        """
        options = options or PredictOptions()
        warnings = []
        suggestions = []

        try:
            # 1. 标准化日期格式
            normalized_date = self._normalize_date(date)
            logger.info(f"开始每日预测: {normalized_date}")

            # 2. 获取或保存图片
            image_today_path, image_today_b64 = await self._get_or_save_image(
                normalized_date, image_path, image_base64
            )

            if not image_today_path:
                raise ValueError(f"找不到日期 {normalized_date} 的图片")

            # 3. YOLO 推理
            yolo_today = await self._run_yolo(image_today_path, normalized_date)
            yolo_metrics = YoloMetrics.from_raw(yolo_today) if yolo_today else None

            # 4. 查找昨日图片 (冷启动检测)
            image_yesterday_path, image_yesterday_b64, yolo_yesterday, is_cold_start = \
                await self._find_yesterday_data(normalized_date)

            if is_cold_start:
                warnings.append("冷启动模式：没有历史数据进行对比分析")
                suggestions.append("建议连续上传多天图片以获得完整的趋势分析")

            # 5. 获取或构建环境数据
            env_data = env_data or self._get_default_env_data(normalized_date)

            # 6. TSMixer 预测
            tsmixer_prediction = await self._run_tsmixer(normalized_date, env_data, yolo_today)

            # 6.5 RAG 检索 (新增)
            rag_results = []
            rag_advice = None
            if options.use_rag and RAG_AVAILABLE and _rag_service:
                rag_results, rag_advice = await self._search_rag(
                    growth_stage=None,  # 将在 PlantResponse 之后更新
                    env_data=env_data,
                    yolo_today=yolo_today
                )
                if rag_results:
                    logger.info(f"RAG 检索到 {len(rag_results)} 条相关知识")

            # 7. 生成 PlantResponse
            plant_response = await self._generate_plant_response(
                image_today_b64=image_today_b64,
                image_yesterday_b64=image_yesterday_b64,
                yolo_today=yolo_today,
                yolo_yesterday=yolo_yesterday,
                env_data=env_data,
                is_cold_start=is_cold_start
            )

            # 8. SanityCheck (可选)
            sanity_check = None
            final_value = tsmixer_prediction
            source = PredictionSource.TSMIXER

            if options.run_sanity_check and plant_response:
                # 获取周摘要上下文
                weekly_context = await memory_service.get_weekly_prompt_block()

                # 如果有 PlantResponse，根据生育期再次检索 RAG
                if plant_response.growth_stage and RAG_AVAILABLE and _rag_service:
                    rag_results, rag_advice = await self._search_rag(
                        growth_stage=plant_response.growth_stage,
                        env_data=env_data,
                        yolo_today=yolo_today
                    )

                sanity_check = await llm_service.sanity_check(
                    tsmixer_prediction=tsmixer_prediction,
                    plant_response=plant_response.model_dump() if plant_response else {},
                    env_data=env_data,
                    weekly_context=weekly_context,
                    rag_advice=rag_advice  # 传递 RAG 建议
                )

                if not sanity_check.is_consistent:
                    final_value = sanity_check.adjusted_value
                    source = PredictionSource.SANITY_ADJUSTED
                    warnings.append(f"SanityCheck 调整: {tsmixer_prediction:.2f} → {final_value:.2f}")

            # 9. 保存 PlantResponse
            response_saved_path = None
            if options.save_response and plant_response:
                response_saved_path = await self._save_plant_response(
                    date=normalized_date,
                    plant_response=plant_response,
                    yolo_today=yolo_today,
                    yolo_yesterday=yolo_yesterday,
                    env_data=env_data,
                    image_today_path=image_today_path,
                    image_yesterday_path=image_yesterday_path
                )

            # 10. 创建 Episode
            episode_id = None
            if options.save_episode:
                episode_id = await self._create_and_save_episode(
                    date=normalized_date,
                    env_data=env_data,
                    yolo_today=yolo_today,
                    tsmixer_prediction=tsmixer_prediction,
                    plant_response=plant_response,
                    sanity_check=sanity_check,
                    final_value=final_value,
                    source=source,
                    is_cold_start=is_cold_start
                )

            # 11. 构建返回结果
            # 转换 RAG 结果为 RAGReference 列表
            rag_refs = [
                RAGReference(
                    doc_id=r.doc_id,
                    title=f"FAO56 - Page {r.page}" if r.is_fao56 else r.source,
                    snippet=r.snippet[:200] + "..." if len(r.snippet) > 200 else r.snippet,
                    relevance=r.relevance_score
                )
                for r in rag_results
            ] if rag_results else []

            return DailyPredictResult(
                date=normalized_date,
                irrigation_amount=final_value,
                source=source,
                is_cold_start=is_cold_start,
                yolo_metrics=yolo_metrics,
                plant_response=plant_response,
                sanity_check=sanity_check,
                rag_references=rag_refs,  # 使用真实 RAG 结果
                warnings=warnings,
                suggestions=suggestions,
                episode_id=episode_id,
                response_saved_path=response_saved_path
            )

        except Exception as e:
            logger.error(f"每日预测失败: {e}")
            raise

    # =========================================================================
    # 辅助方法
    # =========================================================================

    def _normalize_date(self, date: str) -> str:
        """标准化日期格式为 YYYY-MM-DD"""
        # 如果是 MMDD 格式
        if len(date) == 4 and date.isdigit():
            return f"2024-{date[:2]}-{date[2:]}"
        # 如果是 YYYYMMDD 格式
        if len(date) == 8 and date.isdigit():
            return f"{date[:4]}-{date[4:6]}-{date[6:]}"
        # 已经是 YYYY-MM-DD 格式
        return date

    def _date_to_filename(self, date: str) -> str:
        """将日期转换为文件名格式 (MMDD)"""
        parts = date.split("-")
        if len(parts) == 3:
            return f"{parts[1]}{parts[2]}"
        return date

    async def _get_or_save_image(
        self,
        date: str,
        image_path: Optional[str],
        image_base64: Optional[str]
    ) -> Tuple[Optional[str], Optional[str]]:
        """获取或保存图片，返回 (路径, base64)"""

        # 如果提供了 base64，保存到文件
        if image_base64:
            filename = f"{self._date_to_filename(date)}.jpg"
            save_path = IMAGES_DIR / filename

            try:
                image_data = base64.b64decode(image_base64)
                with open(save_path, 'wb') as f:
                    f.write(image_data)
                return str(save_path), image_base64
            except Exception as e:
                logger.error(f"保存图片失败: {e}")

        # 如果提供了路径
        if image_path and os.path.exists(image_path):
            with open(image_path, 'rb') as f:
                image_data = f.read()
            return image_path, base64.b64encode(image_data).decode('utf-8')

        # 尝试从默认目录查找
        date_prefix = self._date_to_filename(date)
        for ext in ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']:
            potential_path = IMAGES_DIR / f"{date_prefix}{ext}"
            if potential_path.exists():
                with open(potential_path, 'rb') as f:
                    image_data = f.read()
                return str(potential_path), base64.b64encode(image_data).decode('utf-8')

        return None, None

    async def _run_yolo(self, image_path: str, date: str) -> dict:
        """运行 YOLO 推理"""
        try:
            # 检查是否有缓存的指标
            metrics_file = YOLO_METRICS_DIR / f"{self._date_to_filename(date)}.json"
            if metrics_file.exists():
                with open(metrics_file, 'r', encoding='utf-8') as f:
                    return json.load(f)

            # 运行 YOLO
            if yolo_service.is_available:
                with open(image_path, 'rb') as f:
                    image_bytes = f.read()

                metrics, _ = yolo_service.process_bytes(
                    image_bytes,
                    filename=self._date_to_filename(date)
                )

                # 保存指标
                with open(metrics_file, 'w', encoding='utf-8') as f:
                    json.dump(metrics, f, ensure_ascii=False, indent=2)

                return metrics
            else:
                logger.warning("YOLO 服务不可用，使用默认指标")
                return self._get_default_yolo_metrics()

        except Exception as e:
            logger.error(f"YOLO 推理失败: {e}")
            return self._get_default_yolo_metrics()

    def _get_default_yolo_metrics(self) -> dict:
        """获取默认 YOLO 指标"""
        return {
            "leaf Instance Count": 8.0,
            "leaf average mask": 5000.0,
            "flower Instance Count": 2.0,
            "flower Mask Pixel Count": 1000.0,
            "terminal average Mask Pixel Count": 500.0,
            "fruit Mask average": 300.0,
            "all leaf mask": 40000.0
        }

    async def _find_yesterday_data(
        self,
        date: str
    ) -> Tuple[Optional[str], Optional[str], Optional[dict], bool]:
        """
        查找昨日数据

        支持回溯最多 3 天

        Returns:
            (image_path, image_base64, yolo_metrics, is_cold_start)
        """
        try:
            current_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return None, None, None, True

        # 回溯最多 3 天
        for days_back in range(1, 4):
            yesterday = current_date - timedelta(days=days_back)
            yesterday_str = yesterday.strftime("%Y-%m-%d")

            # 查找图片
            image_path, image_b64 = await self._get_or_save_image(
                yesterday_str, None, None
            )

            if image_path:
                # 获取 YOLO 指标
                metrics_file = YOLO_METRICS_DIR / f"{self._date_to_filename(yesterday_str)}.json"
                yolo_metrics = None

                if metrics_file.exists():
                    with open(metrics_file, 'r', encoding='utf-8') as f:
                        yolo_metrics = json.load(f)
                else:
                    # 运行 YOLO
                    yolo_metrics = await self._run_yolo(image_path, yesterday_str)

                return image_path, image_b64, yolo_metrics, False

        # 没有找到历史数据，冷启动
        return None, None, None, True

    def _get_default_env_data(self, date: str) -> dict:
        """获取默认环境数据"""
        return {
            "temperature": 25.0,
            "humidity": 70.0,
            "light": 50000.0,
            "date": date
        }

    async def _run_tsmixer(
        self,
        date: str,
        env_data: dict,
        yolo_metrics: dict
    ) -> float:
        """运行 TSMixer 预测"""
        try:
            if tsmixer_service.is_available:
                features = tsmixer_service.build_features(
                    env_data=env_data,
                    yolo_metrics=yolo_metrics,
                    target_date=date
                )
                result = tsmixer_service.predict(features)

                # 如果返回的是字典，提取预测值
                if isinstance(result, dict):
                    return float(result.get("predicted_value", 5.0))
                return float(result)
            else:
                logger.warning("TSMixer 服务不可用，使用默认值")
                return 5.0

        except Exception as e:
            logger.error(f"TSMixer 预测失败: {e}")
            return 5.0

    async def _search_rag(
        self,
        growth_stage: Optional[str],
        env_data: dict,
        yolo_today: dict
    ) -> Tuple[List, Optional[str]]:
        """
        执行 RAG 检索

        Args:
            growth_stage: 生育期 (vegetative/flowering/fruiting/mixed)
            env_data: 环境数据
            yolo_today: YOLO 指标

        Returns:
            (RAG结果列表, 格式化的RAG建议文本)
        """
        if not RAG_AVAILABLE or _rag_service is None:
            return [], None

        try:
            # 根据生育期搜索
            if growth_stage:
                results = _rag_service.search_for_growth_stage(
                    growth_stage=growth_stage,
                    top_k=3
                )
            else:
                # 构建通用查询
                query = "cucumber irrigation water requirement greenhouse"
                results = _rag_service.search(query, top_k=3)

            if not results:
                return [], None

            # 格式化为建议文本
            advice_parts = ["## 知识库参考"]
            for i, r in enumerate(results, 1):
                source_tag = "[FAO56]" if r.is_fao56 else "[文献]"
                advice_parts.append(f"{i}. {source_tag} {r.snippet[:200]}...")

            rag_advice = "\n".join(advice_parts)

            return results, rag_advice

        except Exception as e:
            logger.warning(f"RAG 检索失败: {e}")
            return [], None

    async def _generate_plant_response(
        self,
        image_today_b64: str,
        image_yesterday_b64: Optional[str],
        yolo_today: dict,
        yolo_yesterday: Optional[dict],
        env_data: dict,
        is_cold_start: bool
    ) -> Optional[PlantResponseResult]:
        """生成 PlantResponse"""
        try:
            return await llm_service.generate_plant_response(
                image_today_b64=image_today_b64,
                image_yesterday_b64=image_yesterday_b64,
                yolo_today=yolo_today,
                yolo_yesterday=yolo_yesterday,
                env_data=env_data,
                is_cold_start=is_cold_start
            )
        except Exception as e:
            logger.error(f"生成 PlantResponse 失败: {e}")
            return None

    async def _save_plant_response(
        self,
        date: str,
        plant_response: PlantResponseResult,
        yolo_today: dict,
        yolo_yesterday: Optional[dict],
        env_data: dict,
        image_today_path: str,
        image_yesterday_path: Optional[str]
    ) -> str:
        """
        保存 PlantResponse 到 output/responses/{date}.json
        """
        try:
            response_data = {
                "date": date,
                "created_at": datetime.now().isoformat(),
                "prompt_version": "v2",
                "image_today": image_today_path,
                "image_yesterday": image_yesterday_path,
                "yolo_today": yolo_today,
                "yolo_yesterday": yolo_yesterday,
                "env_today": env_data,
                "response": plant_response.model_dump(),
                "is_cold_start": plant_response.is_cold_start
            }

            save_path = RESPONSES_DIR / f"{date}.json"
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(response_data, f, ensure_ascii=False, indent=2)

            logger.info(f"PlantResponse 已保存: {save_path}")
            return str(save_path)

        except Exception as e:
            logger.error(f"保存 PlantResponse 失败: {e}")
            return ""

    async def _create_and_save_episode(
        self,
        date: str,
        env_data: dict,
        yolo_today: dict,
        tsmixer_prediction: float,
        plant_response: Optional[PlantResponseResult],
        sanity_check: Optional[SanityCheckResult],
        final_value: float,
        source: PredictionSource,
        is_cold_start: bool
    ) -> Optional[str]:
        """创建并保存 Episode"""
        try:
            if EPISODE_MODEL_AVAILABLE:
                episode = Episode(
                    date=date,
                    inputs=EpisodeInputs(
                        environment=env_data,
                        yolo_metrics=yolo_today
                    ),
                    predictions=EpisodePredictions(
                        tsmixer_raw=tsmixer_prediction,
                        plant_response=plant_response.model_dump() if plant_response else {},
                        sanity_check=sanity_check.model_dump() if sanity_check else {},
                        growth_stage=plant_response.growth_stage if plant_response else None
                    ),
                    anomalies=EpisodeAnomalies(),
                    final_decision=FinalDecision(
                        value=final_value,
                        source=source.value
                    )
                )
                return await memory_service.save_episode(episode)
            else:
                # 简化版本
                episode_data = {
                    "date": date,
                    "inputs": {
                        "environment": env_data,
                        "yolo_metrics": yolo_today
                    },
                    "predictions": {
                        "tsmixer_raw": tsmixer_prediction,
                        "plant_response": plant_response.model_dump() if plant_response else {},
                        "sanity_check": sanity_check.model_dump() if sanity_check else {},
                        "is_cold_start": is_cold_start
                    },
                    "final_decision": {
                        "value": final_value,
                        "source": source.value
                    },
                    "created_at": datetime.now().isoformat()
                }
                return await memory_service.save_episode(episode_data)

        except Exception as e:
            logger.error(f"创建 Episode 失败: {e}")
            return None

    async def get_plant_response(self, date: str) -> Optional[dict]:
        """获取指定日期的 PlantResponse"""
        try:
            normalized_date = self._normalize_date(date)
            response_file = RESPONSES_DIR / f"{normalized_date}.json"

            if response_file.exists():
                with open(response_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None

        except Exception as e:
            logger.error(f"获取 PlantResponse 失败: {e}")
            return None

    async def list_plant_responses(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """列出 PlantResponse 文件"""
        try:
            responses = []

            for file in RESPONSES_DIR.glob("*.json"):
                try:
                    file_date = file.stem  # 获取文件名 (不含扩展名)

                    # 日期过滤
                    if start_date and file_date < start_date:
                        continue
                    if end_date and file_date > end_date:
                        continue

                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        responses.append({
                            "date": file_date,
                            "file": str(file),
                            "is_cold_start": data.get("is_cold_start", False),
                            "trend": data.get("response", {}).get("trend")
                        })
                except Exception:
                    continue

            return sorted(responses, key=lambda x: x["date"], reverse=True)

        except Exception as e:
            logger.error(f"列出 PlantResponse 失败: {e}")
            return []


# 创建服务单例
prediction_service = PredictionService()
