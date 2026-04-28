# ============================== Define spec ==============================
from .base_analysis import BaseDyLinAnalysis
from dynapyt.instrument.filters import only

from typing import Callable, Tuple, Dict


"""
    It is strongly recommended that you open files in binary mode. This is because Requests may attempt to provide
    the Content-Length header for you, and if it does this value will be set to the number of bytes in the file.
    Errors may occur if you open the file in text mode.
"""


class Requests_DataMustOpenInBinary(BaseDyLinAnalysis):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.analysis_name = "Requests_DataMustOpenInBinary"

    @only(patterns=["post"])
    def pre_call(
        self, dyn_ast: str, iid: int, function: Callable, pos_args: Tuple, kw_args: Dict
    ) -> None:
        # Restrict check to requests.post API implementation
        targets = ["requests.api"]

        # Resolve function module for API filtering
        if hasattr(function, '__module__'):
            class_name = function.__module__
        else:
            class_name = None

        # Analyze only targeted requests call sites
        if class_name in targets:

            # Inspect common upload kwargs that may hold file-like objects
            kwords = ['data', 'files']
            for k in kwords:
                if k in kw_args:
                    data = kw_args[k]
                    # Text-mode handles can misreport content length and break uploads
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
