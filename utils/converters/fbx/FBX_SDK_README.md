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

The FBX SDK lets you access, create, or modify the following elements of a scene ([FbxScene](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_scene.html)):

* Mesh - [FbxMesh](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_mesh.html)
* Level of detail (LOD) groups - [FbxLodGroup](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_l_o_d_group.html)
* Cameras - [FbxCamera](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_camera.html)
* Lights - [FbxLight](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_light.html)
* NURBS - [FbxNurbs](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_nurbs.html), [FbxNurbsCurve](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_nurbs_curve.html), [FbxNurbsSurface](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_nurbs_surface.html), [FbxTrimNurbsSurface](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_trim_nurbs_surface.html)
* Textures - [FbxTexture](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_texture.html)
* Materials - [FbxSurfaceMaterial](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_surface_material.html)
* Constraints - [FbxConstraint](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_constraint.html)
* Deformers for morph target or skinned animation - [FbxDeformer](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_deformer.html)
* Scene settings that provide Up-Axis (X/Y/Z) and scene scaling (units) - [FbxGlobalSettings](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_global_settings.html), [FbxAxisSystem](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_axis_system.html)
* Transformation data including position, rotation, scale, parent - [FbxNode](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_node.html)
* Markers - [FbxMarker](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_marker.html)
* Skeleton segments - [FbxSkeleton](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_skeleton.html)
* Animation curves - [FbxAnimCurve](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_anim_curve.html)
* Rest and bind pose lists - [FbxPose](http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_pose.html)

