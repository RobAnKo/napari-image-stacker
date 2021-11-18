"""
This module is an example of a barebones QWidget plugin for napari

It implements the ``napari_experimental_provide_dock_widget`` hook specification.
see: https://napari.org/docs/dev/plugins/hook_specifications.html

Replace code below according to your needs.
"""
import napari
from napari import Viewer
from napari.layers import Layer, Image
from napari.layers.utils.stack_utils import images_to_stack, stack_to_images

from napari_plugin_engine import napari_hook_implementation

from qtpy.QtWidgets import QMessageBox
from magicgui import magic_factory

from collections import Counter
#to test
#import datetime
#import pathlib


# class QImageStackerWidget(QWidget):
#     # your QWidget.__init__ can optionally request the napari viewer instance
#     # in one of two ways:
#     # 1. use a parameter called `napari_viewer`, as done here
#     # 2. use a type annotation of 'napari.viewer.Viewer' for any parameter
#     def __init__(self, napari_viewer):
#         super().__init__()
#         self.viewer = napari_viewer
#         n_images = len(self.viewer.layers)
        
#         visible_chkbx = QCheckBox("return visible?")
#         visible_chkbx.setChecked(False)
#         img2stack_btn = QPushButton("All open images to stack")
#         img2stack_btn.clicked.connect(self._on_click_i2s_button)
#         stack2img_btn = QPushButton("All open stacks to images")
#         stack2img_btn.clicked.connect(self._on_click_s2i_button)

#         self.setLayout(QHBoxLayout())
#         self.layout().addWidget(img2stack_btn)
#         self.layout().addWidget(stack2img_btn)
#         self.layout().addWidget(visible_chkbx)

#     def _on_click_i2s_button(self):
#         layers = self.viewer.layers
#         valid = [layer for layer in layers 
#                  if (layer.data.ndim == 2 and not layer.rgb)]
#         print(f"Converting all {len(valid)} open images to a stack")
#         #viewer.
        
#     def _on_click_s2i_button(self):
#         layers = self.viewer.layers
#         valid = [layer for layer in layers 
#                  if (layer.data.ndim == 2 and not layer.rgb)]
#         print(f"Converting all {len(valid)} open images to a stack")


# # @magic_factory(
# #     call_button="Calculate",
# #     slider_float={"widget_type": "FloatSlider", 'max': 10},
# #     dropdown={"choices": ['first', 'second', 'third']},
# # )

# # def widget_demo(
# #     maybe: bool,
# #     some_int: int,
# #     spin_float=3.14159,
# #     slider_float=4.5,
# #     string="Text goes here",
# #     dropdown='first',
# #     date=datetime.datetime.now(),
# #     filename=pathlib.Path('/some/path.ext')
# # ):
# #     widget_demo.show()


@magic_factory(
    call_button="Convert",
    To_convert={"choices": ["Auto-detect", "Selection"]},
    Convert_from={"choices": ["Images to Stack", "Stack to Images"]}
    )

def ImageStackerWidget(viewer: Viewer,
                       To_convert="Auto-detect",
                       From_visible : bool=True,
                       To_visible : bool=False,
                       Remove_original_image : bool=False,
                       Convert_from="Images to Stack",
                       ):
    
    #defines whether output will be visible or not
    meta = {"visible": To_visible}
    
    print(f"There are {len(viewer.layers)} open layers.")
    
    #decide whether to-be-converted images/stacks should be automatically 
    #detected or only selected layers should be used
    if To_convert=="Auto-detect":
        #get all open layers
        layers = viewer.layers
        print("Using all suitable layers for conversion.")
    elif To_convert=="Selection":
        #get only selected layers
        layers = [l for l in viewer.layers.selection]
        print(f"Using only selected layers ({len(layers)}/{len(viewer.layers)}) for conversion.")
    else:
        pass
    
    #decide whether only visible layers should be considered
    if From_visible:
        valid = [True for l in layers if l.visible]
        print(f"Using only visible layers ({sum(valid)}/{len(layers)}).")
        layers = [l for l in layers if l.visible]
    else:
        pass
    
    #extract shapes, dimensions and rgb flags to decide which of the layers 
    #can be concatenated into a stack
    try:
        shapes, dimensions, rgb = zip(*[(l.data.shape, l.data.ndim, l.rgb) 
                                        for l in layers])
    except:
        message = "No convertible images found"
        print(message)
        return
    
    #see how many images of which shapes we have
    Counter_shapes = Counter(shapes)
    
    if Convert_from == "Images to Stack":
        #Stacking only makes sense if there is more than one image of a given 
        #shape
        candidates = [k for k,count in Counter_shapes.items() if count>1]
        
        if not len(candidates):
            print("We did not find multiple same-shaped images to convert.")
            return
        
        #extract groups of images sharing the same shape
        valid_images = [[im for im,sh in zip(layers, shapes) if sh == cand] 
                        for cand in candidates]
        
        #for each shape group return a stack
        for vi in valid_images:
            stackname = vi[0].name+"_stacked"
            print(f"creating stack {stackname}\n"
                  f"from {len(vi)} images.")
            meta["name"] = stackname
            viewer.layers.append(images_to_stack(images=vi, axis=0, **meta))
            
            if Remove_original_image:
                for v in vi:
                    print(f"Removing {v.name}.")
                    viewer.layers.remove(v)
        return
    
    elif Convert_from == "Stack to Images":
        #Unstacking only makes sense if there are sufficient dimensions, depending on
        # whether we deal with an RGB image or not
        candidates = [l for l,d,r in zip(layers,dimensions,rgb) 
                      if ((r and d>3) or (not r and d>2))]
        
        if not len(candidates):
            print("We did not find multiple same-shaped images to convert.")
            return
        
        #for each stack return single images
        for c in candidates:
            n = c.data.shape[0]
            print(f"Colormap: {c.colormap.name}")
            #meta["colormap"] = c.colormap.asdict()#"gray_r"#c.colormap.colors
            print(f"Splitting stack {c.name}\n"
                  f"into {n} single images")
            S = stack_to_images(stack=c, axis=0, **meta)
            
            #This is a workaround, since colormap definition through 
            #**kwargs for stack_to_images does not work properly
            for s in S:
                s.colormap = c.colormap
                s.blending = c.blending
                
            #add them to the viewer
            viewer.layers.extend(S)
            
            if Remove_original_image:
                print(f"Removing {c.name}.")
                viewer.layers.remove(c)
                
        return
    
    else:
        return

@napari_hook_implementation
def napari_experimental_provide_dock_widget():
    return ImageStackerWidget
