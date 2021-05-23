"""
MIT License

Copyright (c) 2020 TehMerow

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


"""

import bpy #type: ignore
from bpy.types import Operator #type: ignore


bl_info = {
    "name"    : "Create Outline Mesh",
    "blender" : (2,90,1),
    "version" : (1,1),
    "category": "Object",
    "author" : "Tehmerow",
    "doc_url" : "https://github.com/TehMerow/blender_create_outline_mesh/wiki/Tutorial",
    "location" : "Object Add Menu > Create Outline Mesh",
    "description" : "Creates a Outline Mesh around your object"
}


def _create_material(self, context):
    outline_color = self.outline_color
    mat_name = "outline_material"
    # Create Material
    bpy.data.materials.new(name=mat_name)

    # cache the material value
    mat = bpy.data.materials[mat_name]
    
    # sets the eevee values 
    mat.diffuse_color = outline_color
    mat.use_backface_culling = True
    mat.shadow_method = "NONE"
    mat.use_nodes = True
    
    return mat


def _create_outline_material(self, context):
    # Creates the outline material 
    mat_name = "outline_material"
    outline_color = self.outline_color

    if bpy.data.materials.find(mat_name) != -1:
        return
    
    mat = _create_material(self, context)
  
    # Creates the outline material group

    if bpy.data.node_groups.find("outline_material_shader_group") != -1:
        return
    
    _create_outline_material_group(self, context)

    # Creates the outline shader group in the material and links it all up
    outline_shader = mat.node_tree.nodes.new(type="ShaderNodeGroup")
    outline_shader.node_tree = bpy.data.node_groups['outline_material_shader_group']
    outline_shader.location = (0, -300)

    output_node = mat.node_tree.nodes.new(type="ShaderNodeOutputMaterial")
    output_node.location = (200, -300)
    output_node.target = "CYCLES"

    mat.node_tree.nodes['Material Output'].target = "EEVEE"
    mat.node_tree.links.new(outline_shader.outputs[0], output_node.inputs[0])

    # Sets the Pricipled nodes default values for outline shader for eevee
    principled_node = mat.node_tree.nodes["Principled BSDF"] 
    principled_node.inputs[0].default_value = outline_color
    principled_node.inputs[4].default_value = 1.0
    principled_node.inputs[5].default_value = 0.0
    principled_node.inputs[7].default_value = 1.0

    # # Create RGB mode for both eevee and cycles outline shaders
    # rgb_node = mat.node_tree.nodes.new(type="ShaderNodeRGB")
    # rgb_node.outputs[0].default_value = outline_color
    # rgb_node.location = (-400, 0)

    # mat.node_tree.links.new(rgb_node.outputs[0], principled_node.inputs[0])
    # mat.node_tree.links.new(rgb_node.outputs[0], outline_shader.inputs[0])

def _create_outline_material_group(self, context):
    # Outline material group for eevee
    outline_name = "outline_material_shader_group"
    outline_color = self.outline_color
    
    # Create the group
    cycles_outline_material_group = bpy.data.node_groups.new(name=outline_name, type="ShaderNodeTree")
    
    # create group input node
    group_inputs = cycles_outline_material_group.nodes.new("NodeGroupInput")
    group_inputs.location = (-1000, 0)
    
    # populate input with props
    # populate output with props
    cycles_outline_material_group.inputs.new(type="NodeSocketColor", name="BaseColor").default_value = outline_color
    cycles_outline_material_group.outputs.new(type="NodeSocketShader", name="Shader")
    
    # Create group output node
    outputs = cycles_outline_material_group.nodes.new("NodeGroupOutput")
    outputs.location = (500, 0)
    
    
    # shader node creation
    emit_node = cycles_outline_material_group.nodes.new("ShaderNodeEmission")
    emit_node.location = (-800, 0)
    
    trans_node = cycles_outline_material_group.nodes.new("ShaderNodeBsdfTransparent")
    trans_node.location = (-600, -200)
    
    light_path_node = cycles_outline_material_group.nodes.new("ShaderNodeLightPath")
    light_path_node.location = (-800, 350)
    
    geom_path_node = cycles_outline_material_group.nodes.new("ShaderNodeNewGeometry")
    geom_path_node.location = (-600, 300)
    
    mix_node_shadeless = cycles_outline_material_group.nodes.new("ShaderNodeMixShader")
    mix_node_shadeless.location = (-600, 0)
    
    mix_node_backface = cycles_outline_material_group.nodes.new("ShaderNodeMixShader")
    mix_node_backface.location = (-300, 0)
    
    # Make connections
    
    cycles_outline_material_group.links.new(group_inputs.outputs[0], emit_node.inputs[0])
    cycles_outline_material_group.links.new(emit_node.outputs[0], mix_node_shadeless.inputs[2])
    cycles_outline_material_group.links.new(light_path_node.outputs[0], mix_node_shadeless.inputs[0])
    cycles_outline_material_group.links.new(mix_node_shadeless.outputs[0], mix_node_backface.inputs[1])
    cycles_outline_material_group.links.new(trans_node.outputs[0], mix_node_backface.inputs[2])
    cycles_outline_material_group.links.new(geom_path_node.outputs[6], mix_node_backface.inputs[0])
    cycles_outline_material_group.links.new(mix_node_backface.outputs[0], outputs.inputs[0])
    

def _update_cycles_settings(self, context):
    # Sets this object properties so the object doesn't
    # affect shading in cycles, not neccecary in Eevee but
    # nice to have
    context.active_object.cycles_visibility.diffuse = False
    context.active_object.cycles_visibility.glossy = False
    context.active_object.cycles_visibility.transmission = False
    context.active_object.cycles_visibility.scatter = False
    context.active_object.cycles_visibility.shadow = False

