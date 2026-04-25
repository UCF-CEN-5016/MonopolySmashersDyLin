# ============================== Define spec ==============================
"""
Module for RandomRandrange_MustNotUseKwargs functionality.
"""
from .base_analysis import BaseDyLinAnalysis
from dynapyt.instrument.filters import only

from typing import Callable, Tuple, Dict


"""
    Keyword arguments should not be used because they can be interpreted in unexpected ways
    source: https://docs.python.org/3/library/random.html#random.randrange
"""


class RandomRandrange_MustNotUseKwargs(BaseDyLinAnalysis):
    """
Randomrandrange mustnotusekwargs: logical component class.
"""

    def __init__(self, **kwargs) -> None:
        """
Init: implementation of the __init__ logic.

Key Variables:
    analysis_name: Local state member.

Returns:
    Standard result object.
"""
        super().__init__(**kwargs)
        self.analysis_name = "RandomRandrange_MustNotUseKwargs"

    @only(patterns=["randrange"])
    def pre_call(
        self, dyn_ast: str, iid: int, function: Callable, pos_args: Tuple, kw_args: Dict
    ) -> None:
        """
Pre call: implementation of the pre_call logic.

Args:
    dyn_ast: Dynamic AST tree.
    iid: Instruction identifier.
    function: Operational parameter.
    pos_args: Positional logic arguments.
    kw_args: Keyword logic arguments.

Key Variables:
    class_name: Local state member.
    targets: Local state member.

Returns:
    Standard result object.
"""
        # The target class names for monitoring
        targets = ["random"]

        # Get the class name
        if hasattr(function, '__module__'):
            class_name = function.__module__
        else:
            class_name = None

        # Check if the class name is the target ones
        if class_name in targets:

            # Spec content
            if kw_args:
                # Spec content
                self.add_finding(
                    iid,
                    dyn_ast,
                    "B-13",
                    f"Keyword arguments should not be used in random.randrange because they can be interpreted in unexpected ways at {dyn_ast}."
                )
# =========================================================================
