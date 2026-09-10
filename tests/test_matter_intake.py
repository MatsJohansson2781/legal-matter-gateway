from datetime import date, timedelta
from uuid import UUID

from legal_gateway.matter_intake import (
    IntakeAssessment,
    MatterIntakeRequest,
    build_workflow,
)


def test_priority_matter_follows_up_one_day_before_due_date() -> None:
    due_date = date.today() + timedelta(days=2)
    request = MatterIntakeRequest(
        matter_id=UUID("c57c21b6-5918-4b66-b3cf-9747229a5911"),
        client_name="Mira Chen",
        matter_summary="Signed storefront lease amendment requiring a prompt landlord response.",
        signed_document_url="https://documents.example/matters/c57c21b6/signed",
        response_due_date=due_date,
    )
    assessment = IntakeAssessment(
        category="property",
        urgency="priority",
        client_note="The signed amendment is ready for delivery.",
    )

    workflow = build_workflow(request, assessment)

    assert workflow.delivery_status == "ready"
    assert workflow.follow_up_on == due_date - timedelta(days=1)
    assert workflow.signed_document_url == request.signed_document_url
