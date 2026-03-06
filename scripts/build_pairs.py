#!/usr/bin/env python
"""构建日期配对索引脚本"""

import sys
from pathlib import Path

import typer
from loguru import logger

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from cucumber_irrigation.processors.pairs_builder import PairsBuilder
from cucumber_irrigation.config import load_settings, get_project_root


app = typer.Typer(help="构建日期配对索引")


@app.command()
def build(
    images_dir: str = typer.Option(
        None,
        "--images-dir", "-i",
        help="图像目录路径"
    ),
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
    构建日期配对索引

    扫描图像目录，匹配 CSV 数据，生成配对索引 JSON 文件。
    """
    # 加载配置
    root = get_project_root()
    settings = load_settings(str(root / config))

    # 使用配置或命令行参数
    images_dir = images_dir or settings.get("data", {}).get("images_dir", "data/images")
    csv_path = csv_path or settings.get("data", {}).get("csv_path", "data/irrigation.csv")
    output = output or settings.get("output", {}).get("pairs_index", "output/pairs_index.json")

    # 转换为绝对路径
    images_dir = str(root / images_dir)
    csv_path = str(root / csv_path)
    output = str(root / output)

    logger.info(f"图像目录: {images_dir}")
    logger.info(f"CSV 文件: {csv_path}")
    logger.info(f"输出文件: {output}")

    # 构建配对
    try:
        builder = PairsBuilder(images_dir, csv_path)
        builder.save_pairs_index(output)

        # 打印统计信息
        pairs = builder.build_pairs()
        missing = builder.get_missing_dates()
        skipped = builder.get_skipped_pairs()

        logger.info(f"\n=== 统计信息 ===")
        logger.info(f"图像总数: {len(builder.image_dates)}")
        logger.info(f"有效配对: {len(pairs)}")
        logger.info(f"缺失日期: {len(missing)}")
        logger.info(f"跳过配对: {len(skipped)}")

        if missing:
            logger.warning(f"缺失日期列表: {missing[:10]}{'...' if len(missing) > 10 else ''}")

        if skipped:
            logger.warning(f"跳过配对原因:")
            for s in skipped[:5]:
                logger.warning(f"  - {s['date']}: {s['reason']}")
            if len(skipped) > 5:
                logger.warning(f"  ... 还有 {len(skipped) - 5} 个")

    except Exception as e:
        logger.error(f"构建失败: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
