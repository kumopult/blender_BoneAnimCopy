import bpy
import difflib
from math import pi

def get_state():
    return bpy.context.object.kumopult_bac

def get_axes():

    def new_axes():
        axes = bpy.data.objects.new(name='BAC_AXES', object_data=None)
        axes.use_fake_user = True
        return axes
    
    return bpy.data.objects.get('BAC_AXES') or new_axes()

def get_similar_bone(owner_name, target_bones):
    similar_name = ''
    similar_ratio = 0

    for target in target_bones:
        r = difflib.SequenceMatcher(None, owner_name, target.name).quick_ratio()
        if r > similar_ratio:
            similar_ratio = r
            similar_name = target.name
    
    return similar_name

def get_mirror_bone_by_location(bone):
    if type(bone) == str:
        bone = get_state().get_owner_armature().get(bone)
    return None

def calc_offset(owner, target):
    if owner != None and target != None:
        euler_offset = (owner.matrix @ target.matrix.inverted()).to_euler()
        step = pi * 0.5
        euler_offset[0] = round(euler_offset[0] / step) * step
        euler_offset[1] = round(euler_offset[1] / step) * step
        euler_offset[2] = round(euler_offset[2] / step) * step
        return euler_offset
    else:
        return None

def alert_error(title, message):
	def draw(self, context):
		self.layout.label(text=message)

	bpy.context.window_manager.popup_menu(draw, title=title, icon='ERROR')