import re

from cypher.cypher_builder import CypherBuilder
from cypher.cypher_generator import CypherGenerator


def test_cypher_builder_single_includes_where_for_size():
    builder = CypherBuilder()
    plan = {"type": "SINGLE", "sizes": ["205/55R16"]}
    cypher, params = builder.build(plan)

    assert cypher is not None
    assert 'WHERE t.size = $size' in cypher
    assert params and params.get('size') == "205/55R16"


def test_cypher_generator_fallback_includes_where_for_size():
    gen = CypherGenerator()
    query = "Tôi muốn lốp 205/55R16"
    # test internal extractor and fallback directly
    size = gen._extract_size_from_query(query)
    assert size is not None
    cypher = gen._fallback_query(query)
    assert cypher is not None
    assert re.search(r'WHERE\s+t\.size\s*=\s*"205/55R16"', cypher)
