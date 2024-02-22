import bpy
import random
import re
import json

## https://docs.blender.org/api/4.0

nfts_traits = []

class ObjectHelper():
    def hide_objects(objects):
        for obj in objects:
            obj.hide_render = True
            obj.hide_set(True)
            
    def clear_name(name):
        return re.sub('\.[0-9]+', '', name)

class ActionHelper:
    def delete_actions(objects):
        for action in bpy.data.actions:
            for obj in objects:
                if action.name.startswith(obj.name):
                    bpy.data.actions.remove(action)
                    break

class ModelHelper():
    models = []
    def find_all(scene):
        for model in scene.collection.children['Models'].children:
            models.append(model)
            
        return models

class Trait:
    def __init__(self, name, object, group_name, model_name):
        self.name = name
        self.object = object
        self.group_name = group_name
        self.model_name = model_name

class TraitHelper:
    def find_all_ex(scene):
        models = {}

        for model in scene.collection.children['Models'].children:
            traits = []

            traits_col = None
            for col in model.children:
                if col.name.lower().startswith('traits'):
                    traits_col = col
                    break
            
            if traits_col != None:
                for col in traits_col.children:
                    for obj in col.objects:
                        traits.append({
                            "object": obj, 
                            "collection": col
                        })
                        
            models[model.name] = {
                "model": model,
                "traits": traits
            }
                        
        return models

    def find_all(scene):
        models = TraitHelper.find_all_ex(scene).items()
        
        traits = sum(list(map(
            lambda model: model[1]['traits'],
            models    
        )), [])
        
        return list(
            map(
                (lambda item: item['object']), 
                traits    
            )
        )

    def generate(qtd, models_props, traits_props, objects):
        models_weights = []
        models_groups = []
        
        for model_prop in models_props:
            groups = {}
            for prop in filter(
                    (lambda item: item.model_name == model_prop.name), 
                    traits_props
                ):
                group = groups.get(prop.group_name)
                if group == None:
                    groups[prop.group_name] = {
                        "weights": [prop.probability], 
                        "props": [prop], 
                        "model_name": model_prop.name
                    }
                else:
                    group["weights"].append(prop.probability)
                    group["props"].append(prop)
                    
            models_weights.append(model_prop.probability) 
            models_groups.append(groups)

        traits = []
        for num in range(qtd):
            obj_traits = []
            groups = random.choices(
                population=models_groups, 
                weights=models_weights
            )[0]
            
            for name, group in groups.items():
                trait = random.choices(
                    population=group['props'], 
                    weights=group['weights']
                )[0]
                object = objects.get(trait.name)
                obj_traits.append(Trait(
                    trait.name, 
                    object, 
                    name,
                    group['model_name']
                ))
                
            traits.append(obj_traits)
                
        return traits
                
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
            'model_name': traits[0].model_name,
            'image': num_s + '.jpg',
            'model': num_s + '.glb',
            'attributes': list(
                map(
                    (lambda trait: {ObjectHelper.clear_name(trait.group_name): ObjectHelper.clear_name(trait.name)}), 
                    filter(
                        (lambda trait: not trait.name.lower().startswith("no ")), 
                        traits
                    )
                )
            )
        }
        f.write(json.dumps(props))
        f.close()

class LookupOp(bpy.types.Operator):
    bl_idname = "wm.lookup"
    bl_label = "Lookup"

    def execute(self, context):
        scene = context.scene
        models_props = scene.na_models
        traits_props = scene.na_traits

        models_props.clear()
        traits_props.clear()

        models = TraitHelper.find_all_ex(scene)
        
        for name, model in models.items():
            item = models_props.add()
            item.name = name
            item.probability = 100.0 / len(models)
            
            traits = model['traits']
        
            groups = {}
            for trait in traits:
                group_name = name + '_' + trait['collection'].name
                group = groups.get(group_name)
                if group == None:
                    groups[group_name] = 1.0
                else:            
                    groups[group_name] += 1.0

            for trait in traits:
                item = traits_props.add()
                item.name = trait['object'].name
                item.group_name = trait['collection'].name
                item.model_name = name
                item.probability = 100.0 / groups[name + '_' + item.group_name]
        
        return {'FINISHED'}

