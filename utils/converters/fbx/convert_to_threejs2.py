# @author zfedoran / http://github.com/zfedoran

import os
import sys
import math
import operator
import re
import json
import types

# #####################################################
# Globals
# #####################################################
option_triangulate = True
option_textures = True
option_prefix = True
option_geometry = False
option_default_camera = False
option_default_light = False
option_animation = False
option_parse_mtl = False
option_pretty_print = True

converter = None
mtl_library = None
mtl_texture_count = 0

# #####################################################
# Custom JSON format encoders
# #####################################################
class NoIndent(object):
    def __init__(self, value):
        self.value = value

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, NoIndent):
            return '[ %s ]' % ', '.join(str(f) for f in obj.value)
        else:
            return json.JSONEncoder.default(self, obj)

# #####################################################
# Templates
# #####################################################
def getVector2(v, round_vector = False):
    # FbxVector2 is not JSON serializable
    # JSON does not support NaN or Inf
    if math.isnan(v[0]) or math.isinf(v[0]):
        v[0] = 0
    if math.isnan(v[1]) or math.isinf(v[1]):
        v[1] = 0
    if round_vector or option_pretty_print:
        v = (round(v[0], 5), round(v[1], 5))
    if option_pretty_print:
        return NoIndent([v[0], v[1]])
    else:
        return [v[0], v[1]]

def getVector3(v, round_vector = False):
    # FbxVector3 is not JSON serializable
    # JSON does not support NaN or Inf
    if math.isnan(v[0]) or math.isinf(v[0]):
        v[0] = 0
    if math.isnan(v[1]) or math.isinf(v[1]):
        v[1] = 0
    if math.isnan(v[2]) or math.isinf(v[2]):
        v[2] = 0
    if round_vector or option_pretty_print:
        v = (round(v[0], 5), round(v[1], 5), round(v[2], 5))
    if option_pretty_print:
        return NoIndent([v[0], v[1], v[2]])
    else:
        return [v[0], v[1], v[2]]

def getVector4(v, round_vector = False):
    # FbxVector4 is not JSON serializable
    # JSON does not support NaN or Inf
    if math.isnan(v[0]) or math.isinf(v[0]):
        v[0] = 0
    if math.isnan(v[1]) or math.isinf(v[1]):
        v[1] = 0
    if math.isnan(v[2]) or math.isinf(v[2]):
        v[2] = 0
    if math.isnan(v[3]) or math.isinf(v[3]):
        v[3] = 0
    if round_vector or option_pretty_print:
        v = (round(v[0], 5), round(v[1], 5), round(v[2], 5), round(v[3], 5))
    if option_pretty_print:
        return NoIndent([v[0], v[1], v[2], v[3]])
    else:
        return [v[0], v[1], v[2], v[3]]

def getVector2String(v, no_brackets = False, round_vector = False):
    # JSON does not support NaN or Inf
    if math.isnan(v[0]) or math.isinf(v[0]):
        v[0] = 0
    if math.isnan(v[1]) or math.isinf(v[1]):
        v[1] = 0
    if round_vector:
        v = (round(v[0], 5), round(v[1], 5))
    if no_brackets:
        return '%g,%g' % (v[0], v[1])
    else:
        return '[ %g, %g ]' % (v[0], v[1])

def getVector3String(v, no_brackets = False, round_vector = False):
    # JSON does not support NaN or Inf
    if math.isnan(v[0]) or math.isinf(v[0]):
        v[0] = 0
    if math.isnan(v[1]) or math.isinf(v[1]):
        v[1] = 0
    if math.isnan(v[2]) or math.isinf(v[2]):
        v[2] = 0
    if round_vector:
        v = (round(v[0], 5), round(v[1], 5), round(v[2], 5))
    if no_brackets:
        return '%g,%g,%g' % (v[0], v[1], v[2])
    else:
        return '[ %g, %g, %g ]' % (v[0], v[1], v[2])

def getVector4String(v, no_brackets = False, round_vector = False):
    # JSON does not support NaN or Inf
    if math.isnan(v[0]) or math.isinf(v[0]):
        v[0] = 0
    if math.isnan(v[1]) or math.isinf(v[1]):
        v[1] = 0
    if math.isnan(v[2]) or math.isinf(v[2]):
        v[2] = 0
    if math.isnan(v[3]) or math.isinf(v[3]):
        v[3] = 0
    if round_vector:
        v = (round(v[0], 5), round(v[1], 5), round(v[2], 5), round(v[3], 5))
    if no_brackets:
        return '%g,%g,%g,%g' % (v[0], v[1], v[2], v[3])
    else:
        return '[ %g, %g, %g, %g ]' % (v[0], v[1], v[2], v[3])

def getLabelString(s):
    s = s.replace('\\','\\\\')
    s = s.replace('"','\\"')
    return '"%s"' % s 

def getArrayString(s):
    return '[ %s ]' % s

def getPaddingString(n):
    output = ""
    for i in range(n):
        output += "\t"
    return output
        
def getBoolString(value):
    if value:
        return "true"
    return "false"

# #####################################################
# Helpers
# #####################################################
def hasUniqueName(o, class_id):
    scene = o.GetScene()
    object_name = o.GetName() 
    object_id = o.GetUniqueID()

    object_count = scene.GetSrcObjectCount(class_id)

    for i in range(object_count):
        other = scene.GetSrcObject(class_id, i)
        other_id = other.GetUniqueID()
        other_name = other.GetName() 

        if other_id == object_id:
            continue
        if other_name == object_name:
            return False

    return True

def getObjectName(o, force_prefix = False): 
    if not o:
        return ""  

    object_name = o.GetName() 
    object_id = o.GetUniqueID()

    if not force_prefix:
        force_prefix = not hasUniqueName(o, FbxNode.ClassId)

    prefix = ""
    if option_prefix or force_prefix:
        prefix = "Object_%s_" % object_id

    return prefix + object_name

def getMaterialName(o, force_prefix = False):
    object_name = o.GetName() 
    object_id = o.GetUniqueID()

    if not force_prefix:
        force_prefix = not hasUniqueName(o, FbxSurfaceMaterial.ClassId)

    prefix = ""
    if option_prefix or force_prefix:
        prefix = "Material_%s_" % object_id

    return prefix + object_name

def getTextureName(t, force_prefix = False):
    if type(t) is FbxFileTexture:
        texture_file = t.GetFileName()
        texture_id = os.path.splitext(os.path.basename(texture_file))[0]
    else:
        texture_id = t.GetName()
        if texture_id == "_empty_":
            texture_id = ""
    prefix = ""
    if option_prefix or force_prefix:
        prefix = "Texture_%s_" % t.GetUniqueID()
        if len(texture_id) == 0:
            prefix = prefix[0:len(prefix)-1]
    return prefix + texture_id

def getMtlTextureName(texture_name, texture_id, force_prefix = False):
    texture_name = os.path.splitext(texture_name)[0]
    prefix = ""
    if option_prefix or force_prefix:
        prefix = "Texture_%s_" % texture_id
    return prefix + texture_name

# TODO: this could be more DRY
def getGeometryName(o, force_prefix = False):
    prefix = ""
    if option_prefix or force_prefix:
        prefix = "Geometry_%s_" % o.GetUniqueID()
    return prefix + o.GetName()

def getEmbedName(o, force_prefix = False):
    prefix = ""
    if option_prefix or force_prefix:
        prefix = "Embed_%s_" % o.GetUniqueID()
    return prefix + o.GetName()

def getAnimationName(o, force_prefix = False):
    prefix = ""
    if option_prefix or force_prefix:
        prefix = "Animation_%s_" % o.GetUniqueID()
    return prefix + o.GetName()
    
def getAnimationLayerName(o, force_prefix = False):
    prefix = ""
    if option_prefix or force_prefix:
        prefix = "Layer_%s" % o.GetUniqueID()
    return prefix 

def getAnimationCurveName(o, force_prefix = False):
    prefix = ""
    if option_prefix or force_prefix:
        prefix = "Curve_%s" % o.GetUniqueID()
    return prefix 

def getPoseName(o, force_prefix = False):
    prefix = ""
    if option_prefix or force_prefix:
        prefix = "Pose_%s_" % o.GetUniqueID()
    return prefix + o.GetName()

def getFogName(o, force_prefix = False):
    prefix = ""
    if option_prefix or force_prefix:
        prefix = "Fog_%s_" % o.GetUniqueID()
    return prefix + o.GetName()

def getObjectVisible(n):
    return True
    
def getRadians(v):
    return ((v[0]*math.pi)/180, (v[1]*math.pi)/180, (v[2]*math.pi)/180)

def getHex(c):
    color = (int(c[0]*255) << 16) + (int(c[1]*255) << 8) + int(c[2]*255)
    return color

def setBit(value, position, on):
    if on:
        mask = 1 << position
        return (value | mask)
    else:
        mask = ~(1 << position)
        return (value & mask)

def convert_fbx_color(color):
    return [color.mRed, color.mGreen, color.mBlue, color.mAlpha]
    
def convert_fbx_vec2(v):
    return [v[0], v[1]]

def convert_fbx_vec3(v):
    return [v[0], v[1], v[2]]
    
def generate_uvs(uv_layers):
    layers = []
    for uvs in uv_layers:
        layer = ",".join(getVector2String(n, True) for n in uvs)
        layers.append(layer)

    return ",".join("[%s]" % n for n in layers)

def generateMultiLineString(lines, separator, padding):
    cleanLines = []
    for i in range(len(lines)):
        line = lines[i]
        line = getPaddingString(padding) + line
        cleanLines.append(line)
    return separator.join(cleanLines)

def generate_bounding_box(vertices):
    minx = float('inf')
    miny = float('inf')
    minz = float('inf')
    maxx = -float('inf')
    maxy = -float('inf')
    maxz = -float('inf')

    for vertex in vertices:
        if vertex[0] < minx:
            minx = vertex[0]
        if vertex[1] < miny:
            miny = vertex[1]
        if vertex[2] < minz:
            minz = vertex[2]

        if vertex[0] > maxx:
            maxx = vertex[0]
        if vertex[1] > maxy:
            maxy = vertex[1]
        if vertex[2] > maxz:
            maxz = vertex[2]

    return [minx, miny, minz], [maxx, maxy, maxz]

    
# #####################################################
# Generate - Triangles 
# #####################################################
def triangulate_node_hierarchy(node):
    node_attribute = node.GetNodeAttribute();

    if node_attribute:
        if node_attribute.GetAttributeType() == FbxNodeAttribute.eMesh or \
           node_attribute.GetAttributeType() == FbxNodeAttribute.eNurbs or \
           node_attribute.GetAttributeType() == FbxNodeAttribute.eNurbsSurface or \
           node_attribute.GetAttributeType() == FbxNodeAttribute.ePatch:
            converter.TriangulateInPlace(node);
        
        child_count = node.GetChildCount()
        for i in range(child_count):
            triangulate_node_hierarchy(node.GetChild(i))

def triangulate_scene(scene):
    node = scene.GetRootNode()
    if node:
        for i in range(node.GetChildCount()):
            triangulate_node_hierarchy(node.GetChild(i))

