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
    # Analysis to detect mutable default arguments (lists, dicts) that persist across function calls
    # This is a common Python pitfall: default argument values are created once at function definition time
    # If they're mutable and get modified, subsequent calls see the modified value
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Track function default arguments and their changes across invocations
        self.function_calls = {}
        self.analysis_name = "MutableDefaultArgsAnalysis"

    def pre_call(self, dyn_ast: str, iid: int, function: Callable, pos_args, kw_args):
        # Hook called before function execution; check if it has mutable default arguments
        # Get string representation of all mutable defaults (lists, dicts, sets) in this function
        dicts_and_lists = self.get_dicts_and_lists_as_str(function)
        # Skip if function has no mutable defaults
        if dicts_and_lists is None:
            return

        if function not in self.function_calls:
            # First time seeing this function: record baseline state of defaults
            # Using string representations avoids expensive deep comparisons on every call
            self.function_calls[function] = {
                "defaults": dicts_and_lists,
                "name": function.__name__,
            }
        else:
            # Subsequent call: check if default arguments changed from initial state
            if self.function_calls[function]["defaults"] != dicts_and_lists:
                prev = self.function_calls[function]["defaults"]
                # Mutable defaults were modified and carried over to this call
                self.add_finding(
                    iid,
                    dyn_ast,
                    "A-10",
                    f"mutable default args reused and changed in function {function.__name__} args: after: {dicts_and_lists} \n prev: {prev} in {dyn_ast}",
                )

    def get_dicts_and_lists_as_str(self, function: Callable) -> Optional[str]:
        # Extract mutable default argument values from function and return as string
        # Built-in methods don't have defaults attribute
        if not "__defaults__" in dir(function):
            return

        defaults = function.__defaults__
        if defaults is None:
            return None

        # Collect all list, dict, and set defaults
        res = []
        for i in defaults:
            if isinstance(i, type([])) or isinstance(i, type({})) or isinstance(i, type(set())):
                res.append(i)
        # Return None if no mutable defaults found
        if len(res) == 0:
            return None
        # Convert to string for efficient comparison (string comparison cheaper than deep object comparison)
        return str(res)
