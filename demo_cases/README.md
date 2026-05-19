# AgriAgent 演示与测试材料

本目录用于本机演示、接口测试和后续录屏。默认服务地址：

- 前端：`http://127.0.0.1:3003`
- 后端：`http://127.0.0.1:8000`
- Swagger：`http://127.0.0.1:8000/docs`

## 1. 启动平台

在项目根目录执行：

```bash
./start.sh
./status.sh
```

停止服务：

```bash
./stop.sh
```

## 2. 写入 2024 验证试验数据

录屏前先把演示数据切换到验证试验区间，时间范围为 `2024-08-20` 到 `2024-10-31`：

```bash
backend/.venv/bin/python demo_cases/scripts/seed_2024_validation_data.py
```

脚本会生成 73 条日尺度 episode、11 条周度汇总，并把默认测试图复制到。当前黄瓜项目可用的原始监控图为 `2880×1620`，不再使用 YOLO 数据集里的 `640×640` 切片图做演示推理：

- `demo_cases/images/cucumber_monitor_original_0420.jpg`
- `data/images/1030.jpg`
- `data/images/1031.jpg`

## 3. 页面演示顺序

1. 打开首页 `http://127.0.0.1:3003`，先展示指挥舱首屏：最新日期、今日建议灌水量、环境指标和风险提示。
2. 在指挥舱趋势图依次点击 `14D`、`7D`，随后向下滚动，完整展示趋势图、昨日/今日视觉生长分析和入口按钮。
3. 进入 `今日决策链`，展示环境感知、植物响应、模型预测、最终决策和智能体洞察的完整链路。
4. 进入 `灌水预测`，上传 `demo_cases/images/cucumber_monitor_original_0420.jpg`，日期填写 `2024-10-31`，展示视觉特征融合后的建议灌水量。
5. 进入 `视觉分析`，上传同一张测试图，展示 YOLO11n 实例分割结果和叶片、花朵、顶芽、果实统计。
6. 进入 `数据分析`，在左上角输入：`最近长势如何？灌水是否合适？有哪些注意的地方`，等待右侧智能助手给出基于历史数据的回复。
7. 进入 `智能问答`，直接输入：`开花期最佳灌水量是多少？`，该问题不强制出图，只展示文本型知识问答。
8. 点击 `上传文献`，现场上传桌面论文 PDF，等待页面显示 `chunks` 与 `indexed/fallback_indexed`，证明系统完成解析、分块、索引入库。
9. PDF 入库后输入：`论文中的是如何进行视觉模型改进的`，该问题会命中文献中的视觉模型改进内容，并展示相关图像资产。
10. 最后进入 `系统设置`，短暂展示模型服务和系统配置入口。
11. 如需展示多智能体后端能力，运行 `demo_cases/scripts/smoke_demo.sh`，重点看 `/api/agent/decision` 和 `/api/knowledge/query` 输出。

## 3. 一键接口冒烟测试

服务启动后执行：

```bash
demo_cases/scripts/smoke_demo.sh
```

脚本会依次验证：

- 后端健康状态
- RAG 状态
- 演示知识库上传
- 知识库检索
- RAG 增强问答
- 非流式聊天回复
- 视觉模型状态和可用图像日期
- 图片分割接口
- 灌水量预测接口
- 多智能体决策接口

## 4. 录屏脚本

如果本机安装了 Playwright，可以执行：

```bash
cd demo_cases
npm exec --yes --package playwright -- node scripts/record_ui_demo.mjs
```

录屏脚本会先预热后端接口，并自动检查桌面论文 PDF 是否已上传。默认 PDF 文件名：
录屏脚本会先预热后端接口，并清理同名旧上传记录。随后在页面中现场上传桌面论文 PDF，展示解析、分块和索引入库状态。默认 PDF 文件名：

- `~/Desktop/Multimodal fusion-driven precision irrigation decision model for greenhouse cucumber integrating enhanced YOLO11n and TSMixer.pdf`

录屏输出目录：

- `demo_cases/recordings/`
- `demo_cases/screenshots/`

Playwright 默认生成 WebM 视频。如果需要 MP4，本机需要额外安装完整 `ffmpeg` 后转换。Playwright 自带的 recorder ffmpeg 只能满足录屏依赖，不适合作为通用 MP4 转码器。

```bash
demo_cases/scripts/convert_recording_to_mp4.sh
```

## 5. 推荐录屏口播重点

- 这个系统不是单一预测页面，而是“视觉识别 + 时序预测 + RAG 问答 + 多智能体决策”的一体化温室黄瓜灌水平台。
- 指挥舱与数据分析页面展示的是 2024 年 8 月到 10 月验证试验数据，不是随机构造数据。
- 视觉模块负责从真实温室图像中提取叶片、花朵、果实、顶芽等表型指标。
- 预测模块将环境数据、历史灌水量和视觉指标融合，输出今日建议灌水量。
- RAG 模块会区分普通灌水知识问题和论文图文问题：普通问题只给文本答复，涉及论文视觉模型改进时才展示相关图像。
- Agent 决策接口在后端编排 YOLOAgent、TSMixerAgent、RAGAgent 和 MainAgent，适合展示多智能体协同链路。
