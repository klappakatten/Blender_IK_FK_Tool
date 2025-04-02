import sys
print(sys.path)
import bpy
from . import addik, addfk

bl_info = {
    "name" : "Create Rig Controllers",
    "author" : "Martin Nyman",
    "version" : (0,0,1),
    "blender": (4,2,1),
    "location" : "3D Viewport > Sidebar > Create Rig Controllers category",
    "description": "Create Rig Controllers",
    "category": "Development"
}

def register_properties():
    bpy.types.Scene.ik_chain_length = bpy.props.IntProperty(
        name="IK Chain Length",
        description="Input your first integer",
        default=2,
        min=0,
        max=5
    )

    bpy.types.Scene.bones_in_chain = bpy.props.IntProperty(
        name="Bones In Chain",
        description="Input your second integer",
        default=3,
        min=0,
        max=10
    )
    
    
    bpy.types.Scene.poles_flipped = bpy.props.BoolProperty(
        name="Flipped Pole Target?",
        description="Wheter to create pole target - direction",
        default=False
    )
    
def unregister_properties():
    del bpy.types.Scene.ik_chain_length
    del bpy.types.Scene.bones_in_chain
    del bpy.types.Scene.poles_flipped
    
def add_fk(self, context):
    print("ADDED FK!")
    addfk.create_fk_controls()

def add_ik(self, context):
    print("ADDED IK!")
    ik_chain_length = context.scene.ik_chain_length
    bones_in_chain = context.scene.bones_in_chain
    poles_flipped = context.scene.poles_flipped
    addik.start_add_ik(ik_chain_length, bones_in_chain, poles_flipped)

class Create_Rig_Panel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Create Rig Controllers"
    bl_label = "Create Rig Controllers"
    bl_idname = "VIEW3D_PT_create_rig_controllers"  # Added this

    def draw(self, context):
        layout = self.layout
        layout.operator("rig.add_fk")
        layout.prop(context.scene, "ik_chain_length")
        layout.prop(context.scene, "bones_in_chain")
        layout.prop(context.scene, "poles_flipped")
        layout.operator("rig.add_ik")

        
class AddFKOperator(bpy.types.Operator):
    bl_idname = "rig.add_fk"
    bl_label = "Add FK"

    def execute(self, context):
        add_fk(self, context)
        return {'FINISHED'}

class AddIKOperator(bpy.types.Operator):
    bl_idname = "rig.add_ik"
    bl_label = "Add IK"
    
    def execute(self, context):
        add_ik(self, context)
        return {'FINISHED'}

def register():
    bpy.utils.register_class(Create_Rig_Panel)
    bpy.utils.register_class(AddFKOperator)
    bpy.utils.register_class(AddIKOperator)
    register_properties()

def unregister():
    unregister_properties()
    bpy.utils.unregister_class(Create_Rig_Panel)
    bpy.utils.unregister_class(AddFKOperator)
    bpy.utils.unregister_class(AddIKOperator)

if __name__ == "__main__":
    register()