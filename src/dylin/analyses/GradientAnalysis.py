"""
Module for GradientAnalysis functionality.
"""
from typing import Any, Callable, Dict, List, Optional, Tuple
import collections

from torch import Tensor
from .base_analysis import BaseDyLinAnalysis
from ..markings.obj_identifier import uniqueid, get_ref, add_cleanup_hook, save_uid

import tensorflow as tf
import torch.nn as nn
import torch


class GradientAnalysis(BaseDyLinAnalysis):
    """
Gradientanalysis: logical component class.
"""
    def __init__(self, **kwargs):
        """
Init: implementation of the __init__ logic.

Key Variables:
    analysis_name: Local state member.
    stored_torch_models: Local state member.
    threshold: Local state member.
    total_gradients_investigated: Local state member.
"""
        super().__init__(**kwargs)
        self.analysis_name = "GradientAnalysis"
        # common clipping values are 1,3,5,8,10
        self.threshold = float(10.0)
        self.stored_torch_models: Dict[str, bool] = {}
        self.total_gradients_investigated = 0

        def cleanup_torch_model(uuid: str):
            """
Cleanup torch model: implementation of the cleanup_torch_model logic.

Args:
    uuid: Operational parameter.
"""
            if not self.stored_torch_models.get(uuid) is None:
                del self.stored_torch_models[uuid]

        add_cleanup_hook(cleanup_torch_model)

    def pre_call(self, dyn_ast: str, iid: int, function: Callable, pos_args: Tuple, kw_args: Dict):
        """
Pre call: implementation of the pre_call logic.

Args:
    dyn_ast: Dynamic AST tree.
    iid: Instruction identifier.
    function: Operational parameter.
    pos_args: Positional logic arguments.
    kw_args: Keyword logic arguments.

Key Variables:
    _max: Local state member.
    _min: Local state member.
    grad: Local state member.
    gradients: Local state member.
    total_gradients_investigated: Local state member.

Loop Behavior:
    Iterates through range(0, len(gradients)).
"""
        # tensorflow
        # print(f"{self.analysis_name} pre_call {iid}")
        if "__func__" in dir(function) and function.__func__ == tf.optimizers.Optimizer.apply_gradients:
            if isinstance(pos_args[0], collections.abc.Iterator):
                # pos_args[0] can be a zip object, which is an Iterator. These objects
                # can only be used once and then return an emtpy list, to prevent that
                # we reassign pos_args with the extracted list in the end
                # pos_args = (l,)
                gradients = list(pos_args[0])
                pos_args[0] = gradients
            else:
                gradients = list(pos_args[0])

            for i in range(0, len(gradients)):
                self.total_gradients_investigated = self.total_gradients_investigated + 1
                # gradients[i] is a tuple where first element is gradient, second trainable variable
                grad: tf.Tensor = gradients[i][0]
                _min = tf.math.reduce_min(grad)
                _max = tf.math.reduce_max(grad)
                if _min <= -self.threshold or _max >= self.threshold:
                    self.add_finding(
                        iid,
                        dyn_ast,
                        "M-28",
                        f"Gradient too high / low gradient has min {_min} max {_max} value",
                    )

    def post_call(
        self,
        dyn_ast: str,
        iid: int,
        val: Any,
        function: Callable,
        pos_args: Tuple,
        kw_args: Dict,
    ) -> Any:
        """
Post call: implementation of the post_call logic.

Args:
    dyn_ast: Dynamic AST tree.
    iid: Instruction identifier.
    val: Operational parameter.
    function: Operational parameter.
    pos_args: Positional logic arguments.
    kw_args: Keyword logic arguments.

Key Variables:
    _max: Local state member.
    _min: Local state member.
    _self: Local state member.
    grads: Local state member.
    model: Local state member.
    params: Local state member.
    ref: Local state member.
    total_gradients_investigated: Local state member.
    uuid: Local state member.

Loop Behavior:
    Iterates through self.stored_torch_models.
    Iterates through grads.

Returns:
    Standard result object.
"""
        # print(f"{self.analysis_name} post_call {iid}")
        if val is function:
            return
        # pytorch

        # nn.Module is the base class for all neural network modules
        # mirror the object and use it later to extract gradients
        if isinstance(val, nn.Module):
            uuid = save_uid(val)
            if self.stored_torch_models.get(uuid) is None:
                self.stored_torch_models[uniqueid(val)] = True
        else:
            # because Optimizer.step sometimes use annotations which hide actual method
            # we just hook every call to Optimizers
            _self = getattr(function, "__self__", lambda: None)
            if _self is not None and isinstance(_self, torch.optim.Optimizer):
                for model_uid in self.stored_torch_models:
                    ref = get_ref(model_uid)
                    if not ref is None:
                        model: nn.Module = ref()
                        # extract params, they include all params for the nn.Module instance
                        # e.g. weights, bias etc. we extract only the ones for which a gradient is available
                        params: List[nn.parameter.Parameter] = model.parameters()
                        grads: List[Optional[Tensor]] = [p.grad for p in params]
                        if len(grads) > 0:
                            self.total_gradients_investigated = self.total_gradients_investigated + 1
                        for grad in grads:
                            if not grad is None:
                                _max = torch.max(grad)
                                _min = torch.min(grad)
                                if _max >= self.threshold or _min <= -self.threshold:
                                    self.add_finding(
                                        iid,
                                        dyn_ast,
                                        "M-28",
                                        f"Gradient too high / low gradient has min {_min} max {_max} value",
                                    )
                                    return

    def end_execution(self) -> None:
        """
End execution: implementation of the end_execution logic.

Returns:
    Standard result object.
"""
        self.add_meta({"total_gradients_investigated": self.total_gradients_investigated})
        super().end_execution()
