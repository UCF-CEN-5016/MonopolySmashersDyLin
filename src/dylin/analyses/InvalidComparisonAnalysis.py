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
    # Analysis to detect risky and invalid comparison operations that may hide bugs
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Track total number of comparisons seen during execution for statistics
        self.nmb_comparisons = 0

        self.stack_levels = 20
        self.analysis_name = "InvalidComparisonAnalysis"
        # List of comparison operations to check for float/type mismatches
        self.float_comparisons_to_check = [
            "Equal",
            "GreaterThan",
            "GreaterThanEqual",
            "LessThan",
            "LessThanEqual",
            "NotEqual",
        ]

    def not_equal(self, dyn_ast: str, iid: int, left: Any, right: Any, result: Any) -> bool:
        # For != operations, flip result and call equal() since != is opposite of ==
        self.equal(dyn_ast, iid, left, right, not result)

    def equal(self, dyn_ast: str, iid: int, left: Any, right: Any, result: Any) -> bool:
        # Hook called after == comparison operations; checks for various problematic patterns
        # print(f"{self.analysis_name} comparison {iid}")
        self.nmb_comparisons += 1
        try:
            # Check if either operand is a float (builtin or numpy)
            if (self._is_float(left) or self._is_float(right)):
                # Flag if comparing with infinity values (may mask NaN errors)
                if self.check_inf(left) or self.check_inf(right):
                    self.add_finding(
                        iid,
                        dyn_ast,
                        "M-31",
                        f"inf floats left {left} right {right} in comparison used",
                    )

                # Flag if two floats are nearly equal (precision issues in equality)
                if self.compare_floats(left, right):
                    self.add_finding(
                        iid,
                        dyn_ast,
                        "A-12",
                        f"compared floats nearly equal {left} and {right}",
                    )

            # Check if comparing incompatible types (e.g., comparing with type object)
            if self.compare_types(left, right):
                self.add_finding(iid, dyn_ast, "A-13", f"compared with type {left} and {right}")

            # Check if comparing function object with non-function (likely bug)
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
        # Check if value is a float (builtin Python or numpy type)
        return isinstance(f, float) or isinstance(f, np.floating)

    def check_nan(self, num: float) -> bool:
        # Check if number is NaN (works for both Python and numpy floats)
        # np.isnan handles python builtin floats and numpy floats
        return self._is_float(num) and np.isnan(num)

    def check_inf(self, num: float) -> bool:
        # Check if number is infinity (positive or negative)
        # np.isinf handles python builtin floats and numpy floats
        return self._is_float(num) and np.isinf(num)

    def compare_floats(self, left: float, right: float) -> bool:
        # Detect floats that are nearly equal (within 1e-8 relative tolerance)
        # This catches precision-related comparison bugs where == fails for nearly-equal values
        return (
            self._is_float(left) and self._is_float(right) and left != right and math.isclose(left, right, rel_tol=1e-8)
        )

    # Change this to analyse iff == returns false but is returns true -> flag issue
    # is compares ids, if they are the same == should return true as well
    def compare_diff_in_operator(self, left: Any, right: Any, op: Callable) -> bool:
        # Detect inconsistency between identity (is) and equality (==) operators
        if type(left) == bool or type(right) == bool:
            res = op(left, right)
            if op == operator.eq and (left is right) != res:
                return True
            elif op == operator.ne and (left is not right) != res:
                return True
        return False

    def in_type_mismatch(self, left: Any, right: Any) -> bool:
        # Detect potential "in" operator misuse with mismatched container types
        if (type(left) is list and type(right) is list) or (type(left) is set and type(right) is set):
            if len(left) == 1 and next(iter(left)) in right:
                return True
        return False

    """
    https://pylint.pycqa.org/en/latest/user_guide/messages/warning/comparison-with-callable.html
    """

    def compare_funct(self, left: Any, right: Any) -> bool:
        # Detect comparisons between function objects and non-function objects
        # This is usually a bug (forgot to call the function)
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
        # Detect comparison between different type objects (e.g., int == str is always False)
        left_is_type = isinstance(left, type)
        right_is_type = isinstance(right, type)

        if left_is_type and right_is_type and left != right:
            return True
        return False

    def compared_with_none(self, dyn_ast: str, iid: int, left: Any, right: Any) -> bool:
        # Detect == comparisons with None; recommend using 'is None' instead
        if isinstance(left, type(None)) or isinstance(right, type(None)):
            self.add_finding(
                iid,
                dyn_ast,
                "compare_with_none",
                f"compared {left} == {right}, use is operator",
            )
            return True
        return False

    def compared_with_itself(self, dyn_ast: str, iid: int, left: Any, right: Any) -> bool:
        # Flag useless comparisons where the same object is compared to itself
        if id(left) == id(right):
            self.add_finding(iid, dyn_ast, "compare_with_itself", f"compared {left} with itself")
            return True
        return False

    def compared_different_types(self, dyn_ast: str, iid: int, left: Any, right: Any, result: Any) -> bool:
        # Detect comparisons between fundamentally different types that return False
        # Ignore float/int comparisons since Python allows these
        if (isinstance(left, type(0)) and isinstance(right, type(0.0))) or (
            isinstance(left, type(0.0)) and isinstance(right, type(0))
        ):
            return False

        type_left = type(left)
        type_right = type(right)

        # Flag if result is False and types are incompatible (not instances of each other)
        # This catches cases like "some_list == some_dict" which is always False
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
        # Add statistics about total comparisons seen during analysis
        self.add_meta({"total_comp": self.nmb_comparisons})
        super().end_execution()
