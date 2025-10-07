import pytest

import regex_automata


@pytest.mark.parametrize("pattern,s,result",
                         [("lo*l", "looooooooool", True),
                          ("lo*l", "lo", False),
                          ("lo*l", "lolo", False),
                          ("lo*l", "olol", False),
                          ("foo|(bar|baz)|quux", "foo", True),
                          ("foo|(bar|baz)|quux", "bar", True),
                          ("foo|(bar|baz)|quux", "baz", True),
                          ("foo|(bar|baz)|quux", "quux", True),
                          ("(ab*)*", "abbabbbbbabbb", True),
                          ("(ab*)*", "", True),
                          ("(ab*)*", "bbbbb", False),
                          ])
def test_fullmatch_regex(pattern: str, s: str, result: bool):
    assert regex_automata.fullmatch(pattern, s) is result
