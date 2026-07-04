from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from presidio_analyzer.nlp_engine import NlpEngineProvider
import json
from pprint import pprint

from llm_guard import scan_output, scan_prompt
from llm_guard.input_scanners import Anonymize, PromptInjection, TokenLimit, Toxicity, BanTopics
from llm_guard.output_scanners import Deanonymize, NoRefusal, Relevance, Sensitive
from llm_guard.vault import Vault

from container import ServiceContainer

service_container=ServiceContainer()

def scan(text:str):
    analyzer_results = service_container.analyzer.analyze(
        text=text, 
        language="zh",
        entities=[
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
            "URL"
        ],
        return_decision_process=False
        )
    return analyzer_results


def anonymize(text:str,analyzer_results):
    anonymized_results = service_container.anonymizer.anonymize(
        text=text,
        analyzer_results=analyzer_results
    )
    return (anonymized_results.text,anonymized_results.items)

def check_input(text:str):
    sanitized_prompt, results_valid, results_score = scan_prompt(service_container.input_scanners, text)
    return (sanitized_prompt, results_valid, results_score)

def check_output(text:str):
    return
def deanonymize(text:str):
    return