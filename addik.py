import bpy,math,re
from mathutils import Vector

def clean_input_string(input):
    pattern = r'[^a-zA-Z0-9_]'
    cleaned_string = re.sub(pattern,'_', input)
    cleaned_string = re.sub(r'__+',"_", cleaned_string)
    cleaned_string = cleaned_string.strip('_')
    return cleaned_string

def create_custom_property_switch(armature, property_name):
    
    armature.data[property_name] = 1
    property = armature.data.id_properties_ensure()
    property = armature.data.id_properties_ui(property_name)

    property.update(
        min=0,
        max=1,
        description="Switch between IK and FK"
    )

def add_driver_on(armature, driver_property, driven_obj, driven_property):
    driver = driven_obj.driver_add(driven_property).driver
    driver.type = 'SCRIPTED'
    
    var = driver.variables.new()
    cleaned_name = clean_input_string(driver_property)
    var.name = cleaned_name +"_IKFK_Switch"
    var.targets[0].id_type = 'ARMATURE'
    var.targets[0].id = armature.data
    var.targets[0].data_path = f'["{driver_property}"]'
    
    driver.expression = var.name
    
def add_driver_off(armature, driver_property, driven_obj, driven_property):
    driver = driven_obj.driver_add(driven_property).driver
    driver.type = 'SCRIPTED'

    var = driver.variables.new()
    cleaned_name = clean_input_string(driver_property)
    var.name = cleaned_name +"_IKFK_Switch"
    var.targets[0].id_type = 'ARMATURE'
    var.targets[0].id = armature.data
    var.targets[0].data_path = f'["{driver_property}"]'

    driver.expression = f"1 - {driver_property}"

def add_ik(bone_list, ik_chain_count, flipped_poles):
    bpy.ops.object.mode_set(mode='POSE')
    
    armature = bpy.context.object
    pose_bones = armature.pose.bones
    edit_bones = armature.data.edit_bones
    
    bone_name = bone_list[len(bone_list)-1]
    
    #Create IK/FK property
    property_name = "IKFKSWITCH"
    property_name = bone_name.replace("_IK","")
    property_name = property_name + "_IK_FK_Switch"
    create_custom_property_switch(armature, property_name)
    
    if bone_name in bpy.context.object.pose.bones:
        armature.data.bones.active = armature.data.bones[bone_name]
    else:
        print(f"ERROR: Bone '{bone_name}' not found.")
        return
    
    bpy.ops.pose.constraint_add(type='IK')
    
    bone_to_ik = pose_bones[bone_name]
    
    ik_constraint = bone_to_ik.constraints["IK"]
    
    ik_constraint.chain_count = ik_chain_count
    ik_constraint.use_tail = False
    
    #Deselect prior selection    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.armature.select_all(action='DESELECT')
    
    #Create new bone group for the IK bones
    collection = armature.data.collections.new(bone_list[len(bone_list)-1])
    
    
    #Create new control group if it does not already exist
    bone_groups = armature.data.collections
    ik_control_bone_collection = None
    for bone_group in bone_groups:
        if bone_group.name == "IK ControlBones":
            ik_control_bone_collection = bone_group
            
    if ik_control_bone_collection is None:
        ik_control_bone_collection = armature.data.collections.new("IK ControlBones")
    ik_control_bone_collection.is_visible = False
    
    #bone in the middle of the chain to use as pole target
    middle_bone_name = bone_list[math.floor(len(bone_list) / 2)]
    middle_bone = edit_bones[middle_bone_name]
    bone_to_copy = edit_bones[bone_to_ik.name]
    
    head_location = bone_to_ik.head.copy()
    tail_location = bone_to_ik.tail.copy()
    roll = edit_bones[bone_to_ik.name].roll
    
    target_bone_name = bone_name+"_Target"  
    target_bone = edit_bones.new(name=target_bone_name)  
    target_bone.head = head_location
    target_bone.tail = tail_location # + Vector((0,0,z_offset))
    target_bone.roll = roll
    collection.assign(target_bone)

    target_bone.color.palette = 'THEME01'
    target_bone.use_deform = False
    collection.assign(target_bone)
    
    z_offset = 15
    dist_from_bone = 60
    
    if flipped_poles:
        z_offset = -z_offset
        dist_from_bone = -dist_from_bone
    
    head_location = middle_bone.head.copy()
    tail_location = middle_bone.tail.copy()
    pole_bone_name = middle_bone.name+"_Pole"
    pole_bone = edit_bones.new(name=pole_bone_name)    
    pole_bone.head = head_location + Vector((0,0,dist_from_bone))
    pole_bone.tail = head_location + Vector((0,0,dist_from_bone + z_offset))
    pole_bone.color.palette = 'THEME01'
    pole_bone.use_deform = False
    collection.assign(pole_bone)
    
    ik_constraint.target = armature
    ik_constraint.subtarget = target_bone.name
    ik_constraint.pole_target = armature
    ik_constraint.pole_subtarget = pole_bone.name

    #Vector world pos variables
    ik_bone_pos = armature.matrix_world @ bone_to_ik.head
    target_pos = armature.matrix_world @ target_bone.head
    pole_pos = armature.matrix_world @ pole_bone.head
    
    #Calculate pole angle
    ik_dir = target_pos.normalized()
    pole_vector = (pole_pos - ik_bone_pos).normalized()
    cross_product = ik_dir.cross(pole_vector)
    dot_product = ik_dir.dot(pole_vector)
    angle = math.atan2(cross_product.length, dot_product) # inverse tangent function arctangent 
    ik_constraint.pole_angle = angle

    bpy.ops.object.mode_set(mode='POSE')
    
    #ADD custom shape to target one
    pose_bones[target_bone_name].custom_shape = bpy.data.objects["Cube"]
    
    #Wont work without changing this for some reason!?!
    ik_constraint.chain_count = ik_chain_count-1
    ik_constraint.chain_count = ik_chain_count
    
    #Change to custom shape
    for bone in pose_bones:
        bone_name = bone.name
        if "IK" in bone_name and bone_name in bone_list:
            bone.bone.color.palette = 'THEME01'
            bone.bone.use_deform = False
            bone.lock_ik_y = True
            bone.lock_ik_z = True
            
            bpy.ops.armature.collection_unassign_named(name="Deform",bone_name=bone_name)
            ik_control_bone_collection.assign(armature.data.bones[bone_name])
            #Delete possible constraints from IK control bones
            for constraint in bone.constraints:
                if not constraint.type == 'IK':
                    bone.constraints.remove(constraint)
                    
            if bone_list[len(bone_list)-1] == bone_name:
               rot_constraint = bone.constraints.new(type='COPY_TRANSFORMS')           
               rot_constraint.target = armature
               rot_constraint.subtarget = target_bone_name
            elif bone_list[0] == bone_name:
               loc_constraint = bone.constraints.new(type='CHILD_OF')           
               loc_constraint.target = armature
               loc_constraint.subtarget = bone.parent.name
               bpy.ops.object.mode_set(mode='EDIT')
               edit_bones[bone_name].parent = None
               bpy.ops.object.mode_set(mode='POSE')
        elif "FK" in bone_name or "end" in bone_name.lower():
            continue
        else:
            #ONLY ADD CONSTRAINTS TO BONES DRIVEN BY IK
            templist = []
            for tbone in bone_list:
                templist.append(tbone.replace("_IK",""))
            if bone_name in templist:
                constraint = bone.constraints.new(type='COPY_TRANSFORMS')
                constraint.target = armature
                constraint.subtarget = bone.name + "_IK"
                #Make FK constraints follow IK
                try: 
                    fk_bone = pose_bones[bone.name+"_FK"]
                    fk_constraint = fk_bone.constraints.new(type='COPY_TRANSFORMS')
                    fk_constraint.target = armature
                    fk_constraint.subtarget = bone.name + "_IK"
                    add_driver_on(armature,property_name,fk_constraint,"influence")
                except:
                    print("Error: No FK Bone found")
                    
                add_driver_on(armature,property_name,constraint,"influence")
    
    
    #Do stuff on bone after IK chain            
    last_bone_name = bone_list[-1].replace("_IK","")
    last_bone = pose_bones[last_bone_name]
    
    bpy.context.object.data.pose_position = 'POSE'

