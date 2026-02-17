from typing import Optional

from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic
from langgraph.types import interrupt

from lib.logging import get_logger
from lib.prompts import INQUIRE_PROMPT
from schemas.app_state import AppState

logger = get_logger(__name__)


class ClarifyingQuestion(BaseModel):
    needs_clarification: bool = Field(
        description="Whether the user's query lacks enough detail about preferences (cuisine, flavor, dietary restrictions, meal type) to generate a good recipe suggestion."
    )
    question: Optional[str] = Field(
        default=None,
        description="A natural clarifying question to ask the user. Only required when needs_clarification is True.",
    )


llm = ChatAnthropic(model="claude-sonnet-4-5-20250929").with_structured_output(
    ClarifyingQuestion
)


def inquire(state: AppState) -> AppState:
    result = llm.invoke(INQUIRE_PROMPT.format(query=state["query"]))

    if not result.needs_clarification:
        logger.info("inquire | no clarification needed, proceeding")
        return {}

    logger.info("inquire | asking clarification: %s", result.question)
    answer = interrupt(result.question)
    logger.info("inquire | received answer: %s", answer)
    return {"user_preferences": answer}
