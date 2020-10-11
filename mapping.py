import bpy
from .utilfuncs import *

def draw_panel(layout):
    s = get_state()
    
    if s.editing_mappings:
        layout.label(text='Edit Bone Mappings:', icon='TOOL_SETTINGS')

        row = layout.row()
        row.template_list('BAC_UL_mappings', '', s, 'mappings', s, 'active_mapping')
        col = row.column(align=True)
        col.operator('kumopult_bac.list_action', icon='ADD', text='').action = 'ADD'
        col.operator('kumopult_bac.list_action', icon='REMOVE', text='').action = 'REMOVE'
        col.operator('kumopult_bac.list_action', icon='TRIA_UP', text='').action = 'UP'
        col.operator('kumopult_bac.list_action', icon='TRIA_DOWN', text='').action = 'DOWN'
        col.operator('kumopult_bac.child_mapping', icon='CON_SPLINEIK', text='')
        layout.operator('kumopult_bac.constraint_apply', text='Done')
    else:
        layout.label(text='Bone Constraints:', icon='TOOL_SETTINGS')
        layout.template_list('BAC_UL_constraints', '', s, 'mappings', s, 'active_mapping')
        layout.operator('kumopult_bac.constraint_edit', text='Edit')


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


class BAC_OT_ListAction(bpy.types.Operator):
    bl_idname = 'kumopult_bac.list_action'
    bl_label = 'Apply'
    action: bpy.props.StringProperty()

    def execute(self, context):
        s = get_state()

        if self.action == 'ADD':
            s.add_mapping('', '')
            s.mappings.move(len(s.mappings) - 1, s.active_mapping + 1)
            s.active_mapping += 1
        elif self.action == 'REMOVE':
            if len(s.mappings) > 0:
                s.remove_mapping(s.active_mapping)
                s.active_mapping =  min(s.active_mapping, len(s.mappings) - 1)
        elif self.action == 'UP':
            if s.active_mapping > 0:
                s.mappings.move(s.active_mapping, s.active_mapping - 1)
        elif self.action == 'DOWN':
            if len(s.mappings) > s.active_mapping + 1:
                s.mappings.move(s.active_mapping, s.active_mapping + 1)


        return {'FINISHED'}


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

classes = (
    BAC_UL_mappings,
    BAC_UL_constraints,
    
    BAC_OT_ListAction,
    BAC_OT_ChildMapping,
    BAC_OT_Apply,
    BAC_OT_Edit
    )