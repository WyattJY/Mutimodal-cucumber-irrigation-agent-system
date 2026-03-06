#!/usr/bin/env python
"""计算增长率统计脚本"""

import sys
from pathlib import Path

import typer
from loguru import logger

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from cucumber_irrigation.processors.stats_calculator import StatsCalculator
from cucumber_irrigation.config import load_settings, get_project_root


app = typer.Typer(help="计算增长率统计")


@app.command()
def calc(
    csv_path: str = typer.Option(
        None,
        "--csv", "-c",
        help="CSV 文件路径"
    ),
    output: str = typer.Option(
        None,
        "--output", "-o",
        help="输出文件路径"
    ),
    config: str = typer.Option(
        "configs/settings.yaml",
        "--config",
        help="配置文件路径"
    )
):
    """
    计算全生育期增长率统计

    从 CSV 文件计算 all_leaf_mask 的增长率统计，
    包括日均增长、标准差、阈值等。
    """
    # 加载配置
    root = get_project_root()
    settings = load_settings(str(root / config))

    # 使用配置或命令行参数
    csv_path = csv_path or settings.get("data", {}).get("csv_path", "data/irrigation.csv")
    output = output or settings.get("output", {}).get("growth_stats", "output/growth_stats.json")

    # 转换为绝对路径
    csv_path = str(root / csv_path)
    output = str(root / output)

    logger.info(f"CSV 文件: {csv_path}")
    logger.info(f"输出文件: {output}")

    # 计算统计
    try:
        calculator = StatsCalculator(csv_path)
        stats = calculator.calc_growth_stats()
        calculator.save_stats(output)

        # 打印详细信息
        logger.info(f"\n=== 增长率统计 ===")
        logger.info(f"日期范围: {stats.date_start} ~ {stats.date_end}")
        logger.info(f"总天数: {stats.total_days}")
        logger.info(f"起始值: {stats.all_leaf_mask_start:.2f}")
        logger.info(f"结束值: {stats.all_leaf_mask_end:.2f}")
        logger.info(f"总增长: {stats.all_leaf_mask_total_growth:.2f}")
        logger.info(f"日均增长: {stats.all_leaf_mask_daily_avg:.2f}")
        logger.info(f"标准差: {stats.all_leaf_mask_daily_std:.2f}")
        logger.info(f"\n=== 趋势判定阈值 ===")
        logger.info(f"better: 日增长 > {stats.threshold_better:.2f}")
        logger.info(f"worse: 日增长 < {stats.threshold_worse:.2f}")
        logger.info(f"same: 介于两者之间")

    except Exception as e:
        logger.error(f"计算失败: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
