import bpy
import os

###### PARAMETERS ######

outputFolder = 'meshes'#Relative path from .blend file
marginParam = 8.0
defaultBakedImageDim = 512
meshesDim = {
"Scarf" : 512,
"Eyes" : 128,
"Nose" : 256,
"Teeth" : 256,
"Theodore" : 1024
}
passFilters = {'COLOR'}#{'COLOR'}
bakingTypes = ["Diffuse", "Roughness"]#, "Normal"]

###### CODE ######

##### CONST
mapTypeToInput = {
"Normal" : "Normal", 
"Roughness" : "Roughness",
"Diffuse" : "Base Color"}

def toAlphaNum(str):
    return ''.join([c if (c.isalnum() or c=='_') else '' for c in str])

basedir = bpy.path.abspath('//')
bakedMapsFolder = os.path.join(basedir, outputFolder)
outpoutedMeshes = []

if not os.path.exists(bakedMapsFolder):
    os.makedirs(bakedMapsFolder)
    
#We check that the image we're going to use, named "Baking", already exist.
#Otherwise we just create it
if not "Baking" in bpy.data.images:
    bpy.data.images.new("Baking", defaultBakedImageDim, defaultBakedImageDim)
    
bakingImg = bpy.data.images["Baking"]
bakingImg.scale(defaultBakedImageDim, defaultBakedImageDim)

worldNodeTree = bpy.context.scene.world.node_tree
worldOutputNode = worldNodeTree.nodes["World Output"]
previousOutput = None
if len(worldNodeTree.nodes["World Output"].inputs['Surface'].links):
    previousOutput = worldNodeTree.nodes["World Output"].inputs['Surface'].links[0].from_node

if previousOutput:
    worldNodeTree.links.remove(worldOutputNode.inputs['Surface'].links[0])

bakeBg = worldNodeTree.nodes.new("ShaderNodeBackground")
bakeBg.name = "BakingBackground"
bakeBg.inputs[1].default_value = 5.0
worldNodeTree.links.new(worldOutputNode.inputs['Surface'], bakeBg.outputs[0])

# Get the path where the blend file is located
originalSelectedMeshes = bpy.context.selected_objects

# Previous hide_render states 
prevHideRender = {}
for obj in bpy.data.objects:
    prevHideRender[obj] = obj.hide_render
    obj.hide_render = True

# We set the engine to Cycles, and remeber the previous one
prevEngine = bpy.context.scene.render.engine
bpy.context.scene.render.engine = 'CYCLES'

# We keep the states of previous objects
for selectedItem in originalSelectedMeshes:
    if selectedItem.type == "MESH":
        print("Baking " + selectedItem.name)
        #We make sure the current mesh is the only selected item
        bpy.ops.object.select_all(action='DESELECT') 
        selectedItem.select_set(True)
        selectedItem.hide_render = False
        
        if not selectedItem.name in meshesDim:
            bakingImg.scale(defaultBakedImageDim,defaultBakedImageDim)
        else:
            bakingImg.scale(meshesDim[selectedItem.name],meshesDim[selectedItem.name])
        
        for mat in selectedItem.data.materials:
            #We first look for an "Image Texture" node in which we can put the baked result
            if not "Baking" in mat.node_tree.nodes.keys():
                mat.node_tree.nodes.new("ShaderNodeTexImage").name = "Baking"
                
            bakingNode = mat.node_tree.nodes["Baking"]
            mat.node_tree.nodes.active = bakingNode
            bakingNode.image = bakingImg
        
        #We create the baked material using the textures
        bakedMatName = selectedItem.name + "_baked"

        if bakedMatName in bpy.data.materials.keys():
            bpy.data.materials.remove(bpy.data.materials[bakedMatName])
            
        bakedMat = bpy.data.materials.new(bakedMatName)
        bakedMat.use_nodes = True
        principledNode = bakedMat.node_tree.nodes["Principled BSDF"]
        
        for currentType in bakingTypes:
            print(" Baking type : " + currentType)
            #We bake the image
            bpy.ops.object.bake(type=currentType.upper(), margin=marginParam, pass_filter=set(passFilters),use_selected_to_active=False)
            
            #Save it
            texPath = os.path.join(bakedMapsFolder, selectedItem.name + currentType + ".png")
            bakingImg.save_render(texPath)
            print(" Baked image saved")
            
            #And finally add it to the shader
            #Create the node
            texNode = bakedMat.node_tree.nodes.new("ShaderNodeTexImage")
            #Set the params (name, image, location...)
            texNode.name = currentType
            texNode.label = currentType + "Tex"
            currentInputId = principledNode.inputs.find(mapTypeToInput[currentType])
            texNode.location.x = principledNode.location.x - 100 - principledNode.width
            texNode.location.y = principledNode.location.y - (principledNode.height+texNode.height) + ((len(principledNode.inputs)*0.5)-currentInputId)*texNode.height*0.5
            texNode.image = bpy.data.images.load(texPath, check_existing=True)
            #Link it
            bakedMat.node_tree.links.new(principledNode.inputs[currentInputId], texNode.outputs["Color"])
            
        selectedItem.hide_render = True

    
#We then restore the items that were selected
for selectedItem in originalSelectedMeshes:
    selectedItem.select_set(True)
    
bpy.context.scene.render.engine = prevEngine
bpy.data.images.remove(bpy.data.images["Baking"])

worldNodeTree.links.remove(worldOutputNode.inputs['Surface'].links[0])
worldNodeTree.nodes.remove(bakeBg)
if previousOutput:
    worldNodeTree.links.new(worldOutputNode.inputs['Surface'], previousOutput.outputs[0])

for obj in bpy.data.objects:
    obj.hide_render = prevHideRender[obj]