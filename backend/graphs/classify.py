from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic

from lib.logging import get_logger
from lib.prompts import CLASSIFY_PROMPT
from schemas.app_state import AppState

logger = get_logger(__name__)


class ClassificationResult(BaseModel):
    is_cooking_related: bool = Field(
        description="Whether the user's query is related to cooking, recipes, food preparation, or kitchen topics."
    )
    query_intent: str | None = Field(
        default=None,
        description="The intent of the query if cooking-related: 'recipe_request', 'what_can_i_make', or 'general'.",
    )


llm = ChatAnthropic(model="claude-sonnet-4-5-20250929").with_structured_output(
    ClassificationResult
)


def classify(state: AppState) -> AppState:
    result = llm.invoke(CLASSIFY_PROMPT.format(query=state["query"]))
    logger.info(
        "classification | cooking=%s intent=%s",
        result.is_cooking_related,
        result.query_intent,
    )
    return {
        "is_cooking_related": result.is_cooking_related,
        "query_intent": result.query_intent,
    }
