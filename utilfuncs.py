import bpy
import difflib

def get_state():
    return bpy.context.object.kumopult_bac

def get_axes():

    def new_axes():
        axes = bpy.data.objects.new(name='BAC_AXES', object_data=None)
        axes.use_fake_user = True
        return axes
    
    return bpy.data.objects.get('BAC_AXES') or new_axes()

def get_similar_bone(target_name, source_bones):
    similar_name = ''
    similar_ratio = 0

    for source in source_bones:
        r = difflib.SequenceMatcher(None, target_name, source.name).quick_ratio()
        if r > similar_ratio:
            similar_ratio = r
            similar_name = source.name
    
    return similar_name

def get_mirror_bone_by_location(bone):
    if type(bone) == str:
        bone = get_state().get_target_armature().get(bone)
    return None

def alert_error(title, message):
	def draw(self, context):
		self.layout.label(text=message)

	bpy.context.window_manager.popup_menu(draw, title=title, icon='ERROR')