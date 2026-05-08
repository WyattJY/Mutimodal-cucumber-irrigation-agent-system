# `src/cucumber_irrigation/processors` 目录说明

## 目录定位
离线处理器：构建图像配对索引、计算增长率统计等（供批量生成与分析脚本使用）。

[上级目录](../DIRECTORY.md)

## 本目录文件概览
- `__init__.py`
- `pairs_builder.py`
- `stats_calculator.py`

## 脚本/模块说明（本目录内）
### `__init__.py`
- 作用/意义: 数据处理器
- 路径: `src/cucumber_irrigation/processors/__init__.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `src/cucumber_irrigation/__init__.py`

### `pairs_builder.py`
- 作用/意义: 日期配对构建器
- 路径: `src/cucumber_irrigation/processors/pairs_builder.py`

**被谁引用/调用（代码级）**
- `scripts/build_pairs.py`

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `__future__`
- `dataclasses`
- `datetime`
- `json`
- `loguru`
- `pandas`
- `pathlib`
- `re`
- `typing`

### `stats_calculator.py`
- 作用/意义: 增长率统计计算器
- 路径: `src/cucumber_irrigation/processors/stats_calculator.py`

**被谁引用/调用（代码级）**
- `scripts/calc_growth_stats.py`

**引用了谁（内部依赖）**
（无）

**引用了谁（外部依赖）**
- `dataclasses`
- `datetime`
- `json`
- `loguru`
- `numpy`
- `pandas`
- `pathlib`
- `typing`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `scripts/build_pairs.py`
- `scripts/calc_growth_stats.py`

**本目录引用了谁（跨目录）**
- `src/cucumber_irrigation/__init__.py`