# #####################################################
# Generate - Material String 
# #####################################################
def generate_texture_bindings(material_property, texture_list):
    binding_types = {
    "DiffuseColor": "map", "DiffuseFactor": "diffuseFactor", "EmissiveColor": "emissiveMap", 
    "EmissiveFactor": "emissiveFactor", "AmbientColor": "ambientMap", "AmbientFactor": "ambientFactor", 
    "SpecularColor": "specularMap", "SpecularFactor": "specularFactor", "ShininessExponent": "shininessExponent",
    "NormalMap": "normalMap", "Bump": "bumpMap", "TransparentColor": "transparentMap", 
    "TransparencyFactor": "transparentFactor", "ReflectionColor": "reflectionMap", 
    "ReflectionFactor": "reflectionFactor", "DisplacementColor": "displacementMap", 
    "VectorDisplacementColor": "vectorDisplacementMap"
    }

    if material_property.IsValid():
        #Here we have to check if it's layeredtextures, or just textures:
        layered_texture_count = material_property.GetSrcObjectCount(FbxLayeredTexture.ClassId)
        if layered_texture_count > 0:
            for j in range(layered_texture_count):
                layered_texture = material_property.GetSrcObject(FbxLayeredTexture.ClassId, j)
                texture_count = layered_texture.GetSrcObjectCount(FbxTexture.ClassId)
                for k in range(texture_count):
                    texture = layered_texture.GetSrcObject(FbxTexture.ClassId,k)
                    if texture:
                        texture_id = getLabelString( getTextureName(texture, True) )
                        texture_binding = '		"%s": %s,' % (binding_types[str(material_property.GetName())], texture_id)
                        texture_list.append(texture_binding)
        else:
            # no layered texture simply get on the property
            texture_count = material_property.GetSrcObjectCount(FbxTexture.ClassId)
            for j in range(texture_count):
                texture = material_property.GetSrcObject(FbxTexture.ClassId,j)
                if texture:
                    texture_id = getLabelString( getTextureName(texture, True) )
                    texture_binding = '		"%s": %s,' % (binding_types[str(material_property.GetName())], texture_id)
                    texture_list.append(texture_binding)

def generate_material_string(material):
    #Get the implementation to see if it's a hardware shader.
    implementation = GetImplementation(material, "ImplementationHLSL")
    implementation_type = "HLSL"
    if not implementation:
        implementation = GetImplementation(material, "ImplementationCGFX")
        implementation_type = "CGFX"

    output = []

    if implementation:
        print("Shader materials are not supported")
        
    elif material.GetClassId().Is(FbxSurfaceLambert.ClassId):

        ambient   = str(getHex(material.Ambient.Get()))
        diffuse   = str(getHex(material.Diffuse.Get()))
        emissive  = str(getHex(material.Emissive.Get()))
        opacity   = 1.0 - material.TransparencyFactor.Get()
        opacity   = 1.0 if opacity == 0 else opacity
        opacity   = str(opacity)
        transparent = getBoolString(False)
        reflectivity = "1"

        output = [

        '\t' + getLabelString( getMaterialName( material ) ) + ': {',
        '	"type"    : "MeshLambertMaterial",',
        '	"parameters"  : {',
        '		"color"  : ' 	  + diffuse + ',',
        '		"ambient"  : ' 	+ ambient + ',',
        '		"emissive"  : ' + emissive + ',',
        '		"reflectivity"  : ' + reflectivity + ',',
        '		"transparent" : '   + transparent + ',',
        '		"opacity" : ' 	    + opacity + ',',

        ]

    elif material.GetClassId().Is(FbxSurfacePhong.ClassId):

        ambient   = str(getHex(material.Ambient.Get()))
        diffuse   = str(getHex(material.Diffuse.Get()))
        emissive  = str(getHex(material.Emissive.Get()))
        specular  = str(getHex(material.Specular.Get()))
        opacity   = 1.0 - material.TransparencyFactor.Get()
        opacity   = 1.0 if opacity == 0 else opacity
        opacity   = str(opacity)
        shininess = str(material.Shininess.Get())
        transparent = getBoolString(False)
        reflectivity = "1"
        bumpScale = "1"

        output = [

        '\t' + getLabelString( getMaterialName( material ) ) + ': {',
        '	"type"    : "MeshPhongMaterial",',
        '	"parameters"  : {',
        '		"color"  : ' 	  + diffuse + ',',
        '		"ambient"  : ' 	+ ambient + ',',
        '		"emissive"  : ' + emissive + ',',
        '		"specular"  : ' + specular + ',',
        '		"shininess" : ' + shininess + ',',
        '		"bumpScale"  : '    + bumpScale + ',',
        '		"reflectivity"  : ' + reflectivity + ',',
        '		"transparent" : '   + transparent + ',',
        '		"opacity" : ' 	+ opacity + ',',

        ]

    else:
      print("Unknown type of Material")

    if not output:
        ambient   = str(getHex((0,0,0)))
        diffuse   = str(getHex((0.5,0.5,0.5)))
        emissive  = str(getHex((0,0,0)))
        opacity   = str(1)
        transparent = getBoolString(False)
        reflectivity = "1"

        output = [

        '\t' + getLabelString( getMaterialName( material ) ) + ': {',
        '	"type"    : "MeshLambertMaterial",',
        '	"parameters"  : {',
        '		"color"  : ' 	  + diffuse + ',',
        '		"ambient"  : ' 	+ ambient + ',',
        '		"emissive"  : ' + emissive + ',',
        '		"reflectivity"  : ' + reflectivity + ',',
        '		"transparent" : '   + transparent + ',',
        '		"opacity" : ' 	    + opacity + ',',

        ]

    if option_textures:
        if mtl_texture_count == 0:
          
            texture_list = []
            texture_count = FbxLayerElement.sTypeTextureCount()
            for texture_index in range(texture_count):
                material_property = material.FindProperty(FbxLayerElement.sTextureChannelNames(texture_index))
                generate_texture_bindings(material_property, texture_list)
            output += texture_list

        else:

            for mtl_material in mtl_library:
                if material.GetName() == mtl_material['name']:
                    if 'AmbientColor' in mtl_material:
                        texture_name = getMtlTextureName(mtl_material['AmbientColor'], mtl_material['AmbientColorId'], True)
                        texture_binding = '		"%s": %s,' % ('ambientMap', getLabelString(texture_name))
                        output.append(texture_binding)
                    if 'DiffuseColor' in mtl_material:
                        texture_name = getMtlTextureName(mtl_material['DiffuseColor'], mtl_material['DiffuseColorId'], True)
                        texture_binding = '		"%s": %s,' % ('map', getLabelString(texture_name))
                        output.append(texture_binding)
                    if 'SpecularColor' in mtl_material:
                        texture_name = getMtlTextureName(mtl_material['SpecularColor'], mtl_material['SpecularColorId'], True)
                        texture_binding = '		"%s": %s,' % ('specularMap', getLabelString(texture_name))
                        output.append(texture_binding)
                    if 'Bump' in mtl_material:
                        texture_name = getMtlTextureName(mtl_material['Bump'], mtl_material['BumpId'], True)
                        texture_binding = '		"%s": %s,' % ('bumpMap', getLabelString(texture_name))
                        output.append(texture_binding)
                    break


    wireframe = getBoolString(False)
    wireframeLinewidth = "1"

    output.append('		"wireframe" : ' + wireframe + ',')
    output.append('		"wireframeLinewidth" : ' + wireframeLinewidth)
    output.append('	}')
    output.append('}')

    return generateMultiLineString( output, '\n\t\t', 0 )

def generate_proxy_material_string(node, material_names):
    
    output = [

    '\t' + getLabelString( getMaterialName( node, True ) ) + ': {',
    '	"type"    : "MeshFaceMaterial",',
    '	"parameters"  : {',
    '		"materials"  : ' + getArrayString( ",".join(getLabelString(m) for m in material_names) ),
    '	}',
    '}'

    ]

    return generateMultiLineString( output, '\n\t\t', 0 )

# #####################################################
# Parse - Materials 
# #####################################################
def extract_materials_from_node(node, material_list):
    name = node.GetName()
    mesh = node.GetNodeAttribute()

    node = None
    if mesh:
        node = mesh.GetNode()
        if node:
            material_count = node.GetMaterialCount()
    
    material_names = []
    for l in range(mesh.GetLayerCount()):
        materials = mesh.GetLayer(l).GetMaterials()
        if materials:
            if materials.GetReferenceMode() == FbxLayerElement.eIndex:
                #Materials are in an undefined external table
                continue
            for i in range(material_count):
                material = node.GetMaterial(i)
                material_names.append(getMaterialName(material))

    if material_count > 1:
        proxy_material = generate_proxy_material_string(node, material_names)
        material_list.append(proxy_material)

def generate_materials_from_hierarchy(node, material_list):
    if node.GetNodeAttribute() == None:
        pass
    else:
        attribute_type = (node.GetNodeAttribute().GetAttributeType())
        if attribute_type == FbxNodeAttribute.eMesh:
            extract_materials_from_node(node, material_list)
    for i in range(node.GetChildCount()):
        generate_materials_from_hierarchy(node.GetChild(i), material_list)

def generate_material_list(scene):
    material_list = []

    material_count = scene.GetSrcObjectCount(FbxSurfaceMaterial.ClassId)
    for i in range(material_count):
        material = scene.GetSrcObject(FbxSurfaceMaterial.ClassId, i)
        material_string = generate_material_string(material)
        material_list.append(material_string)

    # generate material porxies
    node = scene.GetRootNode()
    if node:
        for i in range(node.GetChildCount()):
            generate_materials_from_hierarchy(node.GetChild(i), material_list)

    return material_list

# #####################################################
# Generate - Texture String 
# #####################################################
def generate_texture_object(texture):

    #TODO: extract more texture properties
    wrap_u = texture.GetWrapModeU()
    wrap_v = texture.GetWrapModeV()
    offset = texture.GetUVTranslation()

    if type(texture) is FbxFileTexture:
        url = texture.GetFileName()
    else:
        url = getTextureName( texture )

    output = {

      'url': url,
      'repeat': getVector2( (1,1) ),
      'offset': getVector2( texture.GetUVTranslation() ),
      'magFilter': 'LinearFilter',
      'minFilter': 'LinearMipMapLinearFilter',
      'anisotropy': True

    }

    return output

def generate_mtl_texture_object(texture):

    output = {

      'url': texture,
      'repeat': getVector2( (1,1) ),
      'offset': getVector2( (0,0) ),
      'magFilter': 'LinearFilter',
      'minFilter': 'LinearMipMapLinearFilter',
      'anisotropy': True

    }

    return output

# #####################################################
# Parse - Textures 
# #####################################################
def extract_material_textures(material_property, texture_dict):
    if material_property.IsValid():
        #Here we have to check if it's layeredtextures, or just textures:
        layered_texture_count = material_property.GetSrcObjectCount(FbxLayeredTexture.ClassId)
        if layered_texture_count > 0:
            for j in range(layered_texture_count):
                layered_texture = material_property.GetSrcObject(FbxLayeredTexture.ClassId, j)
                texture_count = layered_texture.GetSrcObjectCount(FbxTexture.ClassId)
                for k in range(texture_count):
                    texture = layered_texture.GetSrcObject(FbxTexture.ClassId,k)
                    if texture:
                        texture_object = generate_texture_object(texture)
                        texture_name = getTextureName( texture, True )
                        print texture_name
                        texture_dict[texture_name] = texture_object
        else:
            # no layered texture simply get on the property
            texture_count = material_property.GetSrcObjectCount(FbxTexture.ClassId)
            for j in range(texture_count):
                texture = material_property.GetSrcObject(FbxTexture.ClassId,j)
                if texture:
                    texture_object = generate_texture_object(texture)
                    texture_name = getTextureName( texture, True )
                    texture_dict[texture_name] = texture_object

