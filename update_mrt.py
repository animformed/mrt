import shutil, os, platform

os_name = platform.system()

if os_name == 'Darwin':
    sourceRootDir = '/Users/hbhattacharya/Documents/github/mrt/main/MRT/'
    targetRootDir = '/Users/hbhattacharya/Library/Preferences/Autodesk/maya/2014-x64/scripts/MRT/'
if os_name == 'Windows':
    sourceRootDir = 'C:/Users/HBhattacharya/Documents/github/mrt/main/MRT/'
    targetRootDir = 'C:/Users/HBhattacharya/Documents/maya/2014-x64/scripts/MRT/'

if os.path.exists(targetRootDir+'MRTstartup.pyc'):
        os.remove(targetRootDir+'MRTstartup.pyc')
        print "mrt_startup.pyc removed."
        
copy_list = ['__init__.py',
            'mrt_controlRig_src.py',
            'mrt_functions.py',
            'mrt_module.py',
            'mrt_objects.py',
            'mrt_UI.py',
            'bone_proxyGeo.ma',
            'elbow_proxyCubeGeo.ma',
            'elbow_proxySphereGeo.ma',
            'bone_proxyGeo.ma',
            '../MRT.mel',
            '../MRTstartup.py',
            'plugin/src/xhandleNode.h',
            'plugin/src/xhandleNode.cpp',
            'plugin/src/xhandleNodePlugin.cpp',
            'plugin/builds/mac/mrt_xhandleShape_m2014x64.bundle',
            'plugin/builds/mac/mrt_xhandleShape_m2015x64.bundle',
            'plugin/builds/windows/mrt_xhandleShape_m2014x64.mll',
            'plugin/builds/windows/mrt_xhandleShape_m2015x64.mll']
            
for item in copy_list:
    out_f = targetRootDir + item
    
    if os.path.exists(out_f):
        os.remove(out_f)
    
    in_f = sourceRootDir + item
    
    if os.path.exists(in_f):
        shutil.copy(in_f, out_f)
        print "Copied: %s" % (in_f)
    else:
        print "Not found: ", in_f
    