#START

def start_add_ik(ik_chain_count, bone_count_from_root, flipped_poles):
    #Push mesh to REST position
    bpy.ops.object.mode_set(mode='POSE',toggle=False)

    bpy.context.object.data.pose_position = 'REST'

    bpy.ops.object.mode_set(mode='EDIT',toggle=False)

    chain_count = bone_count_from_root

    bpy.ops.object.mode_set(mode='EDIT')

    if bpy.context.object.type == 'ARMATURE':
        
        armature = bpy.context.object.data
        selected_bones =[]
        
        for bone in armature.edit_bones:
            if bone.select:
                selected_bones.append(bone.name)
                bone.select = False
        
        #Select one bone or fail
        if len(selected_bones) == 1:
            print(f"SUCCESS: ")
            for index, child in enumerate(bpy.context.active_object.data.bones[selected_bones[0]].children_recursive):
                if index + 1 < chain_count:
                    selected_bones.append(child.name)
            
            #Fix out of bounds error if chain is to big
            if chain_count-1 > len(selected_bones):
                chain_count = len(selected_bones)
            
            bpy.ops.armature.select_all(action='DESELECT')
            
             #Handle naming collisions
            for bone in armature.edit_bones:
                if bone.name in selected_bones:
                    bone.select = True
                    bone.select_head = True
                    bone.select_tail = True
            
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
    
            ik_bones = []
            
            for bone in armature.edit_bones:
                if bone.select:                
                    bone.name += "_IK"
                    bone.name = bone.name.replace(".001","")
                    ik_bones.append(bone.name)
                  #  if selected_bones[0] in bone.name:
                  #      bpy.context.active_bone.parent = None
            add_ik(ik_bones,ik_chain_count,flipped_poles)

        else:
            print("ERROR: SELECT ONE BONE")
            
    else:
        print("PLEASE SELECT FIRST BONE IN IK CHAIN")
        