# *************************************************************************************************************
#
#    mrt_functions.py - Source for all utility / scene / runtime functions. 
#                       Also includes startup functions to verify MRT is correctly installed and supported.
#
#    Feel free to modify or copy for your own purpose :)
#
#    Written by Himanish Bhattacharya.
#
# *************************************************************************************************************

import maya.cmds as cmds
import maya.mel as mel
from pymel.core import melGlobals
from pymel.core.datatypes import Point

from maya.OpenMaya import MGlobal; Error = MGlobal.displayError; Warning = MGlobal.displayWarning

from functools import partial    # Alternative "from pymel.core.windows import Callback"
import os, math, sys, re, glob, shutil, platform

melGlobals.initVar('int[]', '_mrt_utilJobList') # To store utility script jobs (eg., for module mirroring).

os_name = platform.uname()[0]  # Get the OS type

# -------------------------------------------------------------------------------------------------------------
#
#   STARTUP FUNCTIONS
#
# -------------------------------------------------------------------------------------------------------------

def prep_MRTMayaStartupActions():
    '''
    Executed as startup utility function to check if MRT is correctly configured with maya startup.
    It checks for maya.env and the valid userSetup file in maya scripts directory. 

    It adds necessary string values / variables to the maya userSetup file if it doesn't exist.

    It also modifies the "MAYA_PLUG_IN_PATH" variable. It appends necessary string value to it if it
    exists.
    '''
    # Get the current userSetup.* file path with the extension.
    userSetup_return = find_userSetupFileStatus()
    userSetupStatus = False     # If userSetup is written or modified, set it to True. 

    # Open the userSetup file and check if the string value exists and write if needed.
    if userSetup_return.endswith('mel'):
        userSetupFile = open(userSetup_return, 'r')
        startString = '//MRT_STARTUP//'
        commandString = '\npython("try:\\n\\timport MRT.mrt_functions as mfunc\\nexcept ImportError:\\n\\tpass\\nelse:\\n\\tmfunc.runDeferredFunction_wrapper(mfunc.moduleUtilitySwitchScriptJobs)\\n");'

        stringList = [string.strip() for string in userSetupFile.readlines()]
        userSetupFile.close()
        
        for string in stringList:
            if startString in string:
                break
        else:
            stringList.extend([startString, commandString])
            userSetupFile = open(userSetup_return, 'w')
            userSetupFile.writelines(stringList)
            userSetupStatus = True
            userSetupFile.close()

    if userSetup_return.endswith('py'):
        userSetupFile = open(userSetup_return, 'r')
        startString = '#MRT_STARTUP#'
        commandString = '\ntry:\n\timport MRT.mrt_functions as mfunc\nexcept ImportError:\n\tpass\nelse:\n\tmfunc.runDeferredFunction_wrapper(mfunc.moduleUtilitySwitchScriptJobs)\n'

        stringList = [string.strip() for string in userSetupFile.readlines()]
        userSetupFile.close()
        
        for string in stringList:
            if startString in string:
                break
        else:
            stringList.extend([startString, commandString])
            userSetupFile = open(userSetup_return, 'w')
            userSetupFile.writelines(stringList)
            userSetupStatus = True
            userSetupFile.close()

    # If not userSetup file, create a default with "mel" extension.
    if userSetup_return.endswith('scripts/'):
        userSetupFile = open(userSetup_return+'userSetup.mel', 'w')
        userSetupFile.write('//MRT_STARTUP//\npython("try:\\n\\timport MRT.mrt_functions as mfunc\\nexcept ImportError:\\n\\tpass\\nelse:\\n\\tmfunc.runDeferredFunction_wrapper(mfunc.moduleUtilitySwitchScriptJobs)\\n");')

        userSetupStatus = True

        userSetupFile.close()


    # Check for maya.env status, and then modify it later.

    mayaEnv_return = returnEnvPluginPathStatus()
    mayaEnvStatus = False    # If maya.env is to be written or modified, set it to True.

    # Store the string value to be added to "MAYA_PLUG_IN_PATH".
    envString = cmds.internalVar(userScriptDir=True) + 'MRT/plugin/'

    # Get the os separator string for env paths.
    if os_name == 'Windows':
        pathSeparator = ';'
    if os_name == 'Linux' or os_name == 'Darwin':
        pathSeparator = ':'

    # If "MAYA_PLUG_IN_PATH" variable exists, split its existing string value into individual paths
    if mayaEnv_return:

        # Split the path strings
        searchPattern = '[ ]*%s[ ]*' % (pathSeparator)
        pathList = re.split(searchPattern, mayaEnv_return)

        # If the plug-in path to be added if found in the current string value, skip writing.
        for path in pathList:
            if re.match(envString, path):
                break
        else:
            pathList.append(envString)        # Append to current string value
            pathList = filter(lambda item:len(item), pathList)
            
            # New "MAYA_PLUG_IN_PATH" value to be written.
            writeString = 'MAYA_PLUG_IN_PATH = ' + pathSeparator.join(pathList) + pathSeparator + '\n'
            mayaEnvStatus = True

    if not mayaEnv_return:        # '' or None
        writeString = 'MAYA_PLUG_IN_PATH = %s%s\n' % (envString, pathSeparator)
        mayaEnvStatus = True

    if mayaEnvStatus:

        # Write the new maya env file, and rename it with the original one.
        tempEnvPath = str(cmds.internalVar(userScriptDir=True)).rpartition('scripts/')[0] + 'temp__Maya.$env'
        envPath = str(cmds.internalVar(userScriptDir=True)).rpartition('scripts/')[0] + 'Maya.env'

        if mayaEnv_return or mayaEnv_return == '':

            tempEnvFile = open(tempEnvPath, 'w')
            envFile = open(envPath, 'r')

            for line in envFile:
                if re.search('MAYA_PLUG_IN_PATH[ ]*=[ ]*', line):
                    tempEnvFile.write(writeString)
                else:
                    tempEnvFile.write(line)

            tempEnvFile.close()
            envFile.close()

            os.remove(envPath)
            os.rename(tempEnvPath, envPath) 

        # If maya.env doesn't exist, create one and write to it.
        if mayaEnv_return == None:

            envFile = open(envPath, 'a')
            envFile.write(writeString)
            envFile.close()
            
    return userSetupStatus, mayaEnvStatus


def returnEnvPluginPathStatus():
    '''
    Checks and returns the plugin path for the 'MAYA_PLUG_IN_PATH' string value in the maya.env file. 
    Can be modified to work with os.getenv('MAYA_PLUG_IN_PATH') as well.
    '''
    envPath = str(cmds.internalVar(userScriptDir=True)).rpartition('scripts/')[0] + 'Maya.env'
    envSettings = open(envPath)

    plugPaths = ''

    for line in envSettings:

        if re.search('MAYA_PLUG_IN_PATH[ ]*=[ ]*', line) and re.split('[ ]*MAYA_PLUG_IN_PATH', line.strip())[0] != '//':

            paths = re.split('MAYA_PLUG_IN_PATH[ ]*=[ ]*', line.strip())[-1]

            if paths:
                plugPaths = paths

            break;
    else:
        plugPaths = None
        
    envSettings.close()

    return plugPaths


def prep_MRTcontrolRig_source():
    '''
    Executed at startup to combine the .py sources under "userControlClasses" with "mrt_controlRig_src.py"
    as "mrt_controlRig.py", which is then imported and used.
    '''
    # Remove any existing sources.
    cleanup_MRT_actions()

    # Path to custom control classes.
    path = cmds.internalVar(userScriptDir=True) + 'MRT/userControlClasses/'
    
    if os.path.exists(path):
    
        # Get a list of all user custom control class files.
        f_list = set([item for item in os.listdir(path) if re.match('^controlClass_\w+.py$', item)])
    
    else:
        f_list = []

    tmp_coll_f = None

    # Collect all the content of user custom control class files.
    if f_list:
        tmp_coll_f = open(path+'cc_tmp_collect', 'w+')
        for item in f_list:
            file_c = open(path+item)
            for line in file_c:
                tmp_coll_f.write(line)
            tmp_coll_f.write('\n'*2)
            file_c.close()
        tmp_coll_f.close()

    # Create a new "mrt_controlRig.py" and write to it.

    m_path = path.rpartition('userControlClasses/')[0] + 'mrt_controlRig_src.py'
    m_file = open(m_path, 'r')

    f_path = path.rpartition('userControlClasses/')[0] + 'mrt_controlRig.py'
    f_file = open(f_path, 'w')

    for line in m_file:
        f_file.write(line)

    f_file.write('\n\n')

    # Now append content from user custom control class files.
    if tmp_coll_f:

        tmp_coll_f = open(path+'cc_tmp_collect', 'r')
        tmp_coll_f.seek(0)

        for line in tmp_coll_f:
            f_file.write(line)     

        tmp_coll_f.close()

        os.remove(path+'cc_tmp_collect')

    m_file.close()
    f_file.close()


def find_userSetupFileStatus():
    '''
    Checks if a 'userSetup' file exists under the user script directory.
    If found, return its full path name with its extension.
    If only 'mel' or 'py' is found, return it. If both, return 'mel'.
    '''
    scriptDir = cmds.internalVar(userScriptDir=True)
    userSetupFiles = glob.glob(scriptDir + 'userSetup.*')

    valid_userSetupFiles = []

    if len(userSetupFiles) > 0:

        for file in userSetupFiles:

            filename = re.split(r'\/|\\', file)[-1]    # Get the file name in the path

            filenameExtension = filename.rpartition('.')[2]
            filenameExtension = filenameExtension.lower()

            if len(filenameExtension) == 2 and filenameExtension == 'py':
                valid_userSetupFiles.append(file)

            if len(filenameExtension) == 3 and filenameExtension == 'mel':
                valid_userSetupFiles.append(file)

    if len(valid_userSetupFiles):

        if len(valid_userSetupFiles) == 1:

            if valid_userSetupFiles[0].endswith('mel'):
                return os.path.join(scriptDir, 'userSetup.mel')

            if valid_userSetupFiles[0].endswith('py'):
                return os.path.join(scriptDir, 'userSetup.py')

        if len(valid_userSetupFiles) > 1:
            return os.path.join(scriptDir, 'userSetup.mel')

    return scriptDir


# -------------------------------------------------------------------------------------------------------------
#
#   UTILITY FUNCTIONS
#
# -------------------------------------------------------------------------------------------------------------

def runProgressWindow(title='', message='', progress=0, step=0, totalProgress=100, init=False, end=False):
    '''
    Helper function which creates/updates the progress window with messages and progress.
    '''
    # Store the progress window message for re-use, if no new message is passed-in.
    if not cmds.optionVar(exists='rProgressWindowMsg'):
        cmds.optionVar(stringValue=('rProgressWindowMsg', message))

    if not message:
        message = cmds.optionVar(query='rProgressWindowMsg')
    else:
        cmds.optionVar(stringValue=('rProgressWindowMsg', message))

    # If the progress window is to be continued, update the message and the progress as necessary.
    if (init + end) == 0:
        cmds.text('__mrt_progressWindow_status', edit=True, label=message)
        if progress:
            cmds.progressBar('__mrt_progressWindow_bar', edit=True, progress=progress)
        if step:
            cmds.progressBar('__mrt_progressWindow_bar', edit=True, step=step)
        
    # Create or end the progress window, based on the parameters.
    if (init + end) == 1:
        if init:
            try: cmds.deleteUI('__mrt_progressWindow')
            except: pass
            cmds.window('__mrt_progressWindow', title=title, widthHeight=(300, 100), maximizeButton=False, sizeable=False)
            cmds.formLayout('__mrt_progressWindow_form', numberOfDivisions=100)
            cmds.text('__mrt_progressWindow_status', label=message)
            cmds.progressBar('__mrt_progressWindow_bar', width=150, height=20, progress=0, maxValue=totalProgress)
            cmds.formLayout('__mrt_progressWindow_form', edit=True, attachForm=(['__mrt_progressWindow_status', 'top', 15], 
                                                                                ['__mrt_progressWindow_status', 'left', 5],
                                                                                ['__mrt_progressWindow_status', 'right', 5],
                                                                                ['__mrt_progressWindow_bar', 'bottom', 20],
                                                                                ['__mrt_progressWindow_bar', 'left', 20],
                                                                                ['__mrt_progressWindow_bar', 'right', 20]))
            cmds.showWindow('__mrt_progressWindow')
            
        if end:
            try: cmds.deleteUI('__mrt_progressWindow')
            except: pass
            
            
def cleanup_MRT_actions(jobNum=None):
    '''
    Cleans up any temporary .py or .pyc during startup or scene use.
    Modify as necessary.
    '''
    path = cmds.internalVar(userScriptDir=True) + 'MRT/'

    # Clean up 'mrt_controlRig.py'. This file is an aggregate of 'mrt_controlRig_src.py' 
    # and all under the directory MRT/userControlClasses.
    if os.path.exists(path+'mrt_controlRig.py'):
        os.remove(path+'mrt_controlRig.py')
    if os.path.exists(path+'mrt_controlRig.pyc'):
        os.remove(path+'mrt_controlRig.pyc')

    # If a scriptJob is passed in, kill it as well.
    if jobNum:
        cmds.scriptJob(kill=jobNum)


def stripMRTNamespace(moduleName):
    '''
    Separates an input string name if it has a namespace defined by MRT.
    It returns the namespace and the object name.
    '''
    if re.match('^MRT_\D+__\w+:\w+$', moduleName):
        namespaceInfo = str(moduleName).partition(':')

        return namespaceInfo[0], namespaceInfo[2]

    return None


def returnMRT_Namespaces():
    '''
    Returns all current namespaces in the scene defined by MRT.
    '''
    # Get the current namespace, set the namespace to root.
    currentNamespace = cmds.namespaceInfo(currentNamespace=True)
    cmds.namespace(setNamespace=':')
    
    sceneNamespaces = cmds.namespaceInfo(listOnlyNamespaces=True)
    
    MRT_namespaces = []

    for name in sceneNamespaces:
        if re.match('^MRT_\D+__\w+$', name):
            MRT_namespaces.append(str(name))
            
    # Restore the current namespace.
    cmds.namespace(setNamespace=currentNamespace)
    
    if not MRT_namespaces:
        MRT_namespaces = None 
    
    return MRT_namespaces


def validateSceneModules():
    '''
    Checks all scene modules for an older module type. These module(s) if found,
    are incompatible with the latest version of MRT. Returns False if such module is found.
    Returns True in every other case, even with no modules. Modify as necesary.
    '''
    # Get the current namespace, set the namespace to root.
    currentNamespace = cmds.namespaceInfo(currentNamespace=True)
    cmds.namespace(setNamespace=':')
    
    modules = returnMRT_Namespaces() or []
    
    olderModules = []
    
    # Check if any module group doesn't have the 'moduleLength' attribute.
    for module in modules:
        moduleGrp = '%s:moduleGrp' % module
        
        if not cmds.objExists(moduleGrp+'.moduleLength'):
            olderModules.append(module)

    if olderModules:
        Error('MRT: Incompatible, %s module type(s) found in the scene.\n%s' % (len(olderModules), '\n'.join(olderModules)))
    
    # Restore the current namespace.
    cmds.namespace(setNamespace=currentNamespace)    

    return olderModules


def findHighestNumSuffix(baseName, names):
    '''
    Find and return the max numerical suffix value separated by underscore(s) for a given string name.
    '''
    highestValue = 1

    for name in names:

        if re.match('^%s_*\d+$' % baseName, name):
            suffix = re.split('_*', name)[-1]
            numSuffix = int(suffix)

            if numSuffix > highestValue:
                highestValue = numSuffix

    return highestValue


def findHighestCommonTextScrollListNameSuffix(baseName, names):
    '''
    Find and return the max numerical suffix in brackets (num) in textScrollList list names,
    with a common first name. This numerical suffix is added to make them unique.
    Eg:
    Name(2)
    Name(4)
    '''
    highestValue = 1    # Start with base value for the num suffix
    
    for name in names:
    
        # If a num suffix is found, modify the base value.
        if re.match('^%s \(\d+\)$' % baseName, name):
            suffix = name.partition('(')[2].partition(')')[0]
            numSuffix = int(suffix)
            if numSuffix > highestValue:
                highestValue = numSuffix
    
    return highestValue


def returnModuleUserSpecNames(namespaces):
    '''
    Returns a tuple of two lists for a given list of namespaces. 

    A module's namespace has two parts,    one defined by MRT and the other defined by the user, 
    separated by an "__". The first list contains substrings for the namespaces defined by MRT 
    and the second list containing substring names defined by user,for the passed-in namespaces.
    '''
    userSpecifiedNames = []
    strippedNamespaces = []

    for namespace in namespaces:
        userSpecifiedNames.append(namespace.rpartition('__')[2])
        strippedNamespaces.append(namespace.rpartition('__')[0])

    return strippedNamespaces, userSpecifiedNames


def returnVectorMagnitude(transform_start, transform_end):
    '''
    Calculates and returns the magnitude for the input vector, with the arguments for
    start position for input vector and the end position for input vector.
    '''
    transform_vector = map(lambda x,y: x-y, transform_start, transform_end)  # transform_start -> transform_end
    transform_vector_magnitude = math.sqrt(reduce(lambda x,y: x+y, [component**2 for component in transform_vector]))

    return transform_vector_magnitude

    
def compareTransformPairOrientation(transform1, transform2):
    '''
    Compares two input maya transforms for their orientation, by calculating the dot products
    of each of their respective local axes.
    
    For eg., two if two transforms T1 and T2 and passed-in, the function may return as follows:
    
    directions = {'X': 1,   <means that the X axes for T1 and T2 are parallel>
                  'Y': -1,  <means that the Y axes for T1 and T2 are parallel, but opposite in directions,
                  'Z': -1}  <so on>
    '''
    
    # Create two temporary transform groups for representing transform1 and transform2.
    # Each group will have the base transform as the input transform and a child transform to
    # be used as a direction vector.
    
    transform1Pos = cmds.createNode('transform', skipSelect=True)
    align(transform1, transform1Pos)
    transform1Dir = cmds.createNode('transform', p=transform1Pos, skipSelect=True)
    transform1PosValue = cmds.xform(transform1, query=True, worldSpace=True, translation=True)
    
    transform2Pos = cmds.createNode('transform', skipSelect=True)
    align(transform2, transform2Pos)
    transform2Dir = cmds.createNode('transform', p=transform2Pos, skipSelect=True)
    transform2PosValue = cmds.xform(transform2, query=True, worldSpace=True, translation=True)
    
    directions = {}
    
    # Set the direction vector for each of the temporary transform groups, 
    # and calculate their dot alignment, and store it. This is done to check the local axes
    # for each of the input transforms.
    for axis, value in zip(('X', 'Y', 'Z'), ((1,0,0), (0,1,0), (0,0,1))):
    
        cmds.setAttr(transform1Dir+'.translate', *value, type='double3')
        transform1DirValue = cmds.xform(transform1Dir, query=True, worldSpace=True, translation=True)
        cmds.setAttr(transform2Dir+'.translate', *value, type='double3')
        transform2DirValue = cmds.xform(transform2Dir, query=True, worldSpace=True, translation=True)
        
        dir_cosine = returnDotProductDirection(transform1PosValue, transform1DirValue,
                                               transform2PosValue, transform2DirValue)[0]
        
        directions[axis] = dir_cosine
    
    cmds.delete(transform1Pos, transform2Pos)

    return directions
    
    
