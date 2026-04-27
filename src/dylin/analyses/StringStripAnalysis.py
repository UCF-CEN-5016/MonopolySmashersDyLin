from typing import Any, Callable, Dict, Tuple
from .base_analysis import BaseDyLinAnalysis
from dynapyt.instrument.filters import only


class StringStripAnalysis(BaseDyLinAnalysis):
    # Detect common misunderstandings of str.strip behavior
    def __init__(self, **kwargs):
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
        # print(f"{self.analysis_name} post_call {iid}")
        # Ignore non-standard calls where value is the function object itself
        if val is function:
            return
        _self = getattr(function, "__self__", lambda: None)

        # Only analyze bound string.strip calls
        if not isinstance(_self, str):
            return

        if len(pos_args) > 0 and not _self is None and function == _self.strip:
            # strip(chars) treats chars as a set, not an exact prefix/suffix string
            arg = pos_args[0]
            _self = function.__self__
            if len(set(arg)) != len(arg):
                # Duplicate chars in strip argument often signal misunderstanding
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
                # Flag cases where extra neighboring chars can also be stripped unexpectedly
                self.add_finding(
                    iid,
                    dyn_ast,
                    "A-19",
                    f"Possible misuse of str.strip, might have removed something not expected before: {_self} arg: {arg} after: {val}",
                )
