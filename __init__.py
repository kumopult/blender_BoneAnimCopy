# SPDX-License-Identifier: GPL-3.0-or-later
bl_info = {
    "name": "Bone Animation Copy Tool",
    "author": "Kumopult (optimized), maylog",
    "description": "Copy animation between armatures using bone constraints.",
    "blender": (4, 2, 0),
    "version": (1, 1, 5),
    "location": "View 3D > UI > BoneAnimCopy",
    "category": "Animation",
    "tracker_url": "https://github.com/mayloglog/blender_BoneAnimCopy",
}

import bpy
from bl_operators.presets import AddPresetBase
from math import pi
from mathutils import Euler
import difflib
import subprocess
import sys
from typing import Optional

# --- Utilities --------------------------------------------------------------

def safe_get_state() -> Optional["BAC_State"]:
    """Retrieve the BAC state from the current scene's owner armature."""
    scene = bpy.context.scene
    owner = getattr(scene, "kumopult_bac_owner", None)
    if owner and getattr(owner, "type", None) == 'ARMATURE':
        return getattr(owner.data, "kumopult_bac", None)
    return None

def set_constraint_enabled(con: bpy.types.Constraint, state: bool):
    """Enable or disable a constraint, handling different Blender versions."""
    try:
        if hasattr(con, "enabled"):
            con.enabled = state
        elif hasattr(con, "mute"):
            con.mute = not state
    except AttributeError as e:
        print(f"Error setting constraint enabled state: {e}")

def alert_error(title: str, msg: str):
    """Display an error popup with detailed message."""
    def draw(self, context):
        self.layout.label(text=msg)
    bpy.context.window_manager.popup_menu(draw, title=title, icon='ERROR')

def open_folder(path: str):
    """Open a folder in the system file explorer."""
    try:
        bpy.ops.wm.path_open(filepath=path)
    except RuntimeError:
        if sys.platform.startswith("win"):
            subprocess.Popen(["explorer", path])
        elif sys.platform.startswith("darwin"):
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

# Tag constraints created by addon (now using name prefix)
BAC_CONSTRAINT_PREFIX = "BAC_"

# Simple reentrancy guard decorator
def guard(name="is_updating"):
    def dec(fn):
        def wrapper(self, context):
            if getattr(self, name, False):
                return None
            setattr(self, name, True)
            try:
                return fn(self, context)
            finally:
                setattr(self, name, False)
        return wrapper
    return dec

# --- PropertyGroups --------------------------------------------------------

