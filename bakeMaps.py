import bpy
import os

###### PARAMETERS ######

outputFolder = 'textures'#Relative path from .blend file
marginParam = 8.0
defaultBakedImageDim = (1024,1024)
meshesDim = {
"Scarf" : (128,128),
"Eyes" : (128,128),
"Nose" : (256,256),
"Teeth" : (256,256),
"Theodore" : (2048,2048)
}
passFilters = {'COLOR'}#{'COLOR'}
bakingTypes = ["Roughness", "Normal","Emit"]
useAlpha = True
###### CODE ######

###### CONST ######
mapTypeToInput = {
"Normal" : "Normal", 
"Roughness" : "Roughness",
"Diffuse" : "Base Color",
"Combined" : "Base Color",
"Emit" : "Emission"}

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
    bpy.data.images.new("Baking", defaultBakedImageDim[0], defaultBakedImageDim[1], alpha=useAlpha)
    
bakingImg = bpy.data.images["Baking"]
bakingImg.scale(defaultBakedImageDim[0], defaultBakedImageDim[1])

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

gotError = False
# We keep the states of previous objects
for selectedItem in originalSelectedMeshes:
    try:
        if selectedItem.type == "MESH":
            print("Baking " + selectedItem.name)
            #We make sure the current mesh is the only selected item
            bpy.ops.object.select_all(action='DESELECT') 
            selectedItem.select_set(True)
            selectedItem.hide_render = False
            
            if not selectedItem.name in meshesDim:
                bakingImg.scale(defaultBakedImageDim[0],defaultBakedImageDim[1])
            else:
                bakingImg.scale(meshesDim[selectedItem.name][0],meshesDim[selectedItem.name][1])
            
            for mat in selectedItem.data.materials:
                if mat:
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
                texNode.location.x = principledNode.location.x - principledNode.width * 2.0
                texNode.location.y = principledNode.location.y - (principledNode.height+texNode.height) + ((len(principledNode.inputs)*0.5)-currentInputId)*texNode.height*0.5
                texNode.image = bpy.data.images.load(texPath, check_existing=True)
                
                if currentType.upper() == 'EMIT' or currentType.upper() == 'DIFFUSE':
                    texNode.image.colorspace_settings.name = 'sRGB'
                else:
                    texNode.image.colorspace_settings.name = 'Non-Color'
                
                #Link it
                if currentType == 'Normal':
                    normalMapNode = bakedMat.node_tree.nodes.new("ShaderNodeNormalMap")
                    normalMapNode.location = texNode.location
                    #normalMapNode.space = 'OBJECT'
                    texNode.location.x -= normalMapNode.width * 2.0
                    bakedMat.node_tree.links.new(normalMapNode.inputs["Color"], texNode.outputs["Color"])
                    bakedMat.node_tree.links.new(principledNode.inputs["Normal"], normalMapNode.outputs["Normal"])
                else:
                    bakedMat.node_tree.links.new(principledNode.inputs[currentInputId], texNode.outputs["Color"])
                
            selectedItem.hide_render = True
    except Exception as e:
        print(e)
        gotError = True
        break
    
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
    
if gotError:
    raise Exception("Got an error")