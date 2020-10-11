import bpy
from .utilfuncs import *

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
        # cr = self.get_cr()
        rr = self.get_rr()
        
        self.roll = rr.to_min_y_rot
    
    
    def get_cr(self):
        s = get_state()
        tc = s.target.pose.bones[self.target].constraints
        
        def new_cr():
            cr = tc.new(type='COPY_ROTATION')
            cr.name = 'BAC_ROT_COPY'
            return cr
        
        # cr = tc.get('BAC_ROT_COPY') or new_cr()
        return tc.get('BAC_ROT_COPY') or new_cr()
        
    def get_rr(self):
        s = get_state()
        tc = s.target.pose.bones[self.target].constraints
        
        def new_rr():
            rr = tc.new(type='TRANSFORM')
            rr.name = 'BAC_ROT_ROLL'
            rr.map_to = 'ROTATION'
            rr.owner_space = 'LOCAL'
            rr.to_euler_order = 'YXZ'
            rr.target = get_axes()
            return rr
        
        # rr = tc.get('BAC_ROT_ROLL') or new_rr()
        return tc.get('BAC_ROT_ROLL') or new_rr()
    
    def clear(self):
        s = get_state()
        c = s.target.pose.bones[self.target].constraints
        c.remove(self.get_cr)
        c.remove(self.get_rr)



classes = (
	BAC_BoneMapping,
)