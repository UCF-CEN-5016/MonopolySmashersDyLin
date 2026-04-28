# ============================== Define spec ==============================
from .base_analysis import BaseDyLinAnalysis
from dynapyt.instrument.filters import only

from typing import Callable, Tuple, Dict


"""
    Keyword arguments should not be used because they can be interpreted in unexpected ways
    source: https://docs.python.org/3/library/random.html#random.randrange
"""


class RandomRandrange_MustNotUseKwargs(BaseDyLinAnalysis):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.analysis_name = "RandomRandrange_MustNotUseKwargs"

    @only(patterns=["randrange"])
    def pre_call(
        self, dyn_ast: str, iid: int, function: Callable, pos_args: Tuple, kw_args: Dict
    ) -> None:
        # Restrict rule to stdlib random module functions
        targets = ["random"]

        # Resolve module name of called function
        if hasattr(function, '__module__'):
            class_name = function.__module__
        else:
            class_name = None

        # Analyze only random.randrange calls
        if class_name in targets:

            # Keyword args for randrange can be ambiguous and are discouraged by docs
            if kw_args:
                self.add_finding(
                    iid,
                    dyn_ast,
                    "B-13",
                    f"Keyword arguments should not be used in random.randrange because they can be interpreted in unexpected ways at {dyn_ast}."
                )
# =========================================================================
