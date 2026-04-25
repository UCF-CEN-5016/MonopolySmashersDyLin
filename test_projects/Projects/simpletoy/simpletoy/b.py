"""
Module for b functionality.
"""
from .a import foo

def baz(s: str):
    """
Baz: implementation of the baz logic.

Args:
    s: Operational parameter.

Key Variables:
    res: Local state member.

Returns:
    Standard result object.
"""
    res = foo() + s + foo()
    return res