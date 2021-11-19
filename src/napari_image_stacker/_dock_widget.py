"""
This module contains the Image Stacker Widget functionality

It implements the ``napari_experimental_provide_dock_widget`` hook specification.
see: https://napari.org/docs/dev/plugins/hook_specifications.html

"""
from napari import Viewer
from napari.layers.utils.stack_utils import images_to_stack, stack_to_images

from napari_plugin_engine import napari_hook_implementation

from magicgui import magic_factory

from collections import Counter



@magic_factory(
    call_button='Convert',
    To_convert={"choices": ["Auto-detect", "Selection"], 'tooltip': 'Use all suitable layers or only selected layers (highlighted in layer list)'},
    From_visible={'tooltip':"Use only visible layers ('bright eye' in layer list)"},
    To_visible={'tooltip':" Resulting layer(s) are visible"},
    Remove_original_image={'tooltip':"Remove the used layer(s) after conversion"},
    Convert_from={"choices": ["Images to Stack", "Stack to Images"],"tooltip":"Split stack(s) into images or concatenate images into stack(s)"}, 
    )

def image_stacker_widget(viewer: Viewer,
                         To_convert="Auto-detect",
                         From_visible: bool=True,
                         To_visible: bool=False,
                         Remove_original_image: bool=False,
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
    if len(layers):
        shapes, dimensions, rgb = zip(*[(l.data.shape, l.data.ndim, l.rgb) 
                                        for l in layers])
    else:
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
            print("We did not find stacks to convert.")
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
    return image_stacker_widget