def returnCrossProductDirection(transform1_start, transform1_end, transform2_start, transform2_end, normalize=False):
    '''
    Calculates and returns the cross-product data for two input vectors. It has arguments for,
    transform1_start -> Start position for vector 1.
    transform1_end -> End position for vector 1.
    transform2_start -> Start position for vector 2.
    transform2_end -> End position for vector 2.
    normalize -> Normalize the input vectors to unit vectors.

    It returns a tuple (the sine value between two input vectors <float>, 
                        cross product vector <list(3) with floats>, 
                        magnitude of cross product vector <float>)
    '''
    # transform1_start -> transform1_end
    transform1_vector = t1_v = map(lambda x,y: x-y, transform1_start, transform1_end)
    # transform2_start -> transform2_end
    transform2_vector = t2_v = map(lambda x,y: x-y, transform2_start, transform2_end)

    transform1_vector_magnitude = math.sqrt(reduce(lambda x,y: x+y, [component**2 for component in transform1_vector]))
    transform2_vector_magnitude = math.sqrt(reduce(lambda x,y: x+y, [component**2 for component in transform2_vector]))   

    if normalize:
        transform1_vector = t1_v  = [item/transform1_vector_magnitude for item in transform1_vector]
        transform2_vector = t2_v = [item/transform2_vector_magnitude for item in transform2_vector]
        transform1_vector_magnitude = transform2_vector_magnitude = 1.0

    cross_product_vector = [(t1_v[1]*t2_v[2] - t1_v[2]*t2_v[1]) , \
                            (t1_v[2]*t2_v[0] - t1_v[0]*t2_v[2]) , \
                            (t1_v[0]*t2_v[1] - t1_v[1]*t2_v[0])]

    cross_product_vector_magnitude = \
    math.sqrt(reduce(lambda x,y: x+y, [component**2 for component in cross_product_vector]))

    theta_sine = cross_product_vector_magnitude / (transform1_vector_magnitude * transform2_vector_magnitude)

    return theta_sine, cross_product_vector, cross_product_vector_magnitude


def returnDotProductDirection(transform1_start, transform1_end, transform2_start, transform2_end, normalize=False):
    '''
    Calculates and returns the dot-product direction for two input vectors. It has arguments for,
    transform1_start -> Start position for vector 1.
    transform1_end -> End position for vector 1.
    transform2_start -> Start position for vector 2.
    transform2_end -> End position for vector 2.
    normalize -> Normalize the input vectors to unit vectors.

    It returns a tuple (the cosine value between two input vectors <float>, magnitude of dot product vector <float>)
    '''
    # transform1_start -> transform1_end
    transform1_vector = map(lambda x,y: x-y, transform1_start, transform1_end)
    # transform2_start -> transform2_end
    transform2_vector = map(lambda x,y: x-y, transform2_start, transform2_end)

    transform1_vector_magnitude = math.sqrt(reduce(lambda x,y: x+y, [component**2 for component in transform1_vector]))
    transform2_vector_magnitude = math.sqrt(reduce(lambda x,y: x+y, [component**2 for component in transform2_vector]))

    if normalize:
        transform1_vector = [item/transform1_vector_magnitude for item in transform1_vector]
        transform2_vector = [item/transform2_vector_magnitude for item in transform2_vector]
        transform1_vector_magnitude = transform2_vector_magnitude = 1.0  

    # transform1_transform2_dot_magnitude = \
    #                reduce(lambda x,y: x+y, map(lambda x,y: x*y, transform1_vector, transform2_vector))
    transform1_transform2_dot_magnitude = sum(x*y for x,y in zip(transform1_vector, transform2_vector))

    direction_cosine = transform1_transform2_dot_magnitude / (transform1_vector_magnitude*transform2_vector_magnitude)

    return direction_cosine, transform1_transform2_dot_magnitude


def returnOffsetPositionBetweenTwoVectors(startVector, endVector, parameter=0):
    '''
    Calculates and returns a new position with respect to two input vector positions, based on the parameter value.
    It has the following arguments:
    startVector -> Vector position 1.
    endVector -> Vector position 2.
    parameter -> If parameter is 0.5, the function returns the mid position between the two input vectors. 
                 If the parameter is 0, the function returns the position of the first input vector, and so on.
    It returns a vector, <list(3) with floats>
    '''
    direction_vec = map(lambda x,y:x-y, endVector, startVector)

    # Calculate the offset vector on the line represented by the two input vectors.
    off_vec = map(lambda x,y:x+(y*parameter), startVector, direction_vec)

    return off_vec


def comparePositionsForVectors(*args, **kwargs):
    '''
    Returns boolean if an array of positions are equivalent or 
    occupy the same position within tolerance.
    '''
    tolerance = kwargs['tolerance'] if 'tolerance' in kwargs else 0.01
    isEquivalent = False
    
    try:
        if len(args) > 1:
            mainPos = Point(args[0])
            
            for pos in args[1:]:
                pos = Point(pos)
                isEquivalent = mainPos.isEquivalent(pos, tol=tolerance)
        
    except TypeError, NameError:
        return False
    
    return isEquivalent
    
    
def returnModuleTypeFromNamespace(namespace):
    '''
    Return the type of a module from it namespace.
    Eg., "MRT_HingeNode__module1:" will return "HingeNode" 
    '''
    firstPart = namespace.partition('__')[0]
    moduleType = firstPart.partition('_')[2]

    return moduleType


def loadXhandleShapePlugin():
    '''
    Checks and loads the xHandleShape plugin. It finds the correct plugin from the built versions for the 
    current session of maya and os if supported and makes a copy to the plug-in search path.

    It returns a bool if it successfully loads the plugin.

    To be modified for future updates and add mac support ?
    '''
    maya_ver = returnMayaVersion()

    pluginBasePath = cmds.internalVar(userScriptDir=True) + 'MRT/plugin/'

    # Find the correct plugin built version.
    if os_name == 'Windows':
        plugin_source_path = pluginBasePath + '/builds/windows/mrt_xhandleShape_m%sx64.mll'%(maya_ver)
        plugin_dest_path = pluginBasePath + 'mrt_xhandleShape.mll'

    elif os_name == 'Linux':
        plugin_source_path = pluginBasePath + '/builds/linux/mrt_xhandleShape_m%sx64.so'%(maya_ver)
        plugin_dest_path = pluginBasePath + 'mrt_xhandleShape.so'

    elif os_name == 'Darwin':
        plugin_source_path = pluginBasePath + '/builds/mac/mrt_xhandleShape_m%sx64.bundle'%(maya_ver)
        plugin_dest_path = pluginBasePath + 'mrt_xhandleShape.bundle'

    else:
        Error('MRT is not supported on \"'+os_name+'\" platform. Aborting.')
        return False

    # Copy to plugin path and then load it.
    try:
        if not cmds.pluginInfo(plugin_dest_path, query=True, loaded=True):
            shutil.copy2(plugin_source_path, plugin_dest_path)

    except IOError:
        Warning('MRT cannot access path "%s" for writing. Skipping plugin update.' % plugin_dest_path)

    finally:
        try:
            cmds.loadPlugin(plugin_dest_path, quiet=True)
        except:
            Error('MRT: Unable to load plugin "%s". Aborting.' % plugin_dest_path)
            return False

    return True


def selection_sort_by_length(list_sequence):
    '''
    Sorts a given sequence list (list of lists) by their length. In place sort.
    '''
    for i in xrange(0, len(list_sequence)):
        min_index = i
        for j in xrange(i+1, len(list_sequence)):
            if len(list_sequence[min_index]) > len(list_sequence[j]):
                min_index = j
        list_sequence[i] = list_sequence[min_index]
        list_sequence[min_index] = list_sequence[i]
        
        
def capitalize(string):
    '''
    Alternative for str.capitalize, since it doesn't always work as expected.
    '''
    if len(string) > 1:
        return string[0].upper() + string[1:]
    else:
        return string[0].upper()


def runDeferredFunction_wrapper(function):
    '''
    Execute a given function during CPU idle time.
    '''
    # DEPRECATED #
    # global _eval__Function
    # _eval__Function = function
    # global _eval__Return
    # cmds.evalDeferred("mrt_sceneUtils._eval__Return = mrt_sceneUtils._eval__Function()", lowestPriority=True)
    import maya.utils
    maya.utils.executeDeferred(function)


def findLastSubClassForSuperClass(cls):
    '''
    Find the leaf child subclass for a given class. Used by the control
    rig class hierarchy.
    '''
    klasses = cls.__subclasses__()
    
    if not klasses:
        subClass = cls

    if klasses:
        subClass = findLastSubClassForSuperClass(klasses[0])

    return subClass


def returnValidSelectionFlagForModuleTransformObjects(selection):
    '''
    Checks a selection for a valid module object created by MRT.
    '''
    matchObjects = [re.compile('^MRT_\D+__\w+:module_transform$'),
                    re.compile('^MRT_\D+__\w+:root_node_transform$'),
                    re.compile('^MRT_\D+__\w+:end_node_transform$'),
                    re.compile('^MRT_\D+__\w+:node_\d+_transform$'),
                    re.compile('^MRT_\D+__\w+:spline_\d+_adjustCurve_transform$'),
                    re.compile('^MRT_\D+__\w+:splineStartHandleTransform$'),
                    re.compile('^MRT_\D+__\w+:splineEndHandleTransform$'),
                    re.compile('^MRT_\D+__\w+:root_node_transform_control$'),
                    re.compile('^MRT_\D+__\w+:end_node_transform_control$'),
                    re.compile('^MRT_\D+__\w+:node_1_transform_control$'),
                    re.compile('^MRT_\D+__\w+:single_orient_repr_transform$'),
                    re.compile('^MRT_\D+__\w+:[_0-9a-z]*transform_orient_repr_transform$')]

    for matchObject in matchObjects:

        matchResult = matchObject.match(selection)

        if matchResult:
            return True

    return False


def concatenateCommonNamesFromHierarchyData(data, commonNames=[]):
    '''
    This function works upon the hierarchy data returned by traverseParentModules() or traverseChildrenModules().
    It collects all object names uniquely in a mutable sequence (list) passed-in as an argument. 
    '''
    if type(data) == dict:
        for item in data:
            if not item in commonNames:
                commonNames += [item]
            if isinstance(data[item], dict):
                commonNames = concatenateCommonNamesFromHierarchyData(data[item], commonNames)

    if type(data) == list:
        for item in data:
            if isinstance(item, list):
                commonNames = concatenateCommonNamesFromHierarchyData(item, commonNames)
            else:
                if not item in commonNames:
                    commonNames += [item]
    return commonNames


def cmpCustomHierarchyStructureStrings(clsAttrString='', hierarchyString=''):
    """
    Compares two string values, one from the "customHierarchy" string attribute of a control rig class,
    and another from the string return value from "returnHierarchyTreeListStringForCustomControlRigging()",
    to see if they match. This comparison is used to validate if a custom joint hierarchy in character
    can be used with methods for a given control rig class.
    
    For eg., a "customHierarchy" value can be,

    customHierarchy = \
    '''
    <HingeNode>_root_node_joint   
        <HingeNode>_node_1_joint  
            <HingeNode>_end_node_joint  
                <JointNode>_root_node_joint  
                <JointNode>_root_node_joint  
                    <JointNode>_end_node_joint 
                        
    '''
    Here, the "customHierarchy" value is passed-in under "clsAttrString".
    
    "hierarchyString" can be,
    
    '\n<HingeNode>_root_node_joint\n<HingeNode>_node_1_joint\n    <HingeNode>_end_node_joint\n        <JointNode>_root_node_joint\n        <JointNode>_root_node_joint\n            <JointNode>_end_node_joint\n'
    
    which is returned from "returnHierarchyTreeListStringForCustomControlRigging()" and passed-in.
    
    This function is needed since direct string comparision is not correct for all situations. 
    A user may append extra spaces after each joint name in a line under the "customHierarchy", 
    and hence this has to be taken into account.
    
    """
    # Break the individual strings as lists as per newlines, so each joint name occurs 
    # as individual string items in the lists.
    clsAttrString_items = [i for i in re.split('[ ]*\n', clsAttrString) if len(i.strip())]
    hierarchyString_items = [i for i in re.split('[ ]*\n', hierarchyString) if len(i.strip())]
    
    # For "clsAttrString_items", find the common preceding space value and remove them from items.
    paddings = [re.findall('^[ ]*', i)[0] for i in clsAttrString_items]
    clsAttrString_items = [re.sub('^%s' % min(paddings), '', i) for i in clsAttrString_items]
    
    # Check if the lists are of same length, or if they have same number of joints in their descriptions.
    if len(clsAttrString_items) == len(hierarchyString_items):
        
        # If each item matches,
        for str1, str2 in zip(clsAttrString_items, hierarchyString_items):
            if str1 != str2:
                return False
    else:
        return False

    return True
                

# -------------------------------------------------------------------------------------------------------------
#
#   SCENE FUNCTIONS
#
# -------------------------------------------------------------------------------------------------------------

def applyConstraint(*args, **kwargs):
    '''
    Common wrapper function for maya constraints. It names the constraint node
    by looking at the input/output connected nodes without providing a name value.
    
    Accepts a 'constraintType' keyword argument to specify the maya constraint type.
    eg., point, parent, etc.
    '''
    if not 'constraintType' in kwargs:
        cmds.error('No constraint type specified for applyConstraint().')
    
    constraintType = kwargs['constraintType']
    kwargs.pop('constraintType')
    
    if len(args) < 2:
        cmds.error('Check node inputs for applyConstraint().')
    
    # Get the target transform and the object transform(s) from args.
    targetNode = args[-1]
    objectNodes = args[:-1]
    
    # Look for a namespace in the target transform.
    targetNamespaceTokens = [i for i in targetNode.split(':') if i]
    namespace = ':'.join(targetNamespaceTokens[:-1]) if len(targetNamespaceTokens) > 1 else ''
    targetNodeName = targetNamespaceTokens[-1]

    targetStringTokens = [i for i in targetNodeName.split('_') if i]
    targetStringTokens = targetStringTokens[:-1] if len(targetStringTokens) > 1 else targetStringTokens
    
    targetString = ''.join([capitalize(i) for i in targetStringTokens])
    
    objectString = ''
    for node in objectNodes:
        
        objNamespaceTokens = [i for i in node.split(':') if i]
        
        if not namespace:
            namespace = ':'.join(objNamespaceTokens[:-1]) if len(objNamespaceTokens) > 1 else ''
            
        objNodeName = objNamespaceTokens[-1]
        objectStringTokens = [i for i in objNodeName.split('_') if i]
        objectStringTokens = objectStringTokens[:-1] if len(objectStringTokens) > 1 else objectStringTokens        

        string = ''.join([capitalize(i) for i in objectStringTokens])
        objectString += '_' + string if objectString else string
        
    if 'namespace' in kwargs:
        namespace = kwargs['namespace']
        kwargs.pop('namespace')
    
    if not 'remove' in kwargs:
        if not 'name' in kwargs:
            kwargs['name'] = '%s:%s_to_%s_%s' % (namespace, objectString, targetString, constraintType)
    
    # For debug -
    print 'applyConstraint() - \nNAME = "%s"\nTARGET = "%s"\nOBJECTS = "%s"\n' % (kwargs['name'], targetNode, objectNodes)
    
    eval('cmds.%sConstraint(*args, **kwargs)' % constraintType)
    
    if not 'remove' in kwargs:
        return kwargs['name']


# Specify the equivalent wrapper functions below for maya constraint commands, using applyConstraint().
def pointConstraint(*args, **kwargs): kwargs['constraintType']='point'; return applyConstraint(*args, **kwargs)
def parentConstraint(*args, **kwargs): kwargs['constraintType']='parent'; return applyConstraint(*args, **kwargs)
def orientConstraint(*args, **kwargs): kwargs['constraintType']='orient'; return applyConstraint(*args, **kwargs)
def scaleConstraint(*args, **kwargs): kwargs['constraintType']='scale'; return applyConstraint(*args, **kwargs)
def aimConstraint(*args, **kwargs): kwargs['constraintType']='aim'; return applyConstraint(*args, **kwargs)
def geometryConstraint(*args, **kwargs): kwargs['constraintType']='geometry'; return applyConstraint(*args, **kwargs)
def normalConstraint(*args, **kwargs): kwargs['constraintType']='normal'; return applyConstraint(*args, **kwargs)
def tangentConstraint(*args, **kwargs): kwargs['constraintType']='tangent'; return applyConstraint(*args, **kwargs)
def poleVectorConstraint(*args, **kwargs): kwargs['constraintType']='poleVector'; return applyConstraint(*args, **kwargs)


def returnHierarchyTreeListStringForCustomControlRigging(rootJoint, prefix=''):
    '''
    Returns a string value depicting the hierarchy tree list of all joints from a given root joint,
    for a given "rootJoint" of a character hierarchy.
    
    For more description, see the comments for "CustomLegControl" class in "mrt_controlRig_src.py".

    Returns string with following layout for a valid root joint:

    Each child joint is indented with a tab space.

    <HingeNode>_root_node_joint
        <HingeNode>_node_1_joint
            <HingeNode>_end_node_joint
                <JointNode>_root_node_joint
                <JointNode>_root_node_joint
                    <JointNode>_end_node_joint
    '''
    # DEPRECATED >>>>>
    # if prettyPrint:
    #    newLine = '\n'
    #    tabLine = '\t'
    # else:
    #    newLine = '\\n'
    #    tabLine = '\\t'
    # <<<<<<
    
    newLine = '\n'
    tabLine = ' ' * 4

    # Stores the string attributes for the passed-in joint name.
    jh_string = '%s<%s>%s%s' % (prefix, 
                                cmds.getAttr(rootJoint+'.inheritedNodeType'),
                                re.split('(_root_node_joint|_end_node_joint|_node_\d+_joint)', rootJoint)[1], 
                                newLine)

    # Check the joint for multiple children. If they have further descendents, search recursively and collect 
    # their joint name attributes if the passed-in joint has only a single child joint.

    children = cmds.listRelatives(rootJoint, children=True, type='joint')

    while children:

        prefix = prefix + tabLine

        if len(children) == 1:

            # Append the child joint name attributes.
            jh_string += '%s<%s>%s%s' % (prefix, 
                                         cmds.getAttr(children[0]+'.inheritedNodeType'),
                                         re.split('(_root_node_joint|_end_node_joint|_node_\d+_joint)', children[0])[1], 
                                         newLine)

            children = cmds.listRelatives(children[0], children=True, type='joint') 

        else:

            children_list = []
            allC_count_dict = {}

            for child in children:

                allChildren = cmds.listRelatives(child, allDescendents=True, type='joint') or []

                if allC_count_dict.get(len(allChildren)):
                    allC_count_dict[len(allChildren)].append(child)
                else:
                    allC_count_dict[len(allChildren)] = [child]

            if len(allC_count_dict):

                for item in sorted(allC_count_dict):
                    children_list.extend(allC_count_dict[item])

            if len(children_list):

                for child in children_list:
                    jh_string += returnHierarchyTreeListStringForCustomControlRigging(child, prefix)

                break

    return jh_string


