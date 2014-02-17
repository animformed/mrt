# *************************************************************************************************************
#
#    mrt_functions.py - Source for all utility / scene / runtime functions. 
#                       Also includes startup functions to verify MRT is correctly installed and supported.
#
#    Feel free to modify or copy (or whatever) for your own purpose :)
#
#    Written by Himanish Bhattacharya.
#
# *************************************************************************************************************

import maya.cmds as cmds
import maya.
import maya.mel as mel

from functools import partial    # Alternative "from pymel.core.windows import Callback"
import os, math, sys, re, glob, shutil


__MRT_utility_tempScriptJob_list = [] # Could've used optionVar for this, best option is melGlobals.
                                      # But this is just me.

# -------------------------------------------------------------------------------------------------------------
#
#   STARTUP FUNCTIONS
#
# -------------------------------------------------------------------------------------------------------------

def prep_MRTMayaStartupActions():
    """
    Executed as startup utility function to check if MRT is correctly configured with maya startup.
    It checks for maya.env and the valid userSetup file in maya scripts directory. 

    It adds necessary string values / variables to the maya userSetup file if it doesn't exist.

    It also modifies the "MAYA_PLUG_IN_PATH" variable. It appends necessary string value to it if it
    exists.
    """
    # Get the current userSetup.* file path with the extension.
    userSetup_return = find_userSetupFileStatus()
    userSetupStatus = False     # If userSetup is written or modified, set it to True. 

    # Open the userSetup file and check if the string value exists and write if needed.

    userSetup_return = userSetup_return.lower()

    if userSetup_return.endswith('mel'):

        userSetupFile = open(userSetup_return, 'a+')
        startString = '//MRT_STARTUP//'
        writeString = '\n' + startString + '\npython("try:\\n\\timport MRT.mrt_functions as mfunc\\nexcept \
        ImportError:\\n\\tpass\\nelse:\\n\\tmfunc.runDeferredFunction_wrapper(mfunc.moduleUtilitySwitchScriptJob)\\n");'

        stringList = [string.strip() for string in userSetupFile.readlines()]

        if not startString in stringList:
            userSetupFile.write(writeString)
            userSetupStatus = True

        userSetupFile.close()

    if userSetup_return.endswith('py'):

        userSetupFile = open(userSetup_return, 'a+')
        startString = '#MRT_STARTUP#'
        writeString = '\n' + startString + '\ntry:\n\timport MRT.mrt_functions as mfunc\nexcept \
        ImportError:\n\tpass\nelse:\n\tmfunc.runDeferredFunction_wrapper(mfunc.moduleUtilitySwitchScriptJob)\n'

        stringList = [string.strip() for string in userSetupFile.readlines()]

        if not startString in stringList:
            userSetupFile.write(writeString)
            userSetupStatus = True

        userSetupFile.close()

    # If not userSetup file, create a default with "mel" extension.
    if userSetup_return.endswith('scripts/'):

        userSetupFile = open(userSetup_return+'userSetup.mel', 'a')
        userSetupFile.write('//MRT_STARTUP//\npython("try:\\n\\timport MRT.mrt_functions as mfunc\\nexcept \
        ImportError:\\n\\tpass\\nelse:\\n\\tmfunc.runDeferredFunction_wrapper(mfunc.moduleUtilitySwitchScriptJob)\\n");')

        userSetupStatus = True

        userSetupFile.close()


    # Check for maya.env status, and then modify it later.

    mayaEnv_return = returnEnvPluginPathStatus()
    mayaEnvStatus = False    # If maya.env is to be written or modified, set it to True.

    # Store the string value to be added to "MAYA_PLUG_IN_PATH".
    envString = cmds.internalVar(userScriptDir=True) + 'MRT/plugin/'

    # Get the os separator string for env paths.
    if os.name == 'nt':
        pathSeparator = ';'
    if os.name == 'posix':
        pathSeparator = ':'  
    # Line to be added in future for mac "darwin".

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
            writeString = 'MAYA_PLUG_IN_PATH = '+pathSeparator.join(pathList) + pathSeparator
            mayaEnvStatus = True

    if not mayaEnv_return:        # '' or None
        writeString = 'MAYA_PLUG_IN_PATH = %s'%(envString) + pathSeparator
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
                    tempEnvFile.write(line.strip())

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
    """
    Checks and returns the plugin path for the 'MAYA_PLUG_IN_PATH' string value in the maya.env file. 
    Can be modified to work with os.getenv('MAYA_PLUG_IN_PATH') as well.
    """
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

    return plugPaths


def prep_MRTcontrolRig_source():
    """
    Executed at startup to combine the .py sources under "userControlClasses" with "mrt_controlRig_src.py"
    as "mrt_controlRig.py", which is then imported and used.
    """
    # Remove any existing sources
    cleanup_MRT_actions()

    # Path to custom control classes.
    path = cmds.internalVar(userScriptDir=True) + 'MRT/userControlClasses/'

    # Get a list of all user custom control class files.
    f_list = set([item for item in os.listdir(path) if re.match('^controlClass_\w+.py$', item)])

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
    """
    Checks if a 'userSetup' file exists under the user script directory.
    If found, return its full path name with its extension.
    If only 'mel' or 'py' is found, return it. If both, return 'mel'.
    """
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

def cleanup_MRT_actions(jobNum=None):
    """
    Cleans up any temporary .py or .pyc during startup or scene use.
    Modify as necessary.
    """
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
    """
    Separates an input string name if it has a namespace defined by MRT.
    It returns the namespace and the object name.
    """
    if re.match('^MRT_\D+__\w+:\w+$', moduleName):
        namespaceInfo = str(moduleName).partition(':')

        return namespaceInfo[0], namespaceInfo[2]

    return None


def returnMRT_Namespaces(names):
    """
    Returns all current namespaces in the scene defined by MRT.
    """
    MRT_namespaces = []

    for name in names:
        if re.match('^MRT_\D+__\w+$', name):
            MRT_namespaces.append(str(name))

    if len(MRT_namespaces) > 0:
        return MRT_namespaces

    return None


def findHighestNumSuffix(baseName, names):
    """
    Find and return the max numerical suffix value separated by underscore(s) for a given string name.
    """
    highestValue = 1

    for name in names:

        if re.match('^%s_*\d+$' % baseName, name):
            suffix = re.split('_*', name)[-1]
            numSuffix = int(suffix)

            if numSuffix > highestValue:
                highestValue = numSuffix

    return highestValue


def findHighestCommonTextScrollListNameSuffix(baseName, names):
    """
    Find and return the max numerical suffix in brackets (num) in textScrollList list names,
    with a common first name. This numerical suffix is added to make them unique.
    Eg:
    Name(2)
    Name(4)
    """
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
    """
    Returns a tuple of two lists for a given list of namespaces. 

    A module's namespace has two parts,    one defined by MRT and the other defined by the user, 
    separated by an "__". The first list contains substrings for the namespaces defined by MRT 
    and the second list containing substring names defined by user,for the passed-in namespaces.
    """
    userSpecifiedNames = []
    strippedNamespaces = []

    for namespace in namespaces:
        userSpecifiedNames.append(namespace.rpartition('__')[2])
        strippedNamespaces.append(namespace.rpartition('__')[0])

    return strippedNamespaces, userSpecifiedNames


def returnVectorMagnitude(transform_start, transform_end):
    """
    Calculates and returns the magnitude for the input vector, with the arguments for
    start position for input vector and the end position for input vector.
    """
    transform_vector = map(lambda x,y: x-y, transform_start, transform_end)  # transform_start -> transform_end
    transform_vector_magnitude = math.sqrt(reduce(lambda x,y: x+y, [component**2 for component in transform_vector]))

    return transform_vector_magnitude


def returnCrossProductDirection(transform1_start, transform1_end, transform2_start, transform2_end, normalize=False):
    """
    Calculates and returns the cross-product data for two input vectors. It has arguments for,
    transform1_start -> Start position for vector 1.
    transform1_end -> End position for vector 1.
    transform2_start -> Start position for vector 2.
    transform2_end -> End position for vector 2.
    normalize -> Normalize the input vectors to unit vectors.

    It returns a tuple (the sine value between two input vectors <float>, 
                        cross product vector <list(3) with floats>, 
                        magnitude of cross product vector <float>)
    """
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
    """
    Calculates and returns the dot-product direction for two input vectors. It has arguments for,
    transform1_start -> Start position for vector 1.
    transform1_end -> End position for vector 1.
    transform2_start -> Start position for vector 2.
    transform2_end -> End position for vector 2.
    normalize -> Normalize the input vectors to unit vectors.

    It returns a tuple (the cosine value between two input vectors <float>, magnitude of dot product vector <float>)
    """
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
    """
    Calculates and returns a new position with respect to two input vector positions, based on the parameter value.
    It has the following arguments:
    startVector -> Vector position 1.
    endVector -> Vector position 2.
    parameter -> If parameter is 0.5, the function returns the mid position between the two input vectors. 
                 If the parameter is 0, the function returns the position of the first input vector, and so on.
    It returns a vector, <list(3) with floats>
    """
    direction_vec = map(lambda x,y:x-y, endVector, startVector)

    # Calculate the offset vector on the line represented by the two input vectors.
    off_vec = map(lambda x,y:x+(y*parameter), startVector, direction_vec)

    return off_vec


def returnModuleTypeFromNamespace(namespace):
    """
    Return the type of a module from it namespace.
    Eg., "MRT_HingeNode__module1:" will return "HingeNode" 
    """
    firstPart = namespace.partition('__')[0]
    moduleType = firstPart.partition('_')[2]

    return moduleType


