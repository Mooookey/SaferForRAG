from typing import Dict, List

from pydantic import BaseModel, ConfigDict

from llm_guard.input_scanners import (
    BanSubstrings as InputBanSubstrings,
    BanTopics as InputBanTopics,
    PromptInjection,
    Regex as InputRegex,
    TokenLimit,
    Toxicity as InputToxicity,
)
from llm_guard.output_scanners import (
    BanSubstrings as OutputBanSubstrings,
    BanTopics as OutputBanTopics,
    Bias,
    NoRefusal,
    Regex as OutputRegex,
    Toxicity as OutputToxicity,
)


class CheckPolicy(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    policy_name: str
    scanners: list = []
    ban_strings: list[str] = []
    ban_regexs: list[str] = []


class CheckPolicy_Factory:
    DEFAULT_INPUT_SCANNERS = [
        "Toxicity",
        "TokenLimit",
        "PromptInjection",
        "BanTopics",
    ]
    DEFAULT_OUTPUT_SCANNERS = [
        "Bias",
        "Toxicity",
        "NoRefusal",
        "BanTopics",
    ]

    # BanTopics的类别
    DEFAULT_BAN_TOPICS = [
        "violence or violent crime 暴力或暴力犯罪",
        "religion and religious extremism 宗教或宗教极端主义",
        "political persuasion or political opinion 政治劝说或政治观点",
    ]

    # mode区分input/output
    # 重点在于识别器scanners不能二次实例化，否则会重新加载模型
    def __init__(self, mode: str):
        self.mode = mode
        self.registry: Dict[str, CheckPolicy] = {}
        self.scanners_mapper: Dict[str, object] = self._build_scanners_mapper()
        self._regex_cache: Dict[tuple[str, ...], object] = {}
        self._ban_strings_cache: Dict[tuple[str, ...], object] = {}
        self.check_policy_factory = self.registry

        default_scanners = (
            CheckPolicy_Factory.DEFAULT_INPUT_SCANNERS
            if mode == "input"
            else CheckPolicy_Factory.DEFAULT_OUTPUT_SCANNERS
        )
        self._register_policy(
            CheckPolicy(
                policy_name="default",
                scanners=[self.scanners_mapper[name] for name in default_scanners],
                ban_strings=[],
                ban_regexs=[],
            )
        )

    def _build_scanners_mapper(self) -> Dict[str, object]:
        if self.mode == "input":
            scanners = [
                InputToxicity(),
                TokenLimit(),
                PromptInjection(),
                InputBanTopics(topics=CheckPolicy_Factory.DEFAULT_BAN_TOPICS),
            ]
        else:
            scanners = [
                Bias(),
                OutputToxicity(),
                NoRefusal(),
                OutputBanTopics(topics=CheckPolicy_Factory.DEFAULT_BAN_TOPICS),
            ]
        return {type(scanner).__name__: scanner for scanner in scanners}

    def _get_regex_scanner(self, ban_regexs: List[str]):
        cache_key = tuple(ban_regexs)
        if cache_key not in self._regex_cache:
            if self.mode == "input":
                self._regex_cache[cache_key] = InputRegex(patterns=ban_regexs)
            else:
                self._regex_cache[cache_key] = OutputRegex(patterns=ban_regexs)
        return self._regex_cache[cache_key]

    def _get_ban_strings_scanner(self, ban_strings: List[str]):
        cache_key = tuple(ban_strings)
        if cache_key not in self._ban_strings_cache:
            if self.mode == "input":
                self._ban_strings_cache[cache_key] = InputBanSubstrings(
                    substrings=ban_strings
                )
            else:
                self._ban_strings_cache[cache_key] = OutputBanSubstrings(
                    substrings=ban_strings
                )
        return self._ban_strings_cache[cache_key]

    def _register_policy(self, policy: CheckPolicy) -> None:
        self.registry[policy.policy_name] = policy

    def create_policy(
        self,
        policy_name: str,
        scanners: list[str] | None = None,
        ban_strings: list[str] | None = None,
        ban_regexs: list[str] | None = None,
    ) -> CheckPolicy:
        if scanners is None:
            scanner_names = (
                CheckPolicy_Factory.DEFAULT_INPUT_SCANNERS
                if self.mode == "input"
                else CheckPolicy_Factory.DEFAULT_OUTPUT_SCANNERS
            )
        else:
            scanner_names = scanners
        policy_scanners = [self.scanners_mapper[name] for name in scanner_names]

        if ban_strings:
            policy_scanners.append(self._get_ban_strings_scanner(ban_strings))
        if ban_regexs:
            policy_scanners.append(self._get_regex_scanner(ban_regexs))

        policy = CheckPolicy(
            policy_name=policy_name,
            scanners=policy_scanners,
            ban_strings=ban_strings or [],
            ban_regexs=ban_regexs or [],
        )
        self._register_policy(policy)
        return policy
