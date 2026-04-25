"""
Module for InPlaceSortAnalysis functionality.
"""
import traceback
from .base_analysis import BaseDyLinAnalysis
from typing import Any, Callable, Dict, Tuple
from dynapyt.instrument.filters import only

"""
Name: 
UseInplaceSorting

Source:
-

Test description:
Inplace sorting is much faster if a copy is not needed

Why useful in a dynamic analysis approach:
No corresponding static analysis found and we can check if for some runs the
reference to the unsorted list is not needed, indicating for some cases it might be 
useful to skip the sorted() method and do in place sorting.

Discussion:


"""


class InPlaceSortAnalysis(BaseDyLinAnalysis):
    """
Inplacesortanalysis: logical component class.
"""
    def __init__(self, **kwargs):
        """
Init: implementation of the __init__ logic.

Key Variables:
    analysis_name: Local state member.
    stored_lists: Local state member.
    threshold: Local state member.
"""
        super().__init__(**kwargs)
        self.analysis_name = "InPlaceSortAnalysis"
        self.stored_lists = {}
        self.threshold = 1000

    @only(patterns=["sorted"])
    def pre_call(self, dyn_ast: str, iid: int, function: Callable, pos_args, kw_args) -> Any:
        """
Pre call: implementation of the pre_call logic.

Args:
    dyn_ast: Dynamic AST tree.
    iid: Instruction identifier.
    function: Operational parameter.
    pos_args: Positional logic arguments.
    kw_args: Keyword logic arguments.

Returns:
    Standard result object.
"""
        # print(f"{self.analysis_name} pre_call {iid}")
        if function is sorted:
            # we have to keep the list in memory to keep id(pos_args[0]) stable ? nope!
            if self.is_sortable_inplace(pos_args[0]) and len(pos_args[0]) > self.threshold:
                self.stored_lists[id(pos_args[0])] = {
                    "iid": iid,
                    "file_name": dyn_ast,
                    "len": len(pos_args[0]),
                }

    def read_identifier(self, dyn_ast: str, iid: int, val: Any) -> Any:
        """
Read identifier: implementation of the read_identifier logic.

Args:
    dyn_ast: Dynamic AST tree.
    iid: Instruction identifier.
    val: Operational parameter.

Returns:
    Standard result object.
"""
        # print(f"{self.analysis_name} read id {iid} {dyn_ast}")
        if len(self.stored_lists) > 0 and self.is_sortable_inplace(val):
            self.stored_lists.pop(id(val), None)
        return None

    def is_sortable_inplace(self, obj):
        """
Is sortable inplace: implementation of the is_sortable_inplace logic.

Args:
    obj: Operational parameter.

Returns:
    Standard result object.
"""
        return hasattr(obj, "sort") and hasattr(obj, "__len__")

    def end_execution(self) -> None:
        """
End execution: implementation of the end_execution logic.

Loop Behavior:
    Iterates through self.stored_lists.items().

Returns:
    Standard result object.
"""
        for _, l in self.stored_lists.items():
            self.add_finding(
                l["iid"],
                l["file_name"],
                "A-09",
                f"unnessecary use of sorted(), len:{l['len']} in {l['file_name']}",
            )
        super().end_execution()