class BAC_BoneMapping(bpy.types.PropertyGroup):
    selected_owner: bpy.props.StringProperty(name="Owner Bone", update=lambda s, c: s._on_owner(c))
    owner: bpy.props.StringProperty()
    target: bpy.props.StringProperty(name="Target Bone", update=lambda s, c: s._on_target(c))

    has_rotoffs: bpy.props.BoolProperty(name="Rotation Offset", update=lambda s, c: s._apply(c))
    has_loccopy: bpy.props.BoolProperty(name="Copy Location", update=lambda s, c: s._apply(c))
    has_ik: bpy.props.BoolProperty(name="IK", update=lambda s, c: s._apply(c))

    offset: bpy.props.FloatVectorProperty(name="Rotation Offset", subtype='EULER', size=3, min=-pi, max=pi, update=lambda s, c: s._apply(c))
    loc_axis: bpy.props.BoolVectorProperty(name="Location Axes", size=3, default=(True, True, True), update=lambda s, c: s._apply(c))
    ik_influence: bpy.props.FloatProperty(name="IK Influence", default=1.0, min=0.0, max=1.0, update=lambda s, c: s._apply(c))

    selected: bpy.props.BoolProperty(update=lambda s, c: s._on_selected(c))

    is_updating: bool = False

    def _state(self) -> Optional["BAC_State"]:
        """Get the current BAC state."""
        return safe_get_state()

    @guard("is_updating")
    def _on_owner(self, context):
        """Handle owner bone selection update."""
        self.clear_constraints()
        self.owner = self.selected_owner
        state = self._state()
        if state and self.get_owner_pose_bone():
            # 检查非 BAC 约束 (保留 Bug 修复)
            if len([c for c in self.get_owner_pose_bone().constraints if not c.name.startswith(BAC_CONSTRAINT_PREFIX)]) > 0:
                alert_error("Constraint Conflict", f"Bone '{self.owner}' already has non-BAC constraints; mixing may affect baking.")
        self._apply(context)

    @guard("is_updating")
    def _on_target(self, context):
        """Handle target bone selection update and calculate rotation offset."""
        state = self._state()
        if state and self.is_valid() and state.calc_offset and state.target and state.owner:
            owner_bone = self.get_owner_pose_bone()
            target_bone = self.get_target_pose_bone()
            if owner_bone and target_bone:
                try:
                    # 姿态切换/偏移计算逻辑
                    euler = ((state.target.matrix_world @ target_bone.matrix).inverted() @ 
                             (state.owner.matrix_world @ owner_bone.matrix)).to_euler()
                    if state.ortho_offset:
                        step = pi * 0.5
                        euler[0] = round(euler[0]/step) * step
                        euler[1] = round(euler[1]/step) * step
                        euler[2] = round(euler[2]/step) * step
                    if euler != Euler((0, 0, 0)):
                        self.offset = (euler[0], euler[1], euler[2])
                        self.has_rotoffs = True
                except ValueError as e:
                    alert_error("Offset Calculation Failed", f"Cannot calculate rotation offset for '{self.owner}': {str(e)}")
        self._apply(context)

    def _on_selected(self, context):
        """Update selected count when a mapping is selected."""
        state = self._state()
        if state:
            state.selected_count = sum(1 for mapping in state.mappings if mapping.selected)

    def get_owner_pose_bone(self) -> Optional[bpy.types.PoseBone]:
        """Get the owner pose bone."""
        state = self._state()
        if not state or not state.owner:
            return None
        return state.owner.pose.bones.get(self.owner)

    def get_target_pose_bone(self) -> Optional[bpy.types.PoseBone]:
        """Get the target pose bone."""
        state = self._state()
        if not state or not state.target:
            return None
        return state.target.pose.bones.get(self.target)

    def is_valid(self) -> bool:
        """Check if the mapping is valid (both owner and target bones exist)."""
        return self.get_owner_pose_bone() is not None and self.get_target_pose_bone() is not None

    def _new_constraint(self, owner_pb: bpy.types.PoseBone, ctype: str, name: str) -> bpy.types.Constraint:
        """Create or retrieve a constraint for the given bone."""
        con = owner_pb.constraints.get(name)
        if con:
            return con
        try:
            con = owner_pb.constraints.new(ctype)
            con.name = name
            if hasattr(con, "show_expanded"):
                con.show_expanded = False
        except RuntimeError as e:
            alert_error("Constraint Creation Failed", f"Cannot create {ctype} constraint for '{owner_pb.name}': {str(e)}")
        return con

    def get_constraint(self, kind: str) -> Optional[bpy.types.Constraint]:
        """Get or create a constraint of the specified kind."""
        owner_pb = self.get_owner_pose_bone()
        if not owner_pb:
            return None
        if kind == 'rot':
            return self._new_constraint(owner_pb, 'COPY_ROTATION', "BAC_ROT_COPY")
        if kind == 'roll':
            rr = self._new_constraint(owner_pb, 'TRANSFORM', "BAC_ROT_ROLL")
            try:
                rr.map_to = 'ROTATION'
                rr.owner_space = 'CUSTOM'
            except AttributeError as e:
                alert_error("Constraint Setup Failed", f"Cannot configure roll constraint for '{owner_pb.name}': {str(e)}")
            return rr
        if kind == 'loc':
            return self._new_constraint(owner_pb, 'COPY_LOCATION', "BAC_LOC_COPY")
        if kind == 'ik':
            ik = self._new_constraint(owner_pb, 'IK', "BAC_IK")
            try:
                state = self._state()
                # 应用全局 IK 链长
                ik.chain_count = state.ik_chain_count if state else 2
                ik.use_tail = False
            except AttributeError as e:
                alert_error("Constraint Setup Failed", f"Cannot configure IK constraint for '{owner_pb.name}': {str(e)}")
            return ik
        return None

    def _apply(self, context):
        """Apply constraints based on mapping settings."""
        state = self._state()
        owner_pb = self.get_owner_pose_bone()
        target_pb = self.get_target_pose_bone()
        if not state or not owner_pb or not target_pb:
            return

        constraints = {
            'rot': self.get_constraint('rot'),
            'roll': self.get_constraint('roll'),
            'loc': self.get_constraint('loc'),
            'ik': self.get_constraint('ik')
        }

        # Rotation copy
        if constraints['rot']:
            try:
                constraints['rot'].target = state.target
                constraints['rot'].subtarget = self.target
                set_constraint_enabled(constraints['rot'], self.is_valid() and state.preview)
            except AttributeError as e:
                alert_error("Constraint Error", f"Cannot set rotation constraint for '{self.owner}': {str(e)}")

        # Rotation offset
        if constraints['roll']:
            if self.has_rotoffs and self.is_valid():
                try:
                    constraints['roll'].to_min_x_rot = self.offset[0]
                    constraints['roll'].to_min_y_rot = self.offset[1]
                    constraints['roll'].to_min_z_rot = self.offset[2]
                    constraints['roll'].target = constraints['roll'].space_object = state.target
                    constraints['roll'].subtarget = constraints['roll'].space_subtarget = self.target
                    set_constraint_enabled(constraints['roll'], state.preview)
                except AttributeError as e:
                    alert_error("Constraint Error", f"Cannot set roll constraint for '{self.owner}': {str(e)}")
            else:
                self._remove_constraint(constraints['roll'])

        # Location copy
        if constraints['loc']:
            if self.has_loccopy and self.is_valid():
                try:
                    constraints['loc'].use_x = self.loc_axis[0]
                    constraints['loc'].use_y = self.loc_axis[1]
                    constraints['loc'].use_z = self.loc_axis[2]
                    constraints['loc'].target = state.target
                    constraints['loc'].subtarget = self.target
                    # 应用全局位置空间设置
                    constraints['loc'].owner_space = state.loc_space
                    constraints['loc'].target_space = state.loc_space
                    set_constraint_enabled(constraints['loc'], state.preview)
                except AttributeError as e:
                    alert_error("Constraint Error", f"Cannot set location constraint for '{self.owner}': {str(e)}")
            else:
                self._remove_constraint(constraints['loc'])

        # IK
        if constraints['ik']:
            if self.has_ik and self.is_valid():
                try:
                    constraints['ik'].influence = self.ik_influence
                    constraints['ik'].target = state.target
                    constraints['ik'].subtarget = self.target
                    # 应用全局 IK 链长设置
                    constraints['ik'].chain_count = state.ik_chain_count
                    set_constraint_enabled(constraints['ik'], state.preview)
                except AttributeError as e:
                    alert_error("Constraint Error", f"Cannot set IK constraint for '{self.owner}': {str(e)}")
            else:
                self._remove_constraint(constraints['ik'])

    def _remove_constraint(self, con: bpy.types.Constraint):
        """Remove a constraint if it was created by the addon (by name prefix)."""
        owner_pb = self.get_owner_pose_bone()
        if not con or not owner_pb:
            return
        if con.name.startswith(BAC_CONSTRAINT_PREFIX):
            try:
                owner_pb.constraints.remove(con)
            except RuntimeError as e:
                alert_error("Constraint Removal Failed", f"Cannot remove constraint '{con.name}' from '{owner_pb.name}': {str(e)}")

    def clear_constraints(self):
        """Remove all addon-created constraints from the owner bone."""
        owner_pb = self.get_owner_pose_bone()
        if not owner_pb:
            return
        for con in list(owner_pb.constraints):
            if con.name.startswith(BAC_CONSTRAINT_PREFIX):
                self._remove_constraint(con)