def returnRootForCharacterHierarchy(joint):
    '''
    Returns the string name of the root joint of a joint hierarchy in a character for a given joint name, 
    which is part of the hierarchy.
    '''
    rootJoint = ''

    # The cmds version returned occasional errors stating incorrect boolean value with parent flag, if
    # this function was used in a scriptJob event call. Not sure why.
    # parentJoint = cmds.listRelatives(joint, parent=True, type='joint')  <-- What's wrong with you??

    parentJoint = mel.eval('listRelatives -parent -type joint '+joint)

    if parentJoint and parentJoint[0].endswith('_joint'):
        rootJoint = returnRootForCharacterHierarchy(parentJoint[0])
    else:
        rootJoint = joint

    return rootJoint


def returnAxesInfoForFootTransform(transform, foot_vec_dict):
    '''
    This function is used to gather data for a transform's orientation for its use 
    with a reverse IK foot/leg configuration.

    For a given transform with its orientation, return the following data:

    1) Calculate its nearest axis crossing the length of the foot
    2) Calculate its nearest axis along the aim of the foot.
    3) Calculate its nearest axis along the length of the leg.

    Also return the cosine between the nearest axis.
    '''
    # Get the vector crossing the length of the foot  
    foot_cross_vec = foot_vec_dict['cross']

    # Get the vector along the aim of the foot
    foot_aim_vec = foot_vec_dict['aim']

    # Get the position of the hip in the leg hierarchy
    hip_pos = foot_vec_dict['hip_pos']

    # Get the position of the heel in the leg hierarchy
    heel_pos = foot_vec_dict['heel_pos']

    # Get the world pos for the given transform
    transPos = cmds.xform(transform, query=True, worldSpace=True, translation=True)

    # Create a temp locator parented under the given transform
    tempLoc = cmds.spaceLocator()[0]
    cmds.parent(tempLoc, transform, relative=True) 

    cross_res = aim_res = up_res = 0    # assignment by value

    axes_info = {}

    # Iterate all the axes of the transform and find the nearest axes.
    for ax in ['X', 'Y', 'Z']:

        cmds.setAttr(tempLoc+'.translate'+ax, 1)

        locPos = cmds.xform(tempLoc, query=True, worldSpace=True, translation=True) # Can use the worldPosition as well.

        cross_result = returnDotProductDirection(transPos, locPos, heel_pos, foot_cross_vec)
        aim_result = returnDotProductDirection(transPos, locPos, heel_pos, foot_aim_vec)
        up_result = returnDotProductDirection(transPos, locPos, heel_pos, hip_pos)

        cross_direction = round(cross_result[0], 3)
        if abs(cross_direction) > cross_res:
            cross_res = abs(cross_direction)
            axes_info['cross'] = [ax, cross_direction]   

        aim_direction = round(aim_result[0], 3)
        if abs(aim_direction) > aim_res:
            aim_res = abs(aim_direction)
            axes_info['aim'] = [ax, aim_direction]

        up_direction = round(up_result[0], 3)
        if abs(up_direction) > up_res:
            up_res = abs(up_direction)
            axes_info['up'] = [ax, up_direction]

        cmds.setAttr(tempLoc+'.translate'+ax, 0)

    cmds.delete(tempLoc)

    return axes_info


def performOnIdle():
    '''
    Called during CPU idle time to perform post tasks. Can be modified to include more tasks.
    Useful in iterations.
    '''
    cmds.select(clear=True)


def moveSelectionOnIdle(selection, translation_values):
    '''
    Useful for selection and moving after a successful DG update by maya.
    '''
    cmds.select(selection, replace=True)
    cmds.move(*translation_values, relative=True, worldSpace=True)


def traverseParentModules(module_namespace):
    '''
    Returns a list and number of all parent modules from a given module.
    '''
    traverse_length = 0
    traversed_modules = []

    # If the input module has a "moduleParent" attribute.
    if cmds.attributeQuery('moduleParent', node=module_namespace+':moduleGrp', exists=True):

        # Get its value to obtain its parent module
        moduleParentNode = cmds.getAttr(module_namespace+':moduleGrp.moduleParent')

        # Then, search recursively for the parent module for more parents.
        if moduleParentNode != 'None':

            moduleParentNode = moduleParentNode.split(',')[0]
            traverse_length += 1
            moduleParentNamespace = stripMRTNamespace(moduleParentNode)[0]
            traversed_modules += [moduleParentNamespace]

            traverse_length += traverseParentModules(moduleParentNamespace)[1]
            traversed_modules += traverseParentModules(moduleParentNamespace)[0]

    return traversed_modules, traverse_length


def traverseChildrenModules(module_namespace, allChildren=False):
    '''
    Search for children modules from all nodes for a module. Also, search recursively
    for all children to return a dict structure depicting the "allChildren" hierarchy.
    '''
    childrenModules = []
    allChildrenModules = {}

    # Get a list of all node names for the given module (without namespaces).
    numNodes = cmds.getAttr(module_namespace+':moduleGrp.numberOfNodes')

    nodeNameList = ['node_%s_transform' % i for i in range(numNodes)]
    nodeNameList[0] = 'root_node_transform'

    if numNodes > 1:            # If the module consists of more than one node.
        nodeNameList[-1] = 'end_node_transform'


    # For each node in a module, check if it's connected to a child module node.

    for node in nodeNameList:

        fullNodeName = module_namespace+':'+node
        connections = cmds.listConnections(fullNodeName+'.translate', destination=True, type='constraint')

        for name in connections:

            # If a child module node is connected (a child module node is connected using constraints),
            # get its node name. If it's not a part of the passed-in module namespace, collect its namespace.

            if '|' in name:
                name = name.rpartition('|')[2]

            pat = '^%s:\w+$' % module_namespace

            if not re.match(pat, name):
                namespace = stripMRTNamespace(name)[0]
                childrenModules += [namespace]

    # If only direct children are required, return only childrenModules.
    if len(childrenModules) and not allChildren:
        return childrenModules

    # If all children are required (like allDescendents) with allChildren set to True, search recursively.
    if len(childrenModules) and allChildren:

        for childModule in childrenModules:
            allChildrenModules[childModule] = traverseChildrenModules(childModule, allChildren=True)

        return allChildrenModules

    if not len(childrenModules):
        return None


def traverseConstrainedParentHierarchiesForSkeleton(rootJoint):
    '''
    Return a list of all parents (connected using constraints) from a given root joint for 
    a joint hierarchy in a character.
    '''
    allParentRootJoints = []

    # If the passed-in root joint of a hierarchy in a character has a constrained parent, proceed.
    if cmds.attributeQuery('constrainedParent', node=rootJoint, exists=True):

        # Get the name of the constrained parent joint
        rootParent = cmds.getAttr(rootJoint+'.constrainedParent')
        jointIt = [rootParent]

        # With a joint name in the 'constraining' parent hierarchy, get the name of its root joint.
        while jointIt:
            if jointIt[0].endswith('root_node_joint'):
                rootParent = jointIt[0]        
            jointIt = cmds.listRelatives(jointIt, parent=True, type='joint')

        # Append the name of the root joint of the 'constraining' parent joint hierarchy.
        allParentRootJoints += [rootParent]

        # Recursively search for more 'constrained' parents
        allParentRootJoints += traverseConstrainedParentHierarchiesForSkeleton(rootParent)

    return allParentRootJoints


def checkForJointDuplication():
    '''
    Checks if a character joint has been manually duplicated in the scene.
    '''
    allJoints = cmds.ls(type='joint')
    
    # Get all the mrt joint names in the scene. Only the node name at the end of
    # a DAG path.
    mrt_joints = [item.split('|')[-1] for item in allJoints if \
                  cmds.attributeQuery('mrtJoint', node=item, exists=True)]
    check = True

    if mrt_joints:
    
        for joint in mrt_joints:
        
            # If the joint "node" name occurs twice in the list, warn.
            if mrt_joints.count(joint) > 1:
                Error('MRT: One of the character joints has been manually duplicated. \
                              Please undo it in order to perform control rigging.')
                check = False
                break

    return check


def returnConstraintWeightIndexForTransform(transform, constraintNode, matchAttr=False):
    '''
    Returns the weight suffix and the attribute string for a give transform driving 
    a given constraint.
    Eg., If the transform "transform2" was driving a constraint along with other transforms,
    such that the constraint weight attributes are:

    transform1W0
    transform2W1
    transform2W2

    Then this function will return a tuple of (1, transform2W1)

    You can use the matchAttr argument if the weight index name doesn't entirely match the
    name of the transform. Eg., 'transform1' was renamed as 'transform12'

    It has the following arguments:
    transform -> String name for the transform.
    constraintNode -> String name for the constraint node.
    matchAttr -> If the attribute name without the weight index (W#) doesn't match the transform name,
                perform a search if the transform name is a substring of the attribute name.

    Returns a tuple (index <int>, attributeName <str>) if successful and None if no weight attribute for the
    transform is found.
    '''
    # Get a list of all weight attributes for the given constraint node
    constraintWeightAttrs = [attr for attr in cmds.listAttr(constraintNode, keyable=True) \
                            if re.match('^\w+W\d+$', attr)]
    indexAttr = ''

    # Find the weight attribute for the given transform and then return
    for attr in constraintWeightAttrs:
        if matchAttr:
            if re.search(transform, attr):
                indexAttr = attr
                break
        else:
            if re.match('^%sW\d+$'%(transform), attr):
                indexAttr = attr
                break

    if indexAttr:
        return eval(re.split('^\w+W', indexAttr)[1]), indexAttr
    else:
        return None


def lockHideChannelAttrs(node, *attrList, **setAttrs):
    '''
    Sets the lock/channelBox/keyable state of passed-in channel attributes for a node.
    attrList - Sequence of node attributes to be set.
    setAttr - Default arguments to be used to set the states of the attributes.

    Set the following states for an attribute:
    visible - Visible in the channel box, but non-keyable.
    keyable - Keyable & visible in the channel box.
    lock - Lock the attribute.
    '''
    node = str(node)
    
    if cmds.objExists(node) and not cmds.referenceQuery(node, isNodeReferenced=True):

        # Go through the passed-in node attributes.
        for attr in attrList:

            # Get the child attribute(s) if an attribute is compound.
            for attr in cmds.attributeQuery(attr, node=node, listChildren=True) or [attr]:

                # Set the attribute states.
                if 'visible' in setAttrs:
                    cmds.setAttr('%s.%s' % (node, attr), keyable=False, channelBox=setAttrs['visible'])

                if 'keyable' in setAttrs:

                    keyable = setAttrs['keyable']

                    if keyable:
                        cmds.setAttr('%s.%s' % (node, attr), keyable=keyable)
                    else:
                        cmds.setAttr('%s.%s' % (node, attr), channelBox=keyable, keyable=keyable)

                if 'lock' in setAttrs:
                    cmds.setAttr('%s.%s' % (node, attr), lock=setAttrs['lock'])


def returnMayaVersion():
    '''
    Returns the current maya version as an integer.
    '''
    # return int(eval(mel.eval('$val = $gMayaVersionYear')))    # Alternative
    return int(eval(cmds.about(version=True)))


def addNodesToContainer(inputContainer, inputNodes, includeHierarchyBelow=False, includeShapes=False, force=False):
    '''
    Add a list of nodes to a given container name. It has the following arguments:

    inputContainer -> String name for the container.
    inputNodes -> List of string names for nodes.
    includeHierarchyBelow -> Include and append all children nodes to the node list to be added to the container.
    includeShapes -> Include and append any shapes for the transform(s) to the node list to be added to the container.
    force -> All nodes will be disconnected from their current containers, if any, and will be added to the 
             given container.

    Returns True if successful and False if otherwise.
    '''
    
    # Collect the input node(s) in a list. Make sure they exist.
    if isinstance(inputNodes, list):
        nodes = list(inputNodes)
    else:
        nodes = [inputNodes]

    containedNodes = []
    for node in nodes:
        if node and cmds.objExists(node):
            containedNodes.append(node)
    
    # Iterate through the input nodes. Find additional nodes to be added to the input container.
    dgNodes = []
    for node in containedNodes:

        # If the node is a transform or derived from, find the appropriate nodes connected in DG to be added to the container.
        if cmds.objectType(node, isAType='transform'):

            # Find all transforms under the node if "includeHierarchyBelow" is set to True.
            if includeHierarchyBelow:
                listNodes = cmds.listRelatives(node, allDescendents=True, type='transform') or []
                listNodes.append(node)
            else:
                listNodes = [node]

            # Find and add DG nodes created and connected by maya.
            for item in listNodes:
                try: 
                    if not cmds.objectType(item, isType='constraint'):

                        # Find and add all the connected unit conversion nodes.
                        unitConNodes = cmds.listConnections(item, source=True, destination=True, \
                                                        exactType=True, type='unitConversion')
                        if unitConNodes:
                            for uNode in unitConNodes:
                                if uNode not in dgNodes:
                                    dgNodes.append(uNode)

                        # Find and add all the connected set-driven key nodes. 
                        animCurveULNodes = cmds.listConnections(item, source=True, destination=True, \
                                                            exactType=True, type='animCurveUL')
                        if animCurveULNodes:
                            for ulAnim in animCurveULNodes:
                                if ulAnim not in dgNodes:
                                    dgNodes.append(ulAnim)
                        animCurveUANodes = cmds.listConnections(item, source=True, destination=True, \
                                                            exactType=True, type='animCurveUA')
                        if animCurveUANodes:
                            for uaanim in animCurveUANodes:
                                if uaanim not in dgNodes:
                                    dgNodes.append(uaanim)
                        animCurveUUNodes = cmds.listConnections(item, source=True, destination=True, \
                                                            exactType=True, type='animCurveUU')
                        if animCurveUUNodes:
                            for uuanim in animCurveUUNodes:
                                if uuanim not in dgNodes:
                                    dgNodes.append(uuanim)
                except Exception:
                    pass
        else:
            # If the node in iteration is not a transform, only add the unit conversion nodes created by maya
            unitConNodes = cmds.listConnections(node, source=True, destination=True, type='unitConversion')
            if unitConNodes:
                for ucNode in unitConNodes:
                    if ucNode not in dgNodes:
                        dgNodes.append(ucNode)

    containedNodes.extend(dgNodes)

    # Finally add the collected nodes to the input container.
    try:
        cmds.container(inputContainer, edit=True, addNode=containedNodes, ihb=includeHierarchyBelow, \
                    includeShapes=includeShapes, force=force)
        return True

    except Exception:
        return False


def setRotationOrderForFootUtilTransform(transform, axesInfo):
    '''
    Calculate and set the rotate order for a given transform in a reverse IK leg/foot configuration.
    '''
    # Get the axes data from axesInfo using returnAxesInfoForFootTransform() 
    crossAx = axesInfo['cross'][0]
    aimAx = axesInfo['aim'][0]
    upAx = axesInfo['up'][0]

    # Get the rotateOrder based on the order of axes obtained above.
    rotateOrderAxes = aimAx + crossAx + upAx
    rotateOrder = {'xyz':0, 'yzx':1, 'zxy':2, 'xzy':3, 'yxz':4, 'zyx':5}[rotateOrderAxes.lower()]

    # Set rotation order
    cmds.setAttr(transform+'.rotateOrder', rotateOrder)


def align(target, toAlignTransform):
    '''
    Position and sets the orientation of an input "toAlignTransform"
    with respect to a "target" object in the scene.
    '''
    cmds.delete(cmds.parentConstraint(target, toAlignTransform, maintainOffset=False))


def updateNodeList(nodes):
    '''
    Updates all DAG nodes in a given node list.
    '''
    if not isinstance(nodes, list):
        nodes = [nodes]

    cmds.setToolTo('moveSuperContext')

    for node in nodes:
        if cmds.objectType(node, isAType='transform'):
            cmds.select(node, replace=True)  

    cmds.select(clear=True)
    cmds.setToolTo('selectSuperContext')    


def updateAllTransforms():
    '''
    Updates all transforms created by MRT.
    '''
    cmds.setToolTo('moveSuperContext')

    nodes = [node for node in cmds.ls(type='dagNode') if \
            re.match('^MRT_[a-zA-Z0-9_:]*(handle|transform|control){1}$', node)]

    for node in nodes:
        cmds.select(node, replace=True)  

    cmds.select(clear=True)
    cmds.setToolTo('selectSuperContext')   


def updateContainerNodes(container):
    '''
    Updates nodes within a given container.
    '''
    nodes = cmds.container(container, query=True, nodeList=True)
    cmds.setToolTo('moveSuperContext')

    for node in nodes:
        if cmds.objectType(node, isAType='transform'):
            cmds.select(node, replace=True)  

    cmds.select(clear=True)
    cmds.setToolTo('selectSuperContext')


def cleanSceneState():      # This definition is to be modified as necessary.
    '''
    Clean-up a scene, with nodes left by maya.
    '''
    dg_nodes = cmds.ls()
    extra_nodes = [u'ikSplineSolver', u'ikSCsolver', u'ikRPsolver', u'hikSolver']

    for node in extra_nodes:
        if not node in dg_nodes:
            break
    else:
        for node in dg_nodes:
            if cmds.nodeType(node) == 'ikHandle' or cmds.nodeType(node) == 'hikIKEffector':
                break
        else:
            cmds.delete(extra_nodes)


