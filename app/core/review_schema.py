from typing import Literal

from pydantic import BaseModel, Field


class ReviewOutput(BaseModel):
    suggested_docstring: str = Field(description="A concise and accurate docstring for the target function")
    review_comments: list[str] = Field(min_length=2, max_length=4)
    risk_flag: Literal["high", "low"]
    risk_reason: str
