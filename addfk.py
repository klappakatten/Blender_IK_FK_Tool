import bpy
import math

#Ö05 - Blender Rig Script

def create_controls_shapes(box_scale, circle_radius, plane_scale):
    
    bpy.ops.object.mode_set(mode='OBJECT',toggle=False)

    if "Cube" not in bpy.data.objects:
    #Create Controller for BOX
        bpy.ops.mesh.primitive_cube_add(enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(box_scale, box_scale, box_scale))
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.delete(type='ONLY_FACE')
        bpy.ops.object.editmode_toggle()
        bpy.context.object.hide_set(True)
    if "Circle" not in bpy.data.objects:
        #Create Controller for CIRCLE
        bpy.ops.mesh.primitive_circle_add(radius=circle_radius, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        bpy.context.active_object.rotation_euler[0] = math.radians(90)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.delete(type='ONLY_FACE')
        bpy.ops.object.editmode_toggle()
        bpy.context.object.hide_set(True)
    if "Plane" not in bpy.data.objects:
        #Create Controller for PLANE
        bpy.ops.mesh.primitive_plane_add(size=plane_scale, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        bpy.context.active_object.rotation_euler[0] = math.radians(90)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.delete(type='ONLY_FACE')
        bpy.ops.object.editmode_toggle()
        bpy.context.object.hide_set(True)

def show_error_message(message):
    bpy.context.window_manager.popup_menu(lambda self, context: self.layout.label(text=message), title="Error", icon='ERROR')

def create_fk_controls():
    armature = bpy.context.active_object
    selected_objects = bpy.context.selected_objects

    if armature.type != 'ARMATURE':
        show_error_message("PLEASE SELECT ARMATURE OBJECT")
        print("PLEASE SELECT ARMATURE OBJECT")
        return
    if not len(selected_objects) == 1:
        show_error_message("PLEASE SELECT ONLY ONE ARMATURE")
        print("PLEASE SELECT ONLY ONE ARMATURE")
        return
    
    edit_bones = armature.data.edit_bones
    pose_bones = armature.pose.bones
    
    bpy.ops.object.editmode_toggle()    
    bpy.ops.armature.select_all(action='SELECT')
    bpy.ops.object.editmode_toggle()
        
    create_controls_shapes(.3,2,5)
    bpy.ops.object.select_all(action='DESELECT')

    #Reselect armature
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature

    #Push mesh to REST position
    bpy.ops.object.mode_set(mode='POSE',toggle=False)

    bpy.context.object.data.pose_position = 'REST'

    bpy.ops.object.mode_set(mode='EDIT',toggle=False)

    #Duplicate Armature
    bpy.ops.armature.duplicate_move(ARMATURE_OT_duplicate={"do_flip_names":False},
    TRANSFORM_OT_translate={
    "value":(0,0,0),
    "orient_type":'GLOBAL',
    "orient_matrix":((1, 0, 0), (0, 1, 0),(0, 0, 1)),
    "orient_matrix_type":'GLOBAL',
    "constraint_axis":(False, False, False),
    "mirror":False,
    "use_proportional_edit":False,
    "proportional_edit_falloff":'SMOOTH',
    "proportional_size":1,
    "use_proportional_connected":False,
    "use_proportional_projected":False,
    "snap":False,
    "snap_elements":{'INCREMENT'},
    "use_snap_project":False,
    "snap_target":'CLOSEST',
    "use_snap_self":True,
    "use_snap_edit":True,
    "use_snap_nonedit":True,
    "use_snap_selectable":False,
    "snap_point":(0, 0, 0),
    "snap_align":False,
    "snap_normal":(0, 0, 0),
    "gpencil_strokes":False,
    "cursor_transform":False,
    "texture_space":False,
    "remove_on_cancel":False,
    "use_duplicated_keyframes":False,
    "view2d_edge_pan":False,
    "release_confirm":False,
    "use_accurate":False,
    "use_automerge_and_split":False})

    #Handle naming collisions
    for bone in edit_bones:
        if bone.select:
            bone.name = bone.name + "_FK"
            if ".001" in bone.name:
                bone.name = bone.name.replace(".001","")
                if "end" in bone.name.lower():
                    edit_bones.remove(bone) #Remove useless controller bones


    bpy.ops.object.mode_set(mode='POSE',toggle=False)

    selection_names = bpy.context.active_object.pose.bones

    bpy.ops.pose.select_all(action='DESELECT')

    #Change to custom shape
    for pose_bone in pose_bones:
        bone = armature.data.bones[pose_bone.name]
        #Change Shape
        if "FK" in pose_bone.name:
            #Change Color
            bone.color.palette = 'THEME09'
            #Switch of deform for FK bones
            bone.use_deform = False
            #Show controlls in front
            armature.show_in_front = True
            
            if "spine" in pose_bone.name.lower():
                pose_bone.custom_shape = bpy.data.objects["Circle"]
            elif "hips" in pose_bone.name.lower() or "root" in pose_bone.name.lower():
                pose_bone.custom_shape = bpy.data.objects["Plane"]
            else:
                pose_bone.custom_shape = bpy.data.objects["Cube"]
        else:
            bone.select = True
            #Skip adding constraints to end bones
            if "end" in pose_bone.name.lower():
                continue
            
            #Add constraint to deform armature
            constraint = pose_bone.constraints.new(type='COPY_TRANSFORMS')
            constraint.target = armature
            constraint.subtarget = pose_bone.name + "_FK"

    #Hide non FK bones
    #Create new bone collections and assign them
    bpy.ops.armature.collection_create_and_assign(name='Deform')
    armature.data.collections_all["Deform"].is_visible = False
    bpy.ops.pose.select_all(action='INVERT')
    bpy.ops.armature.collection_create_and_assign(name='FK')

    #Reset to Pose Position
    bpy.context.object.data.pose_position = 'POSE'

    bpy.ops.pose.select_all(action='DESELECT')
    
#START
#create_fk_controls()
