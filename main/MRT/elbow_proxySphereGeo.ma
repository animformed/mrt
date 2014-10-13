//Maya ASCII 2011 scene
//Name: elbow_proxySphereGeo.ma
//Codeset: 1252
requires maya "2011";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya 2011";
fileInfo "version" "2011 x64";
fileInfo "cutIdentifier" "201209210409-845513";
createNode transform -n "proxy_elbow_preTransform";
	setAttr -k off ".v";
	setAttr -k off ".tx";
	setAttr -k off ".ty";
	setAttr -k off ".tz";
	setAttr -k off ".rx";
	setAttr -k off ".ry";
	setAttr -k off ".rz";
	setAttr -k off ".sx";
	setAttr -k off ".sy";
	setAttr -k off ".sz";
	setAttr ".rp" -type "double3" 0.50009125471115112 0.5 0.50009119510650635 ;
	setAttr ".sp" -type "double3" 0.50009125471115112 0.5 0.50009119510650635 ;
createNode transform -n "proxy_elbow_scaleTransform" -p "proxy_elbow_preTransform";
	setAttr -k off ".v";
	setAttr -k off ".tx";
	setAttr -k off ".ty";
	setAttr -k off ".tz";
	setAttr -k off ".rx";
	setAttr -k off ".ry";
	setAttr -k off ".rz";
	setAttr -k off ".sx";
	setAttr -k off ".sy";
	setAttr -k off ".sz";
	setAttr ".rp" -type "double3" 0.50009125471115112 0.5 0.50009119510650635 ;
	setAttr ".sp" -type "double3" 0.50009125471115112 0.5 0.50009119510650635 ;
createNode transform -n "proxy_elbow_geo" -p "proxy_elbow_scaleTransform";
	setAttr -k off ".v";
	setAttr -k off ".tx";
	setAttr -k off ".ty";
	setAttr -k off ".tz";
	setAttr -k off ".rx";
	setAttr -k off ".ry";
	setAttr -k off ".rz";
	setAttr -k off ".sx";
	setAttr -k off ".sy";
	setAttr -k off ".sz";
	setAttr ".rp" -type "double3" 0.50009125471115112 0.50000001155833407 0.50009117527390279 ;
	setAttr ".sp" -type "double3" 0.50009125471115112 0.50000001155833407 0.50009117527390279 ;
