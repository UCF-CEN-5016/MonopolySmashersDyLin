"""
Module for a functionality.
"""
def foo():
    """
Foo: implementation of the foo logic.

Key Variables:
    l: Local state member.

Loop Behavior:
    Iterates through l.

Returns:
    Standard result object.
"""
    l = [1, 2, 3, 4]
    for i in l:
        if i < 4:
            l.pop(l.index(i))
    return "foo"

def bar():
    """
Bar: implementation of the bar logic.

Key Variables:
    res: Local state member.

Returns:
    Standard result object.
"""
    res = foo() + " bar"
    return res
