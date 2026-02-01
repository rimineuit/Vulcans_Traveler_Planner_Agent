# Pipeline: Rewrite -> Augment -> Clarify
from pydantic import BaseModel

class QueryCheckAmbitous(BaseModel):
    query: str
    