def extract_textures_from_node(node, texture_dict):
    name = node.GetName()
    mesh = node.GetNodeAttribute()
    
    #for all materials attached to this mesh
    material_count = mesh.GetNode().GetSrcObjectCount(FbxSurfaceMaterial.ClassId)
    for material_index in range(material_count):
        material = mesh.GetNode().GetSrcObject(FbxSurfaceMaterial.ClassId, material_index)

        #go through all the possible textures types
        if material:            
            if mtl_texture_count == 0:

                texture_count = FbxLayerElement.sTypeTextureCount()
                for texture_index in range(texture_count):
                    material_property = material.FindProperty(FbxLayerElement.sTextureChannelNames(texture_index))
                    extract_material_textures(material_property, texture_dict)

            else:

                for mtl_material in mtl_library:
                    if material.GetName() == mtl_material['name']:
                        if 'AmbientColor' in mtl_material:
                            texture_name = mtl_material['AmbientColor'] 
                            texture_id = mtl_material['AmbientColorId'] 
                            texture_object = generate_mtl_texture_object(texture_name)
                            texture_name = getMtlTextureName( texture, textureId, True )
                            texture_dict[texture_name] = texture_object
                        if 'DiffuseColor' in mtl_material:
                            texture_name = mtl_material['DiffuseColor'] 
                            texture_id = mtl_material['DiffuseColorId'] 
                            texture_object = generate_mtl_texture_object(texture_name)
                            texture_name = getMtlTextureName( texture, textureId, True )
                            texture_dict[texture_name] = texture_object
                        if 'SpecularColor' in mtl_material:
                            texture_name = mtl_material['SpecularColor'] 
                            texture_id = mtl_material['SpecularColorId'] 
                            texture_object = generate_mtl_texture_object(texture_name)
                            texture_name = getMtlTextureName( texture, textureId, True )
                            texture_dict[texture_name] = texture_object
                        if 'Bump' in mtl_material:
                            texture_name = mtl_material['Bump'] 
                            texture_id = mtl_material['BumpId'] 
                            texture_object = generate_mtl_texture_object(texture_name)
                            texture_name = getMtlTextureName( texture, textureId, True )
                            texture_dict[texture_name] = texture_object
                        break

def generate_textures_from_hierarchy(node, texture_dict):
    if node.GetNodeAttribute() == None:
        pass
    else:
        attribute_type = (node.GetNodeAttribute().GetAttributeType())
        if attribute_type == FbxNodeAttribute.eMesh:
            extract_textures_from_node(node, texture_dict)
    for i in range(node.GetChildCount()):
        generate_textures_from_hierarchy(node.GetChild(i), texture_dict)

def generate_texture_dict(scene):
    if not option_textures:
        return {}

    texture_dict = {}
    node = scene.GetRootNode()
    if node:
        for i in range(node.GetChildCount()):
            generate_textures_from_hierarchy(node.GetChild(i), texture_dict)
    return texture_dict

# #####################################################
# Extract - Fbx Mesh data
# #####################################################
def extract_fbx_vertex_positions(mesh):
    control_points_count = mesh.GetControlPointsCount()
    control_points = mesh.GetControlPoints()

    positions = []
    for i in range(control_points_count):
        positions.append(convert_fbx_vec3(control_points[i]))

    node = mesh.GetNode()
    if node:
        t = node.GeometricTranslation.Get()
        t = FbxVector4(t[0], t[1], t[2], 1)
        r = node.GeometricRotation.Get()
        r = FbxVector4(r[0], r[1], r[2], 1)
        s = node.GeometricScaling.Get()
        s = FbxVector4(s[0], s[1], s[2], 1)
        
        hasGeometricTransform = False
        if t[0] != 0 or t[1] != 0 or t[2] != 0 or \
           r[0] != 0 or r[1] != 0 or r[2] != 0 or \
           s[0] != 1 or s[1] != 1 or s[2] != 1:
            hasGeometricTransform = True
        
        if hasGeometricTransform:
            geo_transform = FbxMatrix(t,r,s)
        else:
            geo_transform = FbxMatrix()

        transform = None

        if option_geometry:
            # FbxMeshes are local to their node, we need the vertices in global space
            # when scene nodes are not exported
            transform = node.EvaluateGlobalTransform()
            transform = FbxMatrix(transform) * geo_transform

        elif hasGeometricTransform:
            transform = geo_transform
            
        if transform:
            for i in range(len(positions)):
                v = positions[i]
                position = FbxVector4(v[0], v[1], v[2])
                position = transform.MultNormalize(position)
                positions[i] = convert_fbx_vec3(position)

    return positions

def extract_fbx_vertex_normals(mesh):
#   eNone             The mapping is undetermined.
#   eByControlPoint   There will be one mapping coordinate for each surface control point/vertex.
#   eByPolygonVertex  There will be one mapping coordinate for each vertex, for every polygon of which it is a part. This means that a vertex will have as many mapping coordinates as polygons of which it is a part.
#   eByPolygon        There can be only one mapping coordinate for the whole polygon.
#   eByEdge           There will be one mapping coordinate for each unique edge in the mesh. This is meant to be used with smoothing layer elements.
#   eAllSame          There can be only one mapping coordinate for the whole surface.

    layered_normal_indices = []
    layered_normal_values = []

    poly_count = mesh.GetPolygonCount()
    control_points = mesh.GetControlPoints() 

    for l in range(mesh.GetLayerCount()):
        mesh_normals = mesh.GetLayer(l).GetNormals()
        if not mesh_normals:
            continue
          
        normals_array = mesh_normals.GetDirectArray()
        normals_count = normals_array.GetCount()
  
        if normals_count == 0:
            continue

        normal_indices = []
        normal_values = []

        # values
        for i in range(normals_count):
            normal = convert_fbx_vec3(normals_array.GetAt(i))
            normal_values.append(normal)

        node = mesh.GetNode()
        if node:
            t = node.GeometricTranslation.Get()
            t = FbxVector4(t[0], t[1], t[2], 1)
            r = node.GeometricRotation.Get()
            r = FbxVector4(r[0], r[1], r[2], 1)
            s = node.GeometricScaling.Get()
            s = FbxVector4(s[0], s[1], s[2], 1)
            
            hasGeometricTransform = False
            if t[0] != 0 or t[1] != 0 or t[2] != 0 or \
               r[0] != 0 or r[1] != 0 or r[2] != 0 or \
               s[0] != 1 or s[1] != 1 or s[2] != 1:
                hasGeometricTransform = True
            
            if hasGeometricTransform:
                geo_transform = FbxMatrix(t,r,s)
            else:
                geo_transform = FbxMatrix()

            transform = None

            if option_geometry:
                # FbxMeshes are local to their node, we need the vertices in global space
                # when scene nodes are not exported
                transform = node.EvaluateGlobalTransform()
                transform = FbxMatrix(transform) * geo_transform

            elif hasGeometricTransform:
                transform = geo_transform
                
            if transform:
                t = FbxVector4(0,0,0,1)
                transform.SetRow(3, t)

                for i in range(len(normal_values)):
                    n = normal_values[i]
                    normal = FbxVector4(n[0], n[1], n[2])
                    normal = transform.MultNormalize(normal)
                    normal.Normalize()
                    normal_values[i] = convert_fbx_vec3(normal)

        # indices
        vertexId = 0
        for p in range(poly_count):
            poly_size = mesh.GetPolygonSize(p)
            poly_normals = []

            for v in range(poly_size):
                control_point_index = mesh.GetPolygonVertex(p, v)
                
                # mapping mode is by control points. The mesh should be smooth and soft.
                # we can get normals by retrieving each control point
                if mesh_normals.GetMappingMode() == FbxLayerElement.eByControlPoint:

                    # reference mode is direct, the normal index is same as vertex index.
                    # get normals by the index of control vertex
                    if mesh_normals.GetReferenceMode() == FbxLayerElement.eDirect:
                        poly_normals.append(control_point_index)

                    elif mesh_normals.GetReferenceMode() == FbxLayerElement.eIndexToDirect:
                        index = mesh_normals.GetIndexArray().GetAt(control_point_index)
                        poly_normals.append(index)

                # mapping mode is by polygon-vertex.
                # we can get normals by retrieving polygon-vertex.
                elif mesh_normals.GetMappingMode() == FbxLayerElement.eByPolygonVertex:

                    if mesh_normals.GetReferenceMode() == FbxLayerElement.eDirect:
                        poly_normals.append(vertexId)

                    elif mesh_normals.GetReferenceMode() == FbxLayerElement.eIndexToDirect:
                        index = mesh_normals.GetIndexArray().GetAt(vertexId)
                        poly_normals.append(index)

                elif mesh_normals.GetMappingMode() == FbxLayerElement.eByPolygon or \
                     mesh_normals.GetMappingMode() ==  FbxLayerElement.eAllSame or \
                     mesh_normals.GetMappingMode() ==  FbxLayerElement.eNone:       
                    print("unsupported normal mapping mode for polygon vertex")

                vertexId += 1
            normal_indices.append(poly_normals)

        layered_normal_values.append(normal_values)
        layered_normal_indices.append(normal_indices)

    normal_values = []
    normal_indices = []

    # Three.js only supports one layer of normals
    if len(layered_normal_values) > 0:
        normal_values = layered_normal_values[0]
        normal_indices = layered_normal_indices[0]

    return normal_values, normal_indices

def extract_fbx_vertex_colors(mesh):
#   eNone             The mapping is undetermined.
#   eByControlPoint   There will be one mapping coordinate for each surface control point/vertex.
#   eByPolygonVertex  There will be one mapping coordinate for each vertex, for every polygon of which it is a part. This means that a vertex will have as many mapping coordinates as polygons of which it is a part.
#   eByPolygon        There can be only one mapping coordinate for the whole polygon.
#   eByEdge           There will be one mapping coordinate for each unique edge in the mesh. This is meant to be used with smoothing layer elements.
#   eAllSame          There can be only one mapping coordinate for the whole surface.

    layered_color_indices = []
    layered_color_values = []

    poly_count = mesh.GetPolygonCount()
    control_points = mesh.GetControlPoints() 

    for l in range(mesh.GetLayerCount()):
        mesh_colors = mesh.GetLayer(l).GetVertexColors()
        if not mesh_colors:
            continue
          
        colors_array = mesh_colors.GetDirectArray()
        colors_count = colors_array.GetCount()
  
        if colors_count == 0:
            continue

        color_indices = []
        color_values = []

        # values
        for i in range(colors_count):
            color = convert_fbx_color(colors_array.GetAt(i))
            color_values.append(color)

        # indices
        vertexId = 0
        for p in range(poly_count):
            poly_size = mesh.GetPolygonSize(p)
            poly_colors = []

            for v in range(poly_size):
                control_point_index = mesh.GetPolygonVertex(p, v)

                if mesh_colors.GetMappingMode() == FbxLayerElement.eByControlPoint:
                    if mesh_colors.GetReferenceMode() == FbxLayerElement.eDirect:
                        poly_colors.append(control_point_index)
                    elif mesh_colors.GetReferenceMode() == FbxLayerElement.eIndexToDirect:
                        index = mesh_colors.GetIndexArray().GetAt(control_point_index)
                        poly_colors.append(index)
                elif mesh_colors.GetMappingMode() == FbxLayerElement.eByPolygonVertex:
                    if mesh_colors.GetReferenceMode() == FbxLayerElement.eDirect:
                        poly_colors.append(vertexId)
                    elif mesh_colors.GetReferenceMode() == FbxLayerElement.eIndexToDirect:
                        index = mesh_colors.GetIndexArray().GetAt(vertexId)
                        poly_colors.append(index)
                elif mesh_colors.GetMappingMode() == FbxLayerElement.eByPolygon or \
                     mesh_colors.GetMappingMode() ==  FbxLayerElement.eAllSame or \
                     mesh_colors.GetMappingMode() ==  FbxLayerElement.eNone:       
                    print("unsupported color mapping mode for polygon vertex")

                vertexId += 1
            color_indices.append(poly_colors)

    color_values = []
    color_indices = []

    # Three.js only supports one layer of colors
    if len(layered_color_values) > 0:
        color_values = layered_color_values[0]
        color_indices = layered_color_indices[0]

    return color_values, color_indices

