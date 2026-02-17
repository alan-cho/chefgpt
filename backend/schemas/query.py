from pydantic import BaseModel


class Query(BaseModel):
    query: str
    thread_id: str | None = None
    resume: str | None = None
    stream: bool = True
    debug: bool = False
