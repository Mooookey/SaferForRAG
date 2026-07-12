import os
from typing import Dict, List

from pydantic import BaseModel, ConfigDict
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


class TransformationPolicy(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    policy_name: str
    operators: List[TransformationOperator]
    presidio_operator: Dict[str, OperatorConfig] = {}
    llmguard_operator: List[Placeholder_Operator] = []

    def model_post_init(self, __context) -> None:
        self.presidio_operator = {}
        self.llmguard_operator = []
        for operator in self.operators:
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
                policy_name="irreversible",
                operators=[Irreversible_Operator("DEFAULT")],
            )
        )
        self._register_policy(
            TransformationPolicy(
                policy_name="masked",
                operators=[Mask_Operator("DEFAULT")],
            )
        )
        self._register_policy(
            TransformationPolicy(
                policy_name="hash",
                operators=[Hash_Operator("DEFAULT", salt_enabled=False)],
            )
        )
        self._register_policy(
            TransformationPolicy(
                policy_name="placeholder",
                operators=[Placeholder_Operator("DEFAULT")],
            )
        )
        self._register_policy(
            TransformationPolicy(
                policy_name="encrypted",
                operators=[
                    Encrypt_Operator(
                        "DEFAULT",
                        os.getenv("ENCRYPTION_KEY", "${ENCRYPTION_KEY}"),
                    )
                ],
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
            raise ValueError("Duplicate transformation operator entity")
        return TransformationPolicy(policy_name=policy_name, operators=operators)
