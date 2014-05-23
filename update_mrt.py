import shutil, os

sourceRootDir = '/Users/himanishbhattacharya/Documents/hbgitworks/mrt/'
targetRootDir = '/Users/himanishbhattacharya/Library/Preferences/Autodesk/maya/2014-x64/scripts/'

if os.path.exists(targetRootDir+'MRTstartup.pyc'):
		os.remove(targetRootDir+'MRTstartup.pyc')
		print "mrt_startup.pyc removed."
		
copy_list = {'mrt_controlRig_src.py': 'MRT/',
			'mrt_functions.py': 'MRT/',
			'mrt_module.py': 'MRT/',
			'mrt_objects.py': 'MRT/',
			'mrt_sceneCallbacks.py': 'MRT/',
			'mrt_UI.py': 'MRT/',
			'MRT.mel':'',
			'MRTstartup.py':'',
			'plugin/mrt_xhandleShape.h': 'MRT/',
			'plugin/mrt_xhandleShape.cpp': 'MRT/',
			'plugin/mrt_xhandleShapePlugin.cpp': 'MRT/'
			}
			
for srct, trgt in copy_list.items():
	out_f = targetRootDir + trgt + srct
	
	if os.path.exists(out_f):
		os.remove(out_f)
	
	in_f = sourceRootDir + srct
	
	if os.path.exists(in_f):
		shutil.copy(in_f, out_f)
		print "Copied: %s" % (trgt + srct)
	