# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "Bone Animation Copy Tool",
    "author" : "Kumopult <kumopult@qq.com>",
    "description" : "Copy animation between different armature by bone constrain",
    "blender" : (2, 83, 0),
    "version" : (0, 0, 2),
    "location" : "View 3D > Toolshelf",
    "warning" : "因为作者很懒所以没写英文教学！",
    "category" : "Animation",
    "doc_url": "https://github.com/kumopult/blender_BoneAnimCopy",
    "tracker_url": "https://space.bilibili.com/1628026",
    # VScode调试：Ctrl + Shift + P
}

import bpy
from . import data
from . import mapping
from .utilfuncs import *

class BAC_PT_Panel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BoneAnimCopy"
    bl_label = "Bone Animation Copy Tool"
    
    def draw(self, context):
        layout = self.layout
        
        if context.object != None and context.object.type == 'ARMATURE':
            s = get_state()
            
            split = layout.row().split(factor=0.25)
            split.column().label(text='映射目标:')
            split.column().label(text=context.object.name, icon='ARMATURE_DATA')
            layout.prop(s, 'selected_source', text='动作来源', icon='ARMATURE_DATA')
            layout.separator()
            
            if s.source == None:
                layout.label(text='选择另一骨架对象作为动作来源以继续操作', icon='INFO')
            else:
                row = layout.row()
                row.label(text='使用预设:')
                row.menu(mapping.BAC_MT_presets.__name__, text=mapping.BAC_MT_presets.bl_label)
                row.operator(mapping.AddPresetBACMapping.bl_idname, text="", icon='ADD')
                row.operator(mapping.AddPresetBACMapping.bl_idname, text="", icon='REMOVE').remove_active=True
                mapping.draw_panel(layout.box())
                row = layout.row()
                row.prop(s, 'preview', text='预览约束', icon= 'HIDE_OFF' if s.preview else 'HIDE_ON')
                if s.target.select:
                    row = layout.row()
                    row.operator('kumopult_bac.bake', text='烘培动画', icon='NLA')
                    row.operator('kumopult_bac.bake_collection', text='批量烘培动画', icon='NLA', )

        else:
            layout.label(text='未选中骨架对象', icon='ERROR')

class BAC_State(bpy.types.PropertyGroup):
    selected_source: bpy.props.PointerProperty(
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == 'ARMATURE' and obj != bpy.context.object,
        update=lambda self, ctx: get_state().update_source()
    )
    source: bpy.props.PointerProperty(type=bpy.types.Object)
    target: bpy.props.PointerProperty(type=bpy.types.Object)
    
    mappings: bpy.props.CollectionProperty(type=data.BAC_BoneMapping)
    active_mapping: bpy.props.IntProperty(default=-1)
    
    editing_mappings: bpy.props.BoolProperty(default=False, description="展开详细编辑面板")
    editing_type: bpy.props.IntProperty(description="用于记录面板类型")

    preview: bpy.props.BoolProperty(
        default=True, 
        description="开关所有约束以便预览烘培出的动画之类的",
        update=lambda self, ctx: get_state().update_preview()
    )
    source_collection: bpy.props.PointerProperty(type=bpy.types.Collection)
    
    def update_source(self):
        self.target = bpy.context.object
        self.source = self.selected_source

        for m in self.mappings:
            m.apply()
    
    def update_preview(self):
        for m in self.mappings:
            m.mute(not self.preview)
    
    def get_source_armature(self):
        return self.source.data

    def get_target_armature(self):
        return self.target.data
    
    def get_source_pose(self):
        return self.source.pose

    def get_target_pose(self):
        return self.target.pose

    def get_active_mapping(self):
        return self.mappings[self.active_mapping]
    
    def get_mapping_by_source(self, name):
        if name != "":
            for i, m in enumerate(self.mappings):
                if m.source == name:
                    return m, i
        return None, -1

    def get_mapping_by_target(self, name):
        if name != "":
            for i, m in enumerate(self.mappings):
                if m.target == name:
                    return m, i
        return None, -1
    
    def add_mapping(self, target, source):
        # 这里需要检测一下目标骨骼是否已存在映射
        m, i = self.get_mapping_by_target(target)
        # 若已存在，则覆盖原本的源骨骼，并返回映射和索引值
        if m:
            print("目标骨骼已存在映射关系，已覆盖修改源骨骼")
            m.source = source
            return m, i
        # 若不存在，则新建映射，同样返回映射和索引值
        m = self.mappings.add()
        m.selected_target = target
        m.source = source
        return m, len(self.mappings) - 1
    
    def add_mapping_below(self, target, source):
        i = self.add_mapping(target, source)[1]
        self.mappings.move(i, self.active_mapping + 1)
        self.active_mapping += 1
    
    def remove_mapping(self, index):
        self.mappings[index].clear()
        self.mappings.remove(index)

classes = (
	BAC_PT_Panel, 
	*data.classes,
	*mapping.classes,
	BAC_State,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Object.kumopult_bac = bpy.props.PointerProperty(type=BAC_State)
    print("hello kumopult!")

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Object.kumopult_bac
    print("goodbye kumopult!")
