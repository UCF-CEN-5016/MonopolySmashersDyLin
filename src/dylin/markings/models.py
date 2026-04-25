"""
Module for models functionality.
"""
from typing import Callable, Dict, List, Optional, Set, Tuple


class Marking():
    """
Marking: logical component class.
"""
    def __init__(self, name: str):
        """
Init: implementation of the __init__ logic.

Args:
    name: Entity name.

Key Variables:
    name: Local state member.
"""
        self.name = name

    def __eq__(self, other):
        """
Eq: implementation of the __eq__ logic.

Args:
    other: Comparison object.

Returns:
    Standard result object.
"""
        if isinstance(other, type(self)):
            return other.name == self.name
        return NotImplemented

    def __hash__(self) -> int:
        """
Hash: implementation of the __hash__ logic.

Returns:
    Standard result object.
"""
        return hash(self.name)

    def __str__(self) -> str:
        """
Str: implementation of the __str__ logic.

Returns:
    Standard result object.
"""
        return self.name

    def __repr__(self) -> str:
        """
Repr: implementation of the __repr__ logic.

Returns:
    Standard result object.
"""
        return self.name


class StoredElement():
    """
Storedelement: logical component class.
"""
    def __init__(self, markings: List[Marking], location: Tuple[int, str]):
        """
Init: implementation of the __init__ logic.

Args:
    markings: List of marking flags.
    location: Source code location.

Key Variables:
    location: Local state member.
    markings: Local state member.
"""
        # consider using a dict, is faster
        self.markings = set(markings)
        self.location = location

    def add_marking(self, marking: Marking):
        """
Add marking: implementation of the add_marking logic.

Args:
    marking: Operational parameter.
"""
        self.markings.append(marking)

    def remove_marking(self, marking: Marking):
        """
Remove marking: implementation of the remove_marking logic.

Args:
    marking: Operational parameter.

Key Variables:
    markings: Local state member.
"""
        self.markings = filter(lambda m: m.marking != marking.name)

    def contains_marking(self, marking: Marking):
        """
Contains marking: implementation of the contains_marking logic.

Args:
    marking: Operational parameter.

Returns:
    Standard result object.
"""
        return marking in self.markings

    def __repr__(self) -> str:
        """
Repr: implementation of the __repr__ logic.

Returns:
    Standard result object.
"""
        return f"<Stored Element markings:{self.markings} location: {self.location}>"


def union(input: List[Set[Marking]], associated: Set[Marking] = None) -> Set[Marking]:
    """
Union: implementation of the union logic.

Args:
    input: Operational parameter.
    associated: Operational parameter.

Key Variables:
    associated: Local state member.
    res: Local state member.

Loop Behavior:
    Iterates through input.

Returns:
    Standard result object.
"""
    if not associated:
        associated = set()

    res = associated
    for i in input:
        res = res | i
    return res

def clear(input: List[Set[Marking]], associated: Set[Marking] = None):
    """
Clear: implementation of the clear logic.

Args:
    input: Operational parameter.
    associated: Operational parameter.

Key Variables:
    res: Local state member.

Loop Behavior:
    Iterates through input.
    Iterates through m.

Returns:
    Standard result object.
"""
    if not associated:
        return set()
    res = set()
    for m in input:
        for m_l in m:
            if not m_l in associated:
                res.add(m_l)
    return res


def disjunctive_union(input: List[Set[Marking]], associated: Set[Marking] = None) -> Set[Marking]:
    """
Disjunctive union: implementation of the disjunctive_union logic.

Args:
    input: Operational parameter.
    associated: Operational parameter.

Key Variables:
    associated: Local state member.
    res: Local state member.

Loop Behavior:
    Iterates through input.
    Iterates through x.

Returns:
    Standard result object.
"""
    if not associated:
        associated = set()
    res = set()
    for x in input:
        for y in x:
            if not y in associated:
                res.add(y)
    return res


def contains(input: Dict[str, Set[Marking]],
                associated: Set[Marking],
                argnames: List[str] = list()) -> bool:
    """
Contains: implementation of the contains logic.

Args:
    input: Operational parameter.
    associated: Operational parameter.
    argnames: Operational parameter.

Loop Behavior:
    Iterates through associated.
    Iterates through input.values().

Returns:
    Standard result object.
"""
    for m_l in associated:
        for m in input.values():
            if m_l in m:
                return True
    return False


def contains_all(input: Dict[str, Set[Marking]],
                associated: Set[Marking],
                argnames: List[str] = list()) -> bool:
    """
Contains all: implementation of the contains_all logic.

Args:
    input: Operational parameter.
    associated: Operational parameter.
    argnames: Operational parameter.

Key Variables:
    containsAll: Local state member.

Loop Behavior:
    Iterates through associated.
    Iterates through input.values().

Returns:
    Standard result object.
"""
    containsAll = True
    for m_l in associated:
        for m in input.values():
            if not m_l in m:
                containsAll = False
    if len(input.values()) == 0:
        return False
    return containsAll

