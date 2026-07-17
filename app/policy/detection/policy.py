from pydantic import BaseModel, Field

from app.policy.detection.catalog import CustomEntityDefinition


class DetectionPolicy(BaseModel):
    policy_name: str

    # 统一 canonical entity ID
    entities: list[str]

    allow_list: list[str] | None = Field(default_factory=list)
    return_decision_process: bool = False

    # 支持用户在 policy 内加入新实体
    custom_entities: dict[str, CustomEntityDefinition] = Field(
        default_factory=dict
    )
