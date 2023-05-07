from fnmatch import translate

from numpy import true_divide
import bpy
from bl_operators.presets import AddPresetBase
from .utilfuncs import *
import difflib
import os

def draw_panel(layout):
    s = get_state()
    
    row = layout.row()
    left = row.column_flow(columns=1, align=True)
    box = left.box().row()
    # 全选/反选按钮
    if s.editing_type == 0:
        box_left = box.row(align=True)
        if s.selected_count == len(s.mappings):
            box_left.operator('kumopult_bac.select_action', text='', emboss=False, icon='CHECKBOX_HLT').action = 'NONE'
        else:
            box_left.operator('kumopult_bac.select_action', text='', emboss=False, icon='CHECKBOX_DEHLT').action = 'ALL'
            if s.selected_count != 0:
                # 反选按钮仅在选中部分时出现
                box_left.operator('kumopult_bac.select_action', text='', emboss=False, icon='UV_SYNC_SELECT').action = 'INVERSE'
    # 编辑模式切换
    box_right = box.row(align=False)
    box_right.alignment = 'RIGHT'
    box_right.operator('kumopult_bac.select_edit_type', text='' if s.editing_type!=0 else '映射', icon='PRESET', emboss=True, depress=s.editing_type==0).selected_type = 0
    box_right.operator('kumopult_bac.select_edit_type', text='' if s.editing_type!=1 else '旋转', icon='CON_ROTLIKE', emboss=True, depress=s.editing_type==1).selected_type = 1
    box_right.operator('kumopult_bac.select_edit_type', text='' if s.editing_type!=2 else '位移', icon='CON_LOCLIKE', emboss=True, depress=s.editing_type==2).selected_type = 2
    box_right.operator('kumopult_bac.select_edit_type', text='' if s.editing_type!=3 else 'ＩＫ', icon='CON_KINEMATIC', emboss=True, depress=s.editing_type==3).selected_type = 3
    # 映射列表
    left.template_list('BAC_UL_mappings', '', s, 'mappings', s, 'active_mapping', rows=7)
    # 预设菜单
    box = left.box().row(align=True)
    box.menu(BAC_MT_presets.__name__, text=BAC_MT_presets.bl_label, translate=False, icon='PRESET')
    box.operator(AddPresetBACMapping.bl_idname, text="", icon='ADD')
    box.operator(AddPresetBACMapping.bl_idname, text="", icon='REMOVE').remove_active=True
    box.separator()
    box.operator('kumopult_bac.open_preset_folder', text="", icon='FILE_FOLDER')

    right = row.column(align=True)
    right.separator()
    # 设置菜单
    right.menu(BAC_MT_SettingMenu.__name__, text='', icon='DOWNARROW_HLT')
    right.separator()
    # 列表操作按钮
    if s.owner.mode != 'POSE':
        right.operator('kumopult_bac.list_action', icon='ADD', text='').action = 'ADD'
    elif s.target.mode != 'POSE':
        right.operator('kumopult_bac.list_action', icon='PRESET_NEW', text='').action = 'ADD_SELECT'
    else:
        right.operator('kumopult_bac.list_action', icon='PLUS', text='').action = 'ADD_ACTIVE'
    right.operator('kumopult_bac.list_action', icon='REMOVE', text='').action = 'REMOVE'
    right.operator('kumopult_bac.list_action', icon='TRIA_UP', text='').action = 'UP'
    right.operator('kumopult_bac.list_action', icon='TRIA_DOWN', text='').action = 'DOWN'
    right.separator()
    right.operator('kumopult_bac.child_mapping', icon='CON_CHILDOF', text='')
    right.operator('kumopult_bac.name_mapping', icon='CON_TRANSFORM_CACHE', text='')
    right.operator('kumopult_bac.mirror_mapping', icon='MOD_MIRROR', text='')


