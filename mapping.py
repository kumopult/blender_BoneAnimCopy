import bpy
from .utilfuncs import *

def draw_panel(layout):
    s = get_state()
    
    layout.label(text='Edit Bone Mappings:', icon='TOOL_SETTINGS')

    row = layout.row()
    row.template_list('BAC_UL_mappings', '', s, 'mappings', s, 'active_mapping')
    col = row.column(align=True)
    col.operator('kumopult_bac.list_action', icon='ADD', text='').action = 'ADD'
    col.operator('kumopult_bac.list_action', icon='REMOVE', text='').action = 'REMOVE'
    col.operator('kumopult_bac.list_action', icon='TRIA_UP', text='').action = 'UP'
    col.operator('kumopult_bac.list_action', icon='TRIA_DOWN', text='').action = 'DOWN'
    col.operator('kumopult_bac.list_action', icon='CON_SPLINEIK', text='').action = 'CHILD'



class BAC_UL_mappings(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):
        s = get_state()
        layout.alert = not item.is_valid() # 该mapping无效时警告
        layout.prop_search(item, 'selected_target', s.get_target_armature(), 'bones', text='', icon='BONE_DATA')
        layout.label(icon='BACK')
        if item.target_valid():
            # target有效时显示之后的选项
            layout.prop_search(item, 'source', s.get_source_armature(), 'bones', text='', icon='BONE_DATA')
            # 直接操控变换修改器的生效状态，如果不disable就显示接下来的xyz偏移
            if not item.get_rr().mute:
                layout.prop(item, 'offset', text='')
            layout.prop(item.get_rr(), 'mute', icon='ORIENTATION_GIMBAL', icon_only=True)
        else:
            layout.label(icon='BONE_DATA')

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
    bl_label = 'ListAction'
    action: bpy.props.StringProperty()

    def add_mapping_below(self, target, source):
        s = get_state()
        s.add_mapping(target, source)
        s.mappings.move(len(s.mappings) - 1, s.active_mapping + 1)
        s.active_mapping += 1
    
    def child_mapping(self):
        s = get_state()
        m = s.mappings[s.active_mapping]
        
        source_children = s.get_source_armature().bones[m.source].children
        target_children = s.get_target_armature().bones[m.target].children
        
        if len(source_children) == len(target_children) == 1:
            self.add_mapping_below(target_children[0].name, source_children[0].name)
            # 递归调用，实现连锁对应
            self.child_mapping()
        else:
            for i in range(0, len(target_children)):
                self.add_mapping_below(target_children[i].name, '')

    def execute(self, context):
        s = get_state()

        if self.action == 'ADD':
            #这里需要加一下判断，如果有选中的骨骼则自动填入target
            pb = bpy.context.selected_pose_bones_from_active_object
            if pb != None and len(pb) > 0:
                for b in pb:
                    self.add_mapping_below(b.name, '')
            else:
                self.add_mapping_below('', '')
            # self.add_mapping_below('', '')
        
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
        
        elif self.action == 'CHILD':
            if s.mappings[s.active_mapping].is_valid():
                self.child_mapping()
            else:
                self.report({"ERROR"}, "所选mapping不完整")
        
        elif self.action == 'MIRROR':
            # 镜像操作直接对全体骨骼过一遍吧，不搞选中处理了
            for m in s.mappings:
                print(m + "得想想该怎么判断镜像骨骼")

        return {'FINISHED'}

'''
class BAC_OT_ChildMapping(bpy.types.Operator):
    bl_idname = 'kumopult_bac.child_mapping'
    bl_label = 'ChildMap'

    def child_mapping(self):
        s = get_state()
        m = s.mappings[s.active_mapping]
        
        source_children = s.get_source_armature().bones[m.source].children
        target_children = s.get_target_armature().bones[m.target].children
        
        if len(source_children) == len(target_children) == 1:
            s.add_mapping(target_children[0].name, source_children[0].name)
            s.mappings.move(len(s.mappings) - 1, s.active_mapping + 1)
            s.active_mapping += 1
            # 递归调用，实现连锁对应
            self.child_mapping()
        else:
            for i in range(0, len(target_children)):
                s.add_mapping(target_children[i].name, '')
    
    def execute(self, context):
            
        return {'FINISHED'}
'''

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
    
    BAC_OT_ListAction
    )