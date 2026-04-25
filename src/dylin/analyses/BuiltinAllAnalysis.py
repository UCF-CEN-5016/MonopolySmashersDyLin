"""
Module for BuiltinAllAnalysis functionality.
"""
from typing import Any, Callable, Dict, Tuple
from .base_analysis import BaseDyLinAnalysis
import builtins
from dynapyt.instrument.filters import only


class BuiltinAllAnalysis(BaseDyLinAnalysis):
    """
Builtinallanalysis: logical component class.
"""
    def __init__(self, **kwargs):
        """
Init: implementation of the __init__ logic.

Key Variables:
    analysis_name: Local state member.
"""
        super(BuiltinAllAnalysis, self).__init__(**kwargs)
        self.analysis_name = "BuiltinAllAnalysis"

    def _flatten(self, l):
        """
Flatten: implementation of the _flatten logic.

Args:
    l: Operational parameter.

Key Variables:
    new_list: Local state member.

Loop Behavior:
    Iterates through l.

Returns:
    Standard result object.
"""
        new_list = []
        for i in l:
            if isinstance(i, list):
                new_list = new_list + self._flatten(i)
            else:
                new_list.append(i)
        return new_list

    @only(patterns=["all", "any"])
    def post_call(
        self,
        dyn_ast: str,
        iid: int,
        val: Any,
        function: Callable,
        pos_args: Tuple,
        kw_args: Dict,
    ) -> Any:
        """
Post call: implementation of the post_call logic.

Args:
    dyn_ast: Dynamic AST tree.
    iid: Instruction identifier.
    val: Operational parameter.
    function: Operational parameter.
    pos_args: Positional logic arguments.
    kw_args: Keyword logic arguments.

Key Variables:
    arg: Local state member.
    flattened: Local state member.

Returns:
    Standard result object.
"""
        # print(f"{self.analysis_name} post_call {iid}")
        if function == builtins.all or function == builtins.any:
            arg = pos_args[0]
            if isinstance(arg, list):
                flattened = self._flatten(arg)
                if len(flattened) == 0 and val == True:
                    self.add_finding(
                        iid,
                        dyn_ast,
                        "A-21",
                        f"Potentially unintended result for any() call, result: {val} arg: {arg}",
                    )
