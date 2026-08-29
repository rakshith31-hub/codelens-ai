from app.core.review_schema import ReviewOutput


def test_review_output_is_structured():
    review = ReviewOutput(
        suggested_docstring="Calculate the total price.",
        review_comments=["Handle invalid input.", "Consider rounding consistently."],
        risk_flag="low",
        risk_reason="The function has limited dependency fan-in and fan-out.",
    )

    data = review.model_dump()
    assert set(data) == {
        "suggested_docstring",
        "review_comments",
        "risk_flag",
        "risk_reason",
    }
    assert data["risk_flag"] == "low"
