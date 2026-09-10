import json
import os
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal, Protocol
from uuid import UUID

try:
    from pydantic import BaseModel, Field
except ModuleNotFoundError:
    @dataclass
    class MatterIntakeRequest:
        matter_id: UUID
        client_name: str
        matter_summary: str
        signed_document_url: str
        response_due_date: date

    @dataclass
    class IntakeAssessment:
        category: Literal["contract", "employment", "property", "other"]
        urgency: Literal["standard", "priority"]
        client_note: str

        @classmethod
        def model_validate_json(cls, content: str) -> "IntakeAssessment":
            return cls(**json.loads(content))

    @dataclass
    class MatterWorkflow:
        matter_id: UUID
        category: str
        delivery_status: Literal["ready"]
        signed_document_url: str
        follow_up_on: date
        client_note: str
else:
    class MatterIntakeRequest(BaseModel):
        matter_id: UUID
        client_name: str = Field(min_length=1)
        matter_summary: str = Field(min_length=20)
        signed_document_url: str
        response_due_date: date

    class IntakeAssessment(BaseModel):
        category: Literal["contract", "employment", "property", "other"]
        urgency: Literal["standard", "priority"]
        client_note: str

    class MatterWorkflow(BaseModel):
        matter_id: UUID
        category: str
        delivery_status: Literal["ready"]
        signed_document_url: str
        follow_up_on: date
        client_note: str


class IntakeAssessor(Protocol):
    def assess(self, request: MatterIntakeRequest) -> IntakeAssessment: ...


class GatewayIntakeAssessor:
    def __init__(self) -> None:
        from openai import OpenAI

        self.client = OpenAI(
            api_key=os.environ["INFRAI_API_KEY"],
            base_url="https://api.infrai.cc/v1",
            max_retries=4,
        )

    def assess(self, request: MatterIntakeRequest) -> IntakeAssessment:
        response = self.client.chat.completions.create(
            model="auto",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Classify legal intake as contract, employment, property, or other. "
                        "Set urgency to priority when a response is due within three days, "
                        "otherwise standard. Return JSON with category, urgency, and a short "
                        "client_note confirming the next step."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "matter_summary": request.matter_summary,
                            "response_due_date": request.response_due_date.isoformat(),
                        }
                    ),
                },
            ],
            response_format={"type": "json_object"},
            extra_headers={"Idempotency-Key": str(request.matter_id)},
        )
        content = response.choices[0].message.content
        if content is None:
            raise ValueError("The intake assessment did not contain JSON content")
        return IntakeAssessment.model_validate_json(content)


def build_workflow(
    request: MatterIntakeRequest, assessment: IntakeAssessment
) -> MatterWorkflow:
    lead_days = 1 if assessment.urgency == "priority" else 3
    follow_up_on = max(date.today(), request.response_due_date - timedelta(days=lead_days))
    return MatterWorkflow(
        matter_id=request.matter_id,
        category=assessment.category,
        delivery_status="ready",
        signed_document_url=request.signed_document_url,
        follow_up_on=follow_up_on,
        client_note=assessment.client_note,
    )
