# *************************************************************************************************************
#
#    mrt_controlRig_src.py - Contains the standard base and derived control rig classes for 
#                            functioning with modular rigging tools.
#
#    Can be modified or copied for your own purpose. Please don't break what works ;)
#
#    Written by Himanish Bhattacharya 
#
# *************************************************************************************************************

import maya.cmds as cmds
import maya.mel as mel
import re, math, os, math

# Import MRT base and utility functions.
import mrt_functions as mfunc
# Import functions for creating objects.
import mrt_objects as objects


"""
First we'll define the base control class, "BaseJointControl". This class will contain methods for defining controls 
that can be created/applied on all joint hierarchies. Please note that this class will only be derived from, and hence I'll 
not override any methods in it. The methods in this class will not be directly called for creating controls, but its subclass
named "JointControl" will be defined to call the methods derived from its superclass "BaseJointControl". All children of the 
"JointControl" class can override methods derived from it.
"""

"""
For correct functionality, please provide a docstring describing the control type of the class while defining it. For this 
purpose, always provide the docstring before stating class attributes and/or methods. The docstring for a control type class 
has to be formatted correctly with escape sequences.
"""

"""
When defining a control rig method, name the function with the prefix "apply", and then add the control rig name starting 
with an upper-case. For eg, to name a method to create an fk control rig, use the name "applyFK" or "applyFk".
"""


# Get the version of maya.
_maya_version = mfunc.returnMayaVersion()


class BaseJointControl(object):       # <object> For DP inheritance search order, and to track using __subclasses__().

    """Base control class to contain common control rigging methods and will be used solely for inheritance and to
    track all subclasses."""

    # Next, we'll define a class attribute which will store the "hierarchy" structure in a string for a custom hierarchy
    # type, created from multiple modules using "hierarchical" parent relationship(s). This string is used for checking
    # whether the current selected joint hierarchy matches the profile to work with the control rig methods defined in a
    # class. You only need to change the value of this attribute in a derived class, if you want to write a control
    # type (class) to work specifically with a custom joint hierarchy in a character. For an example, see the
    # class "CustomLegControl".

    # I'm creating a class attribute here since it can be retrieved faster without creating an instance for evaluation.
    customHierarchy = None


    def __init__(self, *args, **kwargs):

        '''Initializing instance attributes for use in all methods to be defined.'''
        
        # Get the argument values.
        
        if 'characterName' in kwargs:
            characterName = kwargs['characterName']
        elif len(args) > 0:
            characterName = args[0]
        else:
            characterName = 'default'
            
        if 'rootJoint' in kwargs:
            rootJoint = kwargs['rootJoint']
        elif len(args) > 1:
            rootJoint = args[1]
        else:
            cmds.error('No root joint specified for "%s" __init__(). Aborting.' % self.__class__.__name__)
            
        if 'ctrlRig' in kwargs:
            ctrlRig = kwargs['ctrlRig']
        elif len(args) > 2:
            ctrlRig = args[2]
        else:
            cmds.error('No control rig name specified for "%s" __init__(). Aborting.' % self.__class__.__name__)
            

        # Get the user-defined name for the character.
        self.characterName = characterName

        # Get the user-defined for the selected joint hierarchy on which control is to be applied.
        self.userSpecName = rootJoint.partition('_root_node_joint')[0]

        # Get the name of the root transform control (Large red-blue coloured cross-shaped control).
        self.ch_root_cntl = 'ROOT_CNTL'

        # Get the name of the character world transform control (Large grey-coloured control curve with four arrows).
        self.ch_world_cntl = 'WORLD_CNTL'
        
        # Get the global scaling attribute.
        self.globalScaleAttr = 'ROOT_CNTL.globalScale'

        # Get the name of the root joint of the selected hierarchy.
        self.rootJoint = rootJoint
        
        # The root joint has these custom attributes with values that you may use in a control rig definition.
        #
        # nodeAxes - The axes orientation order for joints in the selected hierarchy for control rigging,
        #            for which the root joint is passed-in. Originating from the module node axes during creation,
        #            it has three upper case characters, X Y and Z in an order. If the nodeAxes is "XYZ", X is the 
        #            aim, Y is the up and Z is the plane (creation plane) axis for joint orientation in the hierarchy.
        # 
        # plane - The creation plane for the originating module for the selected joint hierarchy. It can have the 
        #         following values, XY, YZ and XZ with a - or + sign preceding it. The plane attribute is useful when 
        #         working with joint hierarchy which is created from mirrored module pair. It shows the mirroring plane
        #         and the sign shows the direction of the aim axis down the joint hierarchy. If it's -ve, then it's reversed.
        #
        # translationFunction - This is used for orienting non FK based controls in a control rig definition for the
        #                       selected joint hierarchy. It can have the value, 'local_orientation' or 'world'. This attribute
        #                       is derived from 'translation transform function' during module creation. If set to 'local_orientation', 
        #                       a non FK control for the joint hierarchy can be oriented locally to the closest joint or use
        #                       any other technique that you may wish to have in a control rig definition. If set to 'world',
        #                       the non FK control can have world orientation. 
        #                       
        # rotationFunction - This is used for orienting FK based controls in a control rig definition. It can have the value,
        #                    'behaviour' or 'orientation'. This attribute is derived from 'rotation transform function' during 
        #                    module creation and is useful when writing control definitions for mirrored joint hierarchies,
        #                    created from mirrored module pair(s). If this is set to 'behaviour', then the aim axes for the 
        #                    hierarchies are reversed, as others. Hence, use these values to check for the current orientation 
        #                    of joints, and create the FK controls as necessary.
        #
        # There are other custom attributes which are specific only for joint hierarchies created from :
        #
        # ikSegmentMidPos - For joint hierarchies created from HingeNode module. It stores the world space position of the hinge
        #                   joint (to be used as a knee or elbow) projected on the line segment between the root and end joints.
        #                   A joint hierarchy created from a HingeNode module has three joints (two bones).
        #
        # splineOrientation - For joint hierarchies created from SplineNode module. This attribute is derived from 'node orientation type'
        #                     attribute for the SplineNode module. It can have the value 0 or 1. If set to 0, then the joints in 
        #                     the hierarchy have world orientation, so create the spine controls in that fashion. If set to 1, 
        #                     then the joints have local orientation.
        #
        # You may notice that there are other attributes as well, but they're for other internal use and are not necessary 
        # when writing definitions for control rigging.


        # Get the colour index value of the control rig colour slider from modular rigging tools window.
        self.controlColour = cmds.colorIndexSliderGrp('__MRT_controlLayerColour_IndexSliderGrp', query=True, value=True) - 1

        # Get a list of all joints in the "skinJointList" set.
        allJoints = cmds.getAttr('|%s.skinJointList' % characterName).split(',')

        # Find and sort the names of joints in the selected joint hierarchy from "allJoints".
        self.selCharacterHierarchy = []
        rootJointAllChildren = cmds.listRelatives(rootJoint, allDescendents=True, type='joint')
        if rootJointAllChildren:
            self.selCharacterHierarchy = list(set.intersection(set(allJoints), set(rootJointAllChildren)))
        self.selCharacterHierarchy.append(rootJoint)
        self.selCharacterHierarchy.sort()

        # List to store the driver joint layer set.
        self.driverJointLayerSet = []

        # List to store the names of constraints by which the driver joint layer will drive its main joint hierarchy
        # in a character.
        self.driverConstraintsForInput = []

        # Get the number of joints in the selected joint hierarchy.
        self.numJoints = len(self.selCharacterHierarchy)

        # Get the orientation type for any translation control that might be created.
        # This option was specified when its module was created, before it was converted into a joint hierarchy (character).
        # For this you'll get one of the two values, "world" or "local_orientation".
        self.transOriFunc = cmds.getAttr(rootJoint+'.translationFunction')

        # Get the user specified name for the hierarchy, nice name for the control rig layer, and create the name prefix.
        self.ctrlRigName = ''.join([item.title() for item in ctrlRig.split('_')])
        self.namePrefix = self.userSpecName + '_' + self.ctrlRigName
        
        # Create a container for the control rig.
        self.ctrl_container = cmds.createNode('container', name='MRT_%s__%s_container' % (self.userSpecName, self.ctrlRigName), skipSelect=True)
        
        # Create a generator function to create a control rig group if desired, which can be used to create one inside a control rig method (optional).
        self.ctrlGrp = self.namePrefix + '_ctrlGrp'         # This attribute is to be used only if the control rig group is created.
        self.createCtrlGrp = lambda *CG: cmds.group(empty=True, name=self.ctrlGrp, parent='|%s|controls' % self.characterName)
        
        # Get the name of the control rig display layer.
        self.controlRigDisplayLayer = 'MRT_%s_control_rig' % characterName
        
        # Reset all controls on the character to their default positions, if any.
        # This will also turn off any control weights and their visibility for the selected joint hierarchy.
        # This is to allow the new control rig on the selected hierarchy to have full control, useful for testing.
        self.resetAllControls()
        self.toggleHierarchyCtrlWeights()
        self.toggleHierarchyCtrlVisibility()

        # Force update on all joint attributes, after resetAllControls().
        for joint in allJoints:
            cmds.getAttr(joint+'.translate')
            cmds.getAttr(joint+'.rotate')
            cmds.getAttr(joint+'.scale')

        # To collect nodes to be added to the control rig container.
        self.collectedNodes = []


    def getCtrlNiceNameForPublish(self, ctrl):
        '''
        Returns a nice name for publishing a control/transform name for a container.
        Eg., "l_arm_root_node_CNTL" returns "lArmRootNodeCntl".
        '''
        name_tokens = ctrl.split('_')
        if name_tokens > 1:
            return name_tokens[0].lower() + ''.join([token.title() for token in name_tokens[1:]])
        else:
            return None
    
    
    def getHierarchyCtrlContainers(self):

        '''This class method will return a list of all containers in the scene for control rigs currently applied to the
        a joint hierarchy.'''

        containers = []

        # Get the list of control rigs applied to a joint hierarchy stored as a string value.
        rigLayers = cmds.getAttr(rootJoint+'.rigLayers')

        # Collect the container names and return them.
        if rigLayers != 'None':
            rigLayers = rigLayers.split(',')
            for layer in rigLayers:
                rigLayerName = ''.join([item.title() for item in layer.split('_')])
                name = 'MRT_%s__%s_container' % (self.userSpecName, rigLayerName)
                containers.append(name)

        return containers


    def toggleAllCtrlWeights(self, value=0):

        '''This method will toggle all weights for all existing control rigs in a character by using the attributes created
        on the character root transform control.'''

        # Get the custom attributes on the character root transform.
        ctrl_attribs = cmds.listAttr(self.ch_root_cntl, userDefined=True)

        # Find the attributes to toggle visibility and set them.
        if ctrl_attribs:
            for attr in ctrl_attribs[3:]:
                if not attr.endswith('visibility'):
                    cmds.setAttr(self.ch_root_cntl+'.'+attr, value)


    def resetAllControls(self):

        '''Resets all the control transforms to their initial positions, and removes any keys set on them.'''

        # Reset the time.
        cmds.currentTime(0)

        # Collect the character root and world transform controls, and all the control rig containers currently in the scene.
        nodes = []
        nodes.extend([item for item in cmds.ls(type='transform') \
                      if re.match('^(WORLD|ROOT)_CNTL$', item)])
        nodes.extend([item for item in cmds.ls(type='container') \
                      if re.match('^MRT_\w+__[0-9a-zA-Z]*_container$', item)])

        # Iterate through the nodes, remove all keyframes, and set the channel attributes.
        for node in nodes:
            mel.eval('cutKey -t ":" '+node+';')
            ctrlAttrs = cmds.listAttr(node, keyable=True, visible=True, unlocked=True) or []

            if ctrlAttrs:
                for attr in ctrlAttrs:
                    if re.search('(translate|rotate){1}', attr):
                        cmds.setAttr(node+'.'+attr, 0)
                    if re.search('(scale|globalScale){1}', attr):
                        cmds.setAttr(node+'.'+attr, 1)


    def toggleHierarchyCtrlWeights(self, value=0):

        '''Toggles the weight of all control rigs currently applied to a joint hierarchy.'''

        # Get the custom attributes on the character root transform control.
        ctrl_attribs = cmds.listAttr(self.ch_root_cntl, userDefined=True)
        # Set the value of the attributes on the root transform to toggle weights for control rig layer(s).
        if ctrl_attribs:
            for attr in ctrl_attribs[3:]:
                attrUserSpec = re.split('_[A-Z]', attr)[0]
                if re.match('^%s$' % (self.userSpecName), attrUserSpec):
                    if not attr.endswith('visibility'):
                        cmds.setAttr(self.ch_root_cntl+'.'+attr, value)


    def toggleHierarchyCtrlVisibility(self, value=0):

        '''Toggles the visibility of all control rigs currently applied to a joint hierarchy.'''

        # Get the custom attributes on the character root transform control.
        ctrl_attribs = cmds.listAttr(self.ch_root_cntl, userDefined=True)
        # Set the visibility of the controls currently applied to a joint hierarchy.
        if ctrl_attribs:
            for attr in ctrl_attribs[3:]:
                attrUserSpec = re.split('_[A-Z]', attr)[0]
                if re.match('^%s$' % (self.userSpecName), attrUserSpec):
                    if attr.endswith('visibility'):
                        cmds.setAttr(self.ch_root_cntl+'.'+attr, value)


    def createCtrlRigWeightAttributeOnRootTransform(self, ctrlAttr, visibility_nodes=[]):

        '''Creates a custom attribute on the character root transform for controlling the weight of a control rig layer on
        a joint hierarchy in a character. It accepts the attribute name to be created for the control rig and the list of 
        transform controls in the control rig (optional) to toggle visibility.'''

        # Add the custom attribute for the control rig layer on the character root transform control.
        cmds.addAttr(self.ch_root_cntl, attributeType='float', longName=ctrlAttr, hasMinValue=True, hasMaxValue=True, \
                     minValue=0, maxValue=1, defaultValue=1, keyable=True)

        # Connect the control rig attribute to drive its joint layer.
        # Go through the list of names in the driver joint layer set.
        for joint in self.driverJointLayerSet:

            # Go through the list of names for the constraint nodes (point and orient) used to connect the driver joint
            # layer for the control rig to the joint hierarchy.
            for constraint in self.driverConstraintsForInput:
                constrainResult = mfunc.returnConstraintWeightIndexForTransform(joint, constraint)
                if constrainResult:
                    constraintAttr = constrainResult[1]
                    cmds.connectAttr(self.ch_root_cntl+'.'+ctrlAttr, constraint+'.'+constraintAttr)

        # If transform controls for the control rig is passed-in for toggling their visibility, create the necessary
        # attribute and connect it.
        if visibility_nodes:
            cmds.addAttr(self.ch_root_cntl, attributeType='bool', longName=ctrlAttr+'_visibility', defaultValue=1, \
                         keyable=True)
            for node in visibility_nodes:
                cmds.connectAttr(self.ch_root_cntl+'.'+ctrlAttr+'_visibility', node+'.visibility')

                
    def createParentSwitchGrpForTransform(self, *args, **kwargs):

        '''Creates a parent group node for a given control transform (above its pre-transform or pivot, if specified), 
        so it can receive multiple constraints from other transforms as parent targets. It also creates custom attributes 
        on the given control transform to switch between such parents. Optionally, you can add the character root transform 
        as a parent target, and set its weight. You can also specify if the control transform needs to be scaled along with 
        the character root transform, if it is not a part of a joint hierarchy in a character.'''
        
        if 'ctrl' in kwargs:
            ctrl = kwargs['ctrl']
        elif len(args) > 0:
            ctrl = args[0]
        else:
            cmds.error('No control transform specified for createParentSwitchGrpForTransform()')
        
        if 'pivot' in kwargs:
            pivot = kwargs['pivot']
        elif len(args) > 1:
            pivot = args[1]
        else:
            pivot = ctrl
        
        # Check if the character root control is to be added as a parent target.
        if 'constrainToRootCtrl' in kwargs:
            constrainToRootCtrl = kwargs['constrainToRootCtrl']
        elif len(args) > 2:
            constrainToRootCtrl = args[2]
        else:
            constrainToRootCtrl = False

        if 'weight' in kwargs:
            weight = kwargs['weight']
        elif len(args) > 3:
            weight = args[3]
        else:
            weight = 0
            
        if 'connectScaleWithRootCtrl' in kwargs:
            connectScaleWithRootCtrl = kwargs['connectScaleWithRootCtrl']
        elif len(args) > 4:
            connectScaleWithRootCtrl = args[4]
        else:
            connectScaleWithRootCtrl = False
            
        # Create the parent switch group node which will receive the constraints from target parent transforms.
        parentSwitch_grp = cmds.group(empty=True, name=ctrl + '_parentSwitch_grp')
        cmds.delete(cmds.parentConstraint(pivot, parentSwitch_grp, maintainOffset=False))
        self.collectedNodes.append(parentSwitch_grp)

        # Add custom attributes to the group node.
        cmds.addAttr(ctrl, attributeType='enum', longName='targetParents', enumName='None:', keyable=True)
        cmds.addAttr(parentSwitch_grp, dataType='string', longName='parentTargetList', keyable=False)
        cmds.setAttr(parentSwitch_grp+'.parentTargetList', 'None', type='string', lock=True)
        
        # Get the parent transform for the given control transform's pivot (or pre-transform), if specified.
        transformParent = cmds.listRelatives(pivot, parent=True) or None
        
        # Now, place the parent switch group under the obtained parent transform from above.
        if transformParent:
            cmds.parent(parentSwitch_grp, transformParent[0], absolute=True)
            
        # Place the pivot (or pre-transform) for the given control transform under the parent switch group.
        cmds.parent(pivot, parentSwitch_grp, absolute=True)

        # Add the character root control as a parent switch target, if specified.
        if constrainToRootCtrl:
            
            # Constrain the character root control,
            if cmds.objectType(ctrl, isType='joint'):
                constraint = mfunc.orientConstraint(self.ch_root_cntl, parentSwitch_grp, maintainOffset=True, 
                                                    name=parentSwitch_grp+'_orient')
            else:
                constraint = mfunc.parentConstraint(self.ch_root_cntl, parentSwitch_grp, maintainOffset=True, 
                                                    name=parentSwitch_grp+'_parent')
                
            # Add a custom attribute "targetParents" to store the target list, and for the user to switch them.
            cmds.addAttr(ctrl+'.targetParents', edit=True, enumName='None:'+self.ch_root_cntl)
            
            # Create a condition to set the weight of parent target based on the value of "targetParents".
            # Here the parent target is the character root control.
            parentSwitchCondition = cmds.createNode('condition',
                                                    name=ctrl+'_'+self.ch_root_cntl+'_parentSwitch_condition', 
                                                    skipSelect=True)
            
            # Set/Connect the condition to set the target parent upon switching target(s) under "targetParents".
            cmds.setAttr(parentSwitchCondition+'.firstTerm', 1)
            cmds.setAttr(parentSwitchCondition+'.colorIfTrueR', 1)
            cmds.setAttr(parentSwitchCondition+'.colorIfFalseR', 0)            
            cmds.connectAttr(ctrl+'.targetParents', parentSwitchCondition+'.secondTerm')
            cmds.connectAttr(parentSwitchCondition+'.outColorR', constraint+'.'+self.ch_root_cntl+'W0')
            
            # Set the current target as the character root control, if set.
            if weight == 1:
                cmds.setAttr(ctrl+'.targetParents', 1)
            
            # Update the "parentTargetList" on the parent switch group.
            cmds.setAttr(parentSwitch_grp+'.parentTargetList', lock=False)
            cmds.setAttr(parentSwitch_grp+'.parentTargetList', self.ch_root_cntl, type='string', lock=True)
            
            # Add the parent switch condition and the control to the control rig container, since 'targetParents' on ctrl needs to be published.
            mfunc.addNodesToContainer(self.ctrl_container, [ctrl, parentSwitchCondition])
            
            # Publish the 'targetParents' attribute on the control.
            ctrlName = self.getCtrlNiceNameForPublish(ctrl)
            cmds.container(self.ctrl_container, edit=True, publishAndBind=[ctrl+'.targetParents', ctrlName+'_targetParents'])

        # Connect the scaling on the character root transform to the parent switch group node.
        if connectScaleWithRootCtrl:
            cmds.connectAttr(self.globalScaleAttr, parentSwitch_grp+'.scaleX')
            cmds.connectAttr(self.globalScaleAttr, parentSwitch_grp+'.scaleY')
            cmds.connectAttr(self.globalScaleAttr, parentSwitch_grp+'.scaleZ')

        return parentSwitch_grp


    def applyFK(self):

        '''Creates control layer for simple FK on a character hierarchy.'''

        # First, use the scene utility function "createFKlayerDriverOnJointHierarchy" to create a joint layer over the
        # original (selected) character joint hierarchy. This layer will drive the joint hierarchy and its influence (weight)
        # can also be modified. See "mrt_functions.py", for details.

        # "createFKlayerDriverOnJointHierarchy" has the following arguments :

        # characterJointSet -> For this, we want the selected joint hierarchy, which will be controlled by creating a driver
        # joint layer. Pass-in the self.selCharacterHierarchy variable.
        #
        # jointLayerName -> Name for the joint layer. If you want to create a driver joint layer, you'd want to name it as
        # the control type that you're trying to create. Just pass-in the self.ctrlRigName.
        #
        # characterName -> User specified name for the character. In this case, pass-in the self.characterName variable.
        #
        # asControl -> A suffix "_CNTL" will be added to each joint name for the returned joint layer indicating that
        # these joints would be used as direct control transforms, to keep up with the naming convention. For eg, this can
        # be done while creating a direct FK control layer over the joint hierarchy, which will drive it. This suffix will
        # be added only if this argument is set to True, or it'll be an empty string. Default is False.
        #
        # layerVisibility -> Set this to 'On' if you want to control the visibility of the joint layer using the joints
        # display layer, otherwise, set to 'None', where the joint layer would be hidden (default, 'On').
        #
        # transFilter -> To negate the initial value of translation and scale values from driver joints. If you notice any
        # double transformation while applying a control, set to True. Default is False.
        #
        # controlLayerColour -> Pass-in a maya colour index for the joint layer (default is None).
        #
        # connectLayer -> Connect the joint layer to act as a driver. You'll want to keep this as True if you want the joint
        # layer to drive the original hierarchy. Within a control rig method, you can call "createFKlayerDriverOnJointHierarchy"
        # more than one time to create multiple joint layers, but only one should drive the original joint hierarchy.
        # (default is True).


        # The "createFKlayerDriverOnJointHierarchy" function returns a tuple (newJointSet, driver_constraints, layerRootJoint)
        # which has the following elements:

        # newJointSet -> List containing the names of all joints in the new joint layer.
        #
        # driver_constraints -> List of names of constraint nodes (for translation and rotation) whose weight attributes for
        # the joint layer can be connected for controlling the weight of the joint layer driving the joint hierarchy passed
        # on as the "characterJointSet" to the function.
        #
        # layerRootJoint -> String value for the name of the root joint in the joint layer. This name is also included in
        # the "newJointSet", but is returned here for convenience.


        # You can control the weight of a "driver" joint layer over a joint hierarchy by using the method,
        # "self.createCtrlRigWeightAttributeOnRootTransform". See the method above.

        # For FK control, we'll need only one joint layer, which will also act as the driver. Notice the connectLayer is set
        # to True(last argument). This layer will be controlled directly (notice 'asControl' is set to True).
        
        jointSet, driver_constraints, layerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                                 self.ctrlRigName,
                                                                                                 self.characterName,
                                                                                                 True,           # asControl=True
                                                                                                 'On',
                                                                                                 True,
                                                                                                 self.controlColour,
                                                                                                 True)
        # Collect the driver joints to be added to the control rig container.
        self.collectedNodes.extend(jointSet)
        
        # Update the instance attribute to contain the driver joint layer set.
        self.driverJointLayerSet = jointSet

        # Update the instance attribute to contain the driver constraints for the joint hiearachy.
        self.driverConstraintsForInput = driver_constraints        
        
        # Calculate the size of shape for the FK control.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.35

        # Create a parent switch group for the root FK control joint.
        self.createParentSwitchGrpForTransform(layerRootJoint, constrainToRootCtrl=True)

        # For all the joints in the new layer, lock and hide the translation and scale attributes (only rotation for
        # FK control), attach a custom shape, and set colour and visibility.
        for joint in jointSet:
            cmds.setAttr(joint+'.drawStyle', 2)
            mfunc.lockHideChannelAttrs(joint, 't', 's', 'radi', keyable=False, lock=True)
            cmds.setAttr(joint+'.overrideEnabled', 1)
            cmds.setAttr(joint+'.overrideColor', self.controlColour)
            cmds.setAttr(joint+'.visibility', keyable=False)

            # Load and attach a custom locatorShape to a transform. See the MRT documentation for utility and scene
            # functions available for use.
            xhandle = objects.load_xhandleShape(joint, colour=self.controlColour, transformOnly=True)

            cmds.setAttr(xhandle['shape']+'.localScaleX', shapeRadius)
            cmds.setAttr(xhandle['shape']+'.localScaleY', shapeRadius)
            cmds.setAttr(xhandle['shape']+'.localScaleZ', shapeRadius)
            cmds.setAttr(xhandle['shape']+'.drawStyle', 5)

        # Create a custom keyable attribute on the character root transform by the control name to adjust the weight of the
        # driver joint layer by using the method "createCtrlRigWeightAttributeOnRootTransform".
        self.createCtrlRigWeightAttributeOnRootTransform(self.namePrefix, jointSet)

        # Add the joint layer nodes to the control rig container.
        mfunc.addNodesToContainer(self.ctrl_container, self.collectedNodes, True)

        # Publish the rotate attribute on the driver layer joints (which is used for direct control).
        for joint in jointSet:
            jointName = self.getCtrlNiceNameForPublish(joint)
            cmds.container(self.ctrl_container, edit=True, publishAndBind=[joint+'.rotate', jointName+'_rotate'])
            
        cmds.select(clear=True)


    def applyFK_Stretchy(self):

        '''Creates control layer for simple, scalable fk on a character hierarchy.'''

        # The procedure is the same as FK_Control, with scale added.

        # Create the driver joint layer on top of the selected joint hierarchy.
        jointSet, driver_constraints, layerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                                 self.ctrlRigName,
                                                                                                 self.characterName,
                                                                                                 True,           # asControl=True
                                                                                                 'On',
                                                                                                 True,
                                                                                                 self.controlColour,
                                                                                                 True)
        # Collect the driver joints to be added to the control rig container.
        self.collectedNodes.extend(jointSet)        

        # Update the instance attribute for the driver joint layer set.
        self.driverJointLayerSet = jointSet

        # Update the instance attribute to contain the driver constraints for the joint hierarachy.
        self.driverConstraintsForInput = driver_constraints

        # Calculate the size of shape for the FK control.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.35

        # Create a parent switch group for the root FK control joint.
        self.createParentSwitchGrpForTransform(layerRootJoint, constrainToRootCtrl=True)

        # For all the joints in the new layer, lock and hide the translation attributes, attach a custom shape,
        # and set colour and visibility.
        for joint in jointSet:
            cmds.setAttr(joint+'.drawStyle', 2)
            mfunc.lockHideChannelAttrs(joint, 't', 'radi', keyable=False, lock=True)
            cmds.setAttr(joint+'.overrideEnabled', 1)
            cmds.setAttr(joint+'.overrideColor', self.controlColour)
            cmds.setAttr(joint+'.visibility', keyable=False)

            xhandle = objects.load_xhandleShape(joint, colour=self.controlColour, transformOnly=True)
            cmds.setAttr(xhandle['shape']+'.localScaleX', shapeRadius)
            cmds.setAttr(xhandle['shape']+'.localScaleY', shapeRadius)
            cmds.setAttr(xhandle['shape']+'.localScaleZ', shapeRadius)
            cmds.setAttr(xhandle['shape']+'.drawStyle', 5)

        # Create a custom keyable attribute on the character root transform by the control name to adjust the
        # weight of the driver joint layer by using the method "createCtrlRigWeightAttributeOnRootTransform".
        self.createCtrlRigWeightAttributeOnRootTransform(self.namePrefix, jointSet)

        # Add the joint layer nodes (along with its parent switch group) to the control rig container.
        mfunc.addNodesToContainer(self.ctrl_container, self.collectedNodes, True)

        # Publish the rotate and scale attributes on the driver layer joints (which is used for direct control).
        for joint in jointSet:
            jointName = self.getCtrlNiceNameForPublish(joint)
            cmds.container(self.ctrl_container, edit=True, publishAndBind=[joint+'.rotate', jointName+'_rotate'])
            cmds.container(self.ctrl_container, edit=True, publishAndBind=[joint+'.scale', jointName+'_scale'])
            
        cmds.select(clear=True)


class JointControl(BaseJointControl):

    """Base joint control rigs, which will work on any type of joint hierarchy, created from single or multiple modules."""

    def __init__(self, *args, **kwargs):
        # All methods are derived from BaseJointControl, which are FK control and FK Control Stretchy.
        BaseJointControl.__init__(self,  *args, **kwargs)


