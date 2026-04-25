"""
Module for test_a functionality.
"""
from simpletoy import a as simpleA

def test_foo():
    """
Test foo: implementation of the test_foo logic.

Key Variables:
    res: Local state member.
"""
    res = simpleA.foo()
    assert res == "foo"

def test_bar():
    """
Test bar: implementation of the test_bar logic.

Key Variables:
    res: Local state member.
"""
    res = simpleA.bar()
    assert res == "foo bar"