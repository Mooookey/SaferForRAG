from typing import List

from llm_guard.output_scanners import Deanonymize
from llm_guard.vault import Vault
from presidio_analyzer import RecognizerResult
from presidio_anonymizer import EngineResult, OperatorConfig
from presidio_anonymizer.entities import OperatorResult


class Irreversible_Operator:
    def __init__(self, entity: str):
        self.entity = entity
        self.operator_config: OperatorConfig = OperatorConfig("replace", {})


class Placeholder_Operator:
    def __init__(self, entity: str, max_count: int = 65535):
        if max_count <= 1:
            raise ValueError("计数器循环必须大于1")
        self.entity = entity
        self.count = 1
        self.max_count = max_count

    def _incr_count(self) -> None:
        self.count += 1
        if self.count == self.max_count:
            self.count = 1

    def transform(
        self,
        text: str,
        entities: List[str],
        analyzer_results: List[RecognizerResult],
    ) -> EngineResult:
        result_text: str = ""
        items: List[OperatorResult] = []
        cursor: int = 0

        # 按照脱敏结果analyzer_results.start对序列进行placeholder脱敏，当前指针是cur
        # 下面就是一个指针cur移动并拼接字符串的功能
        for analyzer_result in sorted(analyzer_results, key=lambda result: result.start):
            if self.entity != "DEFAULT" and analyzer_result.entity_type not in entities:
                continue

            result_text += text[cursor:analyzer_result.start]
            original_text: str = text[analyzer_result.start:analyzer_result.end]
            placeholder: str = f"<{analyzer_result.entity_type}_{self.count}>"
            start: int = len(result_text)
            result_text += placeholder
            end: int = len(result_text)

            item = OperatorResult(
                start=start,
                end=end,
                entity_type=analyzer_result.entity_type,
                text=placeholder,
                operator="placeholder",
            )
            item.original_text = original_text
            items.append(item)

            cursor = analyzer_result.end
            self._incr_count()

        result_text += text[cursor:]
        return EngineResult(text=result_text, items=items)

    @staticmethod
    def inverse_transform(text: str, engine_result: EngineResult) -> str:
        vault = Vault()
        for item in engine_result.items:
            if item.operator == "placeholder":
                vault.append((item.text, item.original_text))

        deanonymizer = Deanonymize(vault)
        deanonymized_text, _, _ = deanonymizer.scan("", text)
        return deanonymized_text


class Hash_Operator:
    def __init__(
        self,
        entity: str,
        salt_enabled: bool = False,
        salt: str = "security-processer",
    ):
        self.entity = entity
        params: dict[str, str] = {}
        if not salt_enabled:
            params["salt"] = salt
        self.operator_config: OperatorConfig = OperatorConfig("hash", params)


class Encrypt_Operator:
    def __init__(self, entity: str, encryption_key: str):
        self.entity = entity
        self.operator_config: OperatorConfig = OperatorConfig(
            "encrypt",
            {"key": encryption_key},
        )


class Mask_Operator:
    def __init__(self, entity: str):
        self.entity = entity
        self.operator_config: OperatorConfig = OperatorConfig(
            "mask",
            {
                "masking_char": "*",
                "chars_to_mask": 65535,
                "from_end": False,
            },
        )
