from datetime import date, timedelta
from uuid import UUID

from legal_gateway.matter_intake import (
    IntakeAssessment,
    MatterIntakeRequest,
    build_workflow,
)

request = MatterIntakeRequest(
    matter_id=UUID("c57c21b6-5918-4b66-b3cf-9747229a5911"),
    client_name="Mira Chen",
    matter_summary="Signed storefront lease amendment requiring a prompt landlord response.",
    signed_document_url="https://documents.example/matters/c57c21b6/signed",
    response_due_date=date.today() + timedelta(days=2),
)
assessment = IntakeAssessment(
    category="property",
    urgency="priority",
    client_note="The signed amendment is ready; follow-up is scheduled before the response date.",
)

print(build_workflow(request, assessment).model_dump_json(indent=2))
