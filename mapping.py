import bpy
from bl_operators.presets import AddPresetBase
from .utilfuncs import get_state, get_similar_bone, alert_error, bin_reverse_at

def draw_panel(layout):
    s = get_state()
    
    row = layout.row()
    row.label(text='编辑骨骼映射表:', icon='TOOL_SETTINGS')
    # row.prop(s, 'editing_mappings', text="编辑细节", toggle=True)
    row.operator('kumopult_bac.select_edit_type', icon='PRESET', emboss=True, depress=s.editing_type==0).selected_type = 0
    row.operator('kumopult_bac.select_edit_type', icon='CON_ROTLIKE', emboss=True, depress=s.editing_type==1).selected_type = 1
    row.operator('kumopult_bac.select_edit_type', icon='CON_LOCLIKE', emboss=True, depress=s.editing_type==2).selected_type = 2
    row.operator('kumopult_bac.select_edit_type', icon='CON_KINEMATIC', emboss=True, depress=s.editing_type==3).selected_type = 3

    row = layout.row()
    row.template_list('BAC_UL_mappings', '', s, 'mappings', s, 'active_mapping')
    col = row.column(align=True)
    col.operator('kumopult_bac.list_action', icon='ADD', text='').action = 'ADD'
    col.operator('kumopult_bac.list_action', icon='REMOVE', text='').action = 'REMOVE'
    col.operator('kumopult_bac.list_action', icon='TRIA_UP', text='').action = 'UP'
    col.operator('kumopult_bac.list_action', icon='TRIA_DOWN', text='').action = 'DOWN'
    col.separator()
    col.operator('kumopult_bac.child_mapping', icon='CON_CHILDOF', text='')
    col.operator('kumopult_bac.name_mapping', icon='CON_TRANSFORM_CACHE', text='')

def add_mapping_below(owner, target):
    s = get_state()
    if not s.add_mapping(owner, target):
        return
    s.mappings.move(len(s.mappings) - 1, s.active_mapping + 1)
    s.active_mapping += 1

class BAC_UL_mappings(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):
        s = get_state()
        selected = s.selected_mapping & (1 << index) != 0
        layout.alert = not item.is_valid() # 该mapping无效时警告
        layout.active = selected or s.selected_mapping == 0
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
        right.operator('kumopult_bac.select_mapping', text='', emboss=False, icon='CHECKBOX_HLT' if selected else 'CHECKBOX_DEHLT').index = index
        

    def draw_filter(self, context, layout):
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
        if s.selected_mapping & (1 << self.index) == 0:
            s.selected_mapping |= (1 << self.index)
        else:
            s.selected_mapping &= ~ (1 << self.index)
        # s.selected_mapping = bin_reverse_at(s.selected_mapping, self.index)

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
                    s.add_mapping_below(b.name, '')
            else:
                s.add_mapping_below('', '')
        
        def remove():
            if len(s.mappings) > 0:
                s.remove_mapping(s.active_mapping)
                s.active_mapping =  min(s.active_mapping, len(s.mappings) - 1)
        
        def up():
            if s.active_mapping > 0:
                s.mappings.move(s.active_mapping, s.active_mapping - 1)
                s.active_mapping -= 1
        
        def down():
            if len(s.mappings) > s.active_mapping + 1:
                s.mappings.move(s.active_mapping, s.active_mapping + 1)
                s.active_mapping += 1
        
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
    bl_description = '在选中了某一对源和目标后，如果两者都仅有唯一的子级，则可以快捷地让这对子级建立新的映射关系'
    
    def child_mapping(self):
        s = get_state()
        m = s.get_active_mapping()
        target_children = s.get_target_armature().bones[m.target].children
        owner_children = s.get_owner_armature().bones[m.owner].children
        
        if len(target_children) == len(owner_children) == 1:
            s.add_mapping_below(owner_children[0].name, target_children[0].name)
            # 递归调用，实现连锁对应
            # self.child_mapping()
        else:
            for i in range(0, len(owner_children)):
                s.add_mapping_below(owner_children[i].name, '')
    
    def execute(self, context):
        s = get_state()
        m = s.get_active_mapping()
        if m.is_valid():
            self.child_mapping()
        else:
            self.report({"ERROR"}, "所选映射不完整")
            
        return {'FINISHED'}

class BAC_OT_NameMapping(bpy.types.Operator):
    bl_idname = 'kumopult_bac.name_mapping'
    bl_label = '名称映射'
    bl_description = '按照名称的相似程度来给目标骨骼自动寻找最接近的源骨骼，不怎么准，慎用'

    def execute(self, context):
        s = get_state()
        m = s.get_active_mapping()

        if m.get_owner():
            m.target = get_similar_bone(m.owner, s.get_target_armature().bones)
        else:
            self.report({"ERROR"}, "未选择目标骨骼")

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
    BAC_OT_ListAction,
    BAC_OT_ChildMapping,
    BAC_OT_NameMapping,
    BAC_OT_Bake,
    BAC_OT_BakeCollection,
    )