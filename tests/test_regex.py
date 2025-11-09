import pytest

import regex_automata
from regex_automata import PatternFlag


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
                          ("(a|)", "a", True),
                          ("(a|)", "", True),
                          # ("a||c|", "", True),
                          # ("a||c|", "a", True),
                          # ("a||c|", "c", True),
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


def test_match():
    p1 = regex_automata.compile(r"a{3}")
    m = p1.match("aaa")
    assert m is not None and m.span() == (0, 3)
    m = p1.match("baaa")
    assert m is None
    m = p1.match("baaa", start=1)
    assert m is not None and m.span() == (1, 4)

    p2 = regex_automata.compile(r"a+")
    m = p2.match("aaaaaaaaaaaaaaaaaa", start=5, end=7)
    assert m is not None and m.span() == (5, 7)


def test_search():
    p1 = regex_automata.compile(r"([a-z0-9]+)@([a-z0-9]+\.[a-z0-9]+)")

    m = p1.search("text abc@def.com xyz@123.com")
    assert m is not None
    assert m.group() == "abc@def.com"
    assert m.groupdict() == {0: "abc@def.com", 1: "abc", 2: "def.com"}

    m = p1.search("text abc@def.com xyz@123.com", start=10)
    assert m is not None
    assert m.group() == "xyz@123.com"
    assert m.groupdict() == {0: "xyz@123.com", 1: "xyz", 2: "123.com"}


def test_overlapping_search():
    p1 = regex_automata.compile(r"aa")
    matches = list(p1.finditer("aaaaaaa"))
    assert len(matches) == 3
    assert matches[0].span() == (0, 2)
    assert matches[1].span() == (2, 4)
    assert matches[2].span() == (4, 6)


def test_boundary_assertion():
    m = regex_automata.search(r"abc$", "foo abc")
    assert m is not None and m.group() == "abc"
    m = regex_automata.search(r"abc$", "abcdef")
    assert m is None
    m = regex_automata.search(r"abc$", "abc\ndef", regex_automata.MULTILINE)
    assert m is not None and m.group() == "abc"

    m = regex_automata.search(r"^abc", "abc foo")
    assert m is not None and m.group() == "abc"
    m = regex_automata.search(r"^abc", "foo abc")
    assert m is None
    m = regex_automata.search(r"^abc", "foo\nabc", regex_automata.MULTILINE)
    assert m is not None and m.group() == "abc"

    m = regex_automata.search(r"\bm", "moon")
    assert m is not None and m.span() == (0, 1)
    m = regex_automata.search(r"oon\b", "moon")
    assert m is not None and m.span() == (1, 4)

    m = regex_automata.search(r"\Bon", "at noon")
    assert m is not None and m.span() == (5, 7)
    m = regex_automata.search(r"\Bno", "at noon")
    assert m is None


def test_groups():
    m = regex_automata.match(r"((foo|bar)*)baz", "barbarfoobaz")
    assert m is not None
    assert m.groupdict() == {0: 'barbarfoobaz', 1: 'foo', 2: 'barbarfoo'}


def test_findall():
    assert regex_automata.findall(r'\bf[a-z]*', 'which foot or hand fell fastest') == ['foot', 'fell', 'fastest']
    assert regex_automata.findall(r'(\w+)=(\d+)', 'set width=20 and height=10') == [('width', '20'), ('height', '10')]


def test_split():
    assert regex_automata.split(r'\W+', 'Words, words, words.') == ['Words', 'words', 'words', '']
    assert regex_automata.split(r'(\W+)', 'Words, words, words.') == ['Words', ', ', 'words', ', ', 'words', '.', '']
    assert regex_automata.split(r'\W+', 'Words, words, words.', maxsplit=1) == ['Words', 'words, words.']
    assert regex_automata.split('[a-f]+', '0a3B9', flags=regex_automata.IGNORECASE) == ['0', '3', '9']
    assert regex_automata.split(r'(\W+)', '...words, words...') == ['', '...', 'words', ', ', 'words', '...', '']
    assert regex_automata.split(r'\b', 'Words, words, words.') == ['', 'Words', ', ', 'words', ', ', 'words', '.']
    # assert regex_automata.split(r'\W*', '...words...') == ['', '', 'w', 'o', 'r', 'd', 's', '', '']
    # assert regex_automata.split(r'(\W*)', '...words...') == ['', '...', '', '', 'w', '', 'o', '', 'r', '', 'd', '', 's', '...', '', '', '']
    assert regex_automata.split(r"([a-z]+)|([0-9]+)", "abc.132.def") == ['', 'abc', None, '.', None, '132', '.', 'def', None, '']