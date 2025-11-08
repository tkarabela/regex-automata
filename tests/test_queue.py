from regex_automata.regex.nfa_evaluator import UniquePriorityQueue


def test_simple():
    q = UniquePriorityQueue[int]()
    assert q.peek() is None
    assert list(sorted(q)) == []

    q.push(5)
    assert q.peek() == 5
    assert list(sorted(q)) == [5]

    q.push(5)
    assert q.peek() == 5
    assert list(sorted(q)) == [5]

    q.push(1)
    assert q.peek() == 1
    assert list(sorted(q)) == [1, 5]

    q.push(10)
    assert q.peek() == 1
    assert list(sorted(q)) == [1, 5, 10]

    assert q.pop() == 1
    assert q.peek() == 5
    assert list(sorted(q)) == [5, 10]

    assert q.pop() == 5
    assert q.peek() == 10
    assert list(sorted(q)) == [10]

    assert q.pop() == 10
    assert q.peek() is None
    assert list(sorted(q)) == []
