# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
For directly controlling node IO (as opposed to giving it to nodes by connecting them to other OI).
"""

from __future__ import annotations

import pickle
import base64
from typing import TYPE_CHECKING, Callable

import ipywidgets as widgets
import numpy as np
from IPython.display import display
from ryvencore.InfoMsgs import InfoMsgs
from traitlets import TraitError

from ironflow.gui.workflows.boxes.node_interface.base import NodeInterfaceBase


if TYPE_CHECKING:
    from ironflow.gui.workflows.screen import WorkflowsGUI
    from ironflow.model.node import Node


def deserialize(data):
    return pickle.loads(base64.b64decode(data))


class NodeController(NodeInterfaceBase):
    """
    Handles the creation of widgets for manually adjusting node input and viewing node info.
    """

    def __init__(self, screen: WorkflowsGUI):
        super().__init__()
        self.screen = screen
        self.node = None
        self._margin = 5  # px
        self._row_height = 30  # px

    def _box_height(self, n_rows: int) -> int:
        return n_rows * self._row_height + 2 * self._margin

    @property
    def input_widget(self) -> widgets.Widget:
        try:
            widget = self.node.input_widget(self.screen, self.node).widget
            widget.layout = widgets.Layout(
                height="70px",
                border="solid 1px blue",
                margin=f"{self._margin}px",
                padding="10px",
                width="auto",
            )
            return widget
        except AttributeError:
            return widgets.Output()

    def input_field_list(self) -> list[list[widgets.Widget]]:
        input = []
        if hasattr(self.node, "inputs"):
            for i_c, inp in enumerate(self.node.inputs[:]):
                if inp.dtype is not None:
                    dtype = str(inp.dtype).split(".")[-1]
                    disabled = self.node.block_updates or len(inp.connections) > 0
                    try:
                        dtype_state = deserialize(inp.data()["dtype state"])
                    except TypeError:
                        # `inp.data()` winds up calling `serialize` on `inp.get_val()`
                        # This serialization is a pickle dump, which fails with structures (`Atoms`)
                        # Just gloss over it for now
                        dtype_state = {
                            "val": "Serialization error -- please reconnect an input"
                        }
                    if inp.val is None:
                        inp.val = dtype_state["val"]

                    if dtype_state["batched"]:
                        inp_widget = widgets.Text(
                            f"Batched {dtype}",
                            continuous_update=False,
                            disabled=True,
                        )
                    elif dtype == "Integer":
                        inp_widget = widgets.IntText(
                            value=inp.val,
                            description="",
                            continuous_update=False,
                            disabled=disabled,
                        )
                    elif dtype == "Float":
                        inp_widget = widgets.FloatText(
                            value=inp.val,
                            description="",
                            continuous_update=False,
                            disabled=disabled,
                        )
                    elif dtype == "Boolean":
                        inp_widget = widgets.Checkbox(
                            value=inp.val,
                            indent=False,
                            description="",
                            disabled=disabled,
                        )
                    elif dtype == "Choice":
                        inp_widget = widgets.Dropdown(
                            value=inp.val,
                            options=inp.dtype.items,
                            description="",
                            ensure_option=True,
                            disabled=disabled,
                        )
                    elif dtype == "String" or dtype == "Char":
                        inp_widget = widgets.Text(
                            value=str(inp.val),
                            continuous_update=False,
                            disabled=disabled,
                        )
                    else:
                        inp_widget = widgets.Text(
                            value=str(inp.val), continuous_update=False, disabled=True
                        )
                    description = inp.label_str
                elif inp.label_str != "":
                    inp_widget = widgets.Label(value=inp.type_)
                    description = inp.label_str
                else:
                    inp_widget = widgets.Label(value=inp.type_)
                    description = inp.type_
                inp_widget.layout.width = "100px"
                inp_widget.observe(self.input_change_i(i_c), names="value")
                batch_button = widgets.ToggleButton(
                    description="Batched",
                    tooltip="Use batches batches of correctly typed data instead of "
                            "instances",
                    layout=widgets.Layout(max_width="70px", min_width="70px"),
                    disabled=inp.dtype is None,
                    value=inp.dtype.batched if hasattr(inp, "dtype") else False
                )
                batch_button.observe(self.toggle_batching_i(i_c), names="value")
                reset_button = widgets.Button(
                    tooltip="Reset to default",
                    icon="refresh",
                    layout=widgets.Layout(max_width="50px", min_width="50px"),
                    disabled=inp.dtype is None or inp_widget.disabled,
                )
                reset_button.on_click(self.input_reset_i(i_c, inp_widget))
                input.append(
                    [widgets.Label(description), inp_widget, batch_button, reset_button]
                )
        return input

    def input_change_i(self, i_c) -> Callable:
        def input_change(change: dict) -> None:
            # Todo: Test this in exec mode
            self.node.inputs[i_c].val = change["new"]
            self.node.update(i_c)
            self.screen.redraw_active_flow_canvas()

        return input_change

    def toggle_batching_i(self, i_c) -> Callable:
        def toggle_batching(change: dict) -> None:
            try:
                InfoMsgs.write(
                    f"Batching for {self.node.title}.{self.node.inputs[i_c].label_str} "
                    f"set to {change['new']}"
                )
                self.node.inputs[i_c].dtype.batched = change["new"]
                self.node.update(i_c)
                self.screen.redraw_active_flow_canvas()
                self.draw()
            except AttributeError:
                pass

        return toggle_batching

    def input_reset_i(self, i_c, associated_input_field) -> Callable:
        def input_reset(button: widgets.Button) -> None:
            default = self.node.inputs[i_c].dtype.default
            self.node.inputs[i_c].val = default
            InfoMsgs.write(
                f"Value for {self.node.title}.{self.node.inputs[i_c].label_str} "
                f"reset to {default}"
            )
            try:
                associated_input_field.value = default
            except TraitError:
                associated_input_field.value = associated_input_field.traits()[
                    "value"
                ].default()
            finally:
                pass
            self.node.update(i_c)
            self.screen.redraw_active_flow_canvas()

        return input_reset

    @property
    def input_box(self) -> widgets.GridBox | widgets.Output:
        input_fields = self.input_field_list()
        n_fields = len(input_fields)
        if n_fields > 0:
            return widgets.GridBox(
                list(np.array(input_fields).flatten()),
                layout=widgets.Layout(
                    grid_template_columns="45% 45% 10%",
                    grid_auto_rows=f"{self._row_height}px",
                    border="solid 1px blue",
                    margin=f"{self._margin}px",
                    height=f"{self._box_height(n_fields)}px",
                    # Automatic height like this really should be doable just with the CSS,
                    # but for the life of me I can't get a CSS solution working right -Liam
                ),
            )
        else:
            return widgets.Output()

    @property
    def info_box(self) -> widgets.VBox:
        glob_id_val = None
        if hasattr(self.node, "GLOBAL_ID"):
            glob_id_val = self.node.GLOBAL_ID
        global_id = widgets.Text(
            value=str(glob_id_val), description="GLOBAL_ID:", disabled=True
        )

        title = widgets.Text(
            value=str(self.node.title), description="Title:", disabled=True
        )

        info_box = widgets.VBox([title, global_id])
        info_box.layout = widgets.Layout(
            height=f"{self._box_height(2)}px",
            border="solid 1px red",
            margin=f"{self._margin}px",
            padding="0px",
        )
        return info_box

    def draw(self) -> None:
        self.clear_output()
        if self.node is not None:
            with self.output:
                display(
                    widgets.VBox([self.input_box, self.input_widget, self.info_box])
                )
                # PyCharm nit is invalid, display takes *args is why it claims to want a tuple

    def draw_for_node(self, node: Node | None) -> None:
        self.node = node
        self.draw()

    def close(self) -> None:
        self.draw_for_node(None)
