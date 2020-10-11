bl_info = {
    "name": "Bone Animation Copy Tool",
    "description": "Copy animation between different armature by bone constrain",
    "author": "Kumopult <kumopult@qq.com>",
    "version": (1, 1),
    "blender": (2, 83, 0),
    "location": "View 3D > Toolshelf",
    "doc_url": "https://github.com/kumopult/blender_BoneAnimCopy",
    "tracker_url": "https://github.com/kumopult/blender_BoneAnimCopy/issues",
    "category": "Armature",
    }

import bpy


# UI
class BAC_PT_Panel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BoneAnimCopy"
    bl_label = "Bone Animation Copy Tool"
    
    def draw(self, context):
        layout = self.layout
        
        if context.object != None and context.object.type == 'ARMATURE':
            s = get_state()
            
            split = layout.row().split(factor=0.244)
            split.column().label(text='Target:')
            split.column().label(text=context.object.name, icon='ARMATURE_DATA')
            layout.prop(s, 'selected_source', text='Source', icon='ARMATURE_DATA')
            layout.separator()
            
            if s.source == None:
                layout.label(text='Choose a source armature to continue', icon='INFO')
            else:
                layout.label(text='Bone Mappings')
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
            
        else:
            layout.label(text='No armature selected', icon='ERROR')


# data
class BAC_BoneMapping(bpy.types.PropertyGroup):
    source: bpy.props.StringProperty()
    target: bpy.props.StringProperty()
    roll: bpy.props.FloatProperty()
    
    def is_valid(self):
        return (self.source != None 
                and self.target != None 
                and len(self.source) > 0 
                and len(self.target) > 0)
    
    def apply(self):
        # apply mapping into constraint
        s = get_state()
        
        cr = self.get_cr()
        rr = self.get_rr()
        
        cr.target = s.source
        cr.subtarget = self.source
        rr.to_min_y_rot = self.roll
        
        
    def save(self):
        # save constraint roll into mapping
        cr = self.get_cr()
        rr = self.get_rr()
        
        self.roll = rr.to_min_y_rot
    
    
    def get_cr(self):
        s = get_state()
        tc = s.target.pose.bones[self.target].constraints
        
        def new_cr():
            cr = tc.new(type='COPY_ROTATION')
            cr.name = 'BAC_ROT_COPY'
            return cr
        
        cr = tc.get('BAC_ROT_COPY') or new_cr()
        return cr
        
    def get_rr(self):
        s = get_state()
        tc = s.target.pose.bones[self.target].constraints
        
        def new_rr():
            rr = tc.new(type='TRANSFORM')
            rr.name = 'BAC_ROT_ROLL'
            rr.map_to = 'ROTATION'
            rr.owner_space = 'LOCAL'
            rr.to_euler_order = 'YXZ'
            rr.target = bpy.data.objects['BAC_AXES']
            return rr
        
        rr = tc.get('BAC_ROT_ROLL') or new_rr()
        return rr
    
    def clear(self):
        s = get_state()
        c = s.target.pose.bones[self.target].constraints
        c.remove(self.get_cr)
        c.remove(self.get_rr)
        
     
class BAC_State(bpy.types.PropertyGroup):
    selected_source: bpy.props.PointerProperty(
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == 'ARMATURE' and obj != bpy.context.object,
        update=lambda self, ctx: get_state().update_source()
    )
    source: bpy.props.PointerProperty(type=bpy.types.Object)
    target: bpy.props.PointerProperty(type=bpy.types.Object)
    
    mappings: bpy.props.CollectionProperty(type=BAC_BoneMapping)
    active_mapping: bpy.props.IntProperty()
    
    editing_mappings: bpy.props.BoolProperty(default=False)
    
    def update_source(self):
        self.target = bpy.context.object

        if self.selected_source == None:
            return
        
        self.source = self.selected_source
    
    def get_source_armature(self):
        return self.source.data

    def get_target_armature(self):
        return self.target.data
    
    def add_mapping(self, target, source):
        m = self.mappings.add()
        m.target = target
        m.source = source
        self.active_mapping = len(self.mappings) - 1
        return m
    
    def remove_mapping(self, index):
        self.mappings[index].clear()
        self.mappings.remove(index)
        

# mapping
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
    
    def execute(self, context):
        s = get_state()
        m = s.mappings[s.active_mapping]
        
        source_children = s.get_source_armature().bones[m.source].children
        target_children = s.get_target_armature().bones[m.target].children
        
        for i in range(0, min(len(source_children), len(target_children))):
            s.add_mapping(target_children[i].name, source_children[i].name)
            
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
    

# utils
def get_state():
    return bpy.context.object.kumopult_bac




classes = (
    BAC_PT_Panel,
    
    BAC_BoneMapping,
    BAC_State,
    
    BAC_UL_mappings,
    BAC_UL_constraints,
    
    BAC_OT_ListAction,
    BAC_OT_ChildMapping,
    BAC_OT_Apply,
    BAC_OT_Edit
    )

# register, unregister = bpy.utils.register_classes_factory(classes)

# Register
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Object.kumopult_bac = bpy.props.PointerProperty(type=BAC_State)


# Unregister
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Object.kumopult_bac


if __name__ == "__main__":
    register()