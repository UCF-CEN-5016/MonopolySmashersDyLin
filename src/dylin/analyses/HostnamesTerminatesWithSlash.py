# ============================== Define spec ==============================
"""
Module for HostnamesTerminatesWithSlash functionality.
"""
from .base_analysis import BaseDyLinAnalysis
from dynapyt.instrument.filters import only

from typing import Callable, Tuple, Dict


"""
    It is recommended to terminate full hostnames with a /.
"""


class HostnamesTerminatesWithSlash(BaseDyLinAnalysis):
    """
Hostnamesterminateswithslash: logical component class.
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
        self.analysis_name = "HostnamesTerminatesWithSlash"

    @only(patterns=["mount"])
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
    cls: Local state member.
    targets: Local state member.
    url: Local state member.

Returns:
    Standard result object.
"""
        # The target class names for monitoring
        targets = ["requests.sessions.Session"]

        # Get the class name
        if hasattr(function, '__self__') and hasattr(function.__self__, '__class__'):
            cls = function.__self__.__class__
            class_name = cls.__module__ + "." + cls.__name__
        else:
            class_name = None

        # Check if the class name is the target ones
        if class_name in targets:

            # Spec content
            url = pos_args[0]  # Updated to use the first argument as self is not considered here
            if not url.endswith('/'):

                # Spec content
                self.add_finding(
                    iid,
                    dyn_ast,
                    "B-6",
                    f"The call to method mount in file at {dyn_ast} does not terminate the hostname with a /."
                )
# =========================================================================