def loadXhandleShapePlugin():
    """
    Checks and loads the xHandleShape plugin. It finds the correct plugin from the built versions for the 
    current session of maya and os if supported and makes a copy to the plug-in search path.

    It returns a bool if it successfully loads the plugin.

    To be modified for future updates and add mac support ?
    """
    maya_ver = returnMayaVersion()

    if maya_ver > 2014:
        cmds.warning('MRT is not supported on this version of Maya. Aborting.')
        return False
    if maya_ver < 2011:
        cmds.warning('MRT is not supported on this version of Maya. Aborting.')
        return False

    pluginBasePath = cmds.internalVar(userScriptDir=True) + 'MRT/plugin/'

    # Find the correct plugin built version.
    if os.name == 'nt':
        plugin_source_path = pluginBasePath + '/builds/windows/mrt_xhandleShape_m%sx64.mll'%(maya_ver)
        plugin_dest_path = pluginBasePath + 'mrt_xhandleShape.mll'

    elif os.name == 'posix':
        plugin_source_path = pluginBasePath + '/builds/linux/mrt_xhandleShape_m%sx64.so'%(maya_ver)
        plugin_dest_path = pluginBasePath + 'mrt_xhandleShape.so'

    else:
        cmds.warning('MRT is not supported on \"'+os.name+'\" platform. Aborting.')
        return False

    # Copy to plugin path and then load it.
    try:
        if not cmds.pluginInfo(plugin_dest_path, query=True, loaded=True):
            shutil.copy2(plugin_source_path, plugin_dest_path)

    except IOError:
        cmds.warning('Error: MRT cannot write to plugin path. Aborting.')
        return False

    finally:
        cmds.loadPlugin(plugin_dest_path, quiet=True)

    return True


def selection_sort_by_length(list_sequence):
    """
    Sorts a given sequence list (list of lists) by their length. In place sort.
    """
    for i in xrange(0, len(list_sequence)):
        min_index = i
        for j in xrange(i+1, len(list_sequence)):
            if len(list_sequence[min_index]) > len(list_sequence[j]):
                min_index = j
        list_sequence[i] = list_sequence[min_index]
        list_sequence[min_index] = list_sequence[i]


def runDeferredFunction_wrapper(function):
    """
    Execute a given function during CPU idle time.
    """
    # DEPRECATED #
    # global _eval__Function
    # _eval__Function = function
    # global _eval__Return
    # cmds.evalDeferred("mrt_sceneUtils._eval__Return = mrt_sceneUtils._eval__Function()", lowestPriority=True)
    import maya.utils
    maya.utils.executeDeferred(function)


def returnValidSelectionFlagForModuleTransformObjects(selection):
    """
    Checks a selection for a valid module object created by MRT.
    """
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
                    re.compile('^MRT_\D+__\w+:single_orientation_representation_transform$'),
                    re.compile('^MRT_\D+__\w+:[_0-9a-z]*transform_orientation_representation_transform$')]

    for matchObject in matchObjects:

        matchResult = matchObject.match(selection)

        if matchResult:
            return True

    return False


def concatenateCommonNamesFromHierarchyData(data, commonNames=[]):
    """
    This function works upon the hierarchy data returned by traverseParentModules() or traverseChildrenModules().
    It collects all object names uniquely in a mutable sequence (list) passed-in as an argument. 
    """
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


# -------------------------------------------------------------------------------------------------------------
#
#   SCENE FUNCTIONS
#
# -------------------------------------------------------------------------------------------------------------

def returnHierarchyTreeListStringForCustomControlRigging(rootJoint, prefix='', prettyPrint=True):
    """
    Returns a string value depicting the hierarchy tree list of all joints from a given root joint. 
    For more description, see the comments for "CustomLegControl" class in "mrt_controlRig_src.py".

    Returns string with following layout for a valid root joint with prettyPrint set to True:

    Each child joint is indented with a tab space.

    <HingeNode>_root_node_transform
        <HingeNode>_node_1_transform
            <HingeNode>_end_node_transform
                <JointNode>_root_node_transform
                <JointNode>_root_node_transform
                    <JointNode>_end_node_transform
    """
    if prettyPrint:
        newLine = '\n'
        tabLine = '\t'
    else:
        newLine = '\\n'
        tabLine = '\\t'

    # Stores the string attributes for the passed-in joint name
    jh_string = '%s<%s>%s%s'%(prefix, cmds.getAttr(rootJoint+'.inheritedNodeType'), \
                re.split('(_root_node_transform|_end_node_transform|_node_\d+_transform)', rootJoint)[1], newLine)

    # Check the joint for multiple children. If they have further descendents, search recursively and collect 
    # their joint name attributes if the passed-in joint has only a single child joint.

    children = cmds.listRelatives(rootJoint, children=True, type='joint')

    while children:

        prefix = prefix + tabLine

        if len(children) == 1:

            # Append the child joint name attributes.
            jh_string += '%s<%s>%s%s'%(prefix, cmds.getAttr(children[0]+'.inheritedNodeType'), \
                re.split('(_root_node_transform|_end_node_transform|_node_\d+_transform)', children[0])[1], newLine)

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
                    jh_string += returnHierarchyTreeListStringForCustomControlRigging(child, prefix, prettyPrint=prettyPrint)

                break

    return jh_string


def returnRootForCharacterHierarchy(joint):
    """
    Returns the string name of the root joint of a joint hierarchy in a character for a given joint name, 
    which is part of the hierarchy.
    """
    rootJoint = ''

    # The cmds version returned occasional errors stating incorrect boolean value with parent flag, if
    # this function was used in a scriptJob event call. Not sure why.
    # parentJoint = cmds.listRelatives(joint, parent=True, type='joint')  <-- What's wrong with you??

    parentJoint = mel.eval('listRelatives -parent -type joint '+joint)

    if parentJoint and parentJoint[0].endswith('_transform'):
        rootJoint = returnRootForCharacterHierarchy(parentJoint[0])
    else:
        rootJoint = joint

    return rootJoint


def returnAxesInfoForFootTransform(transform, foot_vec_dict):
    """
    This function is used to gather data for a transform's orientation for its use 
    with a reverse IK foot/leg configuration.

    For a given transform with its orientation, return the following data:

    1) Calculate its nearest axis crossing the length of the foot
    2) Calculate its nearest axis along the aim of the foot.
    3) Calculate its nearest axis along the length of the leg.

    Also return the cosine between the nearest axis.
    """
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
    """
    Called during CPU idle time to perform post tasks. Can be modified to include more tasks.
    Useful in iterations.
    """
    cmds.select(clear=True)


def moveSelectionOnIdle(selection, translation_values):
    """
    Useful for selection and moving after a successful DG update by maya.
    """
    cmds.select(selection, replace=True)
    cmds.move(*translation_values, relative=True, worldSpace=True)


def traverseParentModules(module_namespace):
    """
    Returns a list and number of all parent modules from a given module.
    """
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
    """
    Search for children modules from all nodes for a module. Also, search recursively
    for all children to return a dict structure depicting the "allChildren" hierarchy.
    """
    childrenModules = []
    allChildrenModules = {}

    # Get a list of all node names for the given module (without namespaces).
    numNodes = cmds.getAttr(module_namespace+':moduleGrp.numberOfNodes')

    nodeNameList = ['node_%s_transform'%i for i in range(numNodes)]
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
    """
    Return a list of all parents (connected using constraints) from a given root joint for 
    a joint hierarchy in a character.
    """
    allParentRootJoints = []

    # If the passed-in root joint of a hierarchy in a character has a constrained parent, proceed.
    if cmds.attributeQuery('constrainedParent', node=rootJoint, exists=True):

        # Get the name of the constrained parent joint
        rootParent = cmds.getAttr(rootJoint+'.constrainedParent')
        jointIt = [rootParent]

        # With a joint name in the 'constraining' parent hierarchy, get the name of its root joint.
        while jointIt:
            if jointIt[0].endswith('root_node_transform'):
                rootParent = jointIt[0]        
            jointIt = cmds.listRelatives(jointIt, parent=True, type='joint')

        # Append the name of the root joint of the 'constraining' parent joint hierarchy.
        allParentRootJoints += [rootParent]

        # Recursively search for more 'constrained' parents
        allParentRootJoints += traverseConstrainedParentHierarchiesForSkeleton(rootParent)

    return allParentRootJoints


def checkForJointDuplication():
    """
    Checks if a character joint has been manually duplicated in the scene.
    """
    allJoints = cmds.ls(type='joint')
    
    # Get all the mrt joint names in the scene. Only the node name at the end of
    # a DAG path.
    mrt_joints = [item.split('|')[-1] for item in allJoints if \
                  re.match('^MRT_character\w+_transform$', item.split('|')[-1])]
    check = True

    if mrt_joints:
    
        for joint in mrt_joints:
        
            # If the joint "node" name occurs twice in the list, warn.
            if mrt_joints.count(joint) > 1:
                cmds.warning('MRT Error: One of the character joints has been manually duplicated. \
                              Please undo it in order to perform control rigging.')
                check = False
                break

    return check


def returnConstraintWeightIndexForTransform(transform, constraintNode, matchAttr=False):
    """
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
    """
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


def returnMayaVersion():
    """
    Returns the current maya version as an integer.
    """
    # return int(eval(mel.eval('$val = $gMayaVersionYear')))    # Alternative
    return int(eval(cmds.about(version=True)))


def addNodesToContainer(inputContainer, inputNodes, includeHierarchyBelow=False, includeShapes=False, force=False):
    """
    Add a list of nodes to a given container name. It has the following arguments:

    inputContainer -> String name for the container.
    inputNodes -> List of string names for nodes.
    includeHierarchyBelow -> Include and append all children nodes to the node list to be added to the container.
    includeShapes -> Include and append any shapes for the transform(s) to the node list to be added to the container.
    force -> All nodes will be disconnected from their current containers, if any, and will be added to the 
             given container.

    Returns True if successful and False if otherwise.
    """
    # Collect the input node(s) in a list. Make sure they exist.
    if isinstance(inputNodes, list):
        nodes = list(inputNodes)
    else:
        nodes = [inputNodes]

    containedNodes = []
    for node in nodes:
        if cmds.objExists(node):
            containedNodes.append(node)

    # Iterate through the input nodes. Find additional nodes to be added to the input container.
    dgNodes = []
    for node in containedNodes:

        # If the node is a transform, find the appropriate nodes connected in DG to be added to the container.
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
    """
    Calculate and set the rotate order for a given transform in a reverse IK leg/foot configuration.
    """
    # Get the axes data from axesInfo using returnAxesInfoForFootTransform() 
    crossAx = axesInfo['cross'][0]
    aimAx = axesInfo['aim'][0]
    upAx = axesInfo['up'][0]

    # Get the rotateOrder based on the order of axes obtained above.
    rotateOrderAxes = aimAx + crossAx + upAx
    rotateOrder = {'xyz':0, 'yzx':1, 'zxy':2, 'xzy':3, 'yxz':4, 'zyx':5}[rotateOrderAxes.lower()]

    # Set rotation order
    cmds.setAttr(transform+'.rotateOrder', rotateOrder)


