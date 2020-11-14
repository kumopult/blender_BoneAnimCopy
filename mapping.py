import bpy
from bl_operators.presets import AddPresetBase
from .utilfuncs import get_state, get_similar_bone

def draw_panel(layout):
    s = get_state()
    
    row = layout.row()
    row.label(text='Edit Bone Mappings:', icon='TOOL_SETTINGS')
    # row.prop(s, 'editing_mappings', text="编辑细节", toggle=True)
    row.operator('kumopult_bac.select_edit_type', icon='PRESET', emboss=True, depress=s.editing_type==0).selected_type = 0
    row.operator('kumopult_bac.select_edit_type', icon='CON_ROTLIKE', emboss=True, depress=s.editing_type==1).selected_type = 1
    row.operator('kumopult_bac.select_edit_type', icon='CON_LOCLIKE', emboss=True, depress=s.editing_type==2).selected_type = 2
    row.operator('kumopult_bac.select_edit_type', icon='CON_KINEMATIC', emboss=True, depress=s.editing_type==3).selected_type = 3

    row = layout.row()
    row.template_list('BAC_UL_mappings', '', s, 'mappings', s, 'active_mapping')
    col = row.column(align=True)
    col.operator('kumopult_bac.list_action', icon='ADD').action = 'ADD'
    col.operator('kumopult_bac.list_action', icon='REMOVE').action = 'REMOVE'
    col.operator('kumopult_bac.list_action', icon='TRIA_UP').action = 'UP'
    col.operator('kumopult_bac.list_action', icon='TRIA_DOWN').action = 'DOWN'
    col.separator()
    col.operator('kumopult_bac.child_mapping', icon='CON_CHILDOF', text='',)
    col.operator('kumopult_bac.name_mapping', icon='CON_TRANSFORM_CACHE', text='',)

def add_mapping_below(target, source):
    s = get_state()
    if not s.add_mapping(target, source):
        return
    s.mappings.move(len(s.mappings) - 1, s.active_mapping + 1)
    s.active_mapping += 1

class BAC_UL_mappings(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):
        s = get_state()
        layout.alert = not item.is_valid() # 该mapping无效时警告
        if not item.target_valid():
            layout.label(icon='ZOOM_IN')
            layout.prop_search(item, 'selected_target', s.get_target_armature(), 'bones', text='')
        else:
            def mapping():
                layout.prop_search(item, 'selected_target', s.get_target_armature(), 'bones', text='', icon='BONE_DATA')
                layout.label(icon='BACK')
                layout.prop_search(item, 'source', s.get_source_armature(), 'bones', text='', icon='BONE_DATA')
            def rotation():
                layout.prop(item, 'has_rotoffs', icon='CON_ROTLIKE', icon_only=True)
                layout.label(text=item.selected_target)
                layout.separator(factor=0.5)
                if item.has_rotoffs:
                    layout.prop(item, 'offset', text='')
            def location():
                layout.prop(item, 'has_loccopy', icon='CON_LOCLIKE', icon_only=True)
                layout.label(text=item.selected_target)
                layout.separator(factor=0.5)
                if item.has_loccopy:
                    layout.prop(item.get_cp(), 'use_x', text='X', toggle=True)
                    layout.prop(item.get_cp(), 'use_y', text='Y', toggle=True)
                    layout.prop(item.get_cp(), 'use_z', text='Z', toggle=True)
            def ik():
                layout.prop(item, 'has_ik', icon='CON_KINEMATIC', icon_only=True)
                layout.label(text=item.selected_target)
                layout.separator(factor=0.1)
                if item.has_ik:
                    layout.prop(item.get_ik(), 'influence')
            
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

class BAC_MT_presets(bpy.types.Menu):
    bl_label = "Mapping预设"
    preset_subdir = "kumopult_bac"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset

class AddPresetBACMapping(AddPresetBase, bpy.types.Operator):
    bl_idname = "kumopult_bac.mappings_preset_add"
    bl_label = "Add BAC Mappings Preset"
    preset_menu = "BAC_MT_presets"

    # variable used for all preset values
    preset_defines = [
        "s = bpy.context.object.kumopult_bac"
    ]

    # properties to store in the preset
    preset_values = [
        "s.mappings",
    ]

    # where to store the preset
    preset_subdir = "kumopult_bac"