def returnModuleAttrsFromScene(moduleNamespace):
    '''
    Called to return all module specs / attributes. Accepts an existing
    module namespace. The returned data is used by createModuleFromAttributes(), createSkeletonFromModule(),
    and createProxyForSkeletonFromModule().
    '''

    moduleAttrsDict = {}

    # Get the creation plane, XY, YZ or XZ (along with the side, - or +), eg., +XY
    moduleAttrsDict['creation_plane'] = str(cmds.getAttr(moduleNamespace+':moduleGrp.onPlane'))

    # Get the node orientation order, eg., XYZ, where X is the aim axis, Y is up and so on.
    moduleAttrsDict['node_axes'] = str(cmds.getAttr(moduleNamespace+':moduleGrp.nodeOrient'))

    # Get the number of nodes.
    moduleAttrsDict['num_nodes'] = numNodes = cmds.getAttr(moduleNamespace+':moduleGrp.numberOfNodes')

    # Get the module parent info with default values. This is updated later. It contains the following info:
    # [[current module namespace, module parent info,
    # [mirror module namespace, mirror module parent info (if this module has a mirrored module pair)]]
    moduleAttrsDict['moduleParentInfo'] = [[moduleNamespace, cmds.getAttr(moduleNamespace+':moduleGrp.moduleParent')], \
                                                                                                     [None, u'None']]
    # Get the mirror function info for the module (This info is valid only in case of a mirrored module pair).
    # Initializing with default values. This will be updated below. It contains the following info:
    # [ True if mirroring is turned on,
    # Translation function for controls if mirroring,
    # Rotation function for controls if mirroring]
    moduleAttrsDict['mirror_options'] = ['Off', 'Local_Orientation', 'Behaviour']

    # Set if the module is a mirrored module. This value is needed/modified as needed while creating mirror modules.
    # This can be set to False. It's used to keep track of which module of thesetupParentingForRawCharacterParts mirrored pair is being created (The one
    # on the '-' or the '+' side of the creation plane.
    moduleAttrsDict['mirrorModule'] = False

    # Current module namespace
    moduleAttrsDict['module_Namespace'] = moduleNamespace ## moduleName

    # Get the user specified name for the module
    moduleAttrsDict['userSpecName'] = moduleNamespace.partition(':')[0].partition('__')[2]

    # Mirrored module namespace (valid in case of a mirrored module pair. Setting the default value.)
    moduleAttrsDict['mirror_module_Namespace'] = moduleNamespace + '_mirror'

    # Get the proxy geometry info. It contains the following info:
    # [True if it contains bone proxy geo,
    # True if it contains elbow proxy geo,
    # elbow proxy type, 'sphere' or 'cube' (to be updated later),
    # mirror instancing status for all module proxy geo]
    moduleAttrsDict['proxy_geo_options'] = [False, False, None, 'Off']

    # Get the info for node components for the module. It contains the following info:
    # [True for visibility of module hierarchy representation (set to True as  default),
    # True for visibility of module node orientation representation (set to False as default),
    # True for creation of proxy geometry (set as False as default)]
    moduleAttrsDict['node_compnts'] = [True, False, False]

    # Get the default (initial) length of the module.
    moduleAttrsDict['module_length'] = cmds.getAttr(moduleNamespace+':moduleGrp.moduleLength')

    # Get the default value of offset of module from its creation plane.
    moduleAttrsDict['module_offset'] = 1.0

    # Based on the argument module namespace, get the module creation info.

    if 'MRT_JointNode' in moduleNamespace:

        moduleAttrsDict['node_type'] = 'JointNode'

        moduleAttrsDict['scale'] = cmds.getAttr(moduleNamespace+':module_transform.finalScale')

        # Get the transform values for the module transform
        moduleAttrsDict['module_translation_values'] = cmds.getAttr(moduleNamespace+':module_transform.translate')[0]
        moduleAttrsDict['module_transform_orientation'] = cmds.getAttr(moduleNamespace+':module_transform.rotate')[0]

        # Get the node handle colour for the module
        moduleAttrsDict['handle_colour'] = cmds.getAttr(moduleNamespace+':root_node_transformShape.overrideColor') + 1

        # Get the module transform attributes.
        otherAttrs = cmds.listAttr(moduleNamespace+':module_transform', keyable=True, visible=True, unlocked=True)[6:]
        for attr in otherAttrs:
            moduleAttrsDict[attr] = cmds.getAttr(moduleNamespace+':module_transform'+'.'+attr)

        # Get the orientation and translation values for the module nodes.
        if numNodes == 1:
            moduleAttrsDict['node_handle_sizes'] = [('root_node_transform', \
                                    cmds.getAttr(moduleNamespace+':module_transform.root_node_transform_handle_size'))]

            moduleAttrsDict['orientation_repr_values'] = [('root_node_transform', \
                                  cmds.getAttr(moduleNamespace+':single_orient_repr_transform.rotate')[0])]
            
            moduleAttrsDict['node_world_translation_values'] = [('root_node_transform', \
                    cmds.xform(moduleNamespace+':root_node_transform', query=True, worldSpace=True, translation=True))]

            moduleAttrsDict['node_world_orientation_values'] = [('root_node_transform', \
            cmds.xform(moduleNamespace+':single_orient_repr_transform', query=True, worldSpace=True, rotation=True))]

            moduleAttrsDict['node_rotationOrder_values'] = [('root_node_transform', \
                                                     cmds.getAttr(moduleNamespace+':root_node_transform.rotateOrder'))]

        if numNodes > 1:
            # Get the node orientation representation control values
            node_orientation_Grp = moduleNamespace+':moduleOrientationHierarchyReprGrp'
            node_orientation_Grp_allChildren = \
                cmds.listRelatives(node_orientation_Grp, allDescendents=True, type='transform')
            all_node_orientation_transforms = filter(lambda transform:transform.endswith('orient_repr_transform'), \
                                                                                        node_orientation_Grp_allChildren)

            node_orientation_repr_values = []

            for transform in all_node_orientation_transforms:
                orientationAttr = cmds.listAttr(transform, keyable=True, visible=True, unlocked=True)[0]
                node_orientation_repr_values.append((stripMRTNamespace(transform)[1], \
                                                                                cmds.getAttr(transform+'.'+orientationAttr)))

            moduleAttrsDict['orientation_repr_values'] = node_orientation_repr_values

            # Get the world orientation values for the module nodes.
            node_world_orientations = []

            for transform in all_node_orientation_transforms:
                node_world_orientations.append((stripMRTNamespace(transform)[1].partition('_orient')[0], \
                                          cmds.xform(transform, query=True, worldSpace=True, rotation=True)))
            node_world_orientations.append(('end_node_transform', [0.0, 0.0, 0.0]))
            
            moduleAttrsDict['node_world_orientation_values'] = node_world_orientations

            # Get the node translation, world translation, and orientation values
            node_transform_Grp = moduleNamespace+':moduleNodesGrp'
            node_transform_Grp_allChildren = cmds.listRelatives(node_transform_Grp, allDescendents=True, type='joint')

            node_translations = []
            node_world_translations = []
            node_rotationOrders = []
            node_handle_sizes = []

            for transform in node_transform_Grp_allChildren:
                node_world_translations.append((stripMRTNamespace(transform)[1], cmds.xform(transform, query=True, worldSpace=True, \
                                                                                                            translation=True)))
                node_rotationOrders.append((stripMRTNamespace(transform)[1], cmds.getAttr(transform+'.rotateOrder')))
                node_handle_sizes.append((stripMRTNamespace(transform)[1], \
                            cmds.getAttr(moduleNamespace+':module_transform.'+stripMRTNamespace(transform)[1]+'_handle_size')))

            moduleAttrsDict['node_world_translation_values'] = node_world_translations
            moduleAttrsDict['node_rotationOrder_values'] = node_rotationOrders
            moduleAttrsDict['node_handle_sizes'] = node_handle_sizes


    if 'MRT_SplineNode' in moduleNamespace:

        moduleAttrsDict['node_type'] = 'SplineNode'

        # Get the module overall scale
        moduleAttrsDict['scale'] = cmds.getAttr(moduleNamespace+':splineStartHandleTransform.finalScale')

        # Get the transform values for the start and end spline module transforms
        moduleAttrsDict['splineStartHandleTransform_translation_values'] = \
                                                cmds.getAttr(moduleNamespace+':splineStartHandleTransform.translate')[0]
        moduleAttrsDict['splineEndHandleTransform_translation_values'] = \
                                                cmds.getAttr(moduleNamespace+':splineEndHandleTransform.translate')[0]

        # Get the node handle colour for the module
        moduleAttrsDict['handle_colour'] = cmds.getAttr(moduleNamespace+':spline_1_adjustCurve_transformShape.overrideColor') + 1

        # Get the start spline module transform attributes.
        otherAttrs = cmds.listAttr(moduleNamespace+':splineStartHandleTransform', keyable=True, visible=True, unlocked=True)[3:]
        for attr in otherAttrs:
            moduleAttrsDict[attr] = cmds.getAttr(moduleNamespace+':splineStartHandleTransform'+'.'+attr)

        # Get the spline "axis rotate" orientation value
        moduleAttrsDict['splineOrientation_value'] = cmds.getAttr(moduleNamespace+':splineStartHandleTransform.Axis_Rotate')

        # Get the spline node orientation type, "Object" or "World"
        moduleAttrsDict['node_objectOrientation'] = cmds.getAttr(moduleNamespace+':splineStartHandleTransform.Node_Orientation_Type')

        # Get the translate values for spline module adjust curve controls
        moduleSplineAdjustCurveGrpChildren = \
                cmds.listRelatives(moduleNamespace+':moduleSplineAdjustCurveGrp', allDescendents=True, type='transform')
        moduleSplineAdjustCurveGrp_allTransforms = \
                filter(lambda transform:transform.endswith('adjustCurve_transform'), moduleSplineAdjustCurveGrpChildren)

        splineAdjustCurveTransformValues = []

        for transform in moduleSplineAdjustCurveGrp_allTransforms:
            splineAdjustCurveTransformValues.append((stripMRTNamespace(transform)[1], 
                                                     cmds.xform(transform, query=True, worldSpace=True, translation=True)))

        moduleAttrsDict['splineAdjustCurveTransformValues'] = splineAdjustCurveTransformValues

        # Get the world translation and rotation values for spline nodes. Used when creating a joint hierarchy from
        # spline module in a character.
        node_transform_Grp_allChildren = cmds.listRelatives(moduleNamespace+':moduleNodesGrp', allDescendents=True, type='joint')

        node_world_orientations = []
        node_world_translations = []

        for transform in node_transform_Grp_allChildren:
            node_world_translations.append((stripMRTNamespace(transform)[1], cmds.xform(transform, query=True, worldSpace=True, \
                                                                                                            translation=True)))
            node_world_orientations.append((stripMRTNamespace(transform)[1], cmds.xform(transform, query=True, worldSpace=True, \
                                                                                                               rotation=True)))

        moduleAttrsDict['node_world_translation_values'] = node_world_translations
        moduleAttrsDict['node_world_orientation_values'] = node_world_orientations


    if 'MRT_HingeNode' in moduleNamespace:

        moduleAttrsDict['node_type'] = 'HingeNode'

        # Get the module overall scale
        moduleAttrsDict['scale'] = cmds.getAttr(moduleNamespace+':module_transform.finalScale')

        # Get the transform values for the module transform
        moduleAttrsDict['module_translation_values'] = cmds.getAttr(moduleNamespace+':module_transform.translate')[0]
        moduleAttrsDict['module_transform_orientation'] = cmds.getAttr(moduleNamespace+':module_transform.rotate')[0]

        # Get the node handle colour for the module
        moduleAttrsDict['handle_colour'] = cmds.getAttr(moduleNamespace+':root_node_transform_controlXShape.overrideColor') + 1

        # Get the module transform attributes.
        otherAttrs = cmds.listAttr(moduleNamespace+':module_transform', keyable=True, visible=True, unlocked=True)[6:]
        for attr in otherAttrs:
            moduleAttrsDict[attr] = cmds.getAttr(moduleNamespace+':module_transform'+'.'+attr)

        # Get the world translation and rotation values for hinge module nodes. This is used when creating a joint hierarchy 
        # from hinge module in a character and when duplicating a hinge module. First, in order to get the correct rotation 
        # values of the module nodes, we have to reset the node rotation orders to their default.

        # Get the module node transforms.
        node_transform_Grp_allChildren = cmds.listRelatives(moduleNamespace+':moduleNodesGrp', allDescendents=True, type='joint')

        # Get the current rotation orders of module nodes (set by the user).
        node_rotationOrder = []
        for transform in node_transform_Grp_allChildren[::-1]:
            node_rotationOrder.append((stripMRTNamespace(transform)[1], cmds.getAttr(transform+'.rotateOrder')))

        moduleAttrsDict['node_rotationOrder_values'] = node_rotationOrder

        # Get the module transform rotation order attributes.
        rotOrder_attrs = [attr for attr in \
        cmds.listAttr(moduleNamespace+':module_transform', keyable=True, unlocked=True, visible=True) \
        if attr.find('rotate_order') != -1]

        # Reset the module transform rotation order attributes.
        for attr in rotOrder_attrs:
            cmds.setAttr(moduleNamespace+':module_transform.'+attr, 0)

        # Now, get the node world translation, rotation and sizes
        node_world_orientations = []
        node_world_translations = []
        node_handle_sizes = []

        for transform in node_transform_Grp_allChildren[::-1]:
            node_world_translations.append((stripMRTNamespace(transform)[1], cmds.xform(transform, query=True, worldSpace=True, \
                                                                                                            translation=True)))
            node_world_orientations.append((stripMRTNamespace(transform)[1], cmds.xform(transform, query=True, worldSpace=True, \
                                                                                                               rotation=True)))
            node_handle_sizes.append((stripMRTNamespace(transform)[1], \
                            cmds.getAttr(moduleNamespace+':module_transform.'+stripMRTNamespace(transform)[1]+'_handle_size')))

        moduleAttrsDict['node_world_translation_values'] = node_world_translations
        moduleAttrsDict['node_world_orientation_values'] = node_world_orientations
        moduleAttrsDict['node_handle_sizes'] = node_handle_sizes

        # Now set the user specified rotation orders on module nodes after obtaining their rotations.
        for attr, rotOrder in zip(rotOrder_attrs, node_rotationOrder):
            cmds.setAttr(moduleNamespace+':module_transform.'+attr, rotOrder[1])

        # Get the world position of the middle "hinge" position for the IK chain segment.
        # If the start, hinge and end positions in an IK chain are projected onto a line,
        # the 'ikSegmentMidPos' is the middle position.
        moduleAttrsDict['ikSegmentMidPos'] = cmds.xform(moduleNamespace+':ikSegmentAimCurve.cv[0]', query=True, \
                                                                                            worldSpace=True, translation=True)

    # If proxy geometry exists, get its info.
    if cmds.objExists(moduleNamespace+':proxyGeometryGrp'):

        # Set the proxy geo node component to True
        moduleAttrsDict['node_compnts'][2] = True

        # Check if the module contains 'bone' or 'elbow' proxy geo transforms
        proxyGrpTransforms = cmds.listRelatives(moduleNamespace+':proxyGeometryGrp', allDescendents=True, type='transform')
        proxyGrpTransforms = filter(lambda transform:transform.endswith('_geo'), proxyGrpTransforms)

        for transform in proxyGrpTransforms:
            if re.match(moduleNamespace+':(root_node|end_node|node_\d+)_proxy_bone_geo', transform):
                
                # Set proxy geo options for bone to be True
                moduleAttrsDict['proxy_geo_options'][0] = True
                
            if re.match(moduleNamespace+':(root_node|end_node|node_\d+)_proxy_elbow_geo', transform):
                
                # Set proxy geo options for elbow to be True
                moduleAttrsDict['proxy_geo_options'][1] = True
                
                # Set the elbow proxy geo type
                moduleAttrsDict['proxy_geo_options'][2] = cmds.getAttr(moduleNamespace+':proxyGeometryGrp.elbowType')

    # If a mirrored module pair exists, get the required attributes.
    if cmds.attributeQuery('mirrorModuleNamespace', node=moduleNamespace+':moduleGrp', exists=True):
        
        # Namespace for the mirrored module
        moduleAttrsDict['mirror_module_Namespace'] = cmds.getAttr(moduleNamespace+':moduleGrp.mirrorModuleNamespace')
        
        # Mirrored module parent info
        moduleAttrsDict['moduleParentInfo'][1] =[moduleAttrsDict['mirror_module_Namespace'], \
                                     cmds.getAttr(moduleAttrsDict['mirror_module_Namespace']+':moduleGrp.moduleParent')]
        # Get the mirroring info
        moduleAttrsDict['mirror_options'][0] = 'On'
        moduleAttrsDict['mirror_options'][1] = cmds.getAttr(moduleNamespace+':moduleGrp.mirrorTranslation')
        moduleAttrsDict['mirror_options'][2] = cmds.getAttr(moduleNamespace+':moduleGrp.mirrorRotation')

        # If proxy geo is enabled, get the value of mirror instancing state
        if moduleAttrsDict['node_compnts'][2] == True:
            moduleAttrsDict['proxy_geo_options'][3] = cmds.getAttr(moduleNamespace+':proxyGeometryGrp.mirrorInstance')

    return moduleAttrsDict