class BAC_State(bpy.types.PropertyGroup):
    is_updating: bool = False

    @guard("is_updating")
    def update_constraints(self, context):
        """Uniformly update the state of all constraints.""" #统一更新所有约束状态。
        for mapping in self.mappings:
            mapping._apply(context)

    @guard("is_updating")
    def update_target(self, context):
        """Update target armature and apply constraints."""
        self.owner = bpy.context.scene.kumopult_bac_owner
        self.target = self.selected_target
        self.update_constraints(context)

    def update_preview(self, context):
        """Update constraint preview state."""
        self.update_constraints(context)

    @guard("is_updating")
    def update_active(self, context):
        """Sync active mapping with bone selection."""
        if self.sync_select:
            self.update_select(context)
            if 0 <= self.active_mapping < len(self.mappings):
                owner_active = self.owner.data.bones.get(self.mappings[self.active_mapping].owner)
                if owner_active:
                    self.owner.data.bones.active = owner_active
                if self.target:
                    target_active = self.target.data.bones.get(self.mappings[self.active_mapping].target)
                    if target_active:
                        self.target.data.bones.active = target_active

    @guard("is_updating")
    def update_select(self, context):
        """Synchronize bone selection with mapping selection."""
        if self.sync_select and self.owner and self.target:
            owner_sel = {mapping.owner for mapping in self.mappings if mapping.selected}
            target_sel = {mapping.target for mapping in self.mappings if mapping.selected}
            for bone in self.owner.data.bones:
                bone.select = bone.name in owner_sel
            for bone in self.target.data.bones:
                bone.select = bone.name in target_sel

    selected_target: bpy.props.PointerProperty(
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == 'ARMATURE' and obj != bpy.context.scene.kumopult_bac_owner,
        update=update_target
    )
    target: bpy.props.PointerProperty(type=bpy.types.Object)
    owner: bpy.props.PointerProperty(type=bpy.types.Object)

    mappings: bpy.props.CollectionProperty(type=BAC_BoneMapping)
    active_mapping: bpy.props.IntProperty(default=-1, update=update_active)
    selected_count: bpy.props.IntProperty(default=0, update=update_select)

    editing_type: bpy.props.IntProperty(description="0 mapping, 1 rotation, 2 location, 3 IK")
    preview: bpy.props.BoolProperty(default=True, update=update_preview)

    sync_select: bpy.props.BoolProperty(default=False, description="Synchronize bone selection with mappings")
    calc_offset: bpy.props.BoolProperty(default=True, description="Calculate rotation offset automatically")
    ortho_offset: bpy.props.BoolProperty(default=True, description="Snap offset to orthogonal angles")
    target_animation_layer: bpy.props.StringProperty(default="", description="Target animation layer for baking")

    # LOGIC/UI: Location Space (约束空间)
    loc_space: bpy.props.EnumProperty(
        items=[
            ('WORLD', "World Space", "Use World Space for location constraint"),
            ('POSE', "Pose Space", "Use Pose Space for location constraint (relative to armature object)"),
            ('LOCAL', "Local Space", "Use Local Space for location constraint (relative to bone's parent or self)"),
            ('PARENT', "Parent Space", "Use Parent Space for location constraint")
        ],
        name="Location Space",
        description="Coordinate space for location copy constraints", 
        default='WORLD',
        update=update_constraints
    )

    # LOGIC/UI: IK Chain Count (IK 链数)
    ik_chain_count: bpy.props.IntProperty(
        name="IK Chain Length",
        description="The number of bones in the IK chain (0 means to the root bone)",
        default=2,
        min=0,
        update=update_constraints
    )

    def get_target_armature(self) -> Optional[bpy.types.Armature]:
        """Get the target armature data."""
        return self.target.data if self.target else None

    def get_owner_armature(self) -> Optional[bpy.types.Armature]:
        """Get the owner armature data."""
        return self.owner.data if self.owner else None

    def get_target_pose(self) -> Optional[bpy.types.Pose]:
        """Get the target pose data."""
        return self.target.pose if self.target else None

    def get_owner_pose(self) -> Optional[bpy.types.Pose]:
        """Get the owner pose data."""
        return self.owner.pose if self.owner else None

    def get_selection(self) -> list[int]:
        """Get indices of selected or active mappings."""
        if self.selected_count == 0 and 0 <= self.active_mapping < len(self.mappings):
            return [self.active_mapping]
        return [i for i in range(len(self.mappings)-1, -1, -1) if self.mappings[i].selected]

    def add_mapping(self, owner: str, target: str, index: int = -1) -> tuple["BAC_BoneMapping", int]:
        """Add a new bone mapping."""
        if index == -1:
            index = self.active_mapping + 1
        existing_mapping, existing_index = self.get_mapping_by_owner(owner)
        if existing_mapping:
            existing_mapping.target = target
            self.active_mapping = existing_index
            return existing_mapping, existing_index
        new_mapping = self.mappings.add()
        new_mapping.selected_owner = owner
        new_mapping.target = target
        final = max(0, min(index, len(self.mappings)-1))
        self.mappings.move(len(self.mappings)-1, final)
        self.active_mapping = final
        return self.mappings[final], final

    def remove_mapping(self):
        """Remove selected mappings."""
        for i in self.get_selection():
            try:
                self.mappings[i].clear_constraints()
                self.mappings.remove(i)
            except RuntimeError as e:
                alert_error("Mapping Removal Failed", f"Cannot remove mapping at index {i}: {str(e)}")
        self.active_mapping = min(self.active_mapping, max(0, len(self.mappings)-1))
        self.selected_count = 0

    def get_mapping_by_owner(self, name: str) -> tuple[Optional["BAC_BoneMapping"], int]:
        """Find a mapping by owner bone name."""
        if name:
            for i, mapping in enumerate(self.mappings):
                if mapping.owner == name:
                    return mapping, i
        return None, -1

