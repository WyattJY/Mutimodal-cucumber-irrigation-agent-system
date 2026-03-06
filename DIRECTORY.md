# `.` 目录说明

## 目录定位
项目根目录（AgriAgent/AGRI-COPILOT 温室黄瓜灌溉智能体系统）。本仓库同时包含核心算法包、后端 API、前端 UI、数据/模型与论文级文档。

## 子目录
- `annotations/` → [`annotations/DIRECTORY.md`](annotations/DIRECTORY.md)
- `backend/` → [`backend/DIRECTORY.md`](backend/DIRECTORY.md)
- `config/` → [`config/DIRECTORY.md`](config/DIRECTORY.md)
- `configs/` → [`configs/DIRECTORY.md`](configs/DIRECTORY.md)
- `data/` → [`data/DIRECTORY.md`](data/DIRECTORY.md)
- `db/` → [`db/DIRECTORY.md`](db/DIRECTORY.md)
- `docs/` → [`docs/DIRECTORY.md`](docs/DIRECTORY.md)
- `frontend/` → [`frontend/DIRECTORY.md`](frontend/DIRECTORY.md)
- `logs/` → [`logs/DIRECTORY.md`](logs/DIRECTORY.md)
- `models/` → [`models/DIRECTORY.md`](models/DIRECTORY.md)
- `mongodb/` → [`mongodb/DIRECTORY.md`](mongodb/DIRECTORY.md)
- `output/` → [`output/DIRECTORY.md`](output/DIRECTORY.md)
- `outputs/` → [`outputs/DIRECTORY.md`](outputs/DIRECTORY.md)
- `prompts/` → [`prompts/DIRECTORY.md`](prompts/DIRECTORY.md)
- `reports/` → [`reports/DIRECTORY.md`](reports/DIRECTORY.md)
- `scripts/` → [`scripts/DIRECTORY.md`](scripts/DIRECTORY.md)
- `src/` → [`src/DIRECTORY.md`](src/DIRECTORY.md)
- `tests/` → [`tests/DIRECTORY.md`](tests/DIRECTORY.md)

## 本目录文件概览
- `.env`
- `.gitignore`
- `cankao.html`
- `cankao2.html`
- `cankao3.html`
- `cankao4.html`
- `cankao5.html`
- `config.ini`
- `design_ui.md`
- `pyproject.toml`
- `README.md`
- `requirements_ui.md`
- `start.sh`
- `status.sh`
- `stop.sh`
- `task_ui.md`
- `uv.lock`

## 脚本/模块说明（本目录内）
### `start.sh`
- 作用/意义: ============================================ AGRI-COPILOT Startup Script Cucumber Irrigation Intelligent Agent System ============================================
- 路径: `start.sh`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `status.sh`
- `stop.sh`

### `status.sh`
- 作用/意义: ============================================ AGRI-COPILOT Status Script ============================================ Colors
- 路径: `status.sh`

**被谁引用/调用（代码级）**
- `start.sh`

**引用了谁（内部依赖）**
（无）

### `stop.sh`
- 作用/意义: ============================================ AGRI-COPILOT Stop Script Cucumber Irrigation Intelligent Agent System ============================================ Colors
- 路径: `stop.sh`

**被谁引用/调用（代码级）**
- `start.sh`

**引用了谁（内部依赖）**
（无）

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
（无）

**本目录引用了谁（跨目录）**
（无）