def createSkeletonFromModule(moduleAttrsDict):
    '''
    Converts a module to a joint hierarchy. This method is called during character creation to perform on modules
    in the scene. It uses the module attribute data generated by "returnModuleAttrsFromScene" function.
    '''
    # IN-SCOPE DEF, to be used internally.
    def joint(*args, **kwargs):
        '''
        Wrapper function for creating joint(s) to be used by character/control rigs (not for modules). 
        Creates a custom attribute which can be used to identify the joint(s) created by MRT.
        '''
        # Create the joint with the passed-in parameters.
        jnt = cmds.joint(*args, **kwargs)
        
        if not kwargs.has_key('edit') or kwargs.has_key('query'):
            
            # Create an attribute for identification.
            cmds.addAttr(jnt, attributeType='bool', longName='mrtJoint', dv=1)
        
        return jnt
    
    # MAIN DEF BEGINS
    
    # To collect joints created from the module (by using its attributes)
    joints = []
    
    # If the module is a mirrored module pair, mirror its joint set pair on the + side of its creation plane.
    # First, you always create the joints from a module created on the + side of its creation plane for a mirrored
    # module pair, and then mirror the joint set hierarchy for its mirrored module.
    if moduleAttrsDict.get('mirror_module_Namespace') != None and moduleAttrsDict['creation_plane'][0] == '-':
    
        # Get the namespace for the module in a mirrored pair (the one created on the + side of creation plane).
        origUserSpecName = moduleAttrsDict['mirror_module_Namespace'].partition(':')[0].partition('__')[2]
        
        # Get the name of the root joint from the joint set hierarchy created from that module.
        origRootJointName = origUserSpecName+'_root_node_joint'

        # Set the rotation function for joint hierarchy mirroring. The value found is set to true.
        rotationFunc = {'behaviour':False, 'orientation':False}
        rotationFunc[moduleAttrsDict['mirror_options'][2].lower()] = True
        
        # Set the value for the creation plane to true.
        mirrorAxis = {'XY':False, 'YZ':False, 'XZ':False}
        mirrorAxis[moduleAttrsDict['creation_plane'][1:]] = True
        
        # Mirror the joint hierarchy created from the module (created on + side of the creation plane).
        r_joints = cmds.mirrorJoint(origRootJointName, mirrorBehavior=rotationFunc['behaviour'], mirrorXY=mirrorAxis['XY'], \
                                                                                                 mirrorXZ=mirrorAxis['XZ'], \
                                                                                                 mirrorYZ=mirrorAxis['YZ'])
        # Set the attributes on the mirrored joints.
        for jnt in r_joints:
            cmds.setAttr(jnt+'.plane', lock=False)
            
            # Creation plane.
            cmds.setAttr(jnt+'.plane', '-'+moduleAttrsDict['creation_plane'][1:], type='string', lock=True)
            
            # Get the new name for the joint, and rename it.
            #name = re.split(origUserSpecName, joint)[0] + moduleAttrsDict['userSpecName'] + re.split(origUserSpecName, joint)[1]
            name = moduleAttrsDict['userSpecName'] + re.split(origUserSpecName, jnt)[1]
            name = re.split('\d+$', name)[0]    # Remove any num suffix added by maya during mirroring
            jnt = cmds.rename(jnt, name)
            joints.append(jnt)
        
        # Set the 'Mid pos for the ik segment' attribute, if the mirror module pair is of HingeNode type.
        if moduleAttrsDict['node_type'] == 'HingeNode':
            cmds.setAttr(joints[0]+'.ikSegmentMidPos', lock=False)
            cmds.setAttr(joints[0]+'.ikSegmentMidPos', moduleAttrsDict['ikSegmentMidPos'], type='string', lock=True) 

    # If the module is not part of a mirrored pair, or if it is, but was created on the + side of its creation plane.
    else:
        # If the module type is JointNode.
        if moduleAttrsDict['node_type'] == 'JointNode':
        
            # If the JointNode module has one node.
            if moduleAttrsDict['num_nodes'] == 1:
            
                # Get the name of the joint to be created from the module node.
                name = moduleAttrsDict['userSpecName']+'_root_node_joint'
                
                # Create the joint.
                jointName = joint(name=name, position=moduleAttrsDict['node_world_translation_values'][0][1],
                                       orientation=moduleAttrsDict['node_world_orientation_values'][0][1],
                                       radius=moduleAttrsDict['scale']*moduleAttrsDict['node_handle_sizes'][0][1]*0.16)
                
                # Set the joint attributes.
                cmds.addAttr(jointName, dataType='string', longName='inheritedNodeType')
                cmds.setAttr(jointName+'.inheritedNodeType', 'JointNode', type='string', lock=True)
                cmds.setAttr(jointName+'.rotateOrder', moduleAttrsDict['node_rotationOrder_values'][0][1])
                joints.append(jointName)
                cmds.setAttr(jointName+'.overrideEnabled', 1)
                cmds.setAttr(jointName+'.overrideColor', moduleAttrsDict['handle_colour'])    
            
            # If the JointNode module has more than one node, go over each module node and create a joint hierarchy.
            if moduleAttrsDict['num_nodes'] > 1:
                
                for i, position in enumerate(moduleAttrsDict['node_world_translation_values']):
                
                    # Get the name of the joint to be created from the module node.
                    name = '%s_%s' % (moduleAttrsDict['userSpecName'], position[0].replace('transform', 'joint'))
                    
                    # Create the joint for the module node.
                    jointName = joint(name=name, position=position[1],
                                       radius=moduleAttrsDict['scale']*moduleAttrsDict['node_handle_sizes'][i][1]*0.16)
                                       
                    # Set the joint attributes.
                    cmds.addAttr(jointName, dataType='string', longName='inheritedNodeType')
                    cmds.setAttr(jointName+'.inheritedNodeType', 'JointNode', type='string', lock=True)
                    cmds.setAttr(jointName+'.overrideEnabled', 1)
                    cmds.setAttr(jointName+'.overrideColor', moduleAttrsDict['handle_colour'])                
                    joints.append(jointName)

                # Orient the joint rotation axes. First orient the root joint with children to align the aim axis.
                
                # Get the up axis for joint orientation from creation plane axes.
                s_axis = {'XY':'zup', 'YZ':'xup', 'XZ':'yup'}[moduleAttrsDict['creation_plane'][1:]]
                
                # Select the root joint in the joint hierarchy.
                cmds.select(joints[0], replace=True)
                
                # Perform joint orientation, this is done to align the aim axis down the joint hierarchy.
                joint(edit=True, orientJoint=moduleAttrsDict['node_axes'].lower(), secondaryAxisOrient=s_axis,     \
                                                                                         zeroScaleOrient=True, children=True)
                cmds.select(clear=True)
                
                # Unparent the child joints for further orientation.
                for jnt in joints[1:]:
                    cmds.parent(jnt, absolute=True, world=True)
                
                # Orient the joints using the orientation data.
                for (jnt, orientation) in zip(joints, moduleAttrsDict['node_world_orientation_values']):
                    joint(jnt, edit=True, orientation=orientation[1])

                # Reparent the child joints.
                for i, jnt in enumerate(joints[1:]):
                    cmds.parent(jnt, joints[i], absolute=True)
                
                # Reset the orientation for last joint.
                cmds.setAttr(joints[-1]+'.jointOrient', 0, 0, 0, type='double3')
                cmds.select(clear=True)
                
                # Set the joint rotation orders.
                for jnt, rotOrder in zip(joints, moduleAttrsDict['node_rotationOrder_values']):
                    cmds.setAttr(jnt+'.rotateOrder', rotOrder[1])

        # If the module type is SplineNode.
        if moduleAttrsDict['node_type'] == 'SplineNode':
        
            # Create joints for every spline node position.
            for position in moduleAttrsDict['node_world_translation_values']:
            
                # Get the name for the joint.
                name = '%s_%s' % (moduleAttrsDict['userSpecName'], position[0].replace('transform', 'joint'))
                
                # Create the joint and add attributes
                jointName = joint(name=name, position=position[1], radius=moduleAttrsDict['scale']*0.17)
                cmds.addAttr(jointName, dataType='string', longName='inheritedNodeType')
                cmds.setAttr(jointName+'.inheritedNodeType', 'SplineNode', type='string', lock=True)
                cmds.addAttr(jointName, dataType='string', longName='splineOrientation')
                cmds.setAttr(jointName+'.splineOrientation', moduleAttrsDict['node_objectOrientation'], type='string', lock=True)
                cmds.setAttr(jointName+'.overrideEnabled', 1)
                cmds.setAttr(jointName+'.overrideColor', moduleAttrsDict['handle_colour'])               
                joints.append(jointName)
            
            # Get the up axis for joint orientation from creation plane axes for the spline module.
            s_axis = {'XY':'zup', 'YZ':'xup', 'XZ':'yup'}[moduleAttrsDict['creation_plane'][1:]]
            
            # Orient the joint chain along the aim axis.
            cmds.select(joints[0], replace=True)
            joint(edit=True, orientJoint=moduleAttrsDict['node_axes'].lower(), secondaryAxisOrient=s_axis, \
                                                                                        zeroScaleOrient=True, children=True)
            cmds.select(clear=True)
            
            # Unparent the child joints in the joint chain.
            for jnt in joints[1:]:
                cmds.parent(jnt, absolute=True, world=True)
            
            # If the spline module node orinetatioh type is set to 'object', orient the joints individually.
            if moduleAttrsDict['node_objectOrientation'] == 1:
                aimVector={'X':[1.0, 0.0, 0.0], 'Y':[0.0, 1.0, 0.0], 'Z':[0.0, 0.0, 1.0]}[moduleAttrsDict['node_axes'][0]]
                upVector = {'X':[1.0, 0.0, 0.0], 'Y':[0.0, 1.0, 0.0], 'Z':[0.0, 0.0, 1.0]}[moduleAttrsDict['node_axes'][1]]
                worldUpVector = \
                {'XY':[0.0, 0.0, 1.0], 'YZ':[1.0, 0.0, 0.0], 'XZ':[0.0, 1.0, 0.0]}[moduleAttrsDict['creation_plane'][1:]]
                
                # Aim and orient to the next joint, except the last joint.
                for i in xrange(len(joints)):
                    if not joints[i] == joints[-1]:
                        tempConstraint = cmds.aimConstraint(joints[i+1], joints[i], aimVector=aimVector, upVector=upVector,
                                                                                                worldUpVector=worldUpVector)
                        cmds.delete(tempConstraint) 
                        cmds.makeIdentity(joints[i], rotate=True, apply=True)        
            
                # Add the 'axis rotate' value to the joint orientations.
                for (jnt, orientation) in zip(joints, moduleAttrsDict['node_world_orientation_values']):
                    axes_mult = {'x':[1, 0, 0], 'y':[0, 1, 0], 'z':[0, 0, 1]}[moduleAttrsDict['node_axes'][0].lower()]
                    addOrientation = [moduleAttrsDict['splineOrientation_value']*item for item in axes_mult]
                    jointOrientation = list(cmds.getAttr(jnt+'.jointOrient')[0])
                    newOrientation = map(lambda x, y:x+y, addOrientation, jointOrientation)
                    cmds.setAttr(jnt+'.jointOrient', newOrientation[0], newOrientation[1], newOrientation[2], type='double3')  

            # If the spline node orientation type is set to 'world'.
            else:
                for jnt in joints:
                    cmds.setAttr(jnt+'.jointOrient', 0, 0, 0, type='double3')

            # Re-parent the child joints in the spline joint chain.
            for i, jnt in enumerate(joints[1:]):
                cmds.parent(jnt, joints[i], absolute=True)

            # Set orientation for the last joint.
            cmds.setAttr(joints[-1]+'.jointOrient', 0, 0, 0, type='double3')
        
        # If the module type is HingeNode.
        if moduleAttrsDict['node_type'] == 'HingeNode':
            
            # Create the joints for the module nodes with their position.
            for i, position in enumerate(moduleAttrsDict['node_world_translation_values']):
            
                # Get the name of the joint
                name = '%s_%s' % (moduleAttrsDict['userSpecName'], position[0].replace('transform', 'joint'))
                
                # Create the joint.
                jointName = joint(name=name, position=position[1], \
                                       radius=moduleAttrsDict['scale']*moduleAttrsDict['node_handle_sizes'][i][1]*0.16)
            
                # Add / set the joint attributes.
                cmds.addAttr(jointName, dataType='string', longName='inheritedNodeType')
                cmds.setAttr(jointName+'.inheritedNodeType', 'HingeNode', type='string', lock=True)
                cmds.setAttr(jointName+'.overrideEnabled', 1)
                cmds.setAttr(jointName+'.overrideColor', moduleAttrsDict['handle_colour'])            
                joints.append(jointName)
        
            # Get the secondary / up axis for joint orientation from module creation plane.
            s_axis = {'XY':'zup', 'YZ':'xup', 'XZ':'yup'}[moduleAttrsDict['creation_plane'][1:]]
            cmds.select(joints[0], replace=True)
            
            # Orient the joint chain along their aim axis.
            joint(edit=True, orientJoint=moduleAttrsDict['node_axes'].lower(), secondaryAxisOrient=s_axis, \
                                                                                         zeroScaleOrient=True, children=True)
            cmds.select(clear=True)
            
            # Unparent the child joints.
            for jnt in joints[1:]:
                cmds.parent(jnt, absolute=True, world=True)
            
            # Apply the orientation to joints from the module attribute data.
            for (jnt, orientation) in zip(joints, moduleAttrsDict['node_world_orientation_values']):
                joint(jnt, edit=True, orientation=orientation[1])
            
            # Reparent the child joints.
            for i, jnt in enumerate(joints[1:]):
                cmds.parent(jnt, joints[i], absolute=True)
            
            # Apply the joint rotation orders.
            for jnt, rotOrder in zip(joints, moduleAttrsDict['node_rotationOrder_values']):
                cmds.setAttr(jnt+'.rotateOrder', rotOrder[1])
            
            # Add / set the 'ikSegmentModPos' attribute to the root joint (It's the position of the middle/hinge joint in the
            # joint chain in a straight line).
            cmds.addAttr(joints[0], dataType='string', longName='ikSegmentMidPos')
            cmds.setAttr(joints[0]+'.ikSegmentMidPos', moduleAttrsDict['ikSegmentMidPos'], type='string', lock=True)

        # Add additional joint attributes common to all module types.
        for jnt in joints:
            cmds.addAttr(jnt, longName='numNodes')
            cmds.setAttr(jnt+'.numNodes', moduleAttrsDict['num_nodes'], lock=True)
            cmds.addAttr(jnt, dataType='string', longName='nodeAxes')
            cmds.setAttr(jnt+'.nodeAxes', moduleAttrsDict['node_axes'], type='string', lock=True)
            cmds.addAttr(jnt, dataType='string', longName='plane')
            cmds.setAttr(jnt+'.plane', moduleAttrsDict['creation_plane'], type='string', lock=True)
            cmds.addAttr(jnt, dataType='string', longName='translationFunction')
            cmds.setAttr(jnt+'.translationFunction', moduleAttrsDict['mirror_options'][1].lower(), type='string', lock=True)
            cmds.addAttr(jnt, dataType='string', longName='rotationFunction')
            cmds.setAttr(jnt+'.rotationFunction', moduleAttrsDict['mirror_options'][2].lower(), type='string', lock=True)

        cmds.select(clear=True)

    return joints


def setupParentingForRawCharacterParts(characterJointSet, jointsMainGrp):
    '''
    Set up parenting for joint hierarchies while creating a character. The type of parenting
    depends on the module parenting info stored for joints for a hierarchy in "characterJointSet".

    "Constrained" parenting uses parent constraint, "DG parenting". "Hierarchical" parenting uses DAG parenting.
    '''
    
    # To collect all "constrained" root joints for joint hierarchies. This is the joint above the root joint
    # for a joint hierarchy and it is used to receive constraints.
    all_root_joints = []

    # Iterate through the joints in the hierarchy.
    for item in characterJointSet:

        # Each "item", contains the following data:
        # ("<parent module node>,<parent type>", ["<child hierarchy root joint>", ..., "<child hierarchy end joint>"])
        # As an example:
        # ("MRT_JointNode__r_clavicle:root_node_transform,Constrained", ["r_arm_root_node_joint",
        #                                                                "r_arm_node_1_joint",
        #                                                                "r_arm_end_node_joint"])
        #
        # The module parenting info is stored as string. Eg., if the node "MRT_HingeNode__l_leg:end_node_transform",
        # is a hierarchical parent, it will stored as:
        # "MRT_HingeNode__l_leg:end_node_transform,Hierarchical" or "...,Constrained" if constrained parent.
            
        # If there's no parent info for a joint hierarchy, the "item" contains:
        # ("None", ["module_root_node_joint",
        #           "module_node_1_joint",
        #           "module_node_2_joint"])
        #
        # The first index of the "item" list contains the parent info. Here's it's "None".
        
        # Now, get the parent info for the joint and proceed.
        parentInfo = item[0].split(',')
        
        # From the parent info, get the parent type.
        parentType = parentInfo[-1]

        if parentType != 'None':

            # This parent module node name needs to be converted to its current joint name in the scene, which will be used.
            # This is needed since "setupParentingForRawCharacterParts" is called after all module nodes in the scene
            # are converted to joints.
            # Eg., "MRT_HingeNode__l_leg:end_node_transform" is renamed as "l_leg_end_node_joint".
            userSpecName = parentInfo[0].partition(':')[0].partition('__')[2]
            jointName = parentInfo[0].partition(':')[2].replace('transform', 'joint')
            parentInfo[0] = '%s_%s' % (userSpecName, jointName)

        # If the parent type is "Hierarchical".
        if parentType == 'Hierarchical':
            cmds.parent(item[1][0], parentInfo[0], absolute=True)
            
        if parentType == 'None' or parentType == 'Constrained':

            # Else, the parent type is either "constrained" or it's main root joint hierarchy for the
            # character, driven by the character root control (ROOT_CNTL).
        
            # Create the joint group for joint hierarchy in "characterJointSet".
            # Get its name from the root joint of the joint hierarchy.
            # Eg., if its name is "r_arm_root_node_joint",
            # the name of the joint group is "r_arm_joints".
            name = re.split('_(?:root_node|node_\d+|end_node)_joint', item[1][0])[0] + '_joints'
            jointGrp = cmds.group(empty=True, name=name, parent=jointsMainGrp)
            # The joint group is not needed for a root joint of a joint hierarchy with a hierarchical parent,
            # since it'll be parented under a joint.

            cmds.select(clear=True)

            # Create the "constrained" joint above the root joint of the hierarchy to receive constraints.
            d_joint = cmds.duplicate(item[1][0], parentOnly=True, returnRootsOnly=True, name=item[1][0]+'_constrained')[0]
            cmds.setAttr(d_joint+'.drawStyle', 2)   # drawStyle to None
            cmds.setAttr(d_joint+'.overrideEnabled', 1)
            cmds.setAttr(d_joint+'.overrideDisplayType', 1)
            cmds.setAttr(d_joint+'.radius', 0)

            # Now, specifically, if parent type is "Constrained".
            if parentType == 'Constrained':

                # Add constrained parent info to the root joint of the joint hierarchy
                cmds.addAttr(item[1][0], dataType='string', longName='constrainedParent', keyable=False)
                cmds.setAttr(item[1][0]+'.constrainedParent', parentInfo[0], type='string', lock=True)
                
                # Constrain this joint with its parent.
                parentConstraint(parentInfo[0], d_joint, maintainOffset=True)
                
            # Parent the root joint to it.
            cmds.parent(item[1][0], d_joint, absolute=True)
            
            # Parent the constrained joint under the joint group.
            cmds.parent(d_joint, jointGrp, absolute=True)

            # If a joint hierarchy has no parent type, it's the main root joint hierarchy (or one of) for the character.
            # Later, this joint hierarchy will be constrained under the character root control,
            # under "processCharacterFromScene" in mrt_UI.
            if parentType == 'None':
                # Collect it.
                all_root_joints.append(d_joint)

    return all_root_joints


