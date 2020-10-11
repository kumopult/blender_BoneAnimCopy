import bpy


def get_state():
    return bpy.context.object.kumopult_bac

def get_axes():

    def new_axes():
        axes = bpy.data.objects.new(name='BAC_AXES', object_data=None)
        axes.use_fake_user = True
        return axes
    
    return bpy.data.objects.get('BAC_AXES') or new_axes()
