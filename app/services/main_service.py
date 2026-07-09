from typing import List

from llm_guard import scan_output, scan_prompt
from presidio_analyzer import RecognizerResult
from presidio_anonymizer import DeanonymizeEngine, EngineResult, OperatorConfig
from presidio_anonymizer.entities import OperatorResult

from app.policy.Detection_Policy import DetectionPolicy
from app.policy.Check_Policy import CheckPolicy
from app.policy.Transformation_Policy import TransformationPolicy
from app.services.container import service_container


class Santilizer:
    @staticmethod
    def _merge_overlapping_results(
        analyzer_results: list[RecognizerResult],
    ) -> list[RecognizerResult]:
        sorted_results: list[RecognizerResult] = sorted(
            analyzer_results,
            key=lambda result: (result.start, result.end),
        )
        merged_results: list[RecognizerResult] = []

        for result in sorted_results:
            if not merged_results:
                merged_results.append(result)
                continue

            last_result: RecognizerResult = merged_results[-1]
            has_overlap: bool = result.start < last_result.end and last_result.start < result.end

            if has_overlap:
                result_length: int = result.end - result.start
                last_result_length: int = last_result.end - last_result.start
                if result_length > last_result_length:
                    merged_results[-1] = result
            else:
                merged_results.append(result)

        return merged_results

    @staticmethod
    def scan(
        text: str,
        profile: str | None = None,
        policy: DetectionPolicy | None = None
    ) -> List[RecognizerResult]:
        if (policy is None) and (profile is None):
            raise ValueError("detection_policy or detection_profile is required")

        if (policy is None):
            if profile not in service_container.detection_policy_factory.registry:
                raise ValueError("unknown built-in detection profile")
            policy = service_container.detection_policy_factory.registry[
                profile
            ]

        analyzer_results_zh = service_container.analyzer.analyze(
            text=text,
            language="zh",
            entities=policy.entities,
            return_decision_process=policy.return_decision_process,
            allow_list=policy.allow_list,
        )
        analyzer_results_en = service_container.analyzer.analyze(
            text=text,
            language="en",
            entities=policy.entities,
            return_decision_process=policy.return_decision_process,
            allow_list=policy.allow_list,
        )

        analyzer_results: list[RecognizerResult] = Santilizer._merge_overlapping_results(
            analyzer_results_zh + analyzer_results_en
        )
        return analyzer_results

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

    # 没细看，但粗略看起来没有什么问题，只是实现上比我想得复杂
    @staticmethod
    def anonymize(
        text: str,
        transformation_profile: str | None = None,
        transformation_policy: TransformationPolicy | None = None,
        detection_policy: DetectionPolicy | None = None,
        analyzer_results: List[RecognizerResult] | None = None,
    ) -> EngineResult:
        # 处理参数不合法
        if (analyzer_results is None) and (detection_policy is None):
            raise ValueError("detection_policy is required when analyzer_results is None")
        if (transformation_policy is None) and (transformation_profile is None):
            raise ValueError("transformation_policy or transformation_profile is required")
        if transformation_policy is None:
            if transformation_profile not in service_container.tranformation_policy_factory.registry:
                raise ValueError("unknown built-in transformation profile")
            transformation_policy = service_container.tranformation_policy_factory.registry[
                transformation_profile
            ]

        if analyzer_results is None:
            analyzer_results = Santilizer.scan(text, policy=detection_policy)

        result_text: str = ""
        items: List[OperatorResult] = []
        cursor: int = 0

        for analyzer_result in sorted(analyzer_results, key=lambda result: result.start):
            result_text += text[cursor:analyzer_result.start]
            source_text: str = text[analyzer_result.start:analyzer_result.end]

            placeholder_operator = Santilizer._get_placeholder_operator(
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
                operator_config: OperatorConfig = Santilizer._get_presidio_operator_config(
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
    def deanonymize(text: str, engine_result: EngineResult) -> str:
        # 提取被encrypt或者被placeholder的实体
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

class Guardian:
    @staticmethod
    def check_input(
        text: str,
        profile: str | None = None,
        policy: CheckPolicy | None = None,
    ):
        if (policy is None) and (profile is None):
            raise ValueError("check policy or check profile is required")
        if policy is None:
            if profile not in service_container.check_input_policy_factory.registry:
                raise ValueError("unknown built-in input check profile")
            policy = service_container.check_input_policy_factory.registry[profile]

        sanitized_prompt, results_valid, results_score = scan_prompt(
            policy.scanners,
            text
        )
        return (sanitized_prompt, results_valid, results_score)

    @staticmethod
    def check_output(
        prompt: str,
        text: str,
        profile: str | None = None,
        policy: CheckPolicy | None = None,
    ):
        if (policy is None) and (profile is None):
            raise ValueError("check policy or check profile is required")
        if policy is None:
            if profile not in service_container.check_output_policy_factory.registry:
                raise ValueError("unknown built-in output check profile")
            policy = service_container.check_output_policy_factory.registry[profile]

        sanitized_output, results_valid, results_score = scan_output(
            policy.scanners,
            prompt,
            text
        )
        return (sanitized_output, results_valid, results_score)


if __name__ == "__main__":
    print("-----------测试样例一：placeholder有效性---------------")
    # policy = DetectionPolicy(policy_name="default")
    text = "我的身份证号是110101199003074493"
    results = Santilizer.scan(text, "default")
    anonymized = Santilizer.anonymize(
        text=text,
        transformation_profile="placeholder",
        analyzer_results=results
    )
    deannymized = Santilizer.deanonymize(anonymized.text,anonymized)
    print(anonymized)
    print(deannymized)
