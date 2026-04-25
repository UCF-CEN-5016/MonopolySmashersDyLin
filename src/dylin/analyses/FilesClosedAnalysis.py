"""
Module for FilesClosedAnalysis functionality.
"""
import builtins
from typing import Any, Callable, Dict, Tuple
from .base_analysis import BaseDyLinAnalysis
from dynapyt.instrument.filters import only

"""
Name: 
EnsureFilesClosed

Source:
-

Test description:
Ensures that every file created with `open('filename')` is closed before termination.
Recommended usage is using `with`.
Even though CPython uses reference counting which will close the file other python interpreters like
IronPython, PyPy, and Jython do not use reference counting.  

Why useful in a dynamic analysis approach:
Non trivial control flows can not be analysed properly by static analysis and thus miss a correct / missing close operation

Discussion:


"""


class FilesClosedAnalysis(BaseDyLinAnalysis):
    """
Filesclosedanalysis: logical component class.
"""
    def __init__(self, **kwargs):
        """
Init: implementation of the __init__ logic.

Key Variables:
    analysis_name: Local state member.
    files: Local state member.
"""
        super().__init__(**kwargs)
        self.analysis_name = "FilesClosedAnalysis"
        self.files = {}

    @only(patterns=["open"])
    def post_call(
        self,
        dyn_ast: str,
        iid: int,
        res: Any,
        function: Callable,
        pos_args: Tuple,
        kw_args: Dict,
    ) -> Any:
        """
Post call: implementation of the post_call logic.

Args:
    dyn_ast: Dynamic AST tree.
    iid: Instruction identifier.
    res: Operational parameter.
    function: Operational parameter.
    pos_args: Positional logic arguments.
    kw_args: Keyword logic arguments.

Returns:
    Standard result object.
"""
        if function == builtins.open:
            if id(res) not in self.files:
                # id works here because we keep file into memory
                # could be optimized to use obj mirror though
                self.files[id(res)] = (iid, res, dyn_ast)

    def end_execution(self) -> None:
        """
End execution: implementation of the end_execution logic.

Loop Behavior:
    Iterates through self.files.

Returns:
    Standard result object.
"""
        for id in self.files:
            try:
                if not self.files[id][1].closed:
                    self.add_finding(
                        self.files[id][0],
                        self.files[id][2],
                        "A-08",
                        f"File {self.files[id][1].name} was not closed, opened in {self.files[id][2]} iid {self.files[id][0]}",
                    )
            except AttributeError:
                pass
        super().end_execution()
