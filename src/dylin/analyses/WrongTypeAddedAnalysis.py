import types
from .base_analysis import BaseDyLinAnalysis
from dynapyt.instrument.filters import only
from typing import Any, Callable, Tuple, Dict
import random

# Analysis to detect type inconsistencies when adding elements to homogeneous containers
# If a list/set contains only one type but suddenly a different type is added,
# this likely indicates a bug or logic error


function_names = ["append", "extend", "insert", "add"]


class WrongTypeAddedAnalysis(BaseDyLinAnalysis):
    # Detects when elements of unexpected type are added to homogeneous containers
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Track statistics about type mismatches found
        self.nmb_add = 0
        self.nmb_add_assign = 0
        self.nmb_functions = 0
        self.analysis_name = "WrongTypeAddedAnalysis"
        # Only analyze lists/sets with at least this many elements
        self.threshold = 10

    @only(patterns=function_names)
    def pre_call(self, dyn_ast: str, iid: int, function: Callable, pos_args, kw_args):
        # Hook called before append/extend/insert/add methods on lists/sets
        # print(f"{self.analysis_name} pre_call {iid}")
        if isinstance(function, types.BuiltinFunctionType) and function.__name__ in function_names:
            # Get the container (list/set) that method is being called on
            list_or_set = function.__self__

            # Skip if list/set too small to have meaningful type homogeneity
            if not "__len__" in dir(list_or_set) or len(list_or_set) <= self.threshold:
                return
            self.nmb_functions += 1

            # Pick random sample of container to check type (reduces overhead for large containers)
            type_to_check = type(random.choice(list(list_or_set)))

            # Sample container to test homogeneity (smaller sample for large lists)
            list_or_set = random.sample(list(list_or_set), self.threshold)
            same_type = all(isinstance(n, type_to_check) for n in list_or_set)

            if same_type:
                # Container is homogeneous; check if new element matches
                type_ok = True
                if function.__name__ in ["append", "add"]:
                    # For append/add, check single element being added
                    type_ok = isinstance(pos_args[0], type_to_check)
                    if not type_ok:
                        odd_type = type(pos_args[0])
                elif function.__name__ == "extend":
                    # For extend, check all elements being added
                    sample = pos_args[0]
                    if "__len__" in dir(sample) and len(sample) >= self.threshold:
                        sample = random.sample(list(pos_args[0]), self.threshold)
                    type_ok = all(isinstance(n, type_to_check) for n in sample)
                    if not type_ok:
                        odd_type = [type(n) for n in sample]
                elif function.__name__ == "insert":
                    # For insert, check element being inserted at index
                    type_ok = isinstance(pos_args[1], type_to_check)
                    if not type_ok:
                        odd_type = type(pos_args[1])

                # Report type mismatch if found
                if not type_ok:
                    self.add_finding(
                        iid,
                        dyn_ast,
                        "A-11",
                        f"added potentially wrong type {odd_type} to list of type {type_to_check} in {dyn_ast}",
                    )

    def add_assign(self, dyn_ast: str, iid: int, left: Any, right: Any) -> Any:
        # for some reason left is a lambda
        # print(f"{self.analysis_name} += {iid}")
        self.add(dyn_ast, iid, left(), right)

    def add(self, dyn_ast: str, iid: int, left: Any, right: Any, result: Any = None) -> Any:
        # print(f"{self.analysis_name} + {iid}")
        if isinstance(left, list):
            if len(left) <= self.threshold:
                return

            self.nmb_add += 1

            type_to_check = type(right)
            if type_to_check == list and len(right) > 0:
                type_to_check = type(right[0])
            else:
                return
            one_type = type(random.choice(left))
            random_subset = random.sample(left, self.threshold)
            homogeneous = all(isinstance(n, one_type) for n in random_subset)
            same_type = all(isinstance(n, type_to_check) for n in random_subset)

            # before addition types where the same, if not after addition we may have a problem
            if homogeneous and not same_type:
                self.add_finding(
                    iid,
                    dyn_ast,
                    "A-11",
                    f"add potentially wrong type {type_to_check} to a list of types {one_type}",
                )

    def end_execution(self) -> None:
        self.add_meta(
            {
                "add": self.nmb_add,
                "add_assign": self.nmb_add_assign,
                "nmb_interesing_functions": self.nmb_functions,
            }
        )
        super().end_execution()
