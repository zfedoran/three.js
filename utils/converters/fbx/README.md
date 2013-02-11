## convert-to-threejs

Utility for converting model files to the Three.js JSON format

## Supported Formats

* Fbx (.fbx) (versions 7.3, 7.2, 7.1, 7.0, 6.1, and 6.0) (non-binary)
* Collada (.dae) (1.5 and earlier) 
* Wavefront/Alias (.obj)
* 3D Studio Max (.3ds)

## Usage 

```
convert_to_threejs.py [source_file] [output_file] [options]

Options:
  -t, --triangulate           force quad geometry into triangles
  -x, --ignore-textures       don't include texture references in output file
  -p, --force-prefix          prefix all object names in output file
  -f, --flatten-scene         merge all geometries and apply node transforms
  -a, --include-animations    include animation data in output file
  -m, --manual-mtl-parse      the fbx sdk may fail to bind all textures for materials, parse .mtl files manually
  -c, --add-camera            include default camera in output scene
  -l, --add-light             include default light in output scene
```

## Supported Features

* Object Hierarchies
* Lights (Ambient, Point, Directional)
* Cameras (Perspective, Ortho)
* Geometries (Triangles, Quads, Nurbs)
* Materials (Phong, Lambert)
* Textures (Diffuse, Emissive, Ambient, Specular, Normal, Bump)
* Multiple UV layers
* Multiple materials per mesh
* Animations (Three.js does not yet support the animation JSON)

## Current Limitations

* Only Lambert and Phong materials are supported
* Some camera properties are not converted correctly
* Some light properties are not converted correctly
* Some material properties are not converted correctly

## Dependencies

### FBX SDK
* Requires Autodesk FBX SDK Python 2013.3 bindings. 

```
You can download the python bindings from the Autodesk website: 
  http://usa.autodesk.com/fbx/
```

```
Don't forget the visit the FBX SDK documentation website:
  http://docs.autodesk.com/FBX/2013/ENU/FBX-SDK-Documentation/cpp_ref/index.html
```

### Python
* Requires Python 2.6 or 3.1 (The FBX SDK requires one of these versions)

``` bash
sudo apt-get install build-essential
wget http://www.python.org/ftp/python/2.6.8/Python-2.6.8.tar.bz2
tar jxf ./Python-2.6.8.tar.bz2
cd ./Python-2.6.8
./configure --prefix=/opt/python2.6.8 && make && make install
```
