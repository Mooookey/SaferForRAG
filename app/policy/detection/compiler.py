from app.policy.detection.catalog import ENTITY_CATALOG
from app.policy.detection.plan import (
    UIE_GENERAL_MODEL,
    UIE_MEDICAL_MODEL,
    DetectionPlan,
    PaddleCall,
    PresidioCall,
)
from app.policy.detection.policy import DetectionPolicy


def _build_paddle_call(
    model: str,
    schema_lang: str | None,
    schema: list[str],
    label_to_entity: dict[str, str],
) -> PaddleCall | None:
    if not schema:
        return None

    return PaddleCall(
        model=model,
        schema_lang=schema_lang,
        schema=tuple(schema),
        label_to_entity=label_to_entity,
    )


class DetectionPolicy_Factory:
    def __init__(self) -> None:
        self.registry: dict[str, DetectionPolicy] = {}
        self.entity_catalog = dict(ENTITY_CATALOG)
        self._register_policy(
            DetectionPolicy(
                policy_name="default",
                return_decision_process=False,
                entities=list(self.entity_catalog.keys()),
            )
        )

    def _register_policy(self, policy: DetectionPolicy) -> None:
        self.registry[policy.policy_name] = policy

    def compile(self, policy: DetectionPolicy) -> DetectionPlan:
        catalog = {
            **self.entity_catalog,
            **policy.custom_entities,
        }

        unknown = set(policy.entities) - set(catalog)
        if unknown:
            raise ValueError(f"Unknown entities: {sorted(unknown)}")

        # 从完整目录中提取策略需要的实体定义
        definitions = {
            entity: catalog[entity]
            for entity in policy.entities
        }

        # 抽取presidio支持的实体
        # CustomEntityDefinition 没有 presidio_entity，只走 paddle
        presidio_entities = tuple(
            presidio_entity
            for definition in definitions.values()
            if (presidio_entity := getattr(definition, "presidio_entity", None))
            is not None
        )

        presidio_call = (
            PresidioCall(
                entities=presidio_entities,
                allow_list=policy.allow_list,
                return_decision_process=policy.return_decision_process,
            )
            if presidio_entities
            else None
        )

        # 三次抽取各自的 schema，以及从 schema 标签反查 canonical entity 的映射
        zh_schema: list[str] = []
        zh_label_to_entity: dict[str, str] = {}
        en_schema: list[str] = []
        en_label_to_entity: dict[str, str] = {}
        medical_schema: list[str] = []
        medical_label_to_entity: dict[str, str] = {}

        for entity_type, definition in definitions.items():
            general_labels = definition.uie_general_labels or {}

            zh_label = general_labels.get("zh")
            if zh_label is not None:
                zh_schema.append(zh_label)
                zh_label_to_entity[zh_label] = entity_type

            en_label = general_labels.get("en")
            if en_label is not None:
                en_schema.append(en_label)
                en_label_to_entity[en_label] = entity_type

            if definition.uie_medical is not None:
                medical_schema.append(definition.uie_medical)
                medical_label_to_entity[definition.uie_medical] = entity_type

        # uie-medical-base 只使用中文，不接受 schema_lang
        paddle_calls: tuple[
            PaddleCall | None, PaddleCall | None, PaddleCall | None
        ] = (
            _build_paddle_call(
                UIE_GENERAL_MODEL, "zh", zh_schema, zh_label_to_entity
            ),
            _build_paddle_call(
                UIE_GENERAL_MODEL, "en", en_schema, en_label_to_entity
            ),
            _build_paddle_call(
                UIE_MEDICAL_MODEL, None, medical_schema, medical_label_to_entity
            ),
        )

        return DetectionPlan(
            presidio_call=presidio_call,
            paddle_calls=paddle_calls,
        )
