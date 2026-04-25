"""
Module for test_b functionality.
"""
from simpletoy import b as simpleB

def test_baz():
    """
Test baz: implementation of the test_baz logic.

Key Variables:
    res: Local state member.
"""
    res = simpleB.baz(" ")
    assert res == "foo foo"