def extract_fbx_vertex_uvs(mesh):
#   eNone             The mapping is undetermined.
#   eByControlPoint   There will be one mapping coordinate for each surface control point/vertex.
#   eByPolygonVertex  There will be one mapping coordinate for each vertex, for every polygon of which it is a part. This means that a vertex will have as many mapping coordinates as polygons of which it is a part.
#   eByPolygon        There can be only one mapping coordinate for the whole polygon.
#   eByEdge           There will be one mapping coordinate for each unique edge in the mesh. This is meant to be used with smoothing layer elements.
#   eAllSame          There can be only one mapping coordinate for the whole surface.

    layered_uv_indices = []
    layered_uv_values = []

    poly_count = mesh.GetPolygonCount()
    control_points = mesh.GetControlPoints() 

    for l in range(mesh.GetLayerCount()):
        mesh_uvs = mesh.GetLayer(l).GetUVs()
        if not mesh_uvs:
            continue
          
        uvs_array = mesh_uvs.GetDirectArray()
        uvs_count = uvs_array.GetCount()
  
        if uvs_count == 0:
            continue

        uv_indices = []
        uv_values = []

        # values
        for i in range(uvs_count):
            uv = convert_fbx_vec2(uvs_array.GetAt(i))
            uv_values.append(uv)

        # indices
        vertexId = 0
        for p in range(poly_count):
            poly_size = mesh.GetPolygonSize(p)
            poly_uvs = []

            for v in range(poly_size):
                control_point_index = mesh.GetPolygonVertex(p, v)

                if mesh_uvs.GetMappingMode() == FbxLayerElement.eByControlPoint:
                    if mesh_uvs.GetReferenceMode() == FbxLayerElement.eDirect:
                        poly_uvs.append(control_point_index)
                    elif mesh_uvs.GetReferenceMode() == FbxLayerElement.eIndexToDirect:
                        index = mesh_uvs.GetIndexArray().GetAt(control_point_index)
                        poly_uvs.append(index)
                elif mesh_uvs.GetMappingMode() == FbxLayerElement.eByPolygonVertex:
                    uv_texture_index = mesh.GetTextureUVIndex(p, v)
                    if mesh_uvs.GetReferenceMode() == FbxLayerElement.eDirect or \
                       mesh_uvs.GetReferenceMode() == FbxLayerElement.eIndexToDirect:
                        poly_uvs.append(uv_texture_index)
                elif mesh_uvs.GetMappingMode() == FbxLayerElement.eByPolygon or \
                     mesh_uvs.GetMappingMode() ==  FbxLayerElement.eAllSame or \
                     mesh_uvs.GetMappingMode() ==  FbxLayerElement.eNone:       
                    print("unsupported uv mapping mode for polygon vertex")

                vertexId += 1
            uv_indices.append(poly_uvs)

        layered_uv_values.append(uv_values)
        layered_uv_indices.append(uv_indices)

    return layered_uv_values, layered_uv_indices

# #####################################################
# Generate - Mesh String (for scene output) 
# #####################################################
def generate_mesh_string_for_scene_output(node):
    mesh = node.GetNodeAttribute()
    mesh_list = [ mesh ]

    vertices, vertex_offsets = process_mesh_vertices(mesh_list)
    materials, material_offsets = process_mesh_materials(mesh_list)

    normals_to_indices = generate_unique_normals_dictionary(mesh_list)
    colors_to_indices = generate_unique_colors_dictionary(mesh_list)
    uvs_to_indices_list = generate_unique_uvs_dictionary_layers(mesh_list)
    
    normal_values = generate_normals_from_dictionary(normals_to_indices)
    color_values = generate_colors_from_dictionary(colors_to_indices)
    uv_values = generate_uvs_from_dictionary_layers(uvs_to_indices_list)

    faces = process_mesh_polygons(mesh_list, 
                normals_to_indices, 
                colors_to_indices, 
                uvs_to_indices_list, 
                vertex_offsets, 
                material_offsets)

    nuvs = []
    for layer_index, uvs in enumerate(uv_values):
        nuvs.append(str(len(uvs)))

    nvertices = len(vertices)
    nnormals = len(normal_values)
    ncolors = len(color_values)
    nfaces = len(faces)
    nuvs = ",".join(nuvs)
    
    aabb_min, aabb_max = generate_bounding_box(vertices)
    aabb_min = ",".join(str(f) for f in aabb_min)
    aabb_max = ",".join(str(f) for f in aabb_max)

    vertices = ",".join(getVector3String(v, True) for v in vertices)
    normals  = ",".join(getVector3String(v, True) for v in normal_values)
    colors   = ",".join(getVector3String(v, True) for v in color_values)
    faces    = ",".join(faces)
    uvs      = generate_uvs(uv_values)

    bones   = ""
    weights = ""
    indices = ""
    nskinning_bones   = 0
    nskinning_weights = 0
    nskinning_indices = 0

    if option_animation: 
        skinning_weights = process_mesh_skin_weights(mesh_list)
        skinning_indices = []

        #TODO: merge skeletons when len(mesh_list) > 0
        skinning_bones = process_mesh_skeleton_hierarchy(scene, mesh_list[0])

        for i in range(len(skinning_weights)):
            vertex_weights = skinning_weights[i]
            for j in range(len(vertex_weights)):
                weight = vertex_weights[j]
                if weight[0] > 0:
                    bone_node = weight[1].GetLink()
                    for k in range(len(skinning_bones)):
                        bone = skinning_bones[k]
                        if bone == bone_node:
                            skinning_indices.append(k)
                            break
                else:
                    skinning_indices.append(0)

        nskinning_bones   = len(skinning_bones)
        nskinning_weights = len(skinning_weights) * 2
        nskinning_indices = len(skinning_indices)

        bones    = ",".join(getLabelString(getObjectName(b)) for b in skinning_bones)
        weights  = ",".join(str(round(w[0],6)) for l in skinning_weights for w in l)
        indices  = ",".join(str(i) for i in skinning_indices)

    metadata = [

    '		"vertices" : ' + str(nvertices) + ',',
    '		"skinWeights" : ' + str(nskinning_weights) + ',',
    '		"skinIndices" : ' + str(nskinning_indices) + ',',
    '		"skinBones" : ' + str(nskinning_bones) + ',',
    '		"normals" : ' + str(nnormals) + ',',
    '		"colors" : ' + str(ncolors) + ',',
    '		"faces" : ' + str(nfaces) + ',',
    '		"uvs" : ' + getArrayString(nuvs),

    ]

    skinning = [

    '		"weights" : ' + getArrayString(weights) + ',',   
    '		"indices" : ' + getArrayString(indices) + ',',   
    '		"bones" : ' + getArrayString(bones)    

    ]

    aabb = [

    '		"min" : ' + getArrayString(aabb_min) + ',',   
    '		"max" : ' + getArrayString(aabb_max),   

    ]

    metadata = generateMultiLineString( metadata, '\n\t\t', 0 )
    skinning = generateMultiLineString( skinning, '\n\t\t', 0 )
    aabb = generateMultiLineString( aabb, '\n\t\t', 0 )

    output = [

    '\t' + getLabelString( getEmbedName( node, True ) ) + ' : {',

    '	"metadata" :',
    '	{',
    metadata,
    '	},',
    '',

    '	"boundingBox" :',
    '	{',
    aabb,
    '	},',
    '',

    '	"skinning" :',
    '	{',
    skinning,
    '	},',
    '',

    '	"scale" : ' + str( 1 ) + ',',   
    '	"materials" : ' + getArrayString("") + ',',   
    '	"vertices" : ' + getArrayString(vertices) + ',',   
    '	"normals" : ' + getArrayString(normals) + ',',   
    '	"colors" : ' + getArrayString(colors) + ',',   
    '	"uvs" : ' + getArrayString(uvs) + ',',   
    '	"faces" : ' + getArrayString(faces),
    '}'

    ]
    
    return generateMultiLineString( output, '\n\t\t', 0 )

# #####################################################
# Generate - Mesh String (for non-scene output) 
# #####################################################
def generate_mesh_string_for_non_scene_output(scene):
    mesh_list = generate_mesh_list(scene)

    vertices, vertex_offsets = process_mesh_vertices(mesh_list)
    materials, material_offsets = process_mesh_materials(mesh_list)

    normals_to_indices = generate_unique_normals_dictionary(mesh_list)
    colors_to_indices = generate_unique_colors_dictionary(mesh_list)
    uvs_to_indices_list = generate_unique_uvs_dictionary_layers(mesh_list)
    
    normal_values = generate_normals_from_dictionary(normals_to_indices)
    color_values = generate_colors_from_dictionary(colors_to_indices)
    uv_values = generate_uvs_from_dictionary_layers(uvs_to_indices_list)

    faces = process_mesh_polygons(mesh_list, 
                normals_to_indices, 
                colors_to_indices, 
                uvs_to_indices_list, 
                vertex_offsets, 
                material_offsets)

    nuvs = []
    for layer_index, uvs in enumerate(uv_values):
        nuvs.append(str(len(uvs)))

    nvertices = len(vertices)
    nnormals = len(normal_values)
    ncolors = len(color_values)
    nfaces = len(faces)
    nuvs = ",".join(nuvs)

    aabb_min, aabb_max = generate_bounding_box(vertices)
    aabb_min = ",".join(str(f) for f in aabb_min)
    aabb_max = ",".join(str(f) for f in aabb_max)

    vertices = ",".join(getVector3String(v, True) for v in vertices)
    normals  = ",".join(getVector3String(v, True) for v in normal_values)
    colors   = ",".join(getVector3String(v, True) for v in color_values)
    faces    = ",".join(faces)
    uvs      = generate_uvs(uv_values)

    output = [

    '{',
    '	"metadata"  : {',
    '		"formatVersion" : 3.2,',
    '		"type"		: "geometry",',
    '		"generatedBy"	: "convert-to-threejs.py"' + ',',
    '		"vertices" : ' + str(nvertices) + ',',
    '		"normals" : ' + str(nnormals) + ',',
    '		"colors" : ' + str(ncolors) + ',',
    '		"faces" : ' + str(nfaces) + ',',
    '		"uvs" : ' + getArrayString(nuvs),
    '	},',
    '	"boundingBox"  : {',
    '		"min" : ' + getArrayString(aabb_min) + ',',   
    '		"max" : ' + getArrayString(aabb_max),   
    '	},',
    '	"scale" : ' + str( 1 ) + ',',   
    '	"materials" : ' + getArrayString("") + ',',   
    '	"vertices" : ' + getArrayString(vertices) + ',',   
    '	"normals" : ' + getArrayString(normals) + ',',   
    '	"colors" : ' + getArrayString(colors) + ',',   
    '	"uvs" : ' + getArrayString(uvs) + ',',   
    '	"faces" : ' + getArrayString(faces),
    '}'

    ]

    return generateMultiLineString( output, '\n', 0 )

# #####################################################
# Process - Mesh Geometry
# #####################################################
def generate_normal_key(normal):
    return (round(normal[0], 6), round(normal[1], 6), round(normal[2], 6))

def generate_color_key(color):
    return getHex(color)

def generate_uv_key(uv):
    return (round(uv[0], 6), round(uv[1], 6))
                
def append_non_duplicate_uvs(source_uvs, dest_uvs, counts):
    source_layer_count = len(source_uvs)
    for layer_index in range(source_layer_count):

        dest_layer_count = len(dest_uvs)

        if dest_layer_count <= layer_index:
            dest_uv_layer = {}
            count = 0
            dest_uvs.append(dest_uv_layer)
            counts.append(count)
        else:
            dest_uv_layer = dest_uvs[layer_index]
            count = counts[layer_index]

        source_uv_layer = source_uvs[layer_index]

        for uv in source_uv_layer:
            key = generate_uv_key(uv) 
            if key not in dest_uv_layer:
                dest_uv_layer[key] = count
                count += 1

        counts[layer_index] = count

    return counts

def generate_unique_normals_dictionary(mesh_list):
    normals_dictionary = {}
    nnormals = 0
      
    # Merge meshes, remove duplicate data
    for mesh in mesh_list:
        node = mesh.GetNode()
        normal_values, normal_indices = extract_fbx_vertex_normals(mesh)

        if len(normal_values) > 0:
            for normal in normal_values:
                key = generate_normal_key(normal) 
                if key not in normals_dictionary:
                    normals_dictionary[key] = nnormals
                    nnormals += 1

    return normals_dictionary

def generate_unique_colors_dictionary(mesh_list):
    colors_dictionary = {}
    ncolors = 0
      
    # Merge meshes, remove duplicate data
    for mesh in mesh_list:
        color_values, color_indices = extract_fbx_vertex_colors(mesh)

        if len(color_values) > 0:
            for color in color_values:
                key = generate_color_key(color) 
                if key not in colors_dictionary:
                    colors_dictionary[key] = count
                    count += 1

    return colors_dictionary