def updateNodeList(nodes):
    """
    Updates all DAG nodes in a given node list.
    """
    if not isinstance(nodes, list):
        nodes = [nodes]

    cmds.setToolTo('moveSuperContext')

    for node in nodes:
        if cmds.objectType(node, isAType='transform'):
            cmds.select(node, replace=True)  

    cmds.select(clear=True)
    cmds.setToolTo('selectSuperContext')    


def updateAllTransforms():
    """
    Updates all transforms created by MRT.
    """
    cmds.setToolTo('moveSuperContext')

    nodes = [node for node in cmds.ls(type='dagNode') if \
            re.match('^MRT_[a-zA-Z0-9_:]*(handle|transform|control){1}$', node)]

    for node in nodes:
        cmds.select(node, replace=True)  

    cmds.select(clear=True)
    cmds.setToolTo('selectSuperContext')   


def updateContainerNodes(container):
    """
    Updates nodes within a given container.
    """
    nodes = cmds.container(container, query=True, nodeList=True)
    cmds.setToolTo('moveSuperContext')

    for node in nodes:
        if cmds.objectType(node, isAType='transform'):
            cmds.select(node, replace=True)  

    cmds.select(clear=True)
    cmds.setToolTo('selectSuperContext')


def cleanSceneState():      # This definition is to be modified as necessary.
    """
    Clean-up a scene, with nodes left by maya.
    """
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
    """
    Called to return all module specs / attributes. Accepts an existing
    module namespace. The returned data is used by createModuleFromAttributes(), createSkeletonFromModule(),
    and createProxyForSkeletonFromModule().
    """

    moduleAttrsDict = {}

    # Get the creation plane, XY, YZ or XZ (along with the side, - or +), eg., +XY
    moduleAttrsDict['creation_plane'] = str(cmds.getAttr(moduleNamespace+':moduleGrp.onPlane'))

    # Get the node orientation order, eg., XYZ, where X is the aim axis, Y is up and so on.
    moduleAttrsDict['node_axes'] = str(cmds.getAttr(moduleNamespace+':moduleGrp.nodeOrient'))

    # Get the number of nodes.
    moduleAttrsDict['num_nodes'] = numNodes = cmds.getAttr(moduleNamespace+':moduleGrp.numberOfNodes')

    # Get the module parent info with default values. This is updated later. It contains the following info:
    # [[current module namespace, module parent info,
    # [mirror module namespace, mirror module parent info (if this module's a mirrored module pair]]
    moduleAttrsDict['moduleParentInfo'] = [[moduleNamespace, cmds.getAttr(moduleNamespace+':moduleGrp.moduleParent')], \
                                                                                                     [None, u'None']]
    # Get the mirror function info for the module (This info is valid only in case of a mirrored module pair).
    # Initializing with default values. This will be updated below. It contains the following info:
    # [ True if mirroring is turned on,
    # Translation function for controls if mirroring,
    # Rotation function for controls if mirroring]
    moduleAttrsDict['mirror_options'] = ['Off', 'Local_Orientation', 'Behaviour']

    # Set if the module is a mirrored module. This value is needed/modified as needed while creating mirror modules.
    # This can be set to False. It's used to keep track of which module of the mirrored pair is being created (The one
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
    # elbow proxy type, 'sphere' or 'cube' (to be updated later)]
    # mirror instancing is enabled for all module proxy geo]
    moduleAttrsDict['proxy_geo_options'] = [False, False, None, 'Off']

    # Get the info for node components for the module. It contains the following info:
    # [True for visibility of module hierarchy representation (set to True as  default),
    # True for visibility of module node orientation representation (set to False as default),
    # True for creation of proxy geometry (set as False as default)]
    moduleAttrsDict['node_compnts'] = [True, False, False]

    # Get the default length of the module.
    moduleAttrsDict['module_length'] = 2.0

    # Get the default value of offset of module from its creation plane.
    moduleAttrsDict['module_offset'] = 1.0

    # Based on the argument module namespace, get the module creation info.

    if 'MRT_JointNode' in moduleNamespace:

        moduleAttrsDict['node_type'] = 'JointNode'

        moduleAttrsDict['globalScale'] = cmds.getAttr(moduleNamespace+':module_transform.globalScale')

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

            moduleAttrsDict['orientation_representation_values'] = [('root_node_transform', \
                                  cmds.getAttr(moduleNamespace+':single_orientation_representation_transform.rotate')[0])]

            moduleAttrsDict['node_translation_values'] = [('root_node_transform', \
                                                       cmds.getAttr(moduleNamespace+':root_node_transform.translate')[0])]

            moduleAttrsDict['node_world_translation_values'] = [('root_node_transform', \
                    cmds.xform(moduleNamespace+':root_node_transform', query=True, worldSpace=True, translation=True))]

            moduleAttrsDict['node_world_orientation_values'] = [('root_node_transform', \
            cmds.xform(moduleNamespace+':single_orientation_representation_transform', query=True, worldSpace=True, rotation=True))]

            moduleAttrsDict['node_rotationOrder_values'] = [('root_node_transform', \
                                                     cmds.getAttr(moduleNamespace+':root_node_transform.rotateOrder'))]

        if numNodes > 1:
            # Get the node orientation representation control values
            node_orientation_Grp = moduleNamespace+':moduleOrientationHierarchyRepresentationGrp'
            node_orientation_Grp_allChildren = \
                cmds.listRelatives(node_orientation_Grp, allDescendents=True, type='transform')
            all_node_orientation_transforms = filter(lambda transform:transform.endswith('orientation_representation_transform'), \
                                                                                        node_orientation_Grp_allChildren)

            node_orientation_representation_values = []

            for transform in all_node_orientation_transforms:
                orientationAttr = cmds.listAttr(transform, keyable=True, visible=True, unlocked=True)[0]
                node_orientation_representation_values.append((stripMRTNamespace(transform)[1], \
                                                                                cmds.getAttr(transform+'.'+orientationAttr)))

            moduleAttrsDict['orientation_representation_values'] = node_orientation_representation_values ##

            # Get the world orientation values for the module nodes.
            node_world_orientations = []

            for transform in all_node_orientation_transforms:
                node_world_orientations.append((stripMRTNamespace(transform)[1].partition('_orientation')[0], \
                                          cmds.xform(transform, query=True, worldSpace=True, rotation=True)))
            node_world_orientations.append(('end_node_transform', [0.0, 0.0, 0.0]))

            moduleAttrsDict['node_world_orientation_values'] = node_world_orientations


            # Get the node translation, world translation, and orientation values
            node_transform_Grp = moduleNamespace+':moduleJointsGrp'
            node_transform_Grp_allChildren = cmds.listRelatives(node_transform_Grp, allDescendents=True, type='joint')

            node_translations = []
            node_world_translations = []
            node_rotationOrders = []
            node_handle_sizes = []

            for transform in node_transform_Grp_allChildren:
                node_translations.append((stripMRTNamespace(transform)[1], cmds.getAttr(transform+'.translate')[0]))
                node_world_translations.append((stripMRTNamespace(transform)[1], cmds.xform(transform, query=True, worldSpace=True, \
                                                                                                            translation=True)))
                node_rotationOrders.append((stripMRTNamespace(transform)[1], cmds.getAttr(transform+'.rotateOrder')))
                node_handle_sizes.append((stripMRTNamespace(transform)[1], \
                            cmds.getAttr(moduleNamespace+':module_transform.'+stripMRTNamespace(transform)[1]+'_handle_size')))

            moduleAttrsDict['node_translation_values'] = node_translations ##
            moduleAttrsDict['node_world_translation_values'] = node_world_translations ##
            moduleAttrsDict['node_rotationOrder_values'] = node_rotationOrders
            moduleAttrsDict['node_handle_sizes'] = node_handle_sizes


    if 'MRT_SplineNode' in moduleNamespace:

        moduleAttrsDict['node_type'] = 'SplineNode'

        # Get the module global scale
        moduleAttrsDict['globalScale'] = cmds.getAttr(moduleNamespace+':splineStartHandleTransform.Global_size')

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
            splineAdjustCurveTransformValues.append((stripMRTNamespace(transform)[1], cmds.getAttr(transform+'.translate')[0]))

        moduleAttrsDict['splineAdjustCurveTransformValues'] = splineAdjustCurveTransformValues

        # Get the world translation and rotation values for spline nodes. Used when creating a joint hierarchy from
        # spline module in a character.
        node_transform_Grp_allChildren = cmds.listRelatives(moduleNamespace+':moduleJointsGrp', allDescendents=True, type='joint')

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

        # Get the module global scale
        moduleAttrsDict['globalScale'] = cmds.getAttr(moduleNamespace+':module_transform.globalScale')

        # Get the transform values for the module transform
        moduleAttrsDict['module_translation_values'] = cmds.getAttr(moduleNamespace+':module_transform.translate')[0]
        moduleAttrsDict['module_transform_orientation'] = cmds.getAttr(moduleNamespace+':module_transform.rotate')[0]

        # Get the node handle colour for the module
        moduleAttrsDict['handle_colour'] = cmds.getAttr(moduleNamespace+':root_node_transform_controlXShape.overrideColor') + 1

        # Get the module transform attributes.
        otherAttrs = cmds.listAttr(moduleNamespace+':module_transform', keyable=True, visible=True, unlocked=True)[6:]
        for attr in otherAttrs:
            moduleAttrsDict[attr] = cmds.getAttr(moduleNamespace+':module_transform'+'.'+attr)

        # Get the module node transform values (required for creating a duplicate hinge module)
        moduleIKnodesGrp = moduleNamespace+':moduleIKnodesGrp'
        moduleIKnodesGrp_allChildren = cmds.listRelatives(moduleIKnodesGrp, allDescendents=True, type='transform')

        moduleIKnodesGrp_transforms = filter(lambda transform:transform.endswith('_control'), moduleIKnodesGrp_allChildren)

        node_translations = []

        for transform in moduleIKnodesGrp_transforms:
            node_translations.append((stripMRTNamespace(transform)[1], cmds.getAttr(transform+'.translate')[0]))

        moduleAttrsDict['node_translation_values'] = node_translations

        # Get the world translation and rotation values for hinge module nodes (used when creating a joint hierarchy from
        # hinge module in a character). First, in order to get the correct rotation values of the module nodes, we have to
        # reset the node rotation orders to their default.

        # Get the module node transforms
        node_transform_Grp_allChildren = cmds.listRelatives(moduleNamespace+':moduleJointsGrp', allDescendents=True, type='joint')

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
            if re.match(moduleNamespace+':(root_node_transform|end_node_transform|node_\d+_transform)_proxy_bone_geo', \
                                                                                                            transform):
                # Set proxy geo options for bone to be True
                moduleAttrsDict['proxy_geo_options'][0] = True
            if re.match(moduleNamespace+':(root_node_transform|end_node_transform|node_\d+_transform)_proxy_elbow_geo', \
                                                                                                            transform):
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