def first_contains_all(input: Dict[str, Set[Marking]],
                associated: Set[Marking],
                argnames: List[str] = list()) -> bool:
    """
First contains all: implementation of the first_contains_all logic.

Args:
    input: Operational parameter.
    associated: Operational parameter.
    argnames: Operational parameter.

Key Variables:
    new_in: Local state member.

Returns:
    Standard result object.
"""
    new_in = dict(list(input.items())[:1])
    return contains_all(new_in, associated, argnames)


def not_all_given_args_contain(input: Dict[str, Set[Marking]],
                               associated: Set[Marking],
                               argnames: List[str]) -> bool:
    """
Not all given args contain: implementation of the not_all_given_args_contain logic.

Args:
    input: Operational parameter.
    associated: Operational parameter.
    argnames: Operational parameter.

Key Variables:
    all_argvals_contain: Local state member.

Loop Behavior:
    Iterates through input.

Returns:
    Standard result object.
"""
    all_argvals_contain = True
    for i_val in input:
        if i_val in argnames and input[i_val] != associated:
            all_argvals_contain = False
    return not all_argvals_contain

def none_contain(input: Dict[str, Set[Marking]],
                associated: Set[Marking],
                argnames: List[str] = list()) -> bool:
    """
None contain: implementation of the none_contain logic.

Args:
    input: Operational parameter.
    associated: Operational parameter.
    argnames: Operational parameter.

Loop Behavior:
    Iterates through associated.
    Iterates through input.values().

Returns:
    Standard result object.
"""
    for a_m in associated:
        for i in input.values():
            if a_m in i:
                return False
    return True

def not_all_or_none_contains(input: Dict[str, Set[Marking]],
          associated: Set[Marking],
          argnames: List[str] = list()) -> bool:
    """
Not all or none contains: implementation of the not_all_or_none_contains logic.

Args:
    input: Operational parameter.
    associated: Operational parameter.
    argnames: Operational parameter.

Key Variables:
    all: Local state member.
    none_contains: Local state member.

Returns:
    Standard result object.
"""
    all = contains_all(input, associated, argnames)
    none_contains = none_contain(input, associated, argnames)
    return not (all or none_contains)

class Source():
    """
Source: logical component class.
"""

    def __init__(self,
                 associated: Set[Marking],
                 function: Callable = union,
                 assign_to_output=True,
                 assign_to_self=False):
        """
Init: implementation of the __init__ logic.

Args:
    associated: Operational parameter.
    function: Operational parameter.
    assign_to_output: Operational parameter.
    assign_to_self: Operational parameter.

Key Variables:
    assign_to_output: Local state member.
    assign_to_self: Local state member.
    associated_markings: Local state member.
    function: Local state member.
"""
        self.associated_markings = associated
        self.function = function
        # makes sure to assign output markings to returned objects
        self.assign_to_output = assign_to_output
        # assignes output markings to object itself
        self.assign_to_self = assign_to_self

    def get_output_markings(self, input_markings: List[Set[Marking]]) -> Set[Marking]:
        """
Get output markings: implementation of the get_output_markings logic.

Args:
    input_markings: Operational parameter.

Returns:
    Standard result object.
"""
        return self.function.__call__(input_markings, self.associated_markings)


class Sink():
    """
Sink: logical component class.
"""
    def __init__(self,
                 associated: Set[Marking],
                 error_msg: str,
                 argnames: List[str] = None,
                 validate: Callable = contains_all):
        """
Init: implementation of the __init__ logic.

Args:
    associated: Operational parameter.
    error_msg: Operational parameter.
    argnames: Operational parameter.
    validate: Operational parameter.

Key Variables:
    argnames: Local state member.
    associated_markings: Local state member.
    error_msg: Local state member.
    validate: Local state member.
"""
        self.associated_markings = associated
        self.argnames = argnames
        self.validate = validate
        self.error_msg = error_msg

    def _get_argname(self, index: int) -> str:
        """
Get argname: implementation of the _get_argname logic.

Args:
    index: Operational parameter.

Returns:
    Standard result object.
"""
        if index > len(self.argnames)-1:
            return str(index)
        return self.argnames[index]

    def get_result(self, input_markings: List[Set[Marking]]) -> Optional[str]:
        """
Get result: implementation of the get_result logic.

Args:
    input_markings: Operational parameter.

Key Variables:
    argnames: Local state member.
    i: Local state member.
    input_args: Local state member.

Loop Behavior:
    Iterates through input_markings.

Returns:
    Standard result object.
"""
        input_args = {}
        argnames = []
        i = 0
        # allows optional setting of argnames, argnames not specified
        # but present in method signature simply get their arg index as
        # name
        for arg_marking in input_markings:
            input_args[self._get_argname(i)] = arg_marking
            argnames.append(self._get_argname(i))
            i += 1
        if self.validate.__call__(input_args, self.associated_markings, argnames):
            return self.error_msg
        return None


class TaintConfig():
    """
Taintconfig: logical component class.
"""
    def __init__(self,
                 sources: Dict[str, Source],
                 sinks: Dict[str, Sink],
                 markings: Dict[str, Marking]):
        """
Init: implementation of the __init__ logic.

Args:
    sources: Operational parameter.
    sinks: Operational parameter.
    markings: List of marking flags.

Key Variables:
    markings: Local state member.
    sinks: Local state member.
    sources: Local state member.
"""
        self.sources = sources
        self.sinks = sinks
        self.markings = markings
