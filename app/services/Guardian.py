from typing import TYPE_CHECKING

from llm_guard import scan_output, scan_prompt

from app.policy.Check_Policy import CheckPolicy

if TYPE_CHECKING:
    from app.services.container import ServiceContainer

class Guardian:
    @staticmethod
    def check_input(
        text: str,
        service_container: "ServiceContainer",
        profile: str | None = None,
        policy: CheckPolicy | None = None,
    ):
        if (policy is None) and (profile is None):
            raise ValueError("check policy or check profile is required")
        if policy is None:
            if profile not in service_container.check_input_policy_factory.registry:
                raise ValueError("unknown built-in input check profile")
            policy = service_container.check_input_policy_factory.registry[profile]

        return scan_prompt(policy.scanners, text)

    @staticmethod
    def check_output(
        prompt: str,
        text: str,
        service_container: "ServiceContainer",
        profile: str | None = None,
        policy: CheckPolicy | None = None,
    ):
        if (policy is None) and (profile is None):
            raise ValueError("check policy or check profile is required")
        if policy is None:
            if profile not in service_container.check_output_policy_factory.registry:
                raise ValueError("unknown built-in output check profile")
            policy = service_container.check_output_policy_factory.registry[profile]

        return scan_output(policy.scanners, prompt, text)