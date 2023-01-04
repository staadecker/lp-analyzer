from lp_analyzer.analyze import split_type_and_index


def test_split_type_and_index():
    assert ("var", "") == split_type_and_index("var")
    assert ("var", "1,2,3") == split_type_and_index("var(1,2,3)")
    assert ("var", "1,2, 3") == split_type_and_index("var(1,2, 3)")
