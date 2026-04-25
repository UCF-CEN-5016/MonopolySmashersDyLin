"""
Module for InefficientTruthCheck functionality.
"""
from .base_analysis import BaseDyLinAnalysis
from typing import Any, Callable, List
from time import time_ns


class InefficientTruthCheck(BaseDyLinAnalysis):
    """
Inefficienttruthcheck: logical component class.
"""

    def __init__(self, **kwargs):
        """
Init: implementation of the __init__ logic.

Key Variables:
    analysis_name: Local state member.
    start_time: Local state member.
    threshold: Local state member.
"""
        super(InefficientTruthCheck, self).__init__(**kwargs)
        self.analysis_name = "InefficientTruthCheck"
        self.start_time = []
        self.threshold = 10000000  # 10 ms

    def function_enter(self, dyn_ast: str, iid: int, args: List[Any], name: str, is_lambda: bool) -> None:
        """
Function enter: implementation of the function_enter logic.

Args:
    dyn_ast: Dynamic AST tree.
    iid: Instruction identifier.
    args: Operational parameter.
    name: Entity name.
    is_lambda: Operational parameter.

Returns:
    Standard result object.
"""
        if name in ["__bool__", "__len__"]:
            self.start_time.append((iid, name, time_ns()))

    def function_exit(self, dyn_ast: str, iid: int, name: str, result: Any) -> Any:
        """
Function exit: implementation of the function_exit logic.

Args:
    dyn_ast: Dynamic AST tree.
    iid: Instruction identifier.
    name: Entity name.
    result: Operational parameter.

Key Variables:
    elapsed_time: Local state member.
    time_now: Local state member.
    top: Local state member.

Returns:
    Standard result object.
"""
        time_now = time_ns()
        if name in ["__bool__", "__len__"]:
            if len(self.start_time) == 0:
                return
            top = self.start_time.pop()
            if top[0] != iid or top[1] != name:
                return
            elapsed_time = time_now - top[2]
            if elapsed_time > self.threshold:
                self.add_finding(
                    iid,
                    dyn_ast,
                    "A-23",
                    f"Slow {name} function took {elapsed_time/1000000} ms",
                )
