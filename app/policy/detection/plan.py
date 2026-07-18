from dataclasses import dataclass, field
from typing import Any

UIE_GENERAL_MODEL = "uie-m-base"
UIE_MEDICAL_MODEL = "uie-medical-base"


@dataclass(frozen=True)
class PresidioCall:
    entities: tuple[str, ...]
    language: str
    allow_list: list[str] | None = None
    return_decision_process: bool = False


@dataclass(frozen=True)
class PaddleCall:
    model: str
    schema_lang: str | None
    schema: tuple[str, ...]
    label_to_entity: dict[str, str]


# 三个引擎槽位的位置契约，供 DetectionPlan 校验
_PRESIDIO_LANGS: tuple[str, str] = ("zh", "en")
_PADDLE_SLOTS: tuple[tuple[str, str | None], ...] = (
    (UIE_GENERAL_MODEL, "zh"),
    (UIE_GENERAL_MODEL, "en"),
    (UIE_MEDICAL_MODEL, None),
)


@dataclass(frozen=True)
class DetectionPlan:
    # 无对应实体时为 None，执行方跳过该引擎
    # 先中文，后英文
    presidio_calls: tuple[PresidioCall | None, PresidioCall | None]

    # 依次为通用中文抽取、英文通用抽取、医疗抽取
    paddle_calls: tuple[PaddleCall | None, PaddleCall | None, PaddleCall | None]

    # entity_type -> priority，供 _fuse 仲裁，令 plan 自包含
    entity_priorities: dict[str, int]

    def __post_init__(self) -> None:
        # 硬编码位置契约：presidio 先 zh 后 en
        for call, language in zip(self.presidio_calls, _PRESIDIO_LANGS):
            if call is not None and call.language != language:
                raise ValueError(
                    f"presidio_calls 位置契约错误：该槽位应为 '{language}'，"
                    f"实际为 '{call.language}'"
                )

        # 硬编码位置契约：paddle 依次为 uie-m-base/zh、uie-m-base/en、uie-medical-base
        for call, (model, schema_lang) in zip(self.paddle_calls, _PADDLE_SLOTS):
            if call is not None and (
                call.model != model or call.schema_lang != schema_lang
            ):
                raise ValueError(
                    f"paddle_calls 位置契约错误：该槽位应为 "
                    f"({model}, {schema_lang})，实际为 "
                    f"({call.model}, {call.schema_lang})"
                )


@dataclass
class DetectionCandidate:
    entity_type: str
    start: int
    end: int
    score: float

    source: str
    model: str | None = None
    raw_label: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)
