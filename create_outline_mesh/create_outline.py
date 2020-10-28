import bpy
from bpy.types import Operator


bl_info = {
    "name"    : "Create Outline Mesh",
    "blender" : (2,90,1),
    "version" : (1,0),
    "category": "Object",
    "author" : "Merow",
    "doc_url" : "https://github.com/TehMerow/blender_create_outline_mesh/wiki/Tutorial",
    "location" : "Operator Search Menu (f3) 'Create Outline Mesh'",
    "description" : "Creates a mesh outline around your object"
}


def _create_outline_material():
    mat_name = "outline_material"

    if bpy.data.materials.find(mat_name) != -1:
        return
    # Create Material
    bpy.data.materials.new(name=mat_name)

    # cache the material value
    mat = bpy.data.materials[mat_name]
    
    # sets the eevee values 
    mat.diffuse_color = (0.0,0.0,0.0,1.0)
    mat.use_backface_culling = True
    mat.shadow_method = "NONE"
    mat.use_nodes = True
    
    # Creates the outline material group

    if bpy.data.node_groups.find("outline_material_shader_group") != -1:
        return
    
    _create_outline_material_group()
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
    principled_node.inputs[0].default_value = (0.01, 0.01, 0.01, 1.0)
    principled_node.inputs[4].default_value = 1.0
    principled_node.inputs[5].default_value = 0.0
    principled_node.inputs[7].default_value = 1.0

    # Create RGB mode for both eevee and cycles outline shaders
    rgb_node = mat.node_tree.nodes.new(type="ShaderNodeRGB")
    rgb_node.outputs[0].default_value = (0.01, 0.01, 0.01, 1.0)
    rgb_node.location = (-400, 0)

    mat.node_tree.links.new(rgb_node.outputs[0], principled_node.inputs[0])
    mat.node_tree.links.new(rgb_node.outputs[0], outline_shader.inputs[0])

def _create_outline_material_group():
    outline_name = "outline_material_shader_group"

    
    # Create the group
    cycles_outline_material_group = bpy.data.node_groups.new(name=outline_name, type="ShaderNodeTree")
    
    # create group input node
    group_inputs = cycles_outline_material_group.nodes.new("NodeGroupInput")
    group_inputs.location = (-1000, 0)
    
    # populate input with props
    # populate output with props
    cycles_outline_material_group.inputs.new(type="NodeSocketColor", name="BaseColor").default_value = (0.01,0.01,0.01,1.0)
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
    

def _outline_obj(self, context):

    scale = -self.size
    object_name = context.active_object.name

    # Duplicate selected object
    bpy.ops.object.duplicate_move()
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    
    # Clear all material slots
    material_slots_length = len(bpy.context.active_object.material_slots.items())
    for i in range(0, material_slots_length-1):
        bpy.ops.object.material_slot_remove()
    
    # Jump into edit mode, select all, 
    # flip normals, deselect, exit edit mode
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.flip_normals()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    
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
    
    # Sets this object properties so the object doesn't
    # affect shading in cycles, not neccecary in Eevee but
    # nice to have
    context.active_object.cycles_visibility.diffuse = False
    context.active_object.cycles_visibility.glossy = False
    context.active_object.cycles_visibility.transmission = False
    context.active_object.cycles_visibility.scatter = False
    context.active_object.cycles_visibility.shadow = False

    # Add the outline material to the object in the first slot
    context.active_object.material_slots[0].material = bpy.data.materials['outline_material']
    
    # Change the name of the outline object to 
    # Active object name + .outline
    context.active_object.name = object_name + ".outline"    
    
    # Parents the outline object to the original active object
    if self.parent_to_original:
        context.active_object.parent = bpy.data.objects[object_name]

class CreateOutLine(Operator):
    """Create a new Mesh Object"""
    bl_idname = "mesh.create_outline_mesh"
    bl_label = "Create Outline Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    size: bpy.props.FloatProperty(
        name="Scale",
        default=0.05,
        description="scaling",
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

    def execute(self, context):
        _create_outline_material()

        _outline_obj(self, context)

        return {'FINISHED'}



classes = (
    CreateOutLine,
)


def register():
    for item in classes:
        bpy.utils.register_class(item)



def unregister():
    for item in classes:
        bpy.utils.unregister_class(item)




if __name__ == "__main__":
    register()