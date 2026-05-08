# 植株生长评估请求

## 日期
{date}

## 今日 YOLO 表型指标
```json
{yolo_today}
```

## 昨日 YOLO 表型指标
```json
{yolo_yesterday}
```

## 今日环境数据
```json
{env_today}
```

## 全生育期增长率统计（用于趋势判定参考）
```json
{growth_stats}
```

## 指标说明
- **leaf Instance Count**: 叶片实例数量
- **leaf average mask**: 单叶平均像素面积
- **flower Instance Count**: 花朵数量
- **flower Mask Pixel Count**: 花朵总像素面积
- **terminal average Mask Pixel Count**: 顶芽平均像素面积
- **fruit Mask average**: 果实平均像素面积
- **all leaf mask**: 全部叶片总像素面积（主要参考指标）

## 趋势判定规则
根据增长率统计中的阈值：
- 今日 all_leaf_mask - 昨日 all_leaf_mask > threshold_better → trend = "better"
- 今日 all_leaf_mask - 昨日 all_leaf_mask < threshold_worse → trend = "worse"
- 其他情况 → trend = "same"

**注意**: 数值判定仅作参考，最终判断应结合图像观察。如果图像显示明显异常（萎蔫、黄化等），即使数值正常也应判定为 "worse"。

请仔细对比下方两张图像，结合上述数据，输出 JSON 格式的评估结果。
