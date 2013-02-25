/**
 * @author mrdoob / http://mrdoob.com/
 * @author alteredq / http://alteredqualia.com/
 */

THREE.JSONLoader = function ( showStatus ) {

	THREE.Loader.call( this, showStatus );

	this.withCredentials = false;

};

THREE.JSONLoader.prototype = Object.create( THREE.Loader.prototype );

THREE.JSONLoader.prototype.load = function ( url, callback, texturePath ) {

	var scope = this;

	// todo: unify load API to for easier SceneLoader use

	texturePath = texturePath && ( typeof texturePath === "string" ) ? texturePath : this.extractUrlBase( url );

	this.onLoadStart();
	this.loadAjaxJSON( this, url, callback, texturePath );

};

THREE.JSONLoader.prototype.loadAjaxJSON = function ( context, url, callback, texturePath, callbackProgress ) {

	var xhr = new XMLHttpRequest();

	var length = 0;

	xhr.withCredentials = this.withCredentials;

	xhr.onreadystatechange = function () {

		if ( xhr.readyState === xhr.DONE ) {

			if ( xhr.status === 200 || xhr.status === 0 ) {

				if ( xhr.responseText ) {

					var json = JSON.parse( xhr.responseText );
					context.createModel( json, callback, texturePath );

				} else {

					console.warn( "THREE.JSONLoader: [" + url + "] seems to be unreachable or file there is empty" );

				}

				// in context of more complex asset initialization
				// do not block on single failed file
				// maybe should go even one more level up

				context.onLoadComplete();

			} else {

				console.error( "THREE.JSONLoader: Couldn't load [" + url + "] [" + xhr.status + "]" );

			}

		} else if ( xhr.readyState === xhr.LOADING ) {

			if ( callbackProgress ) {

				if ( length === 0 ) {

					length = xhr.getResponseHeader( "Content-Length" );

				}

				callbackProgress( { total: length, loaded: xhr.responseText.length } );

			}

		} else if ( xhr.readyState === xhr.HEADERS_RECEIVED ) {

			length = xhr.getResponseHeader( "Content-Length" );

		}

	};

	xhr.open( "GET", url, true );
	xhr.send( null );

};

