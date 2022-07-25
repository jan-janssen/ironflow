# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

from unittest import TestCase
from ryven.ironflow import GUI, Node, NodeInputBP, NodeOutputBP, dtypes
import os


class TestGUI(TestCase):

    def tearDown(self) -> None:
        try:
            os.remove("pyiron.log")
        except FileNotFoundError:
            pass

    def test_saving_and_loading(self):
        title = 'foo'
        gui = GUI(script_title=title)
        canvas = gui.canvas_widget
        flow = gui._session.scripts[0].flow

        canvas.add_node(0, 0, gui._nodes_dict['nodes']['val'])  # Need to create with canvas instead of flow
        canvas.add_node(1, 0, gui._nodes_dict['nodes']['result'])  # because serialization includes xy location
        n1, n2 = flow.nodes
        flow.connect_nodes(n1.outputs[0], n2.inputs[0])

        with self.assertRaises(FileNotFoundError):
            gui.on_file_load(None)

        gui.on_file_save(None)

        new_gui = GUI(script_title=title)
        self.assertNotEqual(new_gui._session, gui._session, msg="New instance expected to get its own session")
        # Maybe this will change in the future, but it's baked in the assumptions for now so let's make sure to test it

        new_flow = new_gui._session.scripts[0].flow
        print(new_flow)
        self.assertEqual(0, len(new_flow.nodes), msg="Fresh GUI shouldn't have any nodes yet.")
        self.assertEqual(0, len(new_flow.connections), msg="Fresh GUI shouldn't have any connections yet.")

        new_gui.draw()  # Temporary hack to ensure new_gui.out_canvas exists
        new_gui.on_file_load(None)
        new_flow = new_gui._session.scripts[0].flow  # Session script gets reloaded, so grab this again
        print(new_gui._session.scripts, new_gui._session.scripts[0].flow)
        self.assertEqual(len(flow.nodes), len(new_flow.nodes), msg="Loaded GUI should recover nodes.")
        self.assertEqual(
            len(flow.connections),
            len(new_flow.connections),
            msg="Loaded GUI should recover connections."
        )

        os.remove(f"{title}.json")

    def test_user_node_registration(self):
        """TODO: This only tests the backend graph, need to test front end as well"""
        gui = GUI(script_title='foo')

        class MyNode(Node):
            title = "MyUserNode"
            init_inputs = [
                NodeInputBP(dtype=dtypes.Integer(default=1), label="foo")
            ]
            init_outputs = [
                NodeOutputBP(label="bar")
            ]
            color = 'cyan'

            def update_event(self, inp=-1):
                self.set_output_val(0, self.input(0) + 42)

        gui.register_user_node(MyNode)
        self.assertIn(MyNode, gui.session.nodes)

        gui.canvas_widget.add_node(0, 0, gui._nodes_dict["user"][MyNode.title])
        gui.flow.nodes[0].inputs[0].update(1)
        self.assertEqual(gui.flow.nodes[0].outputs[0].val, 43)

        class MyNode(Node):  # Update class
            title = "MyUserNode"
            init_inputs = [
                NodeInputBP(dtype=dtypes.Integer(default=1), label="foo")
            ]
            init_outputs = [
                NodeOutputBP(label="bar")
            ]
            color = 'cyan'

            def update_event(self, inp=-1):
                self.set_output_val(0, self.input(0) - 42)

        gui.register_user_node(MyNode)
        gui.flow.nodes[0].inputs[0].update(2)
        self.assertEqual(gui.flow.nodes[0].outputs[0].val, 44, msg="Expected to be using instance of old class")

        gui.canvas_widget.add_node(1, 1, gui._nodes_dict["user"][MyNode.title])
        gui.flow.nodes[1].inputs[0].update(2)
        self.assertEqual(gui.flow.nodes[1].outputs[0].val, -40, msg="New node instances should reflect updated class.")
