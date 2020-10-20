import bpy
from .utilfuncs import get_state, get_similar_bone

def draw_panel(layout):
    s = get_state()
    
    row = layout.row()
    row.label(text='Edit Bone Mappings:', icon='TOOL_SETTINGS')
    row.prop(s, 'editing_mappings', text="编辑细节", toggle=True)

    row = layout.row()
    row.template_list('BAC_UL_mappings', '', s, 'mappings', s, 'active_mapping')
    col = row.column(align=True)
    col.operator('kumopult_bac.list_action', icon='ADD', text='').action = 'ADD'
    col.operator('kumopult_bac.list_action', icon='REMOVE', text='').action = 'REMOVE'
    col.operator('kumopult_bac.list_action', icon='TRIA_UP', text='').action = 'UP'
    col.operator('kumopult_bac.list_action', icon='TRIA_DOWN', text='').action = 'DOWN'
    col.separator()
    col.operator('kumopult_bac.child_mapping', icon='CON_CHILDOF', text='',)
    col.operator('kumopult_bac.name_mapping', icon='CON_TRANSFORM_CACHE', text='',)

def add_mapping_below(target, source):
    s = get_state()
    s.add_mapping(target, source)
    s.mappings.move(len(s.mappings) - 1, s.active_mapping + 1)
    s.active_mapping += 1

class BAC_UL_mappings(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):
        s = get_state()
        layout.alert = not item.is_valid() # 该mapping无效时警告
        layout.prop_search(item, 'selected_target', s.get_target_armature(), 'bones', text='', icon='BONE_DATA')
        if not item.target_valid():
            layout.label(icon='BONE_DATA')
        else:
            if not s.editing_mappings:
                layout.label(icon='BACK')
                layout.prop_search(item, 'source', s.get_source_armature(), 'bones', text='', icon='BONE_DATA')
            else:
                layout.separator(factor=0.5)
                if item.has_rotoffs:
                    layout.prop(item, 'offset', text='')
                layout.prop(item, 'has_rotoffs', icon='CON_ROTLIKE', icon_only=True)
                layout.prop(item, 'has_loccopy', icon='CON_LOCLIKE', icon_only=True)

    def draw_filter(self, context, layout):
        pass

    def filter_items(self, context, data, propname):
        flt_flags = []
        flt_neworder = []

        return flt_flags, flt_neworder


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


class BAC_OT_ListAction(bpy.types.Operator):
    bl_idname = 'kumopult_bac.list_action'
    bl_label = '列表基本操作，依次为新建、删除、上移、下移\n其中在姿态模式下选中骨骼并点击新建的话，\n可以自动填入对应骨骼'
    action: bpy.props.StringProperty()

    def execute(self, context):
        s = get_state()

        if self.action == 'ADD':
            #这里需要加一下判断，如果有选中的骨骼则自动填入target
            pb = bpy.context.selected_pose_bones_from_active_object
            if pb != None and len(pb) > 0:
                for b in pb:
                    add_mapping_below(b.name, '')
            else:
                add_mapping_below('', '')
        
        elif self.action == 'REMOVE':
            if len(s.mappings) > 0:
                s.remove_mapping(s.active_mapping)
                s.active_mapping =  min(s.active_mapping, len(s.mappings) - 1)
        
        elif self.action == 'UP':
            if s.active_mapping > 0:
                s.mappings.move(s.active_mapping, s.active_mapping - 1)
                s.active_mapping -= 1
        
        elif self.action == 'DOWN':
            if len(s.mappings) > s.active_mapping + 1:
                s.mappings.move(s.active_mapping, s.active_mapping + 1)
                s.active_mapping += 1

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
    
    BAC_OT_ListAction,
    BAC_OT_ChildMapping,
    BAC_OT_NameMapping
    )