def createSkeletonFromModule(moduleAttrsDict, characterName):
    """
    Converts a module to a joint hierarchy. This method is called during character creation to perform on modules
    in the scene. It uses the module attribute data generated by "returnModuleAttrsFromScene" function.
    """
    # To collect joints created from the module (by using its attributes)
    joints = []
    
    # If the module is a mirrored module pair, mirror its joint set pair on the + side of its creation plane.
    # First, you always create the joints from a module created on the + side of its creation plane for a mirrored
    # module pair, and then mirror the joint set hierarchy for its mirrored module.
    if moduleAttrsDict.get('mirror_module_Namespace') != None and moduleAttrsDict['creation_plane'][0] == '-':
    
        # Get the namespace for the modoule in a mirrored pair (the one created on the + side of creation plane).
        origUserSpecName = moduleAttrsDict['mirror_module_Namespace'].partition(':')[0].partition('__')[2]
        
        # Get the name of the root joint from the joint set hierarchy created from that module.
        origRootJointName = 'MRT_character'+characterName+'__'+origUserSpecName+'_root_node_transform'

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
        for joint in r_joints:
            cmds.setAttr(joint+'.plane', lock=False)
            # Creation plane
            cmds.setAttr(joint+'.plane', '-'+moduleAttrsDict['creation_plane'][1:], type='string', lock=True)
            # Get the new name for the joint, and rename it.
            name = re.split(origUserSpecName, joint)[0] + moduleAttrsDict['userSpecName'] + re.split(origUserSpecName, joint)[1]
            name = re.split('\d+$', name)[0]
            joint = cmds.rename(joint, name)
            joints.append(joint)
        
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
                name = 'MRT_character'+characterName+'__'+moduleAttrsDict['userSpecName']+'_root_node_transform'
                # Create the joint.
                jointName = cmds.joint(name=name, position=moduleAttrsDict['node_world_translation_values'][0][1],
                                       orientation=moduleAttrsDict['node_world_orientation_values'][0][1],
                                       radius=moduleAttrsDict['globalScale']*moduleAttrsDict['node_handle_sizes'][0][1]*0.16)
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
                    name = 'MRT_character'+characterName+'__'+moduleAttrsDict['userSpecName']+'_'+position[0]
                    
                    # Create the joint for the module node.
                    jointName = cmds.joint(name=name, position=position[1],
                                       radius=moduleAttrsDict['globalScale']*moduleAttrsDict['node_handle_sizes'][i][1]*0.16)
                                       
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
                cmds.joint(edit=True, orientJoint=moduleAttrsDict['node_axes'].lower(), secondaryAxisOrient=s_axis,     \
                                                                                         zeroScaleOrient=True, children=True)
                cmds.select(clear=True)
                
                # Unparent the child joints for further orientation.
                for joint in joints[1:]:
                    cmds.parent(joint, absolute=True, world=True)
                
                # Orient the joints using the orientation data.
                for (joint, orientation) in zip(joints, moduleAttrsDict['node_world_orientation_values']):
                    cmds.joint(joint, edit=True, orientation=orientation[1])

                # Reparent the child joints.
                for i, joint in enumerate(joints[1:]):
                    cmds.parent(joint, joints[i], absolute=True)
                
                # Reset the orientation for last joint.
                cmds.setAttr(joints[-1]+'.jointOrient', 0, 0, 0, type='double3')
                cmds.select(clear=True)
                
                # Set the joint rotation orders.
                for joint, rotOrder in zip(joints, moduleAttrsDict['node_rotationOrder_values']):
                    cmds.setAttr(joint+'.rotateOrder', rotOrder[1])

        # If the module type is SplineNode.
        if moduleAttrsDict['node_type'] == 'SplineNode':
        
            # Create joints for every spline node position.
            for position in moduleAttrsDict['node_world_translation_values']:
            
                # Get the name for the joint.
                name = 'MRT_character'+characterName+'__'+moduleAttrsDict['userSpecName']+'_'+position[0]
                
                # Create the joint and add attributes
                jointName = cmds.joint(name=name, position=position[1], radius=moduleAttrsDict['globalScale']*0.17)
                cmds.addAttr(jointName, dataType='string', longName='inheritedNodeType')
                cmds.setAttr(jointName+'.inheritedNodeType', 'SplineNode', type='string', lock=True)
                cmds.addAttr(jointName, dataType='string', longName='splineOrientation')
                cmds.setAttr(jointName+'.splineOrientation', moduleAttrsDict['node_objectOrientation'], type='string', lock=True)
                cmds.setAttr(jointName+'.overrideEnabled', 1)
                cmds.setAttr(jointName+'.overrideColor', moduleAttrsDict['handle_colour'])               
                joints.append(jointName)
            
            # Get the up axis for joint orientation from creation plane axes for the spline module.
            s_axis = {'XY':'zup', 'YZ':'xup', 'XZ':'yup'}[moduleAttrsDict['creation_plane'][1:]]
            
            # Orient the joint chain along the aim axis
            cmds.select(joints[0], replace=True)
            cmds.joint(edit=True, orientJoint=moduleAttrsDict['node_axes'].lower(), secondaryAxisOrient=s_axis, \
                                                                                        zeroScaleOrient=True, children=True)
            cmds.select(clear=True)
            
            # Unparent the child joints in the joint chain
            for joint in joints[1:]:
                cmds.parent(joint, absolute=True, world=True)
            
            # If the spline module node orinetatioh type is set to 'object', orient the joints individually.
            if moduleAttrsDict['node_objectOrientation'] == 1:
                aimVector={'X':[1.0, 0.0, 0.0], 'Y':[0.0, 1.0, 0.0], 'Z':[0.0, 0.0, 1.0]}[moduleAttrsDict['node_axes'][0]]
                upVector = {'X':[1.0, 0.0, 0.0], 'Y':[0.0, 1.0, 0.0], 'Z':[0.0, 0.0, 1.0]}[moduleAttrsDict['node_axes'][1]]
                worldUpVector = \
                {'XY':[0.0, 0.0, 1.0], 'YZ':[1.0, 0.0, 0.0], 'XZ':[0.0, 1.0, 0.0]}[moduleAttrsDict['creation_plane'][1:]]
                
                # Aim and orient to the next joint, except the last joint.
                for i in xrange(len(joints)):
                    if not joints[i] == joints[-1]:
                        tempConstraint = cmds.aimConstraint(joints[i+1], joints[i], aimVector=aimVector, upVector=upVector, \
                                                                                                worldUpVector=worldUpVector)
                        cmds.delete(tempConstraint) 
                        cmds.makeIdentity(joints[i], rotate=True, apply=True)        
            
                # Add the 'axis rotate' value to the joint orientations.
                for (joint, orientation) in zip(joints, moduleAttrsDict['node_world_orientation_values']):
                    axes_mult = {'x':[1, 0, 0], 'y':[0, 1, 0], 'z':[0, 0, 1]}[moduleAttrsDict['node_axes'][0].lower()]
                    addOrientation = [moduleAttrsDict['splineOrientation_value']*item for item in axes_mult]
                    jointOrientation = list(cmds.getAttr(joint+'.jointOrient')[0])
                    newOrientation = map(lambda x, y:x+y, addOrientation, jointOrientation)
                    cmds.setAttr(joint+'.jointOrient', newOrientation[0], newOrientation[1], newOrientation[2], type='double3')  

            # If the spline node orientation type is set to 'world'.
            else:
                for joint in joints:
                    cmds.setAttr(joint+'.jointOrient', 0, 0, 0, type='double3')

            # Re-parent the child joints in the spline joint chain.
            for i, joint in enumerate(joints[1:]):
                cmds.parent(joint, joints[i], absolute=True)

            # Set orientation for the last joint.
            cmds.setAttr(joints[-1]+'.jointOrient', 0, 0, 0, type='double3')
        
        # If the module type is HingeNode.
        if moduleAttrsDict['node_type'] == 'HingeNode':
            
            # Create the joints for the module nodes with their position.
            for i, position in enumerate(moduleAttrsDict['node_world_translation_values']):
            
                # Get the name of the joint
                name = 'MRT_character'+characterName+'__'+moduleAttrsDict['userSpecName']+'_'+position[0]
                
                # Create the joint.
                jointName = cmds.joint(name=name, position=position[1], \
                                       radius=moduleAttrsDict['globalScale']*moduleAttrsDict['node_handle_sizes'][i][1]*0.16)
                                       
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
            cmds.joint(edit=True, orientJoint=moduleAttrsDict['node_axes'].lower(), secondaryAxisOrient=s_axis, \
                                                                                         zeroScaleOrient=True, children=True)
            cmds.select(clear=True)
            
            # Unparent the child joints.
            for joint in joints[1:]:
                cmds.parent(joint, absolute=True, world=True)
            
            # Apply the orientation to joints from the module attribute data.
            for (joint, orientation) in zip(joints, moduleAttrsDict['node_world_orientation_values']):
                cmds.joint(joint, edit=True, orientation=orientation[1])
            
            # Reparent the child joints.
            for i, joint in enumerate(joints[1:]):
                cmds.parent(joint, joints[i], absolute=True)
            
            # Apply the joint rotation orders.
            for joint, rotOrder in zip(joints, moduleAttrsDict['node_rotationOrder_values']):
                cmds.setAttr(joint+'.rotateOrder', rotOrder[1])
            
            # Add / set the 'ikSegmentModPos' attribute to the root joint (It's the position of the middle/hinge joint in the
            # joint chain in a straight line).
            cmds.addAttr(joints[0], dataType='string', longName='ikSegmentMidPos')
            cmds.setAttr(joints[0]+'.ikSegmentMidPos', moduleAttrsDict['ikSegmentMidPos'], type='string', lock=True)

        # Add additional joint attributes common to all module types.
        for joint in joints:
            cmds.addAttr(joint, longName='numNodes')
            cmds.setAttr(joint+'.numNodes', moduleAttrsDict['num_nodes'], lock=True)
            cmds.addAttr(joint, dataType='string', longName='nodeAxes')
            cmds.setAttr(joint+'.nodeAxes', moduleAttrsDict['node_axes'], type='string', lock=True)
            cmds.addAttr(joint, dataType='string', longName='plane')
            cmds.setAttr(joint+'.plane', moduleAttrsDict['creation_plane'], type='string', lock=True)
            cmds.addAttr(joint, dataType='string', longName='translationFunction')
            cmds.setAttr(joint+'.translationFunction', moduleAttrsDict['mirror_options'][1].lower(), type='string', lock=True)
            cmds.addAttr(joint, dataType='string', longName='rotationFunction')
            cmds.setAttr(joint+'.rotationFunction', moduleAttrsDict['mirror_options'][2].lower(), type='string', lock=True)

        cmds.select(clear=True)

    return joints