def generate_unique_uvs_dictionary_layers(mesh_list):
    uvs_dictionary_layers = []
    nuvs_list = []

    # Merge meshes, remove duplicate data
    for mesh in mesh_list:
        uv_values, uv_indices = extract_fbx_vertex_uvs(mesh)

        if len(uv_values) > 0:
            nuvs_list = append_non_duplicate_uvs(uv_values, uvs_dictionary_layers, nuvs_list)

    return uvs_dictionary_layers

def generate_normals_from_dictionary(normals_dictionary):
    normal_values = []
    for key, index in sorted(normals_dictionary.items(), key = operator.itemgetter(1)):
        normal_values.append(key)

    return normal_values

def generate_colors_from_dictionary(colors_dictionary):
    color_values = []
    for key, index in sorted(colors_dictionary.items(), key = operator.itemgetter(1)):
        color_values.append(key)

    return color_values

def generate_uvs_from_dictionary_layers(uvs_dictionary_layers):
    uv_values = []
    for uvs_dictionary in uvs_dictionary_layers:
        uv_values_layer = []    
        for key, index in sorted(uvs_dictionary.items(), key = operator.itemgetter(1)):
            uv_values_layer.append(key)
        uv_values.append(uv_values_layer)

    return uv_values

def generate_normal_indices_for_poly(poly_index, mesh_normal_values, mesh_normal_indices, normals_to_indices):
    if len(mesh_normal_indices) <= 0:
        return []

    poly_normal_indices = mesh_normal_indices[poly_index]
    poly_size = len(poly_normal_indices)

    output_poly_normal_indices = []
    for v in range(poly_size):
        normal_index = poly_normal_indices[v]
        normal_value = mesh_normal_values[normal_index]

        key = generate_normal_key(normal_value)

        output_index = normals_to_indices[key]
        output_poly_normal_indices.append(output_index)

    return output_poly_normal_indices

def generate_color_indices_for_poly(poly_index, mesh_color_values, mesh_color_indices, colors_to_indices):
    if len(mesh_color_indices) <= 0:
        return []

    poly_color_indices = mesh_color_indices[poly_index]
    poly_size = len(poly_color_indices)

    output_poly_color_indices = []
    for v in range(poly_size):
        color_index = poly_color_indices[v]
        color_value = mesh_color_values[color_index]

        key = generate_color_key(color_value)

        output_index = colors_to_indices[key]
        output_poly_color_indices.append(output_index)

    return output_poly_color_indices

def generate_uv_indices_for_poly(poly_index, mesh_uv_values, mesh_uv_indices, uvs_to_indices):
    if len(mesh_uv_indices) <= 0:
        return []

    poly_uv_indices = mesh_uv_indices[poly_index]
    poly_size = len(poly_uv_indices)

    output_poly_uv_indices = []
    for v in range(poly_size):
        uv_index = poly_uv_indices[v]
        uv_value = mesh_uv_values[uv_index]

        key = generate_uv_key(uv_value)

        output_index = uvs_to_indices[key]
        output_poly_uv_indices.append(output_index)

    return output_poly_uv_indices

def process_mesh_vertices(mesh_list):
    vertex_offset = 0
    vertex_offset_list = [0]
    vertices = []
    for mesh in mesh_list:
        node = mesh.GetNode()
        mesh_vertices = extract_fbx_vertex_positions(mesh)
                
        vertices.extend(mesh_vertices[:])
        vertex_offset += len(mesh_vertices)
        vertex_offset_list.append(vertex_offset)

    return vertices, vertex_offset_list


def process_mesh_materials(mesh_list):
    material_offset = 0
    material_offset_list = [0]
    materials_list = []

    #TODO: remove duplicate mesh references
    for mesh in mesh_list:
        node = mesh.GetNode()
                
        material_count = node.GetMaterialCount()
        if material_count > 0:
            for l in range(mesh.GetLayerCount()):
                materials = mesh.GetLayer(l).GetMaterials()
                if materials:
                    if materials.GetReferenceMode() == FbxLayerElement.eIndex:
                        #Materials are in an undefined external table
                        continue

                    for i in range(material_count):
                        material = node.GetMaterial(i)
                        materials_list.append( material )

                    material_offset += material_count
                    material_offset_list.append(material_offset)

    return materials_list, material_offset_list

def process_mesh_polygons(mesh_list, normals_to_indices, colors_to_indices, uvs_to_indices_list, vertex_offset_list, material_offset_list):
    faces = []
    for mesh_index in range(len(mesh_list)):
        mesh = mesh_list[mesh_index]

        flipWindingOrder = False
        node = mesh.GetNode()
        if node:
            local_scale = node.EvaluateLocalScaling()
            if local_scale[0] < 0 or local_scale[1] < 0 or local_scale[2] < 0:
                flipWindingOrder = True

        poly_count = mesh.GetPolygonCount()
        control_points = mesh.GetControlPoints() 

        normal_values, normal_indices = extract_fbx_vertex_normals(mesh)
        color_values, color_indices = extract_fbx_vertex_colors(mesh)
        uv_values_layers, uv_indices_layers = extract_fbx_vertex_uvs(mesh)

        for poly_index in range(poly_count):
            poly_size = mesh.GetPolygonSize(poly_index)

            face_normals = generate_normal_indices_for_poly(poly_index, normal_values, normal_indices, normals_to_indices)
            face_colors = generate_color_indices_for_poly(poly_index, color_values, color_indices, colors_to_indices)

            face_uv_layers = []
            for l in range(len(uv_indices_layers)):
                uv_values = uv_values_layers[l]
                uv_indices = uv_indices_layers[l]
                face_uv_indices = generate_uv_indices_for_poly(poly_index, uv_values, uv_indices, uvs_to_indices_list[l])
                face_uv_layers.append(face_uv_indices)
                
            face_vertices = []
            for vertex_index in range(poly_size):
                control_point_index = mesh.GetPolygonVertex(poly_index, vertex_index)
                face_vertices.append(control_point_index)

            #TODO: assign a default material to any mesh without one
            if len(material_offset_list) <= mesh_index:
                material_offset = 0
            else:
                material_offset = material_offset_list[mesh_index]

            vertex_offset = vertex_offset_list[mesh_index]
            
            if poly_size > 4:
                new_face_normals = []
                new_face_colors = []
                new_face_uv_layers = []

                for i in range(poly_size - 2):
                    new_face_vertices = [face_vertices[0], face_vertices[i+1], face_vertices[i+2]]

                    if len(face_normals):
                        new_face_normals = [face_normals[0], face_normals[i+1], face_normals[i+2]]
                    if len(face_colors):
                        new_face_colors = [face_colors[0], face_colors[i+1], face_colors[i+2]]
                    if len(face_uv_layers):
                        new_face_uv_layers = []
                        for layer in face_uv_layers:
                            new_face_uv_layers.append([layer[0], layer[i+1], layer[i+2]])

                    face = generate_mesh_face(mesh, 
                        poly_index,
                        new_face_vertices,
                        new_face_normals,
                        new_face_colors,
                        new_face_uv_layers,
                        vertex_offset,
                        material_offset,
                        flipWindingOrder)
                    faces.append(face)
            else:
                face = generate_mesh_face(mesh, 
                          poly_index, 
                          face_vertices,
                          face_normals,
                          face_colors,
                          face_uv_layers,
                          vertex_offset,
                          material_offset,
                          flipWindingOrder)
                faces.append(face)

    return faces

def generate_mesh_face(mesh, polygon_index, vertex_indices, normals, colors, uv_layers, vertex_offset, material_offset, flipOrder):
    isTriangle = ( len(vertex_indices) == 3 )
    nVertices = 3 if isTriangle else 4

    hasMaterial = False
    for l in range(mesh.GetLayerCount()):
        materials = mesh.GetLayer(l).GetMaterials()
        if materials:
            hasMaterial = True
            break
                
    hasFaceUvs = False
    hasFaceVertexUvs = len(uv_layers) > 0
    hasFaceNormals = False 
    hasFaceVertexNormals = len(normals) > 0
    hasFaceColors = False 
    hasFaceVertexColors = len(colors) > 0

    faceType = 0
    faceType = setBit(faceType, 0, not isTriangle)
    faceType = setBit(faceType, 1, hasMaterial)
    faceType = setBit(faceType, 2, hasFaceUvs)
    faceType = setBit(faceType, 3, hasFaceVertexUvs)
    faceType = setBit(faceType, 4, hasFaceNormals)
    faceType = setBit(faceType, 5, hasFaceVertexNormals)
    faceType = setBit(faceType, 6, hasFaceColors)
    faceType = setBit(faceType, 7, hasFaceVertexColors)

    faceData = []

    # order is important, must match order in JSONLoader

    # face type
    # vertex indices
    # material index
    # face uvs index
    # face vertex uvs indices
    # face color index
    # face vertex colors indices

    faceData.append(faceType)

    if flipOrder:
        if nVertices == 3:
            vertex_indices = [vertex_indices[0], vertex_indices[2], vertex_indices[1]]
            if hasFaceVertexNormals:
                normals = [normals[0], normals[2], normals[1]]
            if hasFaceVertexColors:
                colors = [colors[0], colors[2], colors[1]]
            if hasFaceVertexUvs:
                tmp = []
                for polygon_uvs in uv_layers:
                    tmp.append([polygon_uvs[0], polygon_uvs[2], polygon_uvs[1]])
                uv_layers = tmp
        else: 
            vertex_indices = [vertex_indices[0], vertex_indices[3], vertex_indices[2], vertex_indices[1]]
            if hasFaceVertexNormals:
                normals = [normals[0], normals[3], normals[2], normals[1]]
            if hasFaceVertexColors:
                colors = [colors[0], colors[3], colors[2], colors[1]]
            if hasFaceVertexUvs:
                tmp = []
                for polygon_uvs in uv_layers:
                    tmp.append([polygon_uvs[0], polygon_uvs[3], polygon_uvs[2], polygon_uvs[3]])
                uv_layers = tmp
        
    for i in range(nVertices):
        index = vertex_indices[i] + vertex_offset
        faceData.append(index)

    if hasMaterial:
        material_id = 0
        for l in range(mesh.GetLayerCount()):
            materials = mesh.GetLayer(l).GetMaterials()
            if materials:
                material_id = materials.GetIndexArray().GetAt(polygon_index)
                break
        material_id += material_offset
        faceData.append( material_id )

    if hasFaceVertexUvs:
        for polygon_uvs in uv_layers:
            for i in range(nVertices):
                index = polygon_uvs[i]
                faceData.append(index)

    if hasFaceVertexNormals:
        for i in range(nVertices):
            index = normals[i]
            faceData.append(index)

    if hasFaceVertexColors:
        for i in range(nVertices):
            index = colors[i]
            faceData.append(index)

    return ",".join( map(str, faceData) ) 


# #####################################################
# Generate - Mesh List 
# #####################################################
def generate_mesh_list_from_hierarchy(node, mesh_list):
    if node.GetNodeAttribute() == None:
        pass
    else:
        attribute_type = (node.GetNodeAttribute().GetAttributeType())
        if attribute_type == FbxNodeAttribute.eMesh or \
           attribute_type == FbxNodeAttribute.eNurbs or \
           attribute_type == FbxNodeAttribute.eNurbsSurface or \
           attribute_type == FbxNodeAttribute.ePatch:

            if attribute_type != FbxNodeAttribute.eMesh:
                converter.TriangulateInPlace(node);

            mesh_list.append(node.GetNodeAttribute())

    for i in range(node.GetChildCount()):
        generate_mesh_list_from_hierarchy(node.GetChild(i), mesh_list)

def generate_mesh_list(scene):
    mesh_list = []
    node = scene.GetRootNode()
    if node:
        for i in range(node.GetChildCount()):
            generate_mesh_list_from_hierarchy(node.GetChild(i), mesh_list)
    return mesh_list