THREE.JSONLoader.prototype.createModel = function ( json, callback, texturePath, sceneJson ) {

	var scope = this,
	geometry = new THREE.Geometry(),
	scale = ( json.scale !== undefined ) ? 1.0 / json.scale : 1.0;

  if ( sceneJson && sceneJson.animations ) {
    preProcessAnimations();
  }

	parseModel( scale );

	parseSkin();
	parseMorphing( scale );

	geometry.computeCentroids();
	geometry.computeFaceNormals();

  function preProcessAnimations() {
    var data = sceneJson;

    if ( data.metadata ) {
      var version = data.metadata.formatVersion;

      if ( version >= 5.0 && data.animations ) {

        var takes = data.animations.takes;
        var layers = data.animations.layers;
        var curves = data.animations.curves;

        for (var key in data.poses) {
          var pose = data.poses[key];
          if ( pose.type == "BindPose" ) {
            var current_pose = pose.children;
            break;
          }
        }

        var skinning = json.skinning;

        var ntakes = Object.keys(takes).length;
        var nlayers = Object.keys(layers).length;
        var ncurves = Object.keys(curves).length;

        parseSceneHierarchy(sceneJson.objects);

        if ( ntakes > 0 && nlayers > 0 && ncurves > 0 && skinning ) {

          var take = takes[Object.keys(takes)[0]];
          var layer = layers[take.layers[0]];
          var root_bone = findRootBone( skinning.bones[0] );

          if ( root_bone ) {
            var num_bones = skinning.bones.length;
            var bones = [];
            var hierarchy = [];

            for ( var i = 0; i < num_bones; i++ ) {
              var bone_name = skinning.bones[i];
              var bone_node = findNode(bone_name, root_bone); 
              var parent_index = -1;

              if (bone_node._parent) {
                parent_index = skinning.bones.indexOf(bone_node._parent._name);
              }

              if (current_pose[bone_name]) {
                bone_node = current_pose[bone_name];
              }
              var bone = {
                "parent" : parent_index,
                "name" : bone_name,
                "pos" : bone_node.position,
                "rot" : bone_node.rotation,
                "rotq" : bone_node.quaternion,
                "scl" : bone_node.scale
              }

              bones.push(bone);

              var keys = {};

              for ( var j = 0; j < layer.curves.length; j++ ) {
                var curve_name = layer.curves[j];
                var curve = curves[curve_name];

                if ( curve.object == bone_name ) {
                  for ( var k = 0; k < curve.keys.length; k+=curve.channels+1 ) {
                    var time = curve.keys[k+0];
                    var value = [];
                    for ( var c = 0; c < curve.channels; c++ ) {
                      value.push(curve.keys[k+c+1]);
                    }
                    addKey(time, value, curve.property, keys);
                  }
                }
              }

              var keyframes = [];
              var times = Object.keys(keys).sort();
              for ( var j = 0; j < times.length; j++ ) {
                var time = times[j];
                var key = keys[time];
                var pos, rot, rotq, scl;

                if ( key.position ) {
                  pos = [];
                  pos.push(key.position[0] || bone_node.position[0]);
                  pos.push(key.position[1] || bone_node.position[1]);
                  pos.push(key.position[2] || bone_node.position[2]);
                }

                if ( key.rotation ) {
                  rot = [];
                  rot.push(key.rotation[0] || bone_node.quaternion[0]);
                  rot.push(key.rotation[1] || bone_node.quaternion[1]);
                  rot.push(key.rotation[2] || bone_node.quaternion[2]);
                  rot.push(key.rotation[3] || bone_node.quaternion[3]);
                }

                if ( key.scale ) {
                  scl = [];
                  scl.push(key.scale[0] || bone_node.scale[0]);
                  scl.push(key.scale[1] || bone_node.scale[1]);
                  scl.push(key.scale[2] || bone_node.scale[2]);
                }

                var keyframe = { time: time };

                if ( pos ) { keyframe.pos = pos; }
                if ( rot ) { keyframe.rot = rot; }
                if ( scl ) { keyframe.scl = scl; }

                keyframes.push(keyframe);
              }

              hierarchy.push({
                "parent" : parent_index,
                "keys" : keyframes
              });
            }

            json.bones = bones;
            json.skinIndices = skinning.indices;
            json.skinWeights = skinning.weights;
            json.animation = {
              "name": Object.keys(takes)[0],
              "length": take.stop - take.start,
              "fps": 25, //TODO: fix this
              "hierarchy": hierarchy
            };
            window.json = json;
          }
        }
      }
    }

    function addKey( time, value, property, dictionary ) { 
      if ( !(time in dictionary) ) { 
        dictionary[time] = {}; 
      }
      dictionary[time][property] = value;
    }

    function findRootBone( name ) {
      var child_name_list = Object.keys(sceneJson.objects);
      var num_children = child_name_list.length;
      for ( var i = num_children - 1; i >= 0 ; i-- ) {
        var node_name = child_name_list[i];
        var node = sceneJson.objects[node_name];
        if ( node_name == name ) {
          return node;
        } else {
          node = findNode( name, sceneJson.objects[child_name_list[i]] ); 
          if ( node ) {
            return node;
          }
        }
      }
      return null;
    }

    function findNode( name, current_node ) {
      if ( current_node._name == name ) {
        return current_node;
      }
      if ( current_node.children ) {
        var child_name_list = Object.keys(current_node.children);
        var num_children = child_name_list.length;
        for ( var i = num_children - 1; i >= 0 ; i-- ) {
          var child_name = child_name_list[i];
          var child_node = current_node.children[child_name];
          var node = findNode( name, child_node );
          if (node) {
            return node;
          }
        }
      }
    }

    function parseSceneHierarchy( scene ) {
      var child_name_list = Object.keys(scene);
      var num_children = child_name_list.length;
      for ( var i = num_children - 1; i >= 0 ; i-- ) {
        var node_name = child_name_list[i];
        var node = scene[node_name];
        node._name = node_name;
        parseNodeHierarchy( node );
      }
    }

    function parseNodeHierarchy( current_node ) {
      if ( current_node.children ) {
        var child_name_list = Object.keys(current_node.children);
        var num_children = child_name_list.length;
        for ( var i = num_children - 1; i >= 0 ; i-- ) {
          var child_name = child_name_list[i];
          var child_node = current_node.children[child_name];
          child_node._name = child_name;
          child_node._parent = current_node;
          var node = parseNodeHierarchy( child_node );
        }
      }
    }
  }

	function parseModel( scale ) {

		function isBitSet( value, position ) {

			return value & ( 1 << position );

		}

		var i, j, fi,

		offset, zLength, nVertices,

		colorIndex, normalIndex, uvIndex, materialIndex,

		type,
		isQuad,
		hasMaterial,
		hasFaceUv, hasFaceVertexUv,
		hasFaceNormal, hasFaceVertexNormal,
		hasFaceColor, hasFaceVertexColor,

		vertex, face, color, normal,

		uvLayer, uvs, u, v,

		faces = json.faces,
		vertices = json.vertices,
		normals = json.normals,
		colors = json.colors,

		nUvLayers = 0;

		// disregard empty arrays

		for ( i = 0; i < json.uvs.length; i++ ) {

			if ( json.uvs[ i ].length ) nUvLayers ++;

		}

		for ( i = 0; i < nUvLayers; i++ ) {

			geometry.faceUvs[ i ] = [];
			geometry.faceVertexUvs[ i ] = [];

		}

		offset = 0;
		zLength = vertices.length;

		while ( offset < zLength ) {

			vertex = new THREE.Vector3();

			vertex.x = vertices[ offset ++ ] * scale;
			vertex.y = vertices[ offset ++ ] * scale;
			vertex.z = vertices[ offset ++ ] * scale;

			geometry.vertices.push( vertex );

		}

		offset = 0;
		zLength = faces.length;

		while ( offset < zLength ) {

			type = faces[ offset ++ ];


			isQuad          	= isBitSet( type, 0 );
			hasMaterial         = isBitSet( type, 1 );
			hasFaceUv           = isBitSet( type, 2 );
			hasFaceVertexUv     = isBitSet( type, 3 );
			hasFaceNormal       = isBitSet( type, 4 );
			hasFaceVertexNormal = isBitSet( type, 5 );
			hasFaceColor	    = isBitSet( type, 6 );
			hasFaceVertexColor  = isBitSet( type, 7 );

			//console.log("type", type, "bits", isQuad, hasMaterial, hasFaceUv, hasFaceVertexUv, hasFaceNormal, hasFaceVertexNormal, hasFaceColor, hasFaceVertexColor);

			if ( isQuad ) {

				face = new THREE.Face4();

				face.a = faces[ offset ++ ];
				face.b = faces[ offset ++ ];
				face.c = faces[ offset ++ ];
				face.d = faces[ offset ++ ];

				nVertices = 4;

			} else {

				face = new THREE.Face3();

				face.a = faces[ offset ++ ];
				face.b = faces[ offset ++ ];
				face.c = faces[ offset ++ ];

				nVertices = 3;

			}

			if ( hasMaterial ) {

				materialIndex = faces[ offset ++ ];
				face.materialIndex = materialIndex;

			}

			// to get face <=> uv index correspondence

			fi = geometry.faces.length;

			if ( hasFaceUv ) {

				for ( i = 0; i < nUvLayers; i++ ) {

					uvLayer = json.uvs[ i ];

					uvIndex = faces[ offset ++ ];

					u = uvLayer[ uvIndex * 2 ];
					v = uvLayer[ uvIndex * 2 + 1 ];

					geometry.faceUvs[ i ][ fi ] = new THREE.Vector2( u, v );

				}

			}

			if ( hasFaceVertexUv ) {

				for ( i = 0; i < nUvLayers; i++ ) {

					uvLayer = json.uvs[ i ];

					uvs = [];

					for ( j = 0; j < nVertices; j ++ ) {

						uvIndex = faces[ offset ++ ];

						u = uvLayer[ uvIndex * 2 ];
						v = uvLayer[ uvIndex * 2 + 1 ];

						uvs[ j ] = new THREE.Vector2( u, v );

					}

					geometry.faceVertexUvs[ i ][ fi ] = uvs;

				}

			}

			if ( hasFaceNormal ) {

				normalIndex = faces[ offset ++ ] * 3;

				normal = new THREE.Vector3();

				normal.x = normals[ normalIndex ++ ];
				normal.y = normals[ normalIndex ++ ];
				normal.z = normals[ normalIndex ];

				face.normal = normal;

			}

			if ( hasFaceVertexNormal ) {

				for ( i = 0; i < nVertices; i++ ) {

					normalIndex = faces[ offset ++ ] * 3;

					normal = new THREE.Vector3();

					normal.x = normals[ normalIndex ++ ];
					normal.y = normals[ normalIndex ++ ];
					normal.z = normals[ normalIndex ];

					face.vertexNormals.push( normal );

				}

			}


			if ( hasFaceColor ) {

				colorIndex = faces[ offset ++ ];

				color = new THREE.Color( colors[ colorIndex ] );
				face.color = color;

			}


			if ( hasFaceVertexColor ) {

				for ( i = 0; i < nVertices; i++ ) {

					colorIndex = faces[ offset ++ ];

					color = new THREE.Color( colors[ colorIndex ] );
					face.vertexColors.push( color );

				}

			}

			geometry.faces.push( face );

		}

	};

	function parseSkin() {

		var i, l, x, y, z, w, a, b, c, d;

		if ( json.skinWeights ) {

			for ( i = 0, l = json.skinWeights.length; i < l; i += 2 ) {

				x = json.skinWeights[ i     ];
				y = json.skinWeights[ i + 1 ];
				z = 0;
				w = 0;

				geometry.skinWeights.push( new THREE.Vector4( x, y, z, w ) );

			}

		}

		if ( json.skinIndices ) {

			for ( i = 0, l = json.skinIndices.length; i < l; i += 2 ) {

				a = json.skinIndices[ i     ];
				b = json.skinIndices[ i + 1 ];
				c = 0;
				d = 0;

				geometry.skinIndices.push( new THREE.Vector4( a, b, c, d ) );

			}

		}

		geometry.bones = json.bones;
		geometry.animation = json.animation;

	};

	function parseMorphing( scale ) {

		if ( json.morphTargets !== undefined ) {

			var i, l, v, vl, dstVertices, srcVertices;

			for ( i = 0, l = json.morphTargets.length; i < l; i ++ ) {

				geometry.morphTargets[ i ] = {};
				geometry.morphTargets[ i ].name = json.morphTargets[ i ].name;
				geometry.morphTargets[ i ].vertices = [];

				dstVertices = geometry.morphTargets[ i ].vertices;
				srcVertices = json.morphTargets [ i ].vertices;

				for( v = 0, vl = srcVertices.length; v < vl; v += 3 ) {

					var vertex = new THREE.Vector3();
					vertex.x = srcVertices[ v ] * scale;
					vertex.y = srcVertices[ v + 1 ] * scale;
					vertex.z = srcVertices[ v + 2 ] * scale;

					dstVertices.push( vertex );

				}

			}

		}

		if ( json.morphColors !== undefined ) {

			var i, l, c, cl, dstColors, srcColors, color;

			for ( i = 0, l = json.morphColors.length; i < l; i++ ) {

				geometry.morphColors[ i ] = {};
				geometry.morphColors[ i ].name = json.morphColors[ i ].name;
				geometry.morphColors[ i ].colors = [];

				dstColors = geometry.morphColors[ i ].colors;
				srcColors = json.morphColors [ i ].colors;

				for ( c = 0, cl = srcColors.length; c < cl; c += 3 ) {

					color = new THREE.Color( 0xffaa00 );
					color.setRGB( srcColors[ c ], srcColors[ c + 1 ], srcColors[ c + 2 ] );
					dstColors.push( color );

				}

			}

		}

	};

	var materials = this.initMaterials( json.materials, texturePath );

	if ( this.needsTangents( materials ) ) geometry.computeTangents();

	callback( geometry, materials );

};