def createProxyForSkeletonFromModule(characterJointSet, moduleAttrsDict, characterName):
    '''
    Set up proxy geometry for joint hierarchies during character creation. It uses the module attribute data generated by 
    "returnModuleAttrsFromScene". It uses the existing module proxy geometry, if it exists.
    
    We'll iterate through joint chain created from its module (nodes), find if the module proxy proxy geometry, bone or elbow
    type exists for the module and hence for the node, duplicate it for the joint and drive it appropriately.
    '''
    
    # Get the joint set, which in this case is the last joint set added to the 'characterJointSet' data list.
    # See 'processCharacterFromScene' in mrt_UI.
    # Then it looks into the joint set data, and lets the joint list from the second (1) index.
    # See 'setupParentingForRawCharacterParts' above for details on 'characterJointSet'.
    jointSet = characterJointSet[-1][1]
    
    # Create the group to contain the joint proxy geometry.
    proxyGrp = cmds.group(empty=True, name=moduleAttrsDict['userSpecName']+'_proxyGeoGrp')

    for (index, joint) in zip(range(moduleAttrsDict['num_nodes']), jointSet):
        
        # Get the naming prefix for the joint (generated from module node).
        if moduleAttrsDict['num_nodes'] > 1:
            if index == moduleAttrsDict['num_nodes']-1:
                namePrefix = 'end_node'
            elif index == 0:
                namePrefix = 'root_node'
            else:
                namePrefix = 'node_%s' % index
        else:
            namePrefix = 'root_node'
            
        # If elbow proxy geometry exists for the module.
        elbow_proxy_preTransform = moduleAttrsDict['module_Namespace']+':%s_proxy_elbow_preTransform' % namePrefix
        if cmds.objExists(elbow_proxy_preTransform):
            
            # Duplicate the module proxy geometry and name it.
            elbow_proxy = cmds.duplicate(elbow_proxy_preTransform, returnRootsOnly=True, renameChildren=True, \
                                         name='%s_%s_proxy_elbow_preTransform' \
                                            % (moduleAttrsDict['userSpecName'], namePrefix))[0]
            cmds.makeIdentity(elbow_proxy, scale=True, apply=True)
            
            # Constrain it to the root joint and palce it under proxy group.
            parentConstraint(joint, elbow_proxy, maintainOffset=True)
            scaleConstraint(joint, elbow_proxy, maintainOffset=True)
            cmds.parent(elbow_proxy, proxyGrp)
            
        # If bone proxy geometry exists for the module.
        bone_proxy_preTransform = moduleAttrsDict['module_Namespace']+':%s_proxy_bone_preTransform' % namePrefix
        if cmds.objExists(bone_proxy_preTransform):
            
            # Duplicate the module proxy geometry and name it.
            bone_proxy = cmds.duplicate(bone_proxy_preTransform, \
                                        returnRootsOnly=True, renameChildren=True, \
                                        name='%s_%s_proxy_bone_preTransform' \
                                            % (moduleAttrsDict['userSpecName'], namePrefix))[0]
            cmds.makeIdentity(bone_proxy, scale=True, apply=True)
            
            # Parent constrain the bone proxy geo to the joint.
            parentConstraint(joint, bone_proxy, maintainOffset=True)
                                      
            # Calculate and drive the aim axis scaling of the bone proxy geometry (which is between two joints).
            
            # Create the utility nodes.
            nodeNamePrefix = '%s_%s_proxy_bone' % (moduleAttrsDict['userSpecName'], namePrefix)
            distanceBetweenNode = cmds.createNode('distanceBetween', name=nodeNamePrefix+'_scaleLengthDistance', skipSelect=True)
            distanceBetween_1_vecPro = cmds.createNode('vectorProduct', name=nodeNamePrefix+'_scaleLengthVector_1_point', skipSelect=True)
            distanceBetween_2_vecPro = cmds.createNode('vectorProduct', name=nodeNamePrefix+'_scaleLengthVector_2_point', skipSelect=True)
            distanceScaleDivide = cmds.createNode('multiplyDivide', name=nodeNamePrefix+'_distanceScaleDivide', skipSelect=True)
            
            # Connect the joints for positions to get the distance between them.
            cmds.connectAttr(joint+'.worldMatrix', distanceBetween_1_vecPro+'.matrix')
            cmds.setAttr(distanceBetween_1_vecPro+'.operation', 4)
            cmds.connectAttr(jointSet[index+1]+'.worldMatrix', distanceBetween_2_vecPro+'.matrix')
            cmds.setAttr(distanceBetween_2_vecPro+'.operation', 4)
            cmds.connectAttr(distanceBetween_1_vecPro+'.output', distanceBetweenNode+'.point1')
            cmds.connectAttr(distanceBetween_2_vecPro+'.output', distanceBetweenNode+'.point2')
            cmds.connectAttr(distanceBetweenNode+'.distance', distanceScaleDivide+'.input1X')
            cmds.setAttr(distanceScaleDivide+'.operation', 2)
            
            # Set the default distance and drive the aim scaling.
            defDistance = cmds.getAttr(distanceScaleDivide+'.input1X')
            cmds.setAttr(distanceScaleDivide+'.input2X', defDistance)
            cmds.connectAttr(distanceScaleDivide+'.outputX', bone_proxy+'.scale'+moduleAttrsDict['node_axes'][0].upper())
            
            # Scale constrain the bone proxy geometry for the joint (skip the aim axis).
            scaleConstraint(joint, bone_proxy, maintainOffset=True, skip=moduleAttrsDict['node_axes'][0].lower())
                                        
            # Place it under proxy group.
            cmds.parent(bone_proxy, proxyGrp)

    # Find all the transforms added under the proxy group.
    allChildren = cmds.listRelatives(proxyGrp, allDescendents=True, fullPath=True, shapes=False)
    
    # To collect all the proxy geo transforms under the proxy group.
    proxy_geo_transforms = []

    # If proxy transforms are found, proceed.
    if allChildren:
    
        for node in allChildren:
        
            # Delete the old constraint transform parented under them (inherited by duplicating the module proxy transform).
            if cmds.objectType(node, isAType='constraint'):
                connections = cmds.listConnections(node)
                
                # If the constraint transform is disconnected, delete it (Newer constraint from joints have connections).
                if not connections:
                    cmds.delete(node)
                
                # If the transform type is a constraint, do not proceed further.
                continue
        
            # Rename any other unnamed transforms.
            nodeName = node.rpartition('|')[-1]
            if re.match('^(root_node|node_\d+|end_node)', nodeName):
                node = cmds.rename(node, moduleAttrsDict['userSpecName']+'_'+nodeName)
            
            # Collect the node if it's a proxy geo transform.
            if str(node).rpartition('geo')[2] == '':
                proxy_geo_transforms.append(node)
                
        # Get a name for the proxy display layer for the character and create it.
        layerName = 'MRT_'+characterName+'_proxy_geometry'
        if not cmds.objExists(layerName):
            cmds.createDisplayLayer(empty=True, name=layerName, noRecurse=True)
            cmds.setAttr(layerName+'.displayType', 2)
            
        # Now set the color for the proxy geo transforms and add it to the display layer.
        for transform in proxy_geo_transforms:
            cmds.polyColorPerVertex(transform+'.vtx[*]', alpha=1.0, rgb=[0.663, 0.561, 0.319], notUndoable=True, \
                                                                                            colorDisplayOption=True)
            cmds.editDisplayLayerMembers(layerName, transform)
        
        return proxyGrp

    # If no proxy geometry was found for the original module, and hence they were not duplicated for the joints and placed
    # under the proxy group, delete it.
    else:
        cmds.delete(proxyGrp)
        return None


def createFKlayerDriverOnJointHierarchy(*args, **kwargs):
    '''
    Creates a joint layer on top of a selected character hierarchy. For description in context, 
    see the "applyFK_Control" method for the "BaseJointControl" class in "mrt_controlRig_src.py"
    '''
    
    # Get the input arguments
    
    # 1
    if 'characterJointSet' in kwargs:
        characterJointSet = kwargs['characterJointSet']
    else:
        characterJointSet = args[0]
    if isinstance(characterJointSet, list) and len(characterJointSet):
        pass
    else:
        Error('MRT: No joint set specified from a character. Cannot create driver hierarchy.')
        # I don't use 'cmds.error' since it generates an exception.
        return
    
    # 2
    if 'jointLayerName' in kwargs:
        jointLayerName = kwargs['jointLayerName']
    else:
        jointLayerName = args[1]
    if not isinstance(jointLayerName, (unicode, str)):
        Error('MRT: No name specified for the driver layer. Aborting.')
        return
    jointLayerName = jointLayerName[0].upper() + jointLayerName[1:] # Capitalize first character.

    # 3
    if 'characterName' in kwargs:
        characterName = kwargs['characterName']
    else:
        characterName = args[2]
    if not isinstance(characterName, (unicode, str)):
        Error('MRT: No character name specified. Aborting.')
        return
    
    # 4
    if 'asControl' in kwargs:
        asControl = kwargs['asControl']
    elif len(args) > 3:
        asControl = args[3]
    else:
        asControl = False
    if not isinstance(asControl, bool):
        asControl = False

    # 5
    if 'layerVisibility' in kwargs:
        layerVisibility = kwargs['layerVisibility']
    elif len(args) > 4:
        layerVisibility = args[4]
    else:
        layerVisibility = 'On'
    if not isinstance(layerVisibility, (unicode, str)):
        layerVisibility = 'On'
    
    # 6
    if 'transFilter' in kwargs:
        transFilter = kwargs['transFilter']
    elif len(args) > 5:
        transFilter = args[5]
    else:
        transFilter = False
    if not isinstance(transFilter, bool):
        transFilter = False
    
    # 7
    if 'controlLayerColour' in kwargs:
        controlLayerColour = kwargs['controlLayerColour']
    elif len(args) > 6:
        controlLayerColour = args[6]
    else:
        controlLayerColour = None
    if not isinstance(controlLayerColour, int):
        controlLayerColour = None
    
    # 8
    if 'connectLayer' in kwargs:
        connectLayer = kwargs['connectLayer']
    elif len(args) > 7:
        connectLayer = args[7]
    else:
        connectLayer = True
    if not isinstance(connectLayer, bool):
        connectLayer = True
    
    
    # Debug only -
    # print 'characterJointSet -> ', characterJointSet
    # print 'jointLayerName -> ', jointLayerName
    # print 'characterName -> ', characterName
    # print 'asControl -> ', asControl
    # print 'layerVisibility -> ', layerVisibility
    # print 'transFilter -> ', transFilter
    # print 'controlLayerColour -> ', controlLayerColour
    # print 'connectLayer -> ', connectLayer

    
    # To get the names of joints in the new driver layer.
    layerJointSet = []

    # To collect the constraints for the new driver joint layer to drive the input joint hierarchy.
    driver_constraints = []

    # To get the name of the root joint of the new driver joint layer.
    layerRootJoint = ''

    # Iterate through the passed-in joint hierarchy (selected, one of) for the character.
    for joint in characterJointSet:

        # Find the root joint of the hierarchy
        if joint.endswith('root_node_joint'):

            # Get the constrained joint for the root joint. It's the joint above the root joint
            # which receives constraints. The root joint is not constrained.
            jointParent = cmds.listRelatives(joint, parent=True, type='joint')

            if jointParent[0].endswith('_constrained'):

                # Get the naming prefix and suffix from the root joint name
                # Eg., if the root joint name is "module_root_node_transform",
                # then the prefix is "module" and the mid suffix is "_root_node".
                
                jointPrefix = re.split('_(?:root_node|node_\d+|end_node)_joint', joint)[0]
                jointSuffix = re.findall('_(?:root_node|node_\d+|end_node)', joint)[0]

                # Provide a name for the joint in the new hierarchy to created in this layer. A "_CNTL" suffix
                # would be added to joint name if it'll be used as direct control transforms (like as an FK control,
                # which will drive the original joint hierarchy).
                # If asControl argument is set to True.
                if asControl:
                    newName = '%s_%s%s_CNTL' % (jointPrefix, jointLayerName, jointSuffix)
                else:
                    newName = '%s_%s%s_joint' % (jointPrefix, jointLayerName, jointSuffix)

                # Duplicate the input joint hierarchy by duplicating its root joint, and name it.
                newRootJoint = cmds.duplicate(joint, returnRootsOnly=True, name=newName)[0]

                # Change the draw style for joint to "None" if to be used as a control.
                if asControl:
                    cmds.setAttr(newRootJoint + '.drawStyle', 2)

                # Get the name of the root joint of this new layer.
                layerRootJoint = newRootJoint

                # Delete the ".rigLayers" attribute from the layer root joint
                # (derived by copying the input joint hierarchy, by duplicating its root joint).
                if cmds.attributeQuery('rigLayers', node=newRootJoint, exists=True):
                    cmds.setAttr(newRootJoint+'.rigLayers', lock=False)
                    cmds.deleteAttr(newRootJoint+'.rigLayers')

                # Append the new driver layer's root joint to the layer set
                layerJointSet.append(newRootJoint)

                # Iterate the hierarchy below the new driver layer's root joint, and rename the joint(s) below it.
                # If it's not a valid joint, delete it from the layer.
                rootChildren = cmds.listRelatives(newRootJoint, allDescendents=True, fullPath=True)

                if rootChildren:
                    for joint in rootChildren:
                        if cmds.objectType(joint, isType='joint'):

                            # If the joint is valid for the driver layer, it'll provide a prefix and a suffix
                            # name as derived below.
                            jointName = joint.rpartition('|')[2]
                            jointPrefix = re.split('_(?:root_node|node_\d+|end_node)_joint', jointName)
                            jointSuffix = re.findall('_(?:root_node|node_\d+|end_node)', jointName)
                            
                            if jointPrefix and jointSuffix:

                                # Get a new name for the joint in the layer.
                                if asControl:
                                    newName = '%s_%s%s_CNTL' % (jointPrefix[0], jointLayerName, jointSuffix[0])
                                else:
                                    newName = '%s_%s%s_joint' % (jointPrefix[0], jointLayerName, jointSuffix[0])

                                # Rename the join in the driver layer.
                                cmds.rename(joint, newName)
                                
                                # Change the draw style for joint to "None" if to be used as a control.
                                if asControl:
                                    cmds.setAttr(newName + '.drawStyle', 2)
                                
                                # Append the renamed joint to the layer set
                                layerJointSet.append(newName)

                        # If invalid joint, delete it.
                            else:
                                cmds.delete(joint)
                        else:
                            cmds.delete(joint)

    # Connect the new joint layer to drive the input joint hierarchy.
    if connectLayer:
        for (joint, layerJoint) in zip(sorted(characterJointSet), sorted(layerJointSet)):
            parent_constraint = parentConstraint(layerJoint, joint, maintainOffset=transFilter)
            scale_constraint = scaleConstraint(layerJoint, joint, maintainOffset=transFilter)
            driver_constraints.extend([parent_constraint, scale_constraint])

    # Disconnect the "all_joints" display to the driver layer joints (inherited by duplicating the input joint hierarchy).
    for joint in layerJointSet:
        cmds.disconnectAttr('MRT_'+characterName+'_all_joints.drawInfo', joint+'.drawOverride')

        # Set the visibility of the driver joint layer based on the "layerVisibility" argument.
        if layerVisibility == 'None':
            cmds.setAttr(joint+'.visibility', 0)

        # If the driver joint layer is to be used as direct control, connect its visibility to the "control_rig" layer.
        if layerVisibility == 'On':
            cmds.setAttr(joint+'.overrideEnabled', 1)
            cmds.connectAttr('MRT_'+characterName+'_control_rig.visibility', joint+'.overrideVisibility')

            # Set its control colour.
            if controlLayerColour:
                cmds.setAttr(joint+'.overrideColor', controlLayerColour)

    # Disconnect the driver layer joints from "skinJointSet" set.
    for joint in layerJointSet:

        # If the destination attribute "dagSetMembers" is returned as connected (from set "skinJointSet")
        c_info = cmds.listConnections(joint+'.instObjGroups[0]', source=False, destination=True, plugs=True)

        # Disconnect it.
        if c_info:
            cmds.disconnectAttr(joint+'.instObjGroups[0]', c_info[0])

    return layerJointSet, driver_constraints, layerRootJoint


