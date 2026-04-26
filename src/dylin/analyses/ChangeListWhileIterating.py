from typing import Any, Iterable, Iterator, List, Optional
from .base_analysis import BaseDyLinAnalysis
import collections


class ChangeListWhileIterating(BaseDyLinAnalysis):
    # Analysis to detect modifications to list during iteration, which can skip/repeat elements
    # PyLint checks for this: W4701 for lists, E4702 (dicts), E4703 (sets)
    
    class ListMeta:
        # Helper class to track state of lists being iterated over
        def __init__(self, l: Iterable, it: Iterator, length: int, dyn_ast: str, iid: int, warned: bool = False):
            self.l = l  # Reference to the list being iterated
            self.it = it  # Iterator object
            self.length = length  # Original list length at iteration start
            self.warned = warned  # Flag to warn only once per list
            self.dyn_ast = dyn_ast  # Source code location
            self.iid = iid  # Instruction ID

    def __init__(self, **kwargs):
        super(ChangeListWhileIterating, self).__init__(**kwargs)
        self.analysis_name = "ChangeListWhileIterating"
        # Stack of ListMeta objects for nested for loops
        self.iterator_stack: List[self.ListMeta] = []

    def enter_for(self, dyn_ast: str, iid: int, next_value: Any, iterable: Iterable, iterator: Iterator) -> Optional[Any]:
        # Hook called when entering a for loop; track list size for change detection
        # print(f"{self.analysis_name} enter_for {iid}")
        # Skip tracking dict iterators and abstract iterators (can't get len())
        if isinstance(iterable, collections.abc.Iterator) or isinstance(iterable, type({})):
            return

        _list = iterable
        try:
            # Check if this is a new for loop iteration or nested loop
            if (
                len(self.iterator_stack) == 0
                or iid != self.iterator_stack[-1].iid
                or dyn_ast != self.iterator_stack[-1].dyn_ast
                or iterator != self.iterator_stack[-1].it
            ):
                # New loop: record initial list length
                length = len(_list)
                self.iterator_stack.append(self.ListMeta(_list, iterator, length, dyn_ast, iid))
            elif len(self.iterator_stack) > 0:
                # Existing loop: check if list size changed
                list_meta: self.ListMeta = self.iterator_stack[-1]
                if (
                    list_meta.warned is False
                    and len(_list) < list_meta.length
                    and id(_list) == id(list_meta.l)
                    and iterable == list_meta.l
                    and iterator == list_meta.it
                ):
                    # List shortened during iteration: elements were removed
                    self.add_finding(
                        iid,
                        dyn_ast,
                        "A-22",
                        f"List length changed while iterating initial length: {list_meta.length} current:{len(_list)}",
                    )
                    # Only warn once per iteration to avoid duplicate reports
                    list_meta.warned = True
        # Necessary for dynamically loaded lists during runtime which sometimes can not be compared in certain test cases
        except Exception as e:
            print(e)

    def exit_for(self, dyn_ast, iid):
        # Hook called when exiting a for loop; remove from tracking stack
        # print(f"{self.analysis_name} exit_for {iid}")
        if len(self.iterator_stack) > 0:
            self.iterator_stack.pop()