def setupParentingForRawCharacterParts(characterJointSet, jointsMainGrp, characterName):
    """
    Set up parenting for joint hierarchies while creating a character. The type of parenting
    depends on the module parenting info stored for joints for a hierarchy in "characterJointSet".

    "Constrained" parenting uses parent constraint, "DG parenting". "Hierarchical" parenting uses DAG parenting.
    """
    # Collect all
    all_root_joints = []

    # Iterate through the joints in the hierarchy.
    for item in characterJointSet:

        # Each "item", contains the following data:
        # ("<parent module node>,<parent type>", ["<child hierarchy root joint>", ..., "<child hierarchy end joint>"])
        # As an example:
        # ("MRT_JointNode__r_clavicle:root_node_transform,Constrained", ["MRT_characterNew__r_arm_root_node_transform",
        #                                                                "MRT_characterNew__r_arm_node_1_transform",
        #                                                                "MRT_characterNew__r_arm_end_node_transform"])

        # Get the parent info for the joint and proceed.
        parentInfo = item[0]

        if parentInfo != 'None':

            # The module parenting info is stored as string. Eg., if the node "MRT_HingeNode__l_leg:end_node_transform",
            # is a hierarchical parent, it will stored as:
            # "MRT_HingeNode__l_leg:end_node_transform,Hierarchical" or "...,Constrained" if constrained parent.
            parentInfo = parentInfo.split(',')

            # This parent module node name needs to be converted to its current joint name in the scene, which will be used.
            # This is needed since "setupParentingForRawCharacterParts" is called after all module nodes in the scene
            # are converted to joints.
            # Eg., "MRT_HingeNode__l_leg:end_node_transform" is renamed as
            #      "MRT_characterNew__l_leg_end_node_transform" (New is character name)
            parentInfo[0] = 'MRT_character%s__%s_%s' % (characterName,
                                                        parentInfo[0].partition(':')[0].partition('__')[2],
                                                        parentInfo[0].partition(':')[2])

            # If the parent type is "Hierarchical".
            if parentInfo[1] == 'Hierarchical':
                cmds.parent(item[1][0], parentInfo[0], absolute=True)

            # Else, the parent type is either "constrained" or it's main root joint hierarchy for the
            # character, driven by the character root transform (<MRT_character*__root_transform>).
            else:
                # Create the joint group for joint hierarchy in "characterJointSet".
                # Get its name from the root joint of the joint hierarchy.
                # Eg., if its name is "MRT_characterNew__r_arm_root_node_transform",
                # the name of the joint group is "MRT_characterNew__r_arm_jointsGrp".
                name = re.split('_(?:root_node|node_\d+|end_node)_transform', joint)[0] + '_jointsGrp'
                jointGrp = cmds.group(empty=True, name=name, parent=jointsMainGrp)
                # The joint group is not needed for a root joint of a joint hierarchy with a hierarchical parent,
                # since it'll be parented under a joint.

                cmds.select(clear=True)

                # Create the "constrained" joint above the root joint of the hierarchy to receive constraints.
                d_joint = cmds.duplicate(item[1][0], parentOnly=True, returnRootsOnly=True, name=item[1][0]+'_constrained')[0]
                cmds.setAttr(d_joint+'.overrideEnabled', 1)
                cmds.setAttr(d_joint+'.overrideDisplayType', 1)
                cmds.setAttr(d_joint+'.radius', 0)

                # Constrain this joint with its parent.
                cmds.parentConstraint(parentInfo[0], d_joint, maintainOffset=True, name=parentInfo[0]+'__parentConstraint')
                # Parent the root joint to it.
                cmds.parent(item[1][0], d_joint, absolute=True)
                # Parent the constrained joint under the joint group.
                cmds.parent(d_joint, jointGrp, absolute=True)

                # If parent type is "Constrained"
                if parentInfo[1] == 'Constrained':

                    # Add constrained parent info to the root joint of the joint hierarchy
                    cmds.addAttr(item[1][0], dataType='string', longName='constrainedParent', keyable=False)
                    cmds.setAttr(item[1][0]+'.constrainedParent', parentInfo[0], type='string', lock=True)

                # Else, the joint hierarchy is the main root joint hierarchy for the character.
                else:
                    # Collect it.
                    all_root_joints.append(d_joint)

    return all_root_joints


def createProxyForSkeletonFromModule(characterJointSet, moduleAttrsDict, characterName):
    """
    Set up proxy geometry for joint hierarchies during character creation. It uses the module attribute data generated by 
    "returnModuleAttrsFromScene". It uses the existing module proxy geometry, if it exists.
    
    We'll iterate through joint chain created from its module (nodes), find if the module proxy proxy geometry, bone or elbow
    type exists for the module and hence for the node, duplicate it for the joint and drive it appropriately.
    """
    
    # Get the joint set, which in this case is the last joint set added to the 'characterJointSet' data list.
    # See 'processCharacterFromScene' in mrt_UI.
    # Then it looks into the joint set data, and lets the joint list from the second (1) index.
    # See 'setupParentingForRawCharacterParts' above for details on 'characterJointSet'.
    jointSet = characterJointSet[-1][1]
    
    # Create the group to contain the joint proxy geometry.
    proxyGrp = cmds.group(empty=True, name='MRT_character'+characterName+'__'+moduleAttrsDict['userSpecName']+'_proxyGeoGrp')

    
    for (index, joint) in zip(range(moduleAttrsDict['num_nodes']), jointSet):
        
        # Get the naming prefix for the joint (generated from module node).
        if index == 0:
            namePrefix = 'root_node_transform'
        
        if moduleAttrsDict['num_nodes'] > 1:
            if index == moduleAttrsDict['num_nodes']-1:
                namePrefix = 'end_node_transform'
            else:
                namePrefix = 'node_%s_transform' % index
            
        # If elbow proxy geometry exists for the module.
        if cmds.objExists(moduleAttrsDict['module_Namespace']+':%s_proxy_elbow_geo_preTransform' % namePrefix):
            
            # Duplicate the module proxy geometry and name it.
            elbow_proxy = cmds.duplicate(moduleAttrsDict['module_Namespace']+':%s_proxy_elbow_geo_preTransform' % namePrefix, \
                                        returnRootsOnly=True, renameChildren=True, \
                                        name='MRT_character%s__%s_%s_proxy_elbow_geo_preTransform' \
                                            % (characterName, moduleAttrsDict['userSpecName'], namePrefix))[0]
            cmds.makeIdentity(elbow_proxy, scale=True, apply=True)
            
            # Constrain it to the root joint and palce it under proxy group.
            cmds.parentConstraint(joint, elbow_proxy, maintainOffset=True, \
                                    name=joint+'_%s_proxy_elbow_geo_preTransform_parentConstraint' % namePrefix)
            cmds.scaleConstraint(joint, elbow_proxy, maintainOffset=True, \
                                     name=joint+'_%s_proxy_elbow_geo_preTransform_scaleConstraint' % namePrefix)
            cmds.parent(elbow_proxy, proxyGrp)
            
        # If bone proxy geometry exists for the module.
        if cmds.objExists(moduleAttrsDict['module_Namespace']+':%s_proxy_bone_geo_preTransform' % namePrefix):
            
            # Duplicate the module proxy geometry and name it.
            bone_proxy = cmds.duplicate(moduleAttrsDict['module_Namespace']+':%s_proxy_bone_geo_preTransform' % namePrefix, \
                                        returnRootsOnly=True, renameChildren=True, \
                                        name='MRT_character%s__%s_%s_proxy_bone_geo_preTransform' % namePrefix \
                                         % (characterName, moduleAttrsDict['userSpecName']))[0]
            cmds.makeIdentity(bone_proxy, scale=True, apply=True)
            
            # Parent constrain the bone proxy geo to the joint.
            cmds.parentConstraint(joint, bone_proxy, maintainOffset=True, \
                                      name=joint+'_%s_proxy_bone_geo_preTransform_parentConstraint' % namePrefix)
                                      
            # Calculate and drive the aim axis scaling of the bone proxy geometry (which is between two joints).
            
            # Create the utility nodes.
            distanceBetweenNode = cmds.createNode('distanceBetween', name=bone_proxy+'_scaleLengthDistance', skipSelect=True)
            distanceBetween_1_vecPro = cmds.createNode('vectorProduct', name=bone_proxy+'_scaleLengthVector_1_point', skipSelect=True)
            distanceBetween_2_vecPro = cmds.createNode('vectorProduct', name=bone_proxy+'_scaleLengthVector_2_point', skipSelect=True)
            distanceScaleDivide = cmds.createNode('multiplyDivide', name=bone_proxy+'_distanceScaleDivide', skipSelect=True)
            
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
            cmds.scaleConstraint(joint, bone_proxy, maintainOffset=True, skip=moduleAttrsDict['node_axes'][0].lower(), \
                                        name=joint+'_%s_proxy_bone_geo_preTransform_scaleConstraint' % namePrefix)
                                        
            # Place it under proxy group.
            cmds.parent(bone_proxy, proxyGrp)

    # Find all the transforms added under the proxy group.
    allChildren = cmds.listRelatives(proxyGrp, allDescendents=True, fullPath=True, shapes=False)
    # Find all the proxy geo transforms under the proxy group.
    proxy_geo_transforms = [item for item in allChildren if str(item).rpartition('geo')[2] == '']
    
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
        
            # Rename any other unnamed transforms
            nodeName = node.rpartition('|')[-1]
            if nodeName[:3] != 'MRT':
                cmds.rename(node, 'MRT_character'+characterName+'__'+moduleAttrsDict['userSpecName']+'_'+nodeName)
    
        # Get a name for the proxy display layer for the character and create it.
        layerName = 'MRT_character'+characterName+'_proxy_geometry'
        if not cmds.objExists(layerName):
            cmds.createDisplayLayer(empty=True, name=layerName, noRecurse=True)
            cmds.setAttr(layerName+'.displayType', 2)
            
        # Set the color for the proxy geo transforms and add it to the display layer.
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


