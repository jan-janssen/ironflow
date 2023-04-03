# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
A new output port class that has a dtype.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Optional, TYPE_CHECKING

from numpy import argwhere
from ryvencore.NodePort import NodeInput as NodeInputCore, NodeOutput as NodeOutputCore
from ryvencore.NodePortBP import (
    NodeOutputBP as NodeOutputBPCore,
    NodeInputBP as NodeInputBPCore,
)
from ryvencore.utils import serialize

from ironflow.model.dtypes import DType, Untyped

if TYPE_CHECKING:
    from ironflow.model.node import Node


class HasDType:
    """A mixin to add the valid value check property"""

    @property
    def dtype_ok(self):
        if self.dtype is not None:
            if self.val is not None:
                return self.dtype.valid_val(self.val)
            else:
                return self.dtype.allow_none
        else:
            return True


class HasOType:
    """A mixin to add the valid value check to properties with an ontology type"""

    @property
    def otype_ok(self):
        if self.otype is not None:
            if isinstance(self, NodeInput):
                input_tree = self.otype.get_source_tree(
                    additional_requirements=self.get_downstream_requirements()
                )
                return all(
                    con.out.all_connections_found_in(input_tree)
                    for con in self.connections
                    if con.out.otype is not None
                )
            else:
                return all(
                    con.inp.workflow_tree_contains_connections_of(self)
                    for con in self.connections
                    if con.inp.otype is not None
                )
        else:
            return True

    def _output_graph_is_represented_in_workflow_tree(self, output_port, input_tree):
        try:
            output_index = argwhere(
                [output_port.otype == source.value for source in input_tree.children]
            )[0][0]
            upstream_inputs = [
                inp
                for inp in output_port.node.inputs
                if inp.otype is not None and len(inp.connections) > 0
            ]
            for usi in upstream_inputs:
                input_branches = input_tree.children[output_index].children[0].children
                # input/generic->outputs->function->inputs

                input_index = argwhere(
                    [usi.otype == source.value for source in input_branches]
                )[0][0]

                for con in usi.connections:
                    if (
                        con.out.otype is not None
                        and not self._output_graph_is_represented_in_workflow_tree(
                            con.out, input_branches[input_index]
                        )
                    ):
                        return False
            return True
        except IndexError:
            # Can't slice argwhere if it finds nothing
            return False

    def get_downstream_requirements(self):
        downstream_requirements = []
        for out in self.node.outputs:
            if out.otype is not None:
                for downstream_inp in [conn.inp for conn in out.connections]:
                    if downstream_inp.otype is not None:
                        downstream_requirements += (
                            downstream_inp.get_downstream_requirements()
                        )
        try:
            return self.otype.get_requirements(list(set(downstream_requirements)))
        except AttributeError:
            return list(set(downstream_requirements))


class HasTypes(HasOType, HasDType):
    @property
    def ready(self):
        return self.dtype_ok and self.otype_ok


class NodeInput(NodeInputCore, HasTypes):
    def __init__(
        self,
        node: Node,
        type_: str = "data",
        label_str: str = "",
        add_data: Optional[dict] = None,
        dtype: Optional[DType] = None,
        otype=None,
    ):
        super().__init__(
            node=node,
            type_=type_,
            label_str=label_str,
            add_data=add_data if add_data is not None else {},
            dtype=Untyped() if dtype is None else deepcopy(dtype),
        )
        self.otype = otype

    def _update_node(self):
        self.node.update(self.node.inputs.index(self))

    def batch(self):
        if self.dtype is not None and not self.dtype.batched:
            self.dtype.batched = True
            if len(self.connections) == 0:
                self.val = [self.val]
            self._update_node()

    def unbatch(self):
        if self.dtype is not None and self.dtype.batched:
            self.dtype.batched = False
            if len(self.connections) == 0:
                self.val = self.val[-1]
            self._update_node()

    def data(self) -> dict:
        data = super().data()

        if self.otype is not None:
            data["otype_namespace"] = self.otype.namespace.name
            data["otype_name"] = self.otype.name

        return data

    def workflow_tree_contains_connections_of(self, port: NodeOutput):
        tree = self.otype.get_source_tree(
            additional_requirements=self.get_downstream_requirements()
        )
        return self._output_graph_is_represented_in_workflow_tree(port, tree)


class NodeOutput(NodeOutputCore, HasTypes):
    def __init__(
        self,
        node,
        type_="data",
        label_str="",
        dtype: Optional[DType] = None,
        otype=None,
    ):
        super().__init__(node=node, type_=type_, label_str=label_str)
        self.dtype = Untyped() if dtype is None else deepcopy(dtype)
        self.otype = otype

    def data(self) -> dict:
        data = super().data()

        if self.dtype is not None:
            data["dtype"] = str(self.dtype)
            data["dtype state"] = serialize(self.dtype.get_state())

        if self.otype is not None:
            data["otype_namespace"] = self.otype.namespace.name
            data["otype_name"] = self.otype.name

        return data

    def all_connections_found_in(self, tree):
        """
        Checks to see if actual ontologically typed connections match with all
        ontologically possible workflows for an input port.
        """
        return self._output_graph_is_represented_in_workflow_tree(self, tree)


class NodeInputBP(NodeInputBPCore):
    def __init__(
        self,
        label: str = "",
        type_: str = "data",
        dtype: DType = None,
        add_data={},
        otype=None,
    ):
        super().__init__(label=label, type_=type_, dtype=dtype, add_data=add_data)
        self.otype = otype


class NodeOutputBP(NodeOutputBPCore):
    def __init__(
        self,
        label: str = "",
        type_: str = "data",
        dtype: Optional[DType] = None,
        otype=None,
    ):
        super().__init__(label=label, type_=type_)
        self.dtype = dtype
        self.otype = otype
