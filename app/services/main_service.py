from typing import List

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer, RecognizerResult
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from presidio_analyzer.nlp_engine import NlpEngineProvider
import json
from pprint import pprint

from llm_guard import scan_output, scan_prompt
from llm_guard.input_scanners import Anonymize, PromptInjection, TokenLimit, Toxicity, BanTopics
from llm_guard.output_scanners import Deanonymize, NoRefusal, Relevance, Sensitive
from llm_guard.vault import Vault

from app.services.container import service_container


class Santilizer:
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

    # 用于合并ZH/EN两种NER识别结果不完全重叠的情况
    @staticmethod
    def _merge_overlapping_results(
        analyzer_results: list[RecognizerResult],
    ) -> list[RecognizerResult]:
        sorted_results: list[RecognizerResult] = sorted(
            analyzer_results,
            key=lambda result: (result.start, result.end),
        )
        merged_results: list[RecognizerResult] = []

        for result in sorted_results:
            if not merged_results:
                merged_results.append(result)
                continue

            last_result: RecognizerResult = merged_results[-1]
            has_overlap: bool = result.start < last_result.end and last_result.start < result.end

            if has_overlap:
                result_length: int = result.end - result.start
                last_result_length: int = last_result.end - last_result.start
                if result_length > last_result_length:
                    merged_results[-1] = result
            else:
                merged_results.append(result)

        return merged_results

    @staticmethod
    def scan(
             text:str,
             return_decision_process:bool=False, 
             entities: list[str]|None=None, 
             allow_list: list[str]|None=None,             
             )-> List[RecognizerResult]:
        if entities is None:
            entities=Santilizer.DEFAULT_ENTITIES

        analyzer_results_zh = service_container.analyzer.analyze(
            text=text, 
            language="zh",
            entities=entities,
            return_decision_process=return_decision_process,
            allow_list=allow_list
            )
        analyzer_results_en = service_container.analyzer.analyze(
            text=text, 
            language="en",
            entities=entities,
            return_decision_process=return_decision_process,
            allow_list=allow_list
            )
        
        analyzer_results: list[RecognizerResult] = Santilizer._merge_overlapping_results(
            analyzer_results_zh + analyzer_results_en
        )
        return analyzer_results

    @staticmethod
    def anonymize(text:str,analyzer_results):
        anonymized_results = service_container.anonymizer.anonymize(
            text=text,
            analyzer_results=analyzer_results
        )
        return (anonymized_results.text,anonymized_results.items)
    
    def deanonymize(self, text:str):
        return

def check_input(text:str):
    sanitized_prompt, results_valid, results_score = scan_prompt(service_container.input_scanners, text)
    return (sanitized_prompt, results_valid, results_score)

def check_output(text:str):
    return

if __name__ == "__main__":
    text:str="我的身份证号是510181198312261892"
    print(Santilizer.scan(text))