class BAC_UL_mappings(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):
        s = get_state()
        layout.alert = not item.is_valid() # 该mapping无效时警告
        layout.active = item.selected or s.selected_count == 0
        row  = layout.row(align=True)

        def mapping():
            row.prop(item, 'selected', text='', emboss=False, icon='CHECKBOX_HLT' if item.selected else 'CHECKBOX_DEHLT')
            row.prop_search(item, 'selected_owner', s.get_owner_armature(), 'bones', text='', translate=False, icon='BONE_DATA')
            row.label(icon='BACK')
            row.prop_search(item, 'target', s.get_target_armature(), 'bones', text='', translate=False, icon='BONE_DATA')
        def rotation():
            row.prop(item, 'has_rotoffs', icon='CON_ROTLIKE', icon_only=True)
            layout.label(text=item.selected_owner, translate=False)
            if item.has_rotoffs:
                layout.prop(item, 'offset', text='')
        def location():
            row.prop(item, 'has_loccopy', icon='CON_LOCLIKE', icon_only=True)
            layout.label(text=item.selected_owner, translate=False)
            if item.has_loccopy:
                layout.row().prop(item, 'loc_axis', text='', toggle=True)
        def ik():
            row.prop(item, 'has_ik', icon='CON_KINEMATIC', icon_only=True)
            layout.label(text=item.selected_owner, translate=False)
            if item.has_ik:
                layout.prop(item, 'ik_influence', text='', slider=True)
        
        draw = {
            0: mapping,
            1: rotation,
            2: location,
            3: ik
        }

        draw[s.editing_type]()

    def draw_filter(self, context, layout):
        pass

    def filter_items(self, context, data, propname):
        flt_flags = []
        flt_neworder = []

        return flt_flags, flt_neworder


class BAC_MT_SettingMenu(bpy.types.Menu):
    bl_label = "Setting"

    def draw(self, context):
        s = get_state()
        layout = self.layout
        layout.prop(s, 'sync_select')
        layout.separator()
        layout.prop(s, 'calc_offset')
        layout.prop(s, 'ortho_offset')
        layout.separator()


class BAC_MT_presets(bpy.types.Menu):
    bl_label = "映射表预设"
    preset_subdir = "kumopult_bac"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset

class AddPresetBACMapping(AddPresetBase, bpy.types.Operator):
    bl_idname = "kumopult_bac.mappings_preset_add"
    bl_label = "添加预设 Add BAC Mappings Preset"
    bl_description = "将当前骨骼映射表保存为预设，以供后续直接套用"
    preset_menu = "BAC_MT_presets"

    # variable used for all preset values
    preset_defines = [
        "s = bpy.context.scene.kumopult_bac_owner.data.kumopult_bac"
    ]

    # properties to store in the preset
    preset_values = [
        "s.mappings",
        "s.selected_count"
    ]

    # where to store the preset
    preset_subdir = "kumopult_bac"

class BAC_OT_OpenPresetFolder(bpy.types.Operator):
    bl_idname = 'kumopult_bac.open_preset_folder'
    bl_label = '打开预设文件夹'

    def execute(self, context):
        os.system('explorer ' + bpy.utils.resource_path('USER') + '\scripts\presets\kumopult_bac')
        return {'FINISHED'}

class BAC_OT_SelectEditType(bpy.types.Operator):
    bl_idname = 'kumopult_bac.select_edit_type'
    bl_label = ''
    bl_description = '选择编辑列表类型'
    bl_options = {'UNDO'}

    selected_type: bpy.props.IntProperty(override={'LIBRARY_OVERRIDABLE'})

    def execute(self, context):
        s = get_state()
        s.editing_type = self.selected_type

        return {'FINISHED'}

class BAC_OT_SelectAction(bpy.types.Operator):
    bl_idname = 'kumopult_bac.select_action'
    bl_label = '列表选择操作'
    bl_description = '全选/弃选/反选'
    bl_options = {'UNDO'}

    action: bpy.props.StringProperty(override={'LIBRARY_OVERRIDABLE'})

    def execute(self, context):
        s = get_state()

        def all():
            for m in s.mappings:
                m.selected = True
            s.selected_count = len(s.mappings)
        
        def inverse():
            for m in s.mappings:
                m.selected = not m.selected

        def none():
            for m in s.mappings:
                m.selected = False
            s.selected_count = 0
        
        ops = {
            'ALL': all,
            'INVERSE': inverse,
            'NONE': none
        }

        ops[self.action]()

        return {'FINISHED'}



