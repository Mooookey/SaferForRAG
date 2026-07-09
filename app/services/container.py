from typing import Dict

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

from app.policy.Check_Policy import CheckPolicy_Factory
from app.policy.Detection_Policy import DetectionPolicy_Factory
from app.policy.Transformation_Policy import TransformationPolicy_Factory
from app.recognizer.China_Id_card_recognizer import ChinaIdCardRecognizer


class ServiceContainer:
    LANGUAGES_CONFIG_FILE: str = "./app/config/lm-config.yaml"
    recognizer_registered: Dict[str, bool] = {
        "CN_id_card_recognizer_registered": False
    }

    def __init__(self):
        provider = NlpEngineProvider(conf_file=ServiceContainer.LANGUAGES_CONFIG_FILE)
        nlp_engine = provider.create_engine()

        self.analyzer = AnalyzerEngine(
            nlp_engine=nlp_engine,
            supported_languages=["zh", "en"],
            log_decision_process=False,
        )
        self._register_recognizer()

        self.anonymizer = AnonymizerEngine()

        self.tranformation_policy_factory = TransformationPolicy_Factory()
        self.detection_policy_factory = DetectionPolicy_Factory()
        self.check_input_policy_factory = CheckPolicy_Factory(mode="input")
        self.check_output_policy_factory = CheckPolicy_Factory(mode="output")

    def _register_recognizer(self) -> None:
        if ServiceContainer.recognizer_registered["CN_id_card_recognizer_registered"]:
            return

        for language in ["zh", "en"]:
            self.analyzer.registry.add_recognizer(
                ChinaIdCardRecognizer(supported_language=language)
            )
        ServiceContainer.recognizer_registered["CN_id_card_recognizer_registered"] = True


service_container = ServiceContainer()
