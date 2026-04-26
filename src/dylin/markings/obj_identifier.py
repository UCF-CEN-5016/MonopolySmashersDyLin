from typing import Optional
import weakref
from collections import defaultdict
from uuid import UUID, uuid4

class HeapMirror():
    # Central registry for mapping Python objects to stable UUIDs across execution
    # Uses 3-tier fallback strategy for object tracking since Python's id() is not stable
    
    def __init__(self):
        # Enable weak reference tracking (preferred for garbage collection awareness)
        self.activate_weak = True
        # Tier 1: Weak references for objects that support them (dicts, lists, custom classes)
        self.mirrored_objects = {}
        # Tier 2: Hash-based fallback for hashable immutables (when weakref unavailable)
        self.hashable_fallback = defaultdict(uuid4)
        # Tier 3: ID-based fallback for unhashable objects like tuples/ints (last resort)
        self.id_fallback = defaultdict(uuid4)
        # Callbacks to invoke when objects are garbage collected (for cleanup)
        self.clean_callbacks = []

    def add_clean_callback(self, func):
        # Register callback to be invoked when mirrored objects are garbage collected
        self.clean_callbacks.append(func)

    def _clean(self, internal_key):
        # Invoke all registered callbacks passing the UUID of the object being collected
        for callback in self.clean_callbacks:
            callback(self.mirrored_objects[internal_key]["uuid"].int)
        # Remove object from mirror after cleanup
        del self.mirrored_objects[internal_key]

    def contains(self, obj: any):
        # Check if object already has a UUID and return it; uses 3-tier lookup
        # Tier 1: Check weak reference dictionary first
        if id(obj) in self.mirrored_objects:
            return self.mirrored_objects[id(obj)]["uuid"]
        try:
            # Tier 2: Try to use object hash if weakref not available
            h = object.__hash__(obj)
            res = self.hashable_fallback.get(h)
            if res is None:
                raise Exception()
            return res
        except Exception:
            # Tier 3: Fall back to id-based lookup (least preferred)
            if id(obj) in self.id_fallback:
                return self.id_fallback[id(obj)]
        return None

    def get_ref(self, uuid) -> Optional[weakref.ReferenceType]:
        # Retrieve weak reference for an object UUID (expensive O(n) scan, use sparingly)
        # Note: Only works for Tier 1 (mirrored) objects, not fallback tiers
        # Use with caution as this scans all mirrored objects
        
        for _id in self.mirrored_objects:
            mirrored = self.mirrored_objects[_id]
            if mirrored["uuid"].int == uuid:
                return mirrored["ref"]
        return None

    def getId(self, obj: any) -> Optional[str]:
        # Generate or retrieve stable UUID for any object using 3-tier fallback strategy
        if self.activate_weak:
            try:
                # Tier 1: Try weak reference (preferred - objects auto-removed when garbage collected)
                # Check if object supports weakref (has __weakrefoffset__)
                if type(obj).__weakrefoffset__ == 0:
                    raise TypeError()

                # Tier 1: Weakref works - create reference with finalization callback
                actual_key = id(obj)
                if not actual_key in self.mirrored_objects:
                    # Create weak reference that triggers _clean callback when object is GC'd
                    reference = weakref.ref(obj)
                    weakref.finalize(obj, self._clean, actual_key)
                    val = {"ref": reference, "uuid": uuid4()}
                    self.mirrored_objects[actual_key] = val

                return self.mirrored_objects[actual_key]["uuid"]
            except TypeError:
                pass
            try:
                # Tier 2: Object doesn't support weakref, try hashing
                # Note: Hash collision risk exists but acceptable since equal objects should have same UUID
                # Per Python docs: objects that compare equal MUST have same hash
                # If two different objects have same hash, they get same UUID (acceptable tradeoff)
                
                # Workaround: prevent infinite loop if __hash__ is overwritten and calls hash()
                h = object.__hash__(obj)
                res = self.hashable_fallback[h]

                return res
            except TypeError:
                pass

        # Tier 3: Neither weakref nor hash available (e.g., mutable types like unhashable tuples)
        # Use id as last resort (stable only within current execution)
        res = self.id_fallback[id(obj)]
        return res

    def cleanup_fallbacks(self):
        # Clear fallback dictionaries (used at function exit to prevent stale entries)
        if self.activate_weak:
            self.id_fallback = defaultdict(uuid4)
            self.hashable_fallback = defaultdict(uuid4)


# Global singleton instance for object tracking across entire DyLin execution
uniqueidmap = HeapMirror()


def wrap(any):
    # Dynamically add __weakref__ support to objects that don't have it (e.g., classes with __slots__)
    # Throws TypeError for objects that can never support weakref (int, tuple, etc.)
    # This allows us to track more object types than would otherwise be possible
    try:
        base = any.__class__
        slots = ()
        try:
            slots = base.__slots__
        except Exception:
            slots = ()
        # Add __weakref__ to slots to enable weak reference support
        slots += ("__weakref__",)

        class ExtraSlots(base):
            __slots__ = slots
        ExtraSlots.__name__ = base.__name__

        return ExtraSlots(any)
    except Exception as e:
        print(e)
        return None


def has_obj(obj) -> Optional[str]:
    # Check if object is already mirrored; returns UUID if found, None otherwise
    return uniqueidmap.contains(obj)


def save_uid(obj) -> Optional[str]:
    # Get UUID for object; if not previously mirrored, generate new one
    # Returns a new unmirrored UUID if object has no tracking entry
    x = uniqueidmap.contains(obj)
    if x is None:
        return uuid4().int
    return x.int


def uniqueid(obj) -> Optional[str]:
    # Generate persistent UUID for any object within current execution
    # Returns None for None input or if object cannot be tracked
    if obj is None:
        return None
    res = uniqueidmap.getId(obj)
    if res is None:
        return None
    return res.int


def get_ref(uuid) -> Optional[weakref.ReferenceType]:
    # Retrieve weak reference for an object by UUID (expensive operation)
    if uuid is None:
        return None
    return uniqueidmap.get_ref(uuid)


def add_cleanup_hook(func):
    # Register callback to be invoked when mirrored objects are garbage collected
    # Callback receives object UUID as parameter for cleanup tracking
    uniqueidmap.add_clean_callback(func)


def cleanup():
    # Clear fallback dictionaries at function/execution boundaries
    # Prevents stale object references from accumulating across invocations
    uniqueidmap.cleanup_fallbacks()
