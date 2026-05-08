#!/usr/bin/env python
"""批量生成 PlantResponse 脚本"""

import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from loguru import logger
from tqdm import tqdm

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from cucumber_irrigation.config import load_settings, load_api_key, get_project_root
from cucumber_irrigation.services.llm_service import LLMService
from cucumber_irrigation.services.image_service import ImageService
from cucumber_irrigation.utils.prompt_builder import PromptBuilder
from cucumber_irrigation.models.plant_response import PlantResponse


app = typer.Typer(help="批量生成 PlantResponse")

# 线程安全的结果收集
results_lock = threading.Lock()
errors_lock = threading.Lock()


def load_pairs_index(path: str) -> dict:
    """加载配对索引"""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_growth_stats(path: str) -> dict:
    """加载增长率统计"""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def process_single_pair(
    pair: dict,
    output_path: Path,
    llm_service: LLMService,
    prompt_builder: PromptBuilder,
    system_prompt: str,
    user_template: str,
    examples: list,
    stats_data: dict,
    prompt_version: str
) -> dict:
    """处理单个配对，返回结果或错误"""
    date = pair["date"]
    output_file = output_path / f"{date}.json"

    # 跳过已存在的结果
    if output_file.exists():
        return {"status": "skipped", "date": date}

    try:
        # 编码图像
        image_today_b64 = ImageService.encode_image(pair["image_today"])
        image_yesterday_b64 = ImageService.encode_image(pair["image_yesterday"])

        # 构建 User Prompt
        user_prompt = prompt_builder.build_user_prompt(
            template=user_template,
            date=date,
            yolo_today=pair.get("yolo_today"),
            yolo_yesterday=pair.get("yolo_yesterday"),
            env_today=pair.get("env_today"),
            growth_stats=stats_data
        )

        # 调用 LLM
        response_json = llm_service.generate_plant_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            image_today_b64=image_today_b64,
            image_yesterday_b64=image_yesterday_b64,
            examples=examples
        )

        # 解析响应
        plant_response = PlantResponse.from_json(response_json)

        # 保存结果
        result = {
            "date": date,
            "created_at": datetime.now().isoformat(),
            "prompt_version": prompt_version,
            "image_today": pair["image_today"],
            "image_yesterday": pair["image_yesterday"],
            "yolo_today": pair.get("yolo_today"),
            "yolo_yesterday": pair.get("yolo_yesterday"),
            "env_today": pair.get("env_today"),
            "response": plant_response.to_dict(),
            "raw_response": response_json
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        return {
            "status": "success",
            "date": date,
            "trend": plant_response.trend.value
        }

    except Exception as e:
        return {
            "status": "error",
            "date": date,
            "error": str(e)
        }


@app.command()
def generate(
    pairs_index: str = typer.Option(
        None,
        "--pairs", "-p",
        help="配对索引文件路径"
    ),
    growth_stats: str = typer.Option(
        None,
        "--stats", "-s",
        help="增长率统计文件路径"
    ),
    output_dir: str = typer.Option(
        None,
        "--output", "-o",
        help="输出目录路径"
    ),
    prompt_version: str = typer.Option(
        "v1",
        "--prompt-version", "-v",
        help="Prompt 版本"
    ),
    limit: Optional[int] = typer.Option(
        None,
        "--limit", "-l",
        help="限制处理数量（用于测试）"
    ),
    skip: int = typer.Option(
        0,
        "--skip",
        help="跳过前 N 个配对"
    ),
    workers: int = typer.Option(
        1,
        "--workers", "-w",
        help="并行线程数"
    ),
    config: str = typer.Option(
        "configs/settings.yaml",
        "--config",
        help="配置文件路径"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="仅打印配置，不实际调用 LLM"
    )
):
    """
    批量生成 PlantResponse

    读取配对索引，对每个配对调用 LLM 生成评估结果。
    支持多线程并行处理。
    """
    # 加载配置
    root = get_project_root()
    settings = load_settings(str(root / config))

    # 使用配置或命令行参数
    pairs_index = pairs_index or settings.get("output", {}).get("pairs_index", "output/pairs_index.json")
    growth_stats = growth_stats or settings.get("output", {}).get("growth_stats", "output/growth_stats.json")
    output_dir = output_dir or settings.get("output", {}).get("responses_dir", "output/responses")
    prompts_dir = settings.get("prompts", {}).get("dir", "prompts/plant_response")

    # 转换为绝对路径
    pairs_index = str(root / pairs_index)
    growth_stats = str(root / growth_stats)
    output_dir = str(root / output_dir)
    prompts_dir = str(root / prompts_dir)

    logger.info(f"配对索引: {pairs_index}")
    logger.info(f"增长率统计: {growth_stats}")
    logger.info(f"输出目录: {output_dir}")
    logger.info(f"Prompt 版本: {prompt_version}")
    logger.info(f"并行线程数: {workers}")

    # 加载数据
    try:
        pairs_data = load_pairs_index(pairs_index)
        stats_data = load_growth_stats(growth_stats)
    except FileNotFoundError as e:
        logger.error(f"文件不存在: {e}")
        logger.info("请先运行 build_pairs.py 和 calc_growth_stats.py")
        raise typer.Exit(1)

    pairs = pairs_data.get("pairs", [])
    total_pairs = len(pairs)

    logger.info(f"总配对数: {total_pairs}")

    if skip > 0:
        pairs = pairs[skip:]
        logger.info(f"跳过前 {skip} 个，剩余: {len(pairs)}")

    if limit:
        pairs = pairs[:limit]
        logger.info(f"限制处理: {limit} 个")

    if dry_run:
        logger.info("=== DRY RUN 模式 ===")
        logger.info(f"将处理 {len(pairs)} 个配对")
        for i, pair in enumerate(pairs[:3]):
            logger.info(f"  [{i+1}] {pair['date']}")
        if len(pairs) > 3:
            logger.info(f"  ... 还有 {len(pairs) - 3} 个")
        return

    # 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 初始化服务
    api_key = load_api_key()
    llm_settings = settings.get("llm", {})

    # 为每个线程创建独立的 LLM 服务实例
    def create_llm_service():
        return LLMService(
            api_key=api_key,
            base_url=llm_settings.get("base_url", "https://yunwu.zeabur.app/v1"),
            model=llm_settings.get("model", "gpt-5.2"),
            temperature=llm_settings.get("temperature", 0.3),
            max_tokens=llm_settings.get("max_tokens", 2000),
            timeout=llm_settings.get("timeout", 120)
        )

    prompt_builder = PromptBuilder(prompts_dir)

    # 加载 Prompt 模板
    try:
        system_prompt = prompt_builder.load_system_prompt(prompt_version)
        user_template = prompt_builder.load_user_template(prompt_version)
        examples = prompt_builder.load_examples(prompt_version)
    except FileNotFoundError as e:
        logger.error(f"Prompt 模板不存在: {e}")
        raise typer.Exit(1)

    logger.info(f"加载了 {len(examples)} 个 few-shot 示例")

    # 并行处理
    results = []
    errors = []
    skipped = 0

    # 使用 ThreadLocal 存储每个线程的 LLM 服务
    thread_local = threading.local()

    def get_llm_service():
        if not hasattr(thread_local, "llm_service"):
            thread_local.llm_service = create_llm_service()
        return thread_local.llm_service

    def process_wrapper(pair):
        llm_service = get_llm_service()
        return process_single_pair(
            pair=pair,
            output_path=output_path,
            llm_service=llm_service,
            prompt_builder=prompt_builder,
            system_prompt=system_prompt,
            user_template=user_template,
            examples=examples,
            stats_data=stats_data,
            prompt_version=prompt_version
        )

    with ThreadPoolExecutor(max_workers=workers) as executor:
        # 提交所有任务
        futures = {executor.submit(process_wrapper, pair): pair for pair in pairs}

        # 使用 tqdm 显示进度
        with tqdm(total=len(pairs), desc=f"生成 PlantResponse ({workers} 线程)") as pbar:
            for future in as_completed(futures):
                result = future.result()

                if result["status"] == "success":
                    results.append(result)
                    logger.debug(f"完成: {result['date']} -> {result['trend']}")
                elif result["status"] == "error":
                    errors.append(result)
                    logger.error(f"失败: {result['date']}: {result['error']}")
                else:  # skipped
                    skipped += 1

                pbar.update(1)

    # 输出统计
    logger.info(f"\n=== 处理完成 ===")
    logger.info(f"成功: {len(results)}")
    logger.info(f"跳过: {skipped}")
    logger.info(f"失败: {len(errors)}")

    if results:
        # 统计趋势分布
        trend_counts = {}
        for r in results:
            trend = r["trend"]
            trend_counts[trend] = trend_counts.get(trend, 0) + 1

        logger.info(f"趋势分布:")
        for trend, count in sorted(trend_counts.items()):
            logger.info(f"  {trend}: {count} ({count/len(results)*100:.1f}%)")

    if errors:
        # 保存错误日志
        error_file = output_path / "errors.json"
        with open(error_file, "w", encoding="utf-8") as f:
            json.dump(errors, f, indent=2, ensure_ascii=False)
        logger.warning(f"错误日志已保存: {error_file}")


@app.command()
def single(
    date: str = typer.Argument(..., help="日期 YYYY-MM-DD"),
    config: str = typer.Option(
        "configs/settings.yaml",
        "--config",
        help="配置文件路径"
    ),
    prompt_version: str = typer.Option(
        "v1",
        "--prompt-version", "-v",
        help="Prompt 版本"
    )
):
    """
    处理单个日期的配对

    用于调试和测试单个配对的效果。
    """
    root = get_project_root()
    settings = load_settings(str(root / config))

    # 加载配对索引
    pairs_index = str(root / settings.get("output", {}).get("pairs_index", "output/pairs_index.json"))
    growth_stats = str(root / settings.get("output", {}).get("growth_stats", "output/growth_stats.json"))
    prompts_dir = str(root / settings.get("prompts", {}).get("dir", "prompts/plant_response"))

    try:
        pairs_data = load_pairs_index(pairs_index)
        stats_data = load_growth_stats(growth_stats)
    except FileNotFoundError as e:
        logger.error(f"文件不存在: {e}")
        raise typer.Exit(1)

    # 查找指定日期
    pair = None
    for p in pairs_data.get("pairs", []):
        if p["date"] == date:
            pair = p
            break

    if not pair:
        logger.error(f"未找到日期: {date}")
        raise typer.Exit(1)

    logger.info(f"处理日期: {date}")
    logger.info(f"今日图像: {pair['image_today']}")
    logger.info(f"昨日图像: {pair['image_yesterday']}")

    # 初始化服务
    api_key = load_api_key()
    llm_settings = settings.get("llm", {})

    llm_service = LLMService(
        api_key=api_key,
        base_url=llm_settings.get("base_url", "https://yunwu.zeabur.app/v1"),
        model=llm_settings.get("model", "gpt-5.2"),
        temperature=llm_settings.get("temperature", 0.3),
        max_tokens=llm_settings.get("max_tokens", 2000),
        timeout=llm_settings.get("timeout", 60)
    )

    prompt_builder = PromptBuilder(prompts_dir)
    system_prompt = prompt_builder.load_system_prompt(prompt_version)
    user_template = prompt_builder.load_user_template(prompt_version)
    examples = prompt_builder.load_examples(prompt_version)

    # 编码图像
    image_today_b64 = ImageService.encode_image(pair["image_today"])
    image_yesterday_b64 = ImageService.encode_image(pair["image_yesterday"])

    # 构建 User Prompt
    user_prompt = prompt_builder.build_user_prompt(
        template=user_template,
        date=date,
        yolo_today=pair.get("yolo_today"),
        yolo_yesterday=pair.get("yolo_yesterday"),
        env_today=pair.get("env_today"),
        growth_stats=stats_data
    )

    logger.info("\n=== User Prompt ===")
    print(user_prompt[:500] + "..." if len(user_prompt) > 500 else user_prompt)

    # 调用 LLM
    logger.info("\n=== 调用 LLM ===")
    response_json = llm_service.generate_plant_response(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        image_today_b64=image_today_b64,
        image_yesterday_b64=image_yesterday_b64,
        examples=examples
    )

    logger.info("\n=== LLM 响应 ===")
    print(response_json)

    # 解析响应
    plant_response = PlantResponse.from_json(response_json)
    logger.info(f"\n=== 解析结果 ===")
    logger.info(f"趋势: {plant_response.trend.value}")
    logger.info(f"置信度: {plant_response.confidence}")
    logger.info(f"生育期: {plant_response.growth_stage.value}")


if __name__ == "__main__":
    app()
