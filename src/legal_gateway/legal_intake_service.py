from fastapi import Depends, FastAPI

from .matter_intake import (
    GatewayIntakeAssessor,
    IntakeAssessor,
    MatterIntakeRequest,
    MatterWorkflow,
    build_workflow,
)

service = FastAPI(title="Legal matter gateway")


def get_assessor() -> IntakeAssessor:
    return GatewayIntakeAssessor()


@service.post("/matters/intake", response_model=MatterWorkflow)
def intake_matter(
    request: MatterIntakeRequest,
    assessor: IntakeAssessor = Depends(get_assessor),
) -> MatterWorkflow:
    return build_workflow(request, assessor.assess(request))