def createFKlayerDriverOnJointHierarchy(**kwargs):
    """
    Creates a joint layer on top of a selected character hierarchy. For description in context, see the "applyFK_Control" method
    for the "BaseJointControl" class in "mrt_controlRig_src.py"
    """
    
    # Get the input arguments
    
    if 'characterJointSet' in kwargs:
        characterJointSet = kwargs['characterJointSet']
    else:
        cmds.warning('Not joint set specified from a character. Cannot create driver hierarchy.')
        # I don't use 'cmds.error' since it generates an exception.
        return

    if 'jointLayerName' in kwargs:
        jointLayerName = kwargs['jointLayerName']
    else:
        cmds.warning('No name specified for the driver layer. Aborting.')
        return

    if 'characterName' in kwargs:
        characterName = kwargs['characterName']
    else:
        cmds.warning('No character name specified. Aborting.')
        return

    if 'asControl' in kwargs:
        asControl = kwargs['asControl']
    else:
        asControl = False

    if 'layerVisibility' in kwargs:
        layerVisibility = kwargs['layerVisibility']
    else:
        layerVisibility = 'On'

    if 'transFilter' in kwargs:
        transFilter = kwargs['transFilter']
    else:
        transFilter = False

    if 'controlLayerColour' in kwargs:
        controlLayerColour = kwargs['controlLayerColour']
    else:
        controlLayerColour = None

    if 'connectLayer' in kwargs:
        connectLayer = kwargs['connectLayer']
    else:
        connectLayer = True

    # To get the names of joints in the new driver layer.
    layerJointSet = []
    # To collect the constraints for the new driver joint layer to drive the input joint hierarchy.
    driver_constraints = []
    # To get the name of the root joint of the new driver joint layer.
    layerRootJoint = ''

    # Iterate through the passed-in joint hierarchy (selected, one of) for the character.
    for joint in characterJointSet:

        # Find the root joint of the hierarchy
        if joint.endswith('root_node_transform'):

            # Get the constrained joint for the root joint. It's the joint above the root joint
            # which receives constraints. The root joint is not constrained.
            jointParent = cmds.listRelatives(joint, parent=True, type='joint')

            if jointParent[0].endswith('_constrained'):

                # Get the naming prefix and suffix from the root joint name
                # Eg., if the root joint name is "MRT_characterNew__module_root_node_transform",
                # then the prefix is "MRT_characterDef__module" and the suffix is "_root_node_transform".
                jointPrefix = re.split('_(?:root_node|node_\d+|end_node)_transform', joint)[0]
                jointSuffix = re.findall('_(?:root_node|node_\d+|end_node)_transform', joint)[0]

                # Provide a name for the joint in the new hierarchy to created in this layer. A "_handle" suffix
                # would be added to joint name if it'll be used as direct control transforms (like as an FK control,
                # which will drive the original joint hierarchy).
                # If asControl argument is set to True.
                if asControl:
                    newName = '%s_%s%s_handle'%(jointPrefix, jointLayerName, jointSuffix)
                else:
                    newName = '%s_%s%s'%(jointPrefix, jointLayerName, jointSuffix)

                # Duplicate the input joint hierarchy by duplicating its root joint, and name it.
                newRootJoint = cmds.duplicate(joint, returnRootsOnly=True, name=newName)[0]

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
                            jointPrefix = re.split('_(?:root_node|node_\d+|end_node)_transform', jointName)
                            jointSuffix = re.findall('_(?:root_node|node_\d+|end_node)_transform', jointName)
                            if jointPrefix and jointSuffix:

                                # Get a new name for the joint in the layer.
                                if asControl:
                                    newName = '%s_%s%s_handle'%(jointPrefix[0], jointLayerName, jointSuffix[0])
                                else:
                                    newName = '%s_%s%s'%(jointPrefix[0], jointLayerName, jointSuffix[0])

                                # Rename the join in the driver layer.
                                cmds.rename(joint, newName)

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
            parentConstraint = cmds.parentConstraint(layerJoint, joint, maintainOffset=transFilter, \
                                                     name=joint+'_all_FK_layer_parentConstraint')[0]
            scaleConstraint = cmds.scaleConstraint(layerJoint, joint, maintainOffset=transFilter, \
                                                   name=joint+'_all_FK_layer_scaleConstraint')[0]
            driver_constraints.extend([parentConstraint, scaleConstraint])

    # Disconnect the "all_joints" display to the driver layer joints (inherited by duplicating the input joint hierarchy).
    for joint in layerJointSet:
        cmds.disconnectAttr('MRT_character'+characterName+'_all_joints.drawInfo', joint+'.drawOverride')

        # Set the visibility of the driver joint layer based on the "layerVisibility" argument.
        if layerVisibility == 'None':
            cmds.setAttr(joint+'.visibility', 0)

        # If the driver joint layer is to be used as direct control, connect its visibility to the "control_rig" layer.
        if layerVisibility == 'On':
            cmds.setAttr(joint+'.overrideEnabled', 1)
            cmds.connectAttr('MRT_character'+characterName+'_control_rig.visibility', joint+'.overrideVisibility')

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
    """
    Called for creating a new module from its attributes / specs. Accepts an existing module data returned by
    returnModuleAttrsFromScene().
    """
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

    # Get the module instance and create it based on its type
    moduleInst = mrt_module.MRT_Module(moduleAttrsDict)
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

        # Create the mirror module and collect it
        mirrorModuleInst = mrt_module.MRT_Module(moduleAttrsDict)
        eval('mirrorModuleInst.create%sModule()' % moduleAttrsDict['node_type'])
        modules.append(moduleAttrsDict['module_Namespace'])
        del mirrorModuleInst

    # Lock the module containers
    for module in modules:
        cmds.lockNode(module+':module_container', lock=True, lockUnpublished=True)

    cmds.select(clear=True)

    # Reset the working module namespace in moduleAttrsDict
    if moduleAttrsDict['creation_plane'][0] == '+' and moduleAttrsDict['mirror_options'][0] == 'On':
        name = moduleAttrsDict['module_Namespace'] 
        moduleAttrsDict['module_Namespace'] = moduleAttrsDict['mirror_module_Namespace']
        moduleAttrsDict['mirror_module_Namespace'] = name


    # If a duplicate module is to be created, or not from the UI
    if not createFromUI:

        # Collect the nodes that have to be updated later for mirroring.
        selectionNodes = []

        # Set the additional module attributes according to their type

        if moduleAttrsDict['node_type'] == 'JointNode':

            # Set the translate / rotate on the module transform
            module_transform = moduleAttrsDict['module_Namespace']+':module_transform'
            selectionNodes.append(module_transform)
            cmds.setAttr(module_transform+'.translate', *moduleAttrsDict['module_translation_values'])
            cmds.setAttr(module_transform+'.rotate', *moduleAttrsDict['module_transform_orientation'])

            # Set the module transform attributes
            module_transform_attrs = cmds.listAttr(module_transform, keyable=True, visible=True, unlocked=True)[6:]
            for attr in module_transform_attrs:
                cmds.setAttr(module_transform+'.'+attr, moduleAttrsDict[str(attr)])

            # Apply module transform values to the mirror module (if it exists)
            if moduleAttrsDict['mirror_options'][0] == 'On':

                # Apply rotation multipliers to mirror module transform
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
                for (node_translation, node_translation_value) in moduleAttrsDict['node_translation_values']:
                    node = moduleAttrsDict['module_Namespace']+':'+node_translation
                    selectionNodes.append(node)
                    cmds.setAttr(node+'.translate', *node_translation_value)

                # Set values for orientation representations.
                for (orientation_node, node_orientation_value) in moduleAttrsDict['orientation_representation_values']:
                    node = moduleAttrsDict['module_Namespace']+':'+orientation_node
                    attr = cmds.listAttr(node, keyable=True, visible=True, unlocked=True)[0]
                    cmds.setAttr(node+'.'+attr, node_orientation_value)

                    # Set the value for its mirror node separately.
                    if moduleAttrsDict['mirror_options'][0] == 'On':
                        mirrorNode = moduleAttrsDict['mirror_module_Namespace']+':'+orientation_node
                        cmds.setAttr(mirrorNode+'.'+attr, node_orientation_value)

            if moduleAttrsDict['num_nodes'] == 1:   # Joint module with a single node

                # Set the node translation
                cmds.setAttr(node+'.translate', *moduleAttrsDict['node_translation_values'][0][1])

                # Get the single orientation representation control for a joint module with a single node
                node = moduleAttrsDict['module_Namespace']+':root_node_transform'
                orientation_representation = moduleAttrsDict['module_Namespace']+':single_orientation_representation_transform'
                selectionNodes.append(node)

                # Set it's orientation
                cmds.setAttr(orientation_representation+'.rotate', *moduleAttrsDict['orientation_representation_values'][0][1])

                # Set the value for orientation representation control's mirror
                if moduleAttrsDict['mirror_options'][0] == 'On':
                    orientation_representation = moduleAttrsDict['mirror_module_Namespace']+':single_orientation_representation_transform'
                    cmds.setAttr(orientation_representation+'.rotate', *moduleAttrsDict['orientation_representation_values'][0][1])


        if moduleAttrsDict['node_type'] == 'SplineNode':

            # Get the start and end module transforms
            splineStartHandleTransform = moduleAttrsDict['module_Namespace']+':splineStartHandleTransform'
            splineEndHandleTransform = moduleAttrsDict['module_Namespace']+':splineEndHandleTransform'
            selectionNodes.extend([splineStartHandleTransform, splineEndHandleTransform])

            # Set their translations
            cmds.setAttr(splineStartHandleTransform+'.translate', *moduleAttrsDict['splineStartHandleTransform_translation_values'])
            cmds.setAttr(splineEndHandleTransform+'.translate', *moduleAttrsDict['splineEndHandleTransform_translation_values'])

            # Set the start module transform attributes
            splineStartHandleTransform_attrs = cmds.listAttr(splineStartHandleTransform, keyable=True, visible=True, unlocked=True)[3:]
            for attr in splineStartHandleTransform_attrs:
                cmds.setAttr(splineStartHandleTransform+'.'+attr, moduleAttrsDict[str(attr)])

            # Set the mirror start module attributes
            if moduleAttrsDict['mirror_options'][0] == 'On':
                mirror_splineStartHandleTransform = moduleAttrsDict['mirror_module_Namespace']+':splineStartHandleTransform'
                for attr in splineStartHandleTransform_attrs:
                    cmds.setAttr(mirror_splineStartHandleTransform+'.'+attr, moduleAttrsDict[str(attr)])

            # Set the translations for spline curve adjust transforms.
            for (splineAdjustCurve_transform, transform_value) in moduleAttrsDict['splineAdjustCurveTransformValues']:
                node = moduleAttrsDict['module_Namespace']+':'+splineAdjustCurve_transform
                selectionNodes.append(node)
                cmds.setAttr(node+'.translate', *transform_value)


        if moduleAttrsDict['node_type'] == 'HingeNode':

            # Get the module transform
            module_transform = moduleAttrsDict['module_Namespace']+':module_transform'
            selectionNodes.append(module_transform)

            # Set the translate / rotate for the module transform
            cmds.setAttr(module_transform+'.translate', *moduleAttrsDict['module_translation_values'])
            cmds.setAttr(module_transform+'.rotate', *moduleAttrsDict['module_transform_orientation'])

            # Set the values for module transform attributes
            module_transform_attrs = cmds.listAttr(module_transform, keyable=True, visible=True, unlocked=True)[6:]
            for attr in module_transform_attrs:
                cmds.setAttr(module_transform+'.'+attr, moduleAttrsDict[str(attr)])

            # If mirroring is enabled, get the rotation multipliers for the mirror module transform and set it
            if moduleAttrsDict['mirror_options'][0] == 'On':

                # Apply rotation multipliers to mirror module transform
                mirrorAxisMultiply = {'XY':[-1, -1, 1], 'YZ':[1, -1, -1], 'XZ':[-1, 1, -1]}[moduleAttrsDict['creation_plane'][-2:]]
                module_orientation_values = [x*y for x,y in zip(mirrorAxisMultiply, moduleAttrsDict['module_transform_orientation'])]

                # Get the mirror module transform and set its orientation
                mirror_module_transform = moduleAttrsDict['mirror_module_Namespace']+':module_transform'
                cmds.setAttr(mirror_module_transform+'.rotate', *module_orientation_values)

                # Set the mirror module transform attributes
                for attr in module_transform_attrs:
                    cmds.setAttr(mirror_module_transform+'.'+attr, moduleAttrsDict[str(attr)])

            # Set attributes for node translations.
            for (translation_node, node_translation_value) in moduleAttrsDict['node_translation_values']:
                node = moduleAttrsDict['module_Namespace']+':'+translation_node
                selectionNodes.append(node)
                cmds.setAttr(node+'.translate', *node_translation_value)

        # Select the control to be updated (in order for their mirror controls to be updated).
        if moduleAttrsDict['mirror_options'][0] == 'On':
            for node in selectionNodes:
                cmds.evalDeferred(partial(cmds.select, node, replace=True), lowestPriority=True)

    # Re-set the current namespace
    cmds.namespace(setNamespace=currentNamespace)

    return modules


