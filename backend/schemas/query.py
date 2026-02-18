from pydantic import BaseModel, Field


class Query(BaseModel):
    query: str = Field(max_length=2000)
    thread_id: str | None = None
    resume: str | None = None
    stream: bool = True
    debug: bool = False
