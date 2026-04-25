# ============================== Define spec ==============================
"""
Module for Requests_DataMustOpenInBinary functionality.
"""
from .base_analysis import BaseDyLinAnalysis
from dynapyt.instrument.filters import only

from typing import Callable, Tuple, Dict


"""
    It is strongly recommended that you open files in binary mode. This is because Requests may attempt to provide
    the Content-Length header for you, and if it does this value will be set to the number of bytes in the file.
    Errors may occur if you open the file in text mode.
"""


class Requests_DataMustOpenInBinary(BaseDyLinAnalysis):
    """
Requests datamustopeninbinary: logical component class.
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
        self.analysis_name = "Requests_DataMustOpenInBinary"

    @only(patterns=["post"])
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
    data: Local state member.
    kwords: Local state member.
    targets: Local state member.

Loop Behavior:
    Iterates through kwords.

Returns:
    Standard result object.
"""
        # The target class names for monitoring
        targets = ["requests.api"]

        # Get the class name
        if hasattr(function, '__module__'):
            class_name = function.__module__
        else:
            class_name = None

        # Check if the class name is the target ones
        if class_name in targets:

            # Check if the data is a file
            kwords = ['data', 'files']
            for k in kwords:
                if k in kw_args:
                    data = kw_args[k]
                    if hasattr(data, 'read') and hasattr(data, 'mode') and 'b' not in data.mode:

                        # Spec content
                        self.add_finding(
                            iid,
                            dyn_ast,
                            "B-14",
                            f"It is strongly recommended that you open files in binary mode at {dyn_ast}. "
                            f"This is because Requests may attempt to provide the Content-Length header for you, "
                            f"and if it does this value will be set to the number of bytes in the file. "
                            f"Errors may occur if you open the file in text mode."
                        )
# =========================================================================