# -------------------------------------------------------------------------------------------------------------
#
#   RUNTIME FUNCTIONS (Or executing runtime functions)
#
# -------------------------------------------------------------------------------------------------------------

def moduleUtilitySwitchScriptJob():      # This definition is to be modified as necessary.
    """
    Included as MRT startup function in userSetup file. Runs a scriptJob to trigger 
    runtime procedures during maya events.
    """
    jobNumber = cmds.scriptJob(event=['SelectionChanged', moduleUtilitySwitchFunctions], protected=True)
    return jobNumber


def moduleUtilitySwitchFunctions():      # This definition is to be modified as necessary.
    """
    Runtime function called by scriptJob to assist in module operations.
    """
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
    """
    This function is called by moduleUtilitySwitchFunctions() to assist in manipulation of mirrored module pairs
    in the scene. Script jobs are executed for runtime functions to enable mirror movements.
    """
    # To collect nodes created in this function. They'll be added to the mirror move container.
    collected_nodes = []

    for (selection, moduleNamespace) in zip(selections, moduleNamespaces):

        validSelection = returnValidSelectionFlagForModuleTransformObjects(selection)

        # If a valid module control object is selected, proceed.
        if validSelection:

            # Create the mirror move container
            if not cmds.objExists('MRT_mirrorMove__Container'):
                cmds.createNode('container', name='MRT_mirrorMove__Container', skipSelect=True)

            # Multiply divide node for translating mirror control objects
            mirrorTranslateMultiplyDivide = 'MRT_mirrorMove_translate__multiplyDivide'+'_'+moduleNamespace
            cmds.createNode('multiplyDivide', name=mirrorTranslateMultiplyDivide, skipSelect=True)

            collected_nodes.append(mirrorTranslateMultiplyDivide)

            # Get the mirror module namespace and the mirror axis, which is based on the creation plane for the
            # mirrored module pair
            mirrorObject = cmds.getAttr(moduleNamespace+':moduleGrp.mirrorModuleNamespace')+':'+stripMRTNamespace(selection)[1]
            mirrorAxis = {'XY':'Z', 'YZ':'X', 'XZ':'Y'}[str(cmds.getAttr(moduleNamespace+':moduleGrp.onPlane'))[1:]]

            # Get the number of attributes on the selected control
            selectionAttrs = cmds.listAttr(selection, keyable=True, visible=True, unlocked=True)

            # Based on the number of attributes on the selected control, affect the mirror attributes.
            if len(selectionAttrs) == 1: # A Joint module orientation representation control ?
                if re.match('^MRT_\D+__\w+:[_0-9a-z]*transform_orientation_representation_transform$', selection):
                    __MRT_utility_tempScriptJob_list.append(cmds.scriptJob(attributeChange=[str(selection+'.'+selectionAttrs[0]), \
                    partial(updateOrientationRepresentationTransformForMirrorMove, selection, mirrorObject, selectionAttrs[0], \
                                                                                                            moduleNamespace)]))
                else:
                    __MRT_utility_tempScriptJob_list.append(cmds.scriptJob(attributeChange=[str(selection+'.'+selectionAttrs[0]), \
                                      partial(updateChangedAttributeForMirrorMove, selection, mirrorObject, selectionAttrs[0])]))


            if len(selectionAttrs) == 3: # A translate / rotate control ?

                if 'translate' in selectionAttrs[0]:
                    cmds.connectAttr(selection+'.translate', mirrorTranslateMultiplyDivide+'.input1')
                    cmds.connectAttr(mirrorTranslateMultiplyDivide+'.output', mirrorObject+'.translate')
                    collected_nodes.append(cmds.listConnections(mirrorTranslateMultiplyDivide, source=True, destination=True, \
                                                                                                    type='unitConversion'))
                    cmds.setAttr(mirrorTranslateMultiplyDivide+'.input2'+mirrorAxis, -1)

                if 'rotate' in selectionAttrs[0]:
                    __MRT_utility_tempScriptJob_list.append(cmds.scriptJob(attributeChange=[str(selection+'.'+selectionAttrs[0]), \
                                        partial(updateChangedAttributeForMirrorMove, selection, mirrorObject, selectionAttrs[0])]))
                    __MRT_utility_tempScriptJob_list.append(cmds.scriptJob(attributeChange=[str(selection+'.'+selectionAttrs[1]), \
                                        partial(updateChangedAttributeForMirrorMove, selection, mirrorObject, selectionAttrs[1])]))
                    __MRT_utility_tempScriptJob_list.append(cmds.scriptJob(attributeChange=[str(selection+'.'+selectionAttrs[2]), \
                                        partial(updateChangedAttributeForMirrorMove, selection, mirrorObject, selectionAttrs[2])]))


            if 6 < len(selectionAttrs) <= 8: # A splineStartHandleTransform control ?

                cmds.connectAttr(selection+'.translate', mirrorTranslateMultiplyDivide+'.input1')
                cmds.connectAttr(mirrorTranslateMultiplyDivide+'.output', mirrorObject+'.translate')
                collected_nodes.append(cmds.listConnections(mirrorTranslateMultiplyDivide, source=True, destination=True, \
                                                                                                        type='unitConversion'))
                cmds.setAttr(mirrorTranslateMultiplyDivide+'.input2'+mirrorAxis, -1)

                for attr in selectionAttrs[3:]:
                    __MRT_utility_tempScriptJob_list.append(cmds.scriptJob(attributeChange=[str(selection+'.'+attr), \
                                                    partial(updateChangedAttributeForMirrorMove, selection, mirrorObject, attr)]))
                # Node orientation type on spline module
                __MRT_utility_tempScriptJob_list.append(cmds.scriptJob(attributeChange=[str(selection+'.Node_Orientation_Type'), \
                    partial(changeSplineJointOrientationType_forMirror, moduleNamespace, \
                                                        cmds.getAttr(moduleNamespace+':moduleGrp.mirrorModuleNamespace'))]))

                # Proxy geometry
                if 'proxy_geometry_draw' in selectionAttrs:
                    __MRT_utility_tempScriptJob_list.append(cmds.scriptJob(attributeChange=[str(selection+'.proxy_geometry_draw'), \
                        partial(changeSplineProxyGeometryDrawStyleForMirror, moduleNamespace, \
                                                        cmds.getAttr(moduleNamespace+':moduleGrp.mirrorModuleNamespace'))]))


            if len(selectionAttrs) > 8: # Module transform ?

                cmds.connectAttr(selection+'.translate', mirrorTranslateMultiplyDivide+'.input1')
                cmds.connectAttr(mirrorTranslateMultiplyDivide+'.output', mirrorObject+'.translate')
                collected_nodes.append(cmds.listConnections(mirrorTranslateMultiplyDivide, source=True, destination=True, \
                                                                                                        type='unitConversion'))
                cmds.setAttr(mirrorTranslateMultiplyDivide+'.input2'+mirrorAxis, -1)

                # Set multipliers for mirroring module transform values
                multipliersFromMirrorAxis = {'X':[1, -1, -1], 'Y':[-1, 1, -1], 'Z':[-1, -1, 1]}[mirrorAxis]

                for (i, multiplier) in zip([3, 4, 5], multipliersFromMirrorAxis):
                    __MRT_utility_tempScriptJob_list.append(cmds.scriptJob(attributeChange=[str(selection+'.'+selectionAttrs[i]), \
                                partial(updateChangedAttributeForMirrorMove, selection, mirrorObject, selectionAttrs[i], multiplier)]))

                for attr in selectionAttrs[6:]:
                    __MRT_utility_tempScriptJob_list.append(cmds.scriptJob(attributeChange=[str(selection+'.'+attr), \
                                        partial(updateChangedAttributeForMirrorMove, selection, mirrorObject, attr)]))
                # Proxy geometry
                if 'proxy_geometry_draw' in selectionAttrs:
                    __MRT_utility_tempScriptJob_list.append(cmds.scriptJob(attributeChange=[str(selection+'.proxy_geometry_draw'), \
                        partial(changeProxyGeometryDrawStyleForMirror, moduleNamespace, \
                                                        cmds.getAttr(moduleNamespace+':moduleGrp.mirrorModuleNamespace'))]))

            # Update the mirror move container
            addNodesToContainer('MRT_mirrorMove__Container', collected_nodes, includeHierarchyBelow=True)


