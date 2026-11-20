from bench.result_hash import result_hash


def test_result_hash_order_independent():
    assert result_hash([(1, 2.345), (2, 3.456)]) == result_hash([(2, 3.456), (1, 2.345)])


def test_result_hash_rounds_floats():
    assert result_hash([(1, 1.234)]) == result_hash([(1, 1.231)])
