from presidio_analyzer import RecognizerResult

from app.policy.detection.plan import DetectionCandidate, PaddleCall

def convert_presidio_results(
    results: list[RecognizerResult],
    language: str,
) -> list[DetectionCandidate]:
    
    PRESIDIO_MODEL_BY_LANG = {"zh": "zh_core_web_lg", "en": "en_core_web_lg"}
    model = PRESIDIO_MODEL_BY_LANG[language]
    return [
        DetectionCandidate(
            entity_type=result.entity_type,
            start=result.start,
            end=result.end,
            score=result.score,
            source="presidio",
            model=model,                       # ← 新增：语言映射成模型名
            raw_label=result.entity_type,      # ← 可选：与 paddle 对称
            metadata={
                "presidio_metadata": result.recognition_metadata,
            },
        )
        for result in results
    ]


def convert_paddle_results(
    raw_results: list[dict],
    call: PaddleCall,
) -> list[DetectionCandidate]:
    candidates: list[DetectionCandidate] = []

    if not raw_results:
        return candidates

    document_result = raw_results[0]

    for schema_label, mentions in document_result.items():
        entity_type = call.label_to_entity.get(schema_label)
        if entity_type is None:
            continue

        for mention in mentions:
            # 分类结果可能没有 start/end；脱敏时忽略
            if "start" not in mention or "end" not in mention:
                continue

            score = float(mention.get("probability", 0.0))

            candidates.append(
                DetectionCandidate(
                    entity_type=entity_type,
                    start=int(mention["start"]),
                    end=int(mention["end"]),
                    score=score,
                    source="paddlenlp",
                    model=call.model,
                    raw_label=schema_label,
                )
            )

    return candidates