createNode mesh -n "proxy_elbow_geoShape" -p "proxy_elbow_geo";
	addAttr -ci true -sn "mso" -ln "miShadingSamplesOverride" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "msh" -ln "miShadingSamples" -min 0 -smx 8 -at "float";
	addAttr -ci true -sn "mdo" -ln "miMaxDisplaceOverride" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "mmd" -ln "miMaxDisplace" -min 0 -smx 1 -at "float";
	setAttr -k off ".v";
	setAttr ".mb" no;
	setAttr ".csh" no;
	setAttr ".rcsh" no;
	setAttr ".vis" no;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 42 ".uvst[0].uvsp[0:41]" -type "float2" 0.61048543 0.04576458
		 0.5 1.4901161e-008 0.38951457 0.04576458 0.34375 0.15625 0.38951457 0.26673543 0.5
		 0.3125 0.61048543 0.26673543 0.65625 0.15625 0.375 0.3125 0.40625 0.3125 0.4375 0.3125
		 0.46875 0.3125 0.5 0.3125 0.53125 0.3125 0.5625 0.3125 0.59375 0.3125 0.625 0.3125
		 0.375 0.68843985 0.40625 0.68843985 0.4375 0.68843985 0.46875 0.68843985 0.5 0.68843985
		 0.53125 0.68843985 0.5625 0.68843985 0.59375 0.68843985 0.625 0.68843985 0.61048543
		 0.73326457 0.5 0.6875 0.38951457 0.73326457 0.34375 0.84375 0.38951457 0.95423543
		 0.5 1 0.61048543 0.95423543 0.65625 0.84375 0.52288228 0.89899272 0.47711772 0.78850728
		 0.45619842 0.92661405 0.41043386 0.81612861 0.44475728 0.13336772 0.55524272 0.17913228
		 0.41713592 0.20005158 0.52762139 0.24581614;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".smo" no;
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
	setAttr -s 24 ".vt[0:23]"  0.57271171 0.4217726 0.32476988 0.42747074 0.4217726 0.32476988
		 0.32476991 0.4217726 0.42747074 0.32476991 0.4217726 0.57271165 0.42747074 0.4217726 0.67541254
		 0.57271171 0.4217726 0.67541254 0.6754126 0.4217726 0.57271171 0.6754126 0.4217726 0.42747065
		 0.57271171 0.5782274 0.32476988 0.42747074 0.5782274 0.32476988 0.32476991 0.5782274 0.42747074
		 0.32476991 0.5782274 0.57271165 0.42747074 0.5782274 0.67541254 0.57271171 0.5782274 0.67541254
		 0.6754126 0.5782274 0.57271171 0.6754126 0.5782274 0.42747065 0.57271171 0.67506868 0.42747068
		 0.57271171 0.67506868 0.57271171 0.42747074 0.67506868 0.42747074 0.42747074 0.67506868 0.57271171
		 0.42747074 0.32493138 0.42747074 0.57271171 0.32493138 0.42747074 0.42747074 0.32493138 0.57271165
		 0.57271171 0.32493138 0.57271165;
	setAttr -s 48 ".ed[0:47]"  0 1 0 1 2 0 2 3 0 3 4 0 4 5 0 5 6 0 6 7 0
		 7 0 0 8 9 0 9 10 0 10 11 0 11 12 0 12 13 0 13 14 0 14 15 0 15 8 0 0 8 0 1 9 0 2 10 0
		 3 11 0 4 12 0 5 13 0 6 14 0 7 15 0 10 18 0 11 19 0 16 15 0 8 16 0 17 14 0 16 17 0
		 17 13 0 18 16 0 9 18 0 19 17 0 18 19 0 19 12 0 1 20 0 0 21 0 20 22 0 2 20 0 21 23 0
		 20 21 0 21 7 0 22 4 0 3 22 0 23 5 0 22 23 0 23 6 0;
	setAttr -s 26 -ch 96 ".fc[0:25]" -type "polyFaces" 
		f 4 0 17 -9 -17
		mu 0 4 8 9 18 17
		f 4 1 18 -10 -18
		mu 0 4 9 10 19 18
		f 4 2 19 -11 -19
		mu 0 4 10 11 20 19
		f 4 3 20 -12 -20
		mu 0 4 11 12 21 20
		f 4 4 21 -13 -21
		mu 0 4 12 13 22 21
		f 4 5 22 -14 -22
		mu 0 4 13 14 23 22
		f 4 6 23 -15 -23
		mu 0 4 14 15 24 23
		f 4 7 16 -16 -24
		mu 0 4 15 16 25 24
		f 3 43 -4 44
		mu 0 3 40 4 3
		f 3 27 26 15
		mu 0 3 32 34 33
		f 4 -27 29 28 14
		mu 0 4 33 34 35 26
		f 3 -29 30 13
		mu 0 3 26 35 27
		f 4 8 32 31 -28
		mu 0 4 32 31 36 34
		f 4 -30 -32 34 33
		mu 0 4 35 34 36 37
		f 4 -31 -34 35 12
		mu 0 4 27 35 37 28
		f 3 -33 9 24
		mu 0 3 36 31 30
		f 4 -35 -25 10 25
		mu 0 4 37 36 30 29
		f 3 -36 -26 11
		mu 0 3 28 37 29
		f 4 45 -5 -44 46
		mu 0 4 41 5 4 40
		f 3 47 -6 -46
		mu 0 3 41 6 5
		f 3 36 -40 -2
		mu 0 3 1 38 2
		f 4 37 -42 -37 -1
		mu 0 4 0 39 38 1
		f 3 -8 -43 -38
		mu 0 3 0 7 39
		f 4 38 -45 -3 39
		mu 0 4 38 40 3 2
		f 4 40 -47 -39 41
		mu 0 4 39 41 40 38
		f 4 42 -7 -48 -41
		mu 0 4 39 7 6 41;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
	setAttr ".vnm" 0;
select -ne :time1;
	setAttr ".o" 0;
select -ne :renderPartition;
	setAttr -s 2 ".st";
select -ne :initialShadingGroup;
	setAttr ".ro" yes;
select -ne :initialParticleSE;
	setAttr ".ro" yes;
select -ne :defaultShaderList1;
	setAttr -s 2 ".s";
select -ne :postProcessList1;
	setAttr -s 2 ".p";
select -ne :defaultRenderingList1;
select -ne :renderGlobalsList1;
select -ne :defaultHardwareRenderGlobals;
	setAttr ".fn" -type "string" "im";
	setAttr ".res" -type "string" "ntsc_4d 646 485 1.333";
connectAttr "proxy_elbow_geoShape.iog" ":initialShadingGroup.dsm" -na;
// End of elbow_proxySphereGeo.ma