class BAC_OT_ListAction(bpy.types.Operator):
    bl_idname = 'kumopult_bac.list_action'
    bl_label = '列表基本操作'
    bl_description = '依次为新建、删除、上移、下移\n其中在姿态模式下选中骨骼并点击新建的话，\n可以自动填入对应骨骼'
    bl_options = {'UNDO'}

    action: bpy.props.StringProperty(override={'LIBRARY_OVERRIDABLE'})

    def execute(self, context):
        s = get_state()

        def add():
            # 普通add
            s.add_mapping('', '')
        
        def add_select():
            # 选中项add
            bone_names = []
            for bone in s.owner.data.bones:
                if bone.select:
                    bone_names.append(bone.name)
            if len(bone_names) > 0:
                for name in bone_names:
                    s.add_mapping(name, '')
            else:
                s.add_mapping('', '')
        
        def add_active():
            # 激活项add
            owner = s.owner.data.bones.active
            target = s.target.data.bones.active
            s.add_mapping(owner.name if owner != None else '', target.name if target != None else '')
        
        def remove():
            if len(s.mappings) > 0:
                s.remove_mapping()
        
        def up():
            if s.selected_count == 0:
                if len(s.mappings) > s.active_mapping > 0:
                    s.mappings.move(s.active_mapping, s.active_mapping - 1)
                    s.active_mapping -= 1
            else:
                move_indices = []
                for i in range(1, len(s.mappings)):
                    if s.mappings[i].selected:
                        move_indices.append(i)
                for i in move_indices:
                    if not s.mappings[i - 1].selected:
                        # 前一项未选中时才能前移
                        s.mappings.move(i, i - 1)
        
        def down():
            if s.selected_count == 0:
                if len(s.mappings) > s.active_mapping + 1 > 0:
                    s.mappings.move(s.active_mapping, s.active_mapping + 1)
                    s.active_mapping += 1
            else:
                move_indices = []
                for i in range(len(s.mappings) - 2, -1, -1):
                    if s.mappings[i].selected:
                        move_indices.append(i)
                for i in move_indices:
                    if not s.mappings[i + 1].selected:
                        # 后一项未选中时才能后移
                        s.mappings.move(i, i + 1)
        
        ops = {
            'ADD': add,
            'ADD_SELECT': add_select,
            'ADD_ACTIVE': add_active,
            'REMOVE': remove,
            'UP': up,
            'DOWN': down
        }

        ops[self.action]()

        return {'FINISHED'}

class BAC_OT_ChildMapping(bpy.types.Operator):
    bl_idname = 'kumopult_bac.child_mapping'
    bl_label = '子级映射'
    bl_description = '如果选中映射的目标骨骼和自身骨骼都有且仅有唯一的子级，则在那两个子级间建立新的映射'
    bl_options = {'UNDO'}
    
    execute_flag: bpy.props.BoolProperty(default=False, override={'LIBRARY_OVERRIDABLE'})

    @classmethod
    def poll(cls, context):
        ret = True
        s = get_state()
        if s == None:
            return False
        for i in s.get_selection():
            if not s.mappings[i].is_valid():
                ret = False
        return ret
    
    def child_mapping(self, index):
        s = get_state()
        m = s.mappings[index]
        if m.selected:
            m.selected = False
        target_children = s.get_target_armature().bones[m.target].children
        owner_children = s.get_owner_armature().bones[m.owner].children
        
        if len(target_children) == len(owner_children) == 1:
            s.add_mapping(owner_children[0].name, target_children[0].name, index + 1)[0].selected = True
            self.execute_flag = True
            # 递归调用，实现连锁对应
            # self.child_mapping()
        else:
            for i in range(0, len(owner_children)):
                s.add_mapping(owner_children[i].name, '', index + i + 1)[0].selected = True
                self.execute_flag = True
    
    def execute(self, context):
        s = get_state()
        self.execute_flag = False
        for i in s.get_selection():
            self.child_mapping(i)
        
        if not self.execute_flag:
            self.report({"ERROR"}, "所选项中没有可建立子级映射的映射")
            
        return {'FINISHED'}

