from pydantic import BaseModel, Field, field_validator

PRESIDIO_DEFAULT_ENTITIES = [
    "CREDIT_CARD",
    "CRYPTO",
    "DATE_TIME",
    "EMAIL_ADDRESS",
    "IBAN_CODE",
    "IP_ADDRESS",
    "MAC_ADDRESS",
    "NRP",
    "LOCATION",
    "PERSON",
    "MEDICAL_LICENSE",
    "URL",
    "CN_ID_CARD",
]


class EntityDefinition(BaseModel):
    entity_type: str

    # Presidio 不支持时为 None
    presidio_entity: str | None = None

    # uie-m-base 的自然语言 prompt
    uie_general_labels: dict[str, str] | None = Field(default_factory=dict)

    # uie-medical-base 只使用中文
    uie_medical: str | None = None

    # 发生冲突时，数值越大优先级越高
    priority: int = 100

    # ============ 校验器 ============
    @field_validator("presidio_entity")
    @classmethod
    def validate_presidio_entity(cls, v: str | None) -> str | None:
        if v is None:
            return v

        if v not in PRESIDIO_DEFAULT_ENTITIES:
            raise ValueError(
                f"presidio_entity must be what presidio engine supports "
                f"got invalid value: {v}"
            )
        return v

    @field_validator("entity_type")
    @classmethod
    def validate_entity_type(cls, v: str) -> str:
        """限制1: entity_type 必须全大写"""
        if not v.isupper():
            raise ValueError(f"entity_type must be all uppercase, got '{v}'")
        return v

    @field_validator("uie_general_labels")
    @classmethod
    def validate_labels(cls, v: dict[str, str] | None) -> dict[str, str] | None:
        """限制2: uie_general_labels 的键只能是 'zh' 或 'en'"""
        if v is None:
            return v

        allowed_keys = {"zh", "en"}
        invalid_keys = set(v.keys()) - allowed_keys
        if invalid_keys:
            raise ValueError(
                f"uie_general_labels keys must be only 'zh' or 'en', "
                f"got invalid keys: {invalid_keys}"
            )
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: int) -> int:
        """限制3: priority 必须在 [1, 1000] 范围内"""
        if not (1 <= v <= 1000):
            raise ValueError(f"priority must be between 1 and 1000, got {v}")
        return v


class CustomEntityDefinition(BaseModel):
    entity_type: str
    uie_general_labels: dict[str, str] | None = Field(default_factory=dict)
    uie_medical: str | None = None
    priority: int = 100

    # ============ 校验器 ============

    @field_validator("entity_type")
    @classmethod
    def validate_entity_type(cls, v: str) -> str:
        """限制1: entity_type 必须全大写"""
        if not v.isupper():
            raise ValueError(f"entity_type must be all uppercase, got '{v}'")
        return v

    @field_validator("uie_general_labels")
    @classmethod
    def validate_labels(cls, v: dict[str, str] | None) -> dict[str, str] | None:
        """限制2: uie_general_labels 的键只能是 'zh' 或 'en'"""
        if v is None:
            return v

        allowed_keys = {"zh", "en"}
        invalid_keys = set(v.keys()) - allowed_keys
        if invalid_keys:
            raise ValueError(
                f"uie_general_labels keys must be only 'zh' or 'en', "
                f"got invalid keys: {invalid_keys}"
            )
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: int) -> int:
        """限制3: priority 必须在 [1, 1000] 范围内"""
        if not (1 <= v <= 1000):
            raise ValueError(f"priority must be between 1 and 1000, got {v}")
        return v


ENTITY_CATALOG: dict[str, EntityDefinition] = {
    "CREDIT_CARD": EntityDefinition(
        entity_type="CREDIT_CARD",
        presidio_entity="CREDIT_CARD",
        priority=100,
    ),
    "CRYPTO": EntityDefinition(
        entity_type="CRYPTO",
        presidio_entity="CRYPTO",
        priority=100,
    ),
    "DATE_TIME": EntityDefinition(
        entity_type="DATE_TIME",
        presidio_entity="DATE_TIME",
        priority=100,
    ),
    "EMAIL_ADDRESS": EntityDefinition(
        entity_type="EMAIL_ADDRESS",
        presidio_entity="EMAIL_ADDRESS",
        priority=100,
    ),
    "IBAN_CODE": EntityDefinition(
        entity_type="IBAN_CODE",
        presidio_entity="IBAN_CODE",
        priority=100,
    ),
    "IP_ADDRESS": EntityDefinition(
        entity_type="IP_ADDRESS",
        presidio_entity="IP_ADDRESS",
        priority=100,
    ),
    "MAC_ADDRESS": EntityDefinition(
        entity_type="MAC_ADDRESS",
        presidio_entity="MAC_ADDRESS",
        priority=100,
    ),
    "NRP": EntityDefinition(
        entity_type="NRP",
        presidio_entity="NRP",
        priority=100,
    ),
    "LOCATION": EntityDefinition(
        entity_type="LOCATION",
        presidio_entity="LOCATION",
        priority=100,
    ),
    "PERSON": EntityDefinition(
        entity_type="PERSON",
        presidio_entity="PERSON",
        priority=100,
    ),
    "MEDICAL_LICENSE": EntityDefinition(
        entity_type="MEDICAL_LICENSE",
        presidio_entity="MEDICAL_LICENSE",
        priority=100,
    ),
    "URL": EntityDefinition(
        entity_type="URL",
        presidio_entity="URL",
        priority=100,
    ),
    "CN_ID_CARD": EntityDefinition(
        entity_type="CN_ID_CARD",
        presidio_entity="CN_ID_CARD",
        priority=100,
    ),
    "PHONE_NUMBER": EntityDefinition(
        entity_type="PHONE_NUMBER",
        uie_general_labels={
            "zh": "电话号码",
            "en": "phone number",
        },
        priority=150,
    ),
    "FAX_NUMBER": EntityDefinition(
        entity_type="FAX_NUMBER",
        uie_general_labels={
            "zh": "传真号码",
            "en": "fax number",
        },
        priority=150,
    ),
    "POSTAL_CODE": EntityDefinition(
        entity_type="POSTAL_CODE",
        uie_general_labels={
            "zh": "邮政编码",
            "en": "postal code",
        },
        priority=150,
    ),
    "DISEASE": EntityDefinition(
        entity_type="DISEASE",
        uie_medical="疾病",
        priority=100,
    ),
    "SYMPTOM": EntityDefinition(
        entity_type="SYMPTOM",
        uie_medical="症状",
        priority=100,
    ),
    "MEDICATION": EntityDefinition(
        entity_type="MEDICATION",
        uie_medical="药物",
        priority=110,
    ),
    "MEDICAL_TEST": EntityDefinition(
        entity_type="MEDICAL_TEST",
        uie_medical="检查项目",
        priority=100,
    ),
    "TREATMENT": EntityDefinition(
        entity_type="TREATMENT",
        uie_medical="治疗方法",
        priority=100,
    ),
    "DOCTOR": EntityDefinition(
        entity_type="DOCTOR",
        uie_medical="医生",
        priority=100,
    ),
}
