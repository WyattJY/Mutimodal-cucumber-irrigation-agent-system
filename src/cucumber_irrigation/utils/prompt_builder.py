"""Prompt 构建器"""

import json
from pathlib import Path
from typing import Optional, List


class PromptBuilder:
    """Prompt 构建器"""

    def __init__(self, prompts_dir: str = "prompts/plant_response"):
        """
        初始化 Prompt 构建器

        Args:
            prompts_dir: Prompt 模板目录
        """
        self.prompts_dir = Path(prompts_dir)

    def load_system_prompt(self, version: str = "v1") -> str:
        """
        加载 System Prompt

        Args:
            version: 版本号

        Returns:
            System Prompt 内容
        """
        path = self.prompts_dir / f"system_{version}.md"
        if not path.exists():
            raise FileNotFoundError(f"System Prompt 不存在: {path}")

        return path.read_text(encoding="utf-8")

    def load_user_template(self, version: str = "v1") -> str:
        """
        加载 User Prompt 模板

        Args:
            version: 版本号

        Returns:
            User Prompt 模板内容
        """
        path = self.prompts_dir / f"user_{version}.md"
        if not path.exists():
            raise FileNotFoundError(f"User Prompt 模板不存在: {path}")

        return path.read_text(encoding="utf-8")

    def load_examples(self, version: str = "v1") -> List[dict]:
        """
        加载 Few-shot 示例

        Args:
            version: 版本号

        Returns:
            示例列表
        """
        path = self.prompts_dir / f"examples_{version}.jsonl"
        if not path.exists():
            return []

        examples = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    examples.append(json.loads(line))

        return examples

    def build_user_prompt(
        self,
        template: str,
        date: str,
        yolo_today: Optional[dict],
        yolo_yesterday: Optional[dict],
        env_today: Optional[dict],
        growth_stats: dict
    ) -> str:
        """
        构建完整的 User Prompt

        Args:
            template: User Prompt 模板
            date: 日期
            yolo_today: 今日 YOLO 指标
            yolo_yesterday: 昨日 YOLO 指标
            env_today: 今日环境数据
            growth_stats: 全生育期增长率统计

        Returns:
            填充后的 User Prompt
        """
        # 处理可能为空的数据
        yolo_today_str = json.dumps(
            yolo_today or {"note": "数据缺失"},
            indent=2,
            ensure_ascii=False
        )
        yolo_yesterday_str = json.dumps(
            yolo_yesterday or {"note": "数据缺失"},
            indent=2,
            ensure_ascii=False
        )
        env_today_str = json.dumps(
            env_today or {"note": "数据缺失"},
            indent=2,
            ensure_ascii=False
        )
        growth_stats_str = json.dumps(
            growth_stats,
            indent=2,
            ensure_ascii=False
        )

        return template.format(
            date=date,
            yolo_today=yolo_today_str,
            yolo_yesterday=yolo_yesterday_str,
            env_today=env_today_str,
            growth_stats=growth_stats_str
        )