'''
先前两个分开显示的列表，现已整合到一起
class BAC_UL_mappings(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):
        s = get_state()
        layout.alert = not item.is_valid()
        layout.prop_search(item, 'target', s.get_target_armature(), 'bones', text='', icon='BONE_DATA')
        layout.label(icon='BACK')
        layout.prop_search(item, 'source', s.get_source_armature(), 'bones', text='', icon='BONE_DATA')

    def draw_filter(self, context, layout):
        pass

    def filter_items(self, context, data, propname):
        flt_flags = []
        flt_neworder = []

        return flt_flags, flt_neworder
    
    
class BAC_UL_constraints(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):
        s = get_state()
        layout.alert = not item.is_valid()
        layout.label(text=item.target, icon='BONE_DATA')
        layout.label(icon='FORWARD')
        layout.prop(item.get_rr(), 'to_min_y_rot', text='')

    def draw_filter(self, context, layout):
        pass

    def filter_items(self, context, data, propname):
        flt_flags = []
        flt_neworder = []

        return flt_flags, flt_neworder
'''

class BAC_OT_SelectEditType(bpy.types.Operator):
    bl_idname = 'kumopult_bac.select_edit_type'
    bl_label = ''
    bl_description = '选择编辑列表类型'
    selected_type: bpy.props.IntProperty()

    def execute(self, context):
        s = get_state()
        s.editing_type = self.selected_type

        return {'FINISHED'}

class BAC_OT_ListAction(bpy.types.Operator):
    bl_idname = 'kumopult_bac.list_action'
    bl_label = ''
    bl_description = '列表基本操作，依次为新建、删除、上移、下移\n其中在姿态模式下选中骨骼并点击新建的话，\n可以自动填入对应骨骼'
    action: bpy.props.StringProperty()

    def execute(self, context):
        s = get_state()

        def add():
            #这里需要加一下判断，如果有选中的骨骼则自动填入target
            pb = bpy.context.selected_pose_bones_from_active_object
            if pb != None and len(pb) > 0:
                for b in pb:
                    add_mapping_below(b.name, '')
            else:
                add_mapping_below('', '')
        
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
    bl_label = '在指定了某一对源和目标后，可以快捷地给两者的子级建立新的对应关系'
    
    def child_mapping(self):
        s = get_state()
        m = s.get_active_mapping()
        source_children = s.get_source_armature().bones[m.source].children
        target_children = s.get_target_armature().bones[m.target].children
        
        if len(source_children) == len(target_children) == 1:
            add_mapping_below(target_children[0].name, source_children[0].name)
            # 递归调用，实现连锁对应
            # self.child_mapping()
        else:
            for i in range(0, len(target_children)):
                add_mapping_below(target_children[i].name, '')
    
    def execute(self, context):
        s = get_state()
        m = s.get_active_mapping()
        if m.is_valid():
            self.child_mapping()
        else:
            self.report({"ERROR"}, "所选mapping不完整")
            
        return {'FINISHED'}

class BAC_OT_NameMapping(bpy.types.Operator):
    bl_idname = 'kumopult_bac.name_mapping'
    bl_label = '指定目标骨骼后，根据最相似的骨骼名称来建立对应关系'

    def execute(self, context):
        s = get_state()
        m = s.get_active_mapping()

        if m.target_valid:
            m.source = get_similar_bone(m.target, s.get_source_armature().bones)
        else:
            self.report({"ERROR"}, "未选择目标骨骼")

        return {'FINISHED'}

'''
class BAC_OT_Apply(bpy.types.Operator):
    bl_idname = 'kumopult_bac.constraint_apply'
    bl_label = 'Apply'
    
    def execute(self, context):
        # exit the edit mode, build or adjust the constraint by mappings
        s = get_state()
        s.editing_mappings = False
        
        for mapping in s.mappings:
            if mapping.is_valid():
                mapping.apply()
            
        return {'FINISHED'}
    
    
class BAC_OT_Edit(bpy.types.Operator):
    bl_idname = 'kumopult_bac.constraint_edit'
    bl_label = 'Edit'
    
    def execute(self, context):
        # enter the edit mode, save the roll value
        s = get_state()
        s.editing_mappings = True
        
        for mapping in s.mappings:
            if mapping.is_valid():
                mapping.save()
            
        return {'FINISHED'}
'''

classes = (
    BAC_UL_mappings,
    BAC_MT_presets,
    AddPresetBACMapping,
    
    BAC_OT_SelectEditType,
    BAC_OT_ListAction,
    BAC_OT_ChildMapping,
    BAC_OT_NameMapping
    )