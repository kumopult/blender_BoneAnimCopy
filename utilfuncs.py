import bpy

def get_state():
    if bpy.context.scene.kumopult_bac_owner == None:
        return None
    return bpy.context.scene.kumopult_bac_owner.data.kumopult_bac

def set_enable(con: bpy.types.Constraint, state):
    if bpy.app.version >= (3, 0, 0):
        con.enabled = state
    else:
        con.mute = not state

def alert_error(title, message):
	def draw(self, context):
		self.layout.label(text=message)

	bpy.context.window_manager.popup_menu(draw, title=title, icon='ERROR')