def createModuleFromAttributes(moduleAttrsDict, createFromUI=False):
    '''
    Called for creating a new module from its attributes / specs. Accepts an existing module data returned by
    returnModuleAttrsFromScene().
    '''
    # Get the current namespace, and set to root namespace
    currentNamespace = mel.eval('namespaceInfo -currentNamespace')
    cmds.namespace(setNamespace=':')

    # If the module namespace in moduleAttrsDict exists, get a new namespace (while creating a duplicate module)
    if cmds.namespace(exists=moduleAttrsDict['module_Namespace']):

        # Get the user specified name.
        currentModuleUserSpecifiedName = moduleAttrsDict['userSpecName']

        underscore_search = '_'

        # The namespace for a module has two naming parts, the first part is assigned by MRT, and the second
        # part is assigned by the user
        # Eg., "MRT_JointNode__userModuleName:", where "userModuleName" is the user specified name.
        # This user specified name can also have a numerical suffix separated by underscore,
        # like MRT_JointNode__userModuleName_2:".

        # If the current user specified name has an integer suffix separated by an underscore
        if re.match('^\w+_[0-9]*$', currentModuleUserSpecifiedName):

            # Find all occurrences of underscores in the string as a list.
            underscore_search = re.findall('_*', currentModuleUserSpecifiedName)
            underscore_search.reverse()

            # Match and return the last underscore(which is added before the integer suffix).
            for item in underscore_search:
                if '_' in item:
                    underscore_search = item
                    break
            # Separate the base user specified name from the integer suffix (with the underscore)
            currentModuleUserSpecifiedNameBase = currentModuleUserSpecifiedName.rpartition(underscore_search)[0]
        else:
            # If not integer suffix found, proceed with the current user specified name
            currentModuleUserSpecifiedNameBase = currentModuleUserSpecifiedName

        # Get all matching module namespaces in the scene with the current base user specified name with a integer suffix.
        currentCopyNamespacesForModule = filter(lambda namespace:re.match('^MRT_\D+__%s%s[0-9]*$'%  \
                                                                          (currentModuleUserSpecifiedNameBase,  \
                                                                           underscore_search), namespace), \
                                                                            cmds.namespaceInfo(listOnlyNamespaces=True))
        # If such module namespaces are found, find the highest integer suffix.
        if len(currentCopyNamespacesForModule) > 0:
            # Get the user specified names
            currentCopyUserNamesForModule = [namespace.partition('__')[2] for namespace in currentCopyNamespacesForModule]
            # Get the highest integer suffix.
            suffix = findHighestNumSuffix(currentModuleUserSpecifiedNameBase, currentCopyUserNamesForModule)
        else:
            suffix = 0

        # Store the original module namespace
        moduleAttrsDict['orig_module_Namespace'] = moduleAttrsDict['module_Namespace']
        # Get the new module namespace, for the new module to be created
        moduleAttrsDict['module_Namespace'] = 'MRT_{0}__{1}{2}{3}'.format(moduleAttrsDict['node_type'], \
                                                                          currentModuleUserSpecifiedNameBase,   \
                                                                          underscore_search, (suffix+1))
        # Update the module parent info (see returnModuleAttrsFromScene())
        moduleAttrsDict['moduleParentInfo'][0][0] = moduleAttrsDict['module_Namespace']

    # If the module to be created is part of a mirrored pair (based on the module info returned by returnModuleAttrsFromScene()),
    # Find the new namespace to be used for creating the new mirrored module. - AS ABOVE -.
    if moduleAttrsDict['mirror_options'][0] == 'On':

        # If the mirror module namespace in moduleAttrsDict exists, get a new namespace (while creating a duplicate module)
        if cmds.namespace(exists=moduleAttrsDict['mirror_module_Namespace']):

            # Get the current mirror module user specified name
            currentModuleUserSpecifiedName = moduleAttrsDict['mirror_module_Namespace'].partition('__')[2]
            underscore_search = '_'

            if re.match('^\w+_[0-9]*$', currentModuleUserSpecifiedName):

                # Find all occurrences of underscores in the string as a list.
                underscore_search = re.findall('_*', currentModuleUserSpecifiedName)
                underscore_search.reverse()

                # Match and return the last underscore.
                for item in underscore_search:
                    if '_' in item:
                        underscore_search = item
                        break
                currentModuleUserSpecifiedNameBase = currentModuleUserSpecifiedName.rpartition(underscore_search)[0]
            else:
                currentModuleUserSpecifiedNameBase = currentModuleUserSpecifiedName

            updated_namespaces_for_mirror = cmds.namespaceInfo(listOnlyNamespaces=True)
            updated_namespaces_for_mirror.append(moduleAttrsDict['module_Namespace'])    # Add the new namspace created above
            currentCopyNamespacesForModule = filter(lambda namespace:re.match('^MRT_\D+__%s%s[0-9]*$'%  \
                                                                              (currentModuleUserSpecifiedNameBase,  \
                                                                               underscore_search), namespace),  \
                                                                                updated_namespaces_for_mirror)

            if len(currentCopyNamespacesForModule) > 0:
                currentCopyUserNamesForModule = [namespace.partition('__')[2] for namespace in currentCopyNamespacesForModule]
                suffix = findHighestNumSuffix(currentModuleUserSpecifiedNameBase, currentCopyUserNamesForModule)
            else:
                suffix = 0

            # Store the original mirror module namespace
            moduleAttrsDict['orig_mirror_module_Namespace'] = moduleAttrsDict['mirror_module_Namespace']
            # Get the new mirror module namespace
            moduleAttrsDict['mirror_module_Namespace'] = 'MRT_{0}__{1}{2}{3}'.format(moduleAttrsDict['node_type'], \
                                                                                     currentModuleUserSpecifiedNameBase, \
                                                                                     underscore_search, (suffix+1))
            moduleAttrsDict['moduleParentInfo'][1][0] = moduleAttrsDict['mirror_module_Namespace']

    # If the current module is on the '-' side of the creation plane for the mirrored module pair,
    # swap the new module and its mirror namespace
    if moduleAttrsDict['creation_plane'][0] == '-' and moduleAttrsDict['mirror_options'][0] == 'On':
        name = moduleAttrsDict['module_Namespace'] 
        moduleAttrsDict['module_Namespace'] = moduleAttrsDict['mirror_module_Namespace']
        moduleAttrsDict['mirror_module_Namespace'] = name

    # Create the module from its updated attributes
    modules = []    # Collect modules as they're created

    # For creating module instances.
    from mrt_module import MRT_Module

    # Get the module instance and create it based on its type
    moduleInst = MRT_Module(moduleAttrsDict)
    eval('moduleInst.create%sModule()' % moduleAttrsDict['node_type'])

    # Collect it
    modules.append(moduleAttrsDict['module_Namespace'])

    # Remove moduleInst reference from current scope (decrease ref count -1, for GC)
    del moduleInst

    # If the module is part of a mirrored pair, create its mirror
    if moduleAttrsDict['mirror_options'][0] == 'On':

        # Swap the working module namespace in moduleAttrsDict
        name = moduleAttrsDict['module_Namespace']
        moduleAttrsDict['module_Namespace'] = moduleAttrsDict['mirror_module_Namespace']
        moduleAttrsDict['mirror_module_Namespace'] = name

        # Set the module to be created as a 'mirror'.
        moduleAttrsDict['mirrorModule'] = True

        # Create the mirror module and collect it.
        mirrorModuleInst = MRT_Module(moduleAttrsDict)
        eval('mirrorModuleInst.create%sModule()' % moduleAttrsDict['node_type'])
        modules.append(moduleAttrsDict['module_Namespace'])
        del mirrorModuleInst

    # Lock the module containers.
    for module in modules:
        cmds.lockNode(module+':module_container', lock=True, lockUnpublished=True)

    cmds.select(clear=True)

    # Reset the working module namespace in moduleAttrsDict.
    if moduleAttrsDict['creation_plane'][0] == '+' and moduleAttrsDict['mirror_options'][0] == 'On':
        name = moduleAttrsDict['module_Namespace'] 
        moduleAttrsDict['module_Namespace'] = moduleAttrsDict['mirror_module_Namespace']
        moduleAttrsDict['mirror_module_Namespace'] = name


    # If a duplicate module is to be created, or not from the UI.
    if not createFromUI:

        # Collect the nodes that have to be updated later for mirroring.
        selectionNodes = []

        # Set the additional module attributes according to their type.

        if moduleAttrsDict['node_type'] == 'JointNode':

            # Set the translate / rotate on the module transform.
            module_transform = moduleAttrsDict['module_Namespace']+':module_transform'
            selectionNodes.append(module_transform)
            cmds.setAttr(module_transform+'.translate', *moduleAttrsDict['module_translation_values'])
            cmds.setAttr(module_transform+'.rotate', *moduleAttrsDict['module_transform_orientation'])

            # Set the module transform attributes.
            module_transform_attrs = cmds.listAttr(module_transform, keyable=True, visible=True, unlocked=True)[6:]
            for attr in module_transform_attrs:
                cmds.setAttr(module_transform+'.'+attr, moduleAttrsDict[str(attr)])

            # Apply module transform values to the mirror module (if it exists).
            if moduleAttrsDict['mirror_options'][0] == 'On':

                # Apply rotation multipliers to mirror module transform.
                mirrorAxisMultiply = {'XY':[-1, -1, 1], 'YZ':[1, -1, -1], 'XZ':[-1, 1, -1]}[moduleAttrsDict['creation_plane'][-2:]]
                module_orientation_values = [x*y for x,y in zip(mirrorAxisMultiply, moduleAttrsDict['module_transform_orientation'])]

                mirror_module_transform = moduleAttrsDict['mirror_module_Namespace']+':module_transform'
                cmds.setAttr(mirror_module_transform+'.rotate', *module_orientation_values)

                # We're not setting the translation for the mirror module transform here since it'll be updated
                # when the module transform on the other side is selected (the selection happens towards the
                # end of this function). The rotation channels for the module transform do not receive direction
                # connection for mirroring, and has to be updated manually. But they get updated automatically
                # during mirror move when manipulated in the UI / viewport.

                # You can set the translation here as well, no harm. But I'm not doing it here.

                # Set the mirror module transform attributes.
                for attr in module_transform_attrs:
                    cmds.setAttr(mirror_module_transform+'.'+attr, moduleAttrsDict[str(attr)])

            if moduleAttrsDict['num_nodes'] > 1:

                # Set values for node translations.
                for (node_translation, node_translation_value) in moduleAttrsDict['node_world_translation_values']:
                    node = moduleAttrsDict['module_Namespace']+':'+node_translation
                    selectionNodes.append(node)
                    cmds.xform(node, worldSpace=True, translation=node_translation_value)

                # Set values for orientation representations.
                for (orientation_node, node_orientation_value) in moduleAttrsDict['orientation_repr_values']:
                    node = '%s:%s' % (moduleAttrsDict['module_Namespace'], orientation_node)
                    attr = cmds.listAttr(node, keyable=True, visible=True, unlocked=True)[0]
                    cmds.setAttr(node+'.'+attr, node_orientation_value)

                    # Set the value for its mirror node separately.
                    if moduleAttrsDict['mirror_options'][0] == 'On':
                        mirrorNode = '%s:%s' % (moduleAttrsDict['mirror_module_Namespace'], orientation_node)
                        cmds.setAttr(mirrorNode+'.'+attr, node_orientation_value)

            if moduleAttrsDict['num_nodes'] == 1:   # Joint module with a single node.
                
                # Get the single orientation representation control for a joint module with a single node.
                node = moduleAttrsDict['module_Namespace']+':root_node_transform'
                orientation_repr = moduleAttrsDict['module_Namespace']+':single_orient_repr_transform'
                selectionNodes.append(node)
                
                # Set the node translation.
                cmds.xform(node, worldSpace=True, translation=moduleAttrsDict['node_world_translation_values'][0][1])
                
                # Set it's orientation.
                cmds.setAttr(orientation_repr+'.rotate', *moduleAttrsDict['orientation_repr_values'][0][1])

                # Set the value for orientation representation control's mirror.
                if moduleAttrsDict['mirror_options'][0] == 'On':
                    orientation_repr = moduleAttrsDict['mirror_module_Namespace']+':single_orient_repr_transform'
                    cmds.setAttr(orientation_repr+'.rotate', *moduleAttrsDict['orientation_repr_values'][0][1])


        if moduleAttrsDict['node_type'] == 'SplineNode':

            # Get the start and end module transforms.
            splineStartHandleTransform = moduleAttrsDict['module_Namespace']+':splineStartHandleTransform'
            splineEndHandleTransform = moduleAttrsDict['module_Namespace']+':splineEndHandleTransform'
            selectionNodes.extend([splineStartHandleTransform, splineEndHandleTransform])

            # Set their translations.
            cmds.setAttr(splineStartHandleTransform+'.translate', *moduleAttrsDict['splineStartHandleTransform_translation_values'])
            cmds.setAttr(splineEndHandleTransform+'.translate', *moduleAttrsDict['splineEndHandleTransform_translation_values'])
            
            # Set the start module transform attributes.
            splineStartHandleTransform_attrs = cmds.listAttr(splineStartHandleTransform, keyable=True, visible=True, unlocked=True)[3:]
            for attr in splineStartHandleTransform_attrs:
                try:cmds.setAttr(splineStartHandleTransform+'.'+attr, moduleAttrsDict[str(attr)])
                except: pass
            
            changeSplineJointOrientationType(moduleAttrsDict['module_Namespace'])

            # Set the mirror start module attributes.
            if moduleAttrsDict['mirror_options'][0] == 'On':

                mirror_splineStartHandleTransform = moduleAttrsDict['mirror_module_Namespace']+':splineStartHandleTransform'
                for attr in splineStartHandleTransform_attrs:
                    try:cmds.setAttr(mirror_splineStartHandleTransform+'.'+attr, moduleAttrsDict[str(attr)])
                    except: pass
                
                changeSplineJointOrientationType(moduleAttrsDict['mirror_module_Namespace'])

            # Set the translations for spline curve adjust transforms.
            for (splineAdjustCurve_transform, transform_value) in moduleAttrsDict['splineAdjustCurveTransformValues']:
                node = moduleAttrsDict['module_Namespace']+':'+splineAdjustCurve_transform
                selectionNodes.append(node)
                cmds.xform(node, worldSpace=True, translation=transform_value)


        if moduleAttrsDict['node_type'] == 'HingeNode':

            # Get the module transform.
            module_transform = moduleAttrsDict['module_Namespace']+':module_transform'
            selectionNodes.append(module_transform)

            # Set the translate / rotate for the module transform.
            cmds.setAttr(module_transform+'.translate', *moduleAttrsDict['module_translation_values'])
            cmds.setAttr(module_transform+'.rotate', *moduleAttrsDict['module_transform_orientation'])

            # Set the values for module transform attributes.
            module_transform_attrs = cmds.listAttr(module_transform, keyable=True, visible=True, unlocked=True)[6:]
            for attr in module_transform_attrs:
                cmds.setAttr(module_transform+'.'+attr, moduleAttrsDict[str(attr)])

            # If mirroring is enabled, get the rotation multipliers for the mirror module transform and set it.
            if moduleAttrsDict['mirror_options'][0] == 'On':

                # Apply rotation multipliers to mirror module transform.
                mirrorAxisMultiply = {'XY':[-1, -1, 1], 'YZ':[1, -1, -1], 'XZ':[-1, 1, -1]}[moduleAttrsDict['creation_plane'][-2:]]
                module_orientation_values = [x*y for x,y in zip(mirrorAxisMultiply, moduleAttrsDict['module_transform_orientation'])]

                # Get the mirror module transform and set its orientation.
                mirror_module_transform = moduleAttrsDict['mirror_module_Namespace']+':module_transform'
                cmds.setAttr(mirror_module_transform+'.rotate', *module_orientation_values)

                # Set the mirror module transform attributes.
                for attr in module_transform_attrs:
                    cmds.setAttr(mirror_module_transform+'.'+attr, moduleAttrsDict[str(attr)])

            # Set attributes for node translations.
            for (translation_node, node_translation_value) in moduleAttrsDict['node_world_translation_values']:
                node = '%s:%s_control' % (moduleAttrsDict['module_Namespace'], translation_node)
                selectionNodes.append(node)
                cmds.xform(node, worldSpace=True, translation=node_translation_value)

        # Select the control to be updated (in order for their mirror controls to be updated).
        if moduleAttrsDict['mirror_options'][0] == 'On':
            for node in selectionNodes:
                cmds.evalDeferred(partial(cmds.select, node, replace=True), lowestPriority=True)

    # Re-set the current namespace.
    cmds.namespace(setNamespace=currentNamespace)

    return modules

    

# -------------------------------------------------------------------------------------------------------------
#
#   RUNTIME FUNCTIONS (Or executing runtime functions)
#
# -------------------------------------------------------------------------------------------------------------

def moduleUtilitySwitchScriptJobs():
    '''
    Included as MRT startup function in userSetup file. Runs a scriptJob to trigger 
    runtime procedures during maya events.
    This definition is to be modified as necessary.
    '''
    # First, kill all previous jobs.
    forceToggleUtilScriptJobs(False)
    
    # To store the executed script jobs.
    jobs = []
    
    jobs.append(cmds.scriptJob(event=['SelectionChanged', moduleUtilitySwitchFunctions]))
    
    melGlobals['_mrt_utilJobList'] = jobs[:]


def forceToggleUtilScriptJobs(state=True):
    '''
    Allows you to forcibly kill or start the utility script jobs.
    '''
    # If toggle is enabled, restart the utility scriptJobs again.
    if state:
        moduleUtilitySwitchScriptJobs()
    else:
        utility_jobs = melGlobals['_mrt_utilJobList']
                
        if len(utility_jobs) > 0:

            for job in utility_jobs:
                if cmds.scriptJob(exists=job):
                    cmds.scriptJob(kill=job)
            
        melGlobals['_mrt_utilJobList'] = []


def moduleUtilitySwitchFunctions():      # This definition is to be modified as necessary.
    '''
    Runtime function called by scriptJob to assist in module operations.
    '''
    # Disable mirror operations
    deleteMirrorMoveConnections()

    # Toggle undo state
    cmds.undoInfo(stateWithoutFlush=False)

    # Get the current namespace, and set to root namespace
    currentNamespace = mel.eval('namespaceInfo -currentNamespace')
    cmds.namespace(setNamespace=':')

    # Get the current selection for modules, if any.
    selection = mel.eval("ls -sl -type dagNode")   # The cmds version returned minor bugs, when executed via a scriptJob. 
                                                   # Sometimes, it wouldn't take the boolean argument for 'selection'.
    selectedModuleNamespaces = []
    selectedMirrorModules = []
    selectedMirrorModuleNamespaces = []

    # If one of the modules in a mirrored module pairs are selected, select their mirrored pair as well.
    if selection:
        selection.reverse()

        for sel in selection:

            # Get the namespace of the selection, if a module is selected.
            namespaceInfo = stripMRTNamespace(sel)
            if namespaceInfo != None:
                selectedModuleNamespaces.append(namespaceInfo[0])

                # Select it mirrored module pair, if it exists (If the selected module is part of mirrored module pair)
                if cmds.attributeQuery('mirrorModuleNamespace', node=namespaceInfo[0]+':moduleGrp', exists=True):
                    selectedMirrorModules.append(sel)
                    selectedMirrorModuleNamespaces.append(namespaceInfo[0])

    # If valid modules are selected, perform operations on them as well.
    if len(selectedModuleNamespaces):

        # Based on the type of the selected module, do as follows
        lastSelectionNamespace = selectedModuleNamespaces[0]
        moduleType = returnModuleTypeFromNamespace(lastSelectionNamespace)

        # If a spline module node is selected
        if moduleType == 'SplineNode':

            # Smooth the display for the spline module curve
            cmds.displaySmoothness(lastSelectionNamespace+':splineNode_curve', pointsWire=32)

            # Execute a single-run scriptJob for changing the orientation type handles for its nodes 
            cmds.scriptJob(attributeChange=[lastSelectionNamespace+':splineStartHandleTransform.Node_Orientation_Type', \
                                        partial(changeSplineJointOrientationType, lastSelectionNamespace)], runOnce=True)

            # If the spline module has proxy geometry, execute a single-run scriptJob for modifying the proxy draw style
            # by using the attribute on the module transform
            if cmds.objExists(lastSelectionNamespace+':proxyGeometryGrp'):

                cmds.scriptJob(attributeChange=[lastSelectionNamespace+':splineStartHandleTransform.proxy_geometry_draw', \
                                        partial(changeSplineProxyGeometryDrawStyle, lastSelectionNamespace)], runOnce=True)


        # If a joint or hinge module node is selected
        if moduleType == 'JointNode' or moduleType == 'HingeNode':
            if cmds.objExists(lastSelectionNamespace+':proxyGeometryGrp'):
                cmds.scriptJob(attributeChange=[lastSelectionNamespace+':module_transform.proxy_geometry_draw', \
                                            partial(changeProxyGeometryDrawStyle, lastSelectionNamespace)], runOnce=True)

    if len(selectedMirrorModules):
        setupMirrorMoveConnections(selectedMirrorModules, selectedMirrorModuleNamespaces)

    # Set to the original namespace
    cmds.namespace(setNamespace=currentNamespace)
    cmds.undoInfo(stateWithoutFlush=True)


