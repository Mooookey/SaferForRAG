from typing import Dict


class DetectionPolicy:
    def __init__(self,
            policy_name:str,
            return_decision_process:bool=False,
            entities: list[str]|None=None,
            allow_list: list[str]|None=None,):
        self.policy_name=policy_name
        self.return_decision_process=return_decision_process
        self.entities=entities
        self.allow_list=allow_list


class DetectionPolicy_Factory:
    DEFAULT_ENTITIES=[
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
        self.registry: Dict[str, DetectionPolicy] = {}
        self._register_policy(
            DetectionPolicy(
                policy_name="default",
                return_decision_process=False,
                entities=DetectionPolicy_Factory.DEFAULT_ENTITIES,
                allow_list=[],
            )
        )

    def _register_policy(self, policy: DetectionPolicy) -> None:
        self.registry[policy.policy_name] = policy
