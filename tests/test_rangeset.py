from regex_automata.automata.rangeset import RangeSet
from itertools import permutations


def test_simple():
    a = RangeSet(ranges=[(0, 10)])
    b = RangeSet(ranges=[(0, 10)], complement=True)

    for x in range(-5, 0):
        assert x not in a
        assert x in b
    for x in range(0, 10):
        assert x in a
        assert x not in b
    for x in range(10, 15):
        assert x not in a
        assert x in b


def test_union():
    base_ranges = [
        (0, -5),
        (3, 3),
        (0, 10),
        (10, 20),
        (5, 8),
        (15, 25),
    ]

    for ranges in permutations(base_ranges):
        for i in range(1, len(ranges)+1):
            reference_set = set()
            range_set_union = RangeSet()
            range_set_direct = RangeSet(ranges=ranges[:i])
            for j in range(i):
                reference_set |= set(range(*ranges[j]))
                range_set_union |= RangeSet(ranges=[ranges[j]])
                assert reference_set == set(range_set_union)
            assert reference_set == set(range_set_direct)


def test_intersection():
    base_ranges = [
        (0, -5),
        (3, 3),
        (0, 10),
        (10, 20),
        (5, 8),
        (15, 25),
    ]

    for ranges in permutations(base_ranges):
        for i in range(1, len(ranges)+1):
            reference_set = set(range(*ranges[0]))
            range_set_intersection = RangeSet(ranges=[ranges[0]])
            for j in range(1, i):
                reference_set &= set(range(*ranges[j]))
                range_set_intersection &= RangeSet(ranges=[ranges[j]])
                assert reference_set == set(range_set_intersection)
