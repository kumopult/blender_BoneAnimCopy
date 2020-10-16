import bpy
from .utilfuncs import *

class BAC_BoneMapping(bpy.types.PropertyGroup):
    '''
    def set_source(self, value):
        # 更改来源骨骼，需要刷新约束上的目标
        self.source = value
        self.apply()

    def set_target(self, value):
        # 更改自身骨骼，需要先清空旧的约束再生成新的约束
        self.clear()
        self.target = value
        self.apply()
    '''
    def update_target(self, context):
        # 更改自身骨骼，需要先清空旧的约束再生成新的约束
        self.clear()
        self.target = self.selected_target
        self.apply()

    def update_source(self, context):
        # 更改来源骨骼，需要刷新约束上的目标
        self.apply()
    
    def update_offset(self, context):
        rr = self.get_rr()
        rr.to_min_y_rot = self.offset[0]
        rr.to_min_x_rot = self.offset[1]
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
    offset: bpy.props.FloatVectorProperty(
        name="offset", 
        description="世界坐标下复制旋转方向后，在本地坐标下进行的额外旋转偏移，顺序为YXZ欧拉。通常只需要调整Y旋转", 
        min=-180,
        max=180,
        update=update_offset
    )
    # last_target: bpy.props.StringProperty()
    # roll: bpy.props.FloatProperty()

    
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
            return None
        # apply mapping into constraint
        s = get_state()
        
        cr = self.get_cr()
        rr = self.get_rr()
        
        cr.target = s.source
        cr.subtarget = self.source
        rr.to_min_y_rot = self.offset[0]
        rr.to_min_x_rot = self.offset[1]
        rr.to_min_z_rot = self.offset[2]
        # rr.to_min_y_rot = self.roll
    
    def clear(self):
        if not self.target_valid():
            return None
        tc = get_state().get_target_pose().bones.get(self.target).constraints
        tc.remove(self.get_cr())
        tc.remove(self.get_rr())
        
    '''
    def save(self):
        # save constraint roll into mapping
        # cr = self.get_cr()
        rr = self.get_rr()
        
        self.roll = rr.to_min_y_rot
    '''
    
    def get_cr(self):
        t = get_state().get_target_pose().bones.get(self.target)
        if t:
            tc = t.constraints
        else:
            return None
        
        def new_cr():
            cr = tc.new(type='COPY_ROTATION')
            cr.name = 'BAC_ROT_COPY'
            return cr
        
        return tc.get('BAC_ROT_COPY') or new_cr()
        
    def get_rr(self):
        t = get_state().get_target_pose().bones.get(self.target)
        if t:
            tc = t.constraints
        else:
            return None
        
        def new_rr():
            rr = tc.new(type='TRANSFORM')
            rr.name = 'BAC_ROT_ROLL'
            rr.map_to = 'ROTATION'
            rr.owner_space = 'LOCAL'
            rr.to_euler_order = 'YXZ'
            rr.target = get_axes()
            rr.mute = True
            return rr
        
        return tc.get('BAC_ROT_ROLL') or new_rr()



classes = (
	BAC_BoneMapping,
)