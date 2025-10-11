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
                          ("ab\\[c", "ab[c", True),
                          ("", "", True),
                          ("()", "", True),
                          ("((((()))))", "", True),
                          ("a+", "", False),
                          ("a+", "a", True),
                          ("a+", "aa", True),
                          ("a?", "", True),
                          ("a?", "a", True),
                          ("a?", "aa", False),
                          ("a{2}", "a", False),
                          ("a{2}", "aa", True),
                          ("a{2}", "aaa", False),
                          ("a{2,}", "a", False),
                          ("a{2,}", "aa", True),
                          ("a{2,}", "aaa", True),
                          ("a{,2}", "", True),
                          ("a{,2}", "a", True),
                          ("a{,2}", "aa", True),
                          ("a{,2}", "aaa", False),
                          ("a{2,3}", "a", False),
                          ("a{2,3}", "aa", True),
                          ("a{2,3}", "aaa", True),
                          ("a{2,3}", "aaaa", False),
                          ])
def test_fullmatch_regex(pattern: str, s: str, result: bool):
    assert (regex_automata.fullmatch(pattern, s) is not None) is result


def test_characterset():
    p1 = regex_automata.compile(r"[abcd]")
    assert all(p1.fullmatch(c) for c in "abcd")

    p2 = regex_automata.compile(r"[a-d]")
    assert all(p2.fullmatch(c) for c in "abcd")

    p3 = regex_automata.compile(r"[a-bc-d]")
    assert all(p3.fullmatch(c) for c in "abcd")

    p4 = regex_automata.compile(r"[]abc]")
    assert all(p4.fullmatch(c) for c in "]abc")

    p5 = regex_automata.compile(r"[-abc]")
    assert all(p5.fullmatch(c) for c in "-abc")

    p6 = regex_automata.compile(r"[abc-]")
    assert all(p6.fullmatch(c) for c in "abc-")

    p7 = regex_automata.compile(r"[a-bC-D]", regex_automata.IGNORECASE)
    assert all(p7.fullmatch(c) for c in "abcdABCD")

    p8 = regex_automata.compile(r"[^a-d]")
    assert all(not p8.fullmatch(c) for c in "abcd")
    assert all(p8.fullmatch(c) for c in "efgh")

    p9 = regex_automata.compile(r"[^^]")
    assert p9.fullmatch("a")
    assert not p9.fullmatch("^")


def test_digits():
    p = regex_automata.compile(r"[1-5][0-9]|[0-9]")
    for i in range(60):
        assert p.fullmatch(str(i))

    assert not p.fullmatch("60")
    assert not p.fullmatch("01")