class CustomLegControl(BaseJointControl):

    """This is a custom hierarchy type which is constructed from a collection of (1) hinge module consisting\nof a hip,
    knee and an ankle with two joint modules connected to the ankle node of the hingle module as children(hierarchical 
    parent type). The (2) first joint module should contain two nodes resembling a ball and toe for a foot, and a 
    (3) third node for a heel."""

    # This string value must be store between multiline quotes, ''', as shown below.
    customHierarchy = \
    '''
    <HingeNode>_root_node_joint
        <HingeNode>_node_1_joint
            <HingeNode>_end_node_joint
                <JointNode>_root_node_joint
                <JointNode>_root_node_joint
                    <JointNode>_end_node_joint
    '''
    # This 'customHierarchy' variable is use to store the string value, which is used to check and match if the selected
    # custom joint hierarchy for control rigging can be applied with methods described in this class, or if it meets the exact
    # joint hierarchy structure required by its methods.

    # The joint hiearchy string for a selected joint hierarchy (created using MRT) can be returned using one of the utility
    # functions, "returnHierarchyTreeListStringForCustomControlRigging".
    # It accepts two arguments: returnHierarchyTreeListStringForCustomControlRigging(rootJoint, prefix='')

    # rootJoint -> Pass-in the root joint for the hierarchy.
    #
    # prefix -> A prefix string that can be used for naming the joints, which is returned with the result.

    # Usage :

    # If the variable 'customHiearchy' is used to store the string output for the result of the function,
    # "returnHierarchyTreeListStringForCustomControlRigging", and then if we print the variable :

    # > customHierarchy = mfunc.returnHierarchyTreeListStringForCustomControlRigging(self.rootJoint, '')  # with no prefix
    # > print customHierarchy
    # <HingeNode>_root_node_joint
    #	    <HingeNode>_node_1_joint
    #		    <HingeNode>_end_node_joint
    #			    <JointNode>_root_node_joint
    #			    <JointNode>_root_node_joint
    #				    <JointNode>_end_node_joint

    # Therefore, copy and paste the printed output of the custom joint hierarchy for the string value for "customHierarchy" as shown above.
    # If you're typing this value by hand, use tab indentation with 4 SPACES ONLY.

    def __init__(self,  *args, **kwargs):
        BaseJointControl.__init__(self,  *args, **kwargs)


    def applyReverse_IK_Leg(self):

        '''Creates controls for a reverse IK leg with a main foot transform and a pole vector transform in auto
        non-flip / manual mode.'''

        # Control group, to be placed under "controls".
        self.createCtrlGrp()
        
        # Add it to the node list to be added to the control rig container.
        self.collectedNodes.append(self.ctrlGrp)
        
        # Get the names of knee, ankle and its children from the original hierarchy.
        origKneeJoint = cmds.listRelatives(self.rootJoint, children=True, type='joint')[0]
        origAnkleJoint = cmds.listRelatives(origKneeJoint, children=True, type='joint')[0]
        origAnkleChildren = cmds.listRelatives(origAnkleJoint, children=True, type='joint')

        # Find the toe and heel joints.
        for child in origAnkleChildren:
            chldJnt = cmds.listRelatives(child, allDescendents=True, type='joint')
            if chldJnt:
                origToeJoint = chldJnt[-1]
                origBallJoint = child
            else:
                origHeelJoint = child

        # Get the positions of ankle, knee and hip to find the IK plane and obtain the perpendicular vector for the leg plane.
        transform1_start_vec = transform2_start_vec = cmds.xform(origKneeJoint, query=True, worldSpace=True, translation=True)
        transform1_end_vec = cmds.xform(origAnkleJoint, query=True, worldSpace=True, translation=True)
        transform2_end_vec = hip_pos = cmds.xform(self.rootJoint, query=True, worldSpace=True, translation=True)
        result = mfunc.returnCrossProductDirection(transform1_start_vec, transform1_end_vec, transform2_start_vec, transform2_end_vec)
        leg_cross_pos = [round(item, 4) for item in result[1]]          # << relative position of vector perpendicular to the leg plane.
        leg_cross_vec = map(lambda x,y:x+y, leg_cross_pos, transform1_start_vec)       # << absolute position of vector perpendicular to the leg plane.

        # Get the positions of heel, toe and the ball joints to find the IK plane and hence the perpendicular vector for
        # the foot plane.
        transform1_start_vec = transform2_start_vec = cmds.xform(origHeelJoint, query=True, worldSpace=True, translation=True)
        transform1_end_vec = cmds.xform(origAnkleJoint, query=True, worldSpace=True, translation=True)
        transform2_end_vec = cmds.xform(origToeJoint, query=True, worldSpace=True, translation=True)
        result = mfunc.returnCrossProductDirection(transform1_start_vec, transform1_end_vec, transform2_start_vec, transform2_end_vec)
        foot_cross_pos = [round(item, 4) for item in result[1]]
        foot_cross_vec = map(lambda x,y:x+y, foot_cross_pos, transform1_start_vec)
        foot_aim_vec = mfunc.returnOffsetPositionBetweenTwoVectors(transform2_start_vec, transform2_end_vec, 1.5)
        foot_vec_dict = {'heel_pos':transform1_start_vec, 'cross':foot_cross_vec, 'aim':foot_aim_vec, 'hip_pos':hip_pos}

        # Create the FK layer for the control rig.
        jointSet, driver_constraints, layerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                                 self.ctrlRigName,
                                                                                                 self.characterName,
                                                                                                 False,
                                                                                                 'None',
                                                                                                 True)
        # Add the joints in the driver layer to be added to the control rig container.
        self.collectedNodes.extend(jointSet)
        
        # Update the instance attribute for the driver joint layer set.
        self.driverJointLayerSet = jointSet

        # Update the instance attribute to contain the driver constraints for the joint hiearachy.
        self.driverConstraintsForInput = driver_constraints

        # Get the names of the hip, knee, ankle, ball, toe and heel joint for the driver layer joint hierarchy.
        hipJoint = layerRootJoint
        kneeJoint = cmds.listRelatives(hipJoint, children=True, type='joint')[0]
        ankleJoint = cmds.listRelatives(kneeJoint, children=True, type='joint')[0]
        ankleChildren = cmds.listRelatives(ankleJoint, children=True, type='joint')
        for child in ankleChildren:
            chldJnt = cmds.listRelatives(child, allDescendents=True, type='joint')
            if chldJnt:
                ballJoint = child
                toeJoint = chldJnt[-1]
            else:
                heelJoint = child

        # Create an IK RP solver from hip to ankle on the driver joint layer.

        # Disable check for cycle.
        cmds.cycleCheck(evaluation=False)
            
        handleName = self.namePrefix + '_hipAnkleIkHandle'
        effName = self.namePrefix + '_hipAnkleIkEffector'
        
        legIkNodes = cmds.ikHandle(startJoint=hipJoint, endEffector=ankleJoint, name=handleName, solver='ikRPsolver')
        cmds.rename(legIkNodes[1], effName)
        cmds.setAttr(legIkNodes[0]+'.visibility', 0)
        cmds.delete(cmds.orientConstraint(ankleJoint, legIkNodes[0], maintainOffset=False))
        mfunc.updateNodeList(legIkNodes[0])

        # Create IK SC solvers from ankle to ball, and from ball to toe, on the driver joint layer.
        handleName = self.namePrefix + '_ankleBallIkHandle'
        effName = self.namePrefix + '_ankleBallIkEffector'
        
        ballIkNodes = cmds.ikHandle(startJoint=ankleJoint, endEffector=ballJoint, name=handleName, solver='ikSCsolver')
        cmds.rename(ballIkNodes[1], effName)
        cmds.setAttr(ballIkNodes[0]+'.visibility', 0)
        
        handleName = self.namePrefix + '_ballToeIkHandle'
        effName = self.namePrefix + '_ballToeIkEffector'
        
        toeIkNodes = cmds.ikHandle(startJoint=ballJoint, endEffector=toeJoint, name=handleName, solver='ikSCsolver')
        cmds.rename(toeIkNodes[1], effName)
        cmds.setAttr(toeIkNodes[0]+'.visibility', 0)
        
        # Enable check for cycle.
        cmds.cycleCheck(evaluation=True)

        # Create the IK control handle.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.88
        legControl = objects.load_xhandleShape(self.namePrefix+'_CNTL', colour=self.controlColour)
        cmds.setAttr(legControl['shape']+'.localScaleX', shapeRadius)
        cmds.setAttr(legControl['shape']+'.localScaleY', shapeRadius)
        cmds.setAttr(legControl['shape']+'.localScaleZ', shapeRadius)
        cmds.setAttr(legControl['shape']+'.drawStyle', 6)
        mfunc.lockHideChannelAttrs(legControl['transform'], 's', keyable=False, lock=True)
        mfunc.lockHideChannelAttrs(legControl['transform'], 'v', visible=False)
        cmds.addAttr(legControl['transform'], attributeType='enum', longName='Foot_Controls', enumName=' ', keyable=True)
        cmds.setAttr(legControl['transform']+'.Foot_Controls', lock=True)
        cmds.addAttr(legControl['transform'], attributeType='double', longName='Foot_Roll', defaultValue=0, keyable=True)
        cmds.addAttr(legControl['transform'], attributeType='double', longName='Foot_Toe_Lift', defaultValue=30, keyable=True)
        cmds.addAttr(legControl['transform'], attributeType='double', longName='Foot_Toe_Straight', defaultValue=70, keyable=True)
        cmds.addAttr(legControl['transform'], attributeType='double', longName='Knee_Twist', defaultValue=0, keyable=True)
        cmds.addAttr(legControl['transform'], attributeType='double', longName='Foot_Bank', defaultValue=0, keyable=True)
        cmds.addAttr(legControl['transform'], attributeType='double', longName='Ball_Pivot', defaultValue=0, keyable=True)
        cmds.addAttr(legControl['transform'], attributeType='double', longName='Toe_Pivot', defaultValue=0, keyable=True)
        cmds.addAttr(legControl['transform'], attributeType='double', longName='Toe_Curl', defaultValue=0, keyable=True)
        cmds.addAttr(legControl['transform'], attributeType='double', longName='Heel_Pivot', defaultValue=0, keyable=True)
        cmds.addAttr(legControl['transform'], attributeType='enum', longName='Pole_Vector_Mode', minValue=0, maxValue=1, \
                     enumName=':No Flip:Manual', defaultValue=0, keyable=True)
        
        # Align the IK control handle based on the 'translation function' value, inherited from the module state.
        if cmds.attributeQuery('translationFunction', node=legControl['transform'], exists=True) and \
           cmds.getAttr(legControl['transform']+'.translationFunction') == 'local_orientation':
            cmds.xform(legControl['preTransform'], worldSpace=True, translation=\
                       cmds.xform(ankleJoint, query=True, worldSpace=True, translation=True), rotation=\
                       cmds.xform(ankleJoint, query=True, worldSpace=True, rotation=True))

            legControlAxesInfo = mfunc.returnAxesInfoForFootTransform(legControl['transform'], foot_vec_dict)
        else:
            cmds.xform(legControl['preTransform'], worldSpace=True, translation=cmds.xform(ankleJoint, query=True, \
                                                                                              worldSpace=True, translation=True))
            cmds.setAttr(legControl['transform']+'.rotateOrder', 2)
        cmds.parent(legControl['preTransform'], self.ctrlGrp, absolute=True)

        # Create a parent switch grp for the IK control handle.
        self.createParentSwitchGrpForTransform(legControl['transform'], constrainToRootCtrl=True, 
                                               weight=1, connectScaleWithRootCtrl=True)


        # Create and place the foot group transforms for parenting the IK handles and set their respective rotation orders.
        
        # heelRoll transform.
        heel_grp_preTransform = self.namePrefix + '_heelRoll_preTransform'
        heel_grp = self.namePrefix + '_heelRoll_transform'
        
        cmds.group(empty=True, name=heel_grp_preTransform)
        cmds.group(empty=True, name=heel_grp)
        
        # Align the heelRoll transform.
        cmds.xform(heel_grp_preTransform, worldSpace=True, 
                   translation=cmds.xform(heelJoint, query=True, worldSpace=True, translation=True),
                   rotation=cmds.xform(heelJoint, query=True, worldSpace=True, rotation=True))
        
        # Place it.
        cmds.parent(heel_grp_preTransform, legControl['transform'], absolute=True)
        cmds.parent(heel_grp, heel_grp_preTransform, relative=True)
        cmds.makeIdentity(heel_grp, rotate=True, apply=True)
        
        # Set the rotation order for the heelRoll grp.
        heel_grp_axesInfoData = mfunc.returnAxesInfoForFootTransform(heel_grp, foot_vec_dict)
        if heel_grp_axesInfoData['cross'][1] > 0:
            heel_grp_cross_ax_rot_mult = 1
        else:
            heel_grp_cross_ax_rot_mult = -1
        mfunc.setRotationOrderForFootUtilTransform(heel_grp, heel_grp_axesInfoData)
        
        
        # toeRoll transform.
        toeRoll_grp = self.namePrefix + '_toeRoll_transform'
        cmds.group(empty=True, name=toeRoll_grp)
        
        # Align the toeRoll transform.
        cmds.xform(toeRoll_grp, worldSpace=True, 
                   translation=cmds.xform(toeJoint, query=True, worldSpace=True, translation=True), 
                   rotation=cmds.xform(toeJoint, query=True, worldSpace=True, rotation=True))
        
        # Place it.
        cmds.parent(toeRoll_grp, heel_grp, absolute=True)
        cmds.makeIdentity(toeRoll_grp, rotate=True, apply=True)
        
        # Set the rotation order for the toeRoll grp.
        toeRoll_grp_axesInfoData = mfunc.returnAxesInfoForFootTransform(toeRoll_grp, foot_vec_dict)
        if toeRoll_grp_axesInfoData['cross'][1] > 0:
            toeRoll_grp_cross_ax_rot_mult = 1
        else:
            toeRoll_grp_cross_ax_rot_mult = -1
        mfunc.setRotationOrderForFootUtilTransform(toeRoll_grp, toeRoll_grp_axesInfoData)
        
        
        # ballRoll transform.
        ballRoll_grp = self.namePrefix + '_ballRoll_transform'
        cmds.group(empty=True, name=ballRoll_grp)
        
        # Align the ballRoll transform.
        cmds.xform(ballRoll_grp, worldSpace=True, translation=\
                   cmds.xform(ballJoint, query=True, worldSpace=True, translation=True), rotation=\
                   cmds.xform(ballJoint, query=True, worldSpace=True, rotation=True))
        
        # Place it.
        cmds.parent(ballRoll_grp, toeRoll_grp, absolute=True)
        cmds.makeIdentity(ballRoll_grp, rotate=True, apply=True)
        
        # Set the rotation order for the ballRoll grp.
        ballRoll_grp_axesInfoData = mfunc.returnAxesInfoForFootTransform(toeRoll_grp, foot_vec_dict)
        if ballRoll_grp_axesInfoData['cross'][1] > 0:
            ballRoll_grp_cross_ax_rot_mult = 1
        else:
            ballRoll_grp_cross_ax_rot_mult = -1
        mfunc.setRotationOrderForFootUtilTransform(ballRoll_grp, ballRoll_grp_axesInfoData)
        
        
        # toeCurl transform.
        toeCurl_grp = self.namePrefix + '_toeCurl_transform'
        cmds.group(empty=True, name=toeCurl_grp)
        
        # Align the toeCurl transform.
        cmds.xform(toeCurl_grp, worldSpace=True, 
                   translation=cmds.xform(ballJoint, query=True, worldSpace=True, translation=True), 
                   rotation=cmds.xform(ballJoint, query=True, worldSpace=True, rotation=True))
        
        # Place it.
        cmds.parent(toeCurl_grp, toeRoll_grp, absolute=True)
        cmds.makeIdentity(toeCurl_grp, rotate=True, apply=True)
        
        # Set the rotation order for the toeCurl grp.
        toeCurl_grp_axesInfoData = mfunc.returnAxesInfoForFootTransform(toeRoll_grp, foot_vec_dict)
        if toeCurl_grp_axesInfoData['cross'][1] > 0:
            toeCurl_grp_cross_ax_rot_mult = 1
        else:
            toeCurl_grp_cross_ax_rot_mult = -1
        mfunc.setRotationOrderForFootUtilTransform(toeCurl_grp, toeCurl_grp_axesInfoData)


        # Now parent the IKs to the foot gropus
        cmds.parent(legIkNodes[0], ballRoll_grp, absolute=True)
        cmds.parent(ballIkNodes[0], toeRoll_grp, absolute=True)
        cmds.parent(toeIkNodes[0], toeCurl_grp, absolute=True)

        # Calculate the knee manual pole vector position.
        
        # Get the "first-pass" position of the manual pole vector position.
        hip_ankle_mid_pos = eval(cmds.getAttr(self.rootJoint+'.ikSegmentMidPos'))
        knee_pos = cmds.xform(kneeJoint, query=True, worldSpace=True, translation=True)
        ik_pv_offset_pos = mfunc.returnOffsetPositionBetweenTwoVectors(hip_ankle_mid_pos, knee_pos, 2.0)    # << manual pole vector position
        
        # Get the hip and knee position, and hence the hip->knee vector.
        hip_pos = cmds.xform(hipJoint, query=True, worldSpace=True, translation=True)
        ankle_pos = cmds.xform(ankleJoint, query=True, worldSpace=True, translation=True)        
        hip_knee_vec = map(lambda x,y: x-y, hip_pos, knee_pos)
        hip_knee_vec_mag = math.sqrt(reduce(lambda x,y: x+y, [component**2 for component in hip_knee_vec]))
        ##hip_ankle_vec = map(lambda x,y: x-y, hip_pos, ankle_pos)  << NOT NEEDED
        ##hip_ankle_vec_mag = math.sqrt(reduce(lambda x,y: x+y, [component**2 for component in hip_ankle_vec]))  << NOT NEEDED
        
        # Now compare the first position of the knee manual pole vector position with the hip->knee vector,
        # by comparing their lengths.        
        i = 1
        while True:

            # Get the pv pos-> knee vector.
            ik_pv_pos_knee_vec = map(lambda x,y: x-y, ik_pv_offset_pos, knee_pos)
            ik_pv_pos_knee_mag = math.sqrt(reduce(lambda x,y: x+y, [component**2 for component in ik_pv_pos_knee_vec]))
            
            # Keep increasing the length of the pv pos->knee vector until it is more than the hip->knee vector length.
            if ik_pv_pos_knee_mag > hip_knee_vec_mag:
                break
            else:
                ik_pv_offset_pos = mfunc.returnOffsetPositionBetweenTwoVectors(hip_ankle_mid_pos, knee_pos, 2.0*i)
            i += 1
        
        
        # Calculate the position for the no-flip pole vector.        
        
        # Create a temp transform to get the world space position for vector placed on the +plane axis for the 
        # leg joint chain (from the knee joint), and then compare it with the leg cross vector calculated before,
        # and use the result to get the ik twist value needed to set the no-flip pole vector mode.
        temp_ik_vec = cmds.group(empty=True)
        cmds.parent(temp_ik_vec, kneeJoint, relative=True)
        nodeAxes = cmds.getAttr(self.rootJoint+'.nodeAxes')
        planeAxis = nodeAxes[2]
        offset = mfunc.returnVectorMagnitude(hip_pos, ankle_pos) * 2
        cmds.setAttr(temp_ik_vec+'.translate'+planeAxis, offset)
        ik_noFlip_pv_offset_startPos = cmds.xform(temp_ik_vec, query=True, worldSpace=True, translation=True)
        cmds.delete(temp_ik_vec)
        noFlip_offset_check = mfunc.returnDotProductDirection(knee_pos, leg_cross_vec, knee_pos, ik_noFlip_pv_offset_startPos)
        direction = round(noFlip_offset_check[0], 3)
        if direction < 0:
            ik_twist = -90
        else:
            ik_twist = 90

        # Create main group for containing pre-transforms for no-flip and manual pole vector transforms.
        pv_main_grp = self.namePrefix + '_poleVector_grp'
        cmds.group(empty=True, name=pv_main_grp, parent=self.ctrlGrp)
        
        # Place it.
        cmds.xform(pv_main_grp, worldSpace=True, translation=\
                   cmds.xform(ankleJoint, query=True, worldSpace=True, translation=True))

        # Create the no-flip pole vector transform and offset its position from the foot accordingly.
        kneePVnoFlip_transform = self.namePrefix + '_kneePVnoFlip_transform'
        kneePVnoFlip_preTransform = self.namePrefix + '_kneePVnoFlip_preTransform'
        cmds.group(empty=True, name=kneePVnoFlip_preTransform, parent=ballRoll_grp)
        cmds.xform(kneePVnoFlip_preTransform, worldSpace=True, translation=\
                   cmds.xform(kneeJoint, query=True, worldSpace=True, translation=True))
        cmds.group(empty=True, name=kneePVnoFlip_transform)
        cmds.xform(kneePVnoFlip_transform, worldSpace=True, translation=ik_noFlip_pv_offset_startPos)
        cmds.parent(kneePVnoFlip_transform, kneePVnoFlip_preTransform, absolute=True)
        cmds.xform(kneePVnoFlip_preTransform, worldSpace=True, translation=\
                   cmds.xform(ankleJoint, query=True, worldSpace=True, translation=True))

        # Create the manual pole vector tansform with its pre-transform, add the custom (xhandleShape) to it and place it.
        manualPVHandleShapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.32
        knee_pv = objects.load_xhandleShape(self.namePrefix+'_kneePV_CNTL', colour=self.controlColour)
        cmds.setAttr(knee_pv['shape']+'.localScaleX', manualPVHandleShapeRadius)
        cmds.setAttr(knee_pv['shape']+'.localScaleY', manualPVHandleShapeRadius)
        cmds.setAttr(knee_pv['shape']+'.localScaleZ', manualPVHandleShapeRadius)
        cmds.setAttr(knee_pv['shape']+'.drawStyle', 3)
        cmds.xform(knee_pv['preTransform'], worldSpace=True, translation=ik_pv_offset_pos)
        cmds.parent(knee_pv['preTransform'], pv_main_grp, absolute=True)
        mfunc.lockHideChannelAttrs(knee_pv['transform'], 'r', 's', keyable=False, lock=True)
        mfunc.lockHideChannelAttrs(knee_pv['transform'], 'v', visible=False)

        # Create a parent switch grp for the manual knee pole vector transform.
        self.createParentSwitchGrpForTransform(knee_pv['transform'], constrainToRootCtrl=True, 
                                               weight=1, connectScaleWithRootCtrl=True)        

        # Calculate the offset position for the foot bank control transform.
        ball_pos = cmds.xform(ballJoint, query=True, worldSpace=True, translation=True)
        heel_pos = cmds.xform(heelJoint, query=True, worldSpace=True, translation=True)
        ball_heel_vec = map(lambda x,y: x-y, ball_pos, heel_pos)
        ball_heel_vec_mag = math.sqrt(reduce(lambda x,y: x+y, [component**2 for component in ball_heel_vec])) * 0.3

        # Create and place the foot bank transform controls.
        bankPivot_1_ctrl = objects.load_xhandleShape(self.namePrefix+'_footBank_1_CNTL', 
                                                          colour=self.controlColour, transformOnly=True)
        cmds.setAttr(bankPivot_1_ctrl['shape']+'.localScaleX', manualPVHandleShapeRadius * 0.7)
        cmds.setAttr(bankPivot_1_ctrl['shape']+'.localScaleY', manualPVHandleShapeRadius * 0.7)
        cmds.setAttr(bankPivot_1_ctrl['shape']+'.localScaleZ', manualPVHandleShapeRadius * 0.7)
        cmds.setAttr(bankPivot_1_ctrl['shape']+'.drawStyle', 3)
        mfunc.lockHideChannelAttrs(bankPivot_1_ctrl['transform'], 'r', 's', keyable=False, lock=True)
        mfunc.lockHideChannelAttrs(bankPivot_1_ctrl['transform'], 'v', visible=False)
        cmds.parent(bankPivot_1_ctrl['transform'], toeRoll_grp, relative=True)
        cmds.setAttr(bankPivot_1_ctrl['transform']+'.translate'+toeRoll_grp_axesInfoData['cross'][0], ball_heel_vec_mag)

        for axis in ['X', 'Y', 'Z']:
            val = cmds.getAttr(bankPivot_1_ctrl['transform']+'.translate'+axis)
            if not val:
                cmds.setAttr(bankPivot_1_ctrl['transform']+'.translate'+axis, keyable=False, channelBox=False, lock=True)

        bankPivot_2_ctrl = objects.load_xhandleShape(self.namePrefix+'_footBank_2_CNTL', 
                                                          colour=self.controlColour, transformOnly=True)
        cmds.setAttr(bankPivot_2_ctrl['shape']+'.localScaleX', manualPVHandleShapeRadius * 0.7)
        cmds.setAttr(bankPivot_2_ctrl['shape']+'.localScaleY', manualPVHandleShapeRadius * 0.7)
        cmds.setAttr(bankPivot_2_ctrl['shape']+'.localScaleZ', manualPVHandleShapeRadius * 0.7)
        cmds.setAttr(bankPivot_2_ctrl['shape']+'.drawStyle', 3)
        mfunc.lockHideChannelAttrs(bankPivot_2_ctrl['transform'], 's', 'r', keyable=False, lock=True)
        mfunc.lockHideChannelAttrs(bankPivot_2_ctrl['transform'], 'v', visible=False)
        cmds.parent(bankPivot_2_ctrl['transform'], toeRoll_grp, relative=True)
        cmds.setAttr(bankPivot_2_ctrl['transform']+'.translate'+toeRoll_grp_axesInfoData['cross'][0], ball_heel_vec_mag*-1)

        for axis in ['X', 'Y', 'Z']:
            val = cmds.getAttr(bankPivot_2_ctrl['transform']+'.translate'+axis)
            if not val:
                cmds.setAttr(bankPivot_2_ctrl['transform']+'.translate'+axis, keyable=False, channelBox=False, lock=True)

        # Create the SDKs for knee pole vector control attributes on the leg IK control to drive the pole vector mode.
        pvConstraint = cmds.poleVectorConstraint(kneePVnoFlip_transform, knee_pv['transform'], legIkNodes[0], \
                                                 name=legIkNodes[0]+'_poleVectorConstraint')[0]
        for driver, driven in [[0, ik_twist], [1, 0]]:
            cmds.setAttr(legControl['transform']+'.Pole_Vector_Mode', driver)
            cmds.setAttr(legIkNodes[0]+'.twist', driven)
            cmds.setDrivenKeyframe(legIkNodes[0]+'.twist', currentDriver=legControl['transform']+'.Pole_Vector_Mode')

        for driver, driven_1, driven_2 in [[0, 1, 0], [1, 0, 1]]:
            cmds.setAttr(legControl['transform']+'.Pole_Vector_Mode', driver)
            cmds.setAttr(pvConstraint+'.'+kneePVnoFlip_transform+'W0', driven_1)
            cmds.setAttr(pvConstraint+'.'+knee_pv['transform']+'W1', driven_2)
            cmds.setAttr(knee_pv['preTransform']+'.visibility', driven_2)
            cmds.setDrivenKeyframe(pvConstraint+'.'+kneePVnoFlip_transform+'W0', \
                                   currentDriver=legControl['transform']+'.Pole_Vector_Mode')
            cmds.setDrivenKeyframe(pvConstraint+'.'+knee_pv['transform']+'W1', \
                                   currentDriver=legControl['transform']+'.Pole_Vector_Mode')
            cmds.setDrivenKeyframe(knee_pv['preTransform']+'.visibility', \
                                   currentDriver=legControl['transform']+'.Pole_Vector_Mode')
        cmds.setAttr(legControl['transform']+'.Pole_Vector_Mode', 0)
        kneePVnoFlip_preTransform_axisInfo = mfunc.returnAxesInfoForFootTransform(kneePVnoFlip_preTransform, foot_vec_dict)
        cmds.connectAttr(legControl['transform']+'.Knee_Twist', \
                         kneePVnoFlip_preTransform+'.rotate'+kneePVnoFlip_preTransform_axisInfo['up'][0])

        # Now connect the custom attributes on the leg IK control, with utility nodes, as needed.
        # Also, set the rotation multipliers for the parent transforms for the foot IKs to ensure correct/preferred rotation.
        
        # BALL ROLL connections.
        ballRoll_setRange = cmds.createNode('setRange', name=self.namePrefix + '_ballRoll_setRange', skipSelect=True)
        
        ballRoll_firstCondition = cmds.createNode('condition', name=self.namePrefix + '_ballRoll_firstCondition', skipSelect=True)
        cmds.setAttr(ballRoll_firstCondition+'.operation', 4)
        
        ballRoll_secondCondition = cmds.createNode('condition', name=self.namePrefix + '_ballRoll_secondCondition', skipSelect=True)
        cmds.setAttr(ballRoll_secondCondition+'.operation', 2)
        cmds.setAttr(ballRoll_secondCondition+'.colorIfFalseR', 0)
        
        cmds.connectAttr(legControl['transform']+'.Foot_Toe_Straight', ballRoll_setRange+'.oldMaxX')
        cmds.connectAttr(legControl['transform']+'.Foot_Toe_Lift', ballRoll_setRange+'.oldMinX')
        cmds.connectAttr(legControl['transform']+'.Foot_Toe_Lift', ballRoll_setRange+'.minX')
        cmds.connectAttr(legControl['transform']+'.Foot_Roll', ballRoll_setRange+'.valueX')
        cmds.connectAttr(ballRoll_setRange+'.outValueX', ballRoll_firstCondition+'.colorIfFalseR')
        cmds.connectAttr(legControl['transform']+'.Foot_Toe_Lift', ballRoll_firstCondition+'.secondTerm')
        cmds.connectAttr(legControl['transform']+'.Foot_Roll', ballRoll_firstCondition+'.colorIfTrueR')
        cmds.connectAttr(legControl['transform']+'.Foot_Roll', ballRoll_firstCondition+'.firstTerm')
        cmds.connectAttr(ballRoll_firstCondition+'.outColorR', ballRoll_secondCondition+'.firstTerm')
        cmds.connectAttr(ballRoll_firstCondition+'.outColorR', ballRoll_secondCondition+'.colorIfTrueR')
        

        ballRollCrossAxMultiply = cmds.createNode('multDoubleLinear', name=self.namePrefix + '_ballRoll_cross_ax_multiply', 
                                                  skipSelect=True)
        cmds.connectAttr(ballRoll_secondCondition+'.outColorR', ballRollCrossAxMultiply+'.input1')
        cmds.setAttr(ballRollCrossAxMultiply+'.input2', ballRoll_grp_cross_ax_rot_mult)
        cmds.connectAttr(ballRollCrossAxMultiply+'.output', ballRoll_grp+'.rotate'+ballRoll_grp_axesInfoData['cross'][0])

        cmds.connectAttr(legControl['transform']+'.Ball_Pivot', ballRoll_grp+'.rotate'+ballRoll_grp_axesInfoData['up'][0])
        self.collectedNodes.extend([ballRoll_setRange, ballRoll_firstCondition, ballRoll_secondCondition, ballRollCrossAxMultiply])
        
        # FOOT BANK PIVOT connections.
        bankPivot_1_condition = cmds.createNode('condition', name=self.namePrefix + '_bankPivot_1_condition', skipSelect=True)
        cmds.setAttr(bankPivot_1_condition+'.colorIfFalseR', 0)
        bankPivot_1_ctrl_axesInfo = mfunc.returnAxesInfoForFootTransform(bankPivot_1_ctrl['transform'], foot_vec_dict)
        val = cmds.getAttr(bankPivot_1_ctrl['transform']+'.translate'+bankPivot_1_ctrl_axesInfo['cross'][0])
        if val > 0:
            cmds.setAttr(bankPivot_1_condition+'.operation', 4)
        else:
            cmds.setAttr(bankPivot_1_condition+'.operation', 2)
            
        bankPivot_2_condition = cmds.createNode('condition', name=self.namePrefix + '_bankPivot_2_condition', skipSelect=True)
        cmds.setAttr(bankPivot_2_condition+'.colorIfFalseR', 0)
        bankPivot_2_ctrl_axesInfo = mfunc.returnAxesInfoForFootTransform(bankPivot_2_ctrl['transform'], foot_vec_dict)
        val = cmds.getAttr(bankPivot_2_ctrl['transform']+'.translate'+bankPivot_2_ctrl_axesInfo['cross'][0])
        if val > 0:
            cmds.setAttr(bankPivot_2_condition+'.operation', 4)
        else:
            cmds.setAttr(bankPivot_2_condition+'.operation', 2)
            
        bankPivotRest_condition = cmds.createNode('condition', name=self.namePrefix + '_bankPivotRest_condition', skipSelect=True)
        cmds.setAttr(bankPivotRest_condition+'.colorIfFalseR', 0)
        cmds.setAttr(bankPivotRest_condition+'.colorIfTrueR', 0)
        cmds.setAttr(bankPivotRest_condition+'.operation', 0)
        cmds.connectAttr(legControl['transform']+'.Foot_Bank', bankPivotRest_condition+'.firstTerm')
        cmds.connectAttr(legControl['transform']+'.Foot_Bank', bankPivot_1_condition+'.firstTerm')
        cmds.connectAttr(legControl['transform']+'.Foot_Bank', bankPivot_2_condition+'.firstTerm')
        cmds.connectAttr(bankPivot_1_ctrl['transform']+'.translate'+bankPivot_1_ctrl_axesInfo['cross'][0], \
                         bankPivot_1_condition+'.colorIfTrueR')
        cmds.connectAttr(bankPivot_2_ctrl['transform']+'.translate'+bankPivot_2_ctrl_axesInfo['cross'][0], \
                         bankPivot_2_condition+'.colorIfTrueR')
        
        # TOE ROLL connections.
        toeRoll_rotCrossAxisPivotPlus = cmds.createNode('plusMinusAverage', name=self.namePrefix + '_toeRoll_rotatePivot%sPlus' \
                                                        % bankPivot_2_ctrl_axesInfo['cross'][0], skipSelect=True)
        cmds.connectAttr(bankPivot_1_condition+'.outColorR', toeRoll_rotCrossAxisPivotPlus+'.input1D[0]')
        cmds.connectAttr(bankPivot_2_condition+'.outColorR', toeRoll_rotCrossAxisPivotPlus+'.input1D[1]')
        cmds.connectAttr(bankPivotRest_condition+'.outColorR', toeRoll_rotCrossAxisPivotPlus+'.input1D[2]')
        cmds.connectAttr(toeRoll_rotCrossAxisPivotPlus+'.output1D', \
                         toeRoll_grp+'.rotatePivot'+toeRoll_grp_axesInfoData['cross'][0])

        toeRollAimAxMultiply = cmds.createNode('multDoubleLinear', \
                                               name=self.namePrefix + '_toeRoll_aim_ax_multiply', skipSelect=True)
        cmds.connectAttr(legControl['transform']+'.Foot_Bank', toeRollAimAxMultiply+'.input1')
        cmds.setAttr(toeRollAimAxMultiply+'.input2', 1)
        cmds.connectAttr(toeRollAimAxMultiply+'.output', toeRoll_grp+'.rotate'+toeRoll_grp_axesInfoData['aim'][0])

        self.collectedNodes.extend([bankPivot_1_condition, bankPivot_2_condition, bankPivotRest_condition,
                               toeRoll_rotCrossAxisPivotPlus, toeRollAimAxMultiply])

        toeRoll_setRange = cmds.createNode('setRange', name=self.namePrefix + '_toeRoll_setRange', skipSelect=True)
        
        toeRoll_firstCondition = cmds.createNode('condition', name=self.namePrefix + '_toeRoll_firstCondition', \
                                                 skipSelect=True)
        cmds.setAttr(toeRoll_firstCondition+'.operation', 2)
        cmds.setAttr(toeRoll_firstCondition+'.colorIfFalseR', 0)
        toeRoll_secondCondition = cmds.createNode('condition', name=self.namePrefix + '_toeRoll_secondCondition', \
                                                  skipSelect=True)
        cmds.setAttr(toeRoll_secondCondition+'.operation', 4)
        
        toeRoll_thirdCondition = cmds.createNode('condition', name=self.namePrefix + '_toeRoll_thirdCondition', \
                                                 skipSelect=True)
        cmds.setAttr(toeRoll_thirdCondition+'.operation', 5)
        cmds.connectAttr(legControl['transform']+'.Foot_Roll', toeRoll_firstCondition+'.colorIfTrueR')
        cmds.connectAttr(legControl['transform']+'.Foot_Roll', toeRoll_firstCondition+'.firstTerm')
        cmds.connectAttr(toeRoll_firstCondition+'.outColorR', toeRoll_secondCondition+'.colorIfTrueR')
        cmds.connectAttr(legControl['transform']+'.Foot_Roll', toeRoll_secondCondition+'.firstTerm')
        cmds.connectAttr(legControl['transform']+'.Foot_Toe_Lift', toeRoll_secondCondition+'.secondTerm')
        cmds.connectAttr(legControl['transform']+'.Foot_Roll', toeRoll_secondCondition+'.colorIfFalseR')
        cmds.connectAttr(toeRoll_secondCondition+'.outColorR', toeRoll_setRange+'.valueX')
        cmds.connectAttr(legControl['transform']+'.Foot_Toe_Lift', toeRoll_setRange+'.oldMinX')
        cmds.connectAttr(legControl['transform']+'.Foot_Toe_Straight', toeRoll_setRange+'.oldMaxX')
        cmds.connectAttr(legControl['transform']+'.Foot_Toe_Straight', toeRoll_setRange+'.maxX')
        cmds.connectAttr(toeRoll_setRange+'.outValueX', toeRoll_thirdCondition+'.colorIfTrueR')
        cmds.connectAttr(legControl['transform']+'.Foot_Roll', toeRoll_thirdCondition+'.firstTerm')
        cmds.connectAttr(legControl['transform']+'.Foot_Toe_Straight', toeRoll_thirdCondition+'.secondTerm')
        cmds.connectAttr(legControl['transform']+'.Foot_Roll', toeRoll_thirdCondition+'.colorIfFalseR')

        toeRollCrossAxMultiply = cmds.createNode('multDoubleLinear', \
                                                 name=self.namePrefix + '_toeRoll_cross_ax_multiply', skipSelect=True)
        cmds.connectAttr(toeRoll_thirdCondition+'.outColorR', toeRollCrossAxMultiply+'.input1')
        cmds.setAttr(toeRollCrossAxMultiply+'.input2', toeRoll_grp_cross_ax_rot_mult)
        cmds.connectAttr(toeRollCrossAxMultiply+'.output', toeRoll_grp+'.rotate'+toeRoll_grp_axesInfoData['cross'][0])
        cmds.connectAttr(legControl['transform']+'.Toe_Pivot', toeRoll_grp+'.rotate'+toeRoll_grp_axesInfoData['up'][0])
        
        # TOE CURL connections.
        toeCurlCrossAxMultiply = cmds.createNode('multDoubleLinear', \
                                                 name=self.namePrefix + '_toeCurl_cross_ax_multiply', skipSelect=True)
        cmds.connectAttr(legControl['transform']+'.Toe_Curl', toeCurlCrossAxMultiply+'.input1')
        cmds.setAttr(toeCurlCrossAxMultiply+'.input2', toeCurl_grp_cross_ax_rot_mult)
        cmds.connectAttr(toeCurlCrossAxMultiply+'.output', toeCurl_grp+'.rotate'+toeCurl_grp_axesInfoData['cross'][0])
        cmds.connectAttr(legControl['transform']+'.Ball_Pivot', toeCurl_grp+'.rotate'+toeCurl_grp_axesInfoData['up'][0])
        self.collectedNodes.extend([toeRoll_setRange, toeRoll_firstCondition, toeRoll_secondCondition,
                               toeRoll_thirdCondition, toeRollCrossAxMultiply, toeCurlCrossAxMultiply])
        
        # HEEL ROLL connections.
        heelRoll_condition = cmds.createNode('condition', name=self.namePrefix + '_heelRoll_condition', skipSelect=True)
        cmds.setAttr(heelRoll_condition+'.operation', 3)
        cmds.setAttr(heelRoll_condition+'.colorIfFalseR', 0)
        cmds.connectAttr(legControl['transform']+'.Foot_Roll', heelRoll_condition+'.colorIfTrueR')
        cmds.connectAttr(legControl['transform']+'.Foot_Roll', heelRoll_condition+'.secondTerm')
        
        heelRollCrossAxMultiply = cmds.createNode('multDoubleLinear', \
                                                  name=self.namePrefix + '_heelRoll_cross_ax_multiply', skipSelect=True)
        cmds.connectAttr(heelRoll_condition+'.outColorR', heelRollCrossAxMultiply+'.input1')
        cmds.setAttr(heelRollCrossAxMultiply+'.input2', heel_grp_cross_ax_rot_mult)
        cmds.connectAttr(heelRollCrossAxMultiply+'.output', heel_grp+'.rotate'+heel_grp_axesInfoData['cross'][0])
        cmds.connectAttr(legControl['transform']+'.Heel_Pivot', heel_grp+'.rotate'+heel_grp_axesInfoData['up'][0])
        self.collectedNodes.extend([heelRoll_condition, heelRollCrossAxMultiply])

        # Check and correct the aim and hence the axial rotation of the toeRoll group along the length of the foot.
        bankPivot_1_restPos = cmds.getAttr(bankPivot_1_ctrl['transform']+'Shape.worldPosition')[0]
        rest_mag_bankPivot_hip = mfunc.returnVectorMagnitude(hip_pos, bankPivot_1_restPos)
        toeRoll_grp_aim_ax_rot_mult = 1
        for value in (15, -15):
            cmds.setAttr(legControl['transform']+'.Foot_Bank', value)
            bankPivot_1_pos = cmds.getAttr(bankPivot_1_ctrl['transform']+'Shape.worldPosition')[0]
            mag_bankPivot_hip = mfunc.returnVectorMagnitude(hip_pos, bankPivot_1_pos)
            if round(mag_bankPivot_hip, 4) > round(rest_mag_bankPivot_hip, 4):
                cmds.setAttr(toeRollAimAxMultiply+'.input2', -1)
        cmds.setAttr(legControl['transform']+'.Foot_Bank', 0)
        
        # Add the nodes to the control rig container, and then publish the necessary keyable attributes.
        mfunc.addNodesToContainer(self.ctrl_container, self.collectedNodes, includeHierarchyBelow=True)

        mfunc.updateContainerNodes(self.ctrl_container)
        
        legControlAttrs = cmds.listAttr(legControl['transform'], keyable=True, visible=True, unlocked=True)
        legControlName = self.getCtrlNiceNameForPublish(legControl['transform'])
        for attr in legControlAttrs:
            if not re.search('Foot_Toe_Straight|Foot_Toe_Lift|targetParents', attr):
                cmds.container(self.ctrl_container, edit=True, publishAndBind=[legControl['transform']+'.'+attr, \
                                                                          legControlName+'_'+attr])
        for axis in ['X', 'Y', 'Z']:
            cmds.container(self.ctrl_container, edit=True, publishAndBind=[knee_pv['transform']+'.translate'+axis, \
                                                                           'kneePV_cntl_translate'+axis])
        cmds.setAttr(legControl['transform']+'.overrideEnabled', 1)
        cmds.connectAttr(self.controlRigDisplayLayer + '.visibility', legControl['transform']+'.overrideVisibility')
        cmds.setAttr(knee_pv['transform']+'.overrideEnabled', 1)
        cmds.connectAttr(self.controlRigDisplayLayer + '.visibility', knee_pv['transform']+'.overrideVisibility')
        
        # Create a custom keyable attribute on the character root transform by the control name to adjust the weight
        # of the driver joint layer by using the method "createCtrlRigWeightAttributeOnRootTransform".
        self.createCtrlRigWeightAttributeOnRootTransform(self.namePrefix,
                                                         [legControl['transform'], bankPivot_1_ctrl['transform'],
                                                          bankPivot_2_ctrl['transform'], knee_pv['transform']])
        cmds.select(clear=True)


    def applyReverse_IK_Leg_Stretchy(self):

        '''Creates controls for a stretchy reverse IK leg with a main foot transform and a pole vector transform in
        auto non-flip / manual mode.'''

        # Control group, to be placed under "controls".
        self.createCtrlGrp()
        
        # Add it to the node list to be added to the control rig container.
        self.collectedNodes.append(self.ctrlGrp)
        
        # Get the names of knee, ankle and its children from the original hierarchy.
        origKneeJoint = cmds.listRelatives(self.rootJoint, children=True, type='joint')[0]
        origAnkleJoint = cmds.listRelatives(origKneeJoint, children=True, type='joint')[0]
        origAnkleChildren = cmds.listRelatives(origAnkleJoint, children=True, type='joint')

        # Find the toe and heel joints.
        for child in origAnkleChildren:
            chldJnt = cmds.listRelatives(child, allDescendents=True, type='joint')
            if chldJnt:
                origToeJoint = chldJnt[-1]
                origBallJoint = child
            else:
                origHeelJoint = child

        # Get the positions of ankle, knee and hip to find the IK plane and obtain the perpendicular vector for the leg plane.
        transform1_start_vec = transform2_start_vec = cmds.xform(origKneeJoint, query=True, worldSpace=True, translation=True)
        transform1_end_vec = cmds.xform(origAnkleJoint, query=True, worldSpace=True, translation=True)
        transform2_end_vec = hip_pos = cmds.xform(self.rootJoint, query=True, worldSpace=True, translation=True)
        result = mfunc.returnCrossProductDirection(transform1_start_vec, transform1_end_vec, transform2_start_vec, transform2_end_vec)
        leg_cross_pos = [round(item, 4) for item in result[1]]          # << relative position of vector perpendicular to the leg plane.
        leg_cross_vec = map(lambda x,y:x+y, leg_cross_pos, transform1_start_vec)       # << absolute position of vector perpendicular to the leg plane.

        # Get the positions of heel, toe and the ball joints to find the IK plane and hence the perpendicular vector for
        # the foot plane.
        transform1_start_vec = transform2_start_vec = cmds.xform(origHeelJoint, query=True, worldSpace=True, translation=True)
        transform1_end_vec = cmds.xform(origAnkleJoint, query=True, worldSpace=True, translation=True)
        transform2_end_vec = cmds.xform(origToeJoint, query=True, worldSpace=True, translation=True)
        result = mfunc.returnCrossProductDirection(transform1_start_vec, transform1_end_vec, transform2_start_vec, transform2_end_vec)
        foot_cross_pos = [round(item, 4) for item in result[1]]
        foot_cross_vec = map(lambda x,y:x+y, foot_cross_pos, transform1_start_vec)
        foot_aim_vec = mfunc.returnOffsetPositionBetweenTwoVectors(transform2_start_vec, transform2_end_vec, 1.5)
        foot_vec_dict = {'heel_pos':transform1_start_vec, 'cross':foot_cross_vec, 'aim':foot_aim_vec, 'hip_pos':hip_pos}

        # Create the FK layer for the control rig.
        jointSet, driver_constraints, layerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                                 self.ctrlRigName,
                                                                                                 self.characterName,
                                                                                                 False,
                                                                                                 'None',
                                                                                                 True)
        # Add the joints in the driver layer to be added to the control rig container.
        self.collectedNodes.extend(jointSet)
        
        # Update the instance attribute for the driver joint layer set.
        self.driverJointLayerSet = jointSet

        # Update the instance attribute to contain the driver constraints for the joint hiearachy.
        self.driverConstraintsForInput = driver_constraints

        # Get the names of the hip, knee, ankle, ball, toe and heel joint for the driver layer joint hierarchy.
        hipJoint = layerRootJoint
        kneeJoint = cmds.listRelatives(hipJoint, children=True, type='joint')[0]
        ankleJoint = cmds.listRelatives(kneeJoint, children=True, type='joint')[0]
        ankleChildren = cmds.listRelatives(ankleJoint, children=True, type='joint')
        for child in ankleChildren:
            chldJnt = cmds.listRelatives(child, allDescendents=True, type='joint')
            if chldJnt:
                ballJoint = child
                toeJoint = chldJnt[-1]
            else:
                heelJoint = child

        # Create an IK RP solver from hip to ankle on the driver joint layer.
        
        # Disable check for cycle.
        cmds.cycleCheck(evaluation=False)        
            
        handleName = self.namePrefix + '_hipAnkleIkHandle'
        effName = self.namePrefix + '_hipAnkleIkEffector'
        
        legIkNodes = cmds.ikHandle(startJoint=hipJoint, endEffector=ankleJoint, name=handleName, solver='ikRPsolver')
        cmds.rename(legIkNodes[1], effName)
        cmds.setAttr(legIkNodes[0]+'.visibility', 0)
        cmds.delete(cmds.orientConstraint(ankleJoint, legIkNodes[0], maintainOffset=False))
        mfunc.updateNodeList(legIkNodes[0])

        # Create IK SC solvers from ankle to ball, and from ball to toe, on the driver joint layer.
        handleName = self.namePrefix + '_ankleBallIkHandle'
        effName = self.namePrefix + '_ankleBallIkEffector'
        
        ballIkNodes = cmds.ikHandle(startJoint=ankleJoint, endEffector=ballJoint, name=handleName, solver='ikSCsolver')
        cmds.rename(ballIkNodes[1], effName)
        cmds.setAttr(ballIkNodes[0]+'.visibility', 0)
        
        handleName = self.namePrefix + '_ballToeIkHandle'
        effName = self.namePrefix + '_ballToeIkEffector'
        
        toeIkNodes = cmds.ikHandle(startJoint=ballJoint, endEffector=toeJoint, name=handleName, solver='ikSCsolver')
        cmds.rename(toeIkNodes[1], effName)
        cmds.setAttr(toeIkNodes[0]+'.visibility', 0)
        
        # Enable check for cycle.
        cmds.cycleCheck(evaluation=True)

        # Create the IK control handle.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.88
        legControl = objects.load_xhandleShape(self.namePrefix+'_CNTL', colour=self.controlColour)
        cmds.setAttr(legControl['shape']+'.localScaleX', shapeRadius)
        cmds.setAttr(legControl['shape']+'.localScaleY', shapeRadius)
        cmds.setAttr(legControl['shape']+'.localScaleZ', shapeRadius)
        cmds.setAttr(legControl['shape']+'.drawStyle', 6)
        mfunc.lockHideChannelAttrs(legControl['transform'], 's', keyable=False, lock=True)
        mfunc.lockHideChannelAttrs(legControl['transform'], 'v', visible=False)
        cmds.addAttr(legControl['transform'], attributeType='enum', longName='Foot_Controls', enumName=' ', keyable=True)
        cmds.setAttr(legControl['transform']+'.Foot_Controls', lock=True)
        cmds.addAttr(legControl['transform'], attributeType='double', longName='Foot_Roll', defaultValue=0, keyable=True)
        cmds.addAttr(legControl['transform'], attributeType='double', longName='Foot_Toe_Lift', defaultValue=30, keyable=True)
        cmds.addAttr(legControl['transform'], attributeType='double', longName='Foot_Toe_Straight', defaultValue=70, keyable=True)
        cmds.addAttr(legControl['transform'], attributeType='double', longName='Knee_Twist', defaultValue=0, keyable=True)
        cmds.addAttr(legControl['transform'], attributeType='double', longName='Foot_Bank', defaultValue=0, keyable=True)
        cmds.addAttr(legControl['transform'], attributeType='double', longName='Ball_Pivot', defaultValue=0, keyable=True)
        cmds.addAttr(legControl['transform'], attributeType='double', longName='Toe_Pivot', defaultValue=0, keyable=True)
        cmds.addAttr(legControl['transform'], attributeType='double', longName='Toe_Curl', defaultValue=0, keyable=True)
        cmds.addAttr(legControl['transform'], attributeType='double', longName='Heel_Pivot', defaultValue=0, keyable=True)
        cmds.addAttr(legControl['transform'], attributeType='enum', longName='Pole_Vector_Mode', minValue=0, maxValue=1, \
                     enumName=':No Flip:Manual', defaultValue=0, keyable=True)
        
        # Align the IK control handle based on the 'translation function' value, inherited from the module state.
        if cmds.attributeQuery('translationFunction', node=legControl['transform'], exists=True) and \
           cmds.getAttr(legControl['transform']+'.translationFunction') == 'local_orientation':
            cmds.xform(legControl['preTransform'], worldSpace=True, translation=\
                       cmds.xform(ankleJoint, query=True, worldSpace=True, translation=True), rotation=\
                       cmds.xform(ankleJoint, query=True, worldSpace=True, rotation=True))

            legControlAxesInfo = mfunc.returnAxesInfoForFootTransform(legControl['transform'], foot_vec_dict)
        else:
            cmds.xform(legControl['preTransform'], worldSpace=True, translation=cmds.xform(ankleJoint, query=True, \
                                                                                              worldSpace=True, translation=True))
            cmds.setAttr(legControl['transform']+'.rotateOrder', 2)
        cmds.parent(legControl['preTransform'], self.ctrlGrp, absolute=True)

        # Create a parent switch grp for the IK control handle.
        self.createParentSwitchGrpForTransform(legControl['transform'], constrainToRootCtrl=True, 
                                               weight=1, connectScaleWithRootCtrl=True)


        # Create and place the foot group transforms for parenting the IK handles and set their respective rotation orders.
        
        # heelRoll transform.
        heel_grp_preTransform = self.namePrefix + '_heelRoll_preTransform'
        heel_grp = self.namePrefix + '_heelRoll_transform'
        
        cmds.group(empty=True, name=heel_grp_preTransform)
        cmds.group(empty=True, name=heel_grp)
        
        # Align the heelRoll transform.
        cmds.xform(heel_grp_preTransform, worldSpace=True, 
                   translation=cmds.xform(heelJoint, query=True, worldSpace=True, translation=True),
                   rotation=cmds.xform(heelJoint, query=True, worldSpace=True, rotation=True))
        
        # Place it.
        cmds.parent(heel_grp_preTransform, legControl['transform'], absolute=True)
        cmds.parent(heel_grp, heel_grp_preTransform, relative=True)
        cmds.makeIdentity(heel_grp, rotate=True, apply=True)
        
        # Set the rotation order for the heelRoll grp.
        heel_grp_axesInfoData = mfunc.returnAxesInfoForFootTransform(heel_grp, foot_vec_dict)
        if heel_grp_axesInfoData['cross'][1] > 0:
            heel_grp_cross_ax_rot_mult = 1
        else:
            heel_grp_cross_ax_rot_mult = -1
        mfunc.setRotationOrderForFootUtilTransform(heel_grp, heel_grp_axesInfoData)
        
        
        # toeRoll transform.
        toeRoll_grp = self.namePrefix + '_toeRoll_transform'
        cmds.group(empty=True, name=toeRoll_grp)
        
        # Align the toeRoll transform.
        cmds.xform(toeRoll_grp, worldSpace=True, 
                   translation=cmds.xform(toeJoint, query=True, worldSpace=True, translation=True), 
                   rotation=cmds.xform(toeJoint, query=True, worldSpace=True, rotation=True))
        
        # Place it.
        cmds.parent(toeRoll_grp, heel_grp, absolute=True)
        cmds.makeIdentity(toeRoll_grp, rotate=True, apply=True)
        
        # Set the rotation order for the toeRoll grp.
        toeRoll_grp_axesInfoData = mfunc.returnAxesInfoForFootTransform(toeRoll_grp, foot_vec_dict)
        if toeRoll_grp_axesInfoData['cross'][1] > 0:
            toeRoll_grp_cross_ax_rot_mult = 1
        else:
            toeRoll_grp_cross_ax_rot_mult = -1
        mfunc.setRotationOrderForFootUtilTransform(toeRoll_grp, toeRoll_grp_axesInfoData)
        
        
        # ballRoll transform.
        ballRoll_grp = self.namePrefix + '_ballRoll_transform'
        cmds.group(empty=True, name=ballRoll_grp)
        
        # Align the ballRoll transform.
        cmds.xform(ballRoll_grp, worldSpace=True, translation=\
                   cmds.xform(ballJoint, query=True, worldSpace=True, translation=True), rotation=\
                   cmds.xform(ballJoint, query=True, worldSpace=True, rotation=True))
        
        # Place it.
        cmds.parent(ballRoll_grp, toeRoll_grp, absolute=True)
        cmds.makeIdentity(ballRoll_grp, rotate=True, apply=True)
        
        # Set the rotation order for the ballRoll grp.
        ballRoll_grp_axesInfoData = mfunc.returnAxesInfoForFootTransform(toeRoll_grp, foot_vec_dict)
        if ballRoll_grp_axesInfoData['cross'][1] > 0:
            ballRoll_grp_cross_ax_rot_mult = 1
        else:
            ballRoll_grp_cross_ax_rot_mult = -1
        mfunc.setRotationOrderForFootUtilTransform(ballRoll_grp, ballRoll_grp_axesInfoData)
        
        
        # toeCurl transform.
        toeCurl_grp = self.namePrefix + '_toeCurl_transform'
        cmds.group(empty=True, name=toeCurl_grp)
        
        # Align the toeCurl transform.
        cmds.xform(toeCurl_grp, worldSpace=True, 
                   translation=cmds.xform(ballJoint, query=True, worldSpace=True, translation=True), 
                   rotation=cmds.xform(ballJoint, query=True, worldSpace=True, rotation=True))
        
        # Place it.
        cmds.parent(toeCurl_grp, toeRoll_grp, absolute=True)
        cmds.makeIdentity(toeCurl_grp, rotate=True, apply=True)
        
        # Set the rotation order for the toeCurl grp.
        toeCurl_grp_axesInfoData = mfunc.returnAxesInfoForFootTransform(toeRoll_grp, foot_vec_dict)
        if toeCurl_grp_axesInfoData['cross'][1] > 0:
            toeCurl_grp_cross_ax_rot_mult = 1
        else:
            toeCurl_grp_cross_ax_rot_mult = -1
        mfunc.setRotationOrderForFootUtilTransform(toeCurl_grp, toeCurl_grp_axesInfoData)


        # Now parent the IKs to the foot gropus
        cmds.parent(legIkNodes[0], ballRoll_grp, absolute=True)
        cmds.parent(ballIkNodes[0], toeRoll_grp, absolute=True)
        cmds.parent(toeIkNodes[0], toeCurl_grp, absolute=True)

        # Calculate the knee manual pole vector position.
        
        # Get the "first-pass" position of the manual pole vector position.
        hip_ankle_mid_pos = eval(cmds.getAttr(self.rootJoint+'.ikSegmentMidPos'))
        knee_pos = cmds.xform(kneeJoint, query=True, worldSpace=True, translation=True)
        ik_pv_offset_pos = mfunc.returnOffsetPositionBetweenTwoVectors(hip_ankle_mid_pos, knee_pos, 2.0)    # << manual pole vector position
        
        # Get the hip and knee position, and hence the hip->knee vector.
        hip_pos = cmds.xform(hipJoint, query=True, worldSpace=True, translation=True)
        ankle_pos = cmds.xform(ankleJoint, query=True, worldSpace=True, translation=True)        
        hip_knee_vec = map(lambda x,y: x-y, hip_pos, knee_pos)
        hip_knee_vec_mag = math.sqrt(reduce(lambda x,y: x+y, [component**2 for component in hip_knee_vec]))
        ##hip_ankle_vec = map(lambda x,y: x-y, hip_pos, ankle_pos)  << NOT NEEDED
        ##hip_ankle_vec_mag = math.sqrt(reduce(lambda x,y: x+y, [component**2 for component in hip_ankle_vec]))  << NOT NEEDED
        
        # Now compare the first position of the knee manual pole vector position with the hip->knee vector,
        # by comparing their lengths.        
        i = 1
        while True:

            # Get the pv pos-> knee vector.
            ik_pv_pos_knee_vec = map(lambda x,y: x-y, ik_pv_offset_pos, knee_pos)
            ik_pv_pos_knee_mag = math.sqrt(reduce(lambda x,y: x+y, [component**2 for component in ik_pv_pos_knee_vec]))
            
            # Keep increasing the length of the pv pos->knee vector until it is more than the hip->knee vector length.
            if ik_pv_pos_knee_mag > hip_knee_vec_mag:
                break
            else:
                ik_pv_offset_pos = mfunc.returnOffsetPositionBetweenTwoVectors(hip_ankle_mid_pos, knee_pos, 2.0*i)
            i += 1
        
        
        # Calculate the position for the no-flip pole vector.        
        
        # Create a temp transform to get the world space position for vector placed on the +plane axis for the 
        # leg joint chain (from the knee joint), and then compare it with the leg cross vector calculated before,
        # and use the result to get the ik twist value needed to set the no-flip pole vector mode.
        temp_ik_vec = cmds.group(empty=True)
        cmds.parent(temp_ik_vec, kneeJoint, relative=True)
        nodeAxes = cmds.getAttr(self.rootJoint+'.nodeAxes')
        planeAxis = nodeAxes[2]
        offset = mfunc.returnVectorMagnitude(hip_pos, ankle_pos) * 2
        cmds.setAttr(temp_ik_vec+'.translate'+planeAxis, offset)
        ik_noFlip_pv_offset_startPos = cmds.xform(temp_ik_vec, query=True, worldSpace=True, translation=True)
        cmds.delete(temp_ik_vec)
        noFlip_offset_check = mfunc.returnDotProductDirection(knee_pos, leg_cross_vec, knee_pos, ik_noFlip_pv_offset_startPos)
        direction = round(noFlip_offset_check[0], 3)
        if direction < 0:
            ik_twist = -90
        else:
            ik_twist = 90

        # Create main group for containing pre-transforms for no-flip and manual pole vector transforms.
        pv_main_grp = self.namePrefix + '_poleVector_grp'
        cmds.group(empty=True, name=pv_main_grp, parent=self.ctrlGrp)
        
        # Place it.
        cmds.xform(pv_main_grp, worldSpace=True, translation=\
                   cmds.xform(ankleJoint, query=True, worldSpace=True, translation=True))

        # Create the no-flip pole vector transform and offset its position from the foot accordingly.
        kneePVnoFlip_transform = self.namePrefix + '_kneePVnoFlip_transform'
        kneePVnoFlip_preTransform = self.namePrefix + '_kneePVnoFlip_preTransform'
        cmds.group(empty=True, name=kneePVnoFlip_preTransform, parent=ballRoll_grp)
        cmds.xform(kneePVnoFlip_preTransform, worldSpace=True, translation=\
                   cmds.xform(kneeJoint, query=True, worldSpace=True, translation=True))
        cmds.group(empty=True, name=kneePVnoFlip_transform)
        cmds.xform(kneePVnoFlip_transform, worldSpace=True, translation=ik_noFlip_pv_offset_startPos)
        cmds.parent(kneePVnoFlip_transform, kneePVnoFlip_preTransform, absolute=True)
        cmds.xform(kneePVnoFlip_preTransform, worldSpace=True, translation=\
                   cmds.xform(ankleJoint, query=True, worldSpace=True, translation=True))

        # Create the manual pole vector tansform with its pre-transform, add the custom (xhandleShape) to it and place it.
        manualPVHandleShapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.32
        knee_pv = objects.load_xhandleShape(self.namePrefix+'_kneePV_CNTL', colour=self.controlColour)
        cmds.setAttr(knee_pv['shape']+'.localScaleX', manualPVHandleShapeRadius)
        cmds.setAttr(knee_pv['shape']+'.localScaleY', manualPVHandleShapeRadius)
        cmds.setAttr(knee_pv['shape']+'.localScaleZ', manualPVHandleShapeRadius)
        cmds.setAttr(knee_pv['shape']+'.drawStyle', 3)
        cmds.xform(knee_pv['preTransform'], worldSpace=True, translation=ik_pv_offset_pos)
        cmds.parent(knee_pv['preTransform'], pv_main_grp, absolute=True)
        mfunc.lockHideChannelAttrs(knee_pv['transform'], 'r', 's', keyable=False, lock=True)
        mfunc.lockHideChannelAttrs(knee_pv['transform'], 'v', visible=False)

        # Create a parent switch grp for the manual knee pole vector transform.
        self.createParentSwitchGrpForTransform(knee_pv['transform'], constrainToRootCtrl=True, 
                                               weight=1, connectScaleWithRootCtrl=True)        

        # Calculate the offset position for the foot bank control transform.
        ball_pos = cmds.xform(ballJoint, query=True, worldSpace=True, translation=True)
        heel_pos = cmds.xform(heelJoint, query=True, worldSpace=True, translation=True)
        ball_heel_vec = map(lambda x,y: x-y, ball_pos, heel_pos)
        ball_heel_vec_mag = math.sqrt(reduce(lambda x,y: x+y, [component**2 for component in ball_heel_vec])) * 0.3

        # Create and place the foot bank transform controls.
        bankPivot_1_ctrl = objects.load_xhandleShape(self.namePrefix+'_footBank_1_CNTL', 
                                                          colour=self.controlColour, transformOnly=True)
        cmds.setAttr(bankPivot_1_ctrl['shape']+'.localScaleX', manualPVHandleShapeRadius * 0.7)
        cmds.setAttr(bankPivot_1_ctrl['shape']+'.localScaleY', manualPVHandleShapeRadius * 0.7)
        cmds.setAttr(bankPivot_1_ctrl['shape']+'.localScaleZ', manualPVHandleShapeRadius * 0.7)
        cmds.setAttr(bankPivot_1_ctrl['shape']+'.drawStyle', 3)
        mfunc.lockHideChannelAttrs(bankPivot_1_ctrl['transform'], 'r', 's', keyable=False, lock=True)
        mfunc.lockHideChannelAttrs(bankPivot_1_ctrl['transform'], 'v', visible=False)
        cmds.parent(bankPivot_1_ctrl['transform'], toeRoll_grp, relative=True)
        cmds.setAttr(bankPivot_1_ctrl['transform']+'.translate'+toeRoll_grp_axesInfoData['cross'][0], ball_heel_vec_mag)

        for axis in ['X', 'Y', 'Z']:
            val = cmds.getAttr(bankPivot_1_ctrl['transform']+'.translate'+axis)
            if not val:
                cmds.setAttr(bankPivot_1_ctrl['transform']+'.translate'+axis, keyable=False, channelBox=False, lock=True)

        bankPivot_2_ctrl = objects.load_xhandleShape(self.namePrefix+'_footBank_2_CNTL', 
                                                          colour=self.controlColour, transformOnly=True)
        cmds.setAttr(bankPivot_2_ctrl['shape']+'.localScaleX', manualPVHandleShapeRadius * 0.7)
        cmds.setAttr(bankPivot_2_ctrl['shape']+'.localScaleY', manualPVHandleShapeRadius * 0.7)
        cmds.setAttr(bankPivot_2_ctrl['shape']+'.localScaleZ', manualPVHandleShapeRadius * 0.7)
        cmds.setAttr(bankPivot_2_ctrl['shape']+'.drawStyle', 3)
        mfunc.lockHideChannelAttrs(bankPivot_2_ctrl['transform'], 's', 'r', keyable=False, lock=True)
        mfunc.lockHideChannelAttrs(bankPivot_2_ctrl['transform'], 'v', visible=False)
        cmds.parent(bankPivot_2_ctrl['transform'], toeRoll_grp, relative=True)
        cmds.setAttr(bankPivot_2_ctrl['transform']+'.translate'+toeRoll_grp_axesInfoData['cross'][0], ball_heel_vec_mag*-1)

        for axis in ['X', 'Y', 'Z']:
            val = cmds.getAttr(bankPivot_2_ctrl['transform']+'.translate'+axis)
            if not val:
                cmds.setAttr(bankPivot_2_ctrl['transform']+'.translate'+axis, keyable=False, channelBox=False, lock=True)

        # Create the SDKs for knee pole vector control attributes on the leg IK control to drive the pole vector mode.
        pvConstraint = cmds.poleVectorConstraint(kneePVnoFlip_transform, knee_pv['transform'], legIkNodes[0],
                                                 name=legIkNodes[0]+'_poleVectorConstraint')[0]
        for driver, driven in [[0, ik_twist], [1, 0]]:
            cmds.setAttr(legControl['transform']+'.Pole_Vector_Mode', driver)
            cmds.setAttr(legIkNodes[0]+'.twist', driven)
            cmds.setDrivenKeyframe(legIkNodes[0]+'.twist', currentDriver=legControl['transform']+'.Pole_Vector_Mode')

        for driver, driven_1, driven_2 in [[0, 1, 0], [1, 0, 1]]:
            cmds.setAttr(legControl['transform']+'.Pole_Vector_Mode', driver)
            cmds.setAttr(pvConstraint+'.'+kneePVnoFlip_transform+'W0', driven_1)
            cmds.setAttr(pvConstraint+'.'+knee_pv['transform']+'W1', driven_2)
            cmds.setAttr(knee_pv['preTransform']+'.visibility', driven_2)
            cmds.setDrivenKeyframe(pvConstraint+'.'+kneePVnoFlip_transform+'W0', \
                                   currentDriver=legControl['transform']+'.Pole_Vector_Mode')
            cmds.setDrivenKeyframe(pvConstraint+'.'+knee_pv['transform']+'W1', \
                                   currentDriver=legControl['transform']+'.Pole_Vector_Mode')
            cmds.setDrivenKeyframe(knee_pv['preTransform']+'.visibility', \
                                   currentDriver=legControl['transform']+'.Pole_Vector_Mode')
        cmds.setAttr(legControl['transform']+'.Pole_Vector_Mode', 0)
        kneePVnoFlip_preTransform_axisInfo = mfunc.returnAxesInfoForFootTransform(kneePVnoFlip_preTransform, foot_vec_dict)
        cmds.connectAttr(legControl['transform']+'.Knee_Twist', \
                         kneePVnoFlip_preTransform+'.rotate'+kneePVnoFlip_preTransform_axisInfo['up'][0])

        # Now connect the custom attributes on the leg IK control, with utility nodes, as needed.
        # Also, set the rotation multipliers for the parent transforms for the foot IKs to ensure correct/preferred rotation.
        
        # BALL ROLL connections.
        ballRoll_setRange = cmds.createNode('setRange', name=self.namePrefix + '_ballRoll_setRange', skipSelect=True)
        
        ballRoll_firstCondition = cmds.createNode('condition', name=self.namePrefix + '_ballRoll_firstCondition', skipSelect=True)
        cmds.setAttr(ballRoll_firstCondition+'.operation', 4)
        
        ballRoll_secondCondition = cmds.createNode('condition', name=self.namePrefix + '_ballRoll_secondCondition', skipSelect=True)
        cmds.setAttr(ballRoll_secondCondition+'.operation', 2)
        cmds.setAttr(ballRoll_secondCondition+'.colorIfFalseR', 0)
        
        cmds.connectAttr(legControl['transform']+'.Foot_Toe_Straight', ballRoll_setRange+'.oldMaxX')
        cmds.connectAttr(legControl['transform']+'.Foot_Toe_Lift', ballRoll_setRange+'.oldMinX')
        cmds.connectAttr(legControl['transform']+'.Foot_Toe_Lift', ballRoll_setRange+'.minX')
        cmds.connectAttr(legControl['transform']+'.Foot_Roll', ballRoll_setRange+'.valueX')
        cmds.connectAttr(ballRoll_setRange+'.outValueX', ballRoll_firstCondition+'.colorIfFalseR')
        cmds.connectAttr(legControl['transform']+'.Foot_Toe_Lift', ballRoll_firstCondition+'.secondTerm')
        cmds.connectAttr(legControl['transform']+'.Foot_Roll', ballRoll_firstCondition+'.colorIfTrueR')
        cmds.connectAttr(legControl['transform']+'.Foot_Roll', ballRoll_firstCondition+'.firstTerm')
        cmds.connectAttr(ballRoll_firstCondition+'.outColorR', ballRoll_secondCondition+'.firstTerm')
        cmds.connectAttr(ballRoll_firstCondition+'.outColorR', ballRoll_secondCondition+'.colorIfTrueR')
        

        ballRollCrossAxMultiply = cmds.createNode('multDoubleLinear', name=self.namePrefix + '_ballRoll_cross_ax_multiply', 
                                                  skipSelect=True)
        cmds.connectAttr(ballRoll_secondCondition+'.outColorR', ballRollCrossAxMultiply+'.input1')
        cmds.setAttr(ballRollCrossAxMultiply+'.input2', ballRoll_grp_cross_ax_rot_mult)
        cmds.connectAttr(ballRollCrossAxMultiply+'.output', ballRoll_grp+'.rotate'+ballRoll_grp_axesInfoData['cross'][0])

        cmds.connectAttr(legControl['transform']+'.Ball_Pivot', ballRoll_grp+'.rotate'+ballRoll_grp_axesInfoData['up'][0])
        self.collectedNodes.extend([ballRoll_setRange, ballRoll_firstCondition, ballRoll_secondCondition, ballRollCrossAxMultiply])
        
        # FOOT BANK PIVOT connections.
        bankPivot_1_condition = cmds.createNode('condition', name=self.namePrefix + '_bankPivot_1_condition', skipSelect=True)
        cmds.setAttr(bankPivot_1_condition+'.colorIfFalseR', 0)
        bankPivot_1_ctrl_axesInfo = mfunc.returnAxesInfoForFootTransform(bankPivot_1_ctrl['transform'], foot_vec_dict)
        val = cmds.getAttr(bankPivot_1_ctrl['transform']+'.translate'+bankPivot_1_ctrl_axesInfo['cross'][0])
        if val > 0:
            cmds.setAttr(bankPivot_1_condition+'.operation', 4)
        else:
            cmds.setAttr(bankPivot_1_condition+'.operation', 2)
            
        bankPivot_2_condition = cmds.createNode('condition', name=self.namePrefix + '_bankPivot_2_condition', skipSelect=True)
        cmds.setAttr(bankPivot_2_condition+'.colorIfFalseR', 0)
        bankPivot_2_ctrl_axesInfo = mfunc.returnAxesInfoForFootTransform(bankPivot_2_ctrl['transform'], foot_vec_dict)
        val = cmds.getAttr(bankPivot_2_ctrl['transform']+'.translate'+bankPivot_2_ctrl_axesInfo['cross'][0])
        if val > 0:
            cmds.setAttr(bankPivot_2_condition+'.operation', 4)
        else:
            cmds.setAttr(bankPivot_2_condition+'.operation', 2)
            
        bankPivotRest_condition = cmds.createNode('condition', name=self.namePrefix + '_bankPivotRest_condition', skipSelect=True)
        cmds.setAttr(bankPivotRest_condition+'.colorIfFalseR', 0)
        cmds.setAttr(bankPivotRest_condition+'.colorIfTrueR', 0)
        cmds.setAttr(bankPivotRest_condition+'.operation', 0)
        cmds.connectAttr(legControl['transform']+'.Foot_Bank', bankPivotRest_condition+'.firstTerm')
        cmds.connectAttr(legControl['transform']+'.Foot_Bank', bankPivot_1_condition+'.firstTerm')
        cmds.connectAttr(legControl['transform']+'.Foot_Bank', bankPivot_2_condition+'.firstTerm')
        cmds.connectAttr(bankPivot_1_ctrl['transform']+'.translate'+bankPivot_1_ctrl_axesInfo['cross'][0], \
                         bankPivot_1_condition+'.colorIfTrueR')
        cmds.connectAttr(bankPivot_2_ctrl['transform']+'.translate'+bankPivot_2_ctrl_axesInfo['cross'][0], \
                         bankPivot_2_condition+'.colorIfTrueR')
        
        # TOE ROLL connections.
        toeRoll_rotCrossAxisPivotPlus = cmds.createNode('plusMinusAverage', name=self.namePrefix + '_toeRoll_rotatePivot%sPlus' \
                                                        % bankPivot_2_ctrl_axesInfo['cross'][0], skipSelect=True)
        cmds.connectAttr(bankPivot_1_condition+'.outColorR', toeRoll_rotCrossAxisPivotPlus+'.input1D[0]')
        cmds.connectAttr(bankPivot_2_condition+'.outColorR', toeRoll_rotCrossAxisPivotPlus+'.input1D[1]')
        cmds.connectAttr(bankPivotRest_condition+'.outColorR', toeRoll_rotCrossAxisPivotPlus+'.input1D[2]')
        cmds.connectAttr(toeRoll_rotCrossAxisPivotPlus+'.output1D', \
                         toeRoll_grp+'.rotatePivot'+toeRoll_grp_axesInfoData['cross'][0])

        toeRollAimAxMultiply = cmds.createNode('multDoubleLinear', \
                                               name=self.namePrefix + '_toeRoll_aim_ax_multiply', skipSelect=True)
        cmds.connectAttr(legControl['transform']+'.Foot_Bank', toeRollAimAxMultiply+'.input1')
        cmds.setAttr(toeRollAimAxMultiply+'.input2', 1)
        cmds.connectAttr(toeRollAimAxMultiply+'.output', toeRoll_grp+'.rotate'+toeRoll_grp_axesInfoData['aim'][0])

        self.collectedNodes.extend([bankPivot_1_condition, bankPivot_2_condition, bankPivotRest_condition,
                               toeRoll_rotCrossAxisPivotPlus, toeRollAimAxMultiply])

        toeRoll_setRange = cmds.createNode('setRange', name=self.namePrefix + '_toeRoll_setRange', skipSelect=True)
        
        toeRoll_firstCondition = cmds.createNode('condition', name=self.namePrefix + '_toeRoll_firstCondition', \
                                                 skipSelect=True)
        cmds.setAttr(toeRoll_firstCondition+'.operation', 2)
        cmds.setAttr(toeRoll_firstCondition+'.colorIfFalseR', 0)
        toeRoll_secondCondition = cmds.createNode('condition', name=self.namePrefix + '_toeRoll_secondCondition', \
                                                  skipSelect=True)
        cmds.setAttr(toeRoll_secondCondition+'.operation', 4)
        
        toeRoll_thirdCondition = cmds.createNode('condition', name=self.namePrefix + '_toeRoll_thirdCondition', \
                                                 skipSelect=True)
        cmds.setAttr(toeRoll_thirdCondition+'.operation', 5)
        cmds.connectAttr(legControl['transform']+'.Foot_Roll', toeRoll_firstCondition+'.colorIfTrueR')
        cmds.connectAttr(legControl['transform']+'.Foot_Roll', toeRoll_firstCondition+'.firstTerm')
        cmds.connectAttr(toeRoll_firstCondition+'.outColorR', toeRoll_secondCondition+'.colorIfTrueR')
        cmds.connectAttr(legControl['transform']+'.Foot_Roll', toeRoll_secondCondition+'.firstTerm')
        cmds.connectAttr(legControl['transform']+'.Foot_Toe_Lift', toeRoll_secondCondition+'.secondTerm')
        cmds.connectAttr(legControl['transform']+'.Foot_Roll', toeRoll_secondCondition+'.colorIfFalseR')
        cmds.connectAttr(toeRoll_secondCondition+'.outColorR', toeRoll_setRange+'.valueX')
        cmds.connectAttr(legControl['transform']+'.Foot_Toe_Lift', toeRoll_setRange+'.oldMinX')
        cmds.connectAttr(legControl['transform']+'.Foot_Toe_Straight', toeRoll_setRange+'.oldMaxX')
        cmds.connectAttr(legControl['transform']+'.Foot_Toe_Straight', toeRoll_setRange+'.maxX')
        cmds.connectAttr(toeRoll_setRange+'.outValueX', toeRoll_thirdCondition+'.colorIfTrueR')
        cmds.connectAttr(legControl['transform']+'.Foot_Roll', toeRoll_thirdCondition+'.firstTerm')
        cmds.connectAttr(legControl['transform']+'.Foot_Toe_Straight', toeRoll_thirdCondition+'.secondTerm')
        cmds.connectAttr(legControl['transform']+'.Foot_Roll', toeRoll_thirdCondition+'.colorIfFalseR')

        toeRollCrossAxMultiply = cmds.createNode('multDoubleLinear', \
                                                 name=self.namePrefix + '_toeRoll_cross_ax_multiply', skipSelect=True)
        cmds.connectAttr(toeRoll_thirdCondition+'.outColorR', toeRollCrossAxMultiply+'.input1')
        cmds.setAttr(toeRollCrossAxMultiply+'.input2', toeRoll_grp_cross_ax_rot_mult)
        cmds.connectAttr(toeRollCrossAxMultiply+'.output', toeRoll_grp+'.rotate'+toeRoll_grp_axesInfoData['cross'][0])
        cmds.connectAttr(legControl['transform']+'.Toe_Pivot', toeRoll_grp+'.rotate'+toeRoll_grp_axesInfoData['up'][0])
        
        # TOE CURL connections.
        toeCurlCrossAxMultiply = cmds.createNode('multDoubleLinear', \
                                                 name=self.namePrefix + '_toeCurl_cross_ax_multiply', skipSelect=True)
        cmds.connectAttr(legControl['transform']+'.Toe_Curl', toeCurlCrossAxMultiply+'.input1')
        cmds.setAttr(toeCurlCrossAxMultiply+'.input2', toeCurl_grp_cross_ax_rot_mult)
        cmds.connectAttr(toeCurlCrossAxMultiply+'.output', toeCurl_grp+'.rotate'+toeCurl_grp_axesInfoData['cross'][0])
        cmds.connectAttr(legControl['transform']+'.Ball_Pivot', toeCurl_grp+'.rotate'+toeCurl_grp_axesInfoData['up'][0])
        self.collectedNodes.extend([toeRoll_setRange, toeRoll_firstCondition, toeRoll_secondCondition,
                               toeRoll_thirdCondition, toeRollCrossAxMultiply, toeCurlCrossAxMultiply])
        
        # HEEL ROLL connections.
        heelRoll_condition = cmds.createNode('condition', name=self.namePrefix + '_heelRoll_condition', skipSelect=True)
        cmds.setAttr(heelRoll_condition+'.operation', 3)
        cmds.setAttr(heelRoll_condition+'.colorIfFalseR', 0)
        cmds.connectAttr(legControl['transform']+'.Foot_Roll', heelRoll_condition+'.colorIfTrueR')
        cmds.connectAttr(legControl['transform']+'.Foot_Roll', heelRoll_condition+'.secondTerm')
        
        heelRollCrossAxMultiply = cmds.createNode('multDoubleLinear', \
                                                  name=self.namePrefix + '_heelRoll_cross_ax_multiply', skipSelect=True)
        cmds.connectAttr(heelRoll_condition+'.outColorR', heelRollCrossAxMultiply+'.input1')
        cmds.setAttr(heelRollCrossAxMultiply+'.input2', heel_grp_cross_ax_rot_mult)
        cmds.connectAttr(heelRollCrossAxMultiply+'.output', heel_grp+'.rotate'+heel_grp_axesInfoData['cross'][0])
        cmds.connectAttr(legControl['transform']+'.Heel_Pivot', heel_grp+'.rotate'+heel_grp_axesInfoData['up'][0])
        self.collectedNodes.extend([heelRoll_condition, heelRollCrossAxMultiply])

        # Apply the stretch functionality.
        
        # Get the real-time world position of the hip joint.        
        hipPosLocator = cmds.spaceLocator(name=self.namePrefix+'_hipPos_loc')[0]
        mfunc.pointConstraint(hipJoint, hipPosLocator, maintainOffset=False)
        cmds.parent(hipPosLocator, self.ctrlGrp, absolute=True)       
        cmds.setAttr(hipPosLocator+'.visibility', 0)

        # Get the real-time length of the leg, from hip to ankle.
        distanceBtwn = cmds.createNode('distanceBetween', name=self.namePrefix+'_hipToAnkle_distance', skipSelect=True)
        cmds.connectAttr(hipPosLocator+'Shape.worldPosition[0]', distanceBtwn+'.point1')
        cmds.connectAttr(legControl['transform']+'Shape.worldPosition[0]', distanceBtwn+'.point2')
        
        # Divide the real-time length of the leg by globalScale to normalize it.
        legLengthNormalize = cmds.createNode('multiplyDivide', name=self.namePrefix+'_hipToAnkle_distance_normalize', skipSelect=True)
        cmds.connectAttr(self.globalScaleAttr, legLengthNormalize+'.input2X')
        cmds.connectAttr(distanceBtwn+'.distance', legLengthNormalize+'.input1X')
        cmds.setAttr(legLengthNormalize+'.operation', 2)
        
        # Get the default rest length of the leg.
        jointAxis =  cmds.getAttr(kneeJoint+'.nodeAxes')[0]
        upperLegLengthTranslate = cmds.getAttr(kneeJoint+'.translate'+jointAxis)
        lowerLegLengthTranslate = cmds.getAttr(ankleJoint+'.translate'+jointAxis)
        legLength = upperLegLengthTranslate + lowerLegLengthTranslate
        
        # Divide the real-time length of the leg, hip to ankle by the default rest length, to get the stretch factor.
        stretchLengthDivide = cmds.createNode('multiplyDivide', name=self.namePrefix+'_hipToAnkle_stretchLengthDivide', skipSelect=True)
        cmds.setAttr(stretchLengthDivide+'.input2X', abs(legLength), lock=True)
        cmds.setAttr(stretchLengthDivide+'.operation', 2)
        cmds.connectAttr(legLengthNormalize+'.outputX', stretchLengthDivide+'.input1X')
        
        # Use a condition node to check if the current length of the leg is more than the 
        # default rest length of the leg, to allow the stretch factor.
        stretchCondition = cmds.createNode('condition', name=self.namePrefix+'_hipToAnkle_stretchCondition', skipSelect=True)
        cmds.setAttr(stretchCondition+'.operation', 2)
        cmds.setAttr(stretchCondition+'.colorIfFalseR', 1)
        cmds.connectAttr(stretchLengthDivide+'.outputX', stretchCondition+'.colorIfTrueR')
        cmds.connectAttr(stretchLengthDivide+'.input2X', stretchCondition+'.secondTerm')
        cmds.connectAttr(stretchLengthDivide+'.input1X', stretchCondition+'.firstTerm')
        
        # Multiply the current length of knee to ankle by the stretch factor.
        lowerLegTranslateMultiply = cmds.createNode('multDoubleLinear', \
                                                    name=self.namePrefix+'_kneeToAnkle_lowerLegTranslateMultiply', skipSelect=True)
        cmds.connectAttr(stretchCondition+'.outColorR', lowerLegTranslateMultiply+'.input1')
        cmds.setAttr(lowerLegTranslateMultiply+'.input2', lowerLegLengthTranslate)
        cmds.connectAttr(lowerLegTranslateMultiply+'.output', ankleJoint+'.translate'+jointAxis)
        
        # Multiply the current length of hip to knee by the stretch factor.
        upperLegTranslateMultiply = cmds.createNode('multDoubleLinear', \
                                                    name=self.namePrefix+'_hipToKnee_upperLegTranslateMultiply', skipSelect=True)
        cmds.connectAttr(stretchCondition+'.outColorR', upperLegTranslateMultiply+'.input1')
        cmds.setAttr(upperLegTranslateMultiply+'.input2', upperLegLengthTranslate)
        cmds.connectAttr(upperLegTranslateMultiply+'.output', kneeJoint+'.translate'+jointAxis)
        
        # Collect the utility nodes to be added to the control rig container.
        self.collectedNodes.extend([distanceBtwn, legLengthNormalize, stretchLengthDivide, stretchCondition,
                               lowerLegTranslateMultiply, upperLegTranslateMultiply])

        # Check and correct the aim and hence the axial rotation of the toeRoll group along the length of the foot.
        bankPivot_1_restPos = cmds.getAttr(bankPivot_1_ctrl['transform']+'Shape.worldPosition')[0]
        rest_mag_bankPivot_hip = mfunc.returnVectorMagnitude(hip_pos, bankPivot_1_restPos)
        toeRoll_grp_aim_ax_rot_mult = 1
        for value in (15, -15):
            cmds.setAttr(legControl['transform']+'.Foot_Bank', value)
            bankPivot_1_pos = cmds.getAttr(bankPivot_1_ctrl['transform']+'Shape.worldPosition')[0]
            mag_bankPivot_hip = mfunc.returnVectorMagnitude(hip_pos, bankPivot_1_pos)
            if round(mag_bankPivot_hip, 4) > round(rest_mag_bankPivot_hip, 4):
                cmds.setAttr(toeRollAimAxMultiply+'.input2', -1)
        cmds.setAttr(legControl['transform']+'.Foot_Bank', 0)
        
        # Add the nodes to the control rig container, and then publish the necessary keyable attributes.
        mfunc.addNodesToContainer(self.ctrl_container, self.collectedNodes, includeHierarchyBelow=True)

        mfunc.updateContainerNodes(self.ctrl_container)
        
        legControlAttrs = cmds.listAttr(legControl['transform'], keyable=True, visible=True, unlocked=True)
        legControlName = self.getCtrlNiceNameForPublish(legControl['transform'])
        for attr in legControlAttrs:
            if not re.search('Foot_Toe_Straight|Foot_Toe_Lift|targetParents', attr):
                cmds.container(self.ctrl_container, edit=True, publishAndBind=[legControl['transform']+'.'+attr, \
                                                                          legControlName+'_'+attr])
        for axis in ['X', 'Y', 'Z']:
            cmds.container(self.ctrl_container, edit=True, publishAndBind=[knee_pv['transform']+'.translate'+axis, \
                                                                      'kneePV_cntl_translate'+axis])
        cmds.setAttr(legControl['transform']+'.overrideEnabled', 1)
        cmds.connectAttr(self.controlRigDisplayLayer + '.visibility', legControl['transform']+'.overrideVisibility')
        cmds.setAttr(knee_pv['transform']+'.overrideEnabled', 1)
        cmds.connectAttr(self.controlRigDisplayLayer + '.visibility', knee_pv['transform']+'.overrideVisibility')
        
        # Create a custom keyable attribute on the character root transform by the control name to adjust the weight
        # of the driver joint layer by using the method "createCtrlRigWeightAttributeOnRootTransform".
        self.createCtrlRigWeightAttributeOnRootTransform(self.namePrefix,
                                                         [legControl['transform'], bankPivot_1_ctrl['transform'],
                                                          bankPivot_2_ctrl['transform'], knee_pv['transform']])
        cmds.select(clear=True)


