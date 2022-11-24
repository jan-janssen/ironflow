# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
A new output port class that has a dtype.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Optional, TYPE_CHECKING

from ryvencore.NodePort import NodeInput as NodeInputCore, NodeOutput as NodeOutputCore
from ryvencore.NodePortBP import NodeOutputBP as NodeOutputBPCore
from ryvencore.utils import serialize

from ironflow.model.dtypes import DType

if TYPE_CHECKING:
    from ironflow.model.node import Node


class HasDType:
    """A mixin to add the valid value check property"""
    @property
    def valid_val(self):
        if self.dtype is not None:
            if self.val is not None:
                return self.dtype._instance_matches(self.val)
            else:
                return self.dtype.allow_none
        else:
            return True


class NodeInput(NodeInputCore, HasDType):
    def __init__(
            self,
            node: Node,
            type_: str = 'data',
            label_str: str = '',
            add_data: Optional[dict] = None,
            dtype: Optional[DType] = None
    ):
        super().__init__(
            node=node,
            type_=type_ if dtype is None else 'data',
            label_str=label_str,
            add_data=add_data if add_data is not None else {},
            dtype=deepcopy(dtype)  # Because some dtypes have mutable fields
        )


class NodeOutput(NodeOutputCore, HasDType):
    def __init__(self, node, type_='data', label_str='', dtype: DType = None):
        super().__init__(
            node=node,
            type_=type_ if dtype is None else 'data',
            label_str=label_str)
        self.dtype = deepcopy(dtype)  # Some dtypes have mutable fields

    def data(self) -> dict:
        data = super().data()

        data['dtype'] = str(self.dtype)
        data['dtype state'] = serialize(self.dtype.get_state())

        return data


class NodeOutputBP(NodeOutputBPCore):
    def __init__(
            self, label: str = '', type_: str = 'data', dtype: Optional[DType] = None
    ):
        super().__init__(label=label, type_=type_)
        self.dtype = dtype
