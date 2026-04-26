from .base_analysis import BaseDyLinAnalysis


class ItemInListAnalysis(BaseDyLinAnalysis):
    # Analysis to detect inefficient linear searches in large lists (should use sets instead)
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.analysis_name = "ItemInListAnalysis"
        # Only flag lists larger than this threshold
        self.threshold = 100
        # Multiply threshold by this to flag when accumulative search cost is high
        self.count = 5
        # Track cumulative size of lists being searched via "in" operator
        self.size_map = {}

    def _in(self, dyn_ast, iid, left, right, result):
        # Hook called after "in" operator; checks if searching large list repeatedly
        # print(f"{self.analysis_name} in {iid}")
        if type(right) == list and len(right) > self.threshold:
            # Use list object ID as key to track searches on same list
            uid = id(right)
            if uid not in self.size_map:
                # First time seeing this list: record its size
                self.size_map[uid] = len(right)
            else:
                # Accumulate total search cost (list length) across all searches
                self.size_map[uid] += len(right)
            # Flag if cumulative search cost exceeds threshold (likely performance issue)
            if self.size_map[uid] > self.threshold * self.count:
                self.add_finding(
                    iid,
                    dyn_ast,
                    "PC-05",
                    f"Searching for an item ({left}) in a long list (length {len(right)}) is not efficient (done for {self.size_map[uid]}). Consider using a set.",
                )

    def not_in(self, dyn_ast, iid, left, right, result):
        # Hook called after "not in" operator; same logic as "in"
        self._in(dyn_ast, iid, left, right, result)