class JointChainControl(BaseJointControl):

    """This hierarchy type is constructed from a joint module consisting of more than two nodes in a linear chain."""


    def __init__(self,  *args, **kwargs):
        BaseJointControl.__init__(self,  *args, **kwargs)


    def applyDynamic_FK(self):

        '''This method creates an FK control joint layer over a selected joint hierarchy and drives it indirectly using a
        second joint layer affected by a dynamic spline IK curve skinned to the first joint layer.'''

        # The dynamic FK control will consist of two sets of joint layers, one which will be used to control a dynamic curve
        # (input curve), which is skinned to it, whose output curve will drive another joint layer, using spline IK, and this
        # joint layer will drive the actual (selected) joint hierarchy.

        # This joint layer will be used as control, and so, we'll set the connectLayer to False
        # (notice the second last argument).
        ctrlJointSet, null, ctrlLayerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                           self.ctrlRigName,
                                                                                           self.characterName,
                                                                                           True,
                                                                                           'On',
                                                                                           True,
                                                                                           self.controlColour,
                                                                                           False)
        # The 'null' is used above since no driver constraints are returned, it's an empty list,
        # since this is not the driver joint layer.
        
        # Collect the control layer joints to be added to the control rig container.
        self.collectedNodes.extend(ctrlJointSet)

        # Get the radius of the shape to be applied to the FK control joints.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.35

        # Create a parent switch group for the root FK control.
        self.createParentSwitchGrpForTransform(ctrlLayerRootJoint, constrainToRootCtrl=True)
        
        # Lock the translation and scale attributes of the control joints, and apply shapes to it.
        for joint in ctrlJointSet:
            cmds.setAttr(joint+'.drawStyle', 2)
            mfunc.lockHideChannelAttrs(joint, 't', 's', 'radi', keyable=False, lock=True)
            mfunc.lockHideChannelAttrs(joint, 'v', visible=False)
            xhandle = objects.load_xhandleShape(joint, colour=self.controlColour, transformOnly=True)
            cmds.setAttr(xhandle['shape']+'.localScaleX', shapeRadius)
            cmds.setAttr(xhandle['shape']+'.localScaleY', shapeRadius)
            cmds.setAttr(xhandle['shape']+'.localScaleZ', shapeRadius)
            cmds.setAttr(xhandle['shape']+'.drawStyle', 5)

        # Now create the driver joint layer.
        defJointSet, driver_constraints, defLayerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                                       self.ctrlRigName,
                                                                                                       self.characterName,
                                                                                                       False,
                                                                                                       'None',
                                                                                                       True,
                                                                                                       None,
                                                                                                       True)
        # Collect the driver layer joints to be added to the control rig container.
        self.collectedNodes.extend(defJointSet)

        # Update the instance attribute for the driver joint layer set.
        self.driverJointLayerSet = defJointSet

        # Update the instance attribute to contain the driver constraints for the joint hiearachy.
        self.driverConstraintsForInput = driver_constraints

        # Create the driver curve.
        curveCVposString = '['
        jointIt = defLayerRootJoint
        while jointIt:
            pos = cmds.xform(jointIt, query=True, worldSpace=True, translation=True)
            curveCVposString += str(tuple(pos))+','
            jointIt = cmds.listRelatives(jointIt, children=True, type='joint')
        curveCVposString = curveCVposString[:-1] + ']'
        curveCVposList = eval(curveCVposString)
        driverCurve = cmds.curve(degree=1, point=curveCVposList)
        driverCurve = cmds.rename(driverCurve, self.namePrefix+'_driverCurve')

        # Skin the driver curve to the FK control joints. To collect all the nodes created during skinning, perform
        # skinning while in a temp namespace, and then collect all nodes within the namespace.
        cmds.namespace(setNamespace=':')
        tempNamespaceName = self.namePrefix+'_tempNamespace'
        cmds.namespace(addNamespace=tempNamespaceName)
        cmds.namespace(setNamespace=tempNamespaceName)
        cmds.select(ctrlJointSet, replace=True)
        cmds.select(driverCurve, add=True)
        if _maya_version >=2013:
            skinCluster = cmds.skinCluster(bindMethod=0, toSelectedBones=True, normalizeWeights=2, obeyMaxInfluences=False, \
                                           maximumInfluences=5, dropoffRate=4.0, ignoreHierarchy=True)
        else:
            skinCluster = cmds.skinCluster(skinMethod=0, toSelectedBones=True, normalizeWeights=2, obeyMaxInfluences=False, \
                                           maximumInfluences=5, dropoffRate=4.0, ignoreHierarchy=True)
        cmds.select(clear=True)
        namespaceNodes = cmds.namespaceInfo(listOnlyDependencyNodes=True)
        skin_nodes = []
        for node in namespaceNodes:
            nodeName = node.partition(':')[2]
            if re.search('^%s' % self.userSpecName, nodeName):
                nameSeq = re.split('\d+', nodeName)
                name = cmds.rename(node, '%s_driverCurve_%s'%(self.namePrefix, ''.join(nameSeq)))
                skin_nodes.append(name.partition(':')[2])
        cmds.namespace(setNamespace=':')
        cmds.namespace(moveNamespace=[tempNamespaceName, ':'], force=True)
        cmds.namespace(removeNamespace=tempNamespaceName)
        self.collectedNodes.extend(skin_nodes)
        cmds.select(clear=True)

        # Create a control group node to place all DAG nodes (not part of the character joint hierarchy) under it.
        self.createCtrlGrp()

        # Collect it to be added to the control rig container.
        self.collectedNodes.append(self.ctrlGrp)

        # Turn the driver curve dynamic (whose output is to be used in spline IK), and set attributes accordingly.
        """
        UNFORTUNATELY THIS OPTION BELOW DOESN'T WORK WITH MAYA 2013(SP2). IF YOU'RE WITHIN A NAMESPACE (EXCEPT ROOT)
        AND IF YOU CREATE A DYNAMIC CURVE, ALL PARENT GROUP NODES, PART OF THE HAIR SYSTEM ARE PLACED IN SELF-GENERATED 
        CHILD NAMESPACES WITHIN THE CURRENT NAMESPACE, WHICH IS UNEXPECTED. THIS IS NOT AN ISSUE IN MAYA 2011, 2012. 
        FOR EXAMPLE, THE FOLLOWING NODES ARE GENERATED WHILE WORKING WITHIN A NAMESPACE "NEW":

        NEW:hairsystem1                       // OK
        NEW:nucleus1                          // OK
        >NEW:NEW:hairSystem1Follicles         // WTF?
        >NEW:NEW:hairSystem1OutputCurves      // WTF?

        # DEPRECATED #
        # Create a temporary namespace to place and rename new nodes for the dynamic curve.
        cmds.namespace(setNamespace=':')
        tempNamespaceName = 'MRT_character%s_%s_tempNamespace'%(self.characterName, self.userSpecName)
        cmds.namespace(addNamespace=tempNamespaceName)
        cmds.namespace(setNamespace=tempNamespaceName)
        """
        all_nodes_p = set(cmds.ls())
        cmds.select(driverCurve, replace=True)
        mel.eval('makeCurvesDynamicHairs 0 0 1')
        all_nodes_f = set(cmds.ls())
        hair_nodes = all_nodes_f.difference(all_nodes_p)  # Also: hair_nodes = set.symmetric_difference(all_nodes_p, all_nodes_f)

        for node in hair_nodes:
            if node.startswith('rebuildCurve'):
                cmds.rename(node, self.namePrefix+'_rebuildCurve')
            if re.match('^follicle\d+$', node):
                follicle = cmds.rename(node, self.namePrefix+'_follicle')
                cmds.parent(follicle, ':'+self.ctrlGrp, absolute=True)
                cmds.setAttr(follicle+'.visibility', 0)
            if re.match('^curve\d+$', node):
                dynCurve = cmds.rename(node, self.namePrefix+'_dynCurve')
                cmds.parent(dynCurve, self.ctrlGrp, absolute=True)
                cmds.setAttr(dynCurve+'.visibility', 0)
            if re.match('^hairSystem\d+$', node):
                hairSystem = cmds.rename(node, self.namePrefix+'_hairSystem')
                cmds.parent(hairSystem, self.ctrlGrp, absolute=True)
                cmds.setAttr(hairSystem+'.visibility', 0)
            if node.startswith('nucleus'):
                nucleus = cmds.rename(node, self.namePrefix+'_nucleus')
                cmds.parent(nucleus, self.ctrlGrp, absolute=True)
                cmds.setAttr(nucleus+'.visibility', 0)
            if re.match('^curve\d+rebuiltCurveShape\d+$', node):
                cmds.rename(node, self.namePrefix+'_driverCurveRebuiltShape')
            if re.match('^hairSystem\d+Follicles$', node):
                cmds.delete(node)
            if re.match('^hairSystem\d+OutputCurves$', node):
                cmds.delete(node)

        cmds.select(clear=True)
        cmds.setAttr(follicle+'Shape.pointLock', 1)
        cmds.setAttr(follicle+'Shape.restPose', 3)

        # Create the spline IK using the driver curve's dynamic output curve.
        defSplineIkHandleNodes = cmds.ikHandle(startJoint=defLayerRootJoint, endEffector=defJointSet[1], \
                                               solver='ikSplineSolver', createCurve=False, simplifyCurve=False, rootOnCurve=False, parentCurve=False, \
                                               curve=dynCurve)
        defSplineIkHandle = cmds.rename(defSplineIkHandleNodes[0], self.namePrefix+'_drivenSplineIkHandle')
        defSplineIkEffector = cmds.rename(defSplineIkHandleNodes[1], self.namePrefix+'_drivenSplineIkEffector')
        cmds.parent(defSplineIkHandle, self.ctrlGrp, absolute=True)
        cmds.setAttr(defSplineIkHandle+'.visibility', 0)

        # Create and place a handle/control for accessing dynamic attributes for the dynamic curve for the spline IK.
        # Add custom attributes to it and connect them.
        colour = self.controlColour - 1
        if self.controlColour < 1:
            colour = self.controlColour + 1
        dynSettingsCtrl = objects.load_xhandleShape(self.namePrefix+'_dynSettings_CNTL', colour=colour, transformOnly=True)
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.32
        cmds.setAttr(dynSettingsCtrl['shape']+'.localScaleX', shapeRadius)
        cmds.setAttr(dynSettingsCtrl['shape']+'.localScaleY', shapeRadius)
        cmds.setAttr(dynSettingsCtrl['shape']+'.localScaleZ', shapeRadius)
        cmds.connectAttr(self.globalScaleAttr, dynSettingsCtrl['transform']+'.scaleX')
        cmds.connectAttr(self.globalScaleAttr, dynSettingsCtrl['transform']+'.scaleY')
        cmds.connectAttr(self.globalScaleAttr, dynSettingsCtrl['transform']+'.scaleZ')
        cmds.setAttr(dynSettingsCtrl['shape']+'.drawStyle', 2)
        cmds.setAttr(dynSettingsCtrl['shape']+'.drawStyle', keyable=False, lock=True)
        cmds.xform(dynSettingsCtrl['transform'], worldSpace=True, translation=cmds.xform(defJointSet[1], query=True, worldSpace=True, translation=True), 
                   rotation=cmds.xform(defJointSet[1], query=True, worldSpace=True, rotation=True))
        upAxis = cmds.getAttr(defJointSet[1]+'.nodeAxes')[1]
        translation = {'X':[shapeRadius*10.0, 0, 0], 'Y':[0, shapeRadius*10.0, 0], 'Z':[0, 0, shapeRadius*10.0]}[upAxis]
        cmds.xform(dynSettingsCtrl['transform'], relative=True, translation=translation)
        cmds.parent(dynSettingsCtrl['transform'], self.ctrlGrp, absolute=True)
        mfunc.parentConstraint(defJointSet[1], dynSettingsCtrl['transform'], maintainOffset=True)

        cmds.setAttr(dynSettingsCtrl['transform']+'.overrideEnabled', 1)
        cmds.connectAttr(self.controlRigDisplayLayer + '.visibility', dynSettingsCtrl['transform']+'.overrideVisibility')
        mfunc.lockHideChannelAttrs(dynSettingsCtrl['transform'], 't', 'r', 's', keyable=False, lock=True)
        mfunc.lockHideChannelAttrs(dynSettingsCtrl['transform'], 'v', visible=False)
        cmds.select(clear=True)
        
        # Add custom dynamic attributes to the control.
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='enum', longName='DynamicsSwitch', keyable=True, enumName=':Off:On')
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='iterations', keyable=True, defaultValue=20)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='stiffness', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='stiffnessScale', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='startCurveAttract', keyable=True, defaultValue=1)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='startCurveAttractDamp', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='damping', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='gravity', keyable=True, defaultValue=0.98)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='enum', longName='Turbulence', keyable=True, enumName=' ')
        cmds.setAttr(dynSettingsCtrl['transform']+'.Turbulence', lock=True)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='intensity', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='frequency', keyable=True, defaultValue=0.2)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='speed', keyable=True, defaultValue=0.2)
        
        # Connect the dynamic attributes.
        for driver, driven in [[0, 0], [1, 2]]:
            cmds.setAttr(dynSettingsCtrl['transform']+'.DynamicsSwitch', driver)
            cmds.setAttr(follicle+'Shape.simulationMethod', driven)
            cmds.setDrivenKeyframe(follicle+'Shape.simulationMethod', currentDriver=dynSettingsCtrl['transform']+'.DynamicsSwitch')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.iterations', hairSystem+'Shape.iterations')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.stiffness', hairSystem+'Shape.stiffness')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.stiffnessScale', hairSystem+'Shape.stiffnessScale[0].stiffnessScale_FloatValue')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.startCurveAttract', hairSystem+'Shape.startCurveAttract')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.startCurveAttractDamp', hairSystem+'Shape.attractionDamp')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.damping', hairSystem+'Shape.damp')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.gravity', hairSystem+'Shape.gravity')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.intensity', hairSystem+'Shape.turbulenceStrength')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.frequency', hairSystem+'Shape.turbulenceFrequency')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.speed', hairSystem+'Shape.turbulenceSpeed')
        cmds.select(clear=True)

        # Add all the rest of the nodes to the control rig container.
        mfunc.addNodesToContainer(self.ctrl_container, self.collectedNodes, includeHierarchyBelow=True)
        
        # Publish the rotate attributes for the control joints.
        for joint in ctrlJointSet:
            jointName = self.getCtrlNiceNameForPublish(joint)
            cmds.container(self.ctrl_container, edit=True, publishAndBind=[joint+'.rotate', jointName+'_rotate'])
            
        # Create a custom keyable attribute on the character root transform by the control name to adjust the weight of
        # the driver joint layer by using the method "createCtrlRigWeightAttributeOnRootTransform".
        self.createCtrlRigWeightAttributeOnRootTransform(self.namePrefix, ctrlJointSet+[dynSettingsCtrl['transform']])
        cmds.select(clear=True)


    def applyDynamic_FK_Stretchy(self):

        '''The control rigging procedure for this method will be the same as 'Dynamic_FK', with added stretch
        functionality to work with the dynamic curve.'''

        # The dynamic FK control will consist of two sets of joint layers, one which will be used to control a dynamic curve
        # (input curve), which is skinned to it, whose output curve
        # will drive another joint layer, using spline IK, and this joint layer will drive the actual (selected) joint hierarchy.

        # This joint layer will be used as control, and so, we'll set the connectLayer to False (notice the second last argument).
        ctrlJointSet, null, ctrlLayerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                           self.ctrlRigName,
                                                                                           self.characterName,
                                                                                           True,
                                                                                           'On',
                                                                                           True,
                                                                                           self.controlColour,
                                                                                           False)
        # The 'null' is used above since no driver constraints are returned, it's an empty list,
        # since this is not the driver joint layer.
        
        # Collect the control layer joints to be added to the control rig container.
        self.collectedNodes.extend(ctrlJointSet)        

        # Get the radius of the shape to be applied to the FK control joints.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.35

        # Lock the translation and scale attributes of the control joints, and apply shapes to it.
        for joint in ctrlJointSet:
            cmds.setAttr(joint+'.drawStyle', 2)
            mfunc.lockHideChannelAttrs(joint, 't', 'radi', keyable=False, lock=True)
            mfunc.lockHideChannelAttrs(joint, 'v', visible=False)
            xhandle = objects.load_xhandleShape(joint, colour=self.controlColour, transformOnly=True)
            cmds.setAttr(xhandle['shape']+'.localScaleX', shapeRadius)
            cmds.setAttr(xhandle['shape']+'.localScaleY', shapeRadius)
            cmds.setAttr(xhandle['shape']+'.localScaleZ', shapeRadius)
            cmds.setAttr(xhandle['shape']+'.drawStyle', 5)

        # Create a parent switch group for the root FK control.
        self.createParentSwitchGrpForTransform(ctrlLayerRootJoint, constrainToRootCtrl=True)

        # Now create the driver joint layer.
        defJointSet, driver_constraints, defLayerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                                       self.ctrlRigName,
                                                                                                       self.characterName,
                                                                                                       False,
                                                                                                       'None',
                                                                                                       True,
                                                                                                       None,
                                                                                                       True)
        # Collect the driver layer joints to be added to the control rig container.
        self.collectedNodes.extend(defJointSet)

        # Update the instance attribute for the driver joint layer set.
        self.driverJointLayerSet = defJointSet

        # Update the instance attribute to contain the driver constraints for the joint hiearachy.
        self.driverConstraintsForInput = driver_constraints

        # Create the driver curve.
        curveCVposString = '['
        jointIt = defLayerRootJoint
        while jointIt:
            pos = cmds.xform(jointIt, query=True, worldSpace=True, translation=True)
            curveCVposString += str(tuple(pos))+','
            jointIt = cmds.listRelatives(jointIt, children=True, type='joint')
        curveCVposString = curveCVposString[:-1] + ']'
        curveCVposList = eval(curveCVposString)
        driverCurve = cmds.curve(degree=1, point=curveCVposList)
        driverCurve = cmds.rename(driverCurve, self.namePrefix+'_driverCurve')

        # Skin the driver curve to the FK control joints. To collect all the nodes created during skinning,
        # perform skinning while in a temp namespace, and then collect all nodes within the namespace.
        cmds.namespace(setNamespace=':')
        tempNamespaceName = self.namePrefix+'_tempNamespace'
        cmds.namespace(addNamespace=tempNamespaceName)
        cmds.namespace(setNamespace=tempNamespaceName)
        cmds.select(ctrlJointSet, replace=True)
        cmds.select(driverCurve, add=True)
        if _maya_version >=2013:
            skinCluster = cmds.skinCluster(bindMethod=0, toSelectedBones=True, normalizeWeights=2, obeyMaxInfluences=False, \
                                           maximumInfluences=5, dropoffRate=4.0, ignoreHierarchy=True)
        else:
            skinCluster = cmds.skinCluster(skinMethod=0, toSelectedBones=True, normalizeWeights=2, obeyMaxInfluences=False, \
                                           maximumInfluences=5, dropoffRate=4.0, ignoreHierarchy=True)
        cmds.select(clear=True)

        namespaceNodes = cmds.namespaceInfo(listOnlyDependencyNodes=True)
        skin_nodes = []
        for node in namespaceNodes:
            nodeName = node.partition(':')[2]
            if re.search('^%s' % self.userSpecName, nodeName):
                nameSeq = re.split('\d+', nodeName)
                name = cmds.rename(node, '%s_driverCurve_%s'%(self.namePrefix, ''.join(nameSeq)))
                skin_nodes.append(name.partition(':')[2])
        cmds.namespace(setNamespace=':')
        cmds.namespace(moveNamespace=[tempNamespaceName, ':'], force=True)
        cmds.namespace(removeNamespace=tempNamespaceName)
        mfunc.addNodesToContainer(self.ctrl_container, skin_nodes, includeHierarchyBelow=True)
        cmds.select(clear=True)

        # Create a control group node to place all DAG nodes (not part of the character joint hierarchy) under it.
        self.createCtrlGrp()
        
        # Collect it to be added to the control rig container.
        self.collectedNodes.append(self.ctrlGrp)

        # Turn the driver curve dynamic (whose output is to be used in spline IK), and set attributes accordingly.
        all_nodes_p = set(cmds.ls())
        cmds.select(driverCurve, replace=True)
        mel.eval('makeCurvesDynamicHairs 0 0 1')
        all_nodes_f = set(cmds.ls())
        hair_nodes = all_nodes_f.difference(all_nodes_p)

        for node in hair_nodes:
            if node.startswith('rebuildCurve'):
                cmds.rename(node, self.namePrefix+'_rebuildCurve')
            if re.match('^follicle\d+$', node):
                follicle = cmds.rename(node, self.namePrefix+'_follicle')
                cmds.parent(follicle, ':'+self.ctrlGrp, absolute=True)
                cmds.setAttr(follicle+'.visibility', 0)
            if re.match('^curve\d+$', node):
                dynCurve = cmds.rename(node, self.namePrefix+'_dynCurve')
                cmds.parent(dynCurve, self.ctrlGrp, absolute=True)
                cmds.setAttr(dynCurve+'.visibility', 0)
            if re.match('^hairSystem\d+$', node):
                hairSystem = cmds.rename(node, self.namePrefix+'_hairSystem')
                cmds.parent(hairSystem, self.ctrlGrp, absolute=True)
                cmds.setAttr(hairSystem+'.visibility', 0)
            if node.startswith('nucleus'):
                nucleus = cmds.rename(node, self.namePrefix+'_nucleus')
                cmds.parent(nucleus, self.ctrlGrp, absolute=True)
                cmds.setAttr(nucleus+'.visibility', 0)
            if re.match('^curve\d+rebuiltCurveShape\d+$', node):
                cmds.rename(node, self.namePrefix+'_driverCurveRebuiltShape')
            if re.match('^hairSystem\d+Follicles$', node):
                cmds.delete(node)
            if re.match('^hairSystem\d+OutputCurves$', node):
                cmds.delete(node)

        cmds.select(clear=True)
        cmds.setAttr(follicle+'Shape.pointLock', 1)
        cmds.setAttr(follicle+'Shape.restPose', 3)

        # Create the spline IK using the driver curve's dynamic output curve.
        defSplineIkHandleNodes = cmds.ikHandle(startJoint=defLayerRootJoint, endEffector=defJointSet[1], \
                                               solver='ikSplineSolver', createCurve=False, simplifyCurve=False, \
                                               rootOnCurve=False, parentCurve=False, curve=dynCurve)
        defSplineIkHandle = cmds.rename(defSplineIkHandleNodes[0], self.namePrefix+'_drivenSplineIkHandle')
        defSplineIkEffector = cmds.rename(defSplineIkHandleNodes[1], self.namePrefix+'_drivenSplineIkEffector')
        cmds.parent(defSplineIkHandle, self.ctrlGrp, absolute=True)
        cmds.setAttr(defSplineIkHandle+'.visibility', 0)

        # Connect the scale attributes between the control and driver joint layers.
        for ctlJoint, defJoint in zip(ctrlJointSet, defJointSet):
            cmds.connectAttr(ctlJoint+'.scale', defJoint+'.scale')

        # Create and place a handle/control for accessing dynamic attributes for the dynamic curve for the spline IK.
        # Add custom attributes to it and connect them.
        colour = self.controlColour - 1
        if self.controlColour < 1:
            colour = self.controlColour + 1
        dynSettingsCtrl = objects.load_xhandleShape(self.namePrefix+'_dynSettings_CNTL', colour=colour, transformOnly=True)
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.32
        cmds.setAttr(dynSettingsCtrl['shape']+'.localScaleX', shapeRadius)
        cmds.setAttr(dynSettingsCtrl['shape']+'.localScaleY', shapeRadius)
        cmds.setAttr(dynSettingsCtrl['shape']+'.localScaleZ', shapeRadius)
        cmds.connectAttr(self.globalScaleAttr, dynSettingsCtrl['transform']+'.scaleX')
        cmds.connectAttr(self.globalScaleAttr, dynSettingsCtrl['transform']+'.scaleY')
        cmds.connectAttr(self.globalScaleAttr, dynSettingsCtrl['transform']+'.scaleZ')
        cmds.setAttr(dynSettingsCtrl['shape']+'.drawStyle', 2)
        cmds.setAttr(dynSettingsCtrl['shape']+'.drawStyle', keyable=False, lock=True)
        cmds.xform(dynSettingsCtrl['transform'], worldSpace=True, translation=\
                   cmds.xform(defJointSet[1], query=True, worldSpace=True, translation=True), rotation=\
                   cmds.xform(defJointSet[1], query=True, worldSpace=True, rotation=True))
        upAxis = cmds.getAttr(defJointSet[1]+'.nodeAxes')[1]
        translation = {'X':[shapeRadius*10.0, 0, 0], 'Y':[0, shapeRadius*10.0, 0], 'Z':[0, 0, shapeRadius*10.0]}[upAxis]
        cmds.xform(dynSettingsCtrl['transform'], relative=True, translation=translation)
        cmds.parent(dynSettingsCtrl['transform'], self.ctrlGrp, absolute=True)
        mfunc.parentConstraint(defJointSet[1], dynSettingsCtrl['transform'], maintainOffset=True)

        cmds.setAttr(dynSettingsCtrl['transform']+'.overrideEnabled', 1)
        cmds.connectAttr(self.controlRigDisplayLayer + '.visibility', dynSettingsCtrl['transform']+'.overrideVisibility')
        mfunc.lockHideChannelAttrs(dynSettingsCtrl['transform'], 't', 'r', 's', keyable=False, lock=True)
        mfunc.lockHideChannelAttrs(dynSettingsCtrl['transform'], 'v', visible=False)
        cmds.select(clear=True)
        
        # Add custom dynamic attributes to the control.
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='enum', longName='DynamicsSwitch', keyable=True, enumName=':Off:On')
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='iterations', keyable=True, defaultValue=20)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='stiffness', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='stiffnessScale', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='startCurveAttract', keyable=True, defaultValue=1)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='startCurveAttractDamp', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='damping', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='gravity', keyable=True, defaultValue=0.98)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='enum', longName='Turbulence', keyable=True, enumName=' ')
        cmds.setAttr(dynSettingsCtrl['transform']+'.Turbulence', lock=True)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='intensity', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='frequency', keyable=True, defaultValue=0.2)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='speed', keyable=True, defaultValue=0.2)
        
        # Connect the dynamic attributes.
        for driver, driven in [[0, 0], [1, 2]]:
            cmds.setAttr(dynSettingsCtrl['transform']+'.DynamicsSwitch', driver)
            cmds.setAttr(follicle+'Shape.simulationMethod', driven)
            cmds.setDrivenKeyframe(follicle+'Shape.simulationMethod', currentDriver=dynSettingsCtrl['transform']+'.DynamicsSwitch')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.iterations', hairSystem+'Shape.iterations')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.stiffness', hairSystem+'Shape.stiffness')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.stiffnessScale', hairSystem+'Shape.stiffnessScale[0].stiffnessScale_FloatValue')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.startCurveAttract', hairSystem+'Shape.startCurveAttract')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.startCurveAttractDamp', hairSystem+'Shape.attractionDamp')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.damping', hairSystem+'Shape.damp')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.gravity', hairSystem+'Shape.gravity')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.intensity', hairSystem+'Shape.turbulenceStrength')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.frequency', hairSystem+'Shape.turbulenceFrequency')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.speed', hairSystem+'Shape.turbulenceSpeed')
        cmds.select(clear=True)

        # Add all the rest of the nodes to the control rig container.
        mfunc.addNodesToContainer(self.ctrl_container, self.collectedNodes, includeHierarchyBelow=True)
        
        # Publish the rotate attributes for the control joints.
        for joint in ctrlJointSet:
            jointName = self.getCtrlNiceNameForPublish(joint)
            cmds.container(self.ctrl_container, edit=True, publishAndBind=[joint+'.rotate', jointName+'_rotate'])
            
        # Create a custom keyable attribute on the character root transform by the control name to adjust the weight
        # of the driver joint layer by using the method "createCtrlRigWeightAttributeOnRootTransform".
        self.createCtrlRigWeightAttributeOnRootTransform(self.namePrefix, \
                                                         ctrlJointSet+[dynSettingsCtrl['transform']])
        cmds.select(clear=True)


    def applyDynamic_End_IK(self):

        '''This method applies an IK control transform at the end position of the selected joint hierarchy on a joint layer
        to drive it indirectly using another joint layer driven using a dynamic spline IK curve which is skinned to the 
        first joint layer.'''

        # This control will consist of two joint layers on top of the selected joint hierarchy. The first layer will have
        # an IK control at its end joint position, with a dynamic curve skinned to it, whose output curve will drive the
        # splineIK for the next joint layer which will drive the joint hierarchy.

        # Create the first joint layer, to be used with an RP IK.
        ctrlJointSet, null, ctrlLayerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                           self.ctrlRigName+'_drv', # '_drv' suffix to keep unique FK layer name, since asControl=False.
                                                                                           self.characterName,
                                                                                           False,
                                                                                           'None',
                                                                                           True,
                                                                                           None,
                                                                                           False)
        # Collect it to be added to the control rig container.
        self.collectedNodes.extend(ctrlJointSet)

        # Create the driver joint layer.
        defJointSet, driver_constraints, defLayerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                                       self.ctrlRigName,
                                                                                                       self.characterName,
                                                                                                       False,
                                                                                                       'None',
                                                                                                       True,
                                                                                                       None,
                                                                                                       True)
        # Collect it to be added to the control rig container.
        self.collectedNodes.extend(defJointSet)

        # Update the instance attribute for the driver joint layer set.
        self.driverJointLayerSet = defJointSet

        # Update the instance attribute to contain the driver constraints for the joint hiearachy.
        self.driverConstraintsForInput = driver_constraints

        # Create a control group node to place all DAG nodes (not part of the character joint hierarchy) under it.
        self.createCtrlGrp()
        
        # Collect it to be added to the control rig container.
        self.collectedNodes.append(self.ctrlGrp)

        # Create the RP IK on the first joint layer.
        ctrlIkHandleNodes = cmds.ikHandle(startJoint=ctrlLayerRootJoint, endEffector=ctrlJointSet[1], solver='ikRPsolver')
        ctrlIkHandle = cmds.rename(ctrlIkHandleNodes[0], self.namePrefix+'_driverIkHandle')
        cmds.setAttr(ctrlIkHandle+'.rotateOrder', 3)
        ctrlIkEffector = cmds.rename(ctrlIkHandleNodes[1], self.namePrefix+'_driverIkEffector')
        cmds.parent(ctrlIkHandle, self.ctrlGrp, absolute=True)
        cmds.setAttr(ctrlIkHandle+'.visibility', 0)

        # Create the end IK control with its pre-transform and position it.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.88
        controlHandle = objects.load_xhandleShape(self.namePrefix+'_CNTL', colour=self.controlColour)
        cmds.setAttr(controlHandle['preTransform']+'.rotateOrder', 3)
        if self.transOriFunc == 'local_orientation':
            tempConstraint = cmds.parentConstraint(ctrlJointSet[1], controlHandle['preTransform'], maintainOffset=False)
        if self.transOriFunc == 'world':
            tempConstraint = cmds.pointConstraint(ctrlJointSet[1], controlHandle['preTransform'], maintainOffset=False)
        cmds.delete(tempConstraint)
        
        cmds.setAttr(controlHandle['shape']+'.localScaleX', shapeRadius)
        cmds.setAttr(controlHandle['shape']+'.localScaleY', shapeRadius)
        cmds.setAttr(controlHandle['shape']+'.localScaleZ', shapeRadius)
        cmds.setAttr(controlHandle['shape']+'.drawStyle', 6)
        cmds.setAttr(controlHandle['transform']+'.rotateOrder', 3)
        mfunc.pointConstraint(controlHandle['transform'], ctrlIkHandle, maintainOffset=False)
        cmds.addAttr(controlHandle['transform'], attributeType='float', longName='IK_Twist', defaultValue=0, keyable=True)
        cmds.connectAttr(controlHandle['transform']+'.IK_Twist', ctrlIkHandle+'.twist')
        cmds.setAttr(controlHandle['transform']+'.overrideEnabled', 1)
        cmds.connectAttr(self.controlRigDisplayLayer + '.visibility', controlHandle['transform']+'.overrideVisibility')
        mfunc.lockHideChannelAttrs(controlHandle['transform'], 'r', 's', keyable=False, lock=True)
        mfunc.lockHideChannelAttrs(controlHandle['transform'], 'v', visible=False)
        cmds.parent(controlHandle['preTransform'], self.ctrlGrp, absolute=True)
        cmds.select(clear=True)

        # Create a parent switch group for the end IK control handle.
        self.createParentSwitchGrpForTransform(controlHandle['transform'], constrainToRootCtrl=True, 
                                               weight=1, connectScaleWithRootCtrl=True)
        
        # Create the driver curve, whose dynamic output curve will drive the splineIK for the driver joint layer.
        curveCVposString = '['
        jointIt = defLayerRootJoint
        while jointIt:
            pos = cmds.xform(jointIt, query=True, worldSpace=True, translation=True)
            curveCVposString += str(tuple(pos))+','
            jointIt = cmds.listRelatives(jointIt, children=True, type='joint')
        curveCVposString = curveCVposString[:-1] + ']'
        curveCVposList = eval(curveCVposString)
        driverCurve = cmds.curve(degree=1, point=curveCVposList)
        driverCurve = cmds.rename(driverCurve, self.namePrefix+'_driverCurve')

        # Skin the driver curve to the first joint layer. To collect all the nodes created during skinning, perform
        # skinning while in a temp namespace, and then collect all nodes within the namespace.
        cmds.namespace(setNamespace=':')
        tempNamespaceName = self.namePrefix+'_tempNamespace'
        cmds.namespace(addNamespace=tempNamespaceName)
        cmds.namespace(setNamespace=tempNamespaceName)
        cmds.select(ctrlJointSet, replace=True)
        cmds.select(driverCurve, add=True)
        if _maya_version >=2013:
            skinCluster = cmds.skinCluster(bindMethod=0, toSelectedBones=True, normalizeWeights=2, obeyMaxInfluences=False, \
                                           maximumInfluences=5, dropoffRate=4.0, ignoreHierarchy=True)
        else:
            skinCluster = cmds.skinCluster(skinMethod=0, toSelectedBones=True, normalizeWeights=2, obeyMaxInfluences=False, \
                                           maximumInfluences=5, dropoffRate=4.0, ignoreHierarchy=True)
        cmds.select(clear=True)
        namespaceNodes = cmds.namespaceInfo(listOnlyDependencyNodes=True)
        skin_nodes = []
        for node in namespaceNodes:
            nodeName = node.partition(':')[2]
            if re.search('^%s' % self.userSpecName, nodeName):
                nameSeq = re.split('\d+', nodeName)
                name = cmds.rename(node, '%s_driverCurve_%s'%(self.namePrefix, ''.join(nameSeq)))
                skin_nodes.append(name.partition(':')[2])
        cmds.namespace(setNamespace=':')
        cmds.namespace(moveNamespace=[tempNamespaceName, ':'], force=True)
        cmds.namespace(removeNamespace=tempNamespaceName)
        self.collectedNodes.extend(skin_nodes)
        cmds.select(clear=True)

        # Turn the driver curve dynamic (whose output to be used in spline IK), and set attributes accordingly.
        all_nodes_p = set(cmds.ls())
        cmds.select(driverCurve, replace=True)
        mel.eval('makeCurvesDynamicHairs 0 0 1')
        all_nodes_f = set(cmds.ls())
        hair_nodes = all_nodes_f.difference(all_nodes_p)

        for node in hair_nodes:
            if node.startswith('rebuildCurve'):
                cmds.rename(node, self.namePrefix+'_rebuildCurve')
            if re.match('^follicle\d+$', node):
                follicle = cmds.rename(node, self.namePrefix+'_follicle')
                cmds.parent(follicle, ':'+self.ctrlGrp, absolute=True)
                cmds.setAttr(follicle+'.visibility', 0)
            if re.match('^curve\d+$', node):
                dynCurve = cmds.rename(node, self.namePrefix+'_dynCurve')
                cmds.parent(dynCurve, self.ctrlGrp, absolute=True)
                cmds.setAttr(dynCurve+'.visibility', 0)
            if re.match('^hairSystem\d+$', node):
                hairSystem = cmds.rename(node, self.namePrefix+'_hairSystem')
                cmds.parent(hairSystem, self.ctrlGrp, absolute=True)
                cmds.setAttr(hairSystem+'.visibility', 0)
            if node.startswith('nucleus'):
                nucleus = cmds.rename(node, self.namePrefix+'_nucleus')
                cmds.parent(nucleus, self.ctrlGrp, absolute=True)
                cmds.setAttr(nucleus+'.visibility', 0)
            if re.match('^curve\d+rebuiltCurveShape\d+$', node):
                cmds.rename(node, self.namePrefix+'_driverCurveRebuiltShape')
            if re.match('^hairSystem\d+Follicles$', node):
                cmds.delete(node)
            if re.match('^hairSystem\d+OutputCurves$', node):
                cmds.delete(node)
        cmds.select(clear=True)
        cmds.setAttr(follicle+'Shape.pointLock', 1)
        cmds.setAttr(follicle+'Shape.restPose', 3)

        # Create the spline IK using the driver curve's dynamic output curve on the driver joint layer.
        defSplineIkHandleNodes = cmds.ikHandle(startJoint=defLayerRootJoint, endEffector=defJointSet[1], \
                                               solver='ikSplineSolver', createCurve=False, simplifyCurve=False, \
                                               rootOnCurve=False, parentCurve=False, curve=dynCurve)
        defSplineIkHandle = cmds.rename(defSplineIkHandleNodes[0], self.namePrefix+'_drivenSplineIkHandle')
        defSplineIkEffector = cmds.rename(defSplineIkHandleNodes[1], self.namePrefix+'_drivenSplineIkEffector')
        cmds.parent(defSplineIkHandle, self.ctrlGrp, absolute=True)
        cmds.setAttr(defSplineIkHandle+'.visibility', 0)

        # Create and position the pole vector handle for the RP IK on the control joint layer.
        pvHandle = objects.load_xhandleShape(self.namePrefix+'_PV_CNTL', colour=self.controlColour)
        cmds.setAttr(pvHandle['shape']+'.localScaleX', shapeRadius*0.5)
        cmds.setAttr(pvHandle['shape']+'.localScaleY', shapeRadius*0.5)
        cmds.setAttr(pvHandle['shape']+'.localScaleZ', shapeRadius*0.5)
        cmds.setAttr(pvHandle['shape']+'.drawStyle', 3)
        p_vector = cmds.getAttr(ctrlIkHandle+'.poleVector')[0]
        cmds.setAttr(pvHandle['preTransform']+'.translate', *p_vector, type='double3')
        cmds.setAttr(pvHandle['transform']+'.overrideEnabled', 1)
        cmds.connectAttr(self.controlRigDisplayLayer + '.visibility', pvHandle['transform']+'.overrideVisibility')
        cmds.parent(pvHandle['preTransform'], self.ctrlGrp, absolute=True)
        mfunc.lockHideChannelAttrs(pvHandle['transform'], 'r', 's', keyable=False, lock=True)
        mfunc.lockHideChannelAttrs(pvHandle['transform'], 'v', visible=False)
        cmds.poleVectorConstraint(pvHandle['transform'], ctrlIkHandle, name=pvHandle['transform']+'_poleVectorConstraint')
        self.createParentSwitchGrpForTransform(pvHandle['transform'], constrainToRootCtrl=True, 
                                               weight=1, connectScaleWithRootCtrl=True)

        # Create and place a handle/control for accessing dynamic attributes for the driver curve for the spline IK.
        # Add custom attributes to it and connect them.
        colour = self.controlColour - 1
        if self.controlColour < 1:
            colour = self.controlColour + 1
        dynSettingsCtrl = objects.load_xhandleShape(self.namePrefix+'_dynSettings_CNTL', colour=colour, transformOnly=True)
        dynHandleShapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.32
        cmds.setAttr(dynSettingsCtrl['shape']+'.localScaleX', dynHandleShapeRadius)
        cmds.setAttr(dynSettingsCtrl['shape']+'.localScaleY', dynHandleShapeRadius)
        cmds.setAttr(dynSettingsCtrl['shape']+'.localScaleZ', dynHandleShapeRadius)
        cmds.connectAttr(self.globalScaleAttr, dynSettingsCtrl['transform']+'.scaleX')
        cmds.connectAttr(self.globalScaleAttr, dynSettingsCtrl['transform']+'.scaleY')
        cmds.connectAttr(self.globalScaleAttr, dynSettingsCtrl['transform']+'.scaleZ')
        cmds.setAttr(dynSettingsCtrl['shape']+'.drawStyle', 2)
        cmds.xform(dynSettingsCtrl['transform'], worldSpace=True, translation=\
                   cmds.xform(defJointSet[1], query=True, worldSpace=True, translation=True), rotation=\
                   cmds.xform(defJointSet[1], query=True, worldSpace=True, rotation=True))
        upAxis = cmds.getAttr(defJointSet[1]+'.nodeAxes')[1]
        translation = {'X':[shapeRadius*6.5, 0, 0], 'Y':[0, shapeRadius*6.5, 0], 'Z':[0, 0, shapeRadius*6.5]}[upAxis]
        cmds.xform(dynSettingsCtrl['transform'], relative=True, translation=translation)
        cmds.parent(dynSettingsCtrl['transform'], self.ctrlGrp, absolute=True)
        mfunc.parentConstraint(defJointSet[1], dynSettingsCtrl['transform'], maintainOffset=True)
        cmds.setAttr(dynSettingsCtrl['transform']+'.overrideEnabled', 1)
        cmds.connectAttr(self.controlRigDisplayLayer + '.visibility', dynSettingsCtrl['transform']+'.overrideVisibility')
        mfunc.lockHideChannelAttrs(dynSettingsCtrl['transform'], 't', 'r', 's', keyable=False, lock=True)
        mfunc.lockHideChannelAttrs(dynSettingsCtrl['transform'], 'v', visible=False)
        cmds.select(clear=True)
        
        # Add custom dynamic attributes to the control.
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='enum', longName='DynamicsSwitch', keyable=True, enumName=':Off:On')
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='iterations', keyable=True, defaultValue=20)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='stiffness', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='stiffnessScale', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='startCurveAttract', keyable=True, defaultValue=1)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='startCurveAttractDamp', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='damping', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='gravity', keyable=True, defaultValue=0.98)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='enum', longName='Turbulence', keyable=True, enumName=' ')
        cmds.setAttr(dynSettingsCtrl['transform']+'.Turbulence', lock=True)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='intensity', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='frequency', keyable=True, defaultValue=0.2)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='speed', keyable=True, defaultValue=0.2)
        
        # Connect the dynamic attributes.
        for driver, driven in [[0, 0], [1, 2]]:
            cmds.setAttr(dynSettingsCtrl['transform']+'.DynamicsSwitch', driver)
            cmds.setAttr(follicle+'Shape.simulationMethod', driven)
            cmds.setDrivenKeyframe(follicle+'Shape.simulationMethod', currentDriver=dynSettingsCtrl['transform']+'.DynamicsSwitch')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.iterations', hairSystem+'Shape.iterations')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.stiffness', hairSystem+'Shape.stiffness')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.stiffnessScale', hairSystem+'Shape.stiffnessScale[0].stiffnessScale_FloatValue')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.startCurveAttract', hairSystem+'Shape.startCurveAttract')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.startCurveAttractDamp', hairSystem+'Shape.attractionDamp')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.damping', hairSystem+'Shape.damp')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.gravity', hairSystem+'Shape.gravity')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.intensity', hairSystem+'Shape.turbulenceStrength')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.frequency', hairSystem+'Shape.turbulenceFrequency')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.speed', hairSystem+'Shape.turbulenceSpeed')
        cmds.select(clear=True)

        # Add all the rest of the nodes to the control rig container and publish necessary attributes.
        mfunc.addNodesToContainer(self.ctrl_container, self.collectedNodes, includeHierarchyBelow=True)
        cmds.container(self.ctrl_container, edit=True, publishAndBind=[pvHandle['transform']+'.translate', 'dynamicEndIk_pvCntl_translate'])
        cmds.container(self.ctrl_container, edit=True, publishAndBind=[controlHandle['transform']+'.translate', 'dynamicEndIk_cntl_translate'])
        cmds.container(self.ctrl_container, edit=True, publishAndBind=[controlHandle['transform']+'.IK_Twist', 'dynamicEndIk_ik_twist'])

        # Create a custom keyable attribute on the character root transform by the control name to adjust the weight of the
        # driver joint layer by using the method "createCtrlRigWeightAttributeOnRootTransform".
        self.createCtrlRigWeightAttributeOnRootTransform(self.namePrefix, \
                                                         [controlHandle['transform'], pvHandle['transform'], dynSettingsCtrl['transform']])
        cmds.select(clear=True)


    def applyDynamic_End_IK_Stretchy(self):

        '''The control rigging procedure for this method will be the same as 'Dynamic_End_IK', with added
        stretch functionality to work with the dynamic curve.'''

        # This control will consist of two joint layers on top of the selected joint hierarchy. The first layer will
        # have an IK control at its end joint position, with a dynamic curve skinned to it,
        # whose output curve will drive the splineIK for the next joint layer which will drive the joint hierarchy.

        # Create the first joint layer, to be used with an RP IK.
        ctrlJointSet, null, ctrlLayerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                           self.ctrlRigName+'_drv', # '_drv' suffix to keep unique FK layer name, since asControl=False.
                                                                                           self.characterName,
                                                                                           False,
                                                                                           'None',
                                                                                           True,
                                                                                           None,
                                                                                           False)
        # Collect it to be added to the control rig container.
        self.collectedNodes.extend(ctrlJointSet)

        # Create the driver joint layer.
        defJointSet, driver_constraints, defLayerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                                       self.ctrlRigName,
                                                                                                       self.characterName,
                                                                                                       False,
                                                                                                       'None',
                                                                                                       True,
                                                                                                       None,
                                                                                                       True)
        # Collect it to be added to the control rig container.
        self.collectedNodes.extend(defJointSet)

        # Update the instance attribute for the driver joint layer set.
        self.driverJointLayerSet = defJointSet

        # Update the instance attribute to contain the driver constraints for the joint hiearachy.
        self.driverConstraintsForInput = driver_constraints

        # Create a control group node to place all DAG nodes (not part of the character joint hierarchy) under it.
        self.createCtrlGrp()
        
        # Collect it to be added to the control rig container.
        self.collectedNodes.append(self.ctrlGrp)

        # Create the RP IK on the first joint layer.
        ctrlIkHandleNodes = cmds.ikHandle(startJoint=ctrlLayerRootJoint, endEffector=ctrlJointSet[1], solver='ikRPsolver')
        ctrlIkHandle = cmds.rename(ctrlIkHandleNodes[0], self.namePrefix+'_driverIkHandle')
        cmds.setAttr(ctrlIkHandle+'.rotateOrder', 3)
        ctrlIkEffector = cmds.rename(ctrlIkHandleNodes[1], self.namePrefix+'_driverIkEffector')
        cmds.parent(ctrlIkHandle, self.ctrlGrp, absolute=True)
        cmds.setAttr(ctrlIkHandle+'.visibility', 0)

        # Create the end IK control with its pre-transform and position it.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.88
        controlHandle = objects.load_xhandleShape(self.namePrefix+'_CNTL', colour=self.controlColour)
        cmds.setAttr(controlHandle['preTransform']+'.rotateOrder', 3)
        if self.transOriFunc == 'local_orientation':
            tempConstraint = cmds.parentConstraint(ctrlJointSet[1], controlHandle['preTransform'], maintainOffset=False)
        if self.transOriFunc == 'world':
            tempConstraint = cmds.pointConstraint(ctrlJointSet[1], controlHandle['preTransform'], maintainOffset=False)
        cmds.delete(tempConstraint)
        cmds.setAttr(controlHandle['shape']+'.localScaleX', shapeRadius)
        cmds.setAttr(controlHandle['shape']+'.localScaleY', shapeRadius)
        cmds.setAttr(controlHandle['shape']+'.localScaleZ', shapeRadius)
        cmds.setAttr(controlHandle['shape']+'.drawStyle', 6)
        cmds.setAttr(controlHandle['transform']+'.rotateOrder', 3)
        mfunc.pointConstraint(controlHandle['transform'], ctrlIkHandle, maintainOffset=False)
        cmds.addAttr(controlHandle['transform'], attributeType='float', longName='IK_Twist', defaultValue=0, keyable=True)
        cmds.connectAttr(controlHandle['transform']+'.IK_Twist', ctrlIkHandle+'.twist')
        cmds.setAttr(controlHandle['transform']+'.overrideEnabled', 1)
        cmds.connectAttr(self.controlRigDisplayLayer + '.visibility', controlHandle['transform']+'.overrideVisibility')
        mfunc.lockHideChannelAttrs(controlHandle['transform'], 'r', 's', keyable=False, lock=True)
        mfunc.lockHideChannelAttrs(controlHandle['transform'], 'v', visible=False)
        cmds.parent(controlHandle['preTransform'], self.ctrlGrp, absolute=True)
        cmds.select(clear=True)

        # Create a parent switch group for the end IK control handle.
        self.createParentSwitchGrpForTransform(controlHandle['transform'], constrainToRootCtrl=True, 
                                               weight=1, connectScaleWithRootCtrl=True)
        
        # Add the stretch functionality.
        ctrlRootJointPosLocator = cmds.spaceLocator(name=self.namePrefix+'_rootJointPos_loc')[0]
        cmds.setAttr(ctrlRootJointPosLocator+'.visibility', 0)
        cmds.parent(ctrlRootJointPosLocator, self.ctrlGrp, absolute=True)
        mfunc.pointConstraint(ctrlLayerRootJoint, ctrlRootJointPosLocator, maintainOffset=False)
        
        # Real-time distance between the base/root position and the end/tip.
        distNode = cmds.createNode('distanceBetween', name=self.namePrefix+'_distance', skipSelect=True)
        cmds.connectAttr(ctrlRootJointPosLocator+'Shape.worldPosition[0]', distNode+'.point1')
        cmds.connectAttr(controlHandle['transform']+'Shape.worldPosition[0]', distNode+'.point2')
        
        # Divide the current length of the joint chain by the global scale to normalize it.
        chainLengthNormalize = cmds.createNode('multiplyDivide', name=self.namePrefix+'_legLengthNormalize', skipSelect=True)
        cmds.connectAttr(self.globalScaleAttr, chainLengthNormalize+'.input2X')
        cmds.connectAttr(distNode+'.distance', chainLengthNormalize+'.input1X')
        cmds.setAttr(chainLengthNormalize+'.operation', 2)
        
        # Get the default, total length of the joint chain.
        jointAxis = cmds.getAttr(ctrlLayerRootJoint+'.nodeAxes')[0]
        chainLength = 0.0
        for joint in ctrlJointSet[1:]:
            chainLength += cmds.getAttr(joint+'.translate'+jointAxis)
        
        # Divide the current distance between the base-tip of the joint chain by its default length to get the stretch factor.
        stretchLengthDivide = cmds.createNode('multiplyDivide', name=self.namePrefix+'_stretchLengthDivide', skipSelect=True)
        cmds.setAttr(stretchLengthDivide+'.input2X', abs(chainLength), lock=True)
        cmds.setAttr(stretchLengthDivide+'.operation', 2)
        cmds.connectAttr(chainLengthNormalize+'.outputX', stretchLengthDivide+'.input1X')
        
        # Use a condition node to check if the current length of the chain is more than the 
        # default rest length of the chain, to allow the stretch factor.
        stretchCondition = cmds.createNode('condition', name=self.namePrefix+'_stretchCondition', skipSelect=True)
        cmds.setAttr(stretchCondition+'.operation', 2)
        cmds.setAttr(stretchCondition+'.colorIfFalseR', 1)
        cmds.connectAttr(stretchLengthDivide+'.outputX', stretchCondition+'.colorIfTrueR')
        cmds.connectAttr(stretchLengthDivide+'.input2X', stretchCondition+'.secondTerm')
        cmds.connectAttr(stretchLengthDivide+'.input1X', stretchCondition+'.firstTerm')
        
        # Connect the stretch length multpliers to the aim translations for the control joints. 
        for joint in ctrlJointSet[1:]:
            stretchMultiply = cmds.createNode('multDoubleLinear', name=joint.replace('_joint', '_stretchMultiply'), skipSelect=True)
            cmds.setAttr(stretchMultiply+'.input1', cmds.getAttr(joint+'.translate'+jointAxis))
            cmds.connectAttr(stretchCondition+'.outColorR', stretchMultiply+'.input2')
            cmds.connectAttr(stretchMultiply+'.output', joint+'.translate'+jointAxis)
            self.collectedNodes.append(stretchMultiply)
            
        self.collectedNodes.extend([distNode, chainLengthNormalize, stretchLengthDivide, stretchCondition])
        
        # Connect the aim translate attribute between the control and driver joint layers.
        for ctlJoint, defJoint in zip(ctrlJointSet, defJointSet):
            cmds.connectAttr(ctlJoint+'.translate'+jointAxis, defJoint+'.translate'+jointAxis)

        # Create the driver curve, whose dynamic output curve will drive the splineIK for the driver joint layer.
        curveCVposString = '['
        jointIt = defLayerRootJoint
        while jointIt:
            pos = cmds.xform(jointIt, query=True, worldSpace=True, translation=True)
            curveCVposString += str(tuple(pos))+','
            jointIt = cmds.listRelatives(jointIt, children=True, type='joint')
        curveCVposString = curveCVposString[:-1] + ']'
        curveCVposList = eval(curveCVposString)
        driverCurve = cmds.curve(degree=1, point=curveCVposList)
        driverCurve = cmds.rename(driverCurve, self.namePrefix+'_driverCurve')

        # Skin the driver curve to the first joint layer. To collect all the nodes created during skinning, perform
        # skinning while in a temp namespace, and then collect all nodes within the namespace.
        cmds.namespace(setNamespace=':')
        tempNamespaceName = self.namePrefix+'_tempNamespace'
        cmds.namespace(addNamespace=tempNamespaceName)
        cmds.namespace(setNamespace=tempNamespaceName)
        cmds.select(ctrlJointSet, replace=True)
        cmds.select(driverCurve, add=True)
        if _maya_version >=2013:
            skinCluster = cmds.skinCluster(bindMethod=0, toSelectedBones=True, normalizeWeights=2, obeyMaxInfluences=False, \
                                           maximumInfluences=5, dropoffRate=4.0, ignoreHierarchy=True)
        else:
            skinCluster = cmds.skinCluster(skinMethod=0, toSelectedBones=True, normalizeWeights=2, obeyMaxInfluences=False, \
                                           maximumInfluences=5, dropoffRate=4.0, ignoreHierarchy=True)
        cmds.select(clear=True)
        namespaceNodes = cmds.namespaceInfo(listOnlyDependencyNodes=True)
        skin_nodes = []
        for node in namespaceNodes:
            nodeName = node.partition(':')[2]
            if re.search('^%s' % self.userSpecName, nodeName):
                nameSeq = re.split('\d+', nodeName)
                name = cmds.rename(node, '%s_driverCurve_%s'%(self.namePrefix, ''.join(nameSeq)))
                skin_nodes.append(name.partition(':')[2])
        cmds.namespace(setNamespace=':')
        cmds.namespace(moveNamespace=[tempNamespaceName, ':'], force=True)
        cmds.namespace(removeNamespace=tempNamespaceName)
        self.collectedNodes.extend(skin_nodes)
        cmds.select(clear=True)

        # Turn the driver curve dynamic (whose output to be used in spline IK), and set attributes accordingly.
        all_nodes_p = set(cmds.ls())
        cmds.select(driverCurve, replace=True)
        mel.eval('makeCurvesDynamicHairs 0 0 1')
        all_nodes_f = set(cmds.ls())
        hair_nodes = all_nodes_f.difference(all_nodes_p)

        for node in hair_nodes:
            if node.startswith('rebuildCurve'):
                cmds.rename(node, self.namePrefix+'_rebuildCurve')
            if re.match('^follicle\d+$', node):
                follicle = cmds.rename(node, self.namePrefix+'_follicle')
                cmds.parent(follicle, ':'+self.ctrlGrp, absolute=True)
                cmds.setAttr(follicle+'.visibility', 0)
            if re.match('^curve\d+$', node):
                dynCurve = cmds.rename(node, self.namePrefix+'_dynCurve')
                cmds.parent(dynCurve, self.ctrlGrp, absolute=True)
                cmds.setAttr(dynCurve+'.visibility', 0)
            if re.match('^hairSystem\d+$', node):
                hairSystem = cmds.rename(node, self.namePrefix+'_hairSystem')
                cmds.parent(hairSystem, self.ctrlGrp, absolute=True)
                cmds.setAttr(hairSystem+'.visibility', 0)
            if node.startswith('nucleus'):
                nucleus = cmds.rename(node, self.namePrefix+'_nucleus')
                cmds.parent(nucleus, self.ctrlGrp, absolute=True)
                cmds.setAttr(nucleus+'.visibility', 0)
            if re.match('^curve\d+rebuiltCurveShape\d+$', node):
                cmds.rename(node, self.namePrefix+'_driverCurveRebuiltShape')
            if re.match('^hairSystem\d+Follicles$', node):
                cmds.delete(node)
            if re.match('^hairSystem\d+OutputCurves$', node):
                cmds.delete(node)
        cmds.select(clear=True)
        cmds.setAttr(follicle+'Shape.pointLock', 1)
        cmds.setAttr(follicle+'Shape.restPose', 3)

        # Create the spline IK using the driver curve's dynamic output curve on the driver joint layer.
        defSplineIkHandleNodes = cmds.ikHandle(startJoint=defLayerRootJoint, endEffector=defJointSet[1], \
                                               solver='ikSplineSolver', createCurve=False, simplifyCurve=False, \
                                               rootOnCurve=False, parentCurve=False, curve=dynCurve)
        defSplineIkHandle = cmds.rename(defSplineIkHandleNodes[0], self.namePrefix+'_drivenSplineIkHandle')
        defSplineIkEffector = cmds.rename(defSplineIkHandleNodes[1], self.namePrefix+'_drivenSplineIkEffector')
        cmds.parent(defSplineIkHandle, self.ctrlGrp, absolute=True)
        cmds.setAttr(defSplineIkHandle+'.visibility', 0)

        # Create and position the pole vector handle for the RP IK on the control joint layer.
        pvHandle = objects.load_xhandleShape(self.namePrefix+'_PV_CNTL', colour=self.controlColour)
        cmds.setAttr(pvHandle['shape']+'.localScaleX', shapeRadius*0.5)
        cmds.setAttr(pvHandle['shape']+'.localScaleY', shapeRadius*0.5)
        cmds.setAttr(pvHandle['shape']+'.localScaleZ', shapeRadius*0.5)
        cmds.setAttr(pvHandle['shape']+'.drawStyle', 3)
        p_vector = cmds.getAttr(ctrlIkHandle+'.poleVector')[0]
        cmds.setAttr(pvHandle['preTransform']+'.translate', *p_vector, type='double3')
        cmds.setAttr(pvHandle['transform']+'.overrideEnabled', 1)
        cmds.connectAttr(self.controlRigDisplayLayer + '.visibility', pvHandle['transform']+'.overrideVisibility')
        cmds.parent(pvHandle['preTransform'], self.ctrlGrp, absolute=True)
        mfunc.lockHideChannelAttrs(pvHandle['transform'], 'r', 's', keyable=False, lock=True)
        mfunc.lockHideChannelAttrs(pvHandle['transform'], 'v', visible=False)
        cmds.poleVectorConstraint(pvHandle['transform'], ctrlIkHandle, name=pvHandle['transform']+'_poleVectorConstraint')
        self.createParentSwitchGrpForTransform(pvHandle['transform'], constrainToRootCtrl=True, 
                                               weight=1, connectScaleWithRootCtrl=True)

        # Create and place a handle/control for accessing dynamic attributes for the driver curve for the spline IK.
        # Add custom attributes to it and connect them.
        colour = self.controlColour - 1
        if self.controlColour < 1:
            colour = self.controlColour + 1
        dynSettingsCtrl = objects.load_xhandleShape(self.namePrefix+'_dynSettings_CNTL', colour=colour, transformOnly=True)
        dynHandleShapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.32
        cmds.setAttr(dynSettingsCtrl['shape']+'.localScaleX', dynHandleShapeRadius)
        cmds.setAttr(dynSettingsCtrl['shape']+'.localScaleY', dynHandleShapeRadius)
        cmds.setAttr(dynSettingsCtrl['shape']+'.localScaleZ', dynHandleShapeRadius)
        cmds.connectAttr(self.globalScaleAttr, dynSettingsCtrl['transform']+'.scaleX')
        cmds.connectAttr(self.globalScaleAttr, dynSettingsCtrl['transform']+'.scaleY')
        cmds.connectAttr(self.globalScaleAttr, dynSettingsCtrl['transform']+'.scaleZ')
        cmds.setAttr(dynSettingsCtrl['shape']+'.drawStyle', 2)
        cmds.xform(dynSettingsCtrl['transform'], worldSpace=True, translation=\
                   cmds.xform(defJointSet[1], query=True, worldSpace=True, translation=True), rotation=\
                   cmds.xform(defJointSet[1], query=True, worldSpace=True, rotation=True))
        upAxis = cmds.getAttr(defJointSet[1]+'.nodeAxes')[1]
        translation = {'X':[shapeRadius*6.5, 0, 0], 'Y':[0, shapeRadius*6.5, 0], 'Z':[0, 0, shapeRadius*6.5]}[upAxis]
        cmds.xform(dynSettingsCtrl['transform'], relative=True, translation=translation)
        cmds.parent(dynSettingsCtrl['transform'], self.ctrlGrp, absolute=True)
        mfunc.parentConstraint(defJointSet[1], dynSettingsCtrl['transform'], maintainOffset=True)
        cmds.setAttr(dynSettingsCtrl['transform']+'.overrideEnabled', 1)
        cmds.connectAttr(self.controlRigDisplayLayer + '.visibility', dynSettingsCtrl['transform']+'.overrideVisibility')
        mfunc.lockHideChannelAttrs(dynSettingsCtrl['transform'], 't', 'r', 's', keyable=False, lock=True)
        mfunc.lockHideChannelAttrs(dynSettingsCtrl['transform'], 'v', visible=False)
        cmds.select(clear=True)
        
        # Add custom dynamic attributes to the control.
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='enum', longName='DynamicsSwitch', keyable=True, enumName=':Off:On')
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='iterations', keyable=True, defaultValue=20)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='stiffness', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='stiffnessScale', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='startCurveAttract', keyable=True, defaultValue=1)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='startCurveAttractDamp', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='damping', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='gravity', keyable=True, defaultValue=0.98)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='enum', longName='Turbulence', keyable=True, enumName=' ')
        cmds.setAttr(dynSettingsCtrl['transform']+'.Turbulence', lock=True)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='intensity', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='frequency', keyable=True, defaultValue=0.2)
        cmds.addAttr(dynSettingsCtrl['transform'], attributeType='float', longName='speed', keyable=True, defaultValue=0.2)
        
        # Connect the dynamic attributes.
        for driver, driven in [[0, 0], [1, 2]]:
            cmds.setAttr(dynSettingsCtrl['transform']+'.DynamicsSwitch', driver)
            cmds.setAttr(follicle+'Shape.simulationMethod', driven)
            cmds.setDrivenKeyframe(follicle+'Shape.simulationMethod', currentDriver=dynSettingsCtrl['transform']+'.DynamicsSwitch')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.iterations', hairSystem+'Shape.iterations')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.stiffness', hairSystem+'Shape.stiffness')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.stiffnessScale', hairSystem+'Shape.stiffnessScale[0].stiffnessScale_FloatValue')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.startCurveAttract', hairSystem+'Shape.startCurveAttract')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.startCurveAttractDamp', hairSystem+'Shape.attractionDamp')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.damping', hairSystem+'Shape.damp')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.gravity', hairSystem+'Shape.gravity')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.intensity', hairSystem+'Shape.turbulenceStrength')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.frequency', hairSystem+'Shape.turbulenceFrequency')
        cmds.connectAttr(dynSettingsCtrl['transform']+'.speed', hairSystem+'Shape.turbulenceSpeed')
        cmds.select(clear=True)

        # Add all the rest of the nodes to the control rig container and publish necessary attributes.
        mfunc.addNodesToContainer(self.ctrl_container, self.collectedNodes, includeHierarchyBelow=True)
        cmds.container(self.ctrl_container, edit=True, publishAndBind=\
                       [pvHandle['transform']+'.translate', 'dynamicEndIk_pvCntl_translate'])
        cmds.container(self.ctrl_container, edit=True, publishAndBind=\
                       [controlHandle['transform']+'.translate', 'dynamicEndIk_cntl_translate'])
        cmds.container(self.ctrl_container, edit=True, publishAndBind=\
                       [controlHandle['transform']+'.IK_Twist', 'dynamicEndIk_ik_twist'])

        # Create a custom keyable attribute on the character root transform by the control name to adjust the
        # weight of the driver joint layer by using the method "createCtrlRigWeightAttributeOnRootTransform".
        self.createCtrlRigWeightAttributeOnRootTransform(self.namePrefix, \
                                                         [controlHandle['transform'], 
                                                          pvHandle['transform'], 
                                                          dynSettingsCtrl['transform']])
        cmds.select(clear=True)


