import bpy
from .utilfuncs import *
from math import pi
from mathutils import Matrix, Euler

class BAC_BoneMapping(bpy.types.PropertyGroup):
    def update_owner(self, context):
        # 更改自身骨骼，需要先清空旧的约束再生成新的约束
        self.clear()
        self.owner = self.selected_owner
        if self.get_owner() != None and len(self.get_owner().constraints) > 0:
            alert_error('所选骨骼上包含其它约束', '本插件所生成的约束(名称以BAC开头)若与其它约束混用，可能导致烘焙效果出现偏差。建议避免映射这根骨骼')
        self.apply()

    def update_target(self, context):
        # 更改目标骨骼，需要刷新约束上的目标
        s = get_state()
        if self.is_valid() and s.calc_offset:
            # 计算旋转偏移
            euler_offset = ((s.target.matrix_world @ self.get_target().matrix).inverted() @ (s.owner.matrix_world @ self.get_owner().matrix)).to_euler()
            if s.ortho_offset:
                step = pi * 0.5
                euler_offset[0] = round(euler_offset[0] / step) * step
                euler_offset[1] = round(euler_offset[1] / step) * step
                euler_offset[2] = round(euler_offset[2] / step) * step
            if euler_offset != None and euler_offset != Euler((0,0,0)):
                self.offset[0] = euler_offset[0]
                self.offset[1] = euler_offset[1]
                self.offset[2] = euler_offset[2]
                self.has_rotoffs = True
        self.apply()
    
    def update_rotcopy(self, context):
        s = get_state()
        cr = self.get_cr()
        cr.target = s.target
        cr.subtarget = self.target
        set_enable(cr, self.is_valid() and s.preview)
    
    def update_rotoffs(self, context):
        s = get_state()
        rr = self.get_rr()
        if self.has_rotoffs:
            rr.to_min_x_rot = self.offset[0]
            rr.to_min_y_rot = self.offset[1]
            rr.to_min_z_rot = self.offset[2]
            rr.target = rr.space_object = s.target
            rr.subtarget = rr.space_subtarget = self.target
            set_enable(rr, self.is_valid() and s.preview)
        else:
            self.remove(rr)
        
    def update_loccopy(self, context):
        s = get_state()
        cp = self.get_cp()
        if self.has_loccopy:
            cp.use_x = self.loc_axis[0]
            cp.use_y = self.loc_axis[1]
            cp.use_z = self.loc_axis[2]
            cp.target = s.target
            cp.subtarget = self.target
            set_enable(cp, self.is_valid() and s.preview)
        else:
            self.remove(cp)
    
    def update_ik(self, context):
        s = get_state()
        ik = self.get_ik()
        if self.has_ik:
            ik.influence = self.ik_influence
            ik.target = s.target
            ik.subtarget = self.target
            set_enable(ik, self.is_valid() and s.preview)
        else:
            self.remove(ik)

    selected_owner: bpy.props.StringProperty(
        name="自身骨骼", 
        description="将对方骨骼的旋转复制到自身的哪根骨骼上？", 
        update=update_owner
    )
    owner: bpy.props.StringProperty()
    target: bpy.props.StringProperty(
        name="约束目标", 
        description="从对方骨架中选择哪根骨骼作为约束目标？", 
        update=update_target
    )

    has_rotoffs: bpy.props.BoolProperty(
        name="旋转偏移", 
        description="附加额外约束，从而在原变换结果的基础上进行额外的旋转", 
        update=update_rotoffs
    )
    has_loccopy: bpy.props.BoolProperty(
        name="位置映射", 
        description="附加额外约束，从而使目标骨骼跟随原骨骼的世界坐标运动，通常应用于根骨骼、武器等", 
        update=update_loccopy
    )
    has_ik: bpy.props.BoolProperty(
        name="IK",
        description="附加额外约束，从而使目标骨骼跟随原骨骼进行IK矫正，通常应用于手掌、脚掌",
        update=update_ik
    )

    offset: bpy.props.FloatVectorProperty(
        name="旋转偏移量", 
        description="世界坐标下复制旋转方向后，在那基础上进行的额外旋转偏移。通常只需要调整Y旋转", 
        min=-pi,
        max=pi,
        subtype='EULER',
        update=update_rotoffs
    )
    loc_axis: bpy.props.BoolVectorProperty(
        name="位置映射轴向",
        default=[True, True, True],
        update=update_loccopy
    )
    ik_influence: bpy.props.FloatProperty(
        name="IK影响权重",
        default=1,
        min=0,
        max=1,
        update=update_ik
    )

    def update_selected(self, context):
        get_state().selected_count += 1 if self.selected else -1
    
    selected: bpy.props.BoolProperty(update=update_selected)

    
    def get_owner(self):
        return get_state().get_owner_pose().bones.get(self.owner)

    def get_target(self):
        return get_state().get_target_pose().bones.get(self.target)

    def is_valid(self):
        return (self.get_owner() != None and self.get_target() != None)
    

    def apply(self):
        if not self.get_owner():
            return
        self.update_rotcopy(bpy.context)
        self.update_rotoffs(bpy.context)
        self.update_loccopy(bpy.context)
        self.update_ik(bpy.context)


    def clear(self):
        self.remove(self.get_cr())
        self.remove(self.get_rr())
        self.remove(self.get_cp())
        self.remove(self.get_ik())
    
    def remove(self, constraint):
        if not self.get_owner():
            return
        self.get_owner().constraints.remove(constraint)

    def get_cr(self) -> bpy.types.Constraint:
        if self.get_owner():
            con = self.get_owner().constraints
        else:
            return None
        
        def new_cr():
            cr = con.new(type='COPY_ROTATION')
            cr.name = 'BAC_ROT_COPY'
            cr.show_expanded = False
            return cr
        
        return con.get('BAC_ROT_COPY') or new_cr()
        
    def get_rr(self) -> bpy.types.Constraint:
        if self.get_owner():
            con = self.get_owner().constraints
        else:
            return None
        
        def new_rr():
            rr = con.new(type='TRANSFORM')
            rr.name = 'BAC_ROT_ROLL'
            rr.map_to = 'ROTATION'
            rr.owner_space = 'CUSTOM'
            rr.show_expanded = False
            return rr
        
        return con.get('BAC_ROT_ROLL') or new_rr()
        
    def get_cp(self) -> bpy.types.Constraint:
        if self.get_owner():
            con = self.get_owner().constraints
        else:
            return None

        def new_cp():
            cp = con.new(type='COPY_LOCATION')
            cp.name = 'BAC_LOC_COPY'
            cp.show_expanded = False
            return cp
        
        return con.get('BAC_LOC_COPY') or new_cp()

    def get_ik(self) -> bpy.types.Constraint:
        if self.get_owner():
            con = self.get_owner().constraints
        else:
            return None
        
        def new_ik():
            ik = con.new(type='IK')
            ik.name = 'BAC_IK'
            ik.show_expanded = False
            ik.chain_count = 2
            ik.use_tail = False
            return ik
        
        return con.get('BAC_IK') or new_ik()

classes = (
	BAC_BoneMapping,
)