class GenerateOp(bpy.types.Operator):
    bl_idname = "wm.generate"
    bl_label = "Generate"

    def execute(self, context):
        global nfts_traits
        scene = context.scene
        settings = scene.na_settings
        models_props = scene.na_models
        traits_props = scene.na_traits
        
        num_frames = settings.qtd
        
        nfts_traits = TraitHelper.generate(
            num_frames, models_props, traits_props, scene.objects)
        
        return {'FINISHED'}

class ExportOp(bpy.types.Operator):
    bl_idname = "wm.export"
    bl_label = "Export"

    def execute(self, context):
        global nfts_traits
        scene = context.scene
        settings = scene.na_settings
        traits_props = scene.na_traits
        
        bpy.ops.object.select_all(action='DESELECT')
        
        all_traits = TraitHelper.find_all(scene)

        ObjectHelper.hide_objects(all_traits)
        ActionHelper.delete_actions(all_traits)
        KeyframeHelper.delete_all_hide_render(scene, all_traits)
        
        num_frames = settings.qtd

        scene.frame_start = 1
        scene.frame_end = num_frames

        KeyframeHelper.insert_all_hide_render(all_traits, True, 0)
        
        scene.frame_set(1)
        
        num = 1
        for traits in nfts_traits:
            for trait in traits:
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
        
        traits = TraitHelper.find_all(scene)

        ObjectHelper.hide_objects(traits)
        ActionHelper.delete_actions(traits)
        KeyframeHelper.delete_all_hide_render(scene, traits)
        
        return {'FINISHED'}

class SettingsProps(bpy.types.PropertyGroup):
    qtd: bpy.props.IntProperty(name="", default=0)
    export_models: bpy.props.BoolProperty(name="", default=True)
    export_traits: bpy.props.BoolProperty(name="", default=True)

class ModelProps(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name", default="")
    probability: bpy.props.FloatProperty(name="Probability", default=0.0)

class TraitProps(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name", default="")
    probability: bpy.props.FloatProperty(name="Probability", default=0.0)
    group_name: bpy.props.StringProperty(name="Group", default="")
    model_name: bpy.props.StringProperty(name="Model", default="")

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
        models_props = scene.na_models
        traits_props = scene.na_traits

        # rarities
        layout.label(text="Models:")
        last_model = ''
        last_group = ''
        box = None
        for trait in traits_props:
            if trait.model_name != last_model:
                last_model = trait.model_name
                row = layout.split()
                col = row.column()
                col.label(text=trait.model_name, icon='OBJECT_DATA')
                col = row.column()
                model = next((item for item in models_props if item.name == trait.model_name), None)
                col.prop(model, 'probability')
                box = layout.box()
                last_group = ''
                
            if trait.group_name != last_group:
                last_group = trait.group_name
                row = box.row()
                row.label(text=ObjectHelper.clear_name(trait.group_name), icon='GROUP')
            
            if box != None:
                row = box.row()
                row.label(text=ObjectHelper.clear_name(trait.name))
                row.prop(trait, 'probability')

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

classes = [SettingsProps, ModelProps, TraitProps, LookupOp, GenerateOp, ExportOp, CleanupOp, MainPanel]

def register():
    for klass in classes:
        bpy.utils.register_class(klass)
    
    bpy.types.Scene.na_settings = bpy.props.PointerProperty(type=SettingsProps)
    bpy.types.Scene.na_models = bpy.props.CollectionProperty(type=ModelProps)
    bpy.types.Scene.na_traits = bpy.props.CollectionProperty(type=TraitProps)

def unregister():
    for klass in classes:
        bpy.utils.unregister_class(klass)
    
if __name__ == "__main__":
    register()
