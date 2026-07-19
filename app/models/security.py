from typing import Any

from pydantic import BaseModel, ConfigDict
from presidio_analyzer import RecognizerResult
from presidio_anonymizer import EngineResult
from presidio_anonymizer.entities import OperatorResult

from app.policy.Check_Policy import CheckPolicy
from app.policy.detection.policy import DetectionPolicy


class ErrorResponse(BaseModel):
    code: str
    message: str


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    time: str


class RecognizerResultModel(BaseModel):
    entity_type: str
    start: int
    end: int
    score: float

    @classmethod
    def from_presidio(cls, result: RecognizerResult) -> "RecognizerResultModel":
        return cls(
            entity_type=result.entity_type,
            start=result.start,
            end=result.end,
            score=result.score,
        )

    def to_presidio(self) -> RecognizerResult:
        return RecognizerResult(
            entity_type=self.entity_type,
            start=self.start,
            end=self.end,
            score=self.score,
        )


class OperatorResultModel(BaseModel):
    start: int
    end: int
    entity_type: str
    text: str | None = None
    operator: str | None = None
    original_text: str | None = None

    @classmethod
    def from_presidio(cls, result: OperatorResult) -> "OperatorResultModel":
        return cls(
            start=result.start,
            end=result.end,
            entity_type=result.entity_type,
            text=result.text,
            operator=result.operator,
            original_text=getattr(result, "original_text", None),
        )

    def to_presidio(self) -> OperatorResult:
        result = OperatorResult(
            start=self.start,
            end=self.end,
            entity_type=self.entity_type,
            text=self.text,
            operator=self.operator,
        )
        if self.original_text is not None:
            result.original_text = self.original_text
        return result


class EngineResultModel(BaseModel):
    text: str
    items: list[OperatorResultModel] = []

    @classmethod
    def from_presidio(cls, result: EngineResult) -> "EngineResultModel":
        return cls(
            text=result.text,
            items=[OperatorResultModel.from_presidio(item) for item in result.items],
        )

    def to_presidio(self) -> EngineResult:
        return EngineResult(
            text=self.text,
            items=[item.to_presidio() for item in self.items],
        )


class ScanRequest(BaseModel):
    text: str
    profile: str | None = None
    policy: DetectionPolicy | None = None


class ScanResponse(BaseModel):
    sha_256: str
    results: list[RecognizerResultModel]


class AnonymizeRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    text: str
    transformation_profile: str | None = None
    transformation_policy: Any | None = None
    detection_profile: str | None = None
    detection_policy: DetectionPolicy | None = None
    analyzer_results: list[RecognizerResultModel] | None = None


class AnonymizeResponse(BaseModel):
    sha_256: str
    engine_result: EngineResultModel


class DeanonymizeRequest(BaseModel):
    text: str
    engine_result: EngineResultModel


class DeanonymizeResponse(BaseModel):
    sha_256: str
    text: str


class CheckInputRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    text: str
    profile: str | None = None
    policy: CheckPolicy | None = None


class CheckOutputRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    prompt: str
    text: str
    profile: str | None = None
    policy: CheckPolicy | None = None


class CheckResponse(BaseModel):
    sha_256: str
    text: str
    valid: dict[str, bool]
    score: dict[str, float]
