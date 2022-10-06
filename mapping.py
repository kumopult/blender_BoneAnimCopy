import bpy
from bl_operators.presets import AddPresetBase
from .utilfuncs import *
import difflib

def draw_panel(layout):
    s = get_state()
    
    row = layout.row()
    left = row.column_flow(columns=1, align=True)
    box = left.box().row()
    box_left = box.row(align=False)
    box_left.alignment = 'LEFT'
    box_left.operator('kumopult_bac.select_edit_type', text='' if s.editing_type!=0 else '映射', icon='PRESET', emboss=True, depress=s.editing_type==0).selected_type = 0
    box_left.operator('kumopult_bac.select_edit_type', text='' if s.editing_type!=1 else '旋转', icon='CON_ROTLIKE', emboss=True, depress=s.editing_type==1).selected_type = 1
    box_left.operator('kumopult_bac.select_edit_type', text='' if s.editing_type!=2 else '位移', icon='CON_LOCLIKE', emboss=True, depress=s.editing_type==2).selected_type = 2
    box_left.operator('kumopult_bac.select_edit_type', text='' if s.editing_type!=3 else 'ＩＫ', icon='CON_KINEMATIC', emboss=True, depress=s.editing_type==3).selected_type = 3

    box_right = box.row(align=True)
    box_right.alignment = 'RIGHT'
    if s.selected_count == len(s.mappings):
        box_right.operator('kumopult_bac.select_action', text='', emboss=False, icon='CHECKBOX_HLT').action = 'NONE'
    else:
        if s.selected_count != 0:
            # 反选按钮仅在选中部分时出现
            box_right.operator('kumopult_bac.select_action', text='', emboss=False, icon='UV_SYNC_SELECT').action = 'INVERSE'
        box_right.operator('kumopult_bac.select_action', text='', emboss=False, icon='CHECKBOX_DEHLT').action = 'ALL'

    left.template_list('BAC_UL_mappings', '', s, 'mappings', s, 'active_mapping', rows=7)

    right = row.column(align=True)
    right.separator()
    right.label(icon='HEART')
    right.separator()
    right.operator('kumopult_bac.list_action', icon='ADD', text='').action = 'ADD'
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
        left  = layout.row(align=True)
        right = layout.row(align=True)
        right.alignment = 'RIGHT'
        # 左侧为mapping信息
        if not item.get_owner():
            left.label(icon='ZOOM_IN')
            left.prop_search(item, 'selected_owner', s.get_owner_armature(), 'bones', text='')
        else:
            def mapping():
                left.prop_search(item, 'selected_owner', s.get_owner_armature(), 'bones', text='', icon='BONE_DATA')
                left.label(icon='BACK')
                left.prop_search(item, 'target', s.get_target_armature(), 'bones', text='', icon='BONE_DATA')
            def rotation():
                left.prop(item, 'has_rotoffs', icon='CON_ROTLIKE', icon_only=True)
                left.label(text=item.selected_owner)
                left.separator(factor=0.5)
                if item.has_rotoffs:
                    left.prop(item, 'offset', text='')
            def location():
                left.prop(item, 'has_loccopy', icon='CON_LOCLIKE', icon_only=True)
                left.label(text=item.selected_owner)
                left.separator(factor=0.5)
                if item.has_loccopy:
                    left.prop(item.get_cp(), 'use_x', text='X', toggle=True)
                    left.prop(item.get_cp(), 'use_y', text='Y', toggle=True)
                    left.prop(item.get_cp(), 'use_z', text='Z', toggle=True)
            def ik():
                left.prop(item, 'has_ik', icon='CON_KINEMATIC', icon_only=True)
                left.label(text=item.selected_owner)
                left.separator(factor=0.1)
                if item.has_ik:
                    left.prop(item.get_ik(), 'influence')
            
            draw = {
                0: mapping,
                1: rotation,
                2: location,
                3: ik
            }

            draw[s.editing_type]()
        # 右侧为选择按钮
        right.operator('kumopult_bac.select_mapping', text='', emboss=False, icon='CHECKBOX_HLT' if item.selected else 'CHECKBOX_DEHLT').index = index
        

    def draw_filter(self, context, layout):
        row = layout.row()
        row.menu(BAC_MT_presets.__name__, text=BAC_MT_presets.bl_label, icon='PRESET')
        row.operator(AddPresetBACMapping.bl_idname, text="", icon='ADD')
        row.operator(AddPresetBACMapping.bl_idname, text="", icon='REMOVE').remove_active=True
        pass

    def filter_items(self, context, data, propname):
        flt_flags = []
        flt_neworder = []

        return flt_flags, flt_neworder

