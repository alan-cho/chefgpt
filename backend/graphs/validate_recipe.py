from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage

from lib.logging import get_logger
from lib.prompts import VALIDATE_RECIPE_PROMPT
from schemas.app_state import AppState

logger = get_logger(__name__)


class RecipeValidation(BaseModel):
    is_safe: bool = Field(
        description="No dangerous food combinations, unsafe cooking temperatures, or allergen issues that could cause harm."
    )
    is_well_structured: bool = Field(
        description="Response includes an ingredients list, step-by-step instructions, and timing information."
    )
    issues: list[str] = Field(
        default_factory=list,
        description="Specific issues found, if any.",
    )


llm = ChatAnthropic(model="claude-sonnet-4-5-20250929").with_structured_output(
    RecipeValidation
)


def validate_recipe(state: AppState) -> AppState:
    last_message = state["messages"][-1]
    recipe_text = last_message.content if isinstance(last_message.content, str) else ""

    if not recipe_text:
        logger.info("validate_recipe | no text content, skipping")
        return {}

    result = llm.invoke(VALIDATE_RECIPE_PROMPT.format(recipe=recipe_text))

    if result.issues:
        logger.warning(
            "validate_recipe | issues found: safe=%s structured=%s issues=%s",
            result.is_safe,
            result.is_well_structured,
            result.issues,
        )
    else:
        logger.info("validate_recipe | passed all checks")

    if not result.is_safe:
        logger.warning("validate_recipe | unsafe recipe detected, replacing response")
        return {
            "messages": [
                AIMessage(
                    content="I wasn't able to generate a safe recipe for that request. Please try rephrasing or asking for a different dish."
                )
            ]
        }

    return {}
