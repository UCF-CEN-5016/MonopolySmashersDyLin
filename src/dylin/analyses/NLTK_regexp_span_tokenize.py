# ============================== Define spec ==============================
"""
Module for NLTK_regexp_span_tokenize functionality.
"""
from .base_analysis import BaseDyLinAnalysis
from dynapyt.instrument.filters import only

from typing import Callable, Tuple, Dict


"""
    Regular expression passed to regexp_span_tokenize must not be empty
    src: https://www.nltk.org/api/nltk.tokenize.util.html
"""


class NLTK_regexp_span_tokenize(BaseDyLinAnalysis):
    """
Nltk regexp span tokenize: logical component class.
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
        self.analysis_name = "NLTK_regexp_span_tokenize"

    @only(patterns=["regexp_span_tokenize"])
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
    regexp: Local state member.
    targets: Local state member.

Returns:
    Standard result object.
"""
        # The target class names for monitoring
        targets = ["nltk.tokenize.util"]

        # Get the class name
        if hasattr(function, '__module__'):
            class_name = function.__module__
        else:
            class_name = None

        # Check if the class name is the target ones
        if class_name in targets:

            # Spec content
            regexp = None
            if kw_args.get('regexp'):
                regexp = kw_args['regexp']
            elif len(pos_args) > 1:
                regexp = pos_args[1]

            # Check if the regular expression is empty
            if regexp == '':

                # Spec content
                self.add_finding(
                    iid,
                    dyn_ast,
                    "B-8",
                    f"Regular expression must not be empty at {dyn_ast}."
                )
# =========================================================================
