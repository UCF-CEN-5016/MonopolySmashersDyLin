from typing import Any, Callable, Dict, Tuple
from .base_analysis import BaseDyLinAnalysis
import builtins
from dynapyt.instrument.filters import only


class BuiltinAllAnalysis(BaseDyLinAnalysis):
    # Analysis to detect misuse of all() and any() builtins, particularly with empty iterables
    def __init__(self, **kwargs):
        super(BuiltinAllAnalysis, self).__init__(**kwargs)
        self.analysis_name = "BuiltinAllAnalysis"

    def _flatten(self, l):
        # Recursively flatten nested lists into a single list for checking contents
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
        # Hook called after all() or any() is executed; check for suspicious empty-iterable cases
        # print(f"{self.analysis_name} post_call {iid}")
        if function == builtins.all or function == builtins.any:
            arg = pos_args[0]
            if isinstance(arg, list):
                # Flatten nested lists to check actual content
                flattened = self._flatten(arg)
                # Flag suspicious case: any([]) returned True (all([]) correctly returns True)
                # This likely indicates a logic error where empty case wasn't properly handled
                if len(flattened) == 0 and val == True:
                    self.add_finding(
                        iid,
                        dyn_ast,
                        "A-21",
                        f"Potentially unintended result for any() call, result: {val} arg: {arg}",
                    )