class HingeControl(BaseJointControl):

    """This hierarchy type is constructed from a hinge module with three nodes, and can be applied with a rotate
    plane IK control. This hierarchy is useful where the middle joint acts as a hinge as it can only rotate in an 
    axis with a preferred and limited direction of rotation."""


    def __init__(self,  *args, **kwargs):
        BaseJointControl.__init__(self,  *args, **kwargs)


    def applyIK(self):

        '''Create a simple rotate plane IK control.'''

        # We'll create a single driver joint layer with an IK RP solver on it.
        jointSet, driver_constraints, layerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                                 self.ctrlRigName,
                                                                                                 self.characterName,
                                                                                                 False,
                                                                                                 'None',
                                                                                                 True,
                                                                                                 None,
                                                                                                 True)
        # Collect it to be added to the control rig container.
        self.collectedNodes.extend(jointSet)        

        # Update the instance attribute for the driver joint layer set.
        self.driverJointLayerSet = jointSet

        # Update the instance attribute to contain the driver constraints for the joint hiearachy.
        self.driverConstraintsForInput = driver_constraints

        # Create a control group node to place all DAG nodes (not part of the character joint hierarchy) under it.
        self.createCtrlGrp()
        
        # Collect it to be added to the control rig container.
        self.collectedNodes.append(self.ctrlGrp)        

        # Create the IK RP solver on the joint layer.
        ctrlIkHandleNodes = cmds.ikHandle(startJoint=layerRootJoint, endEffector=jointSet[1], solver='ikRPsolver')
        ctrlIkHandle = cmds.rename(ctrlIkHandleNodes[0], self.namePrefix+'_driverIkHandle')
        cmds.setAttr(ctrlIkHandle+'.rotateOrder', 3)
        ctrlIkEffector = cmds.rename(ctrlIkHandleNodes[1], self.namePrefix+'_driverIkEffector')
        cmds.parent(ctrlIkHandle, self.ctrlGrp, absolute=True)
        cmds.setAttr(ctrlIkHandle+'.visibility', 0)

        # Create the IK control with its pre-transform and position it.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.88
        controlHandle = objects.load_xhandleShape(self.namePrefix+'_CNTL', colour=self.controlColour)
        cmds.setAttr(controlHandle['preTransform']+'.rotateOrder', 3)
        if self.transOriFunc == 'local_orientation':
            tempConstraint = cmds.parentConstraint(jointSet[1], controlHandle['preTransform'], maintainOffset=False)
        if self.transOriFunc == 'world':
            tempConstraint = cmds.pointConstraint(jointSet[1], controlHandle['preTransform'], maintainOffset=False)
        cmds.delete(tempConstraint)
        cmds.setAttr(controlHandle['shape']+'.localScaleX', shapeRadius)
        cmds.setAttr(controlHandle['shape']+'.localScaleY', shapeRadius)
        cmds.setAttr(controlHandle['shape']+'.localScaleZ', shapeRadius)
        cmds.setAttr(controlHandle['shape']+'.drawStyle', 6)
        cmds.setAttr(controlHandle['transform']+'.rotateOrder', 3)
        mfunc.pointConstraint(controlHandle['transform'], ctrlIkHandle, maintainOffset=False)
        mfunc.orientConstraint(controlHandle['transform'], jointSet[1], maintainOffset=True)
        cmds.setAttr(controlHandle['transform']+'.overrideEnabled', 1)
        cmds.connectAttr(self.controlRigDisplayLayer + '.visibility', controlHandle['transform']+'.overrideVisibility')
        cmds.setAttr(controlHandle['transform']+'.scaleX', keyable=False, lock=True)
        cmds.setAttr(controlHandle['transform']+'.scaleY', keyable=False, lock=True)
        cmds.setAttr(controlHandle['transform']+'.scaleZ', keyable=False, lock=True)
        cmds.setAttr(controlHandle['transform']+'.visibility', keyable=False)
        cmds.parent(controlHandle['preTransform'], self.ctrlGrp, absolute=True)
        cmds.select(clear=True)

        # Create a parent switch group for the IK control handle.
        self.createParentSwitchGrpForTransform(controlHandle['transform'], constrainToRootCtrl=True, 
                                               weight=1, connectScaleWithRootCtrl=True)
        
        # Calculate the position for the IK pole vector control.
        shldr_pos = cmds.xform(layerRootJoint, query=True, worldSpace=True, translation=True)
        wrist_pos = cmds.xform(jointSet[1], query=True, worldSpace=True, translation=True)
        arm_mid_pos = eval(cmds.getAttr(self.rootJoint+'.ikSegmentMidPos'))
        elbow_pos = cmds.xform(jointSet[2], query=True, worldSpace=True, translation=True)
        ik_pv_offset_pos = mfunc.returnOffsetPositionBetweenTwoVectors(elbow_pos, arm_mid_pos, -2)

        # Create and position the IK pole vector control.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.32
        elbow_pv = objects.load_xhandleShape(self.namePrefix+'_elbowPV_CNTL', colour=self.controlColour)
        cmds.xform(elbow_pv['preTransform'], worldSpace=True, translation=ik_pv_offset_pos)
        cmds.setAttr(elbow_pv['shape']+'.localScaleX', shapeRadius)
        cmds.setAttr(elbow_pv['shape']+'.localScaleY', shapeRadius)
        cmds.setAttr(elbow_pv['shape']+'.localScaleZ', shapeRadius)
        cmds.setAttr(elbow_pv['shape']+'.drawStyle', 3)
        mfunc.lockHideChannelAttrs(elbow_pv['transform'], 'r', 's', keyable=False, lock=True)
        mfunc.lockHideChannelAttrs(elbow_pv['transform'], 'v', visible=False)
        cmds.parent(elbow_pv['preTransform'], self.ctrlGrp, absolute=True)
        cmds.poleVectorConstraint(elbow_pv['transform'], ctrlIkHandle, name=elbow_pv['transform']+'_poleVectorConstraint')

        # Create a parent switch group for pole vector control handle.
        self.createParentSwitchGrpForTransform(elbow_pv['transform'], constrainToRootCtrl=True, 
                                               weight=1, connectScaleWithRootCtrl=True)
        
        # Add all the rest of the nodes to the control rig container and publish necessary attributes.
        mfunc.addNodesToContainer(self.ctrl_container, self.collectedNodes, 
                                  includeHierarchyBelow=True)
        cmds.container(self.ctrl_container, edit=True, publishAndBind=\
                       [elbow_pv['transform']+'.translate', 'ik_elbowPV_cntl_translate'])
        cmds.container(self.ctrl_container, edit=True, publishAndBind=\
                       [controlHandle['transform']+'.translate', 'ik_cntl_translate'])
        cmds.container(self.ctrl_container, edit=True, publishAndBind=\
                       [controlHandle['transform']+'.rotate', 'ik_cntl_rotate'])

        # Create a custom keyable attribute on the character root transform by the control name to adjust
        # the weight of the driver joint layer by using the method "createCtrlRigWeightAttributeOnRootTransform".
        self.createCtrlRigWeightAttributeOnRootTransform(self.namePrefix,
                                                         [controlHandle['transform'], 
                                                          elbow_pv['transform']])
        cmds.select(clear=True)


    def applyIK_Stretchy(self):

        '''Create a simple rotate plane IK control with stretch functionality.'''

        # We'll create a single driver joint layer with an IK RP solver on it.
        jointSet, driver_constraints, layerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                                 self.ctrlRigName,
                                                                                                 self.characterName,
                                                                                                 False,
                                                                                                 'None',
                                                                                                 True,
                                                                                                 None,
                                                                                                 True)
        # Collect it to be added to the control rig container.
        self.collectedNodes.extend(jointSet)

        # Update the instance attribute for the driver joint layer set.
        self.driverJointLayerSet = jointSet

        # Update the instance attribute to contain the driver constraints for the joint hierarchy.
        self.driverConstraintsForInput = driver_constraints

        # Create a control group node to place all DAG nodes (not part of the character joint hierarchy) under it.
        self.createCtrlGrp()
        
        # Collect it to be added to the control rig container.
        self.collectedNodes.append(self.ctrlGrp)        

        # Create the IK RP solver on the joint layer.
        ctrlIkHandleNodes = cmds.ikHandle(startJoint=layerRootJoint, endEffector=jointSet[1], solver='ikRPsolver')
        ctrlIkHandle = cmds.rename(ctrlIkHandleNodes[0], self.namePrefix+'_driverIkHandle')
        cmds.setAttr(ctrlIkHandle+'.rotateOrder', 3)
        ctrlIkEffector = cmds.rename(ctrlIkHandleNodes[1], self.namePrefix+'_driverIkEffector')
        cmds.parent(ctrlIkHandle, self.ctrlGrp, absolute=True)
        cmds.setAttr(ctrlIkHandle+'.visibility', 0)

        # Create the IK control with its pre-transform and position it.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.88
        controlHandle = objects.load_xhandleShape(self.namePrefix+'_CNTL', colour=self.controlColour)
        cmds.setAttr(controlHandle['preTransform']+'.rotateOrder', 3)
        if self.transOriFunc == 'local_orientation':
            tempConstraint = cmds.parentConstraint(jointSet[1], controlHandle['preTransform'], maintainOffset=False)
        if self.transOriFunc == 'world':
            tempConstraint = cmds.pointConstraint(jointSet[1], controlHandle['preTransform'], maintainOffset=False)
        cmds.delete(tempConstraint)        
        cmds.setAttr(controlHandle['shape']+'.localScaleX', shapeRadius)
        cmds.setAttr(controlHandle['shape']+'.localScaleY', shapeRadius)
        cmds.setAttr(controlHandle['shape']+'.localScaleZ', shapeRadius)
        cmds.setAttr(controlHandle['shape']+'.drawStyle', 6)
        cmds.setAttr(controlHandle['transform']+'.rotateOrder', 3)
        mfunc.pointConstraint(controlHandle['transform'], ctrlIkHandle, maintainOffset=False)
        mfunc.orientConstraint(controlHandle['transform'], jointSet[1], maintainOffset=True)
        cmds.setAttr(controlHandle['transform']+'.overrideEnabled', 1)
        cmds.connectAttr(self.controlRigDisplayLayer + '.visibility', controlHandle['transform']+'.overrideVisibility')
        mfunc.lockHideChannelAttrs(controlHandle['transform'], 's', keyable=False, lock=True)
        mfunc.lockHideChannelAttrs(controlHandle['transform'], 'v', visible=False)
        cmds.parent(controlHandle['preTransform'], self.ctrlGrp, absolute=True)
        cmds.select(clear=True)

        # Create a parent switch group for the IK control handle.
        self.createParentSwitchGrpForTransform(controlHandle['transform'], constrainToRootCtrl=True, 
                                               weight=1, connectScaleWithRootCtrl=True)
        
        # Calculate the position for the IK pole vector control.
        shldr_pos = cmds.xform(layerRootJoint, query=True, worldSpace=True, translation=True)
        wrist_pos = cmds.xform(jointSet[1], query=True, worldSpace=True, translation=True)
        arm_mid_pos = eval(cmds.getAttr(self.rootJoint+'.ikSegmentMidPos'))
        elbow_pos = cmds.xform(jointSet[2], query=True, worldSpace=True, translation=True)
        ik_pv_offset_pos = mfunc.returnOffsetPositionBetweenTwoVectors(elbow_pos, arm_mid_pos, -2)

        # Create and position the IK pole vector control.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.32
        elbow_pv = objects.load_xhandleShape(self.namePrefix+'_elbowPV_CNTL', colour=self.controlColour)
        cmds.xform(elbow_pv['preTransform'], worldSpace=True, translation=ik_pv_offset_pos)
        cmds.setAttr(elbow_pv['shape']+'.localScaleX', shapeRadius)
        cmds.setAttr(elbow_pv['shape']+'.localScaleY', shapeRadius)
        cmds.setAttr(elbow_pv['shape']+'.localScaleZ', shapeRadius)
        cmds.setAttr(elbow_pv['shape']+'.drawStyle', 3)
        mfunc.lockHideChannelAttrs(elbow_pv['transform'], 'r', 's', keyable=False, lock=True)
        mfunc.lockHideChannelAttrs(elbow_pv['transform'], 'v', visible=False)
        cmds.parent(elbow_pv['preTransform'], self.ctrlGrp, absolute=True)
        cmds.poleVectorConstraint(elbow_pv['transform'], ctrlIkHandle, name=elbow_pv['transform']+'_poleVectorConstraint')

        # Create a parent switch group for pole vector control handle.
        self.createParentSwitchGrpForTransform(elbow_pv['transform'], constrainToRootCtrl=True, 
                                               weight=1, connectScaleWithRootCtrl=True)
        
        # Add the stretch functionality.

        # Get the real-time world position of the shoulder joint.
        shldrPosVecLoc = cmds.spaceLocator(name=self.namePrefix+'_shldrPos_loc')[0]
        mfunc.pointConstraint(layerRootJoint, shldrPosVecLoc, maintainOffset=False)
        cmds.parent(shldrPosVecLoc, self.ctrlGrp, absolute=True)
        cmds.setAttr(shldrPosVecLoc+'.visibility', 0)
        
        # Get the real-time length of the arm, from shoulder to wrist.
        distanceBtwn = cmds.createNode('distanceBetween', name=self.namePrefix+'_shldrToWrist_distance', skipSelect=True)
        cmds.connectAttr(shldrPosVecLoc+'Shape.worldPosition[0]', distanceBtwn+'.point1')
        cmds.connectAttr(controlHandle['transform']+'Shape.worldPosition[0]', distanceBtwn+'.point2')
        
        # Divide the real-time length of the arm by globalScale to normalize it.
        armLengthNormalize = cmds.createNode('multiplyDivide', name=self.namePrefix+'_shldrToWrist_distance_normalize', skipSelect=True)
        cmds.connectAttr(self.globalScaleAttr, armLengthNormalize+'.input2X')
        cmds.connectAttr(distanceBtwn+'.distance', armLengthNormalize+'.input1X')
        cmds.setAttr(armLengthNormalize+'.operation', 2)
        
        # Get the default rest length of the arm.
        jointAxis =  cmds.getAttr(layerRootJoint+'.nodeAxes')[0]
        upperArmLengthTranslate = cmds.getAttr(jointSet[2]+'.translate'+jointAxis)
        lowerArmLengthTranslate = cmds.getAttr(jointSet[1]+'.translate'+jointAxis)
        armLength = upperArmLengthTranslate + lowerArmLengthTranslate
        
        # Divide the real-time length of the arm, shoulder to wrist by the default rest length, to get the stretch factor.
        stretchLengthDivide = cmds.createNode('multiplyDivide', name=self.namePrefix+'_shldrToWrist_stretchLengthDivide', skipSelect=True)
        cmds.setAttr(stretchLengthDivide+'.input2X', abs(armLength), lock=True)
        cmds.setAttr(stretchLengthDivide+'.operation', 2)
        cmds.connectAttr(armLengthNormalize+'.outputX', stretchLengthDivide+'.input1X')
        
        # Use a condition node to check if the current length of the arm is more than the 
        # default rest length of the arm, to allow the stretch factor.        
        stretchCondition = cmds.createNode('condition', name=self.namePrefix+'_shldrToWrist_stretchCondition', skipSelect=True)
        cmds.setAttr(stretchCondition+'.operation', 2)
        cmds.setAttr(stretchCondition+'.colorIfFalseR', 1)
        cmds.connectAttr(stretchLengthDivide+'.outputX', stretchCondition+'.colorIfTrueR')
        cmds.connectAttr(stretchLengthDivide+'.input2X', stretchCondition+'.secondTerm')
        cmds.connectAttr(stretchLengthDivide+'.input1X', stretchCondition+'.firstTerm')
        
        # Multiply the current length of shoulder to elbow by the stretch factor.
        lowerArmTranslateMultiply = cmds.createNode('multDoubleLinear',
                                                    name=self.namePrefix+'_shldrToElbow_lowerArmTranslateMultiply', skipSelect=True)
        cmds.connectAttr(stretchCondition+'.outColorR', lowerArmTranslateMultiply+'.input1')
        cmds.setAttr(lowerArmTranslateMultiply+'.input2', lowerArmLengthTranslate)
        cmds.connectAttr(lowerArmTranslateMultiply+'.output', jointSet[1]+'.translate'+jointAxis)
        
        # Multiply the current length of elbow to wrist by the stretch factor.
        upperArmTranslateMultiply = cmds.createNode('multDoubleLinear',
                                                    name=self.namePrefix+'_elbowToWrist_upperArmTranslateMultiply', skipSelect=True)
        cmds.connectAttr(stretchCondition+'.outColorR', upperArmTranslateMultiply+'.input1')
        cmds.setAttr(upperArmTranslateMultiply+'.input2', upperArmLengthTranslate)
        cmds.connectAttr(upperArmTranslateMultiply+'.output', jointSet[2]+'.translate'+jointAxis)

        # Collect the utility nodes.
        self.collectedNodes.extend([distanceBtwn, armLengthNormalize, stretchLengthDivide, 
                                    stretchCondition, lowerArmTranslateMultiply, upperArmTranslateMultiply])
        
        
        # Add all the rest of the nodes to the control rig container and publish necessary attributes.
        mfunc.addNodesToContainer(self.ctrl_container, self.collectedNodes, includeHierarchyBelow=True)
        cmds.container(self.ctrl_container, edit=True, publishAndBind=\
                       [elbow_pv['transform']+'.translate', 'ik_elbowPV_cntl_translate'])
        cmds.container(self.ctrl_container, edit=True, publishAndBind=[controlHandle['transform']+'.translate', 'ik_cntl_translate'])
        cmds.container(self.ctrl_container, edit=True, publishAndBind=[controlHandle['transform']+'.rotate', 'ik_cntl_rotate'])

        # Create a custom keyable attribute on the character root transform by the control name to adjust the weight
        # of the driver joint layer by using the method "createCtrlRigWeightAttributeOnRootTransform".
        self.createCtrlRigWeightAttributeOnRootTransform(self.namePrefix,
                                                         [controlHandle['transform'], 
                                                          elbow_pv['transform']])
        cmds.select(clear=True)


    def applyIK_Stretchy_With_Elbow(self):

        '''Create a simple rotate plane IK control with stretch functionality to work with the IK transform control
        as well with the pole vector transform (in elbow mode).'''

        # We'll create a single driver joint layer with an IK RP solver on it.
        jointSet, driver_constraints, layerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                                 self.ctrlRigName,
                                                                                                 self.characterName,
                                                                                                 False,
                                                                                                 'None',
                                                                                                 True,
                                                                                                 None,
                                                                                                 True)
        # Collect it to be added to the control rig container.
        self.collectedNodes.extend(jointSet)

        # Update the instance attribute for the driver joint layer set.
        self.driverJointLayerSet = jointSet

        # Update the instance attribute to contain the driver constraints for the joint hiearachy.
        self.driverConstraintsForInput = driver_constraints

        # Create a control group node to place all DAG nodes (not part of the character joint hierarchy) under it.
        self.createCtrlGrp()
        
        # Collect it to be added to the control rig container.
        self.collectedNodes.append(self.ctrlGrp)        

        # Create the IK RP solver on the joint layer.
        ctrlIkHandleNodes = cmds.ikHandle(startJoint=layerRootJoint, endEffector=jointSet[1], solver='ikRPsolver')
        ctrlIkHandle = cmds.rename(ctrlIkHandleNodes[0], self.namePrefix+'_driverIkHandle')
        cmds.setAttr(ctrlIkHandle+'.rotateOrder', 3)
        ctrlIkEffector = cmds.rename(ctrlIkHandleNodes[1], self.namePrefix+'_driverIkEffector')
        cmds.parent(ctrlIkHandle, self.ctrlGrp, absolute=True)
        cmds.setAttr(ctrlIkHandle+'.visibility', 0)

        # Prep the parent transform for IK control to be used to control it while in elbow FK mode.
        elbowFKTransform = cmds.group(empty=True, name=self.namePrefix+'_elbowFKTransform', parent=self.ctrlGrp)
        cmds.xform(elbowFKTransform, worldSpace=True, translation=cmds.xform(jointSet[1], query=True, worldSpace=True, \
                                                                             translation=True))

        # Create the IK control with its pre-transform and position it.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.88
        controlHandle = objects.load_xhandleShape(self.namePrefix+'_CNTL', colour=self.controlColour)
        cmds.setAttr(controlHandle['preTransform']+'.rotateOrder', 3)
        if self.transOriFunc == 'local_orientation':
            tempConstraint = cmds.parentConstraint(jointSet[1], controlHandle['preTransform'], maintainOffset=False)
        if self.transOriFunc == 'world':
            tempConstraint = cmds.pointConstraint(jointSet[1], controlHandle['preTransform'], maintainOffset=False)
        cmds.delete(tempConstraint)
        cmds.setAttr(controlHandle['shape']+'.localScaleX', shapeRadius)
        cmds.setAttr(controlHandle['shape']+'.localScaleY', shapeRadius)
        cmds.setAttr(controlHandle['shape']+'.localScaleZ', shapeRadius)
        cmds.setAttr(controlHandle['shape']+'.drawStyle', 6)
        cmds.setAttr(controlHandle['transform']+'.rotateOrder', 3)
        mfunc.pointConstraint(controlHandle['transform'], ctrlIkHandle, maintainOffset=False)
        mfunc.orientConstraint(controlHandle['transform'], jointSet[1], maintainOffset=True)
        cmds.addAttr(controlHandle['transform'], attributeType='float', longName='Elbow_Blend', minValue=0, maxValue=1, \
                     defaultValue=0, keyable=True)
        cmds.addAttr(controlHandle['transform'], attributeType='enum', longName='Forearm_FK', enumName='Off:On:', defaultValue=0, \
                     keyable=True)
        cmds.setAttr(controlHandle['transform']+'.overrideEnabled', 1)
        cmds.connectAttr(self.controlRigDisplayLayer + '.visibility', controlHandle['transform']+'.overrideVisibility')
        mfunc.lockHideChannelAttrs(controlHandle['transform'], 's', keyable=False, lock=True)
        mfunc.lockHideChannelAttrs(controlHandle['transform'], 'v', visible=False)
        cmds.parent(controlHandle['preTransform'], elbowFKTransform, absolute=True)
        cmds.select(clear=True)
        
        # Create a parent switch group for the IK control handle.
        self.createParentSwitchGrpForTransform(controlHandle['transform'], elbowFKTransform, constrainToRootCtrl=True, 
                                                               weight=1, connectScaleWithRootCtrl=True)        
        
        # Calculate the position for the IK pole vector control.
        shldr_pos = cmds.xform(layerRootJoint, query=True, worldSpace=True, translation=True)
        wrist_pos = cmds.xform(jointSet[1], query=True, worldSpace=True, translation=True)
        arm_mid_pos = eval(cmds.getAttr(self.rootJoint+'.ikSegmentMidPos'))
        elbow_pos = cmds.xform(jointSet[2], query=True, worldSpace=True, translation=True)
        ik_pv_offset_pos = mfunc.returnOffsetPositionBetweenTwoVectors(elbow_pos, arm_mid_pos, -2)

        # Create and position the IK pole vector control.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.32
        
        # Create the elbow IK pole vector control.
        elbow_pv = objects.load_xhandleShape(self.namePrefix+'_elbowPV_CNTL', colour=self.controlColour)
        cmds.xform(elbow_pv['preTransform'], worldSpace=True, translation=ik_pv_offset_pos)
        cmds.setAttr(elbow_pv['shape']+'.localScaleX', shapeRadius)
        cmds.setAttr(elbow_pv['shape']+'.localScaleY', shapeRadius)
        cmds.setAttr(elbow_pv['shape']+'.localScaleZ', shapeRadius)
        cmds.setAttr(elbow_pv['shape']+'.drawStyle', 3)
        mfunc.lockHideChannelAttrs(elbow_pv['transform'], 's', keyable=False, lock=True)
        mfunc.lockHideChannelAttrs(elbow_pv['transform'], 'v', visible=False)
        cmds.parent(elbow_pv['preTransform'], self.ctrlGrp, absolute=True)
        cmds.poleVectorConstraint(elbow_pv['transform'], ctrlIkHandle, name=elbow_pv['transform']+'_poleVectorConstraint')

        # Create a parent switch group for pole vector control handle.
        self.createParentSwitchGrpForTransform(elbow_pv['transform'], constrainToRootCtrl=True, 
                                                               weight=1, connectScaleWithRootCtrl=True)
        

        # Add the stretch functionality, to work with the elbow mode as shown below.
        
        # Get the real-time world position of the shoulder joint.
        shldrPosVecLoc = cmds.spaceLocator(name=self.namePrefix+'_shldrPos_loc')[0]
        mfunc.pointConstraint(layerRootJoint, shldrPosVecLoc, maintainOffset=False)
        cmds.parent(shldrPosVecLoc, self.ctrlGrp, absolute=True)
        cmds.setAttr(shldrPosVecLoc+'.visibility', 0)
        
        # Real-time shoulder to wrist distance.
        shldrToWrist_distanceBtwn = cmds.createNode('distanceBetween', name=self.namePrefix+'_shldrToWrist_distance', skipSelect=True)
        cmds.connectAttr(shldrPosVecLoc+'Shape.worldPosition[0]', shldrToWrist_distanceBtwn+'.point1')  
        cmds.connectAttr(controlHandle['transform']+'.worldPosition[0]', shldrToWrist_distanceBtwn+'.point2')
        
        # Real-time shoulder to elbow distance.
        shldrToElbow_distanceBtwn = cmds.createNode('distanceBetween', name=self.namePrefix+'_shldrToElbow_distance', skipSelect=True)
        cmds.connectAttr(shldrPosVecLoc+'Shape.worldPosition[0]', shldrToElbow_distanceBtwn+'.point1')  
        cmds.connectAttr(elbow_pv['transform']+'.worldPosition[0]', shldrToElbow_distanceBtwn+'.point2')
        
        # Real-time elbow to wrist distance.
        elbowToWrist_distanceBtwn = cmds.createNode('distanceBetween', name=self.namePrefix+'_elbowToWrist_distance', skipSelect=True)
        cmds.connectAttr(elbow_pv['transform']+'.worldPosition[0]', elbowToWrist_distanceBtwn+'.point1')
        cmds.connectAttr(controlHandle['transform']+'Shape.worldPosition[0]', elbowToWrist_distanceBtwn+'.point2')
        
        # Divide the real-time distances for arm parts by globalScale to normalize them.
        armLengthNormalize = cmds.createNode('multiplyDivide', name=self.namePrefix+'_shldrToWrist_legLengthNormalize', skipSelect=True)
        cmds.connectAttr(shldrToWrist_distanceBtwn+'.distance', armLengthNormalize+'.input1X')
        cmds.connectAttr(self.globalScaleAttr, armLengthNormalize+'.input2X') # For distance from shoulder to wrist
        cmds.connectAttr(self.globalScaleAttr, armLengthNormalize+'.input2Y') # For distance from shoulder to elbow (to be used in elbow mode)
        cmds.connectAttr(self.globalScaleAttr, armLengthNormalize+'.input2Z') # For distance from elbow to wrist (to be used in elbow mode)
        cmds.setAttr(armLengthNormalize+'.operation', 2)
        
        # Get the default rest length of the arm.
        jointAxis =  cmds.getAttr(layerRootJoint+'.nodeAxes')[0]
        upperArmLengthTranslate = cmds.getAttr(jointSet[2]+'.translate'+jointAxis)
        lowerArmLengthTranslate = cmds.getAttr(jointSet[1]+'.translate'+jointAxis)
        armLength = upperArmLengthTranslate + lowerArmLengthTranslate
        
        # Divide the real-time length of the arm, shoulder to wrist by the default rest length, to get the stretch factor.
        stretchLengthDivide = cmds.createNode('multiplyDivide', name=self.namePrefix+'_shldrToWrist_stretchLengthDivide', skipSelect=True)
        cmds.setAttr(stretchLengthDivide+'.input2X', abs(armLength), lock=True)
        cmds.setAttr(stretchLengthDivide+'.operation', 2)
        cmds.connectAttr(armLengthNormalize+'.outputX', stretchLengthDivide+'.input1X')
        
        # Use a condition node to check if the current length of the arm is more than the 
        # default rest length of the arm, to allow the stretch factor.                
        stretchCondition = cmds.createNode('condition', name=self.namePrefix+'_shldrToWrist_stretchCondition', skipSelect=True)
        cmds.setAttr(stretchCondition+'.operation', 2)
        cmds.setAttr(stretchCondition+'.colorIfFalseR', 1)
        cmds.connectAttr(stretchLengthDivide+'.outputX', stretchCondition+'.colorIfTrueR')
        cmds.connectAttr(stretchLengthDivide+'.input2X', stretchCondition+'.secondTerm')
        cmds.connectAttr(stretchLengthDivide+'.input1X', stretchCondition+'.firstTerm')
        
        # Create the nodes/connections for elbow blend mode.
        
        # Lower arm, shoulder to elbow.
        
        # Stretched length, from shoulder to elbow.
        lowerArmTranslateMultiply = cmds.createNode('multDoubleLinear',
                                                    name=self.namePrefix+'_shldrToElbow_lowerArmTranslateMultiply', skipSelect=True)
        cmds.connectAttr(stretchCondition+'.outColorR', lowerArmTranslateMultiply+'.input1')
        cmds.setAttr(lowerArmTranslateMultiply+'.input2', lowerArmLengthTranslate)
        
        # Shoulder to elbow distance, for use in elbow mode. Check for the aim axis translation sign.
        lowerArmDistanceMultiply = cmds.createNode('multDoubleLinear',
                                                    name=self.namePrefix+'_shoulderToElbow_lowerArmDistanceMultiply', skipSelect=True)
        cmds.connectAttr(shldrToElbow_distanceBtwn+'.distance', lowerArmDistanceMultiply+'.input1')
        cmds.setAttr(lowerArmDistanceMultiply+'.input2', math.copysign(1, lowerArmLengthTranslate))
        cmds.connectAttr(lowerArmDistanceMultiply+'.output', armLengthNormalize+'.input1Y')
        
        # Shoulder to elbow length blender from arm stretch to elbow mode.
        lowerArmTranslateBlend = cmds.createNode('blendTwoAttr', \
                                                 name=self.namePrefix+'_shldrToElbow_lowerArmTranslateBlend', skipSelect=True)
        cmds.connectAttr(lowerArmTranslateMultiply+'.output', lowerArmTranslateBlend+'.input[0]')
        cmds.connectAttr(armLengthNormalize+'.outputY', lowerArmTranslateBlend+'.input[1]')
        cmds.connectAttr(lowerArmTranslateBlend+'.output', jointSet[2]+'.translate'+jointAxis)
        
        # In the jointSet, first element is the root joint, second is the end joint, and then beginning from the second 
        # joint to the second last. In this case, there's only three joints in jointSet.
        
        
        # Upper arm, elbow to wrist.
        
        # Stretched length, from elbow to wrist.
        upperArmTranslateMultiply = cmds.createNode('multDoubleLinear',
                                                    name=self.namePrefix+'_elbowToWrist_upperArmTranslateMultiply', skipSelect=True)
        cmds.connectAttr(stretchCondition+'.outColorR', upperArmTranslateMultiply+'.input1')
        cmds.setAttr(upperArmTranslateMultiply+'.input2', upperArmLengthTranslate)
        
        # Elbow to wrist distance, for use in elbow mode. Check for the aim axis translation sign.
        upperArmDistanceMultiply = cmds.createNode('multDoubleLinear',
                                                    name=self.namePrefix+'_elbowToWrist_upperArmDistanceMultiply', skipSelect=True)
        cmds.connectAttr(elbowToWrist_distanceBtwn+'.distance', upperArmDistanceMultiply+'.input1')
        cmds.setAttr(upperArmDistanceMultiply+'.input2', math.copysign(1, upperArmLengthTranslate))
        cmds.connectAttr(upperArmDistanceMultiply+'.output', armLengthNormalize+'.input1Z')
        
        # Elbow to wrist length blender from arm stretch to elbow mode.
        upperArmTranslateBlend = cmds.createNode('blendTwoAttr', \
                                                 name=self.namePrefix+'_elbowToWrist_upperArmTranslateBlend', skipSelect=True)
        cmds.connectAttr(upperArmTranslateMultiply+'.output', upperArmTranslateBlend+'.input[0]')
        cmds.connectAttr(armLengthNormalize+'.outputZ', upperArmTranslateBlend+'.input[1]')
        cmds.connectAttr(upperArmTranslateBlend+'.output', jointSet[1]+'.translate'+jointAxis)
        
        # Connect the 'Elbow Blend' to the blender nodes for lower and upper arms.
        cmds.connectAttr(controlHandle['transform']+'.Elbow_Blend', lowerArmTranslateBlend+'.attributesBlender')
        cmds.connectAttr(controlHandle['transform']+'.Elbow_Blend', upperArmTranslateBlend+'.attributesBlender')
        
        self.collectedNodes.extend([armLengthNormalize, stretchLengthDivide, stretchCondition, 
                                    lowerArmTranslateMultiply, lowerArmDistanceMultiply, upperArmTranslateMultiply, 
                                    upperArmDistanceMultiply, lowerArmTranslateBlend, upperArmTranslateBlend, 
                                    shldrToElbow_distanceBtwn, elbowToWrist_distanceBtwn, shldrToWrist_distanceBtwn])       


        # Prepare the elbow FK mode connections.
        elbowParentConstraintFK = mfunc.parentConstraint(elbow_pv['transform'], elbowFKTransform, maintainOffset=True)
        cmds.connectAttr(controlHandle['transform']+'.Forearm_FK', elbowParentConstraintFK+'.'+elbow_pv['transform']+'W0')

        # Add all the rest of the nodes to the control rig container and publish necessary attributes.
        mfunc.addNodesToContainer(self.ctrl_container, self.collectedNodes, includeHierarchyBelow=True)
        cmds.container(self.ctrl_container, edit=True, publishAndBind=[elbow_pv['transform']+'.translate', \
                                                                       'ik_elbowPV_cntl_translate'])
        cmds.container(self.ctrl_container, edit=True, publishAndBind=[controlHandle['transform']+'.translate', 'ik_cntl_translate'])
        cmds.container(self.ctrl_container, edit=True, publishAndBind=[controlHandle['transform']+'.rotate', 'ik_cntl_rotate'])

        # Create a custom keyable attribute on the character root transform by the control name to adjust the weight
        # of the driver joint layer by using the method "createCtrlRigWeightAttributeOnRootTransform".
        self.createCtrlRigWeightAttributeOnRootTransform(self.namePrefix, \
                                                         [controlHandle['transform'], 
                                                          elbow_pv['transform']])
        cmds.select(clear=True)


