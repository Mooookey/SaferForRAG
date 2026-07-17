from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from presidio_analyzer.nlp_engine import NlpEngineProvider
import json
from pprint import pprint

LANGUAGES_CONFIG_FILE = "./app/config/lm-config.yaml"

# Create NLP engine based on configuration file
provider = NlpEngineProvider(conf_file=LANGUAGES_CONFIG_FILE)
nlp_engine = provider.create_engine()

# Pass created NLP engine and supported_languages to the AnalyzerEngine
analyzer = AnalyzerEngine(
    nlp_engine=nlp_engine, 
    supported_languages=["zh", "en"]
)

# 使用中文大模型，无法识别英文实体，比如名字换成John
text="我的电话号码是+86-13957345030，名字是李明，住在上海市"

analyzer_results = analyzer.analyze(text=text, 
                                    language="zh")
print(analyzer_results)
print("-----------------------")

anonymizer = AnonymizerEngine()
anonymized_results = anonymizer.anonymize(
    text=text,
    analyzer_results=analyzer_results,
    operators={
        "DEFAULT": OperatorConfig(
            "encrypt", 
            {
                "key":1
            }
        ),
        "PHONE_NUMBER": OperatorConfig(
            "mask",
            {
                "type": "mask",
                "masking_char": "*",
                "chars_to_mask": 12,
                "from_end": True
            }
        ),
        "TITLE": OperatorConfig("redact", {})
    }
)

print(f"text: {anonymized_results.text}")
print("detailed response:")

pprint(json.loads(anonymized_results.to_json()))