# #####################################################
# Generate - Embeds 
# #####################################################
def generate_embed_list_from_hierarchy(node, embed_list):
    if node.GetNodeAttribute() == None:
        pass
    else:
        attribute_type = (node.GetNodeAttribute().GetAttributeType())
        if attribute_type == FbxNodeAttribute.eMesh or \
           attribute_type == FbxNodeAttribute.eNurbs or \
           attribute_type == FbxNodeAttribute.eNurbsSurface or \
           attribute_type == FbxNodeAttribute.ePatch:

            if attribute_type != FbxNodeAttribute.eMesh:
                converter.TriangulateInPlace(node);

            embed_string = generate_mesh_string_for_scene_output(node)
            embed_list.append(embed_string)

    for i in range(node.GetChildCount()):
        generate_embed_list_from_hierarchy(node.GetChild(i), embed_list)

def generate_embed_list(scene):
    embed_list = []
    node = scene.GetRootNode()
    if node:
        for i in range(node.GetChildCount()):
            generate_embed_list_from_hierarchy(node.GetChild(i), embed_list)
    return embed_list

# #####################################################
# Generate - Geometries 
# #####################################################
def generate_geometry_string(node):

    output = [
    '\t' + getLabelString( getGeometryName( node, True ) ) + ' : {',
    '	"type"  : "embedded",',
    '	"id" : ' + getLabelString( getEmbedName( node, True ) ),
    '}'
    ]

    return generateMultiLineString( output, '\n\t\t', 0 )

def generate_geometry_list_from_hierarchy(node, geometry_list):
    if node.GetNodeAttribute() == None:
        pass
    else:
        attribute_type = (node.GetNodeAttribute().GetAttributeType())
        if attribute_type == FbxNodeAttribute.eMesh:
            geometry_string = generate_geometry_string(node)
            geometry_list.append(geometry_string)
    for i in range(node.GetChildCount()):
        generate_geometry_list_from_hierarchy(node.GetChild(i), geometry_list)

def generate_geometry_list(scene):
    geometry_list = []
    node = scene.GetRootNode()
    if node:
        for i in range(node.GetChildCount()):
            generate_geometry_list_from_hierarchy(node.GetChild(i), geometry_list)
    return geometry_list

# #####################################################
# Generate - Camera Names
# #####################################################
def generate_camera_name_list_from_hierarchy(node, camera_list):
    if node.GetNodeAttribute() == None:
        pass
    else:
        attribute_type = (node.GetNodeAttribute().GetAttributeType())
        if attribute_type == FbxNodeAttribute.eCamera:
            camera_string = getObjectName(node) 
            camera_list.append(camera_string)
    for i in range(node.GetChildCount()):
        generate_camera_name_list_from_hierarchy(node.GetChild(i), camera_list)

def generate_camera_name_list(scene):
    camera_list = []
    node = scene.GetRootNode()
    if node:
        for i in range(node.GetChildCount()):
            generate_camera_name_list_from_hierarchy(node.GetChild(i), camera_list)
    return camera_list

# #####################################################
# Generate - Light Object 
# #####################################################
def generate_default_light():
    direction = (1,1,1)
    color = (1,1,1)
    intensity = 80.0

    output = {
      'type': 'DirectionalLight',
      'color': getHex(color),
      'intensity': intensity/100.00,
      'direction': direction,
      'target': getObjectName( None )
    }

    return output

def generate_light_object(node):
    light = node.GetNodeAttribute()
    light_types = ["point", "directional", "spot", "area", "volume"]
    light_type = light_types[light.LightType.Get()]

    transform = node.EvaluateLocalTransform()
    position = transform.GetT()

    output = None

    if light_type == "directional":

        # Three.js directional lights emit light from a point in 3d space to a target node or the origin.
        # When there is no target, we need to take a point, one unit away from the origin, and move it 
        # into the right location so that the origin acts like the target
        
        if node.GetTarget():
            direction = position
        else:
            translation = FbxVector4(0,0,0,0)
            scale = FbxVector4(1,1,1,1)
            rotation = transform.GetR()
            matrix = FbxMatrix(translation, rotation, scale)
            direction = matrix.MultNormalize(FbxVector4(0,1,0,1)) 

        output = {

          'type': 'DirectionalLight',
          'color': getHex(light.Color.Get()),
          'intensity': light.Intensity.Get()/100.0,
          'direction': getVector3( direction ),
          'target': getLabelString( getObjectName( node.GetTarget() ) )

        }

    elif light_type == "point":

        output = {

          'type': 'PointLight',
          'color': getHex(light.Color.Get()),
          'intensity': light.Intensity.Get()/100.0,
          'position': getVector3( position ),
          'distance': ligth.FarAttenuationEnd.Get()

        }

    elif light_type == "spot":

        output = {

          'type': 'SpotLight',
          'color': getHex(light.Color.Get()),
          'intensity': light.Intensity.Get()/100.0,
          'position': getVector3( position ),
          'distance': ligth.FarAttenuationEnd.Get(),
          'angle': ligth.OuterAngle.Get()*math.pi/180,
          'exponent': ligth.DecayType.Get(),
          'target': getLabelString( getObjectName( node.GetTarget() ) )

        }

    return output

def generate_ambient_light(scene):

    scene_settings = scene.GetGlobalSettings()
    ambient_color = scene_settings.GetAmbientColor()
    ambient_color = (ambient_color.mRed, ambient_color.mGreen, ambient_color.mBlue)

    if ambient_color[0] == 0 and ambient_color[1] == 0 and ambient_color[2] == 0:
        return None

    output = {

      'type': 'AmbientLight',
      'color': getHex(ambient_color)

    }

    return output
    
# #####################################################
# Generate - Camera Object 
# #####################################################
def generate_default_camera():
    position = (100, 100, 100)
    near = 0.1
    far = 1000
    fov = 75

    name = 'DefaultCamera'
    output = {

      'type': 'PerspectiveCamera',
      'fov': fov,
      'near': near,
      'far': far,
      'position': getVector3( position ) 

    }

    return name, output

def generate_camera_object(node):
    camera = node.GetNodeAttribute()

    target_node = node.GetTarget()
    target = ""
    if target_node:
        transform = target.EvaluateLocalTransform()
        target = transform.GetT()
    else:
        target = camera.InterestPosition.Get()

    position = camera.Position.Get()
  
    projection_types = [ "perspective", "orthogonal" ]
    projection = projection_types[camera.ProjectionType.Get()]

    near = camera.NearPlane.Get()
    far = camera.FarPlane.Get()

    name = getObjectName( node )
    output = {}

    if projection == "perspective":

        aspect = camera.PixelAspectRatio.Get()
        fov = camera.FieldOfView.Get()

        output = {

          'type': 'PerspectiveCamera',
          'fov': fov,
          'aspect': aspect,
          'near': near,
          'far': far,
          'position': getVector3( position )

        }

    elif projection == "orthogonal":

        left = ""
        right = ""
        top = ""
        bottom = ""

        output = {

          'type': 'PerspectiveCamera',
          'left': left,
          'right': right,
          'top': top,
          'bottom': bottom,
          'near': near,
          'far': far,
          'position': getVector3( position )

        }

    return output

# #####################################################
# Generate - Mesh Object 
# #####################################################
def generate_mesh_object(node):
    mesh = node.GetNodeAttribute()
    transform = node.EvaluateLocalTransform()
    position = transform.GetT()
    scale = transform.GetS()
    rotation = getRadians(transform.GetR())
    quaternion = transform.GetQ()

    material_count = node.GetMaterialCount()
    material_name = ""

    if material_count > 0:
        material_names = []
        for l in range(mesh.GetLayerCount()):
            materials = mesh.GetLayer(l).GetMaterials()
            if materials:
                if materials.GetReferenceMode() == FbxLayerElement.eIndex:
                    #Materials are in an undefined external table
                    continue
                for i in range(material_count):
                    material = node.GetMaterial(i)
                    material_names.append( getMaterialName(material) )

        if not material_count > 1 and not len(material_names) > 0:
            material_names.append('')

        #If this mesh has more than one material, use a proxy material
        material_name = getMaterialName( node, True) if material_count > 1 else material_names[0] 

    skin_count = mesh.GetDeformerCount(FbxDeformer.eSkin)

    output = {
      'geometry': getGeometryName( node, True ),
      'material': material_name,
      'position': getVector3( position ),
      'quaternion': getVector4( quaternion ),
      'scale': getVector3( scale ),
      'skin': skin_count > 0,
      'visible': getObjectVisible( node ),
    }

    return output

# #####################################################
# Generate - Object 
# #####################################################
def generate_object(node):
    node_types = ["Unknown", "Null", "Marker", "Skeleton", "Mesh", "Nurbs", "Patch", "Camera", 
    "CameraStereo", "CameraSwitcher", "Light", "OpticalReference", "OpticalMarker", "NurbsCurve", 
    "TrimNurbsSurface", "Boundary", "NurbsSurface", "Shape", "LODGroup", "SubDiv", "CachedEffect", "Line"]

    transform = node.EvaluateLocalTransform()
    position = transform.GetT()
    scale = transform.GetS()
    rotation = getRadians(transform.GetR())
    quaternion = transform.GetQ()

    node_type = ""
    if node.GetNodeAttribute() == None:
        node_type = "Null"
    else:
        node_type = node_types[node.GetNodeAttribute().GetAttributeType()]

    name = getObjectName( node )
    output = {
      'fbx_type': node_type,
      'position': getVector3( position ),
      'quaternion': getVector4( quaternion ),
      'scale': getVector3( scale ),
      'visible': getObjectVisible( node )
    }

    return output

# #####################################################
# Parse - Objects 
# #####################################################
def generate_object_hierarchy(node, object_dict):
    object_count = 0
    if node.GetNodeAttribute() == None:
        object_data = generate_object(node)
    else:
        attribute_type = (node.GetNodeAttribute().GetAttributeType())
        if attribute_type == FbxNodeAttribute.eMesh:
            object_data = generate_mesh_object(node)
        elif attribute_type == FbxNodeAttribute.eLight:
            object_data = generate_light_object(node)
        elif attribute_type == FbxNodeAttribute.eCamera:
            object_data = generate_camera_object(node)
        else:
            object_data = generate_object(node)

    object_count += 1
    object_name = getObjectName(node)

    object_children = {}
    for i in range(node.GetChildCount()):
        object_count += generate_object_hierarchy(node.GetChild(i), object_children)

    if node.GetChildCount() > 0:
        # Having 'children' above other attributes is hard to read.
        # We can send it to the bottom using the last letter of the alphabet 'z'. 
        # This letter is removed from the final output.
        if option_pretty_print:
            object_data['zchildren'] = object_children
        else:
            object_data['children'] = object_children

    object_dict[object_name] = object_data

    return object_count

def generate_scene_objects(scene):
    object_count = 0
    object_dict = {}

    ambient_light = generate_ambient_light(scene)
    if ambient_light:
        object_dict['AmbientLight'] = ambient_light
        object_count += 1

    if option_default_light:
        default_light = generate_default_light()
        object_dict['DefaultLight'] = default_light
        object_count += 1

    if option_default_camera:
        default_camera = generate_default_camera()
        object_dict['DefaultCamera'] = default_camera
        object_count += 1

    node = scene.GetRootNode()
    if node:
        for i in range(node.GetChildCount()):
            object_count += generate_object_hierarchy(node.GetChild(i), object_dict)

    return object_dict, object_count

# #####################################################
# Parse - Poses
# #####################################################
def get_local_pose_transform(pose, node_index):
    node = pose.GetNode(node_index)
    parent = node.GetParent()

    if parent:
        parent_index = pose.Find(parent)
        a = pose.GetMatrix(node_index)
        b = pose.GetMatrix(parent_index)
        c = b.Inverse()
        return c * a
    else:
        return pose.GetMatrix(node_index)

