import bpy
from math import pi

def get_state():
    return bpy.context.object.kumopult_bac

def get_axes():

    def new_axes():
        axes = bpy.data.objects.new(name='BAC_AXES', object_data=None)
        axes.use_fake_user = True
        return axes
    
    return bpy.data.objects.get('BAC_AXES') or new_axes()

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

# 二进制相关操作
# def bin_set_at(bin, index, value):
#     if value:
#         return bin | (1 << index)
#     else:
#         return bin & ~(1 << index)

# def bin_insert_at(bin, index, value=0):
#     mask  = (1 << (index)) - 1
#     left  = bin & ~ mask
#     right = bin & mask
#     return (left << 1) | right | (value << index)

# def bin_remove_at(bin, index):
#     mask  = (1 << (index)) - 1
#     left  = bin & ~ mask << 1
#     right = bin & mask
#     return (left >> 1) | right

# def bin_reverse_at(bin, index):
#     mask = 1 << index
#     return (bin & (~ mask)) | (bin ^ mask)
# def bin_reverse(bin, length):
#     reverse_bin = 0
#     for i in range(length):
#         reverse_bin |= ((bin >> i) & 1) << (length - i - 1)
#     return reverse_bin

# def bin_exchange_at(bin, x, y):
#     ret = bin & (~(1 << x)) & (~(1 << y))
#     ret = ret | (((bin >> y) & 1) << x) | (((bin >> x) & 1) << y)
#     return ret