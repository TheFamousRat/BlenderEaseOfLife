import bpy
import os
import shutil

###### OPTIONS ######

outputFolder = 'meshes'#Relative path from .blend file
extraCollections = []#[bpy.data.collections['Stickers']]
useSelection = True
applyModifiers = True
compressFolders = True
desiredFormats = ['dae','gltf','obj','fbx','stl']

###### CODE ######

def toAlphaNum(str):
    return ''.join([c if (c.isalnum() or c=='_') else '' for c in str])

def objValidToExport(obj, extraCollections):
    c1 = (obj.type == 'MESH')
    c2 = ([coll for coll in obj.users_collection if coll in extraCollections] == [])
    c4 = True
    if obj.parent != None:
        c4 = (not objValidToExport(obj.parent, extraCollections))
        
    return (c1 and c2 and c4)

def makeFormatDir(format, absOutputFolder, obj):
    #Kind of a gimicky method. Creates the folder for the format if it doesn't exist
    #Also returns the path of the to-be-exported object
    if not os.path.exists(os.path.join(absOutputFolder,format)):
                os.makedirs(os.path.join(absOutputFolder,format))
    return os.path.join(absOutputFolder, format, toAlphaNum(obj.data.name) + '.' + format)

basedir = bpy.path.abspath('//')
absOutputFolder = os.path.join(basedir, outputFolder)
outpoutedMeshes = []

if not os.path.exists(absOutputFolder):
    os.makedirs(absOutputFolder)

selectedObj = bpy.context.selected_objects.copy()

try:
    for obj in selectedObj:
        if objValidToExport(obj, extraCollections) and (not obj.data in outpoutedMeshes):
            outpoutedMeshes.append(obj.data)
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            for child in obj.children:
                child.select_set(True)
            if obj.parent != None:
                if obj.parent.type == 'ARMATURE':
                    obj.parent.select_set(True)
            
            prevLoc = obj.location.copy()
            obj.location *= 0
            
            format = 'gltf'
            if format in desiredFormats:
                exportPath = makeFormatDir('gltf', absOutputFolder, obj)
                
                bpy.ops.export_scene.gltf(
                    filepath=exportPath,
                    export_format='GLTF_EMBEDDED',
                    export_copyright="TheFamousRat",
                    export_selected=useSelection,
                    export_apply=applyModifiers,
                    export_colors=False,
                    export_materials=True
                )
                
            format = 'obj'
            if format in desiredFormats:
                exportPath = makeFormatDir('obj', absOutputFolder, obj)
                
                bpy.ops.export_scene.obj(
                    filepath=exportPath,
                    use_selection=useSelection,
                    use_mesh_modifiers=applyModifiers
                )
            
            format = 'stl'
            if format in desiredFormats:
                exportPath = makeFormatDir('stl', absOutputFolder, obj)
                
                bpy.ops.export_mesh.stl(
                    filepath=exportPath,
                    use_selection=useSelection,
                    use_mesh_modifiers=applyModifiers
                )
                
            format = 'fbx'
            if format in desiredFormats:
                exportPath = makeFormatDir('fbx', absOutputFolder, obj)
                
                bpy.ops.export_scene.fbx(
                    filepath=exportPath,
                    use_selection=useSelection,
                    use_mesh_modifiers=applyModifiers
                )
                
            format = 'dae'
            if format in desiredFormats:
                exportPath = makeFormatDir('dae', absOutputFolder, obj)
                
                bpy.ops.wm.collada_export(
                    filepath=exportPath,
                    selected=useSelection,
                    apply_modifiers=applyModifiers
                )
            
            obj.location = prevLoc

    if compressFolders:
        blendFileName = os.path.splitext(bpy.path.basename(bpy.data.filepath))[0]
        
        for format in desiredFormats:
            exportPath = os.path.join(absOutputFolder,format)
            print(exportPath)
            shutil.make_archive(os.path.join(absOutputFolder, blendFileName + '_' + format.upper()), 'zip', exportPath)
            
except Exception as e:
    print(e) 

bpy.ops.object.select_all(action='DESELECT')
for obj in selectedObj:
    obj.select_set(True)