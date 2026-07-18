# 依赖
请你先查看AGENTS.md重点查看链接中的文档。
# 背景
我目前需要利用PaddleNLP对本系统能识别的实体进行扩充，补全presidio传统NER模型不足的短板。
我打算使用信息抽取information_extraction，并使用uie-medical-base作为医疗实体识别，使用uie-m-base作为通用实体识别。具体例子已经在example/paddle中给出。我目前对识别规则做了以下更改：
1.建立了统一实体规则ENTITY_CATALOG: dict[str, EntityDefinition]，之后脱敏用该字典的键作为唯一实体识别符

2.这里需要分别提取中文实体抽取、英文实体抽取和医疗实体抽取，分别给uie-m-base、uie-m-base、uie-medical-base，从而得到paddle_calls


# 要求

@app.post("/extract")
async def extract(text: str, schema: dict):
    taskflow = await factory.get_pipeline(schema)
    try:
        return taskflow(text)
    finally:
        await factory.return_pipeline(taskflow)  # 无论如何都要归还


```python
# 修改为异步函数，因为paddle请求加锁
@staticmethod
async def scan(
    text: str,
    service_container: ServiceContainer,
    profile: str | None = None,
    policy: DetectionPolicy | None = None,
) -> list[RecognizerResult]:
    if policy is None:
        if profile is None:
            raise ValueError("detection_policy or detection_profile is required")

        try:
            policy = service_container.detection_policy_factory.registry[profile]
        except KeyError as exc:
            raise ValueError("unknown built-in detection profile") from exc

    plan = service_container.detection_policy_factory.compile(policy)

    candidates: list[DetectionCandidate] = []

    # 1. Presidio
    if presidio_call is None:
        supported = set(service_container.analyzer.get_supported_entities())

        requested = [
            entity
            for entity in plan.entities
            if entity in supported
        ]
        
        for language in ["zh","en"]:
            results = service_container.analyzer.analyze(
                text=text,
                language=language,
                entities=requested,
                return_decision_process=policy.return_decision_process,
                allow_list=policy.allow_list,
            )

            candidates.extend(
                convert_presidio_results(
                    results=results,
                    language=language,
                )
            )

    # 2. PaddleNLP
    for call in plan.paddle_calls:
        if call is None:
            continue

        await raw_results = service_container.paddle_pipeline_factory.predict(
            text=text,
            call=call,
        )

        candidates.extend(
            convert_paddle_results(
                raw_results=raw_results,
                call=call,
            )
        )

    # 3. allow_list 必须再次统一应用
    # 因为 Presidio 已应用，但 Paddle 还没有
    candidates = _apply_allow_list(
        text=text,
        candidates=candidates,
        allow_list=policy.allow_list,
        match_mode=policy.allow_list_match,
    )

    # 4. Fusion
    fused = _fuse(
        candidates=candidates,
        entity_definitions=plan.entity_definitions,
        config=policy.fusion,
    )

    # 5. 统一为 Presidio RecognizerResult
    return [
        RecognizerResult(
            entity_type=item.entity_type,
            start=item.start,
            end=item.end,
            score=item.score,
            recognition_metadata={
                "recognizer_name": "fusion",
                "sources": item.metadata.get("sources", [item.source]),
                "model": item.model,
                "raw_label": item.raw_label,
            },
        )
        for item in fused
    ]
```
```python
import bisect
from app.policy.detection.plan import DetectionCandidate

# 模型置信度的修正系数
MODEL_COEFFICIENTS: dict[str, float] = {
    "zh_core_web_lg": 1.0,
    "en_core_web_lg": 1.0,
    "uie-medical-base": 1.0,
    "uie-m-base": 1.0,
}


def _fuse(
    candidates: list[DetectionCandidate],
    entity_priorities: dict[str, int],
    coefficients: dict[str, float] | None = None,
) -> list[DetectionCandidate]:
    coefficients = coefficients or MODEL_COEFFICIENTS
    if not candidates:
        return []

    # 0. 系数修正（就地），夹在 [0, 1]
    for candidate in candidates:
        factor = coefficients.get(candidate.model, 1.0)
        candidate.score = min(candidate.score * factor, 1.0)

    # 1. 规则(1)：完全相同 span + entity_type → 合并来源、取最高分
    merged: dict[tuple[str, int, int], DetectionCandidate] = {}
    for candidate in candidates:
        key = (candidate.entity_type, candidate.start, candidate.end)
        existing = merged.get(key)
        if existing is None:
            candidate.metadata["sources"] = [candidate.source]
            merged[key] = candidate
            continue
        if candidate.source not in existing.metadata["sources"]:
            existing.metadata["sources"].append(candidate.source)
        existing.score = max(existing.score, candidate.score)

    # 2. 非冲突最大化：加权区间调度 DP
    items = sorted(merged.values(), key=lambda c: c.end)
    ends = [c.end for c in items]
    # 权重：priority 主、score 辅；同分时 DP 的 >= 偏向"多留"
    weights = [
        entity_priorities.get(c.entity_type, 100) + c.score
        for c in items
    ]
    # p[i] = 最靠右且与 items[i] 不冲突（end <= start）的前驱下标 +1
    prev = [bisect.bisect_right(ends, items[i].start) for i in range(len(items))]

    dp = [0.0] * (len(items) + 1)
    take = [False] * len(items)
    for i in range(1, len(items) + 1):
        include = weights[i - 1] + dp[prev[i - 1]]
        exclude = dp[i - 1]
        if include >= exclude:
            dp[i] = include
            take[i - 1] = True
        else:
            dp[i] = exclude

    chosen: list[DetectionCandidate] = []
    i = len(items)
    while i > 0:
        if take[i - 1]:
            chosen.append(items[i - 1])
            i = prev[i - 1]
        else:
            i -= 1

    chosen.sort(key=lambda c: (c.start, c.end))
    return chosen
```