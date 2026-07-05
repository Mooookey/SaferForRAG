from typing import Dict

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from presidio_analyzer.nlp_engine import NlpEngineProvider
import json
from pprint import pprint

from llm_guard import scan_output, scan_prompt
from llm_guard.input_scanners import PromptInjection, TokenLimit, Toxicity, BanTopics, Regex, BanSubstrings
from llm_guard.output_scanners import  NoRefusal, Bias, Toxicity, BanTopics, Regex, BanSubstrings
from llm_guard.vault import Vault

from presidio_anonymizer.entities import InvalidParamError
from presidio_anonymizer.operators import Operator, OperatorType
from presidio_anonymizer.services.validators import validate_parameter

from app.recognizer.China_Id_card_recognizer import ChinaIdCardRecognizer

class ServiceContainer:
    LANGUAGES_CONFIG_FILE:str= "./app/config/lm-config.yaml"
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

        self.input_scanners = [
            Toxicity(), 
            TokenLimit(), 
            PromptInjection(),
            BanTopics(topics=["violence or violent crime 暴力或暴力犯罪",
                              "religion and religious extremism 宗教或宗教极端主义",
                              "political persuasion or political opinion 政治劝说或政治观点"
                              ])
                        ]
        self.output_scanners = [
            Bias(),
            Toxicity(), 
            NoRefusal(),
            BanTopics(topics=["violence or violent crime 暴力或暴力犯罪",
                              "religion and religious extremism 宗教或宗教极端主义",
                              "political persuasion or political opinion 政治劝说或政治观点"
                              ])
                              ]
        
    # 用来批量注册自定义识别器，比如中国身份证号
    def _register_recognizer(self) -> None:
        if ServiceContainer.recognizer_registered["CN_id_card_recognizer_registered"]:
            return

        for language in ["zh", "en"]:
            self.analyzer.registry.add_recognizer(
                ChinaIdCardRecognizer(supported_language=language)
            )
        ServiceContainer.recognizer_registered["CN_id_card_recognizer_registered"] = True


service_container=ServiceContainer()


