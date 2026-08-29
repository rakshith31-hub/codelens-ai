from app.core.repo_indexer import index_repo


def test_index_repo_finds_all_functions():
    records = index_repo("sample_repo")
    names = {r.name for r in records}
    assert names == {
        "calculate_discount",
        "calculate_tax",
        "calculate_total",
        "apply_coupon",
        "checkout",
    }


def test_calculate_total_calls_are_detected():
    records = index_repo("sample_repo")
    total_fn = next(r for r in records if r.name == "calculate_total")
    assert "calculate_discount" in total_fn.calls
    assert "calculate_tax" in total_fn.calls


def test_checkout_has_highest_fan_out():
    records = index_repo("sample_repo")
    checkout_fn = next(r for r in records if r.name == "checkout")
    assert {"calculate_total", "apply_coupon"}.issubset(set(checkout_fn.calls))
