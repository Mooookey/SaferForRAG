from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from presidio_analyzer.nlp_engine import NlpEngineProvider
import json
from pprint import pprint

from llm_guard import scan_output, scan_prompt
from llm_guard.input_scanners import Anonymize, PromptInjection, TokenLimit, Toxicity, BanTopics
from llm_guard.output_scanners import Deanonymize, NoRefusal, Relevance, Sensitive, Bias
from llm_guard.vault import Vault

from presidio_anonymizer.entities import InvalidParamError
from presidio_anonymizer.operators import Operator, OperatorType
from presidio_anonymizer.services.validators import validate_parameter



class ServiceContainer:
    def __init__(self):
        LANGUAGES_CONFIG_FILE:str= "./app/config/lm-config.yaml"
        provider = NlpEngineProvider(conf_file=LANGUAGES_CONFIG_FILE)
        nlp_engine = provider.create_engine()

        self.analyzer = AnalyzerEngine(
            nlp_engine=nlp_engine, 
            supported_languages=["zh", "en"],
            log_decision_process=False,
        )
        

        self.anonymizer = AnonymizerEngine()
        # self.anonymizer.add_anonymizer(MaskMiddleOperator)

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
        
from presidio_anonymizer.entities import OperatorConfig


from presidio_anonymizer.entities import OperatorConfig


class MaskMiddleOperator:
    """
    Presidio-compatible anonymizer operator.

    Rules:
    - len >= 7: keep 2 + 2
    - len >= 5: keep 1 + 1
    - else: full mask
    """

    def __init__(self, mask_char: str = "*"):
        self.mask_char = mask_char
        self.operator_name = "mask_middle"

    def operate(self, text: str, params: OperatorConfig = None, **kwargs) -> str:
        if text is None:
            return text

        text = str(text)
        n = len(text)

        mask_char = self.mask_char
        if n < 5:
            return mask_char * n

        if n < 7:
            return text[0] + mask_char * (n - 2) + text[-1]

        return text[:2] + mask_char * (n - 4) + text[-2:]