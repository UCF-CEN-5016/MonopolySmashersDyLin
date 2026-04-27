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
    # Analysis to detect unnecessary sorted() calls where list.sort() (in-place) could be used
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.analysis_name = "InPlaceSortAnalysis"
        # Track lists passed to sorted() for deferred analysis
        self.stored_lists = {}
        # Only flag sorted() calls on lists longer than this (avoid flagging small lists)
        self.threshold = 1000

    @only(patterns=["sorted"])
    def pre_call(self, dyn_ast: str, iid: int, function: Callable, pos_args, kw_args) -> Any:
        # Hook called before sorted() is executed; record if the list result is never used
        # print(f"{self.analysis_name} pre_call {iid}")
        if function is sorted:
            # Check if list is sortable in-place (has sort() method) and exceeds threshold
            # we have to keep the list in memory to keep id(pos_args[0]) stable ? nope!
            if self.is_sortable_inplace(pos_args[0]) and len(pos_args[0]) > self.threshold:
                # Store reference to track if this list is ever used after sorted() call
                self.stored_lists[id(pos_args[0])] = {
                    "iid": iid,
                    "file_name": dyn_ast,
                    "len": len(pos_args[0]),
                }

    def read_identifier(self, dyn_ast: str, iid: int, val: Any) -> Any:
        # Hook called when a variable is read; if it matches a stored list, remove from tracking
        # print(f"{self.analysis_name} read id {iid} {dyn_ast}")
        if len(self.stored_lists) > 0 and self.is_sortable_inplace(val):
            # List was read/used, so sorted() result must be used; remove from flagged lists
            self.stored_lists.pop(id(val), None)
        return None

    def is_sortable_inplace(self, obj):
        # Check if object supports in-place sorting (has sort() method and __len__)
        return hasattr(obj, "sort") and hasattr(obj, "__len__")

    def end_execution(self) -> None:
        # Flag all sorted() calls whose results were never used; in-place sort would be more efficient
        for _, l in self.stored_lists.items():
            self.add_finding(
                l["iid"],
                l["file_name"],
                "A-09",
                f"unnessecary use of sorted(), len:{l['len']} in {l['file_name']}",
            )
        super().end_execution()