def deleteMirrorMoveConnections():
    """
    Kills all scriptJobs required for mirror move operations for modules,
    removes container for mirror nodes.
    """
    # Toggle undo state
    cmds.undoInfo(stateWithoutFlush=False)

    # Kill all mirror utility scriptJobs. 
    global __MRT_utility_tempScriptJob_list

    if len(__MRT_utility_tempScriptJob_list) > 0:

        for job in __MRT_utility_tempScriptJob_list:
            if cmds.scriptJob(exists=job):
                cmds.scriptJob(kill=job)

        __MRT_utility_tempScriptJob_list = []

    # Delete mirror nodes
    if cmds.objExists('MRT_mirrorMove__Container'):
        cmds.delete('MRT_mirrorMove__Container')

    cmds.undoInfo(stateWithoutFlush=True)


def updateChangedAttributeForMirrorMove(selection, mirrorObject, attribute, multiplier=None):
    """
    This function is called by a scriptJob to affect a control's mirror attributes where the
    control is a part of a mirrored module pair. Used in setupMirrorMoveConnections().
    """
    # Get the value of a control's attribute
    value = cmds.getAttr(selection+'.'+attribute)

    # If a multiplier is passed-in, use it.
    if multiplier:
        value = value * multiplier

    # Affect the mirror control attribute.
    cmds.setAttr(mirrorObject+'.'+attribute, value)


def updateOrientationRepresentationTransformForMirrorMove(selection, mirrorObject, attribute, namespace):
    """
    This function is called by a scriptJob when "orientation_representation_transform" control
    for a mirrored joint module is selected. It mirrors the rotation of the aim axis movement
    of the control to its mirror. Used in setupMirrorMoveConnections().
    """
    # Get the value of the "orientation representation transform" control aim axis rotation.
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
    """
    Executed by scriptJob to modify the spline node orientation type by modifying the "Node_Orientation_Type"
    attribute on the spline module start transform.
    """
    selection = mel.eval('ls -sl -type dagNode')

    cmds.lockNode(moduleNamespace+':module_container', lock=False, lockUnpublished=False)

    # If the node orientation type is set to 'World' 
    if cmds.getAttr(moduleNamespace+':splineStartHandleTransform.Node_Orientation_Type') == 0:

        cmds.setAttr(moduleNamespace+':splineStartHandleTransform.Axis_Rotate', 0, keyable=False)
        node_transform_Grp = moduleNamespace+':moduleJointsGrp'
        node_transform_Grp_allChildren = cmds.listRelatives(node_transform_Grp, allDescendents=True, type='joint')
        for transform in node_transform_Grp_allChildren:
            cmds.setAttr(transform+'_pairBlend.rotateMode', 1)

    # IF the node orientation type is set to 'Object'
    if cmds.getAttr(moduleNamespace+':splineStartHandleTransform.Node_Orientation_Type') == 1:

        cmds.setAttr(moduleNamespace+':splineStartHandleTransform.Axis_Rotate', keyable=True)
        node_transform_Grp = moduleNamespace+':moduleJointsGrp'
        node_transform_Grp_allChildren = cmds.listRelatives(node_transform_Grp, allDescendents=True, type='joint')
        for transform in node_transform_Grp_allChildren:
            cmds.setAttr(transform+'_pairBlend.rotateMode', 2)

    cmds.lockNode(moduleNamespace+':module_container', lock=True, lockUnpublished=True)
    cmds.select(selection)

def changeSplineJointOrientationType_forMirror(moduleNamespace, mirrorModuleNamespace): 
    """
    Executed when one of the mirrored module pairs of a spline module is modified. 
    Called in setupMirrorMoveConnections() by a scriptJob. Modifies the spline node orientation type 
    on modules in a mirrored module pair for a selected spline module (part of the pair).
    """
    selection = mel.eval('ls -sl -type dagNode')

    cmds.lockNode(moduleNamespace+':module_container', lock=False, lockUnpublished=False)
    cmds.lockNode(mirrorModuleNamespace+':module_container', lock=False, lockUnpublished=False)

    if cmds.getAttr(moduleNamespace+':splineStartHandleTransform.Node_Orientation_Type') == 0:

        cmds.setAttr(moduleNamespace+':splineStartHandleTransform.Axis_Rotate', 0, keyable=False)
        cmds.setAttr(mirrorModuleNamespace+':splineStartHandleTransform.Axis_Rotate', 0, keyable=False)

        node_transform_Grp = moduleNamespace+':moduleJointsGrp'
        node_transform_Grp_allChildren = cmds.listRelatives(node_transform_Grp, allDescendents=True, type='joint')
        for transform in node_transform_Grp_allChildren:
            cmds.setAttr(transform+'_pairBlend.rotateMode', 1)

        node_transform_Grp = mirrorModuleNamespace+':moduleJointsGrp'
        node_transform_Grp_allChildren = cmds.listRelatives(node_transform_Grp, allDescendents=True, type='joint')
        for transform in node_transform_Grp_allChildren:
            cmds.setAttr(transform+'_pairBlend.rotateMode', 1)

    if cmds.getAttr(moduleNamespace+':splineStartHandleTransform.Node_Orientation_Type') == 1:

        cmds.setAttr(moduleNamespace+':splineStartHandleTransform.Axis_Rotate', keyable=True)
        cmds.setAttr(mirrorModuleNamespace+':splineStartHandleTransform.Axis_Rotate', keyable=True)

        node_transform_Grp = moduleNamespace+':moduleJointsGrp'
        node_transform_Grp_allChildren = cmds.listRelatives(node_transform_Grp, allDescendents=True, type='joint')
        for transform in node_transform_Grp_allChildren:
            cmds.setAttr(transform+'_pairBlend.rotateMode', 2)

        node_transform_Grp = mirrorModuleNamespace+':moduleJointsGrp'
        node_transform_Grp_allChildren = cmds.listRelatives(node_transform_Grp, allDescendents=True, type='joint')
        for transform in node_transform_Grp_allChildren:
            cmds.setAttr(transform+'_pairBlend.rotateMode', 2)

    cmds.lockNode(moduleNamespace+':module_container', lock=True, lockUnpublished=True)
    cmds.lockNode(mirrorModuleNamespace+':module_container', lock=True, lockUnpublished=True)
    cmds.select(selection)

def changeProxyGeometryDrawStyle(moduleNamespace):
    """
    Toggle the transparency (vertex) draw style for the module proxy geometry, if it exists.
    This function is executed by a scriptJob. See moduleUtilitySwitchFunctions().
    """
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
    """
    Toggle the transparency (vertex) draw style for proxy geometry for a mirrored module pair.
    This function is executed by a scriptJob. See setupMirrorMoveConnections().
    """
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
    """
    Toggle the transparency (vertex) draw style for a spline module proxy geometry, if it exists.
    This function is executed by a scriptJob. See moduleUtilitySwitchFunctions().
    """
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
    """
    Toggle the transparency (vertex) draw style for proxy geometry for a mirrored spline module pair.
    This function is executed by a scriptJob. See setupMirrorMoveConnections().
    """
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


# --------------------------------------------------- END -----------------------------------------------------
