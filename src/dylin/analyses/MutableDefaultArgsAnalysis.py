"""
Module for MutableDefaultArgsAnalysis functionality.
"""
from .base_analysis import BaseDyLinAnalysis
from typing import Any, Callable, List, Optional, Tuple, Dict
import traceback

"""
Name: 
Mutable Default Arguments

Source:
-

Test description:
Because methods are first class objects default values are saved. If default values are changed
a second invocation of the function will keep the changed value

Why useful in a dynamic analysis approach:
Non trivial control flows can make it nearly impossible to detect such behavior in static analysis

Discussion:
This can be useful and is intended behavior for python. Experienced python programmers might use this
deliberately.
"""


class MutableDefaultArgsAnalysis(BaseDyLinAnalysis):
    """
Mutabledefaultargsanalysis: logical component class.
"""
    def __init__(self, **kwargs):
        """
Init: implementation of the __init__ logic.

Key Variables:
    analysis_name: Local state member.
    function_calls: Local state member.
"""
        super().__init__(**kwargs)
        self.function_calls = {}
        self.analysis_name = "MutableDefaultArgsAnalysis"

    def pre_call(self, dyn_ast: str, iid: int, function: Callable, pos_args, kw_args):
        """
Pre call: implementation of the pre_call logic.

Args:
    dyn_ast: Dynamic AST tree.
    iid: Instruction identifier.
    function: Operational parameter.
    pos_args: Positional logic arguments.
    kw_args: Keyword logic arguments.

Key Variables:
    dicts_and_lists: Local state member.
    prev: Local state member.
"""
        dicts_and_lists = self.get_dicts_and_lists_as_str(function)
        # we are only interested in [] or {} or set()
        if dicts_and_lists is None:
            return

        if function not in self.function_calls:
            # comparing string representations of default values is sufficient here
            # and more performant compared to a deep list comparison of each element
            self.function_calls[function] = {
                "defaults": dicts_and_lists,
                "name": function.__name__,
            }
        else:
            if self.function_calls[function]["defaults"] != dicts_and_lists:
                prev = self.function_calls[function]["defaults"]
                self.add_finding(
                    iid,
                    dyn_ast,
                    "A-10",
                    f"mutable default args reused and changed in function {function.__name__} args: after: {dicts_and_lists} \n prev: {prev} in {dyn_ast}",
                )

    def get_dicts_and_lists_as_str(self, function: Callable) -> Optional[str]:
        """
Get dicts and lists as str: implementation of the get_dicts_and_lists_as_str logic.

Args:
    function: Operational parameter.

Key Variables:
    defaults: Local state member.
    res: Local state member.

Loop Behavior:
    Iterates through defaults.

Returns:
    Standard result object.
"""
        # built in methods do not have defaults
        if not "__defaults__" in dir(function):
            return

        defaults = function.__defaults__
        if defaults is None:
            return None

        res = []
        for i in defaults:
            if isinstance(i, type([])) or isinstance(i, type({})) or isinstance(i, type(set())):
                res.append(i)
        if len(res) == 0:
            return None
        return str(res)
