import bpy
import random
import math
import json

## https://docs.blender.org/api/4.0

nfts_traits = []

class ObjectHelper():
    def hide_objects(objects):
        for obj in objects:
            obj.hide_render = True
            obj.hide_set(True)
            
                    
class ActionsHelper:
    def delete_actions(objects):
        for action in bpy.data.actions:
            for obj in objects:
                if action.name.startswith(obj.name):
                    bpy.data.actions.remove(action)
                    break
                
class KeyframeHelper:
    def insert_hide_render(obj, hide, frame_num):
        obj.hide_render = hide
        obj.hide_set(hide)
        obj.keyframe_insert(data_path='hide_render', frame=frame_num)

    def insert_all_hide_render(objects, hide, frame_num):
        for obj in objects:
            KeyframeHelper.insert_hide_render(obj, hide, frame_num)
    
    def delete_all_hide_render(scene, objects):
        actions = []
        if bpy.data.actions:
            frame_ranges = [action.frame_range for action in bpy.data.actions]
            actions = sorted(set([frame for frames in frame_ranges for frame in frames]))

        for obj in objects:
            if len(actions) >= 1:
                for frame in range(0, int(actions[-1] + 1)):
                    try:
                        obj.keyframe_delete(data_path='hide_render', frame=frame)
                    except:
                        continue
                
class ExportHelper():
    def export_gltf(num):
        models_path = bpy.path.abspath('//models/' + format(num, '03'))
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
            
    def export_json(num, traits):
        num_s = format(num, '03')
        
        f = open(bpy.path.abspath('//traits/' + num_s + '.json'), "w")
        props = {
            'name': '#' + num_s,
            'image': num_s + '.jpg',
            'model': num_s + '.glb',
            'attributes': list(
                map(
                    (lambda trait: {trait.group_name: trait.name}), 
                    filter(
                        (lambda trait: not trait.name.lower().startswith("no ")), 
                        traits
                    )
                )
            )
        }
        f.write(json.dumps(props))
        f.close()

class Trait:
    def __init__(self, name, object, group_name):
        self.name = name
        self.object = object
        self.group_name = group_name

class TraitsHelper:
    def find_by_model_ex(scene, name):
        traits = scene.collection.children['Models'].children[name].children['Traits']
        
        objects = []
        for coll in traits.children:
            for obj in coll.objects:
                objects.append({"object": obj, "collection": coll})
        return objects

    def find_by_model(scene, name):
        return list(
            map(
                (lambda item: item['object']), 
                TraitsHelper.find_by_model_ex(scene, name)
            )
        )

    def generate(qtd, traits_props, objects):
        groups = {}
        for prop in traits_props:
            group = groups.get(prop.group)
            if group == None:
                groups[prop.group] = {"weights": [prop.probability], "props": [prop]}
            else:
                group["weights"].append(prop.probability)
                group["props"].append(prop)

        traits = []
        for num in range(qtd):
            obj_traits = []
            for group_name, group in groups.items():
                trait = random.choices(population=group['props'], weights=group['weights'])[0]
                object = objects.get(trait.name)
                obj_traits.append(Trait(trait.name, object, group_name))
                
            traits.append(obj_traits)
                
        return traits
        

class LookupOp(bpy.types.Operator):
    bl_idname = "wm.lookup"
    bl_label = "Lookup"

    def execute(self, context):
        scene = context.scene
        traits_props = scene.na_traits_props

        traits_props.clear()

        traits = TraitsHelper.find_by_model_ex(scene, "Robot")
        
        groups = {}
        for trait in traits:
            name = trait['collection'].name
            group = groups.get(name)
            if group == None:
                groups[name] = 1.0
            else:            
                groups[name] += 1.0
                
        for trait in traits:
            item = traits_props.add()
            item.name = trait['object'].name
            item.group = trait['collection'].name
            item.probability = 100.0 / groups[item.group]
    
        return {'FINISHED'}

class GenerateOp(bpy.types.Operator):
    bl_idname = "wm.generate"
    bl_label = "Generate"

    def execute(self, context):
        global nfts_traits
        scene = context.scene
        settings = scene.na_settings
        traits_props = scene.na_traits_props
        
        num_frames = settings.qtd
        
        nfts_traits = TraitsHelper.generate(num_frames, traits_props, scene.objects)
        
        return {'FINISHED'}

