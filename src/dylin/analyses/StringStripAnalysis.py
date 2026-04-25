"""
Module for StringStripAnalysis functionality.
"""
from typing import Any, Callable, Dict, Tuple
from .base_analysis import BaseDyLinAnalysis
from dynapyt.instrument.filters import only


class StringStripAnalysis(BaseDyLinAnalysis):
    """
Stringstripanalysis: logical component class.
"""
    def __init__(self, **kwargs):
        """
Init: implementation of the __init__ logic.

Key Variables:
    analysis_name: Local state member.
"""
        super(StringStripAnalysis, self).__init__(**kwargs)
        self.analysis_name = "StringStripAnalysis"

    @only(patterns=["strip"])
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
    _self: Local state member.
    arg: Local state member.

Returns:
    Standard result object.
"""
        # print(f"{self.analysis_name} post_call {iid}")
        if val is function:
            return
        _self = getattr(function, "__self__", lambda: None)

        if not isinstance(_self, str):
            return

        if len(pos_args) > 0 and not _self is None and function == _self.strip:
            arg = pos_args[0]
            _self = function.__self__
            if len(set(arg)) != len(arg):
                self.add_finding(
                    iid,
                    dyn_ast,
                    "A-20",
                    f"Possible misuse of str.strip, arg contains duplicates {arg}",
                )
            if len(arg) > 1 and (
                (_self.startswith(arg) and _self[len(arg) : len(arg) + 1] in arg)
                or (_self.endswith(arg) and _self[-len(arg) - 1 : -len(arg)] in arg)
            ):
                self.add_finding(
                    iid,
                    dyn_ast,
                    "A-19",
                    f"Possible misuse of str.strip, might have removed something not expected before: {_self} arg: {arg} after: {val}",
                )