def generate_pose_node_string(pose, node_index, padding):
    node = pose.GetNode(node_index)
    transform = get_local_pose_transform(pose, node_index)

    t = FbxVector4()
    q = FbxQuaternion()
    sh = FbxVector4()
    sc = FbxVector4()

    sign = transform.GetElements(t, q, sh, sc)

    output = [

    getLabelString( getObjectName( node ) ) + ' : {',
    '	"position" : ' + getVector3String( t, False, True ) + ',',
    '	"quaternion" : ' + getVector4String( q, False, True ) + ',',
    '	"scale"	   : ' + getVector3String( sc, False, True ),
    '}'

    ]

    return generateMultiLineString( output, '\n\t\t', padding )

def generate_pose_string(pose, padding):
    node_list = []

    for n in range(pose.GetCount()):
        pose_node = generate_pose_node_string(pose, n, 1)
        node_list.append(pose_node)

    pose_nodes = generateMultiLineString( node_list, ',\n\t\t', padding )
      
    output = [ '\t{', pose_nodes, '}', ]

    return generateMultiLineString( output, '\n\t\t', padding )

def generate_pose_list(scene):
    pose_list = []
    
    for p in range(scene.GetPoseCount()):
        pose = scene.GetPose(p)

        pose_string = generate_pose_string(pose, 0)
        pose_list.append(pose_string)

    return pose_list

# #####################################################
# Parse - Animations
# #####################################################
def generate_animation_key_time_list(curve_node):
    time_list = []

    for i in range(curve_node.GetChannelsCount()):
        curve = curve_node.GetCurve(i)
        if not curve:
            continue
        for j in range(curve.KeyGetCount()):
            time = curve.KeyGetTime(j)
            if not time in time_list:
                time_list.append(time)

    time_list.sort(key=lambda time: time.GetSecondDouble())

    return time_list

def generate_keyframe_string(key_list, index, channel_size, padding):
    if index % (channel_size + 1) == 0:
        return '\n' + getPaddingString(padding) + str(round(key_list[index], 6))
    else:
        return str(round(key_list[index], 6))

def generate_curve_node_string(node, curve_node, property_name, key_list, channel_count):
    keys = ",".join(generate_keyframe_string(key_list, i, channel_count, 5) for i in range(len(key_list)))

    output = [

    '\t' + getLabelString( getAnimationCurveName( curve_node, True ) ) + ' : {',
    '	"object" : ' + getLabelString( getObjectName( node ) ) + ',',
    '	"property" : ' + getLabelString( property_name ) + ',',
    '	"channels" : ' + str( channel_count ) + ',',
    '	"keys" : ' + getArrayString( keys ),
    '}'

    ]

    return generateMultiLineString( output, '\n\t\t', 1 )

def generate_curve_string(channel, node, curve_node, stack):
    time_list = generate_animation_key_time_list(curve_node)

    if len(time_list) < 2:
        time_span = stack.GetLocalTimeSpan() 
        start_time = time_span.GetStart()
        stop_time = time_span.GetStop()
        time_list.append(start_time)
        time_list.append(stop_time)

    keyframes = []

    for time in time_list:
        keyframes.append(time.GetSecondDouble())

        t = FbxVector4()
        sh = FbxVector4()
        sc = FbxVector4()
        q = FbxQuaternion()

        transform = FbxMatrix(node.EvaluateLocalTransform(time))
        transform.GetElements(t, q, sh, sc)

        if channel == "position":
            keyframes.append(t[0])
            keyframes.append(t[1])
            keyframes.append(t[2])
        elif channel == "rotation":
            keyframes.append(q[0])
            keyframes.append(q[1])
            keyframes.append(q[2])
            keyframes.append(q[3])
        elif channel == "scale":
            keyframes.append(sc[0])
            keyframes.append(sc[1])
            keyframes.append(sc[2])

    if channel == "rotation":
        return generate_curve_node_string(node, curve_node, channel, keyframes, 4)
    else:
        return generate_curve_node_string(node, curve_node, channel, keyframes, 3)

def find_stack_for_layer(scene, layer):
    animation_count = scene.GetSrcObjectCount(FbxAnimStack.ClassId)
    for i in range(animation_count):
        stack = scene.GetSrcObject(FbxAnimStack.ClassId, i)
        layer_count = stack.GetSrcObjectCount(FbxAnimLayer.ClassId)
        for j in range(layer_count):
            current_layer = stack.GetSrcObject(FbxAnimLayer.ClassId, j)
            if current_layer.GetUniqueID() == layer.GetUniqueID():
                return stack

def generate_animation_curve_list(scene):
    curve_list = []

    unrollFilter = FbxAnimCurveFilterUnroll()
    reduceFilter = FbxAnimCurveFilterKeyReducer()
    syncFilter = FbxAnimCurveFilterKeySync()

    '''
    # Removes too many keys
    reduceFilter.SetKeySync(True)
    animation_count = scene.GetSrcObjectCount(FbxAnimStack.ClassId)
    for i in range(animation_count):
        stack = scene.GetSrcObject(FbxAnimStack.ClassId, i)
        reduceFilter.Apply(stack)
    '''

    animation_count = scene.GetSrcObjectCount(FbxAnimStack.ClassId)
    for i in range(animation_count):
        stack = scene.GetSrcObject(FbxAnimStack.ClassId, i)
        syncFilter.Apply(stack)
        unrollFilter.Apply(stack)
      
    layer_count = scene.GetSrcObjectCount(FbxAnimLayer.ClassId)

    for l in range(layer_count):
        layer = scene.GetSrcObject(FbxAnimLayer.ClassId, l)
        stack = find_stack_for_layer(scene, layer)
        scene.GetEvaluator().SetContext(stack)

        for n in range(scene.GetNodeCount()):
            node = scene.GetNode(n)
                    
            curve_node = node.LclTranslation.GetCurveNode(layer, True)
            curve_string = generate_curve_string('position', node, curve_node, stack)
            curve_list.append(curve_string)

            curve_node = node.LclRotation.GetCurveNode(layer, True)
            curve_string = generate_curve_string('rotation', node, curve_node, stack)
            curve_list.append(curve_string)

            curve_node = node.LclScaling.GetCurveNode(layer, True)
            curve_string = generate_curve_string('scale', node, curve_node, stack)
            curve_list.append(curve_string)

    return curve_list

def generate_animation_layer_string(layer, scene):
    stack = find_stack_for_layer(scene, layer)
    scene.GetEvaluator().SetContext(stack)

    blend_mode_types = ['additive', 'override']
    blend_mode = blend_mode_types[layer.BlendMode.Get()]

    curve_list = []
    for n in range(scene.GetNodeCount()):
        node = scene.GetNode(n)

        curve_node = node.LclTranslation.GetCurveNode(layer, True)
        curve_string = getAnimationCurveName(curve_node, True)
        curve_list.append(curve_string)

        curve_node = node.LclRotation.GetCurveNode(layer, True)
        curve_string = getAnimationCurveName(curve_node, True)
        curve_list.append(curve_string)

        curve_node = node.LclScaling.GetCurveNode(layer, True)
        curve_string = getAnimationCurveName(curve_node, True)
        curve_list.append(curve_string)
        
    output = [
    '\t' + getLabelString( getAnimationLayerName( layer, True ) ) + ' : {',
    '	"blendMode" : ' + getLabelString( blend_mode ) + ',',
    '	"blendWeight" : ' + str( layer.Weight.Get() / 100 ) + ',',
    '	"curves" : ' + getArrayString( ",".join(getLabelString( c ) for c in curve_list) ),
    '}'
    ]

    return generateMultiLineString( output, '\n\t\t', 1 )

def generate_animation_layer_list(scene):
    layer_list = []
    layer_count = scene.GetSrcObjectCount(FbxAnimLayer.ClassId)
    for j in range(layer_count):
        layer = scene.GetSrcObject(FbxAnimLayer.ClassId, j)
        layer_string = generate_animation_layer_string(layer, scene)
        layer_list.append(layer_string)

    return layer_list

def generate_animation_string(animation, scene):
    time_span = animation.GetLocalTimeSpan() 
    start_time = time_span.GetStart()
    stop_time = time_span.GetStop()

    layer_list = []
    layer_count = animation.GetSrcObjectCount(FbxAnimLayer.ClassId)
    for i in range(layer_count):
        layer = animation.GetSrcObject(FbxAnimLayer.ClassId, i)
        layer_string = getAnimationLayerName(layer, True)
        layer_list.append(layer_string)

    output = [
    '\t' + getLabelString( getAnimationName( animation ) ) + ' : {',
    '	"start" : ' + str( start_time.GetSecondDouble() ) + ',',
    '	"stop" : ' + str( stop_time.GetSecondDouble() ) + ',',
    '	"layers" : ' + getArrayString( ",".join(getLabelString( l ) for l in layer_list) ),
    '}'
    ]

    return generateMultiLineString( output, '\n\t\t', 1 )

def generate_animation_list(scene):
    animation_list = []
    animation_count = scene.GetSrcObjectCount(FbxAnimStack.ClassId)
    for i in range(animation_count):
        stack = scene.GetSrcObject(FbxAnimStack.ClassId, i)
        animation_string = generate_animation_string(stack, scene)
        animation_list.append(animation_string)

    return animation_list

def generate_skeleton_list_from_hierarchy(node, skeleton_list):
    if node.GetNodeAttribute() == None:
        pass
    else:
        attribute_type = (node.GetNodeAttribute().GetAttributeType())
        if attribute_type == FbxNodeAttribute.eSkeleton:
            skeleton_list.append(node)
            return
    for i in range(node.GetChildCount()):
        generate_skeleton_list_from_hierarchy(node.GetChild(i), skeleton_list)

def generate_list_of_skeleton_root_nodes(scene):
    skeleton_list = []
    node = scene.GetRootNode()
    if node:
        for i in range(node.GetChildCount()):
            generate_skeleton_list_from_hierarchy(node.GetChild(i), skeleton_list)
    return skeleton_list

def generate_bone_list_from_hierarchy(node, bone_list):
    bone_list.append(node)
    for i in range(node.GetChildCount()):
        generate_bone_list_from_hierarchy(node.GetChild(i), bone_list)

# #####################################################
# Parse - Skinning
# #####################################################
def extract_fbx_skinning_data(mesh):
    cluster_mode_types = [ "Normalize", "Additive", "Total1" ]

    control_points_count = mesh.GetControlPointsCount()
    skin_count = mesh.GetDeformerCount(FbxDeformer.eSkin)

    mesh_weights = []
    for i in range(control_points_count):
        mesh_weights.append([])

    for i in range(skin_count):
        cluster_count = mesh.GetDeformer(i, FbxDeformer.eSkin).GetClusterCount()

        for j in range(cluster_count):
            cluster = mesh.GetDeformer(i, FbxDeformer.eSkin).GetCluster(j)
            cluster_mode = cluster_mode_types[cluster.GetLinkMode()]

            indices = cluster.GetControlPointIndices()
            weights = cluster.GetControlPointWeights()

            for k in range(len(indices)):
                weight = weights[k]
                control_point_index = indices[k]

                weight_mapping = (weight, cluster)

                vertex_weights = mesh_weights[control_point_index]
                vertex_weights.append(weight_mapping)
                mesh_weights[control_point_index] = sorted(vertex_weights, reverse=True)

    # Three.js only supports 2 weights per vertex
    for i in range(control_points_count):
        vertex_weights = mesh_weights[i]
        vertex_weights = vertex_weights[0:2]

        for j in range(2 - len(vertex_weights)):
            vertex_weights.append((0, None))

        a = vertex_weights[0][0]
        b = vertex_weights[1][0]
        length = math.sqrt(a + b)
        if length != 0:
            a = a / length
            b = b / length
        vertex_weights[0] = (a, vertex_weights[0][1])
        vertex_weights[1] = (b, vertex_weights[1][1])

        mesh_weights[i] = vertex_weights

    return mesh_weights

def process_mesh_skin_weights(mesh_list):
    vertex_offset = 0
    vertex_offset_list = [0]
    weights = []
    for mesh in mesh_list:
        node = mesh.GetNode()
        mesh_weights = extract_fbx_skinning_data(mesh)
                
        weights.extend(mesh_weights[:])
        vertex_offset += len(mesh_weights)
        vertex_offset_list.append(vertex_offset)

    return weights

