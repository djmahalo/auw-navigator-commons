def test_rule_matcher_smoke():
    from api.rules_engine import _matches

    intake = {"DomainModule": "Housing", "Crisis": True, "Narrative": "eviction risk"}
    attrs = {"risk_days": 7}

    match = {"all": [
        {"field": "DomainModule", "op": "eq", "value": "Housing"},
        {"field": "Crisis", "op": "eq", "value": True},
        {"field": "Narrative", "op": "contains", "value": "eviction"},
        {"attr": "risk_days", "op": "lte", "value": 7}
    ]}

    assert _matches(match, intake, attrs) is True
