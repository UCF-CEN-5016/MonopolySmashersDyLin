"""
Module for NonFinitesAnalysis functionality.
"""
from typing import Any, Callable, Dict, Tuple
from .base_analysis import BaseDyLinAnalysis
import pandas as pd
import numpy as np


class NonFinitesAnalysis(BaseDyLinAnalysis):
    """
Nonfinitesanalysis: logical component class.
"""
    def __init__(self, **kwargs):
        """
Init: implementation of the __init__ logic.

Key Variables:
    analysis_name: Local state member.
    total_values_investigated: Local state member.
    tracked_objects: Local state member.
"""
        super().__init__(**kwargs)
        self.analysis_name = "NonFinitesAnalysis"
        self.tracked_objects = {}
        self.total_values_investigated = 0

    def can_be_checked_with_numpy(self, value: any) -> bool:
        """
Can be checked with numpy: implementation of the can_be_checked_with_numpy logic.

Args:
    value: Operational parameter.

Returns:
    Standard result object.
"""
        return isinstance(value, np.ndarray) or isinstance(value, pd.DataFrame)

    def numpy_check_not_finite(self, df: any) -> bool:
        """
Numpy check not finite: implementation of the numpy_check_not_finite logic.

Args:
    df: Operational parameter.

Key Variables:
    is_inf: Local state member.
    result: Local state member.
    total_values_investigated: Local state member.

Returns:
    Standard result object.
"""
        try:
            is_inf = np.isinf(df)
            self.total_values_investigated = self.total_values_investigated + 1
            try:
                # need to extract values from pandas.Dataframes first
                result = True in is_inf.values
                return result
            except AttributeError as e:
                return True in is_inf
        except TypeError as e:
            return False

    def check_np_issue_found(self, value: any) -> bool:
        """
Check np issue found: implementation of the check_np_issue_found logic.

Args:
    value: Operational parameter.

Returns:
    Standard result object.
"""
        if self.can_be_checked_with_numpy(value) and self.numpy_check_not_finite(value):
            return True
        return False

    def post_call(
        self,
        dyn_ast: str,
        iid: int,
        result: Any,
        function: Callable,
        pos_args: Tuple,
        kw_args: Dict,
    ) -> Any:
        """
Post call: implementation of the post_call logic.

Args:
    dyn_ast: Dynamic AST tree.
    iid: Instruction identifier.
    result: Operational parameter.
    function: Operational parameter.
    pos_args: Positional logic arguments.
    kw_args: Keyword logic arguments.

Key Variables:
    args: Local state member.
    no_nan_in_input: Local state member.

Loop Behavior:
    Iterates through args.

Returns:
    Standard result object.
"""
        # print(f"{self.analysis_name} post_call {iid}")
        if result is function:
            return
        args = list(kw_args.values() if not kw_args is None else []) + list(pos_args if not pos_args is None else [])
        no_nan_in_input = True

        for arg in args:
            if self.check_np_issue_found(arg):
                self.add_finding(
                    iid,
                    dyn_ast,
                    "M-32",
                    f"NaN in numpy or Dataframe object in input {arg}",
                )
                no_nan_in_input = False

        if self.check_np_issue_found(result):
            if no_nan_in_input:
                self.add_finding(
                    iid,
                    dyn_ast,
                    "M-33",
                    f"NaN in numpy or Dataframe object in result, after applying function {function}",
                )

    def end_execution(self) -> None:
        """
End execution: implementation of the end_execution logic.

Returns:
    Standard result object.
"""
        self.add_meta({"total_values_investigated": self.total_values_investigated})
        super().end_execution()
