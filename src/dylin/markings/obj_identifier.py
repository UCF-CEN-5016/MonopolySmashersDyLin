"""
Module for obj_identifier functionality.
"""
from typing import Optional
import weakref
from collections import defaultdict
from uuid import UUID, uuid4

class HeapMirror():
    """
Heapmirror: logical component class.
"""
    def __init__(self):
        """
Init: implementation of the __init__ logic.

Key Variables:
    activate_weak: Local state member.
    clean_callbacks: Local state member.
    hashable_fallback: Local state member.
    id_fallback: Local state member.
    mirrored_objects: Local state member.
"""
        self.activate_weak = True
        self.mirrored_objects = {}
        self.hashable_fallback = defaultdict(uuid4)
        self.id_fallback = defaultdict(uuid4)
        self.clean_callbacks = []

    def add_clean_callback(self, func):
        """
Add clean callback: implementation of the add_clean_callback logic.

Args:
    func: Operational parameter.
"""
        self.clean_callbacks.append(func)

    def _clean(self, internal_key):
        """
Clean: implementation of the _clean logic.

Args:
    internal_key: Operational parameter.

Loop Behavior:
    Iterates through self.clean_callbacks.
"""
        for callback in self.clean_callbacks:
            callback(self.mirrored_objects[internal_key]["uuid"].int)
        del self.mirrored_objects[internal_key]

    def contains(self, obj: any):
        """
Contains: implementation of the contains logic.

Args:
    obj: Operational parameter.

Key Variables:
    h: Local state member.
    res: Local state member.

Returns:
    Standard result object.
"""
        if id(obj) in self.mirrored_objects:
            return self.mirrored_objects[id(obj)]["uuid"]
        try:
            h = object.__hash__(obj)
            res = self.hashable_fallback.get(h)
            if res is None:
                raise Exception()
            return res
        except Exception:
            if id(obj) in self.id_fallback:
                return self.id_fallback[id(obj)]
        return None

    def get_ref(self, uuid) -> Optional[weakref.ReferenceType]:
        """
Get ref: implementation of the get_ref logic.

Args:
    uuid: Operational parameter.

Key Variables:
    mirrored: Local state member.

Loop Behavior:
    Iterates through self.mirrored_objects.

Returns:
    Standard result object.
"""

        for _id in self.mirrored_objects:
            mirrored = self.mirrored_objects[_id]
            if mirrored["uuid"].int == uuid:
                return mirrored["ref"]
        return None

    def getId(self, obj: any) -> Optional[str]:
        """
Getid: implementation of the getId logic.

Args:
    obj: Operational parameter.

Key Variables:
    actual_key: Local state member.
    h: Local state member.
    reference: Local state member.
    res: Local state member.
    val: Local state member.

Returns:
    Standard result object.
"""
        if self.activate_weak:
            try:
                # weakref is always preferred, because freed objects
                # are automatically removed

                # checks if weakreference possible
                if type(obj).__weakrefoffset__ == 0:
                    raise TypeError()

                # case 1: weakref works
                actual_key = id(obj)
                if not actual_key in self.mirrored_objects:
                    reference = weakref.ref(obj)
                    weakref.finalize(obj, self._clean, actual_key)
                    val = {"ref": reference, "uuid": uuid4()}
                    self.mirrored_objects[actual_key] = val

                return self.mirrored_objects[actual_key]["uuid"]
            except TypeError:
                pass
            try:
                # Note: hash does not actually give a unique
                # value for each object, from python __hash__ docs:
                # "The only required property is that objects which
                # compare equal have the same hash value".
                # We assume that __hash__ is implemented properly
                # and if two different objects have the same hash
                # value its acceptable that they have the same labels
                # given their equality

                # consider gc callback to remove unused keys before
                # gc run

                # case 2: no weakref possible, but hashable

                # workaround to prevent infinite loop if __hash__ is
                # overwritten and calles hash() again
                h = object.__hash__(obj)
                res = self.hashable_fallback[h]

                return res
            except TypeError:
                pass

        # case 3: neither hashable nor weakref possible
        # -> use id as last resort
        res = self.id_fallback[id(obj)]
        return res

    def cleanup_fallbacks(self):
        """
Cleanup fallbacks: implementation of the cleanup_fallbacks logic.

Key Variables:
    hashable_fallback: Local state member.
    id_fallback: Local state member.
"""
        if self.activate_weak:
            self.id_fallback = defaultdict(uuid4)
            self.hashable_fallback = defaultdict(uuid4)


uniqueidmap = HeapMirror()


def wrap(any):
    """
Wrap: implementation of the wrap logic.

Args:
    any: Operational parameter.

Key Variables:
    __name__: Local state member.
    __slots__: Local state member.
    base: Local state member.
    slots: Local state member.

Returns:
    Standard result object.
"""
    try:
        base = any.__class__
        slots = ()
        try:
            slots = base.__slots__
        except Exception:
            slots = ()
        slots += ("__weakref__",)

        class ExtraSlots(base):
            """
Extraslots: logical component class.
"""
            __slots__ = slots
        ExtraSlots.__name__ = base.__name__

        return ExtraSlots(any)
    except Exception as e:
        print(e)
        return None


def has_obj(obj) -> Optional[str]:
    """
Has obj: implementation of the has_obj logic.

Args:
    obj: Operational parameter.

Returns:
    Standard result object.
"""
    return uniqueidmap.contains(obj)


def save_uid(obj) -> Optional[str]:
    """
Save uid: implementation of the save_uid logic.

Args:
    obj: Operational parameter.

Key Variables:
    x: Local state member.

Returns:
    Standard result object.
"""
    x = uniqueidmap.contains(obj)
    if x is None:
        return uuid4().int
    return x.int


def uniqueid(obj) -> Optional[str]:
    """
Uniqueid: implementation of the uniqueid logic.

Args:
    obj: Operational parameter.

Key Variables:
    res: Local state member.

Returns:
    Standard result object.
"""
    if obj is None:
        return None
    res = uniqueidmap.getId(obj)
    if res is None:
        return None
    return res.int


def get_ref(uuid) -> Optional[weakref.ReferenceType]:
    """
Get ref: implementation of the get_ref logic.

Args:
    uuid: Operational parameter.

Returns:
    Standard result object.
"""
    if uuid is None:
        return None
    return uniqueidmap.get_ref(uuid)


def add_cleanup_hook(func):
    """
Add cleanup hook: implementation of the add_cleanup_hook logic.

Args:
    func: Operational parameter.
"""
    uniqueidmap.add_clean_callback(func)


def cleanup():
    """
Cleanup: implementation of the cleanup logic.
"""
    uniqueidmap.cleanup_fallbacks()