class ExportOp(bpy.types.Operator):
    bl_idname = "wm.export"
    bl_label = "Export"

    def execute(self, context):
        global nfts_traits
        scene = context.scene
        settings = scene.na_settings
        traits_props = scene.na_traits_props
        
        bpy.ops.object.select_all(action='DESELECT')
        
        all_traits = TraitsHelper.find_by_model(scene, "Robot")

        ObjectHelper.hide_objects(all_traits)
        ActionsHelper.delete_actions(all_traits)
        KeyframeHelper.delete_all_hide_render(scene, all_traits)
        
        num_frames = settings.qtd

        scene.frame_start = 1
        scene.frame_end = num_frames

        KeyframeHelper.insert_all_hide_render(all_traits, True, 0)
        
        scene.frame_set(1)
        
        num = 1
        for traits in nfts_traits:
            for trait in traits:
                print(trait.name)
                KeyframeHelper.insert_hide_render(trait.object, False, num)
            
            if settings.export_traits:
                ExportHelper.export_json(num, traits)

            if settings.export_models:
                ExportHelper.export_gltf(num)

            for trait in traits:
                KeyframeHelper.insert_hide_render(trait.object, True, num+1)
                
            num += 1

        ObjectHelper.hide_objects(all_traits)

        return {'FINISHED'}
    
class CleanupOp(bpy.types.Operator):
    bl_idname = "wm.clean_up"
    bl_label = "Clean up"

    def execute(self, context):
        scene = context.scene
        settings = scene.na_settings
        
        bpy.ops.object.select_all(action='DESELECT')
        
        traits = TraitsHelper.find_by_model(scene, "Robot")

        ObjectHelper.hide_objects(traits)
        ActionsHelper.delete_actions(traits)
        KeyframeHelper.delete_all_hide_render(scene, traits)
        
        return {'FINISHED'}

class TraitProps(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name", default="")
    probability: bpy.props.FloatProperty(name="Probability", default=0.0)
    group: bpy.props.StringProperty(name="Group", default="")

class SettingsProps(bpy.types.PropertyGroup):
    qtd: bpy.props.IntProperty(name="", default=0)
    export_models: bpy.props.BoolProperty(name="", default=True)
    export_traits: bpy.props.BoolProperty(name="", default=True)

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
        traits_props = scene.na_traits_props
        layout.label(text="Traits:")
        last_group = ''
        for i in range(len(traits_props)):
            trait = traits_props[i]
            
            if trait.group != last_group:
                last_group = trait.group
                row = layout.row()
                row.label(text=trait.group, icon='GROUP')
                
            row = layout.row()
            row.label(text=trait.name)
            row.prop(traits_props[i], 'probability')

        row = layout.row()
        row.separator()

        # settings
        settings = scene.na_settings
        layout.label(text="Settings:")
        
        row = layout.row()
        row.label(text="Quantity")
        row.prop(settings, 'qtd')

        row = layout.row()
        row.label(text="Export models")
        row.prop(settings, 'export_models')

        row = layout.row()
        row.label(text="Export traits")
        row.prop(settings, 'export_traits')
        
        row = layout.row()
        row.separator()

        # actions
        layout.label(text="Actions:")

        split = layout.split()
        col = split.column()
        col.operator("wm.lookup")

        col = split.column(align=True)
        col.operator("wm.generate")

        split = layout.split()
        col = split.column()
        col.operator("wm.export")

        col = split.column(align=True)
        col.operator("wm.clean_up")

classes = [TraitProps, SettingsProps, LookupOp, GenerateOp, ExportOp, CleanupOp, MainPanel]

def register():
    for klass in classes:
        bpy.utils.register_class(klass)
    
    bpy.types.Scene.na_traits_props = bpy.props.CollectionProperty(type=TraitProps)
    bpy.types.Scene.na_settings = bpy.props.PointerProperty(type=SettingsProps)

def unregister():
    for klass in classes:
        bpy.utils.unregister_class(klass)
    
if __name__ == "__main__":
    register()
