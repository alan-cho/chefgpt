from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic

from lib.prompts import COOKWARE_PROMPT
from lib.constants import USER_COOKWARE
from schemas.app_state import AppState


class CookwareRequirement(BaseModel):
    required_cookware: list[str] = Field(
        description="List of cookware items needed for this dish or query."
    )


llm = ChatAnthropic(model="claude-sonnet-4-5-20250929").with_structured_output(
    CookwareRequirement
)


def check_cookware(state: AppState) -> AppState:
    result = llm.invoke(COOKWARE_PROMPT.format(query=state["query"]))

    required = [item.lower() for item in result.required_cookware]
    available_set = {item.lower() for item in USER_COOKWARE}

    available = [item for item in required if item in available_set]
    missing = [item for item in required if item not in available_set]

    return {
        "required_cookware": result.required_cookware,
        "available_cookware": available,
        "missing_cookware": missing,
    }
