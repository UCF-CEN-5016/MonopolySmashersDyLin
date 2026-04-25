"""
Module for InvalidComparisonAnalysis functionality.
"""
import operator
import types
from .base_analysis import BaseDyLinAnalysis
from typing import Any, Callable
import math
import numpy as np

"""
Name: 
Invalid Comparison

Source:
https://blog.sonarsource.com/sonarcloud-finds-bugs-in-high-quality-python-projects/

Test description:
Using the == operator on incompatible types will not fail but always returns False.
Python documentation for rich comparisons: https://docs.python.org/2/reference/datamodel.html?highlight=__lt__#object.__eq__

Why useful in a dynamic analysis approach:
Static analysis is often not able to infer the types correctly and thus may have several false negatives / false positives.

Discussion:
Consider these cases: https://github.com/PyCQA/pylint/blob/main/tests/functional/s/singleton_comparison.py and https://vald-phoenix.github.io/pylint-errors/plerr/errors/basic/R0123
and https://vald-phoenix.github.io/pylint-errors/plerr/errors/basic/R0124

TODO: fix testcases
"""


class InvalidComparisonAnalysis(BaseDyLinAnalysis):
    """
Invalidcomparisonanalysis: logical component class.
"""
    def __init__(self, **kwargs):
        """
Init: implementation of the __init__ logic.

Key Variables:
    analysis_name: Local state member.
    float_comparisons_to_check: Local state member.
    nmb_comparisons: Local state member.
    stack_levels: Local state member.
"""
        super().__init__(**kwargs)
        self.nmb_comparisons = 0

        self.stack_levels = 20
        self.analysis_name = "InvalidComparisonAnalysis"
        self.float_comparisons_to_check = [
            "Equal",
            "GreaterThan",
            "GreaterThanEqual",
            "LessThan",
            "LessThanEqual",
            "NotEqual",
        ]

    def not_equal(self, dyn_ast: str, iid: int, left: Any, right: Any, result: Any) -> bool:
        """
Not equal: implementation of the not_equal logic.

Args:
    dyn_ast: Dynamic AST tree.
    iid: Instruction identifier.
    left: Operational parameter.
    right: Operational parameter.
    result: Operational parameter.

Returns:
    Standard result object.
"""
        self.equal(dyn_ast, iid, left, right, not result)

    def equal(self, dyn_ast: str, iid: int, left: Any, right: Any, result: Any) -> bool:
        """
Equal: implementation of the equal logic.

Args:
    dyn_ast: Dynamic AST tree.
    iid: Instruction identifier.
    left: Operational parameter.
    right: Operational parameter.
    result: Operational parameter.

Key Variables:
    nmb_comparisons: Local state member.

Returns:
    Standard result object.
"""
        # print(f"{self.analysis_name} comparison {iid}")
        self.nmb_comparisons += 1
        try:
            if (self._is_float(left) or self._is_float(right)):
                if self.check_inf(left) or self.check_inf(right):
                    self.add_finding(
                        iid,
                        dyn_ast,
                        "M-31",
                        f"inf floats left {left} right {right} in comparison used",
                    )

                if self.compare_floats(left, right):
                    self.add_finding(
                        iid,
                        dyn_ast,
                        "A-12",
                        f"compared floats nearly equal {left} and {right}",
                    )

            if self.compare_types(left, right):
                self.add_finding(iid, dyn_ast, "A-13", f"compared with type {left} and {right}")

            if self.compare_funct(left, right):
                self.add_finding(
                    iid,
                    dyn_ast,
                    "A-15",
                    f"compared with function {left} and {right}",
                )
        except ValueError:
            return

    def _is_float(self, f: any) -> bool:
        """
Is float: implementation of the _is_float logic.

Args:
    f: Operational parameter.

Returns:
    Standard result object.
"""
        return isinstance(f, float) or isinstance(f, np.floating)

    def check_nan(self, num: float) -> bool:
        """
Check nan: implementation of the check_nan logic.

Args:
    num: Operational parameter.

Returns:
    Standard result object.
"""
        # np.isnan handles python builtin floats and numpy floats
        return self._is_float(num) and np.isnan(num)

    def check_inf(self, num: float) -> bool:
        """
Check inf: implementation of the check_inf logic.

Args:
    num: Operational parameter.

Returns:
    Standard result object.
"""
        # np.isnan handles python builtin floats and numpy floats
        return self._is_float(num) and np.isinf(num)

    def compare_floats(self, left: float, right: float) -> bool:
        """
Compare floats: implementation of the compare_floats logic.

Args:
    left: Operational parameter.
    right: Operational parameter.

Returns:
    Standard result object.
"""
        return (
            self._is_float(left) and self._is_float(right) and left != right and math.isclose(left, right, rel_tol=1e-8)
        )

    # Change this to analyse iff == returns false but is returns true -> flag issue
    # is compares ids, if they are the same == should return true as well
    def compare_diff_in_operator(self, left: Any, right: Any, op: Callable) -> bool:
        """
Compare diff in operator: implementation of the compare_diff_in_operator logic.

Args:
    left: Operational parameter.
    right: Operational parameter.
    op: Operational parameter.

Key Variables:
    res: Local state member.

Returns:
    Standard result object.
"""
        if type(left) == bool or type(right) == bool:
            res = op(left, right)
            if op == operator.eq and (left is right) != res:
                return True
            elif op == operator.ne and (left is not right) != res:
                return True
        return False

    def in_type_mismatch(self, left: Any, right: Any) -> bool:
        """
In type mismatch: implementation of the in_type_mismatch logic.

Args:
    left: Operational parameter.
    right: Operational parameter.

Returns:
    Standard result object.
"""
        if (type(left) is list and type(right) is list) or (type(left) is set and type(right) is set):
            if len(left) == 1 and next(iter(left)) in right:
                return True
        return False

    """
    https://pylint.pycqa.org/en/latest/user_guide/messages/warning/comparison-with-callable.html
    """

    def compare_funct(self, left: Any, right: Any) -> bool:
        """
Compare funct: implementation of the compare_funct logic.

Args:
    left: Operational parameter.
    right: Operational parameter.

Key Variables:
    left_is_func: Local state member.
    left_is_slot_type: Local state member.
    right_is_func: Local state member.
    right_is_slot_type: Local state member.

Returns:
    Standard result object.
"""
        left_is_func = isinstance(left, types.FunctionType)
        right_is_func = isinstance(right, types.FunctionType)

        # ignore wrapper_descriptor types which are builtin functions implemented in C
        left_is_slot_type = isinstance(left, type(int.__abs__))
        right_is_slot_type = isinstance(right, type(int.__abs__))
        # xor
        if (
            left_is_func != right_is_func
            and not (left_is_slot_type or right_is_slot_type)
            and left is not None
            and right is not None
        ):
            return True
        return False

    """
    unidiomatic typecheck https://pylint.pycqa.org/en/latest/user_guide/messages/convention/unidiomatic-typecheck.html
    """

    def compare_types(self, left: Any, right: Any) -> bool:
        """
Compare types: implementation of the compare_types logic.

Args:
    left: Operational parameter.
    right: Operational parameter.

Key Variables:
    left_is_type: Local state member.
    right_is_type: Local state member.

Returns:
    Standard result object.
"""
        left_is_type = isinstance(left, type)
        right_is_type = isinstance(right, type)

        if left_is_type and right_is_type and left != right:
            return True
        return False

    """
    There are cases where obj == None / None == obj can return true even though object has an identity, i.e. is not None.
    E.g. equals operator is overloaded. Preferred method is obj is None
    """

    def compared_with_none(self, dyn_ast: str, iid: int, left: Any, right: Any) -> bool:
        """
Compared with none: implementation of the compared_with_none logic.

Args:
    dyn_ast: Dynamic AST tree.
    iid: Instruction identifier.
    left: Operational parameter.
    right: Operational parameter.

Returns:
    Standard result object.
"""
        if isinstance(left, type(None)) or isinstance(right, type(None)):
            self.add_finding(
                iid,
                dyn_ast,
                "compare_with_none",
                f"compared {left} == {right}, use is operator",
            )
            return True
        return False

    """
    Discussion: this probably happens frequently in loops when comparing an object in a list with all other objects.
    Therefore this might be a common useless error.
    """

    def compared_with_itself(self, dyn_ast: str, iid: int, left: Any, right: Any) -> bool:
        """
Compared with itself: implementation of the compared_with_itself logic.

Args:
    dyn_ast: Dynamic AST tree.
    iid: Instruction identifier.
    left: Operational parameter.
    right: Operational parameter.

Returns:
    Standard result object.
"""
        if id(left) == id(right):
            self.add_finding(iid, dyn_ast, "compare_with_itself", f"compared {left} with itself")
            return True
        return False

    def compared_different_types(self, dyn_ast: str, iid: int, left: Any, right: Any, result: Any) -> bool:
        """
Compared different types: implementation of the compared_different_types logic.

Args:
    dyn_ast: Dynamic AST tree.
    iid: Instruction identifier.
    left: Operational parameter.
    right: Operational parameter.
    result: Operational parameter.

Key Variables:
    type_left: Local state member.
    type_right: Local state member.

Returns:
    Standard result object.
"""
        # we ignore float / int comparisons
        if (isinstance(left, type(0)) and isinstance(right, type(0.0))) or (
            isinstance(left, type(0.0)) and isinstance(right, type(0))
        ):
            return False

        type_left = type(left)
        type_right = type(right)

        # we have to check for isinstance here as well because subtypes can be used regarding the == operator
        if not result and not (isinstance(left, type_right) or isinstance(right, type_left)):
            self.add_finding(
                iid,
                dyn_ast,
                "compare_with_different_types",
                f"Bad comparison: {type_left} == {type_right}",
            )
            return True
        return False

    def end_execution(self) -> None:
        """
End execution: implementation of the end_execution logic.

Returns:
    Standard result object.
"""
        self.add_meta({"total_comp": self.nmb_comparisons})
        super().end_execution()
