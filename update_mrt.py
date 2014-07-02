import shutil, os, platform

os_name = platform.system()

if os_name == 'Darwin':
    sourceRootDir = '/Users/hbhattacharya/Documents/hbgitworks/mrt/'
    targetRootDir = '/Users/hbhattacharya/Library/Preferences/Autodesk/maya/2014-x64/scripts/'
if os_name == 'Windows':
    sourceRootDir = 'C:/Users/HBhattacharya/Documents/GitHub/mrt/'
    targetRootDir = 'C:/Users/HBhattacharya/Documents/maya/2014-x64/scripts/'

if os.path.exists(targetRootDir+'MRTstartup.pyc'):
        os.remove(targetRootDir+'MRTstartup.pyc')
        print "mrt_startup.pyc removed."
        
copy_list = {'__init__.py': 'MRT/',
            'mrt_controlRig_src.py': 'MRT/',
            'mrt_functions.py': 'MRT/',
            'mrt_module.py': 'MRT/',
            'mrt_objects.py': 'MRT/',
            'mrt_sceneCallbacks.py': 'MRT/',
            'mrt_UI.py': 'MRT/',
            'MRT.mel':'',
            'MRTstartup.py':'',
            'plugin/src/xhandleNode.h': 'MRT/',
            'plugin/src/xhandleNode.cpp': 'MRT/',
            'plugin/src/xhandleNodePlugin.cpp': 'MRT/',
            'plugin/builds/mac/mrt_xhandleShape_m2014x64.bundle': 'MRT/',
            'plugin/builds/mac/mrt_xhandleShape_m2015x64.bundle': 'MRT/'
            }
            
for srct, trgt in copy_list.items():
    out_f = targetRootDir + trgt + srct
    
    if os.path.exists(out_f):
        os.remove(out_f)
    
    in_f = sourceRootDir + srct
    
    if os.path.exists(in_f):
        shutil.copy(in_f, out_f)
        print "Copied: %s" % (trgt + srct)
    else:
        print "Not found: ", in_f
    