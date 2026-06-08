from app.validation.cypher_validator import CypherValidator


def test_validator_rejects_raw_string_literal():
    v = CypherValidator()
    cy = 'MATCH (t:Tire) WHERE t.size = "205/55R16" RETURN t.size LIMIT 1'
    valid, reason = v.validate(cy, params=None)
    assert not valid
    assert 'Raw string literal' in reason


def test_validator_accepts_parameterized_with_params():
    v = CypherValidator()
    cy = 'MATCH (t:Tire) WHERE t.size = $size RETURN t.size LIMIT 1'
    valid, reason = v.validate(cy, params={'size': '205/55R16'})
    assert valid


def test_validator_rejects_missing_params_for_placeholder():
    v = CypherValidator()
    cy = 'MATCH (t:Tire) WHERE t.size = $size RETURN t.size LIMIT 1'
    valid, reason = v.validate(cy, params=None)
    assert not valid
    assert 'Parameterized query missing params' in reason
