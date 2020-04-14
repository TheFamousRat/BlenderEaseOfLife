import bpy
import os

###### OPTIONS ######

outputFolder = 'meshes'#Relative path from .blend file
extraCollections = []#[bpy.data.collections['Stickers']]

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

basedir = bpy.path.abspath('//')
absOutputFolder = os.path.join(basedir, outputFolder)
outpoutedMeshes = []

if not os.path.exists(absOutputFolder):
    os.makedirs(absOutputFolder)

selectedObj = bpy.context.selected_objects.copy()

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
        if not os.path.exists(os.path.join(absOutputFolder,format)):
            os.makedirs(os.path.join(absOutputFolder,format))
        
        bpy.ops.export_scene.gltf(
            filepath=os.path.join(absOutputFolder, format, toAlphaNum(obj.data.name) + '.' + format),
            export_format='GLTF_EMBEDDED',
            export_copyright="TheFamousRat",
            export_selected=True,
            export_apply=True,
            export_materials=True
        )
        
        format = 'obj'
        if not os.path.exists(os.path.join(absOutputFolder,format)):
            os.makedirs(os.path.join(absOutputFolder,format))
        
        bpy.ops.export_scene.obj(
            filepath=os.path.join(absOutputFolder, format, toAlphaNum(obj.data.name) + '.' + format),
            use_selection=True
        )
        
        format = 'stl'
        if not os.path.exists(os.path.join(absOutputFolder,format)):
            os.makedirs(os.path.join(absOutputFolder,format))
        
        bpy.ops.export_mesh.stl(
            filepath=os.path.join(absOutputFolder, format, toAlphaNum(obj.data.name) + '.' + format),
            use_selection=True
        )
        
        obj.location = prevLoc
        
bpy.ops.object.select_all(action='DESELECT')
for obj in selectedObj:
    obj.select_set(True)