def setupMirrorMoveConnections(selections, moduleNamespaces):
    '''
    This function is called by moduleUtilitySwitchFunctions() to assist in manipulation of mirrored module pairs
    in the scene. Script jobs are executed for runtime functions to enable mirror movements.
    '''
    # To collect nodes created in this function. They'll be added to the mirror move container.
    collected_nodes = []
    
    # To collect the mirroring script jobs that are created
    jobNums = []

    for (selection, moduleNamespace) in zip(selections, moduleNamespaces):

        validSelection = returnValidSelectionFlagForModuleTransformObjects(selection)

        # If a valid module control object is selected, proceed.
        if validSelection:

            # Create the mirror move container
            if not cmds.objExists('MRT_mirrorMove_container'):
                cmds.createNode('container', name='MRT_mirrorMove_container', skipSelect=True)
            
            # Multiply divide node for translating mirror control objects
            mirrorTranslateMultiplyDivide = 'MRT_mirrorMove_translate__multiplyDivide'+'_'+moduleNamespace
            cmds.createNode('multiplyDivide', name=mirrorTranslateMultiplyDivide, skipSelect=True)
            cmds.setAttr(mirrorTranslateMultiplyDivide+'.input2', 1, 1, 1, type='double3')
            
            collected_nodes.append(mirrorTranslateMultiplyDivide)

            # Get the mirror module namespace and the mirror axis, which is based on the creation plane for the
            # mirrored module pair
            mirrorObject = cmds.getAttr(moduleNamespace+':moduleGrp.mirrorModuleNamespace')+':'+stripMRTNamespace(selection)[1]
            mirrorAxis = {'XY':'Z', 'YZ':'X', 'XZ':'Y'}[str(cmds.getAttr(moduleNamespace+':moduleGrp.onPlane'))[1:]]

            # Get the number of attributes on the selected control
            selectionAttrs = cmds.listAttr(selection, keyable=True, visible=True, unlocked=True)

            # Based on the number of attributes on the selected control, affect the mirror attributes.
            if len(selectionAttrs) == 1: # A Joint module orientation representation control ?
                if re.match('^MRT_\D+__\w+:[_0-9a-z]*transform_orientation_repr_transform$', selection):
                    
                    jobNums.append(cmds.scriptJob(attributeChange=[str(selection+'.'+selectionAttrs[0]), \
                    partial(updateOrientationReprTransformForMirrorMove, selection, mirrorObject, selectionAttrs[0], \
                                                                                                            moduleNamespace)]))
                else:
                    jobNums.append(cmds.scriptJob(attributeChange=[str(selection+'.'+selectionAttrs[0]), \
                                      partial(updateChangedAttributeForMirrorMove, selection, mirrorObject, selectionAttrs[0])]))


            if len(selectionAttrs) == 3: # A translate / rotate control ?

                if 'translate' in selectionAttrs[0]:
                    
                    # Get the number of nodes in the module.
                    numNodes = cmds.getAttr(moduleNamespace+':moduleGrp.numberOfNodes')
                    
                    # For JointNode module.
                    if 'JointNode' in moduleNamespace:
                        
                        # Get the mirror rotation function.
                        orient_func = cmds.getAttr(moduleNamespace+':moduleGrp.mirrorRotation')
                        
                        if orient_func == 'Behaviour':
                            # All the axes are opposite, except the one which is mirror axis.
                            # Set the multipliers for all axes by -1. The mirror axis will be set to
                            # mirror the translation as well.
                            direction_mult = {'X':-1, 'Y':-1, 'Z':-1}
                            
                        else: # If orient_func is 'Local_Orientation'.
                            direction_mult = {'X':1, 'Y':1, 'Z':1}
                            
                            # Get the local axis for the selection which is aligned with the mirror axis.
                            # For a JointNode module with more than one node, it'll be the node up axis. 
                            # This is specified during module creation (remember?). Multiply the local axis 
                            # which aligns with the mirror axis (its multiplier) by -1, since it will have 
                            # mirror translation values.
                            if numNodes > 1:
                                nodeUpAxis = cmds.getAttr(moduleNamespace+':moduleGrp.nodeOrient')[1]
                                direction_mult[nodeUpAxis] = direction_mult.get(nodeUpAxis) * -1
                            else:
                                # For a JointNode module with a single node, the node has world orientation.
                                # Just multiply the world axis by -1 which is the mirror axis.
                                direction_mult[mirrorAxis] = direction_mult.get(mirrorAxis) * -1
                            
                    else: # For SplineNode module and HingeNode module.

                        # Get the default multipliers for mirror translation.
                        direction_mult = {'X':1, 'Y':1, 'Z':1}
                    
                        # Multiply the translate axis along the mirror axis by -1 to get mirror translation.
                        direction_mult[mirrorAxis] = direction_mult.get(mirrorAxis) * -1
                    
                    # Connect the source translation with the mirror multiplier node.
                    cmds.connectAttr(selection+'.translate', mirrorTranslateMultiplyDivide+'.input1')
                    
                    # Now set the final multipliers.
                    cmds.setAttr(mirrorTranslateMultiplyDivide+'.input2X', direction_mult['X'])
                    cmds.setAttr(mirrorTranslateMultiplyDivide+'.input2Y', direction_mult['Y']) 
                    cmds.setAttr(mirrorTranslateMultiplyDivide+'.input2Z', direction_mult['Z']) 
                    cmds.connectAttr(mirrorTranslateMultiplyDivide+'.output', mirrorObject+'.translate')
                    
                    collected_nodes.append(cmds.listConnections(mirrorTranslateMultiplyDivide, source=True, destination=True, \
                                                                                                    type='unitConversion'))                    


                if 'rotate' in selectionAttrs[0]:
                    jobNums.append(cmds.scriptJob(attributeChange=[str(selection+'.'+selectionAttrs[0]), \
                                        partial(updateChangedAttributeForMirrorMove, selection, mirrorObject, selectionAttrs[0])]))
                    jobNums.append(cmds.scriptJob(attributeChange=[str(selection+'.'+selectionAttrs[1]), \
                                        partial(updateChangedAttributeForMirrorMove, selection, mirrorObject, selectionAttrs[1])]))
                    jobNums.append(cmds.scriptJob(attributeChange=[str(selection+'.'+selectionAttrs[2]), \
                                        partial(updateChangedAttributeForMirrorMove, selection, mirrorObject, selectionAttrs[2])]))


            if re.match('^MRT_\D+__\w+:splineStartHandleTransform$', selection): # A splineStartHandleTransform control ?

                cmds.connectAttr(selection+'.translate', mirrorTranslateMultiplyDivide+'.input1')
                cmds.connectAttr(mirrorTranslateMultiplyDivide+'.output', mirrorObject+'.translate')
                collected_nodes.append(cmds.listConnections(mirrorTranslateMultiplyDivide, source=True, destination=True, \
                                                                                                        type='unitConversion'))
                cmds.setAttr(mirrorTranslateMultiplyDivide+'.input2'+mirrorAxis, -1)

                for attr in selectionAttrs[3:]:
                    jobNums.append(cmds.scriptJob(attributeChange=[str(selection+'.'+attr), \
                                                    partial(updateChangedAttributeForMirrorMove, selection, mirrorObject, attr)]))
                # Node orientation type on spline module
                jobNums.append(cmds.scriptJob(attributeChange=[str(selection+'.Node_Orientation_Type'), \
                    partial(changeSplineJointOrientationType_forMirror, moduleNamespace, \
                                                        cmds.getAttr(moduleNamespace+':moduleGrp.mirrorModuleNamespace'))]))

                # Proxy geometry
                if 'proxy_geometry_draw' in selectionAttrs:
                    jobNums.append(cmds.scriptJob(attributeChange=[str(selection+'.proxy_geometry_draw'), \
                        partial(changeSplineProxyGeometryDrawStyleForMirror, moduleNamespace, \
                                                        cmds.getAttr(moduleNamespace+':moduleGrp.mirrorModuleNamespace'))]))


            if re.match('^MRT_\D+__\w+:module_transform$', selection): # Module transform ?

                cmds.connectAttr(selection+'.translate', mirrorTranslateMultiplyDivide+'.input1')
                cmds.connectAttr(mirrorTranslateMultiplyDivide+'.output', mirrorObject+'.translate')
                collected_nodes.append(cmds.listConnections(mirrorTranslateMultiplyDivide, source=True, destination=True, \
                                                                                                        type='unitConversion'))
                cmds.setAttr(mirrorTranslateMultiplyDivide+'.input2'+mirrorAxis, -1)

                # Set multipliers for mirroring module transform values
                multipliersFromMirrorAxis = {'X':[1, -1, -1], 'Y':[-1, 1, -1], 'Z':[-1, -1, 1]}[mirrorAxis]

                for (i, multiplier) in zip([3, 4, 5], multipliersFromMirrorAxis):
                    jobNums.append(cmds.scriptJob(attributeChange=[str(selection+'.'+selectionAttrs[i]), \
                                partial(updateChangedAttributeForMirrorMove, selection, mirrorObject, selectionAttrs[i], multiplier)]))

                for attr in selectionAttrs[6:]:
                    jobNums.append(cmds.scriptJob(attributeChange=[str(selection+'.'+attr), \
                                        partial(updateChangedAttributeForMirrorMove, selection, mirrorObject, attr)]))
                # Proxy geometry
                if 'proxy_geometry_draw' in selectionAttrs:
                    jobNums.append(cmds.scriptJob(attributeChange=[str(selection+'.proxy_geometry_draw'), \
                        partial(changeProxyGeometryDrawStyleForMirror, moduleNamespace, \
                                                        cmds.getAttr(moduleNamespace+':moduleGrp.mirrorModuleNamespace'))]))
            
            # Update the mirror move container
            addNodesToContainer('MRT_mirrorMove_container', collected_nodes, includeHierarchyBelow=True)
            
            melGlobals['_mrt_utilJobList'] = melGlobals['_mrt_utilJobList'] + jobNums
            

def deleteMirrorMoveConnections():
    '''
    Kills all scriptJobs required for mirror move operations for modules,
    removes container for mirror nodes.
    '''
    # Toggle undo state
    cmds.undoInfo(stateWithoutFlush=False)
    
    # Delete mirror nodes
    if cmds.objExists('MRT_mirrorMove_container'):
        cmds.delete('MRT_mirrorMove_container')

    cmds.undoInfo(stateWithoutFlush=True)


def updateChangedAttributeForMirrorMove(selection, mirrorObject, attribute, multiplier=None):
    '''
    This function is called by a scriptJob to affect a control's mirror attributes where the
    control is a part of a mirrored module pair. Used in setupMirrorMoveConnections().
    '''
    # Get the value of a control's attribute
    value = cmds.getAttr(selection+'.'+attribute)

    # If a multiplier is passed-in, use it.
    if multiplier:
        value = value * multiplier

    # Affect the mirror control attribute.
    cmds.setAttr(mirrorObject+'.'+attribute, value)


def updateOrientationReprTransformForMirrorMove(selection, mirrorObject, attribute, namespace):
    '''
    This function is called by a scriptJob when "orientation_repr_transform" control
    for a mirrored joint module is selected. It mirrors the rotation of the aim axis movement
    of the control to its mirror. Used in setupMirrorMoveConnections().
    '''
    # Get the value of the "orientation repr transform" control aim axis rotation.
    value = cmds.getAttr(selection+'.'+attribute)

    # Set the rotation according to the mirror function.
    if cmds.getAttr(namespace+':moduleGrp.mirrorRotation') == 'Behaviour':
        mirrorAxes = cmds.getAttr(namespace+':moduleGrp.onPlane')[1:]
        mirrorAxes = list(mirrorAxes)
        if attribute[-1] in mirrorAxes:
            cmds.setAttr(mirrorObject+'.'+attribute, value*-1)
        else:
            cmds.setAttr(mirrorObject+'.'+attribute, value)
    else:
        cmds.setAttr(mirrorObject+'.'+attribute, value)


def changeSplineJointOrientationType(moduleNamespace):
    '''
    Executed by scriptJob to modify the spline node orientation type by modifying the "Node_Orientation_Type"
    attribute on the spline module start transform.
    '''
    selection = mel.eval('ls -sl -type dagNode')

    cmds.lockNode(moduleNamespace+':module_container', lock=False, lockUnpublished=False)

    # If the node orientation type is set to 'World' 
    if cmds.getAttr(moduleNamespace+':splineStartHandleTransform.Node_Orientation_Type') == 0:

        cmds.setAttr(moduleNamespace+':splineStartHandleTransform.Axis_Rotate', 0, keyable=False)
        node_transform_Grp = moduleNamespace+':moduleNodesGrp'
        node_transform_Grp_allChildren = cmds.listRelatives(node_transform_Grp, allDescendents=True, type='joint')
        for transform in node_transform_Grp_allChildren:
            cmds.setAttr(transform+'_pairBlend.rotateMode', 1)

    # IF the node orientation type is set to 'Object'
    if cmds.getAttr(moduleNamespace+':splineStartHandleTransform.Node_Orientation_Type') == 1:

        cmds.setAttr(moduleNamespace+':splineStartHandleTransform.Axis_Rotate', keyable=True)
        node_transform_Grp = moduleNamespace+':moduleNodesGrp'
        node_transform_Grp_allChildren = cmds.listRelatives(node_transform_Grp, allDescendents=True, type='joint')
        for transform in node_transform_Grp_allChildren:
            cmds.setAttr(transform+'_pairBlend.rotateMode', 2)

    cmds.lockNode(moduleNamespace+':module_container', lock=True, lockUnpublished=True)
    cmds.select(selection)


def changeSplineJointOrientationType_forMirror(moduleNamespace, mirrorModuleNamespace): 
    '''
    Executed when one of the mirrored module pairs of a spline module is modified. 
    Called in setupMirrorMoveConnections() by a scriptJob. Modifies the spline node orientation type 
    on modules in a mirrored module pair for a selected spline module (part of the pair).
    '''
    selection = mel.eval('ls -sl -type dagNode')

    cmds.lockNode(moduleNamespace+':module_container', lock=False, lockUnpublished=False)
    cmds.lockNode(mirrorModuleNamespace+':module_container', lock=False, lockUnpublished=False)

    if cmds.getAttr(moduleNamespace+':splineStartHandleTransform.Node_Orientation_Type') == 0:

        cmds.setAttr(moduleNamespace+':splineStartHandleTransform.Axis_Rotate', 0, keyable=False)
        cmds.setAttr(mirrorModuleNamespace+':splineStartHandleTransform.Axis_Rotate', 0, keyable=False)

        node_transform_Grp = moduleNamespace+':moduleNodesGrp'
        node_transform_Grp_allChildren = cmds.listRelatives(node_transform_Grp, allDescendents=True, type='joint')
        for transform in node_transform_Grp_allChildren:
            cmds.setAttr(transform+'_pairBlend.rotateMode', 1)

        node_transform_Grp = mirrorModuleNamespace+':moduleNodesGrp'
        node_transform_Grp_allChildren = cmds.listRelatives(node_transform_Grp, allDescendents=True, type='joint')
        for transform in node_transform_Grp_allChildren:
            cmds.setAttr(transform+'_pairBlend.rotateMode', 1)

    if cmds.getAttr(moduleNamespace+':splineStartHandleTransform.Node_Orientation_Type') == 1:

        cmds.setAttr(moduleNamespace+':splineStartHandleTransform.Axis_Rotate', keyable=True)
        cmds.setAttr(mirrorModuleNamespace+':splineStartHandleTransform.Axis_Rotate', keyable=True)

        node_transform_Grp = moduleNamespace+':moduleNodesGrp'
        node_transform_Grp_allChildren = cmds.listRelatives(node_transform_Grp, allDescendents=True, type='joint')
        for transform in node_transform_Grp_allChildren:
            cmds.setAttr(transform+'_pairBlend.rotateMode', 2)

        node_transform_Grp = mirrorModuleNamespace+':moduleNodesGrp'
        node_transform_Grp_allChildren = cmds.listRelatives(node_transform_Grp, allDescendents=True, type='joint')
        for transform in node_transform_Grp_allChildren:
            cmds.setAttr(transform+'_pairBlend.rotateMode', 2)

    cmds.lockNode(moduleNamespace+':module_container', lock=True, lockUnpublished=True)
    cmds.lockNode(mirrorModuleNamespace+':module_container', lock=True, lockUnpublished=True)
    cmds.select(selection)


def changeProxyGeometryDrawStyle(moduleNamespace):
    '''
    Toggle the transparency (vertex) draw style for the module proxy geometry, if it exists.
    This function is executed by a scriptJob. See moduleUtilitySwitchFunctions().
    '''
    proxyGeoGrp = moduleNamespace + ':proxyGeometryGrp'
    allChildren = cmds.listRelatives(proxyGeoGrp, allDescendents=True, type='transform')

    proxy_geo_transforms = [item for item in allChildren if str(item).rpartition('geo')[2] == '']

    if cmds.getAttr(moduleNamespace+':module_transform.proxy_geometry_draw') == 1:
        for transform in proxy_geo_transforms:
            cmds.polyColorPerVertex(transform+'.vtx[*]', alpha=0.3, rgb=[0.663, 0.561, 0.319], notUndoable=True, \
                                                                                           colorDisplayOption=True)

    if cmds.getAttr(moduleNamespace+':module_transform.proxy_geometry_draw') == 0:
        for transform in proxy_geo_transforms:
            cmds.polyColorPerVertex(transform+'.vtx[*]', alpha=1.0, rgb=[0.663, 0.561, 0.319], notUndoable=True, \
                                                                                           colorDisplayOption=True)

    cmds.select(moduleNamespace+':module_transform', replace=True)


def changeProxyGeometryDrawStyleForMirror(moduleNamespace, mirrorModuleNamespace):
    '''
    Toggle the transparency (vertex) draw style for proxy geometry for a mirrored module pair.
    This function is executed by a scriptJob. See setupMirrorMoveConnections().
    '''
    if cmds.getAttr(moduleNamespace+':module_transform.proxy_geometry_draw') == 1:

        for namespace in (moduleNamespace, mirrorModuleNamespace):

            proxyGeoGrp = namespace + ':proxyGeometryGrp'
            allChildren = cmds.listRelatives(proxyGeoGrp, allDescendents=True, type='transform')

            proxy_geo_transforms = [item for item in allChildren if str(item).rpartition('geo')[2] == '']

            for transform in proxy_geo_transforms:
                cmds.polyColorPerVertex(transform+'.vtx[*]', alpha=0.3, rgb=[0.663, 0.561, 0.319], notUndoable=True, \
                                                                                              colorDisplayOption=True)

    if cmds.getAttr(moduleNamespace+':module_transform.proxy_geometry_draw') == 0:

        for namespace in (moduleNamespace, mirrorModuleNamespace):

            proxyGeoGrp = namespace + ':proxyGeometryGrp'
            allChildren = cmds.listRelatives(proxyGeoGrp, allDescendents=True, type='transform')

            proxy_geo_transforms = [item for item in allChildren if str(item).rpartition('geo')[2] == '']

            for transform in proxy_geo_transforms:
                cmds.polyColorPerVertex(transform+'.vtx[*]', alpha=1, rgb=[0.663, 0.561, 0.319], notUndoable=True, \
                                                                                            colorDisplayOption=True)

def changeSplineProxyGeometryDrawStyle(moduleNamespace):
    '''
    Toggle the transparency (vertex) draw style for a spline module proxy geometry, if it exists.
    This function is executed by a scriptJob. See moduleUtilitySwitchFunctions().
    '''
    proxyGeoGrp = moduleNamespace + ':proxyGeometryGrp'
    allChildren = cmds.listRelatives(proxyGeoGrp, allDescendents=True, type='transform')

    proxy_geo_transforms = [item for item in allChildren if str(item).rpartition('geo')[2] == '']

    if cmds.getAttr(moduleNamespace+':splineStartHandleTransform.proxy_geometry_draw') == 1:

        for transform in proxy_geo_transforms:
            cmds.polyColorPerVertex(transform+'.vtx[*]', alpha=0.3, rgb=[0.663, 0.561, 0.319], notUndoable=True, \
                                                                                           colorDisplayOption=True)

    if cmds.getAttr(moduleNamespace+':splineStartHandleTransform.proxy_geometry_draw') == 0:

        for transform in proxy_geo_transforms:
            cmds.polyColorPerVertex(transform+'.vtx[*]', alpha=1.0, rgb=[0.663, 0.561, 0.319], notUndoable=True, \
                                                                                           colorDisplayOption=True)

    cmds.select(moduleNamespace+':splineStartHandleTransform', replace=True)


def changeSplineProxyGeometryDrawStyleForMirror(moduleNamespace, mirrorModuleNamespace):
    '''
    Toggle the transparency (vertex) draw style for proxy geometry for a mirrored spline module pair.
    This function is executed by a scriptJob. See setupMirrorMoveConnections().
    '''
    if cmds.getAttr(moduleNamespace+':splineStartHandleTransform.proxy_geometry_draw') == 1:

        for namespace in (moduleNamespace, mirrorModuleNamespace):

            proxyGeoGrp = namespace + ':proxyGeometryGrp'
            allChildren = cmds.listRelatives(proxyGeoGrp, allDescendents=True, type='transform')

            proxy_geo_transforms = [item for item in allChildren if str(item).rpartition('geo')[2] == '']

            for transform in proxy_geo_transforms:
                cmds.polyColorPerVertex(transform+'.vtx[*]', alpha=0.3, rgb=[0.663, 0.561, 0.319], notUndoable=True, \
                                                                                              colorDisplayOption=True)
    if cmds.getAttr(moduleNamespace+':splineStartHandleTransform.proxy_geometry_draw') == 0:

        for namespace in (moduleNamespace, mirrorModuleNamespace):

            proxyGeoGrp = namespace + ':proxyGeometryGrp'
            allChildren = cmds.listRelatives(proxyGeoGrp, allDescendents=True, type='transform')

            proxy_geo_transforms = [item for item in allChildren if str(item).rpartition('geo')[2] == '']

            for transform in proxy_geo_transforms:
                cmds.polyColorPerVertex(transform+'.vtx[*]', alpha=1, rgb=[0.663, 0.561, 0.319], notUndoable=True, \
                                                                                            colorDisplayOption=True)

