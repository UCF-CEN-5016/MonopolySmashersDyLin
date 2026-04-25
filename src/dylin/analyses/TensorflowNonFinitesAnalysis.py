"""
Module for TensorflowNonFinitesAnalysis functionality.
"""
from typing import Any, Callable, Dict, Tuple
from .base_analysis import BaseDyLinAnalysis
import tensorflow as tf


class TensorflowNonFinitesAnalysis(BaseDyLinAnalysis):
    """
Tensorflownonfinitesanalysis: logical component class.
"""
    def __init__(self, **kwargs):
        """
Init: implementation of the __init__ logic.

Key Variables:
    analysis_name: Local state member.
    total_tensors_investigated: Local state member.
    tracked_objects: Local state member.
"""
        super().__init__(**kwargs)
        tf.get_logger().setLevel("INFO")
        self.analysis_name = "TensorflowNonFinitesAnalysis"
        self.tracked_objects = {}
        self.total_tensors_investigated = 0

    def check_contains_nan_or_inf(self, tensor: tf.Tensor) -> bool:
        """
Check contains nan or inf: implementation of the check_contains_nan_or_inf logic.

Args:
    tensor: Operational parameter.

Key Variables:
    total_tensors_investigated: Local state member.

Returns:
    Standard result object.
"""
        try:
            self.total_tensors_investigated = self.total_tensors_investigated + 1
            # checks if tensor contains NaN / inf / -inf by throwing an exception
            tf.debugging.check_numerics(tensor, "")
        except Exception as e:
            try:
                # Some uncommon exceptions for e can be thrown which do not
                # contain a message attribute as expected
                if "Tensor had" in e.message:
                    return True
            except Exception:
                return False
        return False

    def check_tf_issue_found(self, value: any) -> bool:
        """
Check tf issue found: implementation of the check_tf_issue_found logic.

Args:
    value: Operational parameter.

Returns:
    Standard result object.
"""
        if isinstance(value, tf.Tensor) and tf.is_tensor(value) and self.check_contains_nan_or_inf(value):
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
            if self.check_tf_issue_found(arg):
                self.add_finding(
                    iid,
                    dyn_ast,
                    "M-26",
                    f"NaN in tensor input, result also contains NaN arg {arg}",
                )
                no_nan_in_input = False

        if self.check_tf_issue_found(result):
            if no_nan_in_input:
                self.add_finding(
                    iid,
                    dyn_ast,
                    "M-27",
                    f"NaN in result tensor after applying function {function}",
                )

    def end_execution(self) -> None:
        """
End execution: implementation of the end_execution logic.

Returns:
    Standard result object.
"""
        self.add_meta({"total_tensors_investigated": self.total_tensors_investigated})
        super().end_execution()