def process_mesh_skeleton_hierarchy(scene, mesh):
    node = mesh.GetNode()

    # find a bone referenced by the skin deform for this mesh
    cluster = mesh.GetDeformer(0, FbxDeformer.eSkin).GetCluster(0)
    mesh_bone = cluster.GetLink()
    
    # find the root node of the skeleton that the bone belongs to
    skeleton_list = generate_list_of_skeleton_root_nodes(scene)
    skeleton_root = None

    for bone in skeleton_list:
        if bone == mesh_bone or bone.FindChild(mesh_bone.GetName()):
            skeleton_root = bone
            break

    skeleton_hierarchy = []        
    generate_bone_list_from_hierarchy(skeleton_root, skeleton_hierarchy)

    return skeleton_hierarchy

# #####################################################
# Parse - Scene (scene output)
# #####################################################
def extract_scene(scene, filename):
    global_settings = scene.GetGlobalSettings()
    objects, nobjects = generate_scene_objects(scene)

    textures = generate_texture_dict(scene)

    materials = generate_material_list(scene)
    geometries = generate_geometry_list(scene)
    embeds = generate_embed_list(scene)
    fogs = []

    ntextures = len(textures)
    nmaterials = len(materials)
    ngeometries = len(geometries)

    position = getVector3String( (0,0,0) )
    rotation = getVector3String( (0,0,0) )
    scale    = getVector3String( (1,1,1) )

    camera_names = generate_camera_name_list(scene)
    scene_settings = scene.GetGlobalSettings()

    # This does not seem to be any help here
    # global_settings.GetDefaultCamera() 

    defcamera = getLabelString(camera_names[0] if len(camera_names) > 0 else "")
    if option_default_camera:
      defcamera = getLabelString('default_camera')

    poses = ""
    animation_takes = ""
    animation_layers = ""
    animation_curves = ""
    if option_animation:
        pose_list = generate_pose_list( scene )
        poses = generateMultiLineString( pose_list, ",\n\n\t", 0 )

        animation_take_list = generate_animation_list( scene )
        animation_takes = generateMultiLineString( animation_take_list, ",\n\n\t", 0 )

        animation_layer_list = generate_animation_layer_list( scene )
        animation_layers = generateMultiLineString( animation_layer_list, ",\n\n\t", 0 )

        animation_curve_list = generate_animation_curve_list( scene )
        animation_curves = generateMultiLineString( animation_curve_list, ",\n\n\t", 0 )

    geometries = generateMultiLineString( geometries, ",\n\n\t", 0 )
    materials = generateMultiLineString( materials, ",\n\n\t", 0 )
    embeds = generateMultiLineString( embeds, ",\n\n\t", 0 )
    fogs = generateMultiLineString( fogs, ",\n\n\t", 0 )

    animation = {
      'takes' : animation_takes,
      'layers' : animation_layers,
      'curves' : animation_curves
    }

    metadata = {
      'formatVersion': 4.0,
      'type': 'scene',
      'generatedBy': 'convert-to-threejs.py',
      'objects': nobjects,
      'geometries': ngeometries,
      'materials': nmaterials,
      'textures': ntextures
    }

    output = {
      'metadata': metadata,
      'objects': objects,
     #'geometries': geometries,
     #'materials': materials,
      'textures': textures,
     #'embeds': embeds,
     #'poses': poses,
     #'animation': animation,
     #'embeds': embeds,
    }

    if option_pretty_print:
        output_string = json.dumps(output, indent=4, cls = CustomEncoder, separators=(',', ': '), sort_keys=True)
        # turn array strings into arrays
        output_string = re.sub(':\s*\"(\[.*\])\"', r': \1', output_string)
        # replace 'zchildren' with children
        output_string = re.sub('zchildren', r'children', output_string)
        # add an extra newline after '"children": {'
        output_string = re.sub('(children.*{\s*\n)', r'\1\n', output_string)
        # add an extra newline after '},'
        output_string = re.sub('},\s*\n', r'},\n\n', output_string)
    else:
        output_string = json.dumps(output)

    return output_string

# #####################################################
# Parse - Geometry (non-scene output) 
# #####################################################
def extract_geometry(scene, filename):
    mesh_string = generate_mesh_string_for_non_scene_output(scene)
    return mesh_string

# #####################################################
# file helpers
# #####################################################
def write_file(filepath, content):
    out = open(filepath, "w")
    out.write(content.encode('utf8', 'replace'))
    out.close()

def read_file(filepath):
    f = open(filepath)
    content = f.readlines()
    f.close()
    return content

def findFilesWithExt(directory, ext, include_path = True):
    ext = ext.lower()
    found = []
    for root, dirs, files in os.walk(directory):
        for filename in files:
            current_ext = os.path.splitext(filename)[1].lower()
            if current_ext == ext:
                if include_path:
                    found.append(os.path.join(root, filename))    
                else:
                    found.append(filename)    
    return found
            
# #####################################################
# Parse - Wavefront MTL 
# #####################################################
def parseMtlFile(filepath, textures):
    global mtl_texture_count

    material_library = []
    content = read_file(filepath)

    comment_char = '#'
    mtl_def = 'newmtl '
    ambi_def = 'map_Ka '   # the ambient texture map
    diff_def = 'map_Kd '   # the diffuse texture map
    spec_def = 'map_Ks '  # specular color texture map
    bump_def0 = 'map_bump '   # some implementations use 'map_bump' instead of 'bump'
    bump_def1 = 'bump '
    material = None
    for line in content:
        if not comment_char in line:

            if mtl_def in line:
                if material:
                    if 'AmbientColor' in material or \
                       'DiffuseColor' in material or \
                       'SpecularColor' in material or \
                       'Bump' in material:
                            material_library.append(material)
                material = {}
                material['name'] = line.split(mtl_def, 1)[1].rstrip()

            elif ambi_def in line:
                texture_def = line.split(ambi_def, 1)[1].rstrip()
                if not texture_def.isspace():
                    for texture_file in textures:
                        if texture_file in texture_def:
                            material['AmbientColor'] = texture_file
                            material['AmbientColorId'] = mtl_texture_count
                            mtl_texture_count = mtl_texture_count + 1

            elif diff_def in line:
                texture_def = line.split(diff_def, 1)[1].rstrip()
                if not texture_def.isspace():
                    for texture_file in textures:
                        if texture_file in texture_def:
                            material['DiffuseColor'] = texture_file
                            material['DiffuseColorId'] = mtl_texture_count
                            mtl_texture_count = mtl_texture_count + 1

            elif spec_def in line:
                texture_def = line.split(spec_def, 1)[1].rstrip()
                if not texture_def.isspace():
                    for texture_file in textures:
                        if texture_file in texture_def:
                            material['SpecularColor'] = texture_file
                            material['SpecularColorId'] = mtl_texture_count
                            mtl_texture_count = mtl_texture_count + 1

            elif bump_def0 in line:
                texture_def = line.split(bump_def0, 1)[1].rstrip()
                if not texture_def.isspace():
                    for texture_file in textures:
                        if texture_file in texture_def:
                            material['Bump'] = texture_file
                            material['BumpId'] = mtl_texture_count
                            mtl_texture_count = mtl_texture_count + 1

            elif bump_def1 in line:
                texture_def = line.split(bump_def1, 1)[1].rstrip()
                if not texture_def.isspace():
                    for texture_file in textures:
                        if texture_file in texture_def:
                            material['Bump'] = texture_file
                            material['BumpId'] = mtl_texture_count
                            mtl_texture_count = mtl_texture_count + 1

    if material:
        if 'AmbientColor' in material or \
           'DiffuseColor' in material or \
           'SpecularColor' in material or \
           'Bump' in material:
                material_library.append(material)

    return material_library

def parseAllMtlFiles(directory):
    files = findFilesWithExt(directory, '.mtl')

    supported_texture_formats = ['.jpg','.png','.jpeg','.gif','.tif','.tiff','.bmp','.svg','.dds','.tga','.pcx']
    texture_files = []
    for ext in supported_texture_formats:
        texture_files = texture_files + findFilesWithExt(directory, ext, False)

    material_library = []
    for filepath in files:
        material_library = material_library + parseMtlFile(filepath, texture_files)

    return material_library

# #####################################################
# main
# #####################################################
if __name__ == "__main__":
    from optparse import OptionParser

    try:
        from FbxCommon import *
    except ImportError:
        import platform
        msg = 'Could not locate the python FBX SDK!\n'
        msg += 'You need to copy the FBX SDK into your python install folder such as '
        if platform.system() == 'Windows' or platform.system() == 'Microsoft':
            msg += '"Python26/Lib/site-packages"'
        elif platform.system() == 'Linux':
            msg += '"/usr/local/lib/python2.6/site-packages"'
        elif platform.system() == 'Darwin':
            msg += '"/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/site-packages"'        
        msg += ' folder.'
        print(msg) 
        sys.exit(1)
    
    usage = "Usage: %prog [source_file.fbx] [output_file.js] [options]"
    parser = OptionParser(usage=usage)

    parser.add_option('-t', '--triangulate', action='store_true', dest='triangulate', help="force quad geometry into triangles", default=False)
    parser.add_option('-x', '--ignore-textures', action='store_true', dest='notextures', help="don't include texture references in output file", default=False)
    parser.add_option('-p', '--force-prefix', action='store_true', dest='prefix', help="prefix all object names in output file", default=False)
    parser.add_option('-f', '--flatten-scene', action='store_true', dest='geometry', help="merge all geometries and apply node transforms", default=False)
    parser.add_option('-a', '--include-animations', action='store_true', dest='animation', help="include animation data in output file", default=False)
    parser.add_option('-m', '--manual-mtl-parse', action='store_true', dest='mtl', help="the fbx sdk may fail to bind all textures for materials, parse .mtl files manually", default=False)
    parser.add_option('-c', '--add-camera', action='store_true', dest='defcamera', help="include default camera in output scene", default=False)
    parser.add_option('-l', '--add-light', action='store_true', dest='deflight', help="include default light in output scene", default=False)

    (options, args) = parser.parse_args()

    option_triangulate = options.triangulate 
    option_textures = True if not options.notextures else False
    option_prefix = options.prefix
    option_geometry = options.geometry 
    option_default_camera = options.defcamera 
    option_default_light = options.deflight 
    option_animation = options.animation 
    option_parse_mtl = options.mtl 

    # Prepare the FBX SDK.
    sdk_manager, scene = InitializeSdkObjects()
    converter = FbxGeometryConverter(sdk_manager)

    # The converter takes an FBX file as an argument.
    if len(args) > 1:
        print("\nLoading file: %s" % args[0])
        result = LoadScene(sdk_manager, scene, args[0])
    else:
        result = False
        print("\nUsage: convert_fbx_to_threejs [source_file.fbx] [output_file.js]\n")

    if not result:
        print("\nAn error occurred while loading the file...")
    else:
        if option_triangulate:
            print("\nForcing geometry to triangles")
            triangulate_scene(scene)
            
        axis_system = FbxAxisSystem.MayaYUp
        axis_system.ConvertScene(scene)
            
        if option_animation:
            if scene.GetSrcObjectCount(FbxSkin.ClassId) <= 0:
                option_animation = False

        if option_parse_mtl:
            # The FBX SDK does not bind all textures in .mtl files, so we have to do it manually
            if os.path.splitext(args[0])[1].lower() == '.obj':
                mtl_library = parseAllMtlFiles(os.path.dirname(args[0]))
            else:
                mtl_library = []

        if option_geometry:
            output_content = extract_geometry(scene, os.path.basename(args[0]))
        else:
            output_content = extract_scene(scene, os.path.basename(args[0]))

        output_path = os.path.join(os.getcwd(), args[1])
        write_file(output_path, output_content)

        print("\nExported Three.js file to:\n%s\n" % output_path)

    # Destroy all objects created by the FBX SDK.
    sdk_manager.Destroy()
    sys.exit(0)