class BAC_MT_presets(bpy.types.Menu):
    bl_label = "Mapping预设"
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
        "s = bpy.context.object.kumopult_bac"
    ]

    # properties to store in the preset
    preset_values = [
        "s.mappings"
        "s.selected_count"
    ]

    # where to store the preset
    preset_subdir = "kumopult_bac"

class BAC_OT_SelectEditType(bpy.types.Operator):
    bl_idname = 'kumopult_bac.select_edit_type'
    bl_label = ''
    bl_description = '选择编辑列表类型'

    selected_type: bpy.props.IntProperty()

    def execute(self, context):
        s = get_state()
        s.editing_type = self.selected_type

        return {'FINISHED'}

class BAC_OT_SelectMapping(bpy.types.Operator):
    bl_idname = 'kumopult_bac.select_mapping'
    bl_label = ''
    bl_description = ''

    index: bpy.props.IntProperty()

    def execute(self, context):
        s = get_state()
        s.set_select(self.index, not s.mappings[self.index].selected)

        return {'FINISHED'}

class BAC_OT_SelectAction(bpy.types.Operator):
    bl_idname = 'kumopult_bac.select_action'
    bl_label = '列表选择操作'
    bl_description = '依次为全选、反选、弃选'

    action: bpy.props.StringProperty()

    def execute(self, context):
        s = get_state()

        def all():
            for i in range(len(s.mappings)):
                s.set_select(i, True)
        
        def inverse():
            for i in range(len(s.mappings)):
                s.set_select(i, not s.mappings[i].selected)

        def none():
            for i in range(len(s.mappings)):
                s.set_select(i, False)
        
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

    action: bpy.props.StringProperty()

    def execute(self, context):
        s = get_state()

        def add():
            #这里需要加一下判断，如果有选中的骨骼则自动填入owner
            pb = bpy.context.selected_pose_bones_from_active_object
            if pb != None and len(pb) > 0:
                for b in pb:
                    s.add_mapping(b.name, '')
            else:
                s.add_mapping('', '')
        
        def remove():
            if len(s.mappings) > 0:
                s.remove_mapping()
        
        def up():
            move_indices = []
            if s.selected_count == 0:
                if len(s.mappings) > s.active_mapping > 0:
                    move_indices.append(s.active_mapping)
                    s.active_mapping -= 1
            else:
                for i in range(1, len(s.mappings)):
                    if s.mappings[i].selected:
                        move_indices.append(i)
            
            for i in move_indices:
                if not s.mappings[i - 1].selected:
                    # 前一项未选中时才能前移
                    s.mappings.move(i, i - 1)
        
        def down():
            move_indices = []
            if s.selected_count == 0:
                if len(s.mappings) > s.active_mapping + 1 > 0:
                    move_indices.append(s.active_mapping)
                    s.active_mapping += 1
            else:
                for i in range(len(s.mappings) - 2, -1, -1):
                    if s.mappings[i].selected:
                        move_indices.append(i)
            
            for i in move_indices:
                if not s.mappings[i + 1].selected:
                    # 后一项未选中时才能后移
                    s.mappings.move(i, i + 1)
        
        ops = {
            'ADD': add,
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
    
    execute_flag: bpy.props.BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        ret = True
        s = get_state()
        for i in s.get_selection():
            if not s.mappings[i].is_valid():
                ret = False
        return ret
    
    def child_mapping(self, index):
        s = get_state()
        m = s.mappings[index]
        s.set_select(index, False)
        target_children = s.get_target_armature().bones[m.target].children
        owner_children = s.get_owner_armature().bones[m.owner].children
        
        if len(target_children) == len(owner_children) == 1:
            child_index = s.add_mapping(owner_children[0].name, target_children[0].name, index + 1)[1]
            s.set_select(child_index, True)
            self.execute_flag = True
            # 递归调用，实现连锁对应
            # self.child_mapping()
        else:
            for i in range(0, len(owner_children)):
                child_index = s.add_mapping(owner_children[i].name, '', index + i + 1)[1]
                s.set_select(child_index, True)
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

    @classmethod
    def poll(cls, context):
        ret = True
        s = get_state()
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

    execute_flag: bpy.props.BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        ret = True
        s = get_state()
        for i in s.get_selection():
            if not s.mappings[i].is_valid():
                ret = False
        return ret

    def mirror_mapping(self, index):
        s = get_state()
        m = s.mappings[index]
        s.set_select(index, False)
        owner_mirror = s.get_owner_pose().bones.get(bpy.utils.flip_name(m.owner))
        target_mirror = s.get_target_pose().bones.get(bpy.utils.flip_name(m.target))
        if owner_mirror != None and target_mirror != None:
            self.execute_flag = True
            mirror_index = s.add_mapping(owner_mirror.name, target_mirror.name, index=index + 1)[1]
            s.set_select(mirror_index, True)

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
    bl_description = '根据来源骨架上动作的帧范围将约束效果烘培为新的动作片段'

    def execute(self, context):
        bpy.context.object.select_set(True)
        s = get_state()
        a = s.target.animation_data

        if not a:
            # 先确保源骨架上有动作
            alert_error('源骨架上没有动作！', '确保有动作的情况下才能自动判断烘培的帧范围')
            return {'FINISHED'}
        else:
            # 打开约束进行烘培再关掉
            s.preview = True
            bpy.ops.nla.bake(
                frame_start=int(a.action.frame_range[0]),
                frame_end=int(a.action.frame_range[1]),
                only_selected=False,
                visual_keying=True,
                bake_types={'POSE'}
            )
            s.preview = False
            #重命名动作、添加伪用户
            s.owner.animation_data.action.name = s.target.name
            s.owner.animation_data.action.use_fake_user = True
            return {'FINISHED'}

class BAC_OT_BakeCollection(bpy.types.Operator):
    bl_idname = 'kumopult_bac.bake_collection'
    bl_label = '批量烘培动画'
    bl_description = '将来源骨架所在集合中所有骨架的动画批量烘培至来源骨骼上\n仅适用于所有来源骨架都可以套用同一套映射预设的情况！'

    def execute(self, context):
        s = get_state()

        def get_collection(name):
            # 查找指定名字的物体在哪个集合中
            for c in bpy.data.collections:
                if c.objects.get(name):
                    return c
            alert_error('找不到对象', '要查找的对象不在任一集合中！')
        
        for a in get_collection(s.target.name).objects:
            if a.type != 'ARMATURE':
                continue
            s.selected_target = a
            bpy.ops.kumopult_bac.bake()
        
        return {'FINISHED'}



classes = (
    BAC_UL_mappings,
    BAC_MT_presets,
    AddPresetBACMapping,
    
    BAC_OT_SelectEditType,
    BAC_OT_SelectMapping,
    BAC_OT_SelectAction,
    BAC_OT_ListAction,
    BAC_OT_ChildMapping,
    BAC_OT_NameMapping,
    BAC_OT_MirrorMapping,
    BAC_OT_Bake,
    BAC_OT_BakeCollection,
    )