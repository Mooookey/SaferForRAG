from typing import TYPE_CHECKING, List
import bisect

from presidio_analyzer import RecognizerResult
from presidio_anonymizer import DeanonymizeEngine, EngineResult, OperatorConfig
from presidio_anonymizer.entities import OperatorResult

from app.policy.detection.policy import DetectionPolicy
from app.policy.Transformation_Policy import TransformationPolicy
from app.policy.detection.converter import convert_paddle_results, convert_presidio_results
from app.policy.detection.plan import DetectionCandidate

if TYPE_CHECKING:
    from app.services.container import ServiceContainer

# 模型置信度的修正系数
MODEL_COEFFICIENTS: dict[str, float] = {
    "zh_core_web_lg": 1.0,
    "en_core_web_lg": 1.0,
    "uie-medical-base": 1.0,
    "uie-m-base": 1.0,
}

class Sanitizer:
    @staticmethod
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

    @staticmethod
    def _apply_allow_list(
        text: str,
        candidates: list[DetectionCandidate],
        allow_list: list[str] | None,
        match_mode: str = "exact",
    ) -> list[DetectionCandidate]:
        # Presidio 候选已在 analyze 内过滤，这里只对 Paddle 候选放行
        if not allow_list:
            return candidates

        terms = {term.lower() for term in allow_list}

        def blocked(candidate: DetectionCandidate) -> bool:
            span = text[candidate.start:candidate.end].lower()
            if match_mode == "exact":
                return span in terms
            # "contains"：span 里包含任一白名单词
            return any(term in span for term in terms)

        return [
            candidate
            for candidate in candidates
            if candidate.source != "paddlenlp" or not blocked(candidate)
        ]


    @staticmethod
    async def scan(
        text: str,
        service_container: "ServiceContainer",
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

        # 1. Presidio：plan.presidio_calls 依次为 zh、en，None 表示跳过
        supported = set(service_container.analyzer.get_supported_entities())

        for call in plan.presidio_calls:
            if call is None:
                continue

            requested = [
                entity
                for entity in call.entities
                if entity in supported
            ]

            results = service_container.analyzer.analyze(
                text=text,
                language=call.language,
                entities=requested,
                return_decision_process=call.return_decision_process,
                allow_list=call.allow_list,
            )

            candidates.extend(
                convert_presidio_results(
                    results=results,
                    language=call.language,
                )
            )

        # 2. PaddleNLP
        for call in plan.paddle_calls:
            if call is None:
                continue

            raw_results = await service_container.paddle_pipeline_factory.predict(
                text=text,
                call=call,
            )

            candidates.extend(
                convert_paddle_results(
                    raw_results=raw_results,
                    call=call,
                )
            )

        # 3. allow_list：Presidio 已在 analyze 内应用，这里只补 Paddle
        candidates = Sanitizer._apply_allow_list(
            text=text,
            candidates=candidates,
            allow_list=policy.allow_list,
        )

        # 4. Fusion
        fused = Sanitizer._fuse(
            candidates=candidates,
            entity_priorities=plan.entity_priorities,
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

    @staticmethod
    def _get_placeholder_operator(
        transformation_policy: TransformationPolicy,
        entity_type: str,
    ):
        return next(
            (
                operator
                for operator in transformation_policy.llmguard_operator
                if operator.entity in ["DEFAULT", entity_type]
            ),
            None,
        )

    @staticmethod
    def _get_presidio_operator_config(
        transformation_policy: TransformationPolicy,
        entity_type: str,
    ) -> OperatorConfig:
        return (
            transformation_policy.presidio_operator.get(entity_type)
            or transformation_policy.presidio_operator["DEFAULT"]
        )

    @staticmethod
    async def anonymize(
        text: str,
        service_container: "ServiceContainer",
        transformation_profile: str | None = None,
        transformation_policy: TransformationPolicy | None = None,
        detection_profile: str | None = None,
        detection_policy: DetectionPolicy | None = None,
        analyzer_results: List[RecognizerResult] | None = None,
    ) -> EngineResult:
        if (
            analyzer_results is None
            and detection_profile is None
            and detection_policy is None
        ):
            raise ValueError(
                "detection_policy or detection_profile is required "
                "when analyzer_results is None"
            )
        if (transformation_policy is None) and (transformation_profile is None):
            raise ValueError("transformation_policy or transformation_profile is required")
        if transformation_policy is None:
            if transformation_profile not in service_container.tranformation_policy_factory.registry:
                raise ValueError("unknown built-in transformation profile")
            transformation_policy = service_container.tranformation_policy_factory.registry[
                transformation_profile
            ]

        if analyzer_results is None:
            analyzer_results = await Sanitizer.scan(
                text=text,
                service_container=service_container,
                profile=detection_profile,
                policy=detection_policy,
            )

        result_text: str = ""
        items: List[OperatorResult] = []
        cursor: int = 0

        for analyzer_result in sorted(analyzer_results, key=lambda result: result.start):
            result_text += text[cursor:analyzer_result.start]
            source_text: str = text[analyzer_result.start:analyzer_result.end]

            placeholder_operator = Sanitizer._get_placeholder_operator(
                transformation_policy,
                analyzer_result.entity_type,
            )
            if placeholder_operator is not None:
                single_result: EngineResult = placeholder_operator.transform(
                    text=source_text,
                    entities=[analyzer_result.entity_type],
                    analyzer_results=[
                        RecognizerResult(
                            entity_type=analyzer_result.entity_type,
                            start=0,
                            end=len(source_text),
                            score=analyzer_result.score,
                        )
                    ],
                )
                replacement_text: str = single_result.text
                operator_name: str = "placeholder"
            else:
                operator_config: OperatorConfig = Sanitizer._get_presidio_operator_config(
                    transformation_policy,
                    analyzer_result.entity_type,
                )
                single_result = service_container.anonymizer.anonymize(
                    text=source_text,
                    analyzer_results=[
                        RecognizerResult(
                            entity_type=analyzer_result.entity_type,
                            start=0,
                            end=len(source_text),
                            score=analyzer_result.score,
                        )
                    ],
                    operators={analyzer_result.entity_type: operator_config},
                )
                replacement_text = single_result.text
                operator_name = operator_config.operator_name

            start: int = len(result_text)
            result_text += replacement_text
            end: int = len(result_text)
            item = OperatorResult(
                start=start,
                end=end,
                entity_type=analyzer_result.entity_type,
                text=replacement_text,
                operator=operator_name,
            )
            item.original_text = source_text
            items.append(item)
            cursor = analyzer_result.end

        result_text += text[cursor:]
        return EngineResult(text=result_text, items=items)

    @staticmethod
    def deanonymize(
        text: str,
        engine_result: EngineResult,
        service_container: "ServiceContainer",
    ) -> str:
        encrypt_items: List[OperatorResult] = [
            item for item in engine_result.items if item.operator == "encrypt"
        ]
        placeholder_items: List[OperatorResult] = [
            item for item in engine_result.items if item.operator == "placeholder"
        ]

        if encrypt_items:
            decrypt_engine = DeanonymizeEngine()
            decrypt_result = decrypt_engine.deanonymize(
                text=text,
                entities=encrypt_items,
                operators={
                    item.entity_type: OperatorConfig(
                        "decrypt",
                        {
                            "key": service_container.tranformation_policy_factory.registry[
                                "encrypted"
                            ].presidio_operator["DEFAULT"].params["key"]
                        },
                    )
                    for item in encrypt_items
                },
            )
            text = decrypt_result.text

        if placeholder_items:
            text = service_container.tranformation_policy_factory.registry[
                "placeholder"
            ].inverse_transform(
                text=text,
                engine_result=EngineResult(text=engine_result.text, items=placeholder_items),
            )

        return text