class SplineControl(BaseJointControl):

    """This hierarchy type is constructed from a spine module, and can be applied with controls useful for posing
    a character spine or a neck."""


    def __init__(self,  *args, **kwargs):
        BaseJointControl.__init__(self,  *args, **kwargs)


    def applyFK(self):

        '''Overridden method, originally inherited from 'BaseJointControl'. It's been modified to include a base
        control on top of root FK control.'''

        # Create the driver joint layer.
        jointSet, driver_constraints, layerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                                 self.ctrlRigName,
                                                                                                 self.characterName,
                                                                                                 True,           # asControl=True
                                                                                                 'On',
                                                                                                 True,
                                                                                                 self.controlColour,
                                                                                                 True)
        # Collect it to be added to the control rig container.
        self.collectedNodes.extend(jointSet)

        # Update the instance attribute for the driver joint layer set.
        self.driverJointLayerSet = jointSet

        # Update the instance attribute to contain the driver constraints for the joint hiearachy.
        self.driverConstraintsForInput = driver_constraints

        # Create a control group node to place all DAG nodes (not part of the character joint hierarchy) under it.
        self.createCtrlGrp()
        
        # Collect it to be added to the control rig container.
        self.collectedNodes.append(self.ctrlGrp)

        # Calculate the size of shape for the FK control.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.35

        # Add the root control for the joint layer.
        root_cntl = objects.load_xhandleShape(self.namePrefix+'_main_CNTL', colour=self.controlColour)
        cmds.xform(root_cntl['preTransform'], worldSpace=True, translation=\
                   cmds.xform(layerRootJoint, query=True, worldSpace=True, translation=True))
        cmds.parent(root_cntl['preTransform'], self.ctrlGrp, absolute=True)
        mfunc.lockHideChannelAttrs(root_cntl['transform'], 's', keyable=False, lock=True)
        mfunc.lockHideChannelAttrs(root_cntl['transform'], 'v', visible=False)
        cmds.setAttr(root_cntl['shape']+'.localScaleX', shapeRadius*2)
        cmds.setAttr(root_cntl['shape']+'.localScaleY', shapeRadius*2)
        cmds.setAttr(root_cntl['shape']+'.localScaleZ', shapeRadius*2)
        cmds.setAttr(root_cntl['shape']+'.drawStyle', 3)

        # Create a parent switch group for the root control.
        self.createParentSwitchGrpForTransform(root_cntl['transform'], constrainToRootCtrl=True, 
                                                               weight=1, connectScaleWithRootCtrl=True)
        
        # Create a parent switch group for the root FK control joint.
        ps_grp = self.createParentSwitchGrpForTransform(layerRootJoint, constrainToRootCtrl=True)
        
        # Create a pre-transform for the root FK control.
        rootFKPreTransform = cmds.group(empty=True, parent=ps_grp, name=layerRootJoint.replace('_CNTL', '_preTransform'))
        mfunc.align(layerRootJoint, rootFKPreTransform)
        cmds.parent(layerRootJoint, rootFKPreTransform, absolute=True)

        # Set the attributes and assign shapes to the control joints.
        for joint in jointSet:
            cmds.setAttr(joint+'.drawStyle', 2)
            mfunc.lockHideChannelAttrs(joint, 't', 's', 'radi', keyable=False, lock=True)
            mfunc.lockHideChannelAttrs(joint, 'v', visible=False)
            cmds.setAttr(joint+'.overrideEnabled', 1)
            cmds.setAttr(joint+'.overrideColor', self.controlColour)
            
            xhandle = objects.load_xhandleShape(joint, colour=self.controlColour, transformOnly=True)
            cmds.setAttr(xhandle['shape']+'.localScaleX', shapeRadius)
            cmds.setAttr(xhandle['shape']+'.localScaleY', shapeRadius)
            cmds.setAttr(xhandle['shape']+'.localScaleZ', shapeRadius)
            cmds.setAttr(xhandle['shape']+'.drawStyle', 5)

        # Constrain the parent group for the root FK control joint to the root control.
        mfunc.parentConstraint(root_cntl['transform'], rootFKPreTransform, maintainOffset=True)

        # Add the joint layer nodes to the control rig container.
        mfunc.addNodesToContainer(self.ctrl_container, self.collectedNodes, includeHierarchyBelow=True)

        # Publish the attributes for joints.
        for joint in jointSet:
            jointName = self.getCtrlNiceNameForPublish(joint)
            cmds.container(self.ctrl_container, edit=True, publishAndBind=[joint+'.rotate', jointName+'_rotate'])

        # Publish the root control attributes.
        handleName = self.getCtrlNiceNameForPublish(root_cntl['transform'])
        cmds.container(self.ctrl_container, edit=True, publishAndBind=\
                       [root_cntl['transform']+'.translate', handleName+'_translate'])
        cmds.container(self.ctrl_container, edit=True, publishAndBind=\
                               [root_cntl['transform']+'.rotate', handleName+'_rotate'])        

        # Create a custom keyable attribute on the character root control by the control name to adjust the weight
        # of the driver joint layer by using the method "createCtrlRigWeightAttributeOnRootTransform".
        self.createCtrlRigWeightAttributeOnRootTransform(self.namePrefix, jointSet+[root_cntl['transform']])

        cmds.select(clear=True)


    def applyFK_Stretchy(self):

        '''Overridden method, originally inherited from 'BaseJointControl'. It's been modified to include a base 
        control on top of root FK control.'''

        # Create the driver joint layer.
        jointSet, driver_constraints, layerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                                 self.ctrlRigName,
                                                                                                 self.characterName,
                                                                                                 True,           # asControl=True
                                                                                                 'On',
                                                                                                 True,
                                                                                                 self.controlColour,
                                                                                                 True)
        # Collect it to be added to the control rig container.
        self.collectedNodes.extend(jointSet)        

        # Update the instance attribute for the driver joint layer set.
        self.driverJointLayerSet = jointSet

        # Update the instance attribute to contain the driver constraints for the joint hiearachy.
        self.driverConstraintsForInput = driver_constraints

        # Create a control group node to place all DAG nodes (not part of the character joint hierarchy) under it.
        self.createCtrlGrp()
        
        # Collect it to be added to the control rig container.
        self.collectedNodes.append(self.ctrlGrp)        

        # Calculate the size of shape for the fk control.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.35

        # Add the root control for the joint layer.
        root_cntl = objects.load_xhandleShape(self.namePrefix+'_main_CNTL', colour=self.controlColour)
        cmds.xform(root_cntl['preTransform'], worldSpace=True, translation=\
                   cmds.xform(layerRootJoint, query=True, worldSpace=True, translation=True))
        cmds.parent(root_cntl['preTransform'], self.ctrlGrp, absolute=True)
        mfunc.lockHideChannelAttrs(root_cntl['transform'], 's', keyable=False, lock=True)
        mfunc.lockHideChannelAttrs(root_cntl['transform'], 'v', visible=False)
        cmds.setAttr(root_cntl['shape']+'.localScaleX', shapeRadius*2)
        cmds.setAttr(root_cntl['shape']+'.localScaleY', shapeRadius*2)
        cmds.setAttr(root_cntl['shape']+'.localScaleZ', shapeRadius*2)
        cmds.setAttr(root_cntl['shape']+'.drawStyle', 3)

        # Create a parent switch grp for the root control.
        self.createParentSwitchGrpForTransform(root_cntl['transform'], constrainToRootCtrl=True, 
                                                               weight=1, connectScaleWithRootCtrl=True)

        # Create a parent switch group for the root FK control joint.
        ps_grp = self.createParentSwitchGrpForTransform(layerRootJoint, constrainToRootCtrl=True)
        
        # Create a pre-transform for the root FK control.
        rootFKPreTransform = cmds.group(empty=True, parent=ps_grp, name=layerRootJoint.replace('_CNTL', '_preTransform'))
        mfunc.align(layerRootJoint, rootFKPreTransform)
        cmds.parent(layerRootJoint, rootFKPreTransform, absolute=True)        

        # Set the attributes and assign shapes to the control joints.
        for joint in jointSet:
            cmds.setAttr(joint+'.drawStyle', 2)
            mfunc.lockHideChannelAttrs(joint, 't', 'radi', keyable=False, lock=True)
            mfunc.lockHideChannelAttrs(joint, 'v', visible=False)
            cmds.setAttr(joint+'.overrideEnabled', 1)
            cmds.setAttr(joint+'.overrideColor', self.controlColour)
            
            xhandle = objects.load_xhandleShape(joint, colour=self.controlColour, transformOnly=True)
            cmds.setAttr(xhandle['shape']+'.localScaleX', shapeRadius)
            cmds.setAttr(xhandle['shape']+'.localScaleY', shapeRadius)
            cmds.setAttr(xhandle['shape']+'.localScaleZ', shapeRadius)
            cmds.setAttr(xhandle['shape']+'.drawStyle', 5)

        # Constrain the parent group for the root FK control joint to the root control.
        mfunc.parentConstraint(root_cntl['transform'], rootFKPreTransform, maintainOffset=True)

        # Add the joint layer nodes to the control rig container.
        mfunc.addNodesToContainer(self.ctrl_container, self.collectedNodes, includeHierarchyBelow=True)

        # Publish the attributes for joints.
        for joint in jointSet:
            jointName = self.getCtrlNiceNameForPublish(joint)
            cmds.container(self.ctrl_container, edit=True, publishAndBind=[joint+'.rotate', jointName+'_rotate'])
            cmds.container(self.ctrl_container, edit=True, publishAndBind=[joint+'.scale', jointName+'_scale'])

        # Publish the root control attributes.
        handleName = self.getCtrlNiceNameForPublish(root_cntl['transform'])
        cmds.container(self.ctrl_container, edit=True, publishAndBind=\
                       [root_cntl['transform']+'.translate', handleName+'_translate'])
        cmds.container(self.ctrl_container, edit=True, publishAndBind=\
                               [root_cntl['transform']+'.rotate', handleName+'_rotate'])

        # Create a custom keyable attribute on the character root transform by the control name to adjust the
        # weight of the driver joint layer by using the method "createCtrlRigWeightAttributeOnRootTransform".
        self.createCtrlRigWeightAttributeOnRootTransform(self.namePrefix, \
                                                         jointSet+[root_cntl['transform']])
        cmds.select(clear=True)


    def applyReverse_Spine_FK(self):

        '''Creates a layer of FK controls for the joint chain created from a spline module in reverse order with
        respect to its current hierarchy.'''

        # Here we'll create a single joint layer driven by a hierarchy of transforms in reverse order.

        # Create the joint layer.
        jointSet, driver_constraints, layerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                                 self.ctrlRigName,
                                                                                                 self.characterName,
                                                                                                 False,
                                                                                                 'None',
                                                                                                 True,
                                                                                                 False)
        # Collect it to be added to the control rig container.
        self.collectedNodes.extend(jointSet)        

        # Create a list with names of the joints in the joint layer in reverse order.
        joints = [layerRootJoint]
        joints.extend(jointSet[-1:1:-1])
        joints.append(jointSet[1])

        # Update the instance attribute for the driver joint layer set.
        self.driverJointLayerSet = jointSet

        # Update the instance attribute to contain the driver constraints for the joint hiearachy.
        self.driverConstraintsForInput = driver_constraints

        # Create a control group node to place all DAG nodes (not part of the character joint hierarchy) under it.
        self.createCtrlGrp()
        
        # Collect it to be added to the control rig container.
        self.collectedNodes.append(self.ctrlGrp)        

        # Calculate the size of shape for the FK control.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.35

        # Create and position the reverse FK control handles.
        r_fk_handles = []
        for i in range(self.numJoints-1, -1, -1):
            if i == self.numJoints-1:
                ctrl_handle = objects.load_xhandleShape(self.namePrefix+'_root_CNTL', colour=self.controlColour)
            elif i == 0:
                ctrl_handle = objects.load_xhandleShape(self.namePrefix+'_end_CNTL', colour=self.controlColour)
            else:
                ctrl_handle = objects.load_xhandleShape(self.namePrefix+'_%s_CNTL' % i, colour=self.controlColour)

            cmds.xform(ctrl_handle['preTransform'], worldSpace=True, translation=\
                       cmds.xform(joints[i], query=True, worldSpace=True, translation=True))

            if i == self.numJoints-1 or i == 0:
                cmds.xform(ctrl_handle['preTransform'], worldSpace=True, rotation=cmds.xform(joints[i], query=True, worldSpace=True, rotation=True))
            mfunc.lockHideChannelAttrs(ctrl_handle['transform'], 't', 's', keyable=False, lock=True)
            mfunc.lockHideChannelAttrs(ctrl_handle['transform'], 'v', visible=False)
            cmds.setAttr(ctrl_handle['shape']+'.localScaleX', shapeRadius)
            cmds.setAttr(ctrl_handle['shape']+'.localScaleY', shapeRadius)
            cmds.setAttr(ctrl_handle['shape']+'.localScaleZ', shapeRadius)
            cmds.setAttr(ctrl_handle['shape']+'.drawStyle', 5)
            r_fk_handles.append(ctrl_handle)

        for i, j in zip(range(self.numJoints-3, -1, -1), range(1, self.numJoints-1)):
            cmds.xform(r_fk_handles[j]['preTransform'], worldSpace=True, rotation=\
                       cmds.xform(joints[i], query=True, worldSpace=True, rotation=True))
        
        # Parent the controls.
        for i in range(self.numJoints):
            if i > 0:
                cmds.parent(r_fk_handles[i]['preTransform'], r_fk_handles[i-1]['transform'], absolute=True)
        cmds.parent(r_fk_handles[0]['preTransform'], self.ctrlGrp, absolute=True)

        # Create a parent switch group for the reverse FK control.
        self.createParentSwitchGrpForTransform(ctrl=r_fk_handles[0]['transform'], 
                                               pivot=r_fk_handles[0]['preTransform'], constrainToRootCtrl=True, 
                                               weight=1, connectScaleWithRootCtrl=True)            

        # Constrain the joint layer to the reverse FK handles.
        for i, j in zip(range(self.numJoints), range(self.numJoints-1, -1, -1)):
            mfunc.parentConstraint(r_fk_handles[i]['transform'], joints[j], maintainOffset=True)

        # Add the root control for the joint layer.
        root_cntl = objects.load_xhandleShape(self.namePrefix+'_main_CNTL', colour=self.controlColour)
        cmds.xform(root_cntl['preTransform'], worldSpace=True, translation=\
                   cmds.xform(r_fk_handles[-1]['transform'], query=True, worldSpace=True, translation=True))
        cmds.parent(root_cntl['preTransform'], self.ctrlGrp, absolute=True)
        mfunc.lockHideChannelAttrs(root_cntl['transform'], 's', keyable=False, lock=True)
        mfunc.lockHideChannelAttrs(root_cntl['transform'], 'v', visible=False)
        cmds.setAttr(root_cntl['shape']+'.localScaleX', shapeRadius*2)
        cmds.setAttr(root_cntl['shape']+'.localScaleY', shapeRadius*2)
        cmds.setAttr(root_cntl['shape']+'.localScaleZ', shapeRadius*2)
        cmds.setAttr(root_cntl['shape']+'.drawStyle', 3)

        # Create a parent switch group for the root control.
        self.createParentSwitchGrpForTransform(root_cntl['transform'], constrainToRootCtrl=True, 
                                                               weight=1, connectScaleWithRootCtrl=True)

        # Constrain the parent group for the root FK control joint to the root control.
        mfunc.parentConstraint(root_cntl['transform'], r_fk_handles[0]['preTransform'], maintainOffset=True)

        # Add the joint layer nodes to the control rig container.
        mfunc.addNodesToContainer(self.ctrl_container, self.collectedNodes, includeHierarchyBelow=True)
        
        # Publish the reverse FK control attributes.
        for handle in r_fk_handles:
            handleName = self.getCtrlNiceNameForPublish(handle['transform'])
            cmds.container(self.ctrl_container, edit=True, publishAndBind=[handle['transform']+'.rotate', handleName+'_rotate'])

        # Publish the root control attributes.
        handleName = self.getCtrlNiceNameForPublish(root_cntl['transform'])
        cmds.container(self.ctrl_container, edit=True, publishAndBind=\
                       [root_cntl['transform']+'.translate', handleName+'_translate'])
        cmds.container(self.ctrl_container, edit=True, publishAndBind=\
                       [root_cntl['transform']+'.rotate', handleName+'_rotate'])

        # Create a custom keyable attribute on the character root transform by the control name to adjust the weight
        # of the driver joint layer by using the method "createCtrlRigWeightAttributeOnRootTransform".
        all_controls = [root_cntl['transform']] + [item['transform'] for item in r_fk_handles]
        self.createCtrlRigWeightAttributeOnRootTransform(self.namePrefix, all_controls)
        cmds.select(clear=True)


    def applyReverse_Spine_FK_Stretchy(self):

        '''This control rigging method is same as 'Reverse_Spine_FK' with scalable FK controls.'''

        # Here we'll create a single joint layer driven by a hierarchy of transforms in reverse order.

        # Create the joint layer.
        jointSet, driver_constraints, layerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                                 self.ctrlRigName,
                                                                                                 self.characterName,
                                                                                                 False,
                                                                                                 'None',
                                                                                                 True,
                                                                                                 False)
        # Collect it to be added to the control rig container.
        self.collectedNodes.extend(jointSet)        

        # Create a list with names of the joints in the joint layer in reverse order.
        joints = [layerRootJoint]
        joints.extend(jointSet[-1:1:-1])
        joints.append(jointSet[1])

        # Update the instance attribute for the driver joint layer set.
        self.driverJointLayerSet = jointSet

        # Update the instance attribute to contain the driver constraints for the joint hiearachy.
        self.driverConstraintsForInput = driver_constraints

        # Create a control group node to place all DAG nodes (not part of the character joint hierarchy) under it.
        self.createCtrlGrp()
        
        # Collect it to be added to the control rig container.
        self.collectedNodes.append(self.ctrlGrp)

        # Calculate the size of shape for the FK control.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.35

        # Create and position the reverse FK control handles.
        r_fk_handles = []
        for i in range(self.numJoints-1, -1, -1):
            if i == self.numJoints-1:
                ctrl_handle = objects.load_xhandleShape(self.namePrefix+'_root_CNTL', colour=self.controlColour)
            elif i == 0:
                ctrl_handle = objects.load_xhandleShape(self.namePrefix+'_end_CNTL', colour=self.controlColour)
            else:
                ctrl_handle = objects.load_xhandleShape(self.namePrefix+'_%s_CNTL' % i, colour=self.controlColour)

            cmds.xform(ctrl_handle['preTransform'], worldSpace=True, translation=\
                       cmds.xform(joints[i], query=True, worldSpace=True, translation=True))

            if i == self.numJoints-1 or i == 0:
                cmds.xform(ctrl_handle['preTransform'], worldSpace=True, rotation=cmds.xform(joints[i], query=True, worldSpace=True, rotation=True))
            mfunc.lockHideChannelAttrs(ctrl_handle['transform'], 't', keyable=False, lock=True)
            mfunc.lockHideChannelAttrs(ctrl_handle['transform'], 'v', visible=False)
            cmds.setAttr(ctrl_handle['shape']+'.localScaleX', shapeRadius)
            cmds.setAttr(ctrl_handle['shape']+'.localScaleY', shapeRadius)
            cmds.setAttr(ctrl_handle['shape']+'.localScaleZ', shapeRadius)
            cmds.setAttr(ctrl_handle['shape']+'.drawStyle', 5)
            r_fk_handles.append(ctrl_handle)

        for i, j in zip(range(self.numJoints-3, -1, -1), range(1, self.numJoints-1)):
            cmds.xform(r_fk_handles[j]['preTransform'], worldSpace=True, rotation=\
                       cmds.xform(joints[i], query=True, worldSpace=True, rotation=True))
        
        # Parent the controls.
        for i in range(self.numJoints):
            if i > 0:
                cmds.parent(r_fk_handles[i]['preTransform'], r_fk_handles[i-1]['transform'], absolute=True)
        cmds.parent(r_fk_handles[0]['preTransform'], self.ctrlGrp, absolute=True)

        # Create a parent switch group for the reverse FK control.
        self.createParentSwitchGrpForTransform(ctrl=r_fk_handles[0]['transform'], 
                                               pivot=r_fk_handles[0]['preTransform'], constrainToRootCtrl=True, 
                                               weight=1, connectScaleWithRootCtrl=True)         
        
        # Constrain the joint layer to the reverse FK handles.
        for i, j in zip(range(self.numJoints), range(self.numJoints-1, -1, -1)):
            mfunc.parentConstraint(r_fk_handles[i]['transform'], joints[j], maintainOffset=True)

        # Add the root control for the joint layer.
        root_cntl = objects.load_xhandleShape(self.namePrefix+'_main_CNTL', colour=self.controlColour)
        cmds.xform(root_cntl['preTransform'], worldSpace=True, translation=\
                   cmds.xform(r_fk_handles[-1]['transform'], query=True, worldSpace=True, translation=True))
        cmds.parent(root_cntl['preTransform'], self.ctrlGrp, absolute=True)
        mfunc.lockHideChannelAttrs(root_cntl['transform'], 's', keyable=False, lock=True)
        mfunc.lockHideChannelAttrs(root_cntl['transform'], 'v', visible=False)
        cmds.setAttr(root_cntl['shape']+'.localScaleX', shapeRadius*2)
        cmds.setAttr(root_cntl['shape']+'.localScaleY', shapeRadius*2)
        cmds.setAttr(root_cntl['shape']+'.localScaleZ', shapeRadius*2)
        cmds.setAttr(root_cntl['shape']+'.drawStyle', 3)

        # Create a parent switch group for the root control.
        self.createParentSwitchGrpForTransform(root_cntl['transform'], constrainToRootCtrl=True, 
                                                               weight=1, connectScaleWithRootCtrl=True)
        
        # Constrain the parent group for the root FK control joint to the root translation control.
        mfunc.parentConstraint(root_cntl['transform'], r_fk_handles[0]['preTransform'], maintainOffset=True)

        # Add the joint layer nodes to the control rig container.
        mfunc.addNodesToContainer(self.ctrl_container, self.collectedNodes, includeHierarchyBelow=True)
        
        # Publish the reverse FK control attributes.
        for handle in r_fk_handles:
            handleName = self.getCtrlNiceNameForPublish(handle['transform'])
            cmds.container(self.ctrl_container, edit=True, publishAndBind=[handle['transform']+'.rotate', handleName+'_rotate'])
            cmds.container(self.ctrl_container, edit=True, publishAndBind=[handle['transform']+'.scale', handleName+'_scale'])

        # Publish the root control attributes.
        handleName = self.getCtrlNiceNameForPublish(root_cntl['transform'])
        cmds.container(self.ctrl_container, edit=True, publishAndBind=\
                       [root_cntl['transform']+'.translate', handleName+'_translate'])
        cmds.container(self.ctrl_container, edit=True, publishAndBind=\
                               [root_cntl['transform']+'.rotate', handleName+'_rotate'])

        # Create a custom keyable attribute on the character root transform by the control name to adjust the weight
        # of the driver joint layer by using the method "createCtrlRigWeightAttributeOnRootTransform".
        all_controls = [root_cntl['transform']] + [item['transform'] for item in r_fk_handles]
        self.createCtrlRigWeightAttributeOnRootTransform(self.namePrefix, all_controls)
        cmds.select(clear=True)


    def applyAuto_Spline(self):

        '''This is an alternative implementation for a IK/FK spine control, without using a splineIK solver. This
        implementation responds better to stretch (without over-shooting the end joint position), has better axial twist
        as opposed to limitations of advanced twist in splineIK, while providing a familiar control interface 
        for an animator.'''

        # Create a control group node to place all DAG nodes (not part of the character joint hierarchy) under it.
        self.createCtrlGrp()
        
        # Collect it to be added to the control rig container.
        self.collectedNodes.append(self.ctrlGrp)        

        # Create the driver layer joints, collect them and add to the control container.
        defJointSet, driver_constraints, defLayerRootJoint = \
            mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy, self.ctrlRigName, self.characterName, \
                                                      False, 'None', True)
        defJoints = [defLayerRootJoint]
        defJoints.extend(defJointSet[-1:1:-1])
        defJoints.append(defJointSet[1])
        
        # Collect it to be added to the control rig container.
        self.collectedNodes.extend(defJointSet)        

        # Update the instance attribute for the driver joint layer set.
        self.driverJointLayerSet = defJointSet

        # Update the instance attribute to contain the driver constraints for the joint hiearachy.
        self.driverConstraintsForInput = driver_constraints

        # Define the number of translation controls for the spine (min 4, it's better to keep it this way).
        numCtls = 4

        # Create the FK Control joints based on 'numCtls'.
        jointRadius = cmds.getAttr(self.rootJoint+'.radius')
        ctlJoints = []
        for i in range(numCtls):
            if i == 0:
                jointName = cmds.joint(name=self.namePrefix+'_root_fk_CNTL', radius=jointRadius)
            elif i == (numCtls-1):
                jointName = cmds.joint(name=self.namePrefix+'_end_fk_CNTL', radius=jointRadius)
            else:
                jointName = cmds.joint(name=self.namePrefix+'_%s_fk_CNTL' % i, radius=jointRadius)
            cmds.setAttr(jointName+'.radius', keyable=False, channelBox=False)
            cmds.setAttr(jointName+'.visibility', keyable=False)
            cmds.setAttr(jointName+'.drawStyle', 2)
            cmds.select(clear=True)
            ctlJoints.append(jointName)
        
        self.collectedNodes.extend(ctlJoints)

        # Create and assign the shapes for FK control joints.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.35
        for i in range(numCtls):
            fk_ctrl = objects.load_xhandleShape(ctlJoints[i], colour=self.controlColour, transformOnly=True)
            cmds.setAttr(fk_ctrl['shape']+'.localScaleX', shapeRadius*1.0)
            cmds.setAttr(fk_ctrl['shape']+'.localScaleY', shapeRadius*1.0)
            cmds.setAttr(fk_ctrl['shape']+'.localScaleZ', shapeRadius*1.0)
            cmds.setAttr(fk_ctrl['shape']+'.drawStyle', 5)

        # Collect the world space positions of the spine joints in a list, starting from the root.
        curveCVposString = '['
        jointIt = self.rootJoint
        while jointIt:
            pos = cmds.xform(jointIt, query=True, worldSpace=True, translation=True)
            curveCVposString += str(tuple(pos))+','
            jointIt = cmds.listRelatives(jointIt, children=True, type='joint')
        curveCVposString = curveCVposString[:-1] + ']'
        curveCVposList = eval(curveCVposString)

        # Create a temporary curve along the spine to position the FK control layers by using pocinfo.
        tempCurve = cmds.curve(degree=1, point=curveCVposList)
        tempCurveShape = cmds.listRelatives(tempCurve, children=True, type='nurbsCurve')[0]
        cmds.rebuildCurve(tempCurve, constructionHistory=False, replaceOriginal=True, rebuildType=0, degree=1, \
                          endKnots=True, keepEndPoints=True, keepRange=0, keepControlPoints=True, keepTangents=True, \
                          spans=cmds.getAttr(tempCurve+'.spans'), tolerance=0.01)
        u_offset_mult = (1.0/(numCtls-1))
        tempPointOnCurveInfoNodes = []
        for i, joint in zip(range(numCtls), ctlJoints):
            tempPointOnCurveInfo = cmds.createNode('pointOnCurveInfo', skipSelect=True)
            cmds.connectAttr(tempCurveShape+'.worldSpace[0]', tempPointOnCurveInfo+'.inputCurve')
            cmds.setAttr(tempPointOnCurveInfo+'.parameter', u_offset_mult*i)
            jointPos = cmds.getAttr(tempPointOnCurveInfo+'.position')[0]
            cmds.setAttr(joint+'.translate', *jointPos, type='double3')
            tempPointOnCurveInfoNodes.append(tempPointOnCurveInfo)
            
        mfunc.updateNodeList([tempCurve])
        cmds.delete(tempPointOnCurveInfoNodes)
        cmds.delete(tempCurve)

        # If the spline joints have local orientation, orient the FK control joints as well.
        # Use the "splineOrientation" attribute on the root joint. This originated from the "node orientation type"
        # attribute from its spline module state. It's an enum attribute with 0 as 'world' and 1 as 'local'.
        if cmds.getAttr(self.rootJoint+'.splineOrientation') == '1':
            nodeAxes = cmds.getAttr(self.rootJoint+'.nodeAxes')     # Originated from module state, see node axes for module creation. 
            onPlane = cmds.getAttr(self.rootJoint+'.plane')     # Originated from module state, see creation plane for module creation. 
            
            # Get the axes to be used for orientation.
            aimVector = {'X':[1.0, 0.0, 0.0], 'Y':[0.0, 1.0, 0.0], 'Z':[0.0, 0.0, 1.0]}[nodeAxes[0]]
            upVector = {'X':[1.0, 0.0, 0.0], 'Y':[0.0, 1.0, 0.0], 'Z':[0.0, 0.0, 1.0]}[nodeAxes[1]]
            worldUpVector = {'XY':[0.0, 0.0, 1.0], 'YZ':[1.0, 0.0, 0.0], 'XZ':[0.0, 1.0, 0.0]}[onPlane[1:]]
            
            # If the originating module for current spline joint hierarchy was created on the -ve side of the creation plane,
            # modify the aim vector for orientation accordingly.
            if onPlane[0] == '-':
                rotationFunction = cmds.getAttr(self.rootJoint+'.rotationFunction')
                if rotationFunction == 'behaviour':
                    aimVector = [item*-1 for item in aimVector]
            
            # Orient the root and end fk control joints (They're separate from main driver joints).
            cmds.parent(ctlJoints[0], self.rootJoint, absolute=True)    
            cmds.setAttr(ctlJoints[0]+'.jointOrient', 0, 0, 0, type='double3')
            cmds.parent(ctlJoints[0], world=True, absolute=True)
            
            cmds.parent(ctlJoints[-1], self.selCharacterHierarchy[0], absolute=True)    # First item in self.selCharacterHierarchy is the *end_node_joint.
            cmds.setAttr(ctlJoints[-1]+'.jointOrient', 0, 0, 0, type='double3')
            cmds.parent(ctlJoints[-1], world=True, absolute=True)
            
            ##target = cmds.spaceLocator(absolute=True, position=cmds.xform(self.selCharacterHierarchy[0], query=True, \
                                                                          ##worldSpace=True, translation=True))[0]
            for i in range(1, 3):
                ##tempConstraint = cmds.aimConstraint(ctlJoints[i+1], ctlJoints[i], aimVector=aimVector, upVector=upVector,
                ##worldUpVector=worldUpVector, name=ctlJoints[i]+'_aimConstraint')
                tempConstraint = cmds.aimConstraint(ctlJoints[i+1], ctlJoints[i], aimVector=aimVector, upVector=upVector, \
                                                    worldUpVector=worldUpVector)
                cmds.delete(tempConstraint)
                cmds.makeIdentity(ctlJoints[i], rotate=True, apply=True)
            ##cmds.delete(target)

        # Parent the FK control joints.
        for i, joint in enumerate(ctlJoints[1:]):
            cmds.parent(joint, ctlJoints[i], absolute=True)

        # Place the FK control root, under the 'constrained' parent root joint of the joint hierarchy.
        constrainedHierarchyRoot = cmds.listRelatives(defLayerRootJoint, parent=True, type='joint')[0]
        cmds.parent(ctlJoints[0], constrainedHierarchyRoot, absolute=True)

        # Create a parent switch group for the FK root control.
        fk_ps_grp = self.createParentSwitchGrpForTransform(ctlJoints[0])
        
        # Create a pre-transform for the root FK control.
        rootFKPreTransform = cmds.group(empty=True, parent=fk_ps_grp, name=ctlJoints[0].replace('_CNTL', '_preTransform'))
        mfunc.align(ctlJoints[0], rootFKPreTransform)
        cmds.parent(ctlJoints[0], rootFKPreTransform, absolute=True)
        
        # Lock the translation channels for the FK control joints, add control rig display layer visibility.
        for joint in ctlJoints:
            mfunc.lockHideChannelAttrs(joint, 't', keyable=False, lock=True)
            cmds.setAttr(joint+'.overrideEnabled', 1)
            cmds.setAttr(joint+'.overrideColor', self.controlColour)
            cmds.connectAttr(self.controlRigDisplayLayer + '.visibility', joint+'.overrideVisibility')

        # Add the root control for the joint layer.
        root_cntl = objects.load_xhandleShape(self.namePrefix+'_main_CNTL', colour=self.controlColour)
        cmds.xform(root_cntl['preTransform'], worldSpace=True, translation=\
                   cmds.xform(ctlJoints[0], query=True, worldSpace=True, translation=True))
        cmds.parent(root_cntl['preTransform'], self.ctrlGrp, absolute=True)
        mfunc.lockHideChannelAttrs(root_cntl['transform'], 's', keyable=False, lock=True)
        mfunc.lockHideChannelAttrs(root_cntl['transform'], 'v', visible=False)
        cmds.setAttr(root_cntl['shape']+'.localScaleX', shapeRadius*3)
        cmds.setAttr(root_cntl['shape']+'.localScaleY', shapeRadius*3)
        cmds.setAttr(root_cntl['shape']+'.localScaleZ', shapeRadius*3)
        cmds.setAttr(root_cntl['shape']+'.drawStyle', 3)

        # Create a parent switch group for the root control handle.
        self.createParentSwitchGrpForTransform(root_cntl['transform'], constrainToRootCtrl=True, 
                                               weight=1, connectScaleWithRootCtrl=True)
        
        # Constrain the parent group for the root FK control joint to the root translation control.
        mfunc.parentConstraint(root_cntl['transform'], rootFKPreTransform, maintainOffset=True)        
        
        
        # Create and position the "guide" and "up vector" locators.
        
        # Calculate the relative translation needed to offset the up vector locators from their positions along the spine.
        
        # Get the root position of the spine.
        startJointPos = cmds.xform(ctlJoints[0], query=True, worldSpace=True, translation=True)
        
        # Get the end/tip position of the spine.
        endJointPos = cmds.xform(ctlJoints[-1], query=True, worldSpace=True, translation=True)
        
        # Get the tip->root vector.
        spine_direction_vec = map(lambda x,y:x-y, endJointPos, startJointPos)
        
        # Get its magnitude.
        spine_direction_vec_magnitude = math.sqrt(reduce(lambda x,y: x+y, [component**2 for component in spine_direction_vec]))
        
        # Get the offset length needed to displace the up vector locator positions.
        off_val = spine_direction_vec_magnitude / float(numCtls)
        
        # The "spine_direction_vec" is a relative vector, and using that, we need to calculate the offset translation
        # vector (relative) to re-position the up vector locators. Between the spine root and end positions, find the 
        # world axis value which has minimum translation, and that axis will be used to create the offset translation vector
        # to re-position the up vector locators towards the side of the spine.
        # The idea is not to create an offset translation along the spine.
        off_ax_val = {abs(spine_direction_vec[0]): [off_val, 0, 0],   # X
                      abs(spine_direction_vec[1]): [0, off_val, 0],   # Y
                      abs(spine_direction_vec[2]): [0, 0, off_val]}   # Z
        
        # Now, get the offset translation vector as described above.
        off_ax = off_ax_val[min(off_ax_val)]
        
        # To store the "guide" and "up vector" locators. 
        guide_loc_list = []
        upVec_loc_list = []
        
        # Now create the "guide" and "up vector" locators along the control positions.
        for i in range(numCtls):
            
            # Create the "guide" locator, to be placed along the spine.
            if i == 0:
                g_locName = cmds.spaceLocator(name='%s_splineGuide_root_loc' % self.namePrefix)[0]
            elif i == (numCtls-1):
                g_locName = cmds.spaceLocator(name='%s_splineGuide_end_loc' % self.namePrefix)[0]
            else:
                g_locName = cmds.spaceLocator(name='%s_splineGuide_%s_loc' % (self.namePrefix, i))[0]
                
            guide_loc_list.append(g_locName)
            cmds.setAttr(g_locName+'.visibility', 0)
            
            # Position it.
            cmds.xform(g_locName, worldSpace=True, translation=\
                       cmds.xform(ctlJoints[i], query=True, worldSpace=True, translation=True), rotation=\
                       cmds.xform(ctlJoints[i], query=True, worldSpace=True, rotation=True))
            cmds.parent(g_locName, self.ctrlGrp, absolute=True)
            
            # Create the "up vector" locator, to be placed towards the side of the spine.
            if i == 0:
                u_locName = cmds.spaceLocator(name='%s_splineUpVec_root_loc' % self.namePrefix)[0]
            elif i == (numCtls-1):
                u_locName = cmds.spaceLocator(name='%s_splineUpVec_end_loc' % self.namePrefix)[0]
            else:
                u_locName = cmds.spaceLocator(name='%s_splineUpVec_%s_loc' % (self.namePrefix, i))[0]
                
            cmds.setAttr(u_locName+'.visibility', 0)
            upVec_loc_list.append(u_locName)
            
            # First position it.
            cmds.xform(u_locName, worldSpace=True, translation=\
                       cmds.xform(ctlJoints[i], query=True, worldSpace=True, translation=True), rotation=\
                       cmds.xform(ctlJoints[i], query=True, worldSpace=True, rotation=True))
            cmds.parent(u_locName, self.ctrlGrp, absolute=True)
            
            # Now offset it to the side of the spine.
            cmds.move(off_ax[0], off_ax[1], off_ax[2], u_locName, relative=True, localSpace=True, worldSpaceDistance=True)
            
            # Constrain the up vector locator to the guide locator. 
            mfunc.parentConstraint(g_locName, u_locName, maintainOffset=True)
            
            # Scale constrain the up vector locator to the guide locator. 
            mfunc.scaleConstraint(g_locName, u_locName, maintainOffset=True)


        # Create the 'driver' and the 'up' curve for the spline controls.
        
        # Collect the world space positions of the spline controls in a list, starting from the root control.
        # This list will be used to create the 'driver' and the 'up' curves.
        curveCVposString = '['
        jointIt = ctlJoints[0]
        while jointIt:
            pos = cmds.xform(jointIt, query=True, worldSpace=True, translation=True)
            curveCVposString += str(tuple(pos))+','
            jointIt = cmds.listRelatives(jointIt, children=True, type='joint')
        curveCVposString = curveCVposString[:-1] + ']'
        curveCVposList = eval(curveCVposString)
        
        # Now create the 'driver' curve.
        driverCurve = cmds.curve(degree=2, point=curveCVposList)
        driverCurve = cmds.rename(driverCurve, self.namePrefix + '_driverCurve')
        cmds.setAttr(driverCurve+'.visibility', 0)
        cmds.parent(driverCurve, self.ctrlGrp, absolute=True)
        
        # Create the 'up' curve.
        upVecCurve = cmds.duplicate(driverCurve, returnRootsOnly=True, name=self.namePrefix + '_upVectorCurve')[0]

        # Connect the 'driver' and the 'up' curves to the guide and up vector locators.
        for i in range(numCtls):
            cmds.connectAttr(guide_loc_list[i]+'Shape.worldPosition[0]', driverCurve+'Shape.controlPoints['+str(i)+']')
            cmds.connectAttr(upVec_loc_list[i]+'Shape.worldPosition[0]', upVecCurve+'Shape.controlPoints['+str(i)+']')


        # Create the 'IK style' translation control handles.
        
        # Create the control group.
        ikCtlGrp = cmds.group(empty=True, name=self.namePrefix+'_ik_cntls_grp', parent=self.ctrlGrp)
        cmds.connectAttr(self.globalScaleAttr, ikCtlGrp+'.scaleX')
        cmds.connectAttr(self.globalScaleAttr, ikCtlGrp+'.scaleY')
        cmds.connectAttr(self.globalScaleAttr, ikCtlGrp+'.scaleZ')
        
        # Now create the control handles.
        ik_controls = []
        
        for i in range(numCtls):
            
            # Get the control colour.
            colour = self.controlColour + 2
            if self.controlColour > 29:
                colour = self.controlColour - 2
            
            # Create the control handles.
            if i == 0:
                ik_ctrl = objects.load_xhandleShape(self.namePrefix+'_root_ik_CNTL', colour=colour, transformOnly=True)
                cmds.setAttr(ik_ctrl['shape']+'.localScaleX', shapeRadius*2.0)
                cmds.setAttr(ik_ctrl['shape']+'.localScaleY', shapeRadius*2.0)
                cmds.setAttr(ik_ctrl['shape']+'.localScaleZ', shapeRadius*2.0)
            elif i == (numCtls-1):
                ik_ctrl = objects.load_xhandleShape(self.namePrefix+'_end_ik_CNTL', colour=colour, transformOnly=True)
                cmds.setAttr(ik_ctrl['shape']+'.localScaleX', shapeRadius*1.7)
                cmds.setAttr(ik_ctrl['shape']+'.localScaleY', shapeRadius*1.7)
                cmds.setAttr(ik_ctrl['shape']+'.localScaleZ', shapeRadius*1.7)
            else:
                ik_ctrl = objects.load_xhandleShape(self.namePrefix+'_%s_ik_CNTL' % i, colour=colour, transformOnly=True)
                cmds.setAttr(ik_ctrl['shape']+'.localScaleX', shapeRadius*1.7)
                cmds.setAttr(ik_ctrl['shape']+'.localScaleY', shapeRadius*1.7)
                cmds.setAttr(ik_ctrl['shape']+'.localScaleZ', shapeRadius*1.7)

            cmds.setAttr(ik_ctrl['shape']+'.drawStyle', 3)
            cmds.setAttr(ik_ctrl['shape']+'.wireframeThickness', 2)
            cmds.setAttr(ik_ctrl['transform']+'.overrideEnabled', 1)
            cmds.connectAttr(self.controlRigDisplayLayer + '.visibility', ik_ctrl['transform']+'.overrideVisibility')
            
            # Pre-transform each ik_CNTL handle separately in this case and orient it accordingly.
            ikHandleOriGrp = cmds.group(empty=True, name=ik_ctrl['transform']+'_transOriGrp')
            if self.transOriFunc == 'local_orientation':
                cmds.xform(ikHandleOriGrp, worldSpace=True, 
                           translation=cmds.xform(ctlJoints[i], query=True, worldSpace=True, translation=True), 
                           rotation=cmds.xform(ctlJoints[i], query=True, worldSpace=True, rotation=True))
            if self.transOriFunc == 'world':
                cmds.xform(ikHandleOriGrp, worldSpace=True, 
                           translation=cmds.xform(ctlJoints[i], query=True, worldSpace=True, translation=True))
                
            cmds.parent(ik_ctrl['transform'], ikHandleOriGrp, relative=True)
            cmds.parent(ikHandleOriGrp, ikCtlGrp, absolute=True)
            mfunc.lockHideChannelAttrs(ik_ctrl['transform'], 'r', 's', keyable=False, lock=True)
            mfunc.lockHideChannelAttrs(ik_ctrl['transform'], 'v', visible=False)
            
            # Constrain the guide locators.
            mfunc.parentConstraint(ik_ctrl['transform'], guide_loc_list[i], maintainOffset=True)
            mfunc.scaleConstraint(ik_ctrl['transform'], guide_loc_list[i], maintainOffset=True)
            
            # Constrain the ik control pre-transform with the spline FK controls.
            mfunc.parentConstraint(ctlJoints[i], ikHandleOriGrp, maintainOffset=True)
            
            ik_controls.append(ik_ctrl['transform'])
            
        cmds.select(clear=True)

        # Create the control joint layer (indirect, since it'll be driven by the curve, "driverCurve"), where each joint will
        # be unparented and drive the main joint layer using constraints (notice the connectLayer argument is False).
        crvJointSet, null, crvRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                    self.ctrlRigName+'_crv',
                                                                                    self.characterName,
                                                                                    False,
                                                                                    'None',
                                                                                    False,
                                                                                    None,
                                                                                    False)
        # No driver constraints are returned here, therefore, 'null'.
        
        # Collect it to be added to the control rig container.
        self.collectedNodes.extend(crvJointSet)
        
        # Unparent each joint in this layer.
        for joint in crvJointSet:
            cmds.parent(joint, self.ctrlGrp, absolute=True)

        # The control joints will be driven by the 'driver' curve by constraining to it using motionPath for translation,
        # and then their orientation will be guided by offsetted locators on an 'up' vector curve using constraints.
        crvJoints = [crvRootJoint]
        crvJoints.extend(crvJointSet[-1:1:-1])
        crvJoints.append(crvJointSet[1])
        
        # Calculate the u-parameter offset needed to attach the joint(s) in this layer to the "driverCurve".
        u_offset_mult = (1.0/(self.numJoints-1))
        
        for i in range(self.numJoints):

            # Attach each joint to the driver curve, using motion path.
            cmds.select([crvJoints[i], driverCurve])
            mp_node = cmds.pathAnimation(fractionMode=True, follow=False)
            
            # Remove the motionPath keys.
            mel.eval('cutKey -t ":" -cl -f ":" -at "u" '+mp_node+';')
            
            # Apply the u-parameter to attach at the desired position on the curve.
            cmds.getAttr(mp_node+'.uValue')
            cmds.setAttr(mp_node+'.uValue', i*u_offset_mult)
            
            # Rename the motion path nodes and collect them to be added to the control rig container.
            mp_connections = cmds.listConnections(crvJoints[i], destination=True, type='addDoubleLinear')
            mp_connections = list(set(mp_connections))
            mp_node = cmds.rename(mp_node, crvJoints[i]+'_motionPathNode')
            self.collectedNodes.append(mp_node)
            
            for j, node in enumerate(mp_connections):
                name = cmds.rename(node, '%s_translateAdjust_%s_addDoubleLinear'%(crvJoints[i].replace('_joint', ''), j+1))
                self.collectedNodes.append(name)
            
            # Create world up locators to be attached to the 'up' curve. This will drive the twist rotation for the 
            # joints in the 'crvJoint' layer by using the locators as the world up objects.
            if i == 0:
                u_crv_locName = cmds.spaceLocator(name='%s_curveUpVec_root_loc' % self.namePrefix)[0]
            elif i == (self.numJoints-1):
                u_crv_locName = cmds.spaceLocator(name='%s_curveUpVec_end_loc' % self.namePrefix)[0]
            else:
                u_crv_locName = cmds.spaceLocator(name='%s_curveUpVec_%s_loc' % (self.namePrefix, i))[0]
                
            cmds.setAttr(u_crv_locName+'.localScale', 0.25, 0.25, 0.25, type='double3')
            cmds.setAttr(u_crv_locName+'.visibility', 0)
            cmds.parent(u_crv_locName, self.ctrlGrp, absolute=True)
            
            # Now attach the world up locators to the 'up' curve using motion path.
            cmds.select([u_crv_locName, upVecCurve])
            mp_node = cmds.pathAnimation(fractionMode=True, follow=False)
            mel.eval('cutKey -t ":" -cl -f ":" -at "u" '+mp_node+';')
            cmds.getAttr(mp_node+'.uValue')
            cmds.setAttr(mp_node+'.uValue', i*u_offset_mult)
            
            # Rename the motion path nodes and collect them to be added to the control rig container.
            mp_connections = cmds.listConnections(u_crv_locName, destination=True, type='addDoubleLinear')
            mp_connections = list(set(mp_connections))
            mp_node = cmds.rename(mp_node, u_crv_locName+'_motionPathNode')
            self.collectedNodes.append(mp_node)

            for j, node in enumerate(mp_connections):
                name = cmds.rename(node, '%s_translateAdjust_%s_addDoubleLinear' % (u_crv_locName, j))
                self.collectedNodes.append(name)
            
            # Drive the orientation of each joint in 'crvJoint' layer by aiming it to the next joint.
            # Use the world up locators as the world up objects.
            if i > 0:
                nodeAxes = cmds.getAttr(self.rootJoint+'.nodeAxes')  # Originated from spline module state, see node axes for module creation. 
                onPlane = cmds.getAttr(self.rootJoint+'.plane')     # Originated from spline module state, see creation plane for module creation.
                
                # Get the aim and up vector axes for aim orientation.
                aimVector={'X':[1.0, 0.0, 0.0], 'Y':[0.0, 1.0, 0.0], 'Z':[0.0, 0.0, 1.0]}[nodeAxes[0]]
                upVector = {'X':[1.0, 0.0, 0.0], 'Y':[0.0, 1.0, 0.0], 'Z':[0.0, 0.0, 1.0]}[nodeAxes[1]]
                
                # If the originating module for current spline joint hierarchy was created on the -ve side of the creation plane,
                # modify the aim vector for orientation accordingly.                
                if onPlane[0] == '-':
                    rotationFunction = cmds.getAttr(self.rootJoint+'.rotationFunction')
                    if rotationFunction == 'behaviour':
                        aimVector = [item*-1 for item in aimVector]
                
                aimConstraint = mfunc.aimConstraint(crvJoints[i], crvJoints[i-1], maintainOffset=True, aimVector=aimVector,
                                                   upVector=upVector, worldUpType='object', worldUpObject=u_crv_locName)
            
            # Constrain the last crvJoint with the last FK control joint.
            if i == self.numJoints-1:
                mfunc.orientConstraint(ctlJoints[-1], crvJoints[i], maintainOffset=True)
            
            # Now constrain the driver layer joints with the crvJoint layer.
            mfunc.parentConstraint(crvJoints[i], defJoints[i], maintainOffset=True)

            # This could be done, but only if the fk control joints equal the number of hierarchy joints; it is not
            # completely necessary. If done, you'd have to create a switch for toggling stretch.
            ##mfunc.parentConstraint(ctlJoints[i], defJoints[i], maintainOffset=True)##

            cmds.select(clear=True)

        # Add all the control rig nodes to the container and publish attributes.
        mfunc.addNodesToContainer(self.ctrl_container, self.collectedNodes, includeHierarchyBelow=True)
        
        mfunc.updateContainerNodes(self.ctrl_container)
        
        for i in range(len(ctlJoints)):
            transformName = self.getCtrlNiceNameForPublish(ctlJoints[i])
            if i == 0:
                cmds.container(self.ctrl_container, edit=True, publishAndBind=\
                               [ctlJoints[i]+'.translate', transformName+'_translate'])
            cmds.container(self.ctrl_container, edit=True, publishAndBind=[ctlJoints[i]+'.rotate', transformName+'_rotate'])
            cmds.container(self.ctrl_container, edit=True, publishAndBind=[ctlJoints[i]+'.scale', transformName+'_scale'])
            
        for cntl in ik_controls:
            cntlName = self.getCtrlNiceNameForPublish(cntl)
            cmds.container(self.ctrl_container, edit=True, publishAndBind=[cntl+'.translate', cntlName+'_translate'])

        # Create a custom keyable attribute on the character root transform by the control name to adjust the weight
        # of the driver joint layer by using the method "createCtrlRigWeightAttributeOnRootTransform".
        self.createCtrlRigWeightAttributeOnRootTransform(self.namePrefix, \
                                                         ctlJoints+ik_controls+[root_cntl['transform']])


## End of file. Do not add any newline or line breaks after this >>