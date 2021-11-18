"""
This module is an example of a barebones QWidget plugin for napari

It implements the ``napari_experimental_provide_dock_widget`` hook specification.
see: https://napari.org/docs/dev/plugins/hook_specifications.html

Replace code below according to your needs.
"""
from napari_plugin_engine import napari_hook_implementation
from qtpy.QtWidgets import QWidget, QHBoxLayout, QPushButton, QCheckBox
from magicgui import magic_factory

#to test
import datetime
import pathlib


class QImageStackerWidget(QWidget):
    # your QWidget.__init__ can optionally request the napari viewer instance
    # in one of two ways:
    # 1. use a parameter called `napari_viewer`, as done here
    # 2. use a type annotation of 'napari.viewer.Viewer' for any parameter
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer
        n_images = len(self.viewer.layers)
        
        visible_chkbx = QCheckBox("return visible?")
        visible_chkbx.setChecked(False)
        img2stack_btn = QPushButton("All open images to stack")
        img2stack_btn.clicked.connect(self._on_click_i2s_button)
        stack2img_btn = QPushButton("All open stacks to images")
        stack2img_btn.clicked.connect(self._on_click_s2i_button)

        self.setLayout(QHBoxLayout())
        self.layout().addWidget(img2stack_btn)
        self.layout().addWidget(stack2img_btn)
        self.layout().addWidget(visible_chkbx)

    def _on_click_i2s_button(self):
        layers = self.viewer.layers
        valid = [layer for layer in layers if (layer.data.ndim == 2 and not layer.rgb)]
        print(f"Converting all {len(valid)} open images to a stack")
        #viewer.
        
    def _on_click_s2i_button(self):
        layers = self.viewer.layers
        valid = [layer for layer in layers if (layer.data.ndim == 2 and not layer.rgb)]
        print(f"Converting all {len(valid)} open images to a stack")


@magic_factory(
    call_button="Calculate",
    slider_float={"widget_type": "FloatSlider", 'max': 10},
    dropdown={"choices": ['first', 'second', 'third']},
)

def widget_demo(
    maybe: bool,
    some_int: int,
    spin_float=3.14159,
    slider_float=4.5,
    string="Text goes here",
    dropdown='first',
    date=datetime.datetime.now(),
    filename=pathlib.Path('/some/path.ext')
):
    widget_demo.show()


@magic_factory
def MImageStackerWidget(img_layer: "napari.layers.Image"):
    print(f"you have selected {img_layer}")


@napari_hook_implementation
def napari_experimental_provide_dock_widget():
    # you can return either a single widget, or a sequence of widgets
    return [QImageStackerWidget, widget_demo, MImageStackerWidget]
