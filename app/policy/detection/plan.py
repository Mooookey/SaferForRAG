from dataclasses import dataclass, field
from typing import Any

UIE_GENERAL_MODEL = "uie-m-base"
UIE_MEDICAL_MODEL = "uie-medical-base"


@dataclass(frozen=True)
class PresidioCall:
    entities: tuple[str, ...]
    allow_list: list[str] | None = None
    return_decision_process: bool = False


@dataclass(frozen=True)
class PaddleCall:
    model: str
    schema_lang: str | None
    schema: tuple[str, ...]
    label_to_entity: dict[str, str]


@dataclass(frozen=True)
class DetectionPlan:
    # 无对应实体时为 None，执行方跳过该引擎
    presidio_call: PresidioCall | None

    # 依次为通用中文抽取、英文通用抽取、医疗抽取
    paddle_calls: tuple[PaddleCall | None, PaddleCall | None, PaddleCall | None]


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
