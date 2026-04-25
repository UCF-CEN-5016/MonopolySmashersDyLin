"""
Module for ItemInListAnalysis functionality.
"""
from .base_analysis import BaseDyLinAnalysis


class ItemInListAnalysis(BaseDyLinAnalysis):
    """
Iteminlistanalysis: logical component class.
"""
    def __init__(self, **kwargs) -> None:
        """
Init: implementation of the __init__ logic.

Key Variables:
    analysis_name: Local state member.
    count: Local state member.
    size_map: Local state member.
    threshold: Local state member.

Returns:
    Standard result object.
"""
        super().__init__(**kwargs)
        self.analysis_name = "ItemInListAnalysis"
        self.threshold = 100
        self.count = 5
        self.size_map = {}

    def _in(self, dyn_ast, iid, left, right, result):
        """
In: implementation of the _in logic.

Args:
    dyn_ast: Dynamic AST tree.
    iid: Instruction identifier.
    left: Operational parameter.
    right: Operational parameter.
    result: Operational parameter.

Key Variables:
    uid: Local state member.
"""
        # print(f"{self.analysis_name} in {iid}")
        if type(right) == list and len(right) > self.threshold:
            uid = id(right)
            if uid not in self.size_map:
                self.size_map[uid] = len(right)
            else:
                self.size_map[uid] += len(right)
            if self.size_map[uid] > self.threshold * self.count:
                self.add_finding(
                    iid,
                    dyn_ast,
                    "PC-05",
                    f"Searching for an item ({left}) in a long list (length {len(right)}) is not efficient (done for {self.size_map[uid]}). Consider using a set.",
                )

    def not_in(self, dyn_ast, iid, left, right, result):
        """
Not in: implementation of the not_in logic.

Args:
    dyn_ast: Dynamic AST tree.
    iid: Instruction identifier.
    left: Operational parameter.
    right: Operational parameter.
    result: Operational parameter.
"""
        self._in(dyn_ast, iid, left, right, result)
