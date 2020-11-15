import bpy
from .utilfuncs import *
from math import pi

class BAC_BoneMapping(bpy.types.PropertyGroup):
    def update_target(self, context):
        # 更改自身骨骼，需要先清空旧的约束再生成新的约束
        self.clear()
        self.target = self.selected_target
        self.apply()

    def update_source(self, context):
        # 更改来源骨骼，需要刷新约束上的目标
        self.apply()
    
    def update_rotoffs(self, context):
        if self.has_rotoffs:
            # 开启旋转偏移，需要新建约束
            self.update_offset(context)
        else:
            # 关闭旋转偏移，需要清除约束
            self.remove(self.get_rr())
        
    def update_loccopy(self, context):
        if self.has_loccopy:
            self.get_cp()
        else:
            self.remove(self.get_cp())
    
    def update_ik(self, context):
        if self.has_ik:
            self.get_ik()
        else:
            self.remove(self.get_ik())

    def update_offset(self, context):
        rr = self.get_rr()
        rr.to_min_x_rot = self.offset[0]
        rr.to_min_y_rot = self.offset[1]
        rr.to_min_z_rot = self.offset[2]

    selected_target: bpy.props.StringProperty(
        name="selected_target", 
        description="将对方骨骼的旋转复制到自身的哪根骨骼上？", 
        update=update_target
    )
    target: bpy.props.StringProperty(name="target")
    source: bpy.props.StringProperty(
        name="source", 
        description="从对方骨架中选择哪根骨骼作为动画来源？", 
        update=update_source
    )

    has_rotoffs: bpy.props.BoolProperty(
        name="rotation offset active", 
        description="附加额外约束，从而在原变换结果的基础上进行额外的旋转", 
        update=update_rotoffs
    )
    has_loccopy: bpy.props.BoolProperty(
        name="location copy active", 
        description="附加额外约束，从而使目标骨骼跟随原骨骼的世界坐标运动，通常应用于根骨骼、武器等", 
        update=update_loccopy
    )
    has_ik: bpy.props.BoolProperty(
        name="ik active",
        description="附加额外约束，从而使目标骨骼跟随原骨骼进行IK矫正，通常应用于手掌、脚掌",
        update=update_ik
    )
    offset: bpy.props.FloatVectorProperty(
        name="rotation offset", 
        description="世界坐标下复制旋转方向后，在本地坐标下进行的额外旋转偏移。通常只需要调整Y旋转", 
        min=-pi,
        max=pi,
        subtype='EULER',
        update=update_offset
    )
    con = {
        True:        get_cr,
        has_rotoffs: get_rr,
        has_loccopy: get_cp,
        has_ik:      get_ik
    }
    # last_target: bpy.props.StringProperty()
    # roll: bpy.props.FloatProperty()

    def to_string(self):
        return
    
    def target_valid(self):
        return get_state().get_target_pose().bones.get(self.target)
        # return (self.target != None and len(self.target) > 0)

    def source_valid(self):
        return get_state().get_source_pose().bones.get(self.source)
        # return (self.source != None and len(self.source) > 0)

    def is_valid(self):
        return (self.target_valid() != None and self.source_valid() != None)
    

    def apply(self):
        if not self.target_valid():
            return
        # apply mapping into constraint
        s = get_state()

        for key, value in self.con.items():
            if key:
                c = value()
                c.target = s.source
                c.subtarget = self.source

        if self.has_rotoffs:
            rr = self.get_rr()
            rr.to_min_x_rot = self.offset[0]
            rr.to_min_y_rot = self.offset[1]
            rr.to_min_z_rot = self.offset[2]

        # cr = self.get_cr()
        # cr.target = s.source
        # cr.subtarget = self.source

        # if self.has_loccopy:
        #     cp = self.get_cp()
        #     cp.target = s.source
        #     cp.subtarget = self.source

        # if self.has_ik:
        #     cp = self.get_ik()
        #     cp.target = s.source
        #     cp.subtarget = self.source


    def clear(self):
        for key, value in self.con.items():
            if key:
                self.remove(value())
    
    def remove(self, constraint):
        if not self.target_valid():
            return
        get_state().get_target_pose().bones.get(self.target).constraints.remove(constraint)
        
    '''
    def save(self):
        # save constraint roll into mapping
        # cr = self.get_cr()
        rr = self.get_rr()
        
        self.roll = rr.to_min_y_rot
    '''
    
    def get_cr(self):
        if self.target_valid():
            tc = self.target_valid().constraints
        else:
            return None
        
        def new_cr():
            cr = tc.new(type='COPY_ROTATION')
            cr.name = 'BAC_ROT_COPY'
            cr.show_expanded = False
            cr.target = get_state().source
            cr.subtarget = self.source
            return cr
        
        return tc.get('BAC_ROT_COPY') or new_cr()
        
    def get_rr(self):
        if self.target_valid():
            tc = self.target_valid().constraints
        else:
            return None
        
        def new_rr():
            rr = tc.new(type='TRANSFORM')
            rr.name = 'BAC_ROT_ROLL'
            rr.map_to = 'ROTATION'
            rr.owner_space = 'LOCAL'
            rr.to_euler_order = 'YXZ'
            rr.show_expanded = False
            rr.target = get_axes()
            return rr
        
        return tc.get('BAC_ROT_ROLL') or new_rr()
        
    def get_cp(self):
        if self.target_valid():
            tc = self.target_valid().constraints
        else:
            return None

        def new_cp():
            cp = tc.new(type='COPY_LOCATION')
            cp.name = 'BAC_LOC_COPY'
            cp.show_expanded = False
            cp.target = get_state().source
            cp.subtarget = self.source
            return cp
        
        return tc.get('BAC_LOC_COPY') or new_cp()

    def get_ik(self):
        if self.target_valid():
            tc = self.target_valid().constraints
        else:
            return None
        
        def new_ik():
            ik = tc.new(type='IK')
            ik.name = 'BAC_IK'
            ik.show_expanded = False
            ik.target = get_state().source
            ik.subtarget = self.source
            ik.chain_count = 2
            ik.use_tail = False
            return ik
        
        return tc.get('BAC_IK') or new_ik()

classes = (
	BAC_BoneMapping,
)