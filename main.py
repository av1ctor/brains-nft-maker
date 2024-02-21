import bpy
import random
import math
import json

## https://docs.blender.org/api/4.0

class Utils():
    def find_traits(scene):
        traits = []
        for coll in scene.collection.children:
            if coll.name.lower().endswith("traits"):
                for obj in coll.objects:
                    traits.append(obj)
        return traits

    def hide_objects(traits):
        for obj in traits:
            obj.hide_render = True
            obj.hide_set(True)
            
    def insert_hide_keyframe(obj, hide, frame_num):
        obj.hide_render = hide
        obj.keyframe_insert(data_path='hide_render', frame=frame_num)

    def insert_all_hide_keyframes(traits, hide, frame_num):
        for obj in traits:
            Utils.insert_hide_keyframe(obj, hide, frame_num)
    
    def delete_all_hide_keyframes(scene, traits):
        actions = []
        if bpy.data.actions:
            frame_ranges = [action.frame_range for action in bpy.data.actions]
            actions = sorted(set([frame for frames in frame_ranges for frame in frames]))

        for obj in traits:
            if len(actions) >= 1:
                for frame in range(0, int(actions[-1] + 1)):
                    try:
                        obj.keyframe_delete(data_path='hide_render', frame=frame)
                    except:
                        continue
                    
    def delete_actions(traits):
        for action in bpy.data.actions:
            for trait in traits:
                if action.name.startswith(trait.name):
                    bpy.data.actions.remove(action)
                    break

class LookupOp(bpy.types.Operator):
    bl_idname = "wm.lookup_traits"
    bl_label = "Lookup Traits"

    def execute(self, context):
        scene = context.scene
        settings = scene.na_settings

        settings.clear()

        traits = Utils.find_traits(scene)

        for obj in traits:
            item = settings.add()
            item.name = obj.name
    
        return {'FINISHED'}

class GenerateOp(bpy.types.Operator):
    bl_idname = "wm.generate_nfts"
    bl_label = "Generate NFT's"

    def execute(self, context):
        scene = context.scene
        settings = scene.na_settings
        
        bpy.ops.object.select_all(action='DESELECT')
        
        traits = Utils.find_traits(scene)

        Utils.hide_objects(traits)
        Utils.delete_actions(traits)
        Utils.delete_all_hide_keyframes(scene, traits)
        Utils.insert_all_hide_keyframes(traits, True, 0)
        
        scene.frame_set(1)
        for num in range(1, 21):
            trait = random.choice(traits)
            Utils.insert_hide_keyframe(trait, False, num)
            Utils.insert_hide_keyframe(trait, True, num+1)
            #self.export_scene(num)

        Utils.hide_objects(traits)

        return {'FINISHED'}
    
    def export_scene(self, num):
        models_path = bpy.path.abspath('//models/' + str(num))
        print(models_path)
        bpy.ops.export_scene.gltf(
            filepath=models_path, 
            use_visible=True,
            export_yup=True, 
            export_apply=False, 
            export_materials='EXPORT', 
            export_texcoords=True, 
            export_colors=True, 
            export_format='GLB', 
            export_animations=True,
            export_animation_mode='ACTIONS',
            export_anim_single_armature=True,
            export_reset_pose_bones=True,
            export_optimize_animation_size=True,
            export_optimize_animation_keep_anim_armature=True,
            export_rest_position_armature=True,
            export_influence_nb=4,
            export_force_sampling=True, 
            export_nla_strips=False, 
            export_negative_frame='SLIDE',
            export_morph=True, 
            export_morph_normal=True, 
            export_morph_tangent=True,
            export_morph_reset_sk_data=True,
            export_lights=False,
            export_cameras=False)

class CleanupOp(bpy.types.Operator):
    bl_idname = "wm.clean_up"
    bl_label = "Clean up"

    def execute(self, context):
        scene = context.scene
        settings = scene.na_settings
        
        bpy.ops.object.select_all(action='DESELECT')
        
        traits = Utils.find_traits(scene)

        Utils.hide_objects(traits)
        Utils.delete_actions(traits)
        Utils.delete_all_hide_keyframes(scene, traits)
        
        return {'FINISHED'}

class TraitProps(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name", default="Unknown")
    probability: bpy.props.FloatProperty(name="Probability", default=10.0)

class MainPanel(bpy.types.Panel):
    bl_label = "Neural Arena NFT Maker"
    bl_idname = "SCENE_PT_layout"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    
    def __new__():
        bpy.context.scene.na_settings.clear()
        return super().__new__()

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # rarities
        layout.label(text="Traits:")
        for i in range(len(scene.na_settings)):
            row = layout.row()
            row.label(text=scene.na_settings[i].name)
            row.prop(scene.na_settings[i], 'probability')

        row = layout.row()
        row.separator()

        # actions
        layout.label(text="Actions:")

        split = layout.split()
        col = split.column()
        col.operator("wm.lookup_traits")

        col = split.column(align=True)
        col.operator("wm.generate_nfts")

        split = layout.split()
        col = split.column()
        col.operator("wm.clean_up")


def register():
    bpy.utils.register_class(LookupOp)
    bpy.utils.register_class(GenerateOp)
    bpy.utils.register_class(CleanupOp)
    
    bpy.utils.register_class(TraitProps)
    bpy.types.Scene.na_settings = bpy.props.CollectionProperty(type=TraitProps)
    
    bpy.utils.register_class(MainPanel)


def unregister():
    bpy.utils.unregister_class(MainPanel)
    bpy.utils.unregister_class(TraitProps)
    bpy.utils.register_class(CleanupOp)
    bpy.utils.unregister_class(GenerateOp)
    bpy.utils.unregister_class(LookupOp)
    
if __name__ == "__main__":
    register()