class BAC_OT_NameMapping(bpy.types.Operator):
    bl_idname = 'kumopult_bac.name_mapping'
    bl_label = '名称映射'
    bl_description = '按照名称的相似程度来给自身骨骼自动寻找最接近的目标骨骼'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        ret = True
        s = get_state()
        if s == None:
            return False
        for i in s.get_selection():
            if s.mappings[i].get_owner() == None:
                ret = False
        return ret

    def get_similar_bone(self, owner_name, target_bones):
        similar_name = ''
        similar_ratio = 0

        for target in target_bones:
            r = difflib.SequenceMatcher(None, owner_name, target.name).quick_ratio()
            if r > similar_ratio:
                similar_ratio = r
                similar_name = target.name
        
        return similar_name

    def execute(self, context):
        s = get_state()

        for i in s.get_selection():
            m = s.mappings[i]
            m.target = self.get_similar_bone(m.owner, s.get_target_armature().bones)

        return {'FINISHED'}

class BAC_OT_MirrorMapping(bpy.types.Operator):
    bl_idname = 'kumopult_bac.mirror_mapping'
    bl_label = '镜像映射'
    bl_description = '如果选中映射的目标骨骼和自身骨骼都有与之对称的骨骼，则在那两个对称骨骼间建立新的映射'
    bl_options = {'UNDO'}

    execute_flag: bpy.props.BoolProperty(default=False, override={'LIBRARY_OVERRIDABLE'})

    @classmethod
    def poll(cls, context):
        ret = True
        s = get_state()
        if s == None:
            return False
        for i in s.get_selection():
            if not s.mappings[i].is_valid():
                ret = False
        return ret

    def mirror_mapping(self, index):
        s = get_state()
        m = s.mappings[index]
        if m.selected:
            m.selected = False
        owner_mirror = s.get_owner_pose().bones.get(bpy.utils.flip_name(m.owner))
        target_mirror = s.get_target_pose().bones.get(bpy.utils.flip_name(m.target))
        if owner_mirror != None and target_mirror != None:
            new_mapping = s.add_mapping(owner_mirror.name, target_mirror.name, index=index + 1)[0]
            new_mapping.selected = True
            self.execute_flag = True

    def execute(self, context):
        s = get_state()
        self.execute_flag = False

        for i in s.get_selection():
            self.mirror_mapping(i)
        
        if not self.execute_flag:
            self.report({"ERROR"}, "所选项中没有可镜像的映射")

        return {'FINISHED'}

class BAC_OT_Bake(bpy.types.Operator):
    bl_idname = 'kumopult_bac.bake'
    bl_label = '烘培动画'
    bl_description = '根据来源骨架上动作的帧范围将约束效果烘培为新的动作片段\n本质上是在调用姿态=>动画=>烘焙动作这一方法,并自动设置一些参数\n注意这会让本插件所生成约束以外的约束也被烘焙'
    bl_options = {'UNDO'}

    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = bpy.context.scene.kumopult_bac_owner
        bpy.context.object.select_set(True)

        s = get_state()
        a = s.target.animation_data

        if not a:
            # 先确保源骨架上有动作
            alert_error('源骨架上没有动作！', '确保有动作的情况下才能自动判断烘培的帧范围')
            return {'FINISHED'}
        else:
            # 选中约束的骨骼
            bpy.ops.object.mode_set(mode='POSE')
            bpy.ops.pose.select_all(action='DESELECT')
            for m in s.mappings:
                s.get_owner_armature().bones.get(m.owner).select = True
            # 打开约束进行烘培再关掉
            s.preview = True
            bpy.ops.nla.bake(
                frame_start=int(a.action.frame_range[0]),
                frame_end=int(a.action.frame_range[1]),
                only_selected=True,
                visual_keying=True,
                bake_types={'POSE'}
            )
            s.preview = False
            #重命名动作、添加伪用户
            s.owner.animation_data.action.name = s.target.name
            s.owner.animation_data.action.use_fake_user = True
            return {'FINISHED'}


classes = (
    BAC_UL_mappings,
    BAC_MT_SettingMenu, 
    BAC_MT_presets,
    AddPresetBACMapping,

    BAC_OT_OpenPresetFolder,
    BAC_OT_SelectEditType,
    BAC_OT_SelectAction,
    BAC_OT_ListAction,
    BAC_OT_ChildMapping,
    BAC_OT_NameMapping,
    BAC_OT_MirrorMapping,
    BAC_OT_Bake,
    )