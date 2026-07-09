import os
from typing import Dict, List

from presidio_anonymizer import EngineResult, OperatorConfig

from app.policy.Transformation_Operator import (
    Encrypt_Operator,
    Hash_Operator,
    Irreversible_Operator,
    Mask_Operator,
    Placeholder_Operator,
)

TransformationOperator = (
    Placeholder_Operator
    | Hash_Operator
    | Encrypt_Operator
    | Irreversible_Operator
    | Mask_Operator
)

# 理论上self.operators应该和presidio-anonymizer.anonymize的operator参数类型Dict[str,OperatorConfig]一致
# 但考虑到TransformationPolicy混合了llmguard.output_scanner的Anonymize，所以用List[TransformationOperator]
class TransformationPolicy:
    def __init__(self, policy_name: str, operators: List[TransformationOperator]):
        self.policy_name = policy_name

        # self.operators是一个混合类型
        self.operators = operators
        self.presidio_operator: Dict[str, OperatorConfig] = {}
        self.llmguard_operator: List[Placeholder_Operator] = []

        for operator in operators:
            if type(operator) == Placeholder_Operator:
                self.llmguard_operator.append(operator)
            else:
                self.presidio_operator[operator.entity] = operator.operator_config

    def inverse_transform(self, text: str, engine_result: EngineResult) -> str:
        return self.llmguard_operator[0].inverse_transform(text, engine_result)


class TransformationPolicy_Factory:
    DEFAULT_ENTITIES = [
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

    def __init__(self):
        self.registry: Dict[str, TransformationPolicy] = {}

        self._register_policy(
            TransformationPolicy(
                "irreversible",
                [Irreversible_Operator("DEFAULT")],
            )
        )
        self._register_policy(
            TransformationPolicy(
                "masked",
                [Mask_Operator("DEFAULT")],
            )
        )
        self._register_policy(
            TransformationPolicy(
                "hash",
                [Hash_Operator("DEFAULT", salt_enabled=False)],
            )
        )
        self._register_policy(
            TransformationPolicy(
                "placeholder",
                [Placeholder_Operator("DEFAULT")],
            )
        )
        self._register_policy(
            TransformationPolicy(
                "encrypted",
                [Encrypt_Operator("DEFAULT", os.getenv("ENCRYPTION_KEY", "${ENCRYPTION_KEY}"))],
            )
        )

    def _register_policy(self, policy: TransformationPolicy) -> None:
        self.registry[policy.policy_name] = policy

    def create_policy(
        self,
        operators: List[TransformationOperator],
        policy_name: str = "custom",
    ) -> TransformationPolicy:
        entities: list[str] = [operator.entity for operator in operators]
        if len(entities) != len(set(entities)):
            raise ValueError("同一实体只能采用唯一的脱敏策略")
        return TransformationPolicy(policy_name, operators)