def _duplicate_selected(self, context):
    # Duplicate selected object
    bpy.ops.object.duplicate_move()
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.location_clear(clear_delta=False)
    pass


def _clear_material_slots(self, context):
    # Clear all material slots
    material_slots_length = len(bpy.context.active_object.material_slots.items())
    for i in range(0, material_slots_length-1):
        bpy.ops.object.material_slot_remove()


def _flip_normals(self, context):
    # Jump into edit mode, select all, 
    # flip normals, deselect, exit edit mode
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.flip_normals()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    
def _create_and_apply_displacement(self, context):
    scale = -self.size
    # Create displacement modifier and name it
    # Displacement modifier used to evenley expand
    # the mesh from normals instead of origin
    modifier_name = "outline_displacement"
    context.active_object.modifiers.new(
        name=modifier_name,
        type="DISPLACE"
    )
    
    # Set the strength of the displacement modifier
    context.active_object.modifiers[modifier_name].strength = scale
    
    # Apply the displacement modifier
    if self.apply_displacement:
        bpy.ops.object.modifier_apply(modifier="outline_displacement")


def _add_outline_mat(self, context):
    mat_slots = context.active_object.material_slots
    
    if len(mat_slots) > 0:
        for mat in range(0, len(mat_slots)-1):
            bpy.context.active_object.active_material_index = 0
            bpy.ops.object.material_slot_remove()

        # Add the outline material to the object in the first slot
        context.active_object.material_slots[0].material = bpy.data.materials['outline_material']

    else:
        bpy.ops.object.material_slot_add()
        context.active_object.material_slots[0].material = bpy.data.materials['outline_material']


def _change_obj_name(self, context, object_name):
    # Change the name of the outline object to 
    # Active object name + .outline
    context.active_object.name = object_name + ".outline"    


def _parent_outline_to_original_mesh(self, context, object_name):

    # Parents the outline object to the original active object
    if not self.parent_to_original:
        return
    context.active_object.parent = bpy.data.objects[object_name]




def _outline_obj(self, context):
    object_name = context.active_object.name
    

    _duplicate_selected(self, context)
    _clear_material_slots(self, context)
    _flip_normals(self, context)
    _create_and_apply_displacement(self, context)
    _update_cycles_settings(self, context)
    _add_outline_mat(self, context)
    _change_obj_name(self, context, object_name)
    _parent_outline_to_original_mesh(self, context, object_name)
    _move_to_collection(self, context)
    



def _move_to_collection(self, context):
    if not self.move_to_collection:
        return
    collections = bpy.data.collections
    collection_name = self.collection_name
    outline_collection = None

    active_obj = context.active_object

    if collections.find(collection_name) == -1:
        outline_collection = bpy.data.collections.new(collection_name)
        context.scene.collection.children.link(outline_collection)
    else:
        outline_collection = bpy.data.collections[collection_name]



    outline_collection.objects.link(active_obj)



def set_backface_culling_in_viewports(self, context):
    area = next(area for area in bpy.context.screen.areas if area.type == "VIEW_3D")
    space = next(space for space in area.spaces if space.type == "VIEW_3D")
    space.shading.show_backface_culling = True

    if self.view_in_mat_preview:
        space.shading.type = "MATERIAL"

class CreateOutLine(Operator):
    """Create a new Mesh Object"""
    bl_idname = "mesh.create_outline_mesh"
    bl_label = "Create Outline Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    size: bpy.props.FloatProperty(
        name="Size",
        default=0.05,
        description="scaling",
        min = 0.001,
        max = 1.0,
        precision = 3
    )

    outline_color: bpy.props.FloatVectorProperty(
        name = "Outline Color (Global) \n Note: this only adjusts the color each new material",
        subtype = 'COLOR',
        size = 4,
        default = (0.01, 0.01, 0.01, 1.0),
        step = 100,
        min = 0.0,
        max = 1.0
    )
    view_in_mat_preview: bpy.props.BoolProperty(
        name = "Jump to Material Preview",
        default = False,
        description = "Turn on Material Preview"
    )
    apply_displacement: bpy.props.BoolProperty(
        name = "Apply Displacement Modifier",
        default = True,
        description="Deactivate this so the displacement modifier can be edited in the future"
    )

    parent_to_original: bpy.props.BoolProperty(
        name = "Parent to Original",
        default = True,
        description = "Parents the outline object to the original object"
    )

    move_to_collection: bpy.props.BoolProperty(
        name = "Move to outline Collection",
        default = False,
        description = "Moves the outline object to an outline collection"
    )
    
    collection_name: bpy.props.StringProperty(
        name = "Collection Name",
        default = "outline_collection",
        description = "Which Collection to put the outline mesh"
    )



    def execute(self, context):
        _create_outline_material(self, context)

        _outline_obj(self, context)
        set_backface_culling_in_viewports(self,context)
        return {'FINISHED'}


# UI 



def outline_menu(self, context):
    self.layout.operator("mesh.create_outline_mesh")

classes = (
    CreateOutLine,
)


def register():
    bpy.types.VIEW3D_MT_add.append(outline_menu)
    for item in classes:
        bpy.utils.register_class(item)


def unregister():
    bpy.types.VIEW3D_MT_add.remove(outline_menu)
    for item in classes:
        bpy.utils.unregister_class(item)


if __name__ == "__main__":
    register()