# --- UI list and operators -------------------------------------------------

class BAC_UL_mappings(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        """Draw a single mapping item in the UI list."""
        state = safe_get_state()
        if not state:
            return
        layout.alert = not item.is_valid()
        layout.active = item.selected or state.selected_count == 0
        row = layout.row(align=True)
        if state.editing_type == 0:
            row.prop(item, "selected", text="", emboss=False, icon='CHECKBOX_HLT' if item.selected else 'CHECKBOX_DEHLT')
            row.prop_search(item, "selected_owner", state.get_owner_armature(), "bones", text="", translate=False, icon='BONE_DATA')
            row.label(icon='BACK')
            row.prop_search(item, "target", state.get_target_armature(), "bones", text="", translate=False, icon='BONE_DATA')
        elif state.editing_type == 1:
            row.prop(item, "has_rotoffs", icon='CON_ROTLIKE', icon_only=True)
            layout.label(text=item.selected_owner, translate=False)
            if item.has_rotoffs:
                layout.prop(item, "offset", text="")
        elif state.editing_type == 2:
            row.prop(item, "has_loccopy", icon='CON_LOCLIKE', icon_only=True)
            layout.label(text=item.selected_owner, translate=False)
            if item.has_loccopy:
                layout.prop(item, "loc_axis", text="")
        else: # state.editing_type == 3
            row.prop(item, "has_ik", icon='CON_KINEMATIC', icon_only=True)
            layout.label(text=item.selected_owner, translate=False)
            if item.has_ik:
                layout.prop(item, "ik_influence", text="Influence")


class BAC_MT_SettingMenu(bpy.types.Menu):
    bl_label = "Settings"
    def draw(self, context):
        """Draw the settings menu."""
        state = safe_get_state()
        if not state:
            return
        layout = self.layout
        layout.prop(state, "sync_select")
        layout.prop(state, "calc_offset")
        layout.prop(state, "ortho_offset")
        layout.prop(state, "target_animation_layer", text="Animation Layer")


class BAC_MT_presets(bpy.types.Menu):
    bl_label = "Mapping Presets"
    preset_subdir = "kumopult_bac"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset

class AddPresetBACMapping(AddPresetBase, bpy.types.Operator):
    bl_idname = "kumopult_bac.mappings_preset_add"
    bl_label = "Add BAC Mappings Preset"
    preset_menu = "BAC_MT_presets"
    preset_defines = ["state = bpy.context.scene.kumopult_bac_owner.data.kumopult_bac"]
    preset_values = ["state.mappings", "state.selected_count"]
    preset_subdir = "kumopult_bac"

class BAC_OT_OpenPresetFolder(bpy.types.Operator):
    bl_idname = "kumopult_bac.open_preset_folder"
    bl_label = "Open Preset Folder"
    def execute(self, context):
        """Open the preset folder in the system file explorer."""
        path = bpy.path.abspath(bpy.utils.resource_path('USER') + "/scripts/presets/kumopult_bac")
        open_folder(path)
        return {"FINISHED"}

class BAC_OT_SelectEditType(bpy.types.Operator):
    bl_idname = "kumopult_bac.select_edit_type"
    bl_label = "Select Edit Type"
    selected_type: bpy.props.IntProperty()
    def execute(self, context):
        """Set the editing type."""
        state = safe_get_state()
        if not state:
            return {"CANCELLED"}
        state.editing_type = self.selected_type
        return {"FINISHED"}

class BAC_OT_SelectAction(bpy.types.Operator):
    bl_idname = "kumopult_bac.select_action"
    bl_label = "List Select Action"
    action: bpy.props.StringProperty()
    def execute(self, context):
        """Handle selection actions for mappings."""
        state = safe_get_state()
        if not state:
            return {"CANCELLED"}
        if self.action == 'ALL':
            for mapping in state.mappings:
                mapping.selected = True
            state.selected_count = len(state.mappings)
        elif self.action == 'INVERSE':
            for mapping in state.mappings:
                mapping.selected = not mapping.selected
            state.selected_count = sum(1 for mapping in state.mappings if mapping.selected)
        else:
            for mapping in state.mappings:
                mapping.selected = False
            state.selected_count = 0
        return {"FINISHED"}

class BAC_OT_ListAction(bpy.types.Operator):
    bl_idname = "kumopult_bac.list_action"
    bl_label = "List Basic Actions"
    action: bpy.props.StringProperty()
    def execute(self, context):
        """Handle basic list actions (add, remove, move)."""
        state = safe_get_state()
        if not state:
            return {"CANCELLED"}
        if self.action == 'ADD':
            state.add_mapping('', '')
        elif self.action == 'ADD_SELECT':
            names = [bone.name for bone in state.owner.data.bones if bone.select]
            [state.add_mapping(name, '') for name in names] if names else state.add_mapping('', '')
        elif self.action == 'ADD_ACTIVE':
            owner = state.owner.data.bones.active if state.owner else None
            target = state.target.data.bones.active if state.target else None
            state.add_mapping(owner.name if owner else '', target.name if target else '')
        elif self.action == 'REMOVE':
            state.remove_mapping()
        elif self.action == 'UP':
            if state.selected_count == 0:
                if len(state.mappings) > state.active_mapping > 0:
                    state.mappings.move(state.active_mapping, state.active_mapping-1)
                    state.active_mapping -= 1
            else:
                idxs = [i for i in range(1, len(state.mappings)) if state.mappings[i].selected]
                for i in idxs:
                    if not state.mappings[i-1].selected:
                        state.mappings.move(i, i-1)
        elif self.action == 'DOWN':
            if state.selected_count == 0:
                if len(state.mappings) > state.active_mapping+1 > 0:
                    state.mappings.move(state.active_mapping, state.active_mapping+1)
                    state.active_mapping += 1
            else:
                idxs = [i for i in range(len(state.mappings)-2, -1, -1) if state.mappings[i].selected]
                for i in idxs:
                    if not state.mappings[i+1].selected:
                        state.mappings.move(i, i+1)
        return {"FINISHED"}

class BAC_OT_ChildMapping(bpy.types.Operator):
    bl_idname = "kumopult_bac.child_mapping"
    bl_label = "Child Mapping"
    def execute(self, context):
        """Create mappings for child bones."""
        state = safe_get_state()
        if not state:
            return {"CANCELLED"}
        flag = False
        selection = state.get_selection()
        
        # If selection is empty, use the active one
        if not selection and state.active_mapping != -1:
            selection = [state.active_mapping]

        for i in selection:
            mapping = state.mappings[i]
            if mapping.selected:
                mapping.selected = False
            
            owner_armature = state.get_owner_armature()
            target_armature = state.get_target_armature()
            
            if not owner_armature or not target_armature:
                continue

            owner_bone = owner_armature.bones.get(mapping.owner)
            target_bone = target_armature.bones.get(mapping.target)
            
            if not owner_bone or not target_bone:
                continue
            
            owner_children = owner_bone.children
            target_children = target_bone.children
            
            if len(owner_children) == 1 and len(target_children) == 1:
                # Add the new mapping right after the current one
                new_mapping, _ = state.add_mapping(owner_children[0].name, target_children[0].name, i+1)
                new_mapping.selected = True
                flag = True
            elif len(owner_children) > 0 and len(target_children) > 0:
                self.report({"WARNING"}, f"Bone '{mapping.owner}' has multiple children. Skipping child mapping.")
        
        if not flag and not selection:
             self.report({"ERROR"}, "No active or selected mappings to process.")
        elif not flag:
            self.report({"ERROR"}, "No eligible single-child bones found for mapping or mapping not selected/active.")
            
        return {"FINISHED"}


class BAC_OT_NameMapping(bpy.types.Operator):
    bl_idname = "kumopult_bac.name_mapping"
    bl_label = "Name Mapping"
    prefix: bpy.props.StringProperty(default="", description="Prefix to match in bone names")
    suffix: bpy.props.StringProperty(default="", description="Suffix to match in bone names")
    use_hierarchy: bpy.props.BoolProperty(default=False, description="Match bones based on hierarchy")

    def execute(self, context):
        """Map bones by name similarity or hierarchy."""
        state = safe_get_state()
        if not state or not state.target:
            return {"CANCELLED"}
        
        selection = state.get_selection()
        if not selection:
            self.report({"ERROR"}, "No active or selected mappings to process.")
            return {"CANCELLED"}

        target_bones = state.get_target_armature().bones
        
        for i in selection:
            mapping = state.mappings[i]
            best_match = ''
            best_score = 0.0
            owner_bone = state.get_owner_armature().bones.get(mapping.owner)
            if not owner_bone:
                continue
            
            if self.use_hierarchy:
                owner_parent = owner_bone.parent
                for target_bone in target_bones:
                    if owner_parent and target_bone.parent:
                        if owner_parent.name == mapping.owner and target_bone.parent.name == mapping.target:
                            best_match = target_bone.name
                            best_score = 1.0
                            break
            else:
                for target_bone in target_bones:
                    target_name = target_bone.name
                    if self.prefix and not target_name.startswith(self.prefix):
                        continue
                    if self.suffix and not target_name.endswith(self.suffix):
                        continue
                    score = difflib.SequenceMatcher(None, mapping.owner, target_name).quick_ratio()
                    if score > best_score:
                        best_score = score
                        best_match = target_name
            
            if best_match:
                mapping.target = best_match
            else:
                self.report({"WARNING"}, f"No matching bone found for '{mapping.owner}' (Score: {best_score:.2f})")
                
        state.update_constraints(context)
        return {"FINISHED"}

class BAC_OT_MirrorMapping(bpy.types.Operator):
    bl_idname = "kumopult_bac.mirror_mapping"
    bl_label = "Mirror Mapping"
    def execute(self, context):
        """Create mirrored mappings for selected bones."""
        state = safe_get_state()
        if not state:
            return {"CANCELLED"}
        flag = False
        
        selection = state.get_selection()
        if not selection and state.active_mapping != -1:
            selection = [state.active_mapping]

        for i in selection:
            mapping = state.mappings[i]
            if mapping.selected:
                mapping.selected = False

            owner_mirrored_name = bpy.utils.flip_name(mapping.owner)
            target_mirrored_name = bpy.utils.flip_name(mapping.target)
            
            owner_mirrored = state.get_owner_pose().bones.get(owner_mirrored_name)
            target_mirrored = state.get_target_pose().bones.get(target_mirrored_name)
            
            if owner_mirrored and target_mirrored:
                new_mapping, _ = state.add_mapping(owner_mirrored.name, target_mirrored.name, i+1)
                new_mapping.selected = True
                flag = True
            elif owner_mirrored_name and target_mirrored_name:
                new_mapping, _ = state.add_mapping(owner_mirrored_name, target_mirrored_name, i+1)
                new_mapping.selected = True
                flag = True
            else:
                self.report({"WARNING"}, f"No mirrored bones found for mapping: '{mapping.owner}' -> '{owner_mirrored_name}'")
        
        if not flag and not selection:
            self.report({"ERROR"}, "No active or selected mappings to mirror.")
            return {"CANCELLED"}

        return {"FINISHED"}

class BAC_OT_Bake(bpy.types.Operator):
    bl_idname = "kumopult_bac.bake"
    bl_label = "Bake Animation"
    def execute(self, context):
        """Bake animation from target to owner armature."""
        scene = context.scene
        owner_obj = getattr(scene, "kumopult_bac_owner", None)
        state = safe_get_state()
        if not owner_obj or not state or not state.target:
            alert_error("Bake Failed", "Source or target armature not set")
            return {"CANCELLED"}
        
        target_anim = state.target.animation_data
        if not target_anim or not getattr(target_anim, "action", None):
            alert_error("No Source Action", f"Target armature '{state.target.name}' has no animation data or active action")
            return {"CANCELLED"}

        # Store original mode and switch to object mode for safe operation
        try:
            prev_mode = owner_obj.mode
            bpy.ops.object.mode_set(mode='OBJECT')
        except:
            self.report({'WARNING'}, "Could not set owner object to OBJECT mode before baking.")
            prev_mode = None


        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = owner_obj
        owner_obj.select_set(True)

        # 1. Disable non-BAC constraints on Owner
        non_bac_constraints = []
        for pose_bone in owner_obj.pose.bones:
            for con in list(pose_bone.constraints):
                # 修复 BUG：只检查非 BAC 约束
                if not con.name.startswith(BAC_CONSTRAINT_PREFIX):
                    try:
                        prev_enabled = con.enabled if hasattr(con, "enabled") else (not con.mute if hasattr(con, "mute") else True)
                        non_bac_constraints.append((con, prev_enabled))
                        set_constraint_enabled(con, False)
                    except AttributeError as e:
                        self.report({"WARNING"}, f"Cannot disable constraint '{con.name}' on '{pose_bone.name}': {str(e)}")

        # 2. Enable BAC constraints for the bake process
        state.preview = True

        # 3. Perform the Bake
        try:
            bake_args = {
                "frame_start": int(target_anim.action.frame_range[0]),
                "frame_end": int(target_anim.action.frame_range[1]),
                "only_selected": False,
                "visual_keying": True,
                "clear_constraints": False,
                "use_current_action": True,
                "bake_types": {'POSE'}
            }
            if state.target_animation_layer:
                bake_args["animation_layer"] = state.target_animation_layer
            
            bpy.ops.nla.bake(**bake_args)
            
        except RuntimeError as e:
            alert_error("Bake Error", f"Failed to bake animation: {str(e)}")
        finally:
            # 4. Disable BAC constraints again
            state.preview = False

        # 5. Restore non-BAC constraints
        for con, enabled in non_bac_constraints:
            try:
                set_constraint_enabled(con, enabled)
            except AttributeError as e:
                self.report({"WARNING"}, f"Cannot restore constraint '{con.name}': {str(e)}")

        # 6. Rename and protect the baked action
        if owner_obj.animation_data and owner_obj.animation_data.action:
            try:
                owner_obj.animation_data.action.name = f"{state.target.name}_baked"
                owner_obj.animation_data.action.use_fake_user = True
            except AttributeError as e:
                self.report({"WARNING"}, f"Cannot rename baked action: {str(e)}")
        
        # 7. Restore object mode
        if prev_mode:
            try:
                bpy.ops.object.mode_set(mode=prev_mode)
            except:
                self.report({'WARNING'}, "Could not restore previous object mode.")

        return {"FINISHED"}

# Panel draw
def draw_panel(layout):
    """Draw the main panel for bone mapping controls."""
    state = safe_get_state()
    if not state:
        return
    row = layout.row()
    
    # LEFT COLUMN: List and Controls 
    left = row.column_flow(columns=1, align=True)
    
    # 1. Header Box (Selection/Edit Type)
    box = left.box().row()
    if state.editing_type == 0:
        box_left = box.row(align=True)
        if state.selected_count == len(state.mappings) and len(state.mappings) > 0:
            box_left.operator('kumopult_bac.select_action', text='', emboss=False, icon='CHECKBOX_HLT').action = 'NONE'
        else:
            box_left.operator('kumopult_bac.select_action', text='', emboss=False, icon='CHECKBOX_DEHLT').action = 'ALL'
            if state.selected_count != 0:
                box_left.operator('kumopult_bac.select_action', text='', emboss=False, icon='UV_SYNC_SELECT').action = 'INVERSE'
    box_right = box.row(align=False)
    box_right.alignment = 'RIGHT'
    box_right.operator('kumopult_bac.select_edit_type', text='' if state.editing_type != 0 else 'Mapping', icon='PRESET').selected_type = 0
    box_right.operator('kumopult_bac.select_edit_type', text='' if state.editing_type != 1 else 'Rotation', icon='CON_ROTLIKE').selected_type = 1
    box_right.operator('kumopult_bac.select_edit_type', text='' if state.editing_type != 2 else 'Location', icon='CON_LOCLIKE').selected_type = 2
    box_right.operator('kumopult_bac.select_edit_type', text='' if state.editing_type != 3 else 'IK', icon='CON_KINEMATIC').selected_type = 3

    # 2. List Template
    left.template_list('BAC_UL_mappings', '', state, 'mappings', state, 'active_mapping', rows=7)
    
    # 3. Presets Box
    box = left.box().row(align=True)
    box.menu(BAC_MT_presets.__name__, text=BAC_MT_presets.bl_label, translate=False, icon='PRESET')
    box.operator(AddPresetBACMapping.bl_idname, text="", icon='ADD')
    box.operator(AddPresetBACMapping.bl_idname, text="", icon='REMOVE').remove_active = True
    box.separator()
    box.operator('kumopult_bac.open_preset_folder', text="", icon='FILE_FOLDER')

    # RIGHT COLUMN: Vertical Actions 
    right = row.column(align=True)
    right.separator()
    right.menu(BAC_MT_SettingMenu.__name__, text='', icon='DOWNARROW_HLT')
    right.separator()
    if state.owner and state.owner.mode != 'POSE':
        right.operator('kumopult_bac.list_action', icon='ADD', text='').action = 'ADD'
    elif state.target and state.target.mode != 'POSE':
        right.operator('kumopult_bac.list_action', icon='PRESET_NEW', text='').action = 'ADD_SELECT'
    else:
        right.operator('kumopult_bac.list_action', icon='PLUS', text='').action = 'ADD_ACTIVE'
    right.operator('kumopult_bac.list_action', icon='REMOVE', text='').action = 'REMOVE'
    right.operator('kumopult_bac.list_action', icon='TRIA_UP', text='').action = 'UP'
    right.operator('kumopult_bac.list_action', icon='TRIA_DOWN', text='').action = 'DOWN'
    right.separator()
    right.operator('kumopult_bac.child_mapping', icon='CON_CHILDOF', text='')
    # Name mapping
    name_map_op = right.operator('kumopult_bac.name_mapping', icon='CON_TRANSFORM_CACHE', text='')
    name_map_op.prefix = ''
    name_map_op.suffix = ''
    name_map_op.use_hierarchy = False
    
    right.operator('kumopult_bac.mirror_mapping', icon='MOD_MIRROR', text='')


class BAC_PT_Panel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BoneAnimCopy"
    bl_label = "Bone Animation Copy Tool"
    def draw(self, context):
        """Draw the main UI panel."""
        layout = self.layout
        scene = context.scene
        
        # Source/Target Selection Header
        split = layout.row().split(factor=0.2)
        left = split.column()
        right = split.column()
        
        # Row 1: Source Armature
        left.label(text='Source Armature:')
        right.prop(scene, 'kumopult_bac_owner', text='', icon='ARMATURE_DATA', translate=False)
        
        state = safe_get_state()
        
        if scene.kumopult_bac_owner and scene.kumopult_bac_owner.type == 'ARMATURE' and state:
            # Row 2: Target Armature
            left.label(text='Target Armature:')
            right.prop(state, 'selected_target', text='', icon='ARMATURE_DATA', translate=False)

            # Row 3: IK Chain Length
            left.label(text='IK Chain Len:') 
            right.prop(state, 'ik_chain_count', text='')

            # Row 4: Location Space
            left.label(text='Location Space:')
            right.prop(state, 'loc_space', text='')
            
            if not state.target:
                layout.label(text='Select a different armature object as target to continue', icon='INFO')
            else:
                # Main content
                draw_panel(layout.row())
                # Footer (Preview and Bake)
                row = layout.row()
                row.prop(state, 'preview', text='Preview Constraints', icon='HIDE_OFF' if state.preview else 'HIDE_ON')
                row.operator('kumopult_bac.bake', text='Bake Animation', icon='NLA')
        else:
            right.label(text='No source armature selected', icon='ERROR')

# --- Registration -----------------------------------------------------------

classes = (
    BAC_BoneMapping, BAC_State, BAC_UL_mappings, BAC_MT_SettingMenu, BAC_MT_presets,
    AddPresetBACMapping, BAC_OT_OpenPresetFolder, BAC_OT_SelectEditType, BAC_OT_SelectAction,
    BAC_OT_ListAction, BAC_OT_ChildMapping, BAC_OT_NameMapping, BAC_OT_MirrorMapping,
    BAC_OT_Bake, BAC_PT_Panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    # 注册 Scene 属性
    bpy.types.Scene.kumopult_bac_owner = bpy.props.PointerProperty(
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == 'ARMATURE',
        name="Source Armature"
    )
    # 注册 Armature 属性
    bpy.types.Armature.kumopult_bac = bpy.props.PointerProperty(type=BAC_State)
    print("BAC registered")

def unregister():
    try:
        del bpy.types.Scene.kumopult_bac_owner
    except AttributeError:
        pass
    try:
        del bpy.types.Armature.kumopult_bac
    except AttributeError:
        pass
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
    print("BAC unregistered")

if __name__ == "__main__":
    register()