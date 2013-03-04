## Current Version

The converter requires Autodesk FBX SDK 2013.3 (FBX SDK 2014 is currently in [Beta](http://area.autodesk.com/forum/autodesk-fbx/fbx-sdk/fbx-sdk-beta-site/))

## Documentation

Further documentation is availible through the `FBX SDK Programmer's Guide` on the official website: 

http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/index.html

## Supported File Formats

The FBX SDK can:

    Import FBX files compatible with FBX file format versions 7.3, 7.2, 7.1, 7.0, 6.1, and 6.0
    Export FBX files compatible with FBX file format versions 7.3, 7.2, 7.1, 7.0, and 6.1.

FBX SDK imports and exports FBX files compatible with the following applications:

* MotionBuilder (Version 5.5 and later)
* FBX Plug-in for 3ds Max (All versions)
* FBX Plug-in for Maya (All versions)
* Flame (Version 8.0 and later)
* Flint (Version 8.0 and later)
* Inferno (Version 5.0 and later)
* Smoke	(Version 6.0 and later)
* Revit Architecture (Version 2009.1 and later)
* AutoCAD (Version 2011 and later)

As well, FBX SDK has partial import/export support for the following file formats:

* Autodesk AutoCAD DXF (.dxf) (Version 13 and earlier)
* Collada DAE (.dae) (Version 1.5 and earlier)
* Alias OBJ ( .obj) (All Versions)
* Autodesk 3d Studio Max (.3ds) (Import support only)

## Supported Scene Elements

The [FbxScene](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_scene.html) graph is organized as a tree of [FbxNode](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_node.html) objects. Associated to these nodes are cameras, meshes, NURBS, lights, and other scene elements. These scene elements are specialized instances of [FbxNodeAttribute](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_node_attribute.html). 

### Nodes

The position of a scene element such as a mesh, a light, a camera, a skeleton, or a line can be described by a sequence of translations, rotations, and scaling operations. This geometric transformation data is encapsulated by [FbxNode](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_node.html).

---
        
The FBX SDK and Maya use the same formula to compute a global transformation matrix. The formula used by 3ds Max is different. Be careful to take this into consideration when exporting Mesh vertex positions!

Here is how FBX SDK and Maya compute the transformation matrix for a node:

        WorldTransform = ParentWorldTransform * T * Roff * Rp * Rpre * R * Rpost -1 * Rp -1 * Soff * Sp * S * Sp -1
        
Here is how 3ds Max computes the transformation matrix for a node:

        WorldTransform = ParentWorldTransform * T * R * S * OT * OR * OS
    
More information on how the transformations are calculated internally can be found on the [Computing Transfomation Matrices](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/files/GUID-10CDD63C-79C1-4F2D-BB28-AD2BE65A02ED.htm) page.

---

### Node Attributes

Consider a camera in the scene. In addition to its translation, rotation, and scaling values, it can also define its frame width, frame height, depth of field, motion blur, etc. This additional data is encapsulated by [FbxCamera](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_camera.html), which is a subclass of [FbxNodeAttribute](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_node_attribute.html). [FbxMesh](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_mesh.html) and [FbxLight](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_light.html) are also subclasses of [FbxNodeAttribute](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_node_attribute.html), and may be bound to a [FbxNode](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_node.html) to specify their location in the scene.


Instances of [FbxNode](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_node.html) can exist without a bound [FbxNodeAttribute](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_node_attribute.html). In this case, such a [FbxNode](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_node.html) can be used to group or position its children nodes in the scene.

### Node Attribute Types

* Mesh - [FbxMesh](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_mesh.html)
* Level of detail (LOD) groups - [FbxLodGroup](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_l_o_d_group.html)
* Cameras - [FbxCamera](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_camera.html)
* Lights - [FbxLight](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_light.html)
* NURBS - [FbxNurbs](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_nurbs.html), [FbxNurbsCurve](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_nurbs_curve.html), [FbxNurbsSurface](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_nurbs_surface.html), [FbxTrimNurbsSurface](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_trim_nurbs_surface.html)
* Markers - [FbxMarker](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_marker.html)
* Skeleton segments - [FbxSkeleton](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_skeleton.html)

### Additional Scene Elements

The FBX SDK lets you access, create, or modify the following elements of a scene 

* Textures - [FbxTexture](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_texture.html)
* Materials - [FbxSurfaceMaterial](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_surface_material.html)
* Constraints - [FbxConstraint](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_constraint.html)
* Deformers for morph target or skinned animation - [FbxDeformer](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_deformer.html)
* Scene settings that provide Up-Axis (X/Y/Z) and scene scaling (units) - [FbxGlobalSettings](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_global_settings.html), [FbxAxisSystem](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_axis_system.html)
* Animation curves - [FbxAnimCurve](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_anim_curve.html)
* Rest and bind pose lists - [FbxPose](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_pose.html)




