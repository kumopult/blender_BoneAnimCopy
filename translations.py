# translations.py
# Bone Animation Copy Tool 翻译文件

translations_dict = {
    "zh_HANS": {
        # bl_info 中的描述
        ("*", "Copy animation between armatures using bone constraints."): "使用骨骼约束在骨架之间复制动画。",
        
        # BAC_BoneMapping 属性标签
        ("*", "Owner Bone"): "源骨骼",
        ("*", "Target Bone"): "目标骨骼",
        ("*", "Rotation Offset"): "旋转偏移",
        ("*", "Location Axes"): "位置轴",
        ("*", "IK Influence"): "IK 影响",
        
        # BAC_BoneMapping 属性描述
        ("*", "Rotation Offset"): "旋转偏移",
        ("*", "IK Influence"): "IK 影响",
        
        # BAC_State 属性
        ("*", "World Space"): "世界空间",
        ("*", "Pose Space"): "姿态空间",
        ("*", "Local Space"): "局部空间",
        ("*", "Parent Space"): "父级空间",
        ("*", "Location Space"): "位置空间",
        ("*", "Coordinate space for location copy constraints"): "位置复制约束的坐标空间",
        ("*", "IK Chain Length"): "IK 链长度",
        ("*", "The number of bones in the IK chain (0 means to the root bone)"): "IK 链中的骨骼数量（0 表示到根骨骼）",
        ("*", "Synchronize bone selection with mappings"): "将骨骼选择与映射同步",
        ("*", "Calculate rotation offset automatically"): "自动计算旋转偏移",
        ("*", "Snap offset to orthogonal angles"): "将偏移吸附到正交角度",
        ("*", "Target animation layer for baking"): "烘焙的目标动画层",
        
        # BAC_MT_SettingMenu
        ("*", "Settings"): "设置",
        ("*", "Animation Layer"): "动画层",
        
        # BAC_MT_presets
        ("*", "Mapping Presets"): "映射预设",
        
        # AddPresetBACMapping
        ("*", "Add BAC Mappings Preset"): "添加 BAC 映射预设",
        
        # BAC_OT_OpenPresetFolder
        ("*", "Open Preset Folder"): "打开预设文件夹",
        
        # BAC_OT_SelectEditType
        ("*", "Select Edit Type"): "选择编辑类型",
        
        # BAC_OT_SelectAction
        ("*", "List Select Action"): "删除映射",
        
        # BAC_OT_ListAction
        ("*", "List Basic Actions"): "添加映射",
        
        # BAC_OT_ChildMapping
        ("*", "Child Mapping"): "子级映射",
        
        # BAC_OT_NameMapping
        ("*", "Name Mapping"): "名称映射",
        ("*", "Prefix to match in bone names"): "骨骼名称中匹配的前缀",
        ("*", "Suffix to match in bone names"): "骨骼名称中匹配的后缀",
        ("*", "Match bones based on hierarchy"): "基于层级匹配骨骼",
        
        # BAC_OT_MirrorMapping
        ("*", "Mirror Mapping"): "镜像映射",
        
        # BAC_OT_Bake
        ("*", "Bake Animation"): "烘焙动画",
        
        # BAC_PT_Panel
        ("*", "Bone Animation Copy Tool"): "骨骼动画复制工具",
        ("*", "BoneAnimCopy"): "骨骼动画复制",
        ("*", "Source Armature:"): "源骨架：",
        ("*", "Target Armature:"): "目标骨架：",
        ("*", "IK Chain Len:"): "IK 链长度：",
        ("*", "Location Space:"): "位置空间：",
        ("*", "Select a different armature object as target to continue"): "选择另一个骨架对象作为目标以继续",
        ("*", "No source armature selected"): "未选择源骨架",
        
        # Panel 中的按钮和标签
        ("*", "Preview Constraints"): "预览约束",
        ("*", "Bake Animation"): "烘焙动画",
        
        # 布局中的文本
        ("*", "Mapping"): "映射",
        ("*", "Rotation"): "旋转",
        ("*", "Location"): "位置",
        ("*", "IK"): "IK",
        
        # 报告信息
        ("*", "Bone '{}' has multiple children. Skipping child mapping."): "骨骼 '{}' 有多个子级。跳过子级映射。",
        ("*", "No active or selected mappings to process."): "没有要处理的激活或选中的映射。",
        ("*", "No eligible single-child bones found for mapping or mapping not selected/active."): "未找到符合条件的单子级骨骼进行映射，或映射未被选中/激活。",
        ("*", "No matching bone found for '{}' (Score: {:.2f})"): "未找到与 '{}' 匹配的骨骼（匹配度：{:.2f}）",
        ("*", "No mirrored bones found for mapping: '{}' -> '{}'"): "未找到映射的镜像骨骼：'{}' -> '{}'",
        ("*", "No active or selected mappings to mirror."): "没有要镜像的激活或选中的映射。",
        ("*", "Bake Failed"): "烘焙失败",
        ("*", "Source or target armature not set"): "未设置源骨架或目标骨架",
        ("*", "No Source Action"): "没有源动作",
        ("*", "Target armature '{}' has no animation data or active action"): "目标骨架 '{}' 没有动画数据或激活的动作",
        ("*", "Could not set owner object to OBJECT mode before baking."): "烘焙前无法将源对象设置为物体模式。",
        ("*", "Cannot disable constraint '{}' on '{}': {}"): "无法禁用 '{}' 上的约束 '{}'：{}",
        ("*", "Bake Error"): "烘焙错误",
        ("*", "Failed to bake animation: {}"): "烘焙动画失败：{}",
        ("*", "Cannot restore constraint '{}': {}"): "无法恢复约束 '{}'：{}",
        ("*", "Cannot rename baked action: {}"): "无法重命名烘焙动作：{}",
        ("*", "Could not restore previous object mode."): "无法恢复之前的物体模式。",
        ("*", "Add"): "添加",
        ("*", "Add Selected"): "添加所选",
        ("*", "Add Active"): "添加激活",
        ("*", "Remove"): "删除",
        ("*", "Move Up"): "上移",
        ("*", "Move Down"): "下移",
        ("*", "Mapping"): "映射",
    },
    "zh_HANT": {
        # bl_info 中的描述
        ("*", "Copy animation between armatures using bone constraints."): "使用骨骼約束在骨架之間複製動畫。",
        
        # BAC_BoneMapping 属性标签
        ("*", "Owner Bone"): "源骨骼",
        ("*", "Target Bone"): "目標骨骼",
        ("*", "Rotation Offset"): "旋轉偏移",
        ("*", "Location Axes"): "位置軸",
        ("*", "IK Influence"): "IK 影響",
        
        # BAC_BoneMapping 属性描述
        ("*", "Rotation Offset"): "旋轉偏移",
        ("*", "IK Influence"): "IK 影響",
        
        # BAC_State 属性
        ("*", "World Space"): "世界空間",
        ("*", "Pose Space"): "姿態空間",
        ("*", "Local Space"): "局部空間",
        ("*", "Parent Space"): "父級空間",
        ("*", "Location Space"): "位置空間",
        ("*", "Coordinate space for location copy constraints"): "位置複製約束的座標空間",
        ("*", "IK Chain Length"): "IK 鏈長度",
        ("*", "The number of bones in the IK chain (0 means to the root bone)"): "IK 鏈中的骨骼數量（0 表示到根骨骼）",
        ("*", "Synchronize bone selection with mappings"): "將骨骼選擇與映射同步",
        ("*", "Calculate rotation offset automatically"): "自動計算旋轉偏移",
        ("*", "Snap offset to orthogonal angles"): "將偏移吸附到正交角度",
        ("*", "Target animation layer for baking"): "烘焙的目標動畫層",
        
        # BAC_MT_SettingMenu
        ("*", "Settings"): "設定",
        ("*", "Animation Layer"): "動畫層",
        
        # BAC_MT_presets
        ("*", "Mapping Presets"): "映射預設",
        
        # AddPresetBACMapping
        ("*", "Add BAC Mappings Preset"): "添加 BAC 映射預設",
        
        # BAC_OT_OpenPresetFolder
        ("*", "Open Preset Folder"): "打開預設資料夾",
        
        # BAC_OT_SelectEditType
        ("*", "Select Edit Type"): "選擇編輯類型",
        
        # BAC_OT_SelectAction
        ("*", "List Select Action"): "去除映射",
        
        # BAC_OT_ListAction
        ("*", "List Basic Actions"): "添加映射",
        
        # BAC_OT_ChildMapping
        ("*", "Child Mapping"): "子級映射",
        
        # BAC_OT_NameMapping
        ("*", "Name Mapping"): "名稱映射",
        ("*", "Prefix to match in bone names"): "骨骼名稱中匹配的前綴",
        ("*", "Suffix to match in bone names"): "骨骼名稱中匹配的後綴",
        ("*", "Match bones based on hierarchy"): "基於層級匹配骨骼",
        
        # BAC_OT_MirrorMapping
        ("*", "Mirror Mapping"): "鏡像映射",
        
        # BAC_OT_Bake
        ("*", "Bake Animation"): "烘焙動畫",
        
        # BAC_PT_Panel
        ("*", "Bone Animation Copy Tool"): "骨骼動畫複製工具",
        ("*", "BoneAnimCopy"): "骨骼動畫複製",
        ("*", "Source Armature:"): "源骨架：",
        ("*", "Target Armature:"): "目標骨架：",
        ("*", "IK Chain Len:"): "IK 鏈長度：",
        ("*", "Location Space:"): "位置空間：",
        ("*", "Select a different armature object as target to continue"): "選擇另一個骨架物件作為目標以繼續",
        ("*", "No source armature selected"): "未選擇源骨架",
        
        # Panel 中的按钮和标签
        ("*", "Preview Constraints"): "預覽約束",
        ("*", "Bake Animation"): "烘焙動畫",
        
        # 布局中的文本
        ("*", "Mapping"): "映射",
        ("*", "Rotation"): "旋轉",
        ("*", "Location"): "位置",
        ("*", "IK"): "IK",
        
        # 报告信息
        ("*", "Bone '{}' has multiple children. Skipping child mapping."): "骨骼 '{}' 有多個子級。跳過子級映射。",
        ("*", "No active or selected mappings to process."): "沒有要處理的啟用或選中的映射。",
        ("*", "No eligible single-child bones found for mapping or mapping not selected/active."): "未找到符合條件的單子級骨骼進行映射，或映射未被選中/啟用。",
        ("*", "No matching bone found for '{}' (Score: {:.2f})"): "未找到與 '{}' 匹配的骨骼（匹配度：{:.2f}）",
        ("*", "No mirrored bones found for mapping: '{}' -> '{}'"): "未找到映射的鏡像骨骼：'{}' -> '{}'",
        ("*", "No active or selected mappings to mirror."): "沒有要鏡像的啟用或選中的映射。",
        ("*", "Bake Failed"): "烘焙失敗",
        ("*", "Source or target armature not set"): "未設置源骨架或目標骨架",
        ("*", "No Source Action"): "沒有源動作",
        ("*", "Target armature '{}' has no animation data or active action"): "目標骨架 '{}' 沒有動畫資料或啟用的動作",
        ("*", "Could not set owner object to OBJECT mode before baking."): "烘焙前無法將源物件設定為物體模式。",
        ("*", "Cannot disable constraint '{}' on '{}': {}"): "無法禁用 '{}' 上的約束 '{}'：{}",
        ("*", "Bake Error"): "烘焙錯誤",
        ("*", "Failed to bake animation: {}"): "烘焙動畫失敗：{}",
        ("*", "Cannot restore constraint '{}': {}"): "無法恢復約束 '{}'：{}",
        ("*", "Cannot rename baked action: {}"): "無法重新命名烘焙動作：{}",
        ("*", "Could not restore previous object mode."): "無法恢復之前的物體模式。",
        ("*", "Add"): "添加",
        ("*", "Add Selected"): "添加所選",
        ("*", "Add Active"): "添加啟用",
        ("*", "Remove"): "刪除",
        ("*", "Move Up"): "上移",
        ("*", "Move Down"): "下移",
        ("*", "Mapping"): "映射",
    },
}