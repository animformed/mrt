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
import re, math, os

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


    def __init__(self, characterName, rootJoint):

        '''Initializing instance attributes for use in all methods to be defined.'''

        # Get the user-defined name for the character.
        self.characterName = characterName

        # Get the user-defined for the selected joint hierarchy on which control is to be applied.
        self.userSpecName = re.split('_root_node_transform', rootJoint)[0].partition('__')[2]

        # Get the name of the root transform control (Large red-blue coloured cross-shaped control).
        self.ch_root_transform = 'MRT_character'+characterName+'__root_transform'

        # Get the name of the character world transform control (Large grey-coloured control curve with four arrows).
        self.ch_world_transform = 'MRT_character'+characterName+'__world_transform'

        # Get the name of the root joint of the selected hierarchy.
        self.rootJoint = rootJoint

        # Get the colour index value of the control rig colour slider from modular rigging tools window.
        self.controlColour = cmds.colorIndexSliderGrp('__MRT_controlLayerColour_IndexSliderGrp', query=True, value=True) - 1

        # Get a list of all joints in the "skinJointList" set.
        allJoints = (cmds.getAttr('MRT_character'+characterName+'__mainGrp.skinJointList')).split(',')

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

        # Create the control attribute / naming prefix.
        self.ctrlAttrPrefix = re.split('_root_node_transform', rootJoint)[0].partition('__')[2]
        self.namePrefix = rootJoint.partition('_root_node_transform')[0]

        # Reset all controls on the character to their default positions, if any.
        # This will also turn off any control weights and their visibility for the selected joint hierarchy.
        # This is to allow the new control rig on the selected hierarchy to have full control, useful for testing.
        self.resetAllControls()
        self.toggleHierarchyCtrlWeights()
        self.toggleHierarchyCtrlVisibility()

        # Force update on all joint attributes, after resetAllControls()
        for joint in allJoints:
            cmds.getAttr(joint+'.translate')
            cmds.getAttr(joint+'.rotate')
            cmds.getAttr(joint+'.scale')


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
                name = '%s_%s_Container'%(self.namePrefix, layer)
                containers.append(name)

        return containers


    def toggleAllCtrlWeights(self, value=0):

        '''This method will toggle all weights for all existing control rigs in a character by using the attributes created
        on the character root transform control.'''

        # Get the custom attributes on the character root transform.
        ctrl_attribs = cmds.listAttr(self.ch_root_transform, userDefined=True)

        # Find the attributes to toggle visibility and set them.
        if ctrl_attribs:
            for attr in ctrl_attribs[3:]:
                if not attr.endswith('visibility'):
                    cmds.setAttr('MRT_character'+self.characterName+'__root_transform'+'.'+attr, value)


    def resetAllControls(self):

        '''Resets all the control transforms to their initial positions, and removes any keys set on them.'''

        # Reset the time.
        cmds.currentTime(0)

        # Collect the character root and world transform controls, and all the control rig containers currently in the scene.
        nodes = []
        nodes.extend([item for item in cmds.ls(type='transform') \
                                    if re.match('^MRT_character%s__(world|root){1}_transform$'%(self.characterName), item)])
        nodes.extend([item for item in cmds.ls(type='container') \
                                                if re.match('^MRT_character%s__\w+_Container$'%(self.characterName), item)])
        # Iterate through the nodes, remove all keyframes, and set the channel attributes.
        for node in nodes:
            mel.eval('cutKey -t ":" '+node+';')
            ctrlAttrs = cmds.listAttr(node, keyable=True, visible=True, unlocked=True) or []
            if ctrlAttrs:
                for attr in ctrlAttrs:
                    if re.search('(translate|rotate){1}', attr):
                        cmds.setAttr(node+'.'+attr, 0)
                    if re.search('scale', attr):
                        cmds.setAttr(node+'.'+attr, 1)


    def toggleHierarchyCtrlWeights(self, value=0):

        '''Toggles the weight of all control rigs currently applied to a joint hierarchy.'''

        # Get the custom attributes on the character root transform control.
        ctrl_attribs = cmds.listAttr(self.ch_root_transform, userDefined=True)
        # Set the value of the attributes on the root transform to toggle weights for control rig layer(s).
        if ctrl_attribs:
            for attr in ctrl_attribs[3:]:
                attrUserSpec = re.split('_[A-Z]', attr)[0]
                if re.match('^%s$'%(self.userSpecName), attrUserSpec):
                    if not attr.endswith('visibility'):
                        cmds.setAttr('MRT_character'+self.characterName+'__root_transform'+'.'+attr, value)


    def toggleHierarchyCtrlVisibility(self, value=0):

        '''Toggles the visibility of all control rigs currently applied to a joint hierarchy.'''

        # Get the custom attributes on the character root transform control.
        ctrl_attribs = cmds.listAttr(self.ch_root_transform, userDefined=True)
        # Set the visibility of the controls currently applied to a joint hierarchy.
        if ctrl_attribs:
            for attr in ctrl_attribs[3:]:
                attrUserSpec = re.split('_[A-Z]', attr)[0]
                if re.match('^%s$'%(self.userSpecName), attrUserSpec):
                    if attr.endswith('visibility'):
                        cmds.setAttr('MRT_character'+self.characterName+'__root_transform'+'.'+attr, value)


    def createCtrlRigWeightAttributeOnRootTransform(self, ctrlAttr, visibility_nodes=[]):

        '''Creates a custom attribute on the character root transform for controlling the weight of a control rig layer on
        a joint hierarchy in a character. It accepts the attribute name to be created for the control rig and the list of 
        transform controls in the control rig (optional) to toggle visibility.'''

        # Add the custom attribute for the control rig layer on the character root transform control.
        cmds.addAttr(self.ch_root_transform, attributeType='float', longName=ctrlAttr, hasMinValue=True, hasMaxValue=True, \
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
                    cmds.connectAttr(self.ch_root_transform+'.'+ctrlAttr, constraint+'.'+constraintAttr)

        # If transform controls for the control rig is passed-in for toggling their visibility, create the necessary
        # attribute and connect it.
        if visibility_nodes:
            cmds.addAttr(self.ch_root_transform, attributeType='bool', longName=ctrlAttr+'_visibility', defaultValue=1, \
                                                                                                                keyable=True)
            for node in visibility_nodes:
                cmds.connectAttr(self.ch_root_transform+'.'+ctrlAttr+'_visibility', node+'.visibility')


    def createParentSwitchGrpForTransform(self, transform, constrainToRootTransform=False, weight=0, connectScaleWithRootTransform=False):

        '''Creates a parent group node (with a child pre-transform) for a given transform, so it can receive multiple
        constraints from other transforms as parents. It also creates custom attributes on the given transform to switch 
        between such parents. Optionally, you can add the character root transform as a parent, and set its weight. You can 
        also specify if the transform needs to be scaled along with the character root transform, if it is not a part of a 
        joint hierarchy in a character.'''

        # Create the group node which will receive the constraints from parent transforms.
        parentSwitch_grp = cmds.group(empty=True, name=transform + '_parentSwitch_grp')
        tempConstraint = cmds.parentConstraint(transform, parentSwitch_grp, maintainOffset=False)[0]
        cmds.delete(tempConstraint)

        # Add custom attributes to the group node, and create a child transform to contain the main transform,
        # for which the parent switch group is being created.
        cmds.addAttr(transform, attributeType='enum', longName='targetParents', enumName='None:', keyable=True)
        cmds.addAttr(parentSwitch_grp, dataType='string', longName='parentTargetList', keyable=False)
        cmds.setAttr(parentSwitch_grp+'.parentTargetList', 'None', type='string', lock=True)
        transform_grp = cmds.duplicate(parentSwitch_grp, parentOnly=True, name=transform+'_grp')[0]
        transformParent = cmds.listRelatives(transform, parent=True)
        if transformParent:
            cmds.parent(parentSwitch_grp, transformParent[0], absolute=True)
        cmds.parent(transform_grp, parentSwitch_grp, absolute=True)
        cmds.parent(transform, transform_grp, absolute=True)

        # Add the character root transform as a parent, if specified.
        if constrainToRootTransform:
            if cmds.objectType(transform, isType='joint'):
                constraint = cmds.orientConstraint(self.ch_root_transform, parentSwitch_grp, maintainOffset=True, \
                                                                                name=parentSwitch_grp+'_orientConstraint')[0]
            else:
                constraint = cmds.parentConstraint(self.ch_root_transform, parentSwitch_grp, maintainOffset=True, \
                                                                                name=parentSwitch_grp+'_parentConstraint')[0]
            cmds.addAttr(transform+'.targetParents', edit=True, enumName='None:'+self.ch_root_transform)
            parentSwitchCondition = cmds.createNode('condition', \
                                        name=transform+'_'+self.ch_root_transform+'_parentSwitch_condition', skipSelect=True)
            cmds.setAttr(parentSwitchCondition+'.firstTerm', 1)
            cmds.connectAttr(transform+'.targetParents', parentSwitchCondition+'.secondTerm')
            cmds.setAttr(parentSwitchCondition+'.colorIfTrueR', 1)
            cmds.setAttr(parentSwitchCondition+'.colorIfFalseR', 0)
            cmds.connectAttr(parentSwitchCondition+'.outColorR', constraint+'.'+self.ch_root_transform+'W0')
            if weight == 1:
                cmds.setAttr(transform+'.targetParents', 1)
            cmds.setAttr(parentSwitch_grp+'.parentTargetList', lock=False)
            cmds.setAttr(parentSwitch_grp+'.parentTargetList', self.ch_root_transform, type='string', lock=True)

        # Connect the scaling on the character root transform to the parent switch group node.
        if connectScaleWithRootTransform:
            cmds.connectAttr(self.ch_root_transform+'.globalScale', parentSwitch_grp+'.scaleX')
            cmds.connectAttr(self.ch_root_transform+'.globalScale', parentSwitch_grp+'.scaleY')
            cmds.connectAttr(self.ch_root_transform+'.globalScale', parentSwitch_grp+'.scaleZ')

        return [parentSwitch_grp, transform_grp]


    def applyFK_Control(self):

        '''Creates control layer for simple FK on a character hierarchy.'''

        # First, use the scene utility function "createFKlayerDriverOnJointHierarchy" to create a joint layer over the
        # original (selected) character joint hierarchy. This layer will drive the joint hierarchy and its influence (weight)
        # can also be modified. See "mrt_functions.py", line # 1996 for details.

        # "createFKlayerDriverOnJointHierarchy" has the following arguments :

        # characterJointSet -> For this, we want the selected joint hierarchy, which will be controlled by creating a driver
        # joint layer. Pass-in the self.selCharacterHierarchy variable.
        #
        # jointLayerName -> Name for the joint layer. If you want to create a driver joint layer, you'd want to name it as
        # the control type that you're trying to create.
        #
        # characterName -> User specified name for the character. In this case, pass-in the self.characterName variable.
        #
        # asControl -> A suffix "_handle" would be added to each joint name for the returned joint layer indicating that
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
                                                                                                'FK_Control',
                                                                                                self.characterName,
                                                                                                True,
                                                                                                'On',
                                                                                                True,
                                                                                                self.controlColour,
                                                                                                True)

        # Update the instance attribute to contain the driver joint layer set.
        self.driverJointLayerSet = jointSet

        # Update the instance attribute to contain the driver constraints for the joint hiearachy.
        self.driverConstraintsForInput = driver_constraints

        # Update the naming prefix for the control rig.
        self.namePrefix = self.namePrefix + '_FK_Control'

        # Calculate the size of shape for the FK control.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.35

        # Create a parent switch group for the root FK control joint.
        ps_grps = self.createParentSwitchGrpForTransform(layerRootJoint, True)

        # For all the joints in the new layer, lock and hide the translation and scale attributes (only rotation for
        # FK control), attach a custom shape, and set colour and visibility.
        for joint in jointSet:
            cmds.setAttr(joint+'.radius', 0)
            mfunc.lockHideChannelAttrs(joint, 't', 's', 'radi', keyable=False, lock=True)
            cmds.setAttr(joint+'.overrideEnabled', 1)
            cmds.setAttr(joint+'.overrideColor', self.controlColour)
            cmds.setAttr(joint+'.visibility', keyable=False)

            # Load and attach a custom locatorShape to a transform. See the MRT documentation for utility and scene
            # functions available for use.
            xhandle = objects.load_xhandleShape(joint, self.controlColour)

            cmds.setAttr(xhandle[0]+'.localScaleX', shapeRadius)
            cmds.setAttr(xhandle[0]+'.localScaleY', shapeRadius)
            cmds.setAttr(xhandle[0]+'.localScaleZ', shapeRadius)
            cmds.setAttr(xhandle[0]+'.drawStyle', 5)

        # Create a custom keyable attribute on the character root transform by the control name to adjust the weight of the
        # driver joint layer by using the method "createCtrlRigWeightAttributeOnRootTransform".
        self.createCtrlRigWeightAttributeOnRootTransform(self.ctrlAttrPrefix+'_FK_Control', jointSet)

        # Create a container for the control rig and add the joint layer nodes to it.
        ctrl_container = cmds.createNode('container', name=self.namePrefix+'_Container', skipSelect=True)
        mfunc.addNodesToContainer(ctrl_container, ps_grps, True)

        # Publish the rotate attribute on the driver layer joints (which is used for direct control).
        for joint in jointSet:
            jointName = re.split('MRT_character%s__'%(self.characterName), joint)[1]
            cmds.container(ctrl_container, edit=True, publishAndBind=[joint+'.rotate', jointName+'_rotate'])
        cmds.select(clear=True)


    def applyFK_Control_Stretchy(self):

        '''Creates control layer for simple, scalable fk on a character hierarchy.'''

        # The procedure is the same as FK_Control, with scale added.

        # Create the driver joint layer on top of the selected joint hierarchy.
        jointSet, driver_constraints, layerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                                'FK_Control_Stretchy',
                                                                                                self.characterName,
                                                                                                True,
                                                                                                'On',
                                                                                                True,
                                                                                                self.controlColour,
                                                                                                True)

        # Update the instance attribute for the driver joint layer set.
        self.driverJointLayerSet = jointSet

        # Update the instance attribute to contain the driver constraints for the joint hierarachy.
        self.driverConstraintsForInput = driver_constraints

        # Update the naming prefix for the control rig.
        self.namePrefix = self.namePrefix + '_FK_Control_Stretchy'

        # Calculate the size of shape for the FK control.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.35

        # Create a parent switch group for the root FK control joint.
        ps_grps = self.createParentSwitchGrpForTransform(layerRootJoint, True)

        # For all the joints in the new layer, lock and hide the translation attributes, attach a custom shape,
        # and set colour and visibility.
        for joint in jointSet:
            cmds.setAttr(joint+'.radius', 0)
            mfunc.lockHideChannelAttrs(joint, 't', 'radi', keyable=False, lock=True)
            cmds.setAttr(joint+'.overrideEnabled', 1)
            cmds.setAttr(joint+'.overrideColor', self.controlColour)
            cmds.setAttr(joint+'.visibility', keyable=False)
            xhandle = objects.load_xhandleShape(joint, self.controlColour)
            cmds.setAttr(xhandle[0]+'.localScaleX', shapeRadius)
            cmds.setAttr(xhandle[0]+'.localScaleY', shapeRadius)
            cmds.setAttr(xhandle[0]+'.localScaleZ', shapeRadius)
            cmds.setAttr(xhandle[0]+'.drawStyle', 5)

            # Set 'transformScaling'. This is an attribute on the custom shape node which negates any scaling transformation
            # inherited from its parent transform, both inclusive and exclusive. Here, we want scaling for the control
            # shapes only from the character root transform control.
            cmds.setAttr(xhandle[0]+'.transformScaling', 0)

            # 'addScale' is an attribute on the custom shape node which can be used to receive DG connections to
            # increment/decrement the current 'localScale' value internally without re-setting it as a result of a
            # direct DG connection.
            cmds.connectAttr(self.ch_root_transform+'.globalScale', xhandle[0]+'.addScaleX')
            cmds.connectAttr(self.ch_root_transform+'.globalScale', xhandle[0]+'.addScaleY')
            cmds.connectAttr(self.ch_root_transform+'.globalScale', xhandle[0]+'.addScaleZ')

        # Create a custom keyable attribute on the character root transform by the control name to adjust the
        # weight of the driver joint layer by using the method "createCtrlRigWeightAttributeOnRootTransform".
        self.createCtrlRigWeightAttributeOnRootTransform(self.ctrlAttrPrefix+'_FK_Control_Stretchy', jointSet)

        # Create a container for the control rig and add the joint layer nodes (along with its parent switch group) to it.
        ctrl_container = cmds.createNode('container', name=self.namePrefix+'_Container', skipSelect=True)
        mfunc.addNodesToContainer(ctrl_container, ps_grps, True)

        # Publish the rotate and scale attributes on the driver layer joints (which is used for direct control).
        for joint in jointSet:
            jointName = re.split('MRT_character%s__'%(self.characterName), joint)[1]
            cmds.container(ctrl_container, edit=True, publishAndBind=[joint+'.rotate', jointName+'_rotate'])
            cmds.container(ctrl_container, edit=True, publishAndBind=[joint+'.scale', jointName+'_scale'])
        cmds.select(clear=True)


class JointControl(BaseJointControl):

    """Base joint control rigs, which will work on any type of joint hierarchy, created from single or multiple modules."""

    def __init__(self, characterName, rootJoint):
        # All methods are derived from BaseJointControl, which are FK control and FK Control Stretchy.
        BaseJointControl.__init__(self, characterName, rootJoint)


class CustomLegControl(BaseJointControl):

    """This is a custom hierarchy type which is constructed from a collection of (1) hinge module consisting\nof a hip,
    knee and an ankle with two joint modules connected to the ankle node of the hingle module as children(hierarchical 
    parent type). The (2) first joint module should contain two nodes resembling a ball and toe for a foot, and a 
    (3) third node for a heel."""

    # This string value must be store in one line.
    customHierarchy = '<HingeNode>_root_node_transform\n\t<HingeNode>_node_1_transform\n\t\t<HingeNode>_end_node_transform\n\t\t\t<JointNode>_root_node_transform\n\t\t\t<JointNode>_root_node_transform\n\t\t\t\t<JointNode>_end_node_transform\n'

    # This 'customHierarchy' variable is use to store the string value, which is used to check and match if the selected
    # custom joint hierarchy for control rigging can be applied with methods 	# in this class, or if it meets the exact
    # joint hiearchy structure required for this purpose.

    # The joint hiearchy string for a selected joint hierarchy (created using MRT) can be returned using one of base utility
    # functions, "returnHierarchyTreeListStringForCustomControlRigging".
    # It accepts three arguments: returnHierarchyTreeListStringForCustomControlRigging(rootJoint, prefix='', prettyPrint=True)

    # rootJoint -> Pass-in the root joint for the hierarchy.
    #
    # prefix -> A prefix string that can be used for naming the joints, which is returned with the result.
    #
    # prettyPrint -> Construct the returned string, that can be printed in a more user-friendly fashion.

    # Usage :

    # If the variable 'customHiearchy' is used to store the string output for the result of the function,
    # "returnHierarchyTreeListStringForCustomControlRigging", and then if we print the variable :

    # > customHierarchy = mfunc.returnHierarchyTreeListStringForCustomControlRigging(self.rootJoint, '', True)  # with no prefix, and prettyPrint=True
    # > print customHierarchy
    # <HingeNode>_root_node_transform
    #	    <HingeNode>_node_1_transform
    #		    <HingeNode>_end_node_transform
    #			    <JointNode>_root_node_transform
    #			    <JointNode>_root_node_transform
    #				    <JointNode>_end_node_transform

    # > customHierarchy = mfunc.returnHierarchyTreeListStringForCustomControlRigging(self.rootJoint, '', False)  # with no prefix, and prettyPrint=False
    # > print customHierarchy
    # <HingeNode>_root_node_transform\n\t<HingeNode>_node_1_transform\n\t\t<HingeNode>_end_node_transform\n\t\t\t<JointNode>_root_node_transform\n\t\t\t<JointNode>_root_node_transform\n\t\t\t\t<JointNode>_end_node_transform\n

    # With prettyPrint=True, it prints out the hierarchical structure of the joint chain starting from the passed-in
    # root joint.

    # Therefore, to get a printed output that can be copied and pasted as above (as with 'customHierarchy'),
    # set prettyPrint to False (I'd prefer you do it this way).


    def __init__(self, characterName, rootJoint):
        BaseJointControl.__init__(self, characterName, rootJoint)


    def applyReverse_IK_Leg_Control(self):

        '''Creates controls for a reverse IK leg with a main foot transform and a pole vector transform in auto
        non-flip / manual mode.'''

        # Update the naming prefix for the control rig.
        self.namePrefix = self.namePrefix + '_Reverse_IK_Leg_Control'

        # Control group, to be placed under "__controlGrp".
        ctrlGrp = cmds.group(empty=True, name=self.namePrefix + '_Grp', \
                                                                   parent='MRT_character%s__controlGrp'%(self.characterName))

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
        result = mfunc.returnCrossProductDirection(transform1_start_vec, transform1_end_vec, transform2_start_vec, \
                                                                                                          transform2_end_vec)
        leg_cross_pos = [round(item, 4) for item in result[1]]
        leg_cross_vec = map(lambda x,y:x+y, leg_cross_pos, transform1_start_vec)

        # Get the positions of heel, toe and the ball joints to find the IK plane and hence the perpendicular vector for
        # the foot plane.
        transform1_start_vec = transform2_start_vec = cmds.xform(origHeelJoint, query=True, worldSpace=True, translation=True)
        transform1_end_vec = cmds.xform(origAnkleJoint, query=True, worldSpace=True, translation=True)
        transform2_end_vec = cmds.xform(origToeJoint, query=True, worldSpace=True, translation=True)
        result = mfunc.returnCrossProductDirection(transform1_start_vec, transform1_end_vec, transform2_start_vec, \
                                                                                                          transform2_end_vec)
        foot_cross_pos = [round(item, 4) for item in result[1]]
        foot_cross_vec = map(lambda x,y:x+y, foot_cross_pos, transform1_start_vec)
        foot_aim_vec = mfunc.returnOffsetPositionBetweenTwoVectors(transform2_start_vec, transform2_end_vec, 1.5)
        foot_vec_dict = {'heel_pos':transform1_start_vec, 'cross':foot_cross_vec, 'aim':foot_aim_vec, 'hip_pos':hip_pos}

        # Create the FK layer for the control rig.
        jointSet, driver_constraints, layerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                                    'Reverse_IK_Leg_Control',
                                                                                                     self.characterName,
                                                                                                     False,
                                                                                                     'None',
                                                                                                     True)

        # Update the instance attribute for the driver joint layer set.
        self.driverJointLayerSet = jointSet

        # Update the instance attribute to contain the driver constraints for the joint hiearachy.
        self.driverConstraintsForInput = driver_constraints

        # Create a container for the control rig.
        ctrl_container = cmds.createNode('container', name=self.namePrefix+'_Container', skipSelect=True)

        # Add the driver layer joints to the container.
        mfunc.addNodesToContainer(ctrl_container, jointSet, includeHierarchyBelow=True)

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
        check = cmds.cycleCheck(query=True, evaluation=True)
        if check:
            cmds.cycleCheck(evaluation=False)
        handleName = self.namePrefix + '_hipAnkleIkHandle'
        effName = self.namePrefix + '_hipAnkleIkEffector'
        legIkNodes = cmds.ikHandle(startJoint=hipJoint, endEffector=ankleJoint, name=handleName, solver='ikRPsolver')
        cmds.rename(legIkNodes[1], effName)
        cmds.setAttr(legIkNodes[0]+'.visibility', 0)
        tempConstraint = cmds.orientConstraint(ankleJoint, legIkNodes[0], maintainOffset=False)
        cmds.delete(tempConstraint)
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
        if check:
            cmds.cycleCheck(evaluation=True)

        # Create the IK control handle.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.88
        legControlHandle_preTransform = self.namePrefix + '_handle_preTransform'
        cmds.group(empty=True, name=legControlHandle_preTransform)
        legControlHandle = objects.load_xhandleShape(self.namePrefix+'_handle', self.controlColour, True)
        cmds.parent(legControlHandle[1], legControlHandle_preTransform, relative=True)
        cmds.makeIdentity(legControlHandle[1], translate=True, rotate=True, apply=True)
        cmds.setAttr(legControlHandle[0]+'.localScaleX', shapeRadius)
        cmds.setAttr(legControlHandle[0]+'.localScaleY', shapeRadius)
        cmds.setAttr(legControlHandle[0]+'.localScaleZ', shapeRadius)
        cmds.setAttr(legControlHandle[0]+'.drawStyle', 6)
        mfunc.lockHideChannelAttrs(legControlHandle[1], 's', 'v', keyable=False, lock=True)
        cmds.addAttr(legControlHandle[1], attributeType='enum', longName='Foot_Controls', enumName=' ', keyable=True)
        cmds.setAttr(legControlHandle[1]+'.Foot_Controls', lock=True)
        cmds.addAttr(legControlHandle[1], attributeType='double', longName='Foot_Roll', defaultValue=0, keyable=True)
        cmds.addAttr(legControlHandle[1], attributeType='double', longName='Foot_Toe_Lift', defaultValue=30, keyable=True)
        cmds.addAttr(legControlHandle[1], attributeType='double', longName='Foot_Toe_Straight', defaultValue=70, keyable=True)
        cmds.addAttr(legControlHandle[1], attributeType='double', longName='Knee_Twist', defaultValue=0, keyable=True)
        cmds.addAttr(legControlHandle[1], attributeType='double', longName='Foot_Bank', defaultValue=0, keyable=True)
        cmds.addAttr(legControlHandle[1], attributeType='double', longName='Ball_Pivot', defaultValue=0, keyable=True)
        cmds.addAttr(legControlHandle[1], attributeType='double', longName='Toe_Pivot', defaultValue=0, keyable=True)
        cmds.addAttr(legControlHandle[1], attributeType='double', longName='Toe_Curl', defaultValue=0, keyable=True)
        cmds.addAttr(legControlHandle[1], attributeType='double', longName='Heel_Pivot', defaultValue=0, keyable=True)
        cmds.addAttr(legControlHandle[1], attributeType='enum', longName='Pole_Vector_Mode', minValue=0, maxValue=1, \
                                                                    enumName=':No Flip:Manual', defaultValue=0, keyable=True)

        if cmds.attributeQuery('translationFunction', node=legControlHandle[1], exists=True) and \
                                            cmds.getAttr(legControlHandle[1]+'.translationFunction') == 'local_orientation':
            cmds.xform(legControlHandle_preTransform, worldSpace=True, translation=\
                cmds.xform(ankleJoint, query=True, worldSpace=True, translation=True), rotation=\
                    cmds.xform(ankleJoint, query=True, worldSpace=True, rotation=True))

            legControlAxesInfo = mfunc.returnAxesInfoForFootTransform(legControlHandle[1], foot_vec_dict)
        else:
            cmds.xform(legControlHandle_preTransform, worldSpace=True, translation=cmds.xform(ankleJoint, query=True, \
                                                                                        worldSpace=True, translation=True))
            cmds.setAttr(legControlHandle[1]+'.rotateOrder', 2)
        cmds.parent(legControlHandle_preTransform, ctrlGrp, absolute=True)

        # Create a parent switch grp for the IK control handle.
        ps_groups = self.createParentSwitchGrpForTransform(legControlHandle[1], True, 1, True)

        # Create and place the foot group transforms for parenting IK handles and set their respective rotation orders.
        heel_grp_preTransform = self.namePrefix + '_heelRoll_preTransform'
        heel_grp = self.namePrefix + '_heelRoll_transform'
        cmds.group(empty=True, name=heel_grp_preTransform)
        cmds.group(empty=True, name=heel_grp)
        cmds.xform(heel_grp_preTransform, worldSpace=True, translation=cmds.xform(heelJoint, query=True, worldSpace=True, \
                               translation=True), rotation=cmds.xform(heelJoint, query=True, worldSpace=True, rotation=True))
        cmds.parent(heel_grp_preTransform, legControlHandle[1], absolute=True)
        cmds.parent(heel_grp, heel_grp_preTransform, relative=True)
        cmds.makeIdentity(heel_grp, rotate=True, apply=True)
        heel_grp_axesInfoData = mfunc.returnAxesInfoForFootTransform(heel_grp, foot_vec_dict)
        if heel_grp_axesInfoData['cross'][1] > 0:
            heel_grp_cross_ax_rot_mult = 1
        else:
            heel_grp_cross_ax_rot_mult = -1
        mfunc.setRotationOrderForFootUtilTransform(heel_grp, heel_grp_axesInfoData)

        toeRoll_grp = self.namePrefix + '_toeRoll_transform'
        cmds.group(empty=True, name=toeRoll_grp)

        cmds.xform(toeRoll_grp, worldSpace=True, translation=\
            cmds.xform(toeJoint, query=True, worldSpace=True, translation=True), rotation=\
                cmds.xform(toeJoint, query=True, worldSpace=True, rotation=True))

        cmds.parent(toeRoll_grp, heel_grp, absolute=True)
        cmds.makeIdentity(toeRoll_grp, rotate=True, apply=True)
        toeRoll_grp_axesInfoData = mfunc.returnAxesInfoForFootTransform(toeRoll_grp, foot_vec_dict)
        if toeRoll_grp_axesInfoData['cross'][1] > 0:
            toeRoll_grp_cross_ax_rot_mult = 1
        else:
            toeRoll_grp_cross_ax_rot_mult = -1
        mfunc.setRotationOrderForFootUtilTransform(toeRoll_grp, toeRoll_grp_axesInfoData)

        ballRoll_grp = self.namePrefix + '_ballRoll_transform'
        cmds.group(empty=True, name=ballRoll_grp)

        cmds.xform(ballRoll_grp, worldSpace=True, translation=\
            cmds.xform(ballJoint, query=True, worldSpace=True, translation=True), rotation=\
                cmds.xform(ballJoint, query=True, worldSpace=True, rotation=True))

        cmds.parent(ballRoll_grp, toeRoll_grp, absolute=True)
        cmds.makeIdentity(ballRoll_grp, rotate=True, apply=True)
        ballRoll_grp_axesInfoData = mfunc.returnAxesInfoForFootTransform(toeRoll_grp, foot_vec_dict)
        if ballRoll_grp_axesInfoData['cross'][1] > 0:
            ballRoll_grp_cross_ax_rot_mult = 1
        else:
            ballRoll_grp_cross_ax_rot_mult = -1
        mfunc.setRotationOrderForFootUtilTransform(ballRoll_grp, ballRoll_grp_axesInfoData)

        toeCurl_grp = self.namePrefix + '_toeCurl_transform'
        cmds.group(empty=True, name=toeCurl_grp)

        cmds.xform(toeCurl_grp, worldSpace=True, translation=\
            cmds.xform(ballJoint, query=True, worldSpace=True, translation=True), rotation=\
                cmds.xform(ballJoint, query=True, worldSpace=True, rotation=True))

        cmds.parent(toeCurl_grp, toeRoll_grp, absolute=True)
        cmds.makeIdentity(toeCurl_grp, rotate=True, apply=True)
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

        # Find the world positions for hip, knee and ankle, and then calculate the knee manual pole vector and start
        # position for the no-flip pole vector.
        hip_pos = cmds.xform(hipJoint, query=True, worldSpace=True, translation=True)
        ankle_pos = cmds.xform(ankleJoint, query=True, worldSpace=True, translation=True)
        hip_ankle_mid_pos = eval(cmds.getAttr(self.rootJoint+'.ikSegmentMidPos'))
        knee_pos = cmds.xform(kneeJoint, query=True, worldSpace=True, translation=True)
        ik_pv_offset_pos = mfunc.returnOffsetPositionBetweenTwoVectors(hip_ankle_mid_pos, knee_pos, 2.0)

        hip_knee_vec = map(lambda x,y: x-y, hip_pos, knee_pos)
        hip_ankle_vec = map(lambda x,y: x-y, hip_pos, ankle_pos)
        hip_knee_vec_mag = math.sqrt(reduce(lambda x,y: x+y, [component**2 for component in hip_knee_vec]))
        hip_ankle_vec_mag = math.sqrt(reduce(lambda x,y: x+y, [component**2 for component in hip_ankle_vec]))

        i = 1
        while True:
            ik_pv_pos_knee_vec = map(lambda x,y: x-y, ik_pv_offset_pos, knee_pos)
            ik_pv_pos_knee_mag = math.sqrt(reduce(lambda x,y: x+y, [component**2 for component in ik_pv_pos_knee_vec]))
            if ik_pv_pos_knee_mag > hip_knee_vec_mag:
                break
            else:
                ik_pv_offset_pos = mfunc.returnOffsetPositionBetweenTwoVectors(hip_ankle_mid_pos, knee_pos, 2.0*i)
            i += 1

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
        pv_main_grp = self.namePrefix + '_poleVector_mainGrp'
        cmds.group(empty=True, name=pv_main_grp, parent=ctrlGrp)

        cmds.xform(pv_main_grp, worldSpace=True, translation=\
            cmds.xform(ankleJoint, query=True, worldSpace=True, translation=True))

        # Create the no-flip pole vector transform and offset its position from the foot accordingly.
        kneePVnoFlip_transform = self.namePrefix + '_kneePVnoFlip_handle'
        kneePVnoFlip_preTransform = self.namePrefix + '_kneePVnoFlip_handle_preTransform'
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
        knee_manual_preTransform = self.namePrefix + '_kneeManualPV_handle_preTransform'
        cmds.group(empty=True, name=knee_manual_preTransform, parent=pv_main_grp)
        ##cmds.xform(elbow_pv_preTransform, worldSpace=True, translation=ik_pv_offset_pos)
        cmds.xform(knee_manual_preTransform, worldSpace=True, translation=ik_pv_offset_pos)
        knee_manual_transform = objects.load_xhandleShape(self.namePrefix+'_kneeManualPV_handle', self.controlColour, True)
        cmds.setAttr(knee_manual_transform[0]+'.localScaleX', manualPVHandleShapeRadius)
        cmds.setAttr(knee_manual_transform[0]+'.localScaleY', manualPVHandleShapeRadius)
        cmds.setAttr(knee_manual_transform[0]+'.localScaleZ', manualPVHandleShapeRadius)
        cmds.setAttr(knee_manual_transform[0]+'.drawStyle', 3)
        ##cmds.xform(knee_manual_transform[1], worldSpace=True, translation=ik_pv_offset_pos)
        ##cmds.parent(knee_manual_transform[1], knee_manual_preTransform, absolute=True)
        cmds.parent(knee_manual_transform[1], knee_manual_preTransform, relative=True)
        ##cmds.makeIdentity(knee_manual_transform[1], translate=True, apply=True)
        mfunc.lockHideChannelAttrs(knee_manual_transform[1], 'r', 's', 'v', keyable=False, lock=True)

        # Create a parent switch grp for the manual knee pole vector transform.
        ps_groups = self.createParentSwitchGrpForTransform(knee_manual_transform[1], True, 1, True)

        # Calculate the offset position for the foot bank control transform.
        ball_pos = cmds.xform(ballJoint, query=True, worldSpace=True, translation=True)
        heel_pos = cmds.xform(heelJoint, query=True, worldSpace=True, translation=True)
        ball_heel_vec = map(lambda x,y: x-y, ball_pos, heel_pos)
        ball_heel_vec_mag = math.sqrt(reduce(lambda x,y: x+y, [component**2 for component in ball_heel_vec])) * 0.3

        # Create and place the foot bank transform controls.
        bankPivot_1_transform = objects.load_xhandleShape(self.namePrefix+'_footBankPivot_1_handle', self.controlColour, True)
        cmds.setAttr(bankPivot_1_transform[0]+'.localScaleX', manualPVHandleShapeRadius * 0.7)
        cmds.setAttr(bankPivot_1_transform[0]+'.localScaleY', manualPVHandleShapeRadius * 0.7)
        cmds.setAttr(bankPivot_1_transform[0]+'.localScaleZ', manualPVHandleShapeRadius * 0.7)
        cmds.setAttr(bankPivot_1_transform[0]+'.drawStyle', 3)
        mfunc.lockHideChannelAttrs(bankPivot_1_transform[1], 'r', 's', 'v', keyable=False, lock=True)
        cmds.parent(bankPivot_1_transform[1], toeRoll_grp, relative=True)
        cmds.setAttr(bankPivot_1_transform[1]+'.translate'+toeRoll_grp_axesInfoData['cross'][0], ball_heel_vec_mag)

        for axis in ['X', 'Y', 'Z']:
            val = cmds.getAttr(bankPivot_1_transform[1]+'.translate'+axis)
            if not val:
                cmds.setAttr(bankPivot_1_transform[1]+'.translate'+axis, keyable=False, channelBox=False, lock=True)

        bankPivot_2_transform = objects.load_xhandleShape(self.namePrefix+'_footBankPivot_2_handle', self.controlColour, True)
        cmds.setAttr(bankPivot_2_transform[0]+'.localScaleX', manualPVHandleShapeRadius * 0.7)
        cmds.setAttr(bankPivot_2_transform[0]+'.localScaleY', manualPVHandleShapeRadius * 0.7)
        cmds.setAttr(bankPivot_2_transform[0]+'.localScaleZ', manualPVHandleShapeRadius * 0.7)
        cmds.setAttr(bankPivot_2_transform[0]+'.drawStyle', 3)
        mfunc.lockHideChannelAttrs(bankPivot_2_transform[1], 's', 'r', 'v', keyable=False, lock=True)
        cmds.parent(bankPivot_2_transform[1], toeRoll_grp, relative=True)
        cmds.setAttr(bankPivot_2_transform[1]+'.translate'+toeRoll_grp_axesInfoData['cross'][0], ball_heel_vec_mag*-1)

        for axis in ['X', 'Y', 'Z']:
            val = cmds.getAttr(bankPivot_2_transform[1]+'.translate'+axis)
            if not val:
                cmds.setAttr(bankPivot_2_transform[1]+'.translate'+axis, keyable=False, channelBox=False, lock=True)

        # Create the SDKs for knee pole vector control attributes on the leg IK control to drive the pole vector mode.
        containedNodes = []
        pvConstraint = cmds.poleVectorConstraint(kneePVnoFlip_transform, knee_manual_transform[1], legIkNodes[0], \
                                                                                name=legIkNodes[0]+'_poleVectorConstraint')[0]
        for driver, driven in [[0, ik_twist], [1, 0]]:
            cmds.setAttr(legControlHandle[1]+'.Pole_Vector_Mode', driver)
            cmds.setAttr(legIkNodes[0]+'.twist', driven)
            cmds.setDrivenKeyframe(legIkNodes[0]+'.twist', currentDriver=legControlHandle[1]+'.Pole_Vector_Mode')

        for driver, driven_1, driven_2 in [[0, 1, 0], [1, 0, 1]]:
            cmds.setAttr(legControlHandle[1]+'.Pole_Vector_Mode', driver)
            cmds.setAttr(pvConstraint+'.'+kneePVnoFlip_transform+'W0', driven_1)
            cmds.setAttr(pvConstraint+'.'+knee_manual_transform[1]+'W1', driven_2)
            cmds.setAttr(knee_manual_transform[1]+'_preTransform.visibility', driven_2)
            cmds.setDrivenKeyframe(pvConstraint+'.'+kneePVnoFlip_transform+'W0', \
                                                                       currentDriver=legControlHandle[1]+'.Pole_Vector_Mode')
            cmds.setDrivenKeyframe(pvConstraint+'.'+knee_manual_transform[1]+'W1', \
                                                                       currentDriver=legControlHandle[1]+'.Pole_Vector_Mode')
            cmds.setDrivenKeyframe(knee_manual_transform[1]+'_preTransform.visibility', \
                                                                       currentDriver=legControlHandle[1]+'.Pole_Vector_Mode')
        cmds.setAttr(legControlHandle[1]+'.Pole_Vector_Mode', 0)
        kneePVnoFlip_preTransform_axisInfo = mfunc.returnAxesInfoForFootTransform(kneePVnoFlip_preTransform, foot_vec_dict)
        cmds.connectAttr(legControlHandle[1]+'.Knee_Twist', \
                                             kneePVnoFlip_preTransform+'.rotate'+kneePVnoFlip_preTransform_axisInfo['up'][0])

        # Now connect the custom attributes on the leg IK control, with utility nodes, as needed.
        # Also, set the rotation multipliers for the parent transforms for the foot IKs to ensure correct/preferred rotation.
        ballRoll_setRange = cmds.createNode('setRange', name=ballRoll_grp.rpartition('transform')[0]+'setRange', \
                                                                                                             skipSelect=True)
        ballRoll_firstCondition = cmds.createNode('condition', name=ballRoll_grp.rpartition('transform')[0]+'firstCondition',\
                                                                                                             skipSelect=True)
        cmds.setAttr(ballRoll_firstCondition+'.operation', 4)
        ballRoll_secondCondition = cmds.createNode('condition', name=ballRoll_grp.rpartition('transform')[0]+'secondCondition', \
                                                                                                             skipSelect=True)
        cmds.setAttr(ballRoll_secondCondition+'.operation', 2)
        cmds.setAttr(ballRoll_secondCondition+'.colorIfFalseR', 0)
        cmds.connectAttr(legControlHandle[1]+'.Foot_Toe_Straight', ballRoll_setRange+'.oldMaxX')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Toe_Lift', ballRoll_setRange+'.oldMinX')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Toe_Lift', ballRoll_setRange+'.minX')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Roll', ballRoll_setRange+'.valueX')
        cmds.connectAttr(ballRoll_setRange+'.outValueX', ballRoll_firstCondition+'.colorIfFalseR')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Toe_Lift', ballRoll_firstCondition+'.secondTerm')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Roll', ballRoll_firstCondition+'.colorIfTrueR')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Roll', ballRoll_firstCondition+'.firstTerm')
        cmds.connectAttr(ballRoll_firstCondition+'.outColorR', ballRoll_secondCondition+'.firstTerm')
        cmds.connectAttr(ballRoll_firstCondition+'.outColorR', ballRoll_secondCondition+'.colorIfTrueR')
        ballRollCrossAxMultiply = cmds.createNode('multDoubleLinear', \
                                            name=ballRoll_grp.rpartition('transform')[0]+'cross_ax_multiply', skipSelect=True)
        cmds.connectAttr(ballRoll_secondCondition+'.outColorR', ballRollCrossAxMultiply+'.input1')
        cmds.setAttr(ballRollCrossAxMultiply+'.input2', ballRoll_grp_cross_ax_rot_mult)
        cmds.connectAttr(ballRollCrossAxMultiply+'.output', ballRoll_grp+'.rotate'+ballRoll_grp_axesInfoData['cross'][0])

        cmds.connectAttr(legControlHandle[1]+'.Ball_Pivot', ballRoll_grp+'.rotate'+ballRoll_grp_axesInfoData['up'][0])
        containedNodes.extend([ballRoll_setRange, ballRoll_firstCondition, ballRoll_secondCondition, ballRollCrossAxMultiply])

        bankPivot_1_condition = cmds.createNode('condition', \
                                            name=bankPivot_1_transform[1].rpartition('Handle')[0]+'condition', skipSelect=True)
        cmds.setAttr(bankPivot_1_condition+'.colorIfFalseR', 0)
        bankPivot_1_transform_axesInfo = mfunc.returnAxesInfoForFootTransform(bankPivot_1_transform[1], foot_vec_dict)
        val = cmds.getAttr(bankPivot_1_transform[1]+'.translate'+bankPivot_1_transform_axesInfo['cross'][0])
        if val > 0:
            cmds.setAttr(bankPivot_1_condition+'.operation', 4)
        else:
            cmds.setAttr(bankPivot_1_condition+'.operation', 2)
        bankPivot_2_condition = cmds.createNode('condition', \
                                            name=bankPivot_2_transform[1].rpartition('Handle')[0]+'condition', skipSelect=True)
        cmds.setAttr(bankPivot_2_condition+'.colorIfFalseR', 0)
        bankPivot_2_transform_axesInfo = mfunc.returnAxesInfoForFootTransform(bankPivot_2_transform[1], foot_vec_dict)
        val = cmds.getAttr(bankPivot_2_transform[1]+'.translate'+bankPivot_2_transform_axesInfo['cross'][0])
        if val > 0:
            cmds.setAttr(bankPivot_2_condition+'.operation', 4)
        else:
            cmds.setAttr(bankPivot_2_condition+'.operation', 2)
        bankPivotRest_condition = cmds.createNode('condition', name=re.split('\d+_handle', \
                                                                bankPivot_1_transform[1])[0]+'restCondition', skipSelect=True)
        cmds.setAttr(bankPivotRest_condition+'.colorIfFalseR', 0)
        cmds.setAttr(bankPivotRest_condition+'.colorIfTrueR', 0)
        cmds.setAttr(bankPivotRest_condition+'.operation', 0)
        cmds.connectAttr(legControlHandle[1]+'.Foot_Bank', bankPivotRest_condition+'.firstTerm')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Bank', bankPivot_1_condition+'.firstTerm')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Bank', bankPivot_2_condition+'.firstTerm')
        cmds.connectAttr(bankPivot_1_transform[1]+'.translate'+bankPivot_1_transform_axesInfo['cross'][0], \
                                                                                        bankPivot_1_condition+'.colorIfTrueR')
        cmds.connectAttr(bankPivot_2_transform[1]+'.translate'+bankPivot_2_transform_axesInfo['cross'][0], \
                                                                                        bankPivot_2_condition+'.colorIfTrueR')
        toeRoll_rotCrossAxisPivotPlus = cmds.createNode('plusMinusAverage', \
            name=toeRoll_grp.rpartition('transform')[0]+'rotatePivot'+bankPivot_2_transform_axesInfo['cross'][0]+'Plus', \
                                                                                                              skipSelect=True)
        cmds.connectAttr(bankPivot_1_condition+'.outColorR', toeRoll_rotCrossAxisPivotPlus+'.input1D[0]')
        cmds.connectAttr(bankPivot_2_condition+'.outColorR', toeRoll_rotCrossAxisPivotPlus+'.input1D[1]')
        cmds.connectAttr(bankPivotRest_condition+'.outColorR', toeRoll_rotCrossAxisPivotPlus+'.input1D[2]')
        cmds.connectAttr(toeRoll_rotCrossAxisPivotPlus+'.output1D', \
                                                              toeRoll_grp+'.rotatePivot'+toeRoll_grp_axesInfoData['cross'][0])

        toeRollAimAxMultiply = cmds.createNode('multDoubleLinear', \
                                               name=toeRoll_grp.rpartition('transform')[0]+'aim_ax_multiply', skipSelect=True)
        cmds.connectAttr(legControlHandle[1]+'.Foot_Bank', toeRollAimAxMultiply+'.input1')
        cmds.setAttr(toeRollAimAxMultiply+'.input2', 1)
        cmds.connectAttr(toeRollAimAxMultiply+'.output', toeRoll_grp+'.rotate'+toeRoll_grp_axesInfoData['aim'][0])

        containedNodes.extend([bankPivot_1_condition, bankPivot_2_condition, bankPivotRest_condition,
                                                                         toeRoll_rotCrossAxisPivotPlus, toeRollAimAxMultiply])

        toeRoll_setRange = cmds.createNode('setRange', name=toeRoll_grp.rpartition('transform')[0]+'setRange', skipSelect=True)
        toeRoll_firstCondition = cmds.createNode('condition', name=toeRoll_grp.rpartition('transform')[0]+'firstCondition', \
                                                                                                               skipSelect=True)
        cmds.setAttr(toeRoll_firstCondition+'.operation', 2)
        cmds.setAttr(toeRoll_firstCondition+'.colorIfFalseR', 0)
        toeRoll_secondCondition = cmds.createNode('condition', name=toeRoll_grp.rpartition('transform')[0]+'secondCondition', \
                                                                                                               skipSelect=True)
        cmds.setAttr(toeRoll_secondCondition+'.operation', 4)
        toeRoll_thirdCondition = cmds.createNode('condition', name=toeRoll_grp.rpartition('transform')[0]+'thirdCondition', \
                                                                                                               skipSelect=True)
        cmds.setAttr(toeRoll_thirdCondition+'.operation', 5)
        cmds.connectAttr(legControlHandle[1]+'.Foot_Roll', toeRoll_firstCondition+'.colorIfTrueR')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Roll', toeRoll_firstCondition+'.firstTerm')
        cmds.connectAttr(toeRoll_firstCondition+'.outColorR', toeRoll_secondCondition+'.colorIfTrueR')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Roll', toeRoll_secondCondition+'.firstTerm')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Toe_Lift', toeRoll_secondCondition+'.secondTerm')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Roll', toeRoll_secondCondition+'.colorIfFalseR')
        cmds.connectAttr(toeRoll_secondCondition+'.outColorR', toeRoll_setRange+'.valueX')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Toe_Lift', toeRoll_setRange+'.oldMinX')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Toe_Straight', toeRoll_setRange+'.oldMaxX')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Toe_Straight', toeRoll_setRange+'.maxX')
        cmds.connectAttr(toeRoll_setRange+'.outValueX', toeRoll_thirdCondition+'.colorIfTrueR')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Roll', toeRoll_thirdCondition+'.firstTerm')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Toe_Straight', toeRoll_thirdCondition+'.secondTerm')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Roll', toeRoll_thirdCondition+'.colorIfFalseR')

        toeRollCrossAxMultiply = cmds.createNode('multDoubleLinear', \
                                             name=toeRoll_grp.rpartition('transform')[0]+'cross_ax_multiply', skipSelect=True)
        cmds.connectAttr(toeRoll_thirdCondition+'.outColorR', toeRollCrossAxMultiply+'.input1')
        cmds.setAttr(toeRollCrossAxMultiply+'.input2', toeRoll_grp_cross_ax_rot_mult)
        cmds.connectAttr(toeRollCrossAxMultiply+'.output', toeRoll_grp+'.rotate'+toeRoll_grp_axesInfoData['cross'][0])
        cmds.connectAttr(legControlHandle[1]+'.Toe_Pivot', toeRoll_grp+'.rotate'+toeRoll_grp_axesInfoData['up'][0])
        toeCurlCrossAxMultiply = cmds.createNode('multDoubleLinear', \
                                             name=toeCurl_grp.rpartition('transform')[0]+'cross_ax_multiply', skipSelect=True)
        cmds.connectAttr(legControlHandle[1]+'.Toe_Curl', toeCurlCrossAxMultiply+'.input1')
        cmds.setAttr(toeCurlCrossAxMultiply+'.input2', toeCurl_grp_cross_ax_rot_mult)
        cmds.connectAttr(toeCurlCrossAxMultiply+'.output', toeCurl_grp+'.rotate'+toeCurl_grp_axesInfoData['cross'][0])
        cmds.connectAttr(legControlHandle[1]+'.Ball_Pivot', toeCurl_grp+'.rotate'+toeCurl_grp_axesInfoData['up'][0])
        containedNodes.extend([toeRoll_setRange, toeRoll_firstCondition, toeRoll_secondCondition,
                                                      toeRoll_thirdCondition, toeRollCrossAxMultiply, toeCurlCrossAxMultiply])

        heelRoll_condition = cmds.createNode('condition', name=heel_grp.rpartition('transform')[0]+'condition', skipSelect=True)
        cmds.setAttr(heelRoll_condition+'.operation', 3)
        cmds.setAttr(heelRoll_condition+'.colorIfFalseR', 0)
        cmds.connectAttr(legControlHandle[1]+'.Foot_Roll', heelRoll_condition+'.colorIfTrueR')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Roll', heelRoll_condition+'.secondTerm')
        heelRollCrossAxMultiply = cmds.createNode('multDoubleLinear', \
                                                 name=heel_grp.rpartition('transform')[0]+'cross_ax_multiply', skipSelect=True)
        cmds.connectAttr(heelRoll_condition+'.outColorR', heelRollCrossAxMultiply+'.input1')
        cmds.setAttr(heelRollCrossAxMultiply+'.input2', heel_grp_cross_ax_rot_mult)
        cmds.connectAttr(heelRollCrossAxMultiply+'.output', heel_grp+'.rotate'+heel_grp_axesInfoData['cross'][0])
        cmds.connectAttr(legControlHandle[1]+'.Heel_Pivot', heel_grp+'.rotate'+heel_grp_axesInfoData['up'][0])
        containedNodes.extend([heelRoll_condition, heelRollCrossAxMultiply])

        # Add the nodes to the control rig container, and then publish the necessary keyable attributes.
        mfunc.addNodesToContainer(ctrl_container, containedNodes+[ctrlGrp], includeHierarchyBelow=True)

        mfunc.updateContainerNodes(ctrl_container)

        # Check and correct the aim and hence the axial rotation of the toeRoll group along the length of the foot.
        bankPivot_1_restPos = cmds.getAttr(bankPivot_1_transform[1]+'Shape.worldPosition')[0]
        rest_mag_bankPivot_hip = mfunc.returnVectorMagnitude(hip_pos, bankPivot_1_restPos)
        toeRoll_grp_aim_ax_rot_mult = 1
        for value in (15, -15):
            cmds.setAttr(legControlHandle[1]+'.Foot_Bank', value)
            bankPivot_1_pos = cmds.getAttr(bankPivot_1_transform[1]+'Shape.worldPosition')[0]
            mag_bankPivot_hip = mfunc.returnVectorMagnitude(hip_pos, bankPivot_1_pos)
            if round(mag_bankPivot_hip, 4) > round(rest_mag_bankPivot_hip, 4):
                cmds.setAttr(toeRollAimAxMultiply+'.input2', -1)
        cmds.setAttr(legControlHandle[1]+'.Foot_Bank', 0)

        legControlAttrs = cmds.listAttr(legControlHandle[1], keyable=True, visible=True, unlocked=True)
        legControlName = legControlHandle[1].partition('__')[2]
        for attr in legControlAttrs:
            if not re.search('Foot_Toe_Straight|Foot_Toe_Lift', attr):
                cmds.container(ctrl_container, edit=True, publishAndBind=[legControlHandle[1]+'.'+attr, \
                                                                                                    legControlName+'_'+attr])
        for axis in ['X', 'Y', 'Z']:
            cmds.container(ctrl_container, edit=True, publishAndBind=[knee_manual_transform[1]+'.translate'+axis, \
                                                                                      'kneePVmanual_control_translate'+axis])
        cmds.setAttr(legControlHandle[1]+'.overrideEnabled', 1)
        cmds.connectAttr('MRT_character'+self.characterName+'_control_rig.visibility', \
                                                                                   legControlHandle[1]+'.overrideVisibility')
        cmds.setAttr(knee_manual_transform[1]+'.overrideEnabled', 1)
        cmds.connectAttr('MRT_character'+self.characterName+'_control_rig.visibility', \
                                                                              knee_manual_transform[1]+'.overrideVisibility')

        # Create a custom keyable attribute on the character root transform by the control name to adjust the weight
        # of the driver joint layer by using the method "createCtrlRigWeightAttributeOnRootTransform".
        self.createCtrlRigWeightAttributeOnRootTransform(self.ctrlAttrPrefix+'_Reverse_IK_Leg_Control',
                                                        [legControlHandle[1], bankPivot_1_transform[1],
                                                        bankPivot_2_transform[1], knee_manual_transform[1]])
        cmds.select(clear=True)


    def applyReverse_IK_Leg_Control_Stretchy(self):

        '''Creates controls for a stretchy reverse IK leg with a main foot transform and a pole vector transform in
        auto non-flip / manual mode.'''

        # Update the naming prefix for the control rig.
        self.namePrefix = self.namePrefix + '_Reverse_IK_Leg_Control_Stretchy'

        # Control group, to be placed under "__controlGrp".
        ctrlGrp = cmds.group(empty=True, name=self.namePrefix + '_Grp', \
                                                                    parent='MRT_character%s__controlGrp'%(self.characterName))

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
        result = mfunc.returnCrossProductDirection(transform1_start_vec, transform1_end_vec, transform2_start_vec, \
                                                                                                           transform2_end_vec)
        leg_cross_pos = [round(item, 4) for item in result[1]]
        leg_cross_vec = map(lambda x,y:x+y, leg_cross_pos, transform1_start_vec)

        # Get the positions of heel, toe and the ball joints to find the IK plane and hence the perpendicular vector
        # for the foot plane.
        transform1_start_vec = transform2_start_vec = cmds.xform(origHeelJoint, query=True, worldSpace=True, translation=True)
        transform1_end_vec = cmds.xform(origAnkleJoint, query=True, worldSpace=True, translation=True)
        transform2_end_vec = cmds.xform(origToeJoint, query=True, worldSpace=True, translation=True)
        result = mfunc.returnCrossProductDirection(transform1_start_vec, transform1_end_vec, transform2_start_vec, \
                                                                                                           transform2_end_vec)
        foot_cross_pos = [round(item, 4) for item in result[1]]
        foot_cross_vec = map(lambda x,y:x+y, foot_cross_pos, transform1_start_vec)
        foot_aim_vec = mfunc.returnOffsetPositionBetweenTwoVectors(transform2_start_vec, transform2_end_vec, 1.5)
        foot_vec_dict = {'heel_pos':transform1_start_vec, 'cross':foot_cross_vec, 'aim':foot_aim_vec, 'hip_pos':hip_pos}

        # Create the FK layer for the control rig.
        jointSet, driver_constraints, layerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                            'Reverse_IK_Leg_Control_Stretchy',
                                                                                             self.characterName,
                                                                                             False,
                                                                                             'None',
                                                                                             True)
        # Update the instance attribute for the driver joint layer set.
        self.driverJointLayerSet = jointSet

        # Update the instance attribute to contain the driver constraints for the joint hiearachy.
        self.driverConstraintsForInput = driver_constraints

        # Create a container for the control rig.
        ctrl_container = cmds.createNode('container', name=self.namePrefix+'_Container', skipSelect=True)

        # Add the driver layer joints to the container.
        mfunc.addNodesToContainer(ctrl_container, jointSet, includeHierarchyBelow=True)

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
        check = cmds.cycleCheck(query=True, evaluation=True)
        if check:
            cmds.cycleCheck(evaluation=False)
        handleName = self.namePrefix + '_hipAnkleIkHandle'
        effName = self.namePrefix + '_hipAnkleIkEffector'
        legIkNodes = cmds.ikHandle(startJoint=hipJoint, endEffector=ankleJoint, name=handleName, solver='ikRPsolver')
        cmds.rename(legIkNodes[1], effName)
        cmds.setAttr(legIkNodes[0]+'.visibility', 0)
        tempConstraint = cmds.orientConstraint(ankleJoint, legIkNodes[0], maintainOffset=False)
        cmds.delete(tempConstraint)
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
        if check:
            cmds.cycleCheck(evaluation=True)

        # Create the IK control handle.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.88
        legControlHandle_preTransform = self.namePrefix + '_handle_preTransform'
        cmds.group(empty=True, name=legControlHandle_preTransform)
        legControlHandle = objects.load_xhandleShape(self.namePrefix+'_handle', self.controlColour, True)
        cmds.parent(legControlHandle[1], legControlHandle_preTransform, relative=True)
        cmds.makeIdentity(legControlHandle[1], translate=True, rotate=True, apply=True)
        cmds.setAttr(legControlHandle[0]+'.localScaleX', shapeRadius)
        cmds.setAttr(legControlHandle[0]+'.localScaleY', shapeRadius)
        cmds.setAttr(legControlHandle[0]+'.localScaleZ', shapeRadius)
        cmds.setAttr(legControlHandle[0]+'.drawStyle', 6)
        mfunc.lockHideChannelAttrs(legControlHandle[1], 's', 'v', keyable=False, lock=True)
        cmds.addAttr(legControlHandle[1], attributeType='enum', longName='Foot_Controls', enumName=' ', keyable=True)
        cmds.setAttr(legControlHandle[1]+'.Foot_Controls', lock=True)
        cmds.addAttr(legControlHandle[1], attributeType='double', longName='Foot_Roll', defaultValue=0, keyable=True)
        cmds.addAttr(legControlHandle[1], attributeType='double', longName='Foot_Toe_Lift', defaultValue=30, keyable=True)
        cmds.addAttr(legControlHandle[1], attributeType='double', longName='Foot_Toe_Straight', defaultValue=70, keyable=True)
        cmds.addAttr(legControlHandle[1], attributeType='double', longName='Knee_Twist', defaultValue=0, keyable=True)
        cmds.addAttr(legControlHandle[1], attributeType='double', longName='Foot_Bank', defaultValue=0, keyable=True)
        cmds.addAttr(legControlHandle[1], attributeType='double', longName='Ball_Pivot', defaultValue=0, keyable=True)
        cmds.addAttr(legControlHandle[1], attributeType='double', longName='Toe_Pivot', defaultValue=0, keyable=True)
        cmds.addAttr(legControlHandle[1], attributeType='double', longName='Toe_Curl', defaultValue=0, keyable=True)
        cmds.addAttr(legControlHandle[1], attributeType='double', longName='Heel_Pivot', defaultValue=0, keyable=True)
        cmds.addAttr(legControlHandle[1], attributeType='enum', longName='Pole_Vector_Mode', minValue=0, maxValue=1, \
                                                                     enumName=':No Flip:Manual', defaultValue=0, keyable=True)
        if cmds.attributeQuery('translationFunction', node=legControlHandle[1], exists=True) and \
                                            cmds.getAttr(legControlHandle[1]+'.translationFunction') == 'local_orientation':
            cmds.xform(legControlHandle_preTransform, worldSpace=True, translation=\
                cmds.xform(ankleJoint, query=True, worldSpace=True, translation=True), rotation=\
                    cmds.xform(ankleJoint, query=True, worldSpace=True, rotation=True))
            legControlAxesInfo = mfunc.returnAxesInfoForFootTransform(legControlHandle[1], foot_vec_dict)
        else:
            cmds.xform(legControlHandle_preTransform, worldSpace=True, translation=\
                cmds.xform(ankleJoint, query=True, worldSpace=True, translation=True))
            cmds.setAttr(legControlHandle[1]+'.rotateOrder', 2)
        cmds.parent(legControlHandle_preTransform, ctrlGrp, absolute=True)

        # Create a parent switch grp for the IK control handle.
        ps_groups = self.createParentSwitchGrpForTransform(legControlHandle[1], True, 1, True)

        # Create and place the foot group transforms for parenting IK handles and set their respective rotation orders.
        heel_grp_preTransform = self.namePrefix + '_heelRoll_preTransform'
        heel_grp = self.namePrefix + '_heelRoll_transform'
        cmds.group(empty=True, name=heel_grp_preTransform)
        cmds.group(empty=True, name=heel_grp)
        cmds.xform(heel_grp_preTransform, worldSpace=True, translation=\
            cmds.xform(heelJoint, query=True, worldSpace=True, translation=True), rotation=\
                cmds.xform(heelJoint, query=True, worldSpace=True, rotation=True))
        cmds.parent(heel_grp_preTransform, legControlHandle[1], absolute=True)
        cmds.parent(heel_grp, heel_grp_preTransform, relative=True)
        cmds.makeIdentity(heel_grp, rotate=True, apply=True)
        heel_grp_axesInfoData = mfunc.returnAxesInfoForFootTransform(heel_grp, foot_vec_dict)
        if heel_grp_axesInfoData['cross'][1] > 0:
            heel_grp_cross_ax_rot_mult = 1
        else:
            heel_grp_cross_ax_rot_mult = -1
        mfunc.setRotationOrderForFootUtilTransform(heel_grp, heel_grp_axesInfoData)

        toeRoll_grp = self.namePrefix + '_toeRoll_transform'
        cmds.group(empty=True, name=toeRoll_grp)
        cmds.xform(toeRoll_grp, worldSpace=True, translation=\
            cmds.xform(toeJoint, query=True, worldSpace=True, translation=True), rotation=\
                cmds.xform(toeJoint, query=True, worldSpace=True, rotation=True))
        cmds.parent(toeRoll_grp, heel_grp, absolute=True)
        cmds.makeIdentity(toeRoll_grp, rotate=True, apply=True)
        toeRoll_grp_axesInfoData = mfunc.returnAxesInfoForFootTransform(toeRoll_grp, foot_vec_dict)
        if toeRoll_grp_axesInfoData['cross'][1] > 0:
            toeRoll_grp_cross_ax_rot_mult = 1
        else:
            toeRoll_grp_cross_ax_rot_mult = -1
        mfunc.setRotationOrderForFootUtilTransform(toeRoll_grp, toeRoll_grp_axesInfoData)

        ballRoll_grp = self.namePrefix + '_ballRoll_transform'
        cmds.group(empty=True, name=ballRoll_grp)
        cmds.xform(ballRoll_grp, worldSpace=True, translation=\
            cmds.xform(ballJoint, query=True, worldSpace=True, translation=True), rotation=\
                cmds.xform(ballJoint, query=True, worldSpace=True, rotation=True))
        cmds.parent(ballRoll_grp, toeRoll_grp, absolute=True)
        cmds.makeIdentity(ballRoll_grp, rotate=True, apply=True)
        ballRoll_grp_axesInfoData = mfunc.returnAxesInfoForFootTransform(toeRoll_grp, foot_vec_dict)
        if ballRoll_grp_axesInfoData['cross'][1] > 0:
            ballRoll_grp_cross_ax_rot_mult = 1
        else:
            ballRoll_grp_cross_ax_rot_mult = -1
        mfunc.setRotationOrderForFootUtilTransform(ballRoll_grp, ballRoll_grp_axesInfoData)

        toeCurl_grp = self.namePrefix + '_toeCurl_transform'
        cmds.group(empty=True, name=toeCurl_grp)
        cmds.xform(toeCurl_grp, worldSpace=True, translation=\
            cmds.xform(ballJoint, query=True, worldSpace=True, translation=True), rotation=\
                cmds.xform(ballJoint, query=True, worldSpace=True, rotation=True))
        cmds.parent(toeCurl_grp, toeRoll_grp, absolute=True)
        cmds.makeIdentity(toeCurl_grp, rotate=True, apply=True)
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

        # Find the world positions for hip, knee and ankle, and then calculate the knee manual pole vector and
        # start position for the no-flip pole vector.
        hip_pos = cmds.xform(hipJoint, query=True, worldSpace=True, translation=True)
        ankle_pos = cmds.xform(ankleJoint, query=True, worldSpace=True, translation=True)
        hip_ankle_mid_pos = eval(cmds.getAttr(self.rootJoint+'.ikSegmentMidPos'))
        knee_pos = cmds.xform(kneeJoint, query=True, worldSpace=True, translation=True)
        ik_pv_offset_pos = mfunc.returnOffsetPositionBetweenTwoVectors(hip_ankle_mid_pos, knee_pos, 2.0)

        hip_knee_vec = map(lambda x,y: x-y, hip_pos, knee_pos)
        hip_ankle_vec = map(lambda x,y: x-y, hip_pos, ankle_pos)
        hip_knee_vec_mag = math.sqrt(reduce(lambda x,y: x+y, [component**2 for component in hip_knee_vec]))
        hip_ankle_vec_mag = math.sqrt(reduce(lambda x,y: x+y, [component**2 for component in hip_ankle_vec]))

        i = 1
        while True:
            ik_pv_pos_knee_vec = map(lambda x,y: x-y, ik_pv_offset_pos, knee_pos)
            ik_pv_pos_knee_mag = math.sqrt(reduce(lambda x,y: x+y, [component**2 for component in ik_pv_pos_knee_vec]))
            if ik_pv_pos_knee_mag > hip_knee_vec_mag:
                break
            else:
                ik_pv_offset_pos = mfunc.returnOffsetPositionBetweenTwoVectors(hip_ankle_mid_pos, knee_pos, 2.0*i)
            i += 1

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
        pv_main_grp = self.namePrefix + '_poleVector_mainGrp'
        cmds.group(empty=True, name=pv_main_grp, parent=ctrlGrp)
        cmds.xform(pv_main_grp, worldSpace=True, translation=\
            cmds.xform(ankleJoint, query=True, worldSpace=True, translation=True))

        # Create the no-flip pole vector transform and offset its position from the foot accordingly.
        kneePVnoFlip_transform = self.namePrefix + '_kneePVnoFlip_handle'
        kneePVnoFlip_preTransform = self.namePrefix + '_kneePVnoFlip_handle_preTransform'
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
        knee_manual_preTransform = self.namePrefix + '_kneeManualPV_handle_preTransform'
        cmds.group(empty=True, name=knee_manual_preTransform, parent=pv_main_grp)

        cmds.xform(knee_manual_preTransform, worldSpace=True, translation=ik_pv_offset_pos)
        knee_manual_transform = objects.load_xhandleShape(self.namePrefix+'_kneeManualPV_handle', self.controlColour, True)
        cmds.setAttr(knee_manual_transform[0]+'.localScaleX', manualPVHandleShapeRadius)
        cmds.setAttr(knee_manual_transform[0]+'.localScaleY', manualPVHandleShapeRadius)
        cmds.setAttr(knee_manual_transform[0]+'.localScaleZ', manualPVHandleShapeRadius)
        cmds.setAttr(knee_manual_transform[0]+'.drawStyle', 3)
        cmds.parent(knee_manual_transform[1], knee_manual_preTransform, relative=True)
        mfunc.lockHideChannelAttrs(knee_manual_transform[1], 's', 'r', 'v', keyable=False, lock=True)

        # Create a parent switch grp for the manual knee pole vector transform.
        ps_groups = self.createParentSwitchGrpForTransform(knee_manual_transform[1], True, 1, True)

        # Calculate the offset position for the foot bank control transform.
        ball_pos = cmds.xform(ballJoint, query=True, worldSpace=True, translation=True)
        heel_pos = cmds.xform(heelJoint, query=True, worldSpace=True, translation=True)
        ball_heel_vec = map(lambda x,y: x-y, ball_pos, heel_pos)
        ball_heel_vec_mag = math.sqrt(reduce(lambda x,y: x+y, [component**2 for component in ball_heel_vec])) * 0.3

        # Create and place the foot bank transform controls.
        bankPivot_1_transform = objects.load_xhandleShape(self.namePrefix+'_footBankPivot_1_handle', self.controlColour, True)
        cmds.setAttr(bankPivot_1_transform[0]+'.localScaleX', manualPVHandleShapeRadius * 0.7)
        cmds.setAttr(bankPivot_1_transform[0]+'.localScaleY', manualPVHandleShapeRadius * 0.7)
        cmds.setAttr(bankPivot_1_transform[0]+'.localScaleZ', manualPVHandleShapeRadius * 0.7)
        cmds.setAttr(bankPivot_1_transform[0]+'.drawStyle', 3)
        mfunc.lockHideChannelAttrs(bankPivot_1_transform[1], 's', 'r', 'v', keyable=False, lock=True)
        cmds.parent(bankPivot_1_transform[1], toeRoll_grp, relative=True)
        cmds.setAttr(bankPivot_1_transform[1]+'.translate'+toeRoll_grp_axesInfoData['cross'][0], ball_heel_vec_mag)

        for axis in ['X', 'Y', 'Z']:
            val = cmds.getAttr(bankPivot_1_transform[1]+'.translate'+axis)
            if not val:
                cmds.setAttr(bankPivot_1_transform[1]+'.translate'+axis, keyable=False, channelBox=False, lock=True)

        bankPivot_2_transform = objects.load_xhandleShape(self.namePrefix+'_footBankPivot_2_handle', self.controlColour, True)
        cmds.setAttr(bankPivot_2_transform[0]+'.localScaleX', manualPVHandleShapeRadius * 0.7)
        cmds.setAttr(bankPivot_2_transform[0]+'.localScaleY', manualPVHandleShapeRadius * 0.7)
        cmds.setAttr(bankPivot_2_transform[0]+'.localScaleZ', manualPVHandleShapeRadius * 0.7)
        cmds.setAttr(bankPivot_2_transform[0]+'.drawStyle', 3)
        mfunc.lockHideChannelAttrs(bankPivot_2_transform[1], 'r', 's', 'v', keyable=False, lock=True)
        cmds.parent(bankPivot_2_transform[1], toeRoll_grp, relative=True)
        cmds.setAttr(bankPivot_2_transform[1]+'.translate'+toeRoll_grp_axesInfoData['cross'][0], ball_heel_vec_mag*-1)

        for axis in ['X', 'Y', 'Z']:
            val = cmds.getAttr(bankPivot_2_transform[1]+'.translate'+axis)
            if not val:
                cmds.setAttr(bankPivot_2_transform[1]+'.translate'+axis, keyable=False, channelBox=False, lock=True)

        # Create the SDKs for knee pole vector control attributes on the leg IK control to drive the pole vector mode.
        containedNodes = []
        pvConstraint = cmds.poleVectorConstraint(kneePVnoFlip_transform, knee_manual_transform[1], legIkNodes[0], \
                                                                                name=legIkNodes[0]+'_poleVectorConstraint')[0]
        for driver, driven in [[0, ik_twist], [1, 0]]:
            cmds.setAttr(legControlHandle[1]+'.Pole_Vector_Mode', driver)
            cmds.setAttr(legIkNodes[0]+'.twist', driven)
            cmds.setDrivenKeyframe(legIkNodes[0]+'.twist', currentDriver=legControlHandle[1]+'.Pole_Vector_Mode')
        for driver, driven_1, driven_2 in [[0, 1, 0], [1, 0, 1]]:
            cmds.setAttr(legControlHandle[1]+'.Pole_Vector_Mode', driver)
            cmds.setAttr(pvConstraint+'.'+kneePVnoFlip_transform+'W0', driven_1)
            cmds.setAttr(pvConstraint+'.'+knee_manual_transform[1]+'W1', driven_2)
            cmds.setAttr(knee_manual_transform[1]+'_preTransform.visibility', driven_2)
            cmds.setDrivenKeyframe(pvConstraint+'.'+kneePVnoFlip_transform+'W0', \
                                                                        currentDriver=legControlHandle[1]+'.Pole_Vector_Mode')
            cmds.setDrivenKeyframe(pvConstraint+'.'+knee_manual_transform[1]+'W1', \
                                                                        currentDriver=legControlHandle[1]+'.Pole_Vector_Mode')
            cmds.setDrivenKeyframe(knee_manual_transform[1]+'_preTransform.visibility', \
                                                                        currentDriver=legControlHandle[1]+'.Pole_Vector_Mode')
        cmds.setAttr(legControlHandle[1]+'.Pole_Vector_Mode', 0)
        kneePVnoFlip_preTransform_axisInfo = mfunc.returnAxesInfoForFootTransform(kneePVnoFlip_preTransform, foot_vec_dict)
        cmds.connectAttr(legControlHandle[1]+'.Knee_Twist', \
                                              kneePVnoFlip_preTransform+'.rotate'+kneePVnoFlip_preTransform_axisInfo['up'][0])

        # Now connect the custom attributes on the leg IK control, with utility nodes, as needed.
        # Also, set the rotation multipliers for the parent transforms for the foot IKs to ensure correct/preferred rotation.
        ballRoll_setRange = cmds.createNode('setRange', name=ballRoll_grp.rpartition('transform')[0]+'setRange', skipSelect=True)
        ballRoll_firstCondition = cmds.createNode('condition', name=ballRoll_grp.rpartition('transform')[0]+'firstCondition',\
                                                                                                              skipSelect=True)
        cmds.setAttr(ballRoll_firstCondition+'.operation', 4)
        ballRoll_secondCondition = cmds.createNode('condition', name=ballRoll_grp.rpartition('transform')[0]+'secondCondition',\
                                                                                                              skipSelect=True)
        cmds.setAttr(ballRoll_secondCondition+'.operation', 2)
        cmds.setAttr(ballRoll_secondCondition+'.colorIfFalseR', 0)
        cmds.connectAttr(legControlHandle[1]+'.Foot_Toe_Straight', ballRoll_setRange+'.oldMaxX')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Toe_Lift', ballRoll_setRange+'.oldMinX')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Toe_Lift', ballRoll_setRange+'.minX')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Roll', ballRoll_setRange+'.valueX')
        cmds.connectAttr(ballRoll_setRange+'.outValueX', ballRoll_firstCondition+'.colorIfFalseR')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Toe_Lift', ballRoll_firstCondition+'.secondTerm')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Roll', ballRoll_firstCondition+'.colorIfTrueR')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Roll', ballRoll_firstCondition+'.firstTerm')
        cmds.connectAttr(ballRoll_firstCondition+'.outColorR', ballRoll_secondCondition+'.firstTerm')
        cmds.connectAttr(ballRoll_firstCondition+'.outColorR', ballRoll_secondCondition+'.colorIfTrueR')
        ballRollCrossAxMultiply = cmds.createNode('multDoubleLinear', \
                                            name=ballRoll_grp.rpartition('transform')[0]+'cross_ax_multiply', skipSelect=True)
        cmds.connectAttr(ballRoll_secondCondition+'.outColorR', ballRollCrossAxMultiply+'.input1')
        cmds.setAttr(ballRollCrossAxMultiply+'.input2', ballRoll_grp_cross_ax_rot_mult)
        cmds.connectAttr(ballRollCrossAxMultiply+'.output', ballRoll_grp+'.rotate'+ballRoll_grp_axesInfoData['cross'][0])

        cmds.connectAttr(legControlHandle[1]+'.Ball_Pivot', ballRoll_grp+'.rotate'+ballRoll_grp_axesInfoData['up'][0])
        containedNodes.extend([ballRoll_setRange, ballRoll_firstCondition, ballRoll_secondCondition, ballRollCrossAxMultiply])

        bankPivot_1_condition = cmds.createNode('condition', \
                                            name=bankPivot_1_transform[1].rpartition('Handle')[0]+'condition', skipSelect=True)
        cmds.setAttr(bankPivot_1_condition+'.colorIfFalseR', 0)
        bankPivot_1_transform_axesInfo = mfunc.returnAxesInfoForFootTransform(bankPivot_1_transform[1], foot_vec_dict)
        val = cmds.getAttr(bankPivot_1_transform[1]+'.translate'+bankPivot_1_transform_axesInfo['cross'][0])
        if val > 0:
            cmds.setAttr(bankPivot_1_condition+'.operation', 4)
        else:
            cmds.setAttr(bankPivot_1_condition+'.operation', 2)
        bankPivot_2_condition = cmds.createNode('condition', name=bankPivot_2_transform[1].rpartition('Handle')[0]+'condition',\
                                                                                                              skipSelect=True)
        cmds.setAttr(bankPivot_2_condition+'.colorIfFalseR', 0)
        bankPivot_2_transform_axesInfo = mfunc.returnAxesInfoForFootTransform(bankPivot_2_transform[1], foot_vec_dict)
        val = cmds.getAttr(bankPivot_2_transform[1]+'.translate'+bankPivot_2_transform_axesInfo['cross'][0])
        if val > 0:
            cmds.setAttr(bankPivot_2_condition+'.operation', 4)
        else:
            cmds.setAttr(bankPivot_2_condition+'.operation', 2)
        bankPivotRest_condition = cmds.createNode('condition', name=re.split('\d+_handle', \
                                                                bankPivot_1_transform[1])[0]+'restCondition', skipSelect=True)
        cmds.setAttr(bankPivotRest_condition+'.colorIfFalseR', 0)
        cmds.setAttr(bankPivotRest_condition+'.colorIfTrueR', 0)
        cmds.setAttr(bankPivotRest_condition+'.operation', 0)
        cmds.connectAttr(legControlHandle[1]+'.Foot_Bank', bankPivotRest_condition+'.firstTerm')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Bank', bankPivot_1_condition+'.firstTerm')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Bank', bankPivot_2_condition+'.firstTerm')
        cmds.connectAttr(bankPivot_1_transform[1]+'.translate'+bankPivot_1_transform_axesInfo['cross'][0], \
                                                                                        bankPivot_1_condition+'.colorIfTrueR')
        cmds.connectAttr(bankPivot_2_transform[1]+'.translate'+bankPivot_2_transform_axesInfo['cross'][0], \
                                                                                        bankPivot_2_condition+'.colorIfTrueR')
        toeRoll_rotCrossAxisPivotPlus = cmds.createNode('plusMinusAverage', \
                name=toeRoll_grp.rpartition('transform')[0]+'rotatePivot'+bankPivot_2_transform_axesInfo['cross'][0]+'Plus', \
                                                                                                              skipSelect=True)
        cmds.connectAttr(bankPivot_1_condition+'.outColorR', toeRoll_rotCrossAxisPivotPlus+'.input1D[0]')
        cmds.connectAttr(bankPivot_2_condition+'.outColorR', toeRoll_rotCrossAxisPivotPlus+'.input1D[1]')
        cmds.connectAttr(bankPivotRest_condition+'.outColorR', toeRoll_rotCrossAxisPivotPlus+'.input1D[2]')
        cmds.connectAttr(toeRoll_rotCrossAxisPivotPlus+'.output1D', toeRoll_grp+'.rotatePivot'+toeRoll_grp_axesInfoData['cross'][0])

        toeRollAimAxMultiply = cmds.createNode('multDoubleLinear', name=toeRoll_grp.rpartition('transform')[0]+'aim_ax_multiply', \
                                                                                                              skipSelect=True)
        cmds.connectAttr(legControlHandle[1]+'.Foot_Bank', toeRollAimAxMultiply+'.input1')
        cmds.setAttr(toeRollAimAxMultiply+'.input2', 1)
        cmds.connectAttr(toeRollAimAxMultiply+'.output', toeRoll_grp+'.rotate'+toeRoll_grp_axesInfoData['aim'][0])

        containedNodes.extend([bankPivot_1_condition, bankPivot_2_condition, bankPivotRest_condition, \
                                                                         toeRoll_rotCrossAxisPivotPlus, toeRollAimAxMultiply])

        toeRoll_setRange = cmds.createNode('setRange', name=toeRoll_grp.rpartition('transform')[0]+'setRange', skipSelect=True)
        toeRoll_firstCondition = cmds.createNode('condition', name=toeRoll_grp.rpartition('transform')[0]+'firstCondition', \
                                                                                                              skipSelect=True)
        cmds.setAttr(toeRoll_firstCondition+'.operation', 2)
        cmds.setAttr(toeRoll_firstCondition+'.colorIfFalseR', 0)
        toeRoll_secondCondition = cmds.createNode('condition', name=toeRoll_grp.rpartition('transform')[0]+'secondCondition', \
                                                                                                              skipSelect=True)
        cmds.setAttr(toeRoll_secondCondition+'.operation', 4)
        toeRoll_thirdCondition = cmds.createNode('condition', name=toeRoll_grp.rpartition('transform')[0]+'thirdCondition', \
                                                                                                              skipSelect=True)
        cmds.setAttr(toeRoll_thirdCondition+'.operation', 5)
        cmds.connectAttr(legControlHandle[1]+'.Foot_Roll', toeRoll_firstCondition+'.colorIfTrueR')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Roll', toeRoll_firstCondition+'.firstTerm')
        cmds.connectAttr(toeRoll_firstCondition+'.outColorR', toeRoll_secondCondition+'.colorIfTrueR')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Roll', toeRoll_secondCondition+'.firstTerm')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Toe_Lift', toeRoll_secondCondition+'.secondTerm')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Roll', toeRoll_secondCondition+'.colorIfFalseR')
        cmds.connectAttr(toeRoll_secondCondition+'.outColorR', toeRoll_setRange+'.valueX')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Toe_Lift', toeRoll_setRange+'.oldMinX')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Toe_Straight', toeRoll_setRange+'.oldMaxX')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Toe_Straight', toeRoll_setRange+'.maxX')
        cmds.connectAttr(toeRoll_setRange+'.outValueX', toeRoll_thirdCondition+'.colorIfTrueR')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Roll', toeRoll_thirdCondition+'.firstTerm')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Toe_Straight', toeRoll_thirdCondition+'.secondTerm')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Roll', toeRoll_thirdCondition+'.colorIfFalseR')

        toeRollCrossAxMultiply = cmds.createNode('multDoubleLinear', \
                                             name=toeRoll_grp.rpartition('transform')[0]+'cross_ax_multiply', skipSelect=True)
        cmds.connectAttr(toeRoll_thirdCondition+'.outColorR', toeRollCrossAxMultiply+'.input1')
        cmds.setAttr(toeRollCrossAxMultiply+'.input2', toeRoll_grp_cross_ax_rot_mult)
        cmds.connectAttr(toeRollCrossAxMultiply+'.output', toeRoll_grp+'.rotate'+toeRoll_grp_axesInfoData['cross'][0])
        cmds.connectAttr(legControlHandle[1]+'.Toe_Pivot', toeRoll_grp+'.rotate'+toeRoll_grp_axesInfoData['up'][0])
        toeCurlCrossAxMultiply = cmds.createNode('multDoubleLinear', \
                                             name=toeCurl_grp.rpartition('transform')[0]+'cross_ax_multiply', skipSelect=True)
        cmds.connectAttr(legControlHandle[1]+'.Toe_Curl', toeCurlCrossAxMultiply+'.input1')
        cmds.setAttr(toeCurlCrossAxMultiply+'.input2', toeCurl_grp_cross_ax_rot_mult)
        cmds.connectAttr(toeCurlCrossAxMultiply+'.output', toeCurl_grp+'.rotate'+toeCurl_grp_axesInfoData['cross'][0])
        cmds.connectAttr(legControlHandle[1]+'.Ball_Pivot', toeCurl_grp+'.rotate'+toeCurl_grp_axesInfoData['up'][0])
        containedNodes.extend([toeRoll_setRange, toeRoll_firstCondition, toeRoll_secondCondition, toeRoll_thirdCondition,
                                                                              toeRollCrossAxMultiply, toeCurlCrossAxMultiply])

        heelRoll_condition = cmds.createNode('condition', name=heel_grp.rpartition('transform')[0]+'condition', skipSelect=True)
        cmds.setAttr(heelRoll_condition+'.operation', 3)
        cmds.setAttr(heelRoll_condition+'.colorIfFalseR', 0)
        cmds.connectAttr(legControlHandle[1]+'.Foot_Roll', heelRoll_condition+'.colorIfTrueR')
        cmds.connectAttr(legControlHandle[1]+'.Foot_Roll', heelRoll_condition+'.secondTerm')
        heelRollCrossAxMultiply = cmds.createNode('multDoubleLinear', \
                                                name=heel_grp.rpartition('transform')[0]+'cross_ax_multiply', skipSelect=True)
        cmds.connectAttr(heelRoll_condition+'.outColorR', heelRollCrossAxMultiply+'.input1')
        cmds.setAttr(heelRollCrossAxMultiply+'.input2', heel_grp_cross_ax_rot_mult)
        cmds.connectAttr(heelRollCrossAxMultiply+'.output', heel_grp+'.rotate'+heel_grp_axesInfoData['cross'][0])
        cmds.connectAttr(legControlHandle[1]+'.Heel_Pivot', heel_grp+'.rotate'+heel_grp_axesInfoData['up'][0])
        containedNodes.extend([heelRoll_condition, heelRollCrossAxMultiply])

        # Apply the stretch functionality.
        cmds.select(clear=True)
        extrasGrp = cmds.group(empty=True, name=self.namePrefix+'_extrasGrp', parent=ctrlGrp)
        hipPosLocator = cmds.spaceLocator(name=self.namePrefix+'_hipPos_loc')[0]
        cmds.setAttr(hipPosLocator+'.visibility', 0)
        cmds.parent(hipPosLocator, extrasGrp, absolute=True)
        cmds.xform(hipPosLocator, worldSpace=True, translation=cmds.xform(hipJoint, query=True, worldSpace=True, \
                                                                                                            translation=True))
        cmds.pointConstraint(hipJoint, hipPosLocator, maintainOffset=True, name=self.namePrefix+'_hipPos_pointConstraint')
        distanceBtwn = cmds.createNode('distanceBetween', name=self.namePrefix+'_hipToAnkle_distance', skipSelect=True)
        cmds.connectAttr(hipPosLocator+'Shape.worldPosition[0]', distanceBtwn+'.point1')
        cmds.connectAttr(legControlHandle[1]+'Shape.worldPosition[0]', distanceBtwn+'.point2')
        restLengthFactor = cmds.createNode('multiplyDivide', name=self.namePrefix+'_hipToAnkle_restLengthFactor', skipSelect=True)
        cmds.connectAttr(self.ch_root_transform+'.globalScale', restLengthFactor+'.input2X')
        cmds.connectAttr(distanceBtwn+'.distance', restLengthFactor+'.input1X')
        cmds.setAttr(restLengthFactor+'.operation', 2)
        jointAxis =  cmds.getAttr(kneeJoint+'.nodeAxes')[0]
        upperLegLengthTranslate = cmds.getAttr(kneeJoint+'.translate'+jointAxis)
        lowerLegLengthTranslate = cmds.getAttr(ankleJoint+'.translate'+jointAxis)
        legLength = upperLegLengthTranslate + lowerLegLengthTranslate
        stretchLengthDivide = cmds.createNode('multiplyDivide', name=self.namePrefix+'_hipToAnkle_stretchLengthDivide', \
                                                                                                                skipSelect=True)
        cmds.setAttr(stretchLengthDivide+'.input2X', abs(legLength), lock=True)
        cmds.setAttr(stretchLengthDivide+'.operation', 2)
        cmds.connectAttr(restLengthFactor+'.outputX', stretchLengthDivide+'.input1X')
        stretchCondition = cmds.createNode('condition', name=self.namePrefix+'_hipToAnkle_stretchCondition', skipSelect=True)
        cmds.setAttr(stretchCondition+'.operation', 2)
        cmds.connectAttr(stretchLengthDivide+'.outputX', stretchCondition+'.colorIfTrueR')
        cmds.connectAttr(stretchLengthDivide+'.input2X', stretchCondition+'.secondTerm')
        cmds.connectAttr(stretchLengthDivide+'.input1X', stretchCondition+'.firstTerm')
        lowerLegTranslateMultiply = cmds.createNode('multDoubleLinear', \
                                                name=self.namePrefix+'_hipToAnkle_lowerLegTranslateMultiply', skipSelect=True)
        cmds.connectAttr(stretchCondition+'.outColorR', lowerLegTranslateMultiply+'.input1')
        cmds.setAttr(lowerLegTranslateMultiply+'.input2', lowerLegLengthTranslate)
        cmds.connectAttr(lowerLegTranslateMultiply+'.output', ankleJoint+'.translate'+jointAxis)
        upperLegTranslateMultiply = cmds.createNode('multDoubleLinear', \
                                                name=self.namePrefix+'_hipToAnkle_upperLegTranslateMultiply', skipSelect=True)
        cmds.connectAttr(stretchCondition+'.outColorR', upperLegTranslateMultiply+'.input1')
        cmds.setAttr(upperLegTranslateMultiply+'.input2', upperLegLengthTranslate)
        cmds.connectAttr(upperLegTranslateMultiply+'.output', kneeJoint+'.translate'+jointAxis)
        containedNodes.extend([extrasGrp, distanceBtwn, restLengthFactor, stretchLengthDivide, stretchCondition,
                                                                        lowerLegTranslateMultiply, upperLegTranslateMultiply])

        # Add the nodes to the control rig container, and then publish the necessary keyable attributes.
        mfunc.addNodesToContainer(ctrl_container, containedNodes+[ctrlGrp], includeHierarchyBelow=True)

        mfunc.updateContainerNodes(ctrl_container)

        # Check and correct the aim and hence the axial rotation of the toeRoll group along the length of the foot.
        bankPivot_1_restPos = cmds.getAttr(bankPivot_1_transform[1]+'Shape.worldPosition')[0]
        rest_mag_bankPivot_hip = mfunc.returnVectorMagnitude(hip_pos, bankPivot_1_restPos)
        toeRoll_grp_aim_ax_rot_mult = 1
        for value in (15, -15):
            cmds.setAttr(legControlHandle[1]+'.Foot_Bank', value)
            bankPivot_1_pos = cmds.getAttr(bankPivot_1_transform[1]+'Shape.worldPosition')[0]
            mag_bankPivot_hip = mfunc.returnVectorMagnitude(hip_pos, bankPivot_1_pos)
            if round(mag_bankPivot_hip, 4) > round(rest_mag_bankPivot_hip, 4):
                cmds.setAttr(toeRollAimAxMultiply+'.input2', -1)
        cmds.setAttr(legControlHandle[1]+'.Foot_Bank', 0)

        legControlAttrs = cmds.listAttr(legControlHandle[1], keyable=True, visible=True, unlocked=True)
        legControlName = legControlHandle[1].partition('__')[2]
        for attr in legControlAttrs:
            if not re.search('Foot_Toe_Straight|Foot_Toe_Lift', attr):
                cmds.container(ctrl_container, edit=True, publishAndBind=[legControlHandle[1]+'.'+attr, legControlName+'_'+attr])
        for axis in ['X', 'Y', 'Z']:
            cmds.container(ctrl_container, edit=True, publishAndBind=[knee_manual_transform[1]+'.translate'+axis, \
                                                                                        'kneePVmanual_control_translate'+axis])
        cmds.setAttr(legControlHandle[1]+'.overrideEnabled', 1)
        cmds.connectAttr('MRT_character'+self.characterName+'_control_rig.visibility', \
                                                                                    legControlHandle[1]+'.overrideVisibility')
        cmds.setAttr(knee_manual_transform[1]+'.overrideEnabled', 1)
        cmds.connectAttr('MRT_character'+self.characterName+'_control_rig.visibility', \
                                                                               knee_manual_transform[1]+'.overrideVisibility')

        # Create a custom keyable attribute on the character root transform by the control name to adjust the weight
        # of the driver joint layer by using the method "createCtrlRigWeightAttributeOnRootTransform".
        self.createCtrlRigWeightAttributeOnRootTransform(self.ctrlAttrPrefix+'_Reverse_IK_Leg_Control_Stretchy', \
                          [legControlHandle[1], bankPivot_1_transform[1], bankPivot_2_transform[1], knee_manual_transform[1]])

        cmds.select(clear=True)


class JointChainControl(BaseJointControl):

    """This hierarchy type is constructed from a joint module consisting of more than two nodes in a linear chain."""


    def __init__(self, characterName, rootJoint):
        BaseJointControl.__init__(self, characterName, rootJoint)


    def applyDynamic_FK_Control(self):

        '''This method creates an FK control joint layer over a selected joint hierarchy and drives it indirectly using a
        second joint layer affected by a dynamic spline IK curve skinned to the first joint layer.'''

        # The dynamic FK control will consist of two sets of joint layers, one which will be used to control a dynamic curve
        # (input curve), which is skinned to it, whose output curve will drive another joint layer, using spline IK, and this
        # joint layer will drive the actual (selected) joint hierarchy.

        # This joint layer will be used as control, and so, we'll set the connectLayer to False
        # (notice the second last argument).
        ctrlJointSet, null, ctrlLayerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                           'Dynamic_FK_Control',
                                                                                            self.characterName,
                                                                                            True,
                                                                                            'On',
                                                                                            True,
                                                                                            self.controlColour,
                                                                                            False)
        # The 'null' is used above since no driver constraints are returned, it's an empty list,
        # since this is not the driver joint layer.

        # Update the naming prefix for the control rig.
        self.namePrefix = self.namePrefix + '_Dynamic_FK_Control'

        # Create a container for the control rig.
        ctrl_container = cmds.createNode('container', name=self.namePrefix+'_Container', skipSelect=True)

        # Get the radius of the shape to be applied to the FK control joints.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.35

        # Create a parent switch group for the root FK control.
        ps_grps = self.createParentSwitchGrpForTransform(ctrlLayerRootJoint, True)

        # Lock the translation and scale attributes of the control joints, and apply shapes to it.
        for joint in ctrlJointSet:
            cmds.setAttr(joint+'.radius', 0)
            mfunc.lockHideChannelAttrs(joint, 't', 's', 'radi', 'v', keyable=False, lock=True)
            xhandle = objects.load_xhandleShape(joint, self.controlColour)
            cmds.setAttr(xhandle[0]+'.localScaleX', shapeRadius)
            cmds.setAttr(xhandle[0]+'.localScaleY', shapeRadius)
            cmds.setAttr(xhandle[0]+'.localScaleZ', shapeRadius)
            cmds.setAttr(xhandle[0]+'.drawStyle', 5)

        # Add the FK control joints and the parent switch group to the control rig container.
        mfunc.addNodesToContainer(ctrl_container, ps_grps, includeHierarchyBelow=True)

        # Publish the rotate attributes for the control joints.
        for joint in ctrlJointSet:
            jointName = re.split('MRT_character%s__'%(self.characterName), joint)[1]
            cmds.container(ctrl_container, edit=True, publishAndBind=[joint+'.rotate', jointName+'_rotate'])

        # Now create the driver joint layer.
        defJointSet, driver_constraints, defLayerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                                      'Dynamic_FK',
                                                                                                       self.characterName,
                                                                                                       False,
                                                                                                       'None',
                                                                                                       True,
                                                                                                       None,
                                                                                                       True)
        # Update the instance attribute for the driver joint layer set.
        self.driverJointLayerSet = defJointSet

        # Update the instance attribute to contain the driver constraints for the joint hiearachy.
        self.driverConstraintsForInput = driver_constraints

        # Add the driver joint layer to the control rig container.
        mfunc.addNodesToContainer(ctrl_container, defJointSet, includeHierarchyBelow=True)

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
            if nodeName.find('MRT_character') == -1:
                nameSeq = re.split('\d+', nodeName)
                name = cmds.rename(node, '%s_driverCurve_%s'%(self.namePrefix, ''.join(nameSeq)))
                skin_nodes.append(name.partition(':')[2])
        cmds.namespace(setNamespace=':')
        cmds.namespace(moveNamespace=[tempNamespaceName, ':'], force=True)
        cmds.namespace(removeNamespace=tempNamespaceName)
        mfunc.addNodesToContainer(ctrl_container, skin_nodes, includeHierarchyBelow=True)
        cmds.select(clear=True)

        # Create a control group node to place all DAG nodes (not part of the character joint hierarchy) under it.
        ctrlGrp = cmds.group(empty=True, name=self.namePrefix + '_Grp', parent='MRT_character%s__controlGrp'%(self.characterName))

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
                cmds.parent(follicle, ':'+ctrlGrp, absolute=True)
                cmds.setAttr(follicle+'.visibility', 0)
            if re.match('^curve\d+$', node):
                dynCurve = cmds.rename(node, self.namePrefix+'_dynCurve')
                cmds.parent(dynCurve, ctrlGrp, absolute=True)
                cmds.setAttr(dynCurve+'.visibility', 0)
            if re.match('^hairSystem\d+$', node):
                hairSystem = cmds.rename(node, self.namePrefix+'_hairSystem')
                cmds.parent(hairSystem, ctrlGrp, absolute=True)
                cmds.setAttr(hairSystem+'.visibility', 0)
            if node.startswith('nucleus'):
                nucleus = cmds.rename(node, self.namePrefix+'_nucleus')
                cmds.parent(nucleus, ctrlGrp, absolute=True)
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
        cmds.parent(defSplineIkHandle, ctrlGrp, absolute=True)
        cmds.setAttr(defSplineIkHandle+'.visibility', 0)

        # Create and place a handle/control for accessing dynamic attributes for the dynamic curve for the spline IK.
        # Add custom attributes to it and connect them.
        colour = self.controlColour - 1
        if self.controlColour < 1:
            colour = self.controlColour + 1
        dynSettingsHandle = objects.load_xhandleShape(self.namePrefix+'_dynSettings_handle', colour, True)
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.32
        cmds.setAttr(dynSettingsHandle[0]+'.localScaleX', shapeRadius)
        cmds.setAttr(dynSettingsHandle[0]+'.localScaleY', shapeRadius)
        cmds.setAttr(dynSettingsHandle[0]+'.localScaleZ', shapeRadius)
        cmds.connectAttr(self.ch_root_transform+'.globalScale', dynSettingsHandle[1]+'.scaleX')
        cmds.connectAttr(self.ch_root_transform+'.globalScale', dynSettingsHandle[1]+'.scaleY')
        cmds.connectAttr(self.ch_root_transform+'.globalScale', dynSettingsHandle[1]+'.scaleZ')
        cmds.setAttr(dynSettingsHandle[0]+'.drawStyle', 2)
        cmds.setAttr(dynSettingsHandle[0]+'.drawStyle', keyable=False, lock=True)
        cmds.xform(dynSettingsHandle[1], worldSpace=True, translation=cmds.xform(defJointSet[1], query=True, worldSpace=True, \
                            translation=True), rotation=cmds.xform(defJointSet[1], query=True, worldSpace=True, rotation=True))
        upAxis = cmds.getAttr(defJointSet[1]+'.nodeAxes')[1]
        translation = {'X':[shapeRadius*10.0, 0, 0], 'Y':[0, shapeRadius*10.0, 0], 'Z':[0, 0, shapeRadius*10.0]}[upAxis]
        cmds.xform(dynSettingsHandle[1], relative=True, translation=translation)
        cmds.parent(dynSettingsHandle[1], ctrlGrp, absolute=True)
        cmds.parentConstraint(defJointSet[1], dynSettingsHandle[1], maintainOffset=True, \
            name='MRT_character%s__%s_Dynamic_FK_dynSettingsHandle_parentConstraint'%(self.characterName, self.userSpecName))
        cmds.setAttr(dynSettingsHandle[1]+'.overrideEnabled', 1)
        cmds.connectAttr('MRT_character'+self.characterName+'_control_rig.visibility', dynSettingsHandle[1]+'.overrideVisibility')
        mfunc.lockHideChannelAttrs(dynSettingsHandle[1], 't', 'r', 's', 'v', keyable=False, lock=True)
        cmds.select(clear=True)
        cmds.addAttr(dynSettingsHandle[1], attributeType='enum', longName='DynamicsSwitch', keyable=True, enumName=':Off:On')
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='iterations', keyable=True, defaultValue=20)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='stiffness', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='stiffnessScale', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='startCurveAttract', keyable=True, defaultValue=1)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='startCurveAttractDamp', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='damping', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='gravity', keyable=True, defaultValue=0.98)
        cmds.addAttr(dynSettingsHandle[1], attributeType='enum', longName='Turbulence', keyable=True, enumName=' ')
        cmds.setAttr(dynSettingsHandle[1]+'.Turbulence', lock=True)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='intensity', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='frequency', keyable=True, defaultValue=0.2)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='speed', keyable=True, defaultValue=0.2)
        for driver, driven in [[0, 0], [1, 2]]:
            cmds.setAttr(dynSettingsHandle[1]+'.DynamicsSwitch', driver)
            cmds.setAttr(follicle+'Shape.simulationMethod', driven)
            cmds.setDrivenKeyframe(follicle+'Shape.simulationMethod', currentDriver=dynSettingsHandle[1]+'.DynamicsSwitch')
        cmds.connectAttr(dynSettingsHandle[1]+'.iterations', hairSystem+'Shape.iterations')
        cmds.connectAttr(dynSettingsHandle[1]+'.stiffness', hairSystem+'Shape.stiffness')
        cmds.connectAttr(dynSettingsHandle[1]+'.stiffnessScale', hairSystem+'Shape.stiffnessScale[0].stiffnessScale_FloatValue')
        cmds.connectAttr(dynSettingsHandle[1]+'.startCurveAttract', hairSystem+'Shape.startCurveAttract')
        cmds.connectAttr(dynSettingsHandle[1]+'.startCurveAttractDamp', hairSystem+'Shape.attractionDamp')
        cmds.connectAttr(dynSettingsHandle[1]+'.damping', hairSystem+'Shape.damp')
        cmds.connectAttr(dynSettingsHandle[1]+'.gravity', hairSystem+'Shape.gravity')
        cmds.connectAttr(dynSettingsHandle[1]+'.intensity', hairSystem+'Shape.turbulenceStrength')
        cmds.connectAttr(dynSettingsHandle[1]+'.frequency', hairSystem+'Shape.turbulenceFrequency')
        cmds.connectAttr(dynSettingsHandle[1]+'.speed', hairSystem+'Shape.turbulenceSpeed')
        cmds.select(clear=True)

        # Add all the rest of the nodes to the control rig container.
        mfunc.addNodesToContainer(ctrl_container, [ctrlGrp], includeHierarchyBelow=True)

        # Create a custom keyable attribute on the character root transform by the control name to adjust the weight of
        # the driver joint layer by using the method "createCtrlRigWeightAttributeOnRootTransform".
        self.createCtrlRigWeightAttributeOnRootTransform(self.ctrlAttrPrefix+'_Dynamic_FK_Control', \
                                                                                            ctrlJointSet+[dynSettingsHandle[1]])
        cmds.select(clear=True)


    def applyDynamic_FK_Control_Stretchy(self):

        '''The control rigging procedure for this method will be the same as 'Dynamic_FK_Control', with added stretch
        functionality to work with the dynamic curve.'''

        # The dynamic FK control will consist of two sets of joint layers, one which will be used to control a dynamic curve
        # (input curve), which is skinned to it, whose output curve
        # will drive another joint layer, using spline IK, and this joint layer will drive the actual (selected) joint hierarchy.

        # This joint layer will be used as control, and so, we'll set the connectLayer to False (notice the second last argument).
        ctrlJointSet, null, ctrlLayerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                          'Dynamic_FK_Control_Stretchy',
                                                                                           self.characterName,
                                                                                           True,
                                                                                           'On',
                                                                                           True,
                                                                                           self.controlColour,
                                                                                           False)
        # The 'null' is used above since no driver constraints are returned, it's an empty list,
        # since this is not the driver joint layer.

        # Update the naming prefix for the control rig.
        self.namePrefix = self.namePrefix + '_Dynamic_FK_Control_Stretchy'

        # Create a container for the control rig.
        ctrl_container = cmds.createNode('container', name=self.namePrefix+'_Container', skipSelect=True)

        # Get the radius of the shape to be applied to the FK control joints.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.35

        # Lock the translation and scale attributes of the control joints, and apply shapes to it.
        for joint in ctrlJointSet:
            cmds.setAttr(joint+'.radius', 0)
            mfunc.lockHideChannelAttrs(joint, 't', 'radi', 'v', keyable=False, lock=True)
            xhandle = objects.load_xhandleShape(joint, self.controlColour)
            cmds.setAttr(xhandle[0]+'.localScaleX', shapeRadius)
            cmds.setAttr(xhandle[0]+'.localScaleY', shapeRadius)
            cmds.setAttr(xhandle[0]+'.localScaleZ', shapeRadius)
            cmds.setAttr(xhandle[0]+'.drawStyle', 5)
            cmds.setAttr(xhandle[0]+'.transformScaling', 0)
            cmds.connectAttr(self.ch_root_transform+'.globalScale', xhandle[0]+'.addScaleX')
            cmds.connectAttr(self.ch_root_transform+'.globalScale', xhandle[0]+'.addScaleY')
            cmds.connectAttr(self.ch_root_transform+'.globalScale', xhandle[0]+'.addScaleZ')

        # Create a parent switch group for the root FK control.
        ps_grps = self.createParentSwitchGrpForTransform(ctrlLayerRootJoint, True)

        # Add the FK control joints and the parent switch group to the control rig container.
        mfunc.addNodesToContainer(ctrl_container, ps_grps, includeHierarchyBelow=True)

        # Publish the rotate attributes for the control joints.
        for joint in ctrlJointSet:
            jointName = re.split('MRT_character%s__'%(self.characterName), joint)[1]
            cmds.container(ctrl_container, edit=True, publishAndBind=[joint+'.rotate', jointName+'_rotate'])

        # Now create the driver joint layer.
        defJointSet, driver_constraints, defLayerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                                      'Dynamic_FK_Stretchy',
                                                                                                       self.characterName,
                                                                                                       False,
                                                                                                       'None',
                                                                                                       True,
                                                                                                       None,
                                                                                                       True)
        # Update the instance attribute for the driver joint layer set.
        self.driverJointLayerSet = defJointSet

        # Update the instance attribute to contain the driver constraints for the joint hiearachy.
        self.driverConstraintsForInput = driver_constraints

        # Add the driver joint layer to the control rig container.
        mfunc.addNodesToContainer(ctrl_container, defJointSet, includeHierarchyBelow=True)

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
            if nodeName.find('MRT_character') == -1:
                nameSeq = re.split('\d+', nodeName)
                name = cmds.rename(node, '%s_driverCurve_%s'%(self.namePrefix, ''.join(nameSeq)))
                skin_nodes.append(name.partition(':')[2])
        cmds.namespace(setNamespace=':')
        cmds.namespace(moveNamespace=[tempNamespaceName, ':'], force=True)
        cmds.namespace(removeNamespace=tempNamespaceName)
        mfunc.addNodesToContainer(ctrl_container, skin_nodes, includeHierarchyBelow=True)
        cmds.select(clear=True)

        # Create a control group node to place all DAG nodes (not part of the character joint hierarchy) under it.
        ctrlGrp = cmds.group(empty=True, name=self.namePrefix + '_Grp', parent='MRT_character%s__controlGrp'%(self.characterName))

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
                cmds.parent(follicle, ':'+ctrlGrp, absolute=True)
                cmds.setAttr(follicle+'.visibility', 0)
            if re.match('^curve\d+$', node):
                dynCurve = cmds.rename(node, self.namePrefix+'_dynCurve')
                cmds.parent(dynCurve, ctrlGrp, absolute=True)
                cmds.setAttr(dynCurve+'.visibility', 0)
            if re.match('^hairSystem\d+$', node):
                hairSystem = cmds.rename(node, self.namePrefix+'_hairSystem')
                cmds.parent(hairSystem, ctrlGrp, absolute=True)
                cmds.setAttr(hairSystem+'.visibility', 0)
            if node.startswith('nucleus'):
                nucleus = cmds.rename(node, self.namePrefix+'_nucleus')
                cmds.parent(nucleus, ctrlGrp, absolute=True)
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
        cmds.parent(defSplineIkHandle, ctrlGrp, absolute=True)
        cmds.setAttr(defSplineIkHandle+'.visibility', 0)

        # Connect the scale attributes between the control and driver joint layers.
        for ctlJoint, defJoint in zip(ctrlJointSet, defJointSet):
            cmds.connectAttr(ctlJoint+'.scale', defJoint+'.scale')

        # Create and place a handle/control for accessing dynamic attributes for the dynamic curve for the spline IK.
        # Add custom attributes to it and connect them.
        colour = self.controlColour - 1
        if self.controlColour < 1:
            colour = self.controlColour + 1
        dynSettingsHandle = objects.load_xhandleShape(self.namePrefix+'_dynSettings_handle', colour, True)
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.32
        cmds.setAttr(dynSettingsHandle[0]+'.localScaleX', shapeRadius)
        cmds.setAttr(dynSettingsHandle[0]+'.localScaleY', shapeRadius)
        cmds.setAttr(dynSettingsHandle[0]+'.localScaleZ', shapeRadius)
        cmds.connectAttr(self.ch_root_transform+'.globalScale', dynSettingsHandle[1]+'.scaleX')
        cmds.connectAttr(self.ch_root_transform+'.globalScale', dynSettingsHandle[1]+'.scaleY')
        cmds.connectAttr(self.ch_root_transform+'.globalScale', dynSettingsHandle[1]+'.scaleZ')
        cmds.setAttr(dynSettingsHandle[0]+'.drawStyle', 2)
        cmds.setAttr(dynSettingsHandle[0]+'.drawStyle', keyable=False, lock=True)
        cmds.xform(dynSettingsHandle[1], worldSpace=True, translation=\
            cmds.xform(defJointSet[1], query=True, worldSpace=True, translation=True), rotation=\
                cmds.xform(defJointSet[1], query=True, worldSpace=True, rotation=True))
        upAxis = cmds.getAttr(defJointSet[1]+'.nodeAxes')[1]
        translation = {'X':[shapeRadius*10.0, 0, 0], 'Y':[0, shapeRadius*10.0, 0], 'Z':[0, 0, shapeRadius*10.0]}[upAxis]
        cmds.xform(dynSettingsHandle[1], relative=True, translation=translation)
        cmds.parent(dynSettingsHandle[1], ctrlGrp, absolute=True)
        cmds.parentConstraint(defJointSet[1], dynSettingsHandle[1], maintainOffset=True, \
            name='MRT_character%s__%s_Dynamic_FK_dynSettingsHandle_parentConstraint'%(self.characterName, self.userSpecName))
        cmds.setAttr(dynSettingsHandle[1]+'.overrideEnabled', 1)
        cmds.connectAttr('MRT_character'+self.characterName+'_control_rig.visibility', dynSettingsHandle[1]+'.overrideVisibility')
        mfunc.lockHideChannelAttrs(dynSettingsHandle[1], 't', 'r', 's', 'v', keyable=False, lock=True)
        cmds.select(clear=True)
        cmds.addAttr(dynSettingsHandle[1], attributeType='enum', longName='DynamicsSwitch', keyable=True, enumName=':Off:On')
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='iterations', keyable=True, defaultValue=20)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='stiffness', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='stiffnessScale', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='startCurveAttract', keyable=True, defaultValue=1)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='startCurveAttractDamp', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='damping', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='gravity', keyable=True, defaultValue=0.98)
        cmds.addAttr(dynSettingsHandle[1], attributeType='enum', longName='Turbulence', keyable=True, enumName=' ')
        cmds.setAttr(dynSettingsHandle[1]+'.Turbulence', lock=True)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='intensity', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='frequency', keyable=True, defaultValue=0.2)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='speed', keyable=True, defaultValue=0.2)
        for driver, driven in [[0, 0], [1, 2]]:
            cmds.setAttr(dynSettingsHandle[1]+'.DynamicsSwitch', driver)
            cmds.setAttr(follicle+'Shape.simulationMethod', driven)
            cmds.setDrivenKeyframe(follicle+'Shape.simulationMethod', currentDriver=dynSettingsHandle[1]+'.DynamicsSwitch')
        cmds.connectAttr(dynSettingsHandle[1]+'.iterations', hairSystem+'Shape.iterations')
        cmds.connectAttr(dynSettingsHandle[1]+'.stiffness', hairSystem+'Shape.stiffness')
        cmds.connectAttr(dynSettingsHandle[1]+'.stiffnessScale', hairSystem+'Shape.stiffnessScale[0].stiffnessScale_FloatValue')
        cmds.connectAttr(dynSettingsHandle[1]+'.startCurveAttract', hairSystem+'Shape.startCurveAttract')
        cmds.connectAttr(dynSettingsHandle[1]+'.startCurveAttractDamp', hairSystem+'Shape.attractionDamp')
        cmds.connectAttr(dynSettingsHandle[1]+'.damping', hairSystem+'Shape.damp')
        cmds.connectAttr(dynSettingsHandle[1]+'.gravity', hairSystem+'Shape.gravity')
        cmds.connectAttr(dynSettingsHandle[1]+'.intensity', hairSystem+'Shape.turbulenceStrength')
        cmds.connectAttr(dynSettingsHandle[1]+'.frequency', hairSystem+'Shape.turbulenceFrequency')
        cmds.connectAttr(dynSettingsHandle[1]+'.speed', hairSystem+'Shape.turbulenceSpeed')
        cmds.select(clear=True)

        # Add all the rest of the nodes to the control rig container.
        mfunc.addNodesToContainer(ctrl_container, [ctrlGrp], includeHierarchyBelow=True)

        # Create a custom keyable attribute on the character root transform by the control name to adjust the weight
        # of the driver joint layer by using the method "createCtrlRigWeightAttributeOnRootTransform".
        self.createCtrlRigWeightAttributeOnRootTransform(self.ctrlAttrPrefix+'_Dynamic_FK_Control_Stretchy', \
                                                                                            ctrlJointSet+[dynSettingsHandle[1]])
        cmds.select(clear=True)


    def applyDynamic_End_IK_Control(self):

        '''This method applies an IK control transform at the end position of the selected joint hierarchy on a joint layer
        to drive it indirectly using another joint layer driven using a dynamic spline IK curve which is skinned to the 
        first joint layer.'''

        # This control will consist of two joint layers on top of the selected joint hierarchy. The first layer will have
        # an IK control at its end joint position, with a dynamic curve skinned to it, whose output curve will drive the
        # splineIK for the next joint layer which will drive the joint hierarchy.

        # Create the first joint layer, to be used with an RP IK.
        ctrlJointSet, null, ctrlLayerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                          'Dynamic_End_IK_Control',
                                                                                           self.characterName,
                                                                                           False,
                                                                                           'None',
                                                                                           True,
                                                                                           None,
                                                                                           False)
        # Update the naming prefix for the control rig.
        self.namePrefix = self.namePrefix + '_Dynamic_End_IK_Control'

        # Create a container for the control rig.
        ctrl_container = cmds.createNode('container', name=self.namePrefix+'_Container', skipSelect=True)

        # Add the control layer joints (to be used with RP IK) to the control rig container.
        mfunc.addNodesToContainer(ctrl_container, ctrlJointSet, includeHierarchyBelow=True)

        # Create the driver joint layer.
        defJointSet, driver_constraints, defLayerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                                      'Dynamic_End_IK',
                                                                                                       self.characterName,
                                                                                                       False,
                                                                                                       'None',
                                                                                                       True,
                                                                                                       None,
                                                                                                       True)
        # Update the instance attribute for the driver joint layer set.
        self.driverJointLayerSet = defJointSet

        # Update the instance attribute to contain the driver constraints for the joint hiearachy.
        self.driverConstraintsForInput = driver_constraints

        # Add the driver joint layer to the control rig container.
        mfunc.addNodesToContainer(ctrl_container, defJointSet, includeHierarchyBelow=True)

        # Create a control group node to place all DAG nodes (not part of the character joint hierarchy) under it.
        ctrlGrp = cmds.group(empty=True, name=self.namePrefix + '_Grp', \
                                                                    parent='MRT_character%s__controlGrp'%(self.characterName))

        # Create the RP IK on the first joint layer.
        ctrlIkHandleNodes = cmds.ikHandle(startJoint=ctrlLayerRootJoint, endEffector=ctrlJointSet[1], solver='ikRPsolver')
        ctrlIkHandle = cmds.rename(ctrlIkHandleNodes[0], self.namePrefix+'_driverIkHandle')
        cmds.setAttr(ctrlIkHandle+'.rotateOrder', 3)
        ctrlIkEffector = cmds.rename(ctrlIkHandleNodes[1], self.namePrefix+'_driverIkEffector')
        cmds.parent(ctrlIkHandle, ctrlGrp, absolute=True)
        cmds.setAttr(ctrlIkHandle+'.visibility', 0)

        # Create the end IK control with its pre-transform and position it.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.88
        controlPreTransform = cmds.group(empty=True, name=self.namePrefix + '_handle_preTransform')
        cmds.setAttr(controlPreTransform+'.rotateOrder', 3)
        if self.transOriFunc == 'local_orientation':
            tempConstraint = cmds.parentConstraint(ctrlJointSet[1], controlPreTransform, maintainOffset=False)
        if self.transOriFunc == 'world':
            tempConstraint = cmds.pointConstraint(ctrlJointSet[1], controlPreTransform, maintainOffset=False)
        cmds.delete(tempConstraint)
        controlHandle = objects.load_xhandleShape(self.namePrefix+'_handle', self.controlColour, True)
        cmds.setAttr(controlHandle[0]+'.localScaleX', shapeRadius)
        cmds.setAttr(controlHandle[0]+'.localScaleY', shapeRadius)
        cmds.setAttr(controlHandle[0]+'.localScaleZ', shapeRadius)
        cmds.setAttr(controlHandle[0]+'.drawStyle', 6)
        cmds.setAttr(controlHandle[1]+'.rotateOrder', 3)
        cmds.parent(controlHandle[1], controlPreTransform, relative=True)
        cmds.makeIdentity(controlHandle[1], translate=True, rotate=True, apply=True)
        cmds.pointConstraint(controlHandle[1], ctrlIkHandle, maintainOffset=False, name=controlHandle[1]+'_pointConstraint')
        cmds.addAttr(controlHandle[1], attributeType='float', longName='IK_Twist', defaultValue=0, keyable=True)
        cmds.connectAttr(controlHandle[1]+'.IK_Twist', ctrlIkHandle+'.twist')
        cmds.setAttr(controlHandle[1]+'.overrideEnabled', 1)
        cmds.connectAttr('MRT_character'+self.characterName+'_control_rig.visibility', controlHandle[1]+'.overrideVisibility')
        mfunc.lockHideChannelAttrs(controlHandle[1], 'r', 's', 'v', keyable=False, lock=True)
        cmds.parent(controlPreTransform, ctrlGrp, absolute=True)
        cmds.select(clear=True)

        # Create a parent switch group for the end IK control handle.
        ps_groups = self.createParentSwitchGrpForTransform(controlHandle[1], True, 1, True)

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
            if nodeName.find('MRT_character') == -1:
                nameSeq = re.split('\d+', nodeName)
                name = cmds.rename(node, '%s_driverCurve_%s'%(self.namePrefix, ''.join(nameSeq)))
                skin_nodes.append(name.partition(':')[2])
        cmds.namespace(setNamespace=':')
        cmds.namespace(moveNamespace=[tempNamespaceName, ':'], force=True)
        cmds.namespace(removeNamespace=tempNamespaceName)
        mfunc.addNodesToContainer(ctrl_container, skin_nodes, includeHierarchyBelow=True)
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
                cmds.parent(follicle, ':'+ctrlGrp, absolute=True)
                cmds.setAttr(follicle+'.visibility', 0)
            if re.match('^curve\d+$', node):
                dynCurve = cmds.rename(node, self.namePrefix+'_dynCurve')
                cmds.parent(dynCurve, ctrlGrp, absolute=True)
                cmds.setAttr(dynCurve+'.visibility', 0)
            if re.match('^hairSystem\d+$', node):
                hairSystem = cmds.rename(node, self.namePrefix+'_hairSystem')
                cmds.parent(hairSystem, ctrlGrp, absolute=True)
                cmds.setAttr(hairSystem+'.visibility', 0)
            if node.startswith('nucleus'):
                nucleus = cmds.rename(node, self.namePrefix+'_nucleus')
                cmds.parent(nucleus, ctrlGrp, absolute=True)
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
        cmds.parent(defSplineIkHandle, ctrlGrp, absolute=True)
        cmds.setAttr(defSplineIkHandle+'.visibility', 0)

        # Create and position the pole vector handle for the RP IK on the control joint layer.
        pvHandle = objects.load_xhandleShape(self.namePrefix+'_PV_handle', self.controlColour, True)
        cmds.setAttr(pvHandle[0]+'.localScaleX', shapeRadius*0.5)
        cmds.setAttr(pvHandle[0]+'.localScaleY', shapeRadius*0.5)
        cmds.setAttr(pvHandle[0]+'.localScaleZ', shapeRadius*0.5)
        cmds.setAttr(pvHandle[0]+'.drawStyle', 3)
        cmds.xform(pvHandle[1], worldSpace=True, translation=\
            cmds.xform(ctrlLayerRootJoint, query=True, worldSpace=True, translation=True))
        cmds.makeIdentity(pvHandle[1], translate=True, apply=True)
        cmds.setAttr(pvHandle[1]+'.overrideEnabled', 1)
        cmds.connectAttr('MRT_character'+self.characterName+'_control_rig.visibility', pvHandle[1]+'.overrideVisibility')
        pvPos = cmds.getAttr(ctrlIkHandle+'.poleVector')[0]
        cmds.setAttr(pvHandle[1]+'.translate', pvPos[0], pvPos[1], pvPos[2], type='double3')
        ctrlLayerRootJointparent = cmds.listRelatives(ctrlLayerRootJoint, parent=True, type='joint')[0]
        cmds.parent(pvHandle[1], ctrlLayerRootJointparent, absolute=True)
        cmds.makeIdentity(pvHandle[1], translate=True, rotate=True, scale=True, apply=True)
        mfunc.lockHideChannelAttrs(pvHandle[1], 'r', 's', 'v', keyable=False, lock=True)
        cmds.poleVectorConstraint(pvHandle[1], ctrlIkHandle, name=pvHandle[1]+'_poleVectorConstraint')

        # Create and place a handle/control for accessing dynamic attributes for the driver curve for the spline IK.
        # Add custom attributes to it and connect them.
        colour = self.controlColour - 1
        if self.controlColour < 1:
            colour = self.controlColour + 1
        dynSettingsHandle = objects.load_xhandleShape(self.namePrefix+'_dynSettings_handle', colour, True)
        dynHandleShapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.32
        cmds.setAttr(dynSettingsHandle[0]+'.localScaleX', dynHandleShapeRadius)
        cmds.setAttr(dynSettingsHandle[0]+'.localScaleY', dynHandleShapeRadius)
        cmds.setAttr(dynSettingsHandle[0]+'.localScaleZ', dynHandleShapeRadius)
        cmds.connectAttr(self.ch_root_transform+'.globalScale', dynSettingsHandle[1]+'.scaleX')
        cmds.connectAttr(self.ch_root_transform+'.globalScale', dynSettingsHandle[1]+'.scaleY')
        cmds.connectAttr(self.ch_root_transform+'.globalScale', dynSettingsHandle[1]+'.scaleZ')
        cmds.setAttr(dynSettingsHandle[0]+'.drawStyle', 2)
        cmds.xform(dynSettingsHandle[1], worldSpace=True, translation=\
            cmds.xform(defJointSet[1], query=True, worldSpace=True, translation=True), rotation=\
                cmds.xform(defJointSet[1], query=True, worldSpace=True, rotation=True))
        upAxis = cmds.getAttr(defJointSet[1]+'.nodeAxes')[1]
        translation = {'X':[shapeRadius*6.5, 0, 0], 'Y':[0, shapeRadius*6.5, 0], 'Z':[0, 0, shapeRadius*6.5]}[upAxis]
        cmds.xform(dynSettingsHandle[1], relative=True, translation=translation)
        cmds.parent(dynSettingsHandle[1], ctrlGrp, absolute=True)
        cmds.parentConstraint(defJointSet[1], dynSettingsHandle[1], maintainOffset=True, name=defJointSet[1]+'_parentConstraint')
        cmds.setAttr(dynSettingsHandle[1]+'.overrideEnabled', 1)
        cmds.connectAttr('MRT_character'+self.characterName+'_control_rig.visibility', dynSettingsHandle[1]+'.overrideVisibility')
        mfunc.lockHideChannelAttrs(dynSettingsHandle[1], 't', 'r', 's', 'v', keyable=False, lock=True)
        cmds.select(clear=True)
        cmds.addAttr(dynSettingsHandle[1], attributeType='enum', longName='DynamicsSwitch', keyable=True, enumName=':Off:On')
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='iterations', keyable=True, defaultValue=20)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='stiffness', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='stiffnessScale', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='startCurveAttract', keyable=True, defaultValue=1)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='startCurveAttractDamp', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='damping', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='gravity', keyable=True, defaultValue=0.98)
        cmds.addAttr(dynSettingsHandle[1], attributeType='enum', longName='Turbulence', keyable=True, enumName=' ')
        cmds.setAttr(dynSettingsHandle[1]+'.Turbulence', lock=True)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='intensity', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='frequency', keyable=True, defaultValue=0.2)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='speed', keyable=True, defaultValue=0.2)
        for driver, driven in [[0, 0], [1, 2]]:
            cmds.setAttr(dynSettingsHandle[1]+'.DynamicsSwitch', driver)
            cmds.setAttr(follicle+'Shape.simulationMethod', driven)
            cmds.setDrivenKeyframe(follicle+'Shape.simulationMethod', currentDriver=dynSettingsHandle[1]+'.DynamicsSwitch')
        cmds.connectAttr(dynSettingsHandle[1]+'.iterations', hairSystem+'Shape.iterations')
        cmds.connectAttr(dynSettingsHandle[1]+'.stiffness', hairSystem+'Shape.stiffness')
        cmds.connectAttr(dynSettingsHandle[1]+'.stiffnessScale', hairSystem+'Shape.stiffnessScale[0].stiffnessScale_FloatValue')
        cmds.connectAttr(dynSettingsHandle[1]+'.startCurveAttract', hairSystem+'Shape.startCurveAttract')
        cmds.connectAttr(dynSettingsHandle[1]+'.startCurveAttractDamp', hairSystem+'Shape.attractionDamp')
        cmds.connectAttr(dynSettingsHandle[1]+'.damping', hairSystem+'Shape.damp')
        cmds.connectAttr(dynSettingsHandle[1]+'.gravity', hairSystem+'Shape.gravity')
        cmds.connectAttr(dynSettingsHandle[1]+'.intensity', hairSystem+'Shape.turbulenceStrength')
        cmds.connectAttr(dynSettingsHandle[1]+'.frequency', hairSystem+'Shape.turbulenceFrequency')
        cmds.connectAttr(dynSettingsHandle[1]+'.speed', hairSystem+'Shape.turbulenceSpeed')
        cmds.select(clear=True)

        # Add all the rest of the nodes to the control rig container and publish necessary attributes.
        mfunc.addNodesToContainer(ctrl_container, [ctrlGrp, pvHandle[1]], includeHierarchyBelow=True)
        cmds.container(ctrl_container, edit=True, publishAndBind=[pvHandle[1]+'.translate', 'dynamicEndIk_pvHandle_translate'])
        cmds.container(ctrl_container, edit=True, publishAndBind=[controlHandle[1]+'.translate', 'Dynamic_End_IK_Control_translate'])
        cmds.container(ctrl_container, edit=True, publishAndBind=[controlHandle[1]+'.IK_Twist', 'Dynamic_End_IK_Control_ik_twist'])

        # Create a custom keyable attribute on the character root transform by the control name to adjust the weight of the
        # driver joint layer by using the method "createCtrlRigWeightAttributeOnRootTransform".
        self.createCtrlRigWeightAttributeOnRootTransform(self.ctrlAttrPrefix+'_Dynamic_End_IK_Control', \
                                                                        [controlHandle[1], pvHandle[1], dynSettingsHandle[1]])
        cmds.select(clear=True)


    def applyDynamic_End_IK_Control_Stretchy(self):

        '''The control rigging procedure for this method will be the same as 'Dynamic_End_IK_Control', with added
        stretch functionality to work with the dynamic curve.'''

        # This control will consist of two joint layers on top of the selected joint hierarchy. The first layer will
        # have an IK control at its end joint position, with a dynamic curve skinned to it,
        # whose output curve will drive the splineIK for the next joint layer which will drive the joint hierarchy.

        # Create the first joint layer, to be used with an RP IK.
        ctrlJointSet, null, ctrlLayerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                          'Dynamic_End_IK_Control_Stretchy',
                                                                                          self.characterName,
                                                                                          False,
                                                                                          'None',
                                                                                          True,
                                                                                          None,
                                                                                          False)
        # Update the naming prefix for the control rig.
        self.namePrefix = self.namePrefix + '_Dynamic_End_IK_Control_Stretchy'

        # Create a container for the control rig.
        ctrl_container = cmds.createNode('container', name=self.namePrefix+'_Container', skipSelect=True)

        # Add the control layer joints (to be used with RP IK) to the control rig container.
        mfunc.addNodesToContainer(ctrl_container, ctrlJointSet, includeHierarchyBelow=True)

        # Create the driver joint layer.
        defJointSet, driver_constraints, defLayerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                                    'Dynamic_End_IK_Stretchy',
                                                                                                    self.characterName,
                                                                                                    False,
                                                                                                    'None',
                                                                                                    True,
                                                                                                    None,
                                                                                                    True)
        # Update the instance attribute for the driver joint layer set.
        self.driverJointLayerSet = defJointSet

        # Update the instance attribute to contain the driver constraints for the joint hiearachy.
        self.driverConstraintsForInput = driver_constraints

        # Add the driver joint layer to the control rig container.
        mfunc.addNodesToContainer(ctrl_container, defJointSet, includeHierarchyBelow=True)

        # Create a control group node to place all DAG nodes (not part of the character joint hierarchy) under it.
        ctrlGrp = cmds.group(empty=True, name=self.namePrefix + '_Grp', parent='MRT_character%s__controlGrp'%(self.characterName))

        # Create the RP IK on the first joint layer.
        ctrlIkHandleNodes = cmds.ikHandle(startJoint=ctrlLayerRootJoint, endEffector=ctrlJointSet[1], solver='ikRPsolver')
        ctrlIkHandle = cmds.rename(ctrlIkHandleNodes[0], self.namePrefix+'_driverIkHandle')
        cmds.setAttr(ctrlIkHandle+'.rotateOrder', 3)
        ctrlIkEffector = cmds.rename(ctrlIkHandleNodes[1], self.namePrefix+'_driverIkEffector')
        cmds.parent(ctrlIkHandle, ctrlGrp, absolute=True)
        cmds.setAttr(ctrlIkHandle+'.visibility', 0)

        # Create the end IK control with its pre-transform and position it.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.88
        controlPreTransform = cmds.group(empty=True, name=self.namePrefix + '_handle_preTransform')
        cmds.setAttr(controlPreTransform+'.rotateOrder', 3)
        if self.transOriFunc == 'local_orientation':
            tempConstraint = cmds.parentConstraint(ctrlJointSet[1], controlPreTransform, maintainOffset=False)
        if self.transOriFunc == 'world':
            tempConstraint = cmds.pointConstraint(ctrlJointSet[1], controlPreTransform, maintainOffset=False)
        cmds.delete(tempConstraint)
        controlHandle = objects.load_xhandleShape(self.namePrefix+'_handle', self.controlColour, True)
        cmds.setAttr(controlHandle[0]+'.localScaleX', shapeRadius)
        cmds.setAttr(controlHandle[0]+'.localScaleY', shapeRadius)
        cmds.setAttr(controlHandle[0]+'.localScaleZ', shapeRadius)
        cmds.setAttr(controlHandle[0]+'.drawStyle', 6)
        cmds.setAttr(controlHandle[1]+'.rotateOrder', 3)
        cmds.parent(controlHandle[1], controlPreTransform, relative=True)
        cmds.makeIdentity(controlHandle[1], translate=True, rotate=True, apply=True)
        cmds.pointConstraint(controlHandle[1], ctrlIkHandle, maintainOffset=False, name=controlHandle[1]+'_pointConstraint')
        cmds.addAttr(controlHandle[1], attributeType='float', longName='IK_Twist', defaultValue=0, keyable=True)
        cmds.connectAttr(controlHandle[1]+'.IK_Twist', ctrlIkHandle+'.twist')
        cmds.setAttr(controlHandle[1]+'.overrideEnabled', 1)
        cmds.connectAttr('MRT_character'+self.characterName+'_control_rig.visibility', controlHandle[1]+'.overrideVisibility')
        mfunc.lockHideChannelAttrs(controlHandle[1], 'r', 's', 'v', keyable=False, lock=True)
        cmds.parent(controlPreTransform, ctrlGrp, absolute=True)
        cmds.select(clear=True)

        # Create a parent switch group for the end IK control handle.
        ps_groups = self.createParentSwitchGrpForTransform(controlHandle[1], True, 1, True)

        # Add the stretch functionality.
        ctrlRootJointPosLocator = cmds.spaceLocator(name=self.namePrefix+'_rootJointPos_loc')[0]
        cmds.setAttr(ctrlRootJointPosLocator+'.visibility', 0)
        cmds.parent(ctrlRootJointPosLocator, ctrlGrp, absolute=True)
        cmds.pointConstraint(ctrlLayerRootJoint, ctrlRootJointPosLocator, maintainOffset=False, \
                                                                                    name=ctrlLayerRootJoint+'_pointConstraint')
        distNode = cmds.createNode('distanceBetween', name=self.namePrefix+'_distance', skipSelect=True)
        cmds.connectAttr(ctrlRootJointPosLocator+'Shape.worldPosition[0]', distNode+'.point1')
        cmds.connectAttr(controlHandle[1]+'Shape.worldPosition[0]', distNode+'.point2')
        restLengthFactor = cmds.createNode('multiplyDivide', name=self.namePrefix+'_restLengthFactor', skipSelect=True)
        cmds.connectAttr(self.ch_root_transform+'.globalScale', restLengthFactor+'.input2X')
        cmds.connectAttr(distNode+'.distance', restLengthFactor+'.input1X')
        cmds.setAttr(restLengthFactor+'.operation', 2)
        jointAxis = cmds.getAttr(ctrlLayerRootJoint+'.nodeAxes')[0]
        stretchLengthDivide = cmds.createNode('multiplyDivide', name=self.namePrefix+'_stretchLengthDivide', skipSelect=True)
        legLength = 0.0
        for joint in ctrlJointSet[1:]:
            legLength += cmds.getAttr(joint+'.translate'+jointAxis)
        cmds.setAttr(stretchLengthDivide+'.input2X', abs(legLength), lock=True)
        cmds.setAttr(stretchLengthDivide+'.operation', 2)
        cmds.connectAttr(restLengthFactor+'.outputX', stretchLengthDivide+'.input1X')
        stretchCondition = cmds.createNode('condition', name=self.namePrefix+'_stretchCondition', skipSelect=True)
        cmds.setAttr(stretchCondition+'.operation', 2)
        cmds.connectAttr(stretchLengthDivide+'.outputX', stretchCondition+'.colorIfTrueR')
        cmds.connectAttr(stretchLengthDivide+'.input2X', stretchCondition+'.secondTerm')
        cmds.connectAttr(stretchLengthDivide+'.input1X', stretchCondition+'.firstTerm')
        cmds.connectAttr(stretchCondition+'.outColorR', ctrlLayerRootJoint+'.scale'+jointAxis)
        for joint in ctrlJointSet[2:]:
            cmds.connectAttr(stretchCondition+'.outColorR', joint+'.scale'+jointAxis)
        mfunc.addNodesToContainer(ctrl_container, [distNode, restLengthFactor, stretchLengthDivide, stretchCondition], \
                                                                                                  includeHierarchyBelow=True)

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
            if nodeName.find('MRT_character') == -1:
                nameSeq = re.split('\d+', nodeName)
                name = cmds.rename(node, '%s_driverCurve_%s'%(self.namePrefix, ''.join(nameSeq)))
                skin_nodes.append(name.partition(':')[2])
        cmds.namespace(setNamespace=':')
        cmds.namespace(moveNamespace=[tempNamespaceName, ':'], force=True)
        cmds.namespace(removeNamespace=tempNamespaceName)
        mfunc.addNodesToContainer(ctrl_container, skin_nodes, includeHierarchyBelow=True)
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
                cmds.parent(follicle, ':'+ctrlGrp, absolute=True)
                cmds.setAttr(follicle+'.visibility', 0)
            if re.match('^curve\d+$', node):
                dynCurve = cmds.rename(node, self.namePrefix+'_dynCurve')
                cmds.parent(dynCurve, ctrlGrp, absolute=True)
                cmds.setAttr(dynCurve+'.visibility', 0)
            if re.match('^hairSystem\d+$', node):
                hairSystem = cmds.rename(node, self.namePrefix+'_hairSystem')
                cmds.parent(hairSystem, ctrlGrp, absolute=True)
                cmds.setAttr(hairSystem+'.visibility', 0)
            if node.startswith('nucleus'):
                nucleus = cmds.rename(node, self.namePrefix+'_nucleus')
                cmds.parent(nucleus, ctrlGrp, absolute=True)
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

        # Connect the scale attributes between the control and driver joint layers.
        for ctlJoint, defJoint in zip(ctrlJointSet, defJointSet):
            cmds.connectAttr(ctlJoint+'.scale', defJoint+'.scale')

        # Create the spline IK using the driver curve's dynamic output curve on the driver joint layer.
        defSplineIkHandleNodes = cmds.ikHandle(startJoint=defLayerRootJoint, endEffector=defJointSet[1], \
                                               solver='ikSplineSolver', createCurve=False, simplifyCurve=False, \
                                                                    rootOnCurve=False, parentCurve=False, curve=dynCurve)
        defSplineIkHandle = cmds.rename(defSplineIkHandleNodes[0], self.namePrefix+'_drivenSplineIkHandle')
        defSplineIkEffector = cmds.rename(defSplineIkHandleNodes[1], self.namePrefix+'_drivenSplineIkEffector')
        cmds.parent(defSplineIkHandle, ctrlGrp, absolute=True)
        cmds.setAttr(defSplineIkHandle+'.visibility', 0)

        # Create and position the pole vector handle for the RP IK on the control joint layer.
        pvHandle = objects.load_xhandleShape(self.namePrefix+'_PV_handle', self.controlColour, True)
        cmds.setAttr(pvHandle[0]+'.localScaleX', shapeRadius*0.5)
        cmds.setAttr(pvHandle[0]+'.localScaleY', shapeRadius*0.5)
        cmds.setAttr(pvHandle[0]+'.localScaleZ', shapeRadius*0.5)
        cmds.setAttr(pvHandle[0]+'.drawStyle', 3)
        cmds.xform(pvHandle[1], worldSpace=True, translation=\
            cmds.xform(ctrlLayerRootJoint, query=True, worldSpace=True, translation=True))
        cmds.makeIdentity(pvHandle[1], translate=True, apply=True)
        cmds.setAttr(pvHandle[1]+'.overrideEnabled', 1)
        cmds.connectAttr('MRT_character'+self.characterName+'_control_rig.visibility', pvHandle[1]+'.overrideVisibility')
        pvPos = cmds.getAttr(ctrlIkHandle+'.poleVector')[0]
        cmds.setAttr(pvHandle[1]+'.translate', pvPos[0], pvPos[1], pvPos[2], type='double3')
        ctrlLayerRootJointparent = cmds.listRelatives(ctrlLayerRootJoint, parent=True, type='joint')[0]
        cmds.parent(pvHandle[1], ctrlLayerRootJointparent, absolute=True)
        cmds.makeIdentity(pvHandle[1], translate=True, rotate=True, scale=True, apply=True)
        mfunc.lockHideChannelAttrs(pvHandle[1], 'r', 's', 'v', keyable=False, lock=True)
        cmds.poleVectorConstraint(pvHandle[1], ctrlIkHandle, name=pvHandle[1]+'_poleVectorConstraint')

        # Create and place a handle/control for accessing dynamic attributes for the driver curve for the spline IK.
        # Add custom attributes to it and connect them.
        colour = self.controlColour - 1
        if self.controlColour < 1:
            colour = self.controlColour + 1
        dynSettingsHandle = objects.load_xhandleShape(self.namePrefix+'_dynSettings_handle', colour, True)
        dynHandleShapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.32
        cmds.setAttr(dynSettingsHandle[0]+'.localScaleX', dynHandleShapeRadius)
        cmds.setAttr(dynSettingsHandle[0]+'.localScaleY', dynHandleShapeRadius)
        cmds.setAttr(dynSettingsHandle[0]+'.localScaleZ', dynHandleShapeRadius)
        cmds.connectAttr(self.ch_root_transform+'.globalScale', dynSettingsHandle[1]+'.scaleX')
        cmds.connectAttr(self.ch_root_transform+'.globalScale', dynSettingsHandle[1]+'.scaleY')
        cmds.connectAttr(self.ch_root_transform+'.globalScale', dynSettingsHandle[1]+'.scaleZ')
        cmds.setAttr(dynSettingsHandle[0]+'.drawStyle', 2)
        cmds.xform(dynSettingsHandle[1], worldSpace=True, translation=\
            cmds.xform(defJointSet[1], query=True, worldSpace=True, translation=True), rotation=\
                cmds.xform(defJointSet[1], query=True, worldSpace=True, rotation=True))
        upAxis = cmds.getAttr(defJointSet[1]+'.nodeAxes')[1]
        translation = {'X':[shapeRadius*6.5, 0, 0], 'Y':[0, shapeRadius*6.5, 0], 'Z':[0, 0, shapeRadius*6.5]}[upAxis]
        cmds.xform(dynSettingsHandle[1], relative=True, translation=translation)
        cmds.parent(dynSettingsHandle[1], ctrlGrp, absolute=True)
        cmds.parentConstraint(defJointSet[1], dynSettingsHandle[1], maintainOffset=True, name=defJointSet[1]+'_parentConstraint')
        cmds.setAttr(dynSettingsHandle[1]+'.overrideEnabled', 1)
        cmds.connectAttr('MRT_character'+self.characterName+'_control_rig.visibility', dynSettingsHandle[1]+'.overrideVisibility')
        mfunc.lockHideChannelAttrs(dynSettingsHandle[1], 't', 'r', 's', 'v', keyable=False, lock=True)
        cmds.select(clear=True)
        cmds.addAttr(dynSettingsHandle[1], attributeType='enum', longName='DynamicsSwitch', keyable=True, enumName=':Off:On')
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='iterations', keyable=True, defaultValue=20)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='stiffness', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='stiffnessScale', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='startCurveAttract', keyable=True, defaultValue=1)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='startCurveAttractDamp', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='damping', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='gravity', keyable=True, defaultValue=0.98)
        cmds.addAttr(dynSettingsHandle[1], attributeType='enum', longName='Turbulence', keyable=True, enumName=' ')
        cmds.setAttr(dynSettingsHandle[1]+'.Turbulence', lock=True)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='intensity', keyable=True, defaultValue=0)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='frequency', keyable=True, defaultValue=0.2)
        cmds.addAttr(dynSettingsHandle[1], attributeType='float', longName='speed', keyable=True, defaultValue=0.2)
        for driver, driven in [[0, 0], [1, 2]]:
            cmds.setAttr(dynSettingsHandle[1]+'.DynamicsSwitch', driver)
            cmds.setAttr(follicle+'Shape.simulationMethod', driven)
            cmds.setDrivenKeyframe(follicle+'Shape.simulationMethod', currentDriver=dynSettingsHandle[1]+'.DynamicsSwitch')
        cmds.connectAttr(dynSettingsHandle[1]+'.iterations', hairSystem+'Shape.iterations')
        cmds.connectAttr(dynSettingsHandle[1]+'.stiffness', hairSystem+'Shape.stiffness')
        cmds.connectAttr(dynSettingsHandle[1]+'.stiffnessScale', hairSystem+'Shape.stiffnessScale[0].stiffnessScale_FloatValue')
        cmds.connectAttr(dynSettingsHandle[1]+'.startCurveAttract', hairSystem+'Shape.startCurveAttract')
        cmds.connectAttr(dynSettingsHandle[1]+'.startCurveAttractDamp', hairSystem+'Shape.attractionDamp')
        cmds.connectAttr(dynSettingsHandle[1]+'.damping', hairSystem+'Shape.damp')
        cmds.connectAttr(dynSettingsHandle[1]+'.gravity', hairSystem+'Shape.gravity')
        cmds.connectAttr(dynSettingsHandle[1]+'.intensity', hairSystem+'Shape.turbulenceStrength')
        cmds.connectAttr(dynSettingsHandle[1]+'.frequency', hairSystem+'Shape.turbulenceFrequency')
        cmds.connectAttr(dynSettingsHandle[1]+'.speed', hairSystem+'Shape.turbulenceSpeed')
        cmds.select(clear=True)

        # Add all the rest of the nodes to the control rig container and publish necessary attributes.
        mfunc.addNodesToContainer(ctrl_container, [ctrlGrp, pvHandle[1]], includeHierarchyBelow=True)
        cmds.container(ctrl_container, edit=True, publishAndBind=\
                                                        [pvHandle[1]+'.translate', 'dynamicEndIk_pvHandle_translate'])
        cmds.container(ctrl_container, edit=True, publishAndBind=\
                                                        [controlHandle[1]+'.translate', 'Dynamic_End_IK_Control_translate'])
        cmds.container(ctrl_container, edit=True, publishAndBind=\
                                                        [controlHandle[1]+'.IK_Twist', 'Dynamic_End_IK_Control_ik_twist'])

        # Create a custom keyable attribute on the character root transform by the control name to adjust the
        # weight of the driver joint layer by using the method "createCtrlRigWeightAttributeOnRootTransform".
        self.createCtrlRigWeightAttributeOnRootTransform(self.ctrlAttrPrefix+'_Dynamic_End_IK_Control_Stretchy', \
                                                                        [controlHandle[1], pvHandle[1], dynSettingsHandle[1]])
        cmds.select(clear=True)


class HingeControl(BaseJointControl):

    """This hierarchy type is constructed from a hinge module with three nodes, and can be applied with a rotate
    plane IK control. This hierarchy is useful where the middle joint acts as a hinge as it can only rotate in an 
    axis with a preferred and limited direction of rotation."""


    def __init__(self, characterName, rootJoint):
        BaseJointControl.__init__(self, characterName, rootJoint)


    def applyIK_Control(self):

        '''Create a simple rotate plane IK control.'''

        # We'll create a single driver joint layer with an IK RP solver on it.
        jointSet, driver_constraints, layerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                                 'IK_Control',
                                                                                                 self.characterName,
                                                                                                 False,
                                                                                                 'None',
                                                                                                 True,
                                                                                                 None,
                                                                                                 True)
        # Update the naming prefix for the control rig.
        self.namePrefix = self.namePrefix + '_IK_Control'

        # Update the instance attribute for the driver joint layer set.
        self.driverJointLayerSet = jointSet

        # Update the instance attribute to contain the driver constraints for the joint hiearachy.
        self.driverConstraintsForInput = driver_constraints

        # Create a container for the control rig.
        ctrl_container = cmds.createNode('container', name=self.namePrefix+'_Container', skipSelect=True)

        # Add the control layer joints (to be used with RP IK) to the control rig ocntainer.
        mfunc.addNodesToContainer(ctrl_container, jointSet, includeHierarchyBelow=True)

        # Create a control group node to place all DAG nodes (not part of the character joint hierarchy) under it.
        ctrlGrp = cmds.group(empty=True, name=self.namePrefix + '_Grp', \
                                                                   parent='MRT_character%s__controlGrp'%(self.characterName))

        # Create the IK RP solver on the joint layer.
        ctrlIkHandleNodes = cmds.ikHandle(startJoint=layerRootJoint, endEffector=jointSet[1], solver='ikRPsolver')
        ctrlIkHandle = cmds.rename(ctrlIkHandleNodes[0], self.namePrefix+'_driverIkHandle')
        cmds.setAttr(ctrlIkHandle+'.rotateOrder', 3)
        ctrlIkEffector = cmds.rename(ctrlIkHandleNodes[1], self.namePrefix+'_driverIkEffector')
        cmds.parent(ctrlIkHandle, ctrlGrp, absolute=True)
        cmds.setAttr(ctrlIkHandle+'.visibility', 0)

        # Create the IK control with its pre-transform and position it.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.88
        controlPreTransform = cmds.group(empty=True, name=self.namePrefix + '_handle_preTransform')
        cmds.setAttr(controlPreTransform+'.rotateOrder', 3)
        if self.transOriFunc == 'local_orientation':
            tempConstraint = cmds.parentConstraint(jointSet[1], controlPreTransform, maintainOffset=False)
        if self.transOriFunc == 'world':
            tempConstraint = cmds.pointConstraint(jointSet[1], controlPreTransform, maintainOffset=False)
        cmds.delete(tempConstraint)
        controlHandle = objects.load_xhandleShape(self.namePrefix+'_handle', self.controlColour, True)
        cmds.setAttr(controlHandle[0]+'.localScaleX', shapeRadius)
        cmds.setAttr(controlHandle[0]+'.localScaleY', shapeRadius)
        cmds.setAttr(controlHandle[0]+'.localScaleZ', shapeRadius)
        cmds.setAttr(controlHandle[0]+'.drawStyle', 6)
        cmds.setAttr(controlHandle[1]+'.rotateOrder', 3)
        cmds.parent(controlHandle[1], controlPreTransform, relative=True)
        cmds.makeIdentity(controlHandle[1], translate=True, rotate=True, apply=True)
        cmds.pointConstraint(controlHandle[1], ctrlIkHandle, maintainOffset=False, name=controlHandle[1]+'_pointConstraint')
        cmds.orientConstraint(controlHandle[1], jointSet[1], maintainOffset=True, name=controlHandle[1]+'_orientConstraint')
        cmds.setAttr(controlHandle[1]+'.overrideEnabled', 1)
        cmds.connectAttr('MRT_character'+self.characterName+'_control_rig.visibility', controlHandle[1]+'.overrideVisibility')
        cmds.setAttr(controlHandle[1]+'.scaleX', keyable=False, lock=True)
        cmds.setAttr(controlHandle[1]+'.scaleY', keyable=False, lock=True)
        cmds.setAttr(controlHandle[1]+'.scaleZ', keyable=False, lock=True)
        cmds.setAttr(controlHandle[1]+'.visibility', keyable=False)
        cmds.parent(controlPreTransform, ctrlGrp, absolute=True)
        cmds.select(clear=True)

        # Create a parent switch group for the IK control handle.
        ps_groups = self.createParentSwitchGrpForTransform(controlHandle[1], True, 1, True)

        # Calculate the position for the IK pole vector control.
        shldr_pos = cmds.xform(layerRootJoint, query=True, worldSpace=True, translation=True)
        wrist_pos = cmds.xform(jointSet[1], query=True, worldSpace=True, translation=True)
        arm_mid_pos = eval(cmds.getAttr(self.rootJoint+'.ikSegmentMidPos'))
        elbow_pos = cmds.xform(jointSet[2], query=True, worldSpace=True, translation=True)
        ik_pv_offset_pos = mfunc.returnOffsetPositionBetweenTwoVectors(elbow_pos, arm_mid_pos, -2)

        # Create and position the IK pole vector control.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.32
        elbow_pv_preTransform = cmds.group(empty=True, name=self.namePrefix + '_elbowPV_handle_preTransform')
        cmds.xform(elbow_pv_preTransform, worldSpace=True, translation=ik_pv_offset_pos)
        elbow_pv_transform = objects.load_xhandleShape(self.namePrefix+'_elbowPV_handle', self.controlColour, True)
        cmds.setAttr(elbow_pv_transform[0]+'.localScaleX', shapeRadius)
        cmds.setAttr(elbow_pv_transform[0]+'.localScaleY', shapeRadius)
        cmds.setAttr(elbow_pv_transform[0]+'.localScaleZ', shapeRadius)
        cmds.setAttr(elbow_pv_transform[0]+'.drawStyle', 3)
        mfunc.lockHideChannelAttrs(elbow_pv_transform[1], 'r', 's', 'v', keyable=False, lock=True)
        cmds.parent(elbow_pv_transform[1], elbow_pv_preTransform, relative=True)
        cmds.parent(elbow_pv_preTransform, ctrlGrp, absolute=True)
        cmds.poleVectorConstraint(elbow_pv_transform[1], ctrlIkHandle, name=elbow_pv_transform[1]+'_poleVectorConstraint')

        # Create a parent switch group for pole vector control handle.
        ps_groups = self.createParentSwitchGrpForTransform(elbow_pv_transform[1], True, 1, True)

        # Add all the rest of the nodes to the control rig container and publish necessary attributes.
        mfunc.addNodesToContainer(ctrl_container, [controlPreTransform, ctrlGrp, elbow_pv_transform[1]], \
                                                                                                includeHierarchyBelow=True)
        cmds.container(ctrl_container, edit=True, publishAndBind=\
                                                      [elbow_pv_transform[1]+'.translate', 'ik_elbowPV_control_translate'])
        cmds.container(ctrl_container, edit=True, publishAndBind=\
                                                      [controlHandle[1]+'.translate', 'ik_control_translate'])
        cmds.container(ctrl_container, edit=True, publishAndBind=\
                                                      [controlHandle[1]+'.rotate', 'ik_control_rotate'])

        # Create a custom keyable attribute on the character root transform by the control name to adjust
        # the weight of the driver joint layer by using the method "createCtrlRigWeightAttributeOnRootTransform".
        self.createCtrlRigWeightAttributeOnRootTransform(self.ctrlAttrPrefix+'_IK_Control', \
                                                                                [controlHandle[1], elbow_pv_transform[1]])
        cmds.select(clear=True)


    def applyIK_Control_Stretchy(self):

        '''Create a simple rotate plane IK control with stretch functionality.'''

        # Update the naming prefix for the control rig.
        self.namePrefix = self.namePrefix + '_IK_Control_Stretchy'

        # We'll create a single driver joint layer with an IK RP solver on it.
        jointSet, driver_constraints, layerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                                 'IK_Control_Stretchy',
                                                                                                 self.characterName,
                                                                                                 False,
                                                                                                 'None',
                                                                                                 True,
                                                                                                 None,
                                                                                                 True)
        # Update the instance attribute for the driver joint layer set.
        self.driverJointLayerSet = jointSet

        # Update the instance attribute to contain the driver constraints for the joint hiearachy.
        self.driverConstraintsForInput = driver_constraints

        # Create a container for the control rig.
        ctrl_container = cmds.createNode('container', name=self.namePrefix+'_Container', skipSelect=True)

        # Add the control layer joints (to be used with RP IK) to the control rig ocntainer.
        mfunc.addNodesToContainer(ctrl_container, jointSet, includeHierarchyBelow=True)

        # Create a control group node to place all DAG nodes (not part of the character joint hierarchy) under it.
        ctrlGrp = cmds.group(empty=True, name=self.namePrefix + '_Grp', \
                                                                parent='MRT_character%s__controlGrp'%(self.characterName))

        # Create the IK RP solver on the joint layer.
        ctrlIkHandleNodes = cmds.ikHandle(startJoint=layerRootJoint, endEffector=jointSet[1], solver='ikRPsolver')
        ctrlIkHandle = cmds.rename(ctrlIkHandleNodes[0], self.namePrefix+'_driverIkHandle')
        cmds.setAttr(ctrlIkHandle+'.rotateOrder', 3)
        ctrlIkEffector = cmds.rename(ctrlIkHandleNodes[1], self.namePrefix+'_driverIkEffector')
        cmds.parent(ctrlIkHandle, ctrlGrp, absolute=True)
        cmds.setAttr(ctrlIkHandle+'.visibility', 0)

        # Create the IK control with its pre-transform and position it.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.88
        controlPreTransform = cmds.group(empty=True, name=self.namePrefix + '_handle_preTransform')
        cmds.setAttr(controlPreTransform+'.rotateOrder', 3)
        if self.transOriFunc == 'local_orientation':
            tempConstraint = cmds.parentConstraint(jointSet[1], controlPreTransform, maintainOffset=False)
        if self.transOriFunc == 'world':
            tempConstraint = cmds.pointConstraint(jointSet[1], controlPreTransform, maintainOffset=False)
        cmds.delete(tempConstraint)
        controlHandle = objects.load_xhandleShape(self.namePrefix+'_handle', self.controlColour, True)
        cmds.setAttr(controlHandle[0]+'.localScaleX', shapeRadius)
        cmds.setAttr(controlHandle[0]+'.localScaleY', shapeRadius)
        cmds.setAttr(controlHandle[0]+'.localScaleZ', shapeRadius)
        cmds.setAttr(controlHandle[0]+'.drawStyle', 6)
        cmds.setAttr(controlHandle[1]+'.rotateOrder', 3)
        cmds.parent(controlHandle[1], controlPreTransform, relative=True)
        cmds.makeIdentity(controlHandle[1], translate=True, rotate=True, apply=True)
        cmds.pointConstraint(controlHandle[1], ctrlIkHandle, maintainOffset=False, name=controlHandle[1]+'_pointConstraint')
        cmds.orientConstraint(controlHandle[1], jointSet[1], maintainOffset=True, name=controlHandle[1]+'_orientConstraint')
        cmds.setAttr(controlHandle[1]+'.overrideEnabled', 1)
        cmds.connectAttr('MRT_character'+self.characterName+'_control_rig.visibility', controlHandle[1]+'.overrideVisibility')
        mfunc.lockHideChannelAttrs(controlHandle[1], 's', 'v', keyable=False, lock=True)
        cmds.parent(controlPreTransform, ctrlGrp, absolute=True)
        cmds.select(clear=True)

        # Create a parent switch group for the IK control handle.
        ps_groups = self.createParentSwitchGrpForTransform(controlHandle[1], True, 1, True)

        # Calculate the position for the IK pole vector control.
        shldr_pos = cmds.xform(layerRootJoint, query=True, worldSpace=True, translation=True)
        wrist_pos = cmds.xform(jointSet[1], query=True, worldSpace=True, translation=True)
        arm_mid_pos = eval(cmds.getAttr(self.rootJoint+'.ikSegmentMidPos'))
        elbow_pos = cmds.xform(jointSet[2], query=True, worldSpace=True, translation=True)
        ik_pv_offset_pos = mfunc.returnOffsetPositionBetweenTwoVectors(elbow_pos, arm_mid_pos, -2)

        # Create and position the IK pole vector control.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.32
        elbow_pv_preTransform = cmds.group(empty=True, name=self.namePrefix + '_elbowPV_handle_preTransform')
        cmds.xform(elbow_pv_preTransform, worldSpace=True, translation=ik_pv_offset_pos)
        elbow_pv_transform = objects.load_xhandleShape(self.namePrefix+'_elbowPV_handle', self.controlColour, True)
        cmds.setAttr(elbow_pv_transform[0]+'.localScaleX', shapeRadius)
        cmds.setAttr(elbow_pv_transform[0]+'.localScaleY', shapeRadius)
        cmds.setAttr(elbow_pv_transform[0]+'.localScaleZ', shapeRadius)
        cmds.setAttr(elbow_pv_transform[0]+'.drawStyle', 3)
        mfunc.lockHideChannelAttrs(elbow_pv_transform[1], 'r', 's', 'v', keyable=False, lock=True)
        cmds.parent(elbow_pv_transform[1], elbow_pv_preTransform, relative=True)
        cmds.parent(elbow_pv_preTransform, ctrlGrp, absolute=True)
        cmds.poleVectorConstraint(elbow_pv_transform[1], ctrlIkHandle, name=elbow_pv_transform[1]+'_poleVectorConstraint')

        # Create a parent switch group for pole vector control handle.
        ps_groups = self.createParentSwitchGrpForTransform(elbow_pv_transform[1], True, 1, True)

        # Add the stretch functionality.
        shldrPosLocator = cmds.spaceLocator(name=self.namePrefix+'_shldrPos_loc')[0]
        cmds.setAttr(shldrPosLocator+'.visibility', 0)
        cmds.parent(shldrPosLocator, ctrlGrp, absolute=True)
        cmds.pointConstraint(layerRootJoint, shldrPosLocator, maintainOffset=False, name=layerRootJoint+'_pointConstraint')
        distanceBtwn = cmds.createNode('distanceBetween', name=self.namePrefix+'_shldrToWrist_distance', skipSelect=True)
        cmds.connectAttr(shldrPosLocator+'Shape.worldPosition[0]', distanceBtwn+'.point1')
        cmds.connectAttr(controlHandle[1]+'Shape.worldPosition[0]', distanceBtwn+'.point2')
        restLengthFactor = cmds.createNode('multiplyDivide', name=self.namePrefix+'_shldrToWrist_restLengthFactor', \
                                                                                                            skipSelect=True)
        cmds.connectAttr(self.ch_root_transform+'.globalScale', restLengthFactor+'.input2X')
        cmds.connectAttr(distanceBtwn+'.distance', restLengthFactor+'.input1X')
        cmds.setAttr(restLengthFactor+'.operation', 2)
        jointAxis =  cmds.getAttr(layerRootJoint+'.nodeAxes')[0]
        upperArmLengthTranslate = cmds.getAttr(jointSet[2]+'.translate'+jointAxis)
        lowerArmLengthTranslate = cmds.getAttr(jointSet[1]+'.translate'+jointAxis)
        armLength = upperArmLengthTranslate + lowerArmLengthTranslate
        stretchLengthDivide = cmds.createNode('multiplyDivide', name=self.namePrefix+'_shldrToWrist_stretchLengthDivide', \
                                                                                                            skipSelect=True)
        cmds.setAttr(stretchLengthDivide+'.input2X', abs(armLength), lock=True)
        cmds.setAttr(stretchLengthDivide+'.operation', 2)
        cmds.connectAttr(restLengthFactor+'.outputX', stretchLengthDivide+'.input1X')
        stretchCondition = cmds.createNode('condition', name=self.namePrefix+'_shldrToWrist_stretchCondition', \
                                                                                                            skipSelect=True)
        cmds.setAttr(stretchCondition+'.operation', 2)
        cmds.connectAttr(stretchLengthDivide+'.outputX', stretchCondition+'.colorIfTrueR')
        cmds.connectAttr(stretchLengthDivide+'.input2X', stretchCondition+'.secondTerm')
        cmds.connectAttr(stretchLengthDivide+'.input1X', stretchCondition+'.firstTerm')
        lowerArmTranslateMultiply = cmds.createNode('multDoubleLinear', \
                                            name=self.namePrefix+'_shldrToWrist_lowerArmTranslateMultiply', skipSelect=True)
        cmds.connectAttr(stretchCondition+'.outColorR', lowerArmTranslateMultiply+'.input1')
        cmds.setAttr(lowerArmTranslateMultiply+'.input2', lowerArmLengthTranslate)
        cmds.connectAttr(lowerArmTranslateMultiply+'.output', jointSet[1]+'.translate'+jointAxis)
        upperArmTranslateMultiply = cmds.createNode('multDoubleLinear', \
                                            name=self.namePrefix+'_shldrToWrist_upperArmTranslateMultiply', skipSelect=True)
        cmds.connectAttr(stretchCondition+'.outColorR', upperArmTranslateMultiply+'.input1')
        cmds.setAttr(upperArmTranslateMultiply+'.input2', upperArmLengthTranslate)
        cmds.connectAttr(upperArmTranslateMultiply+'.output', jointSet[2]+'.translate'+jointAxis)

        # Add all the rest of the nodes to the control rig container and publish necessary attributes.
        mfunc.addNodesToContainer(ctrl_container, [controlPreTransform, ctrlGrp, elbow_pv_transform[1], distanceBtwn,   \
                                                   restLengthFactor, stretchLengthDivide, stretchCondition, \
                                                   lowerArmTranslateMultiply, upperArmTranslateMultiply],   \
                                                   includeHierarchyBelow=True)
        cmds.container(ctrl_container, edit=True, publishAndBind=\
                                                    [elbow_pv_transform[1]+'.translate', 'ik_elbowPV_control_translate'])
        cmds.container(ctrl_container, edit=True, publishAndBind=[controlHandle[1]+'.translate', 'ik_control_translate'])
        cmds.container(ctrl_container, edit=True, publishAndBind=[controlHandle[1]+'.rotate', 'ik_control_rotate'])

        # Create a custom keyable attribute on the character root transform by the control name to adjust the weight
        # of the driver joint layer by using the method "createCtrlRigWeightAttributeOnRootTransform".
        self.createCtrlRigWeightAttributeOnRootTransform(self.ctrlAttrPrefix+'_IK_Control_Stretchy', \
                                                                                [controlHandle[1], elbow_pv_transform[1]])
        cmds.select(clear=True)


    def applyIK_Control_Stretchy_With_Elbow_Control(self):

        '''Create a simple rotate plane IK control with stretch functionality to work with the IK transform control
        as well with the pole vector transform (in elbow mode).'''

        # We'll create a single driver joint layer with an IK RP solver on it.
        jointSet, driver_constraints, layerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                    'IK_Control_Stretchy_With_Elbow_Control',
                                                                                     self.characterName,
                                                                                     False,
                                                                                     'None',
                                                                                     True,
                                                                                     None,
                                                                                     True)
        # Update the naming prefix for the control rig.
        self.namePrefix = self.namePrefix + '_IK_Control_Stretchy_With_Elbow_Control'

        # Update the instance attribute for the driver joint layer set.
        self.driverJointLayerSet = jointSet

        # Update the instance attribute to contain the driver constraints for the joint hiearachy.
        self.driverConstraintsForInput = driver_constraints

        # Create a container for the control rig.
        ctrl_container = cmds.createNode('container', name=self.namePrefix+'_Container', skipSelect=True)

        # Add the control layer joints (to be used with RP IK) to the control rig ocntainer.
        mfunc.addNodesToContainer(ctrl_container, jointSet, includeHierarchyBelow=True)

        # Create a control group node to place all DAG nodes (not part of the character joint hierarchy) under it.
        ctrlGrp = cmds.group(empty=True, name=self.namePrefix + '_Grp', \
                                                                parent='MRT_character%s__controlGrp'%(self.characterName))

        # Create the IK RP solver on the joint layer.
        ctrlIkHandleNodes = cmds.ikHandle(startJoint=layerRootJoint, endEffector=jointSet[1], solver='ikRPsolver')
        ctrlIkHandle = cmds.rename(ctrlIkHandleNodes[0], self.namePrefix+'_driverIkHandle')
        cmds.setAttr(ctrlIkHandle+'.rotateOrder', 3)
        ctrlIkEffector = cmds.rename(ctrlIkHandleNodes[1], self.namePrefix+'_driverIkEffector')
        cmds.parent(ctrlIkHandle, ctrlGrp, absolute=True)
        cmds.setAttr(ctrlIkHandle+'.visibility', 0)

        # Prep the parent transform for IK control to be used to control it while in elbow FK mode.
        elbowFKTransform = cmds.group(empty=True, name=self.namePrefix+'_elbowFKTransform', parent=ctrlGrp)
        cmds.xform(elbowFKTransform, worldSpace=True, translation=cmds.xform(jointSet[1], query=True, worldSpace=True, \
                                                                                                        translation=True))

        # Create the IK control with its pre-transform and position it.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.88
        controlPreTransform = cmds.group(empty=True, name=self.namePrefix + '_handle_preTransform', parent=elbowFKTransform)
        cmds.setAttr(controlPreTransform+'.rotateOrder', 3)
        if self.transOriFunc == 'local_orientation':
            tempConstraint = cmds.parentConstraint(jointSet[1], controlPreTransform, maintainOffset=False)
        if self.transOriFunc == 'world':
            tempConstraint = cmds.pointConstraint(jointSet[1], controlPreTransform, maintainOffset=False)
        cmds.delete(tempConstraint)
        controlHandle = objects.load_xhandleShape(self.namePrefix+'_handle', self.controlColour, True)
        cmds.setAttr(controlHandle[0]+'.localScaleX', shapeRadius)
        cmds.setAttr(controlHandle[0]+'.localScaleY', shapeRadius)
        cmds.setAttr(controlHandle[0]+'.localScaleZ', shapeRadius)
        cmds.setAttr(controlHandle[0]+'.drawStyle', 6)
        cmds.setAttr(controlHandle[1]+'.rotateOrder', 3)
        cmds.parent(controlHandle[1], controlPreTransform, relative=True)
        cmds.makeIdentity(controlHandle[1], translate=True, rotate=True, apply=True)
        cmds.pointConstraint(controlHandle[1], ctrlIkHandle, maintainOffset=False, name=controlHandle[1]+'_pointConstraint')
        cmds.orientConstraint(controlHandle[1], jointSet[1], maintainOffset=True, name=controlHandle[1]+'_orientConstraint')
        cmds.addAttr(controlHandle[1], attributeType='float', longName='Elbow_Blend', minValue=0, maxValue=1, \
                                                                                               defaultValue=0, keyable=True)
        cmds.addAttr(controlHandle[1], attributeType='enum', longName='Forearm_FK', enumName='Off:On:', defaultValue=0, \
                                                                                                               keyable=True)
        cmds.setAttr(controlHandle[1]+'.overrideEnabled', 1)
        cmds.connectAttr('MRT_character'+self.characterName+'_control_rig.visibility', controlHandle[1]+'.overrideVisibility')
        mfunc.lockHideChannelAttrs(controlHandle[1], 's', 'v', keyable=False, lock=True)
        cmds.select(clear=True)

        # Create a parent switch group for the IK control handle.
        ps_groups = self.createParentSwitchGrpForTransform(controlHandle[1], True, 1, True)

        # Calculate the position for the IK pole vector control.
        shldr_pos = cmds.xform(layerRootJoint, query=True, worldSpace=True, translation=True)
        wrist_pos = cmds.xform(jointSet[1], query=True, worldSpace=True, translation=True)
        arm_mid_pos = eval(cmds.getAttr(self.rootJoint+'.ikSegmentMidPos'))
        elbow_pos = cmds.xform(jointSet[2], query=True, worldSpace=True, translation=True)
        ik_pv_offset_pos = mfunc.returnOffsetPositionBetweenTwoVectors(elbow_pos, arm_mid_pos, -2)

        # Create and position the IK pole vector control.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.32
        elbow_pv_preTransform = cmds.group(empty=True, name=self.namePrefix + '_elbowPV_handle_preTransform')
        cmds.xform(elbow_pv_preTransform, worldSpace=True, translation=ik_pv_offset_pos)
        elbow_pv_transform = objects.load_xhandleShape(self.namePrefix+'_elbowPV_handle', self.controlColour, True)
        cmds.setAttr(elbow_pv_transform[0]+'.localScaleX', shapeRadius)
        cmds.setAttr(elbow_pv_transform[0]+'.localScaleY', shapeRadius)
        cmds.setAttr(elbow_pv_transform[0]+'.localScaleZ', shapeRadius)
        cmds.setAttr(elbow_pv_transform[0]+'.drawStyle', 3)
        mfunc.lockHideChannelAttrs(elbow_pv_transform[1], 's', 'v', keyable=False, lock=True)
        cmds.parent(elbow_pv_transform[1], elbow_pv_preTransform, relative=True)
        cmds.parent(elbow_pv_preTransform, ctrlGrp, absolute=True)
        cmds.poleVectorConstraint(elbow_pv_transform[1], ctrlIkHandle, name=elbow_pv_transform[1]+'_poleVectorConstraint')

        # Create a parent switch group for pole vector control handle.
        ps_groups = self.createParentSwitchGrpForTransform(elbow_pv_transform[1], True, 1, True)

        containedNodes = []
        # Add the stretch functionality, to work with the elbow mode.
        shldrPosLocator = cmds.spaceLocator(name=self.namePrefix+'_shldrPos_loc')[0]
        cmds.setAttr(shldrPosLocator+'.visibility', 0)
        cmds.parent(shldrPosLocator, ctrlGrp, absolute=True)
        cmds.pointConstraint(layerRootJoint, shldrPosLocator, maintainOffset=False, \
                                                                        name=self.namePrefix+'_shldrPos_pointConstraint')
        shldrToWrist_distanceBtwn = cmds.createNode('distanceBetween', name=self.namePrefix+'_shldrToWrist_distance', \
                                                                                                            skipSelect=True)
        shldrToElbow_distanceBtwn = cmds.createNode('distanceBetween', name=self.namePrefix+'_shldrToElbow_distance', \
                                                                                                            skipSelect=True)
        elbowToWrist_distanceBtwn = cmds.createNode('distanceBetween', name=self.namePrefix+'_elbowToWrist_distance', \
                                                                                                            skipSelect=True)
        cmds.connectAttr(shldrPosLocator+'Shape.worldPosition[0]', shldrToWrist_distanceBtwn+'.point1')
        cmds.connectAttr(controlHandle[1]+'Shape.worldPosition[0]', shldrToWrist_distanceBtwn+'.point2')
        cmds.connectAttr(shldrPosLocator+'Shape.worldPosition[0]', shldrToElbow_distanceBtwn+'.point1')
        cmds.connectAttr(elbow_pv_transform[1]+'Shape.worldPosition[0]', shldrToElbow_distanceBtwn+'.point2')
        cmds.connectAttr(elbow_pv_transform[1]+'Shape.worldPosition[0]', elbowToWrist_distanceBtwn+'.point1')
        cmds.connectAttr(controlHandle[1]+'Shape.worldPosition[0]', elbowToWrist_distanceBtwn+'.point2')
        restLengthFactor = cmds.createNode('multiplyDivide', name=self.namePrefix+'_shldrToWrist_restLengthFactor', \
                                                                                                            skipSelect=True)
        cmds.connectAttr(self.ch_root_transform+'.globalScale', restLengthFactor+'.input2X')
        cmds.connectAttr(shldrToWrist_distanceBtwn+'.distance', restLengthFactor+'.input1X')
        cmds.setAttr(restLengthFactor+'.operation', 2)
        jointAxis =  cmds.getAttr(layerRootJoint+'.nodeAxes')[0]
        upperArmLengthTranslate = cmds.getAttr(jointSet[2]+'.translate'+jointAxis)
        lowerArmLengthTranslate = cmds.getAttr(jointSet[1]+'.translate'+jointAxis)
        armLength = upperArmLengthTranslate + lowerArmLengthTranslate
        stretchLengthDivide = cmds.createNode('multiplyDivide', name=self.namePrefix+'_shldrToWrist_stretchLengthDivide', \
                                                                                                            skipSelect=True)
        cmds.setAttr(stretchLengthDivide+'.input2X', abs(armLength), lock=True)
        cmds.setAttr(stretchLengthDivide+'.operation', 2)
        cmds.connectAttr(restLengthFactor+'.outputX', stretchLengthDivide+'.input1X')
        stretchCondition = cmds.createNode('condition', name=self.namePrefix+'_shldrToWrist_stretchCondition', \
                                                                                                            skipSelect=True)
        cmds.setAttr(stretchCondition+'.operation', 2)
        cmds.connectAttr(stretchLengthDivide+'.outputX', stretchCondition+'.colorIfTrueR')
        cmds.connectAttr(stretchLengthDivide+'.input2X', stretchCondition+'.secondTerm')
        cmds.connectAttr(stretchLengthDivide+'.input1X', stretchCondition+'.firstTerm')
        lowerArmTranslateMultiply = cmds.createNode('multDoubleLinear', \
                                            name=self.namePrefix+'_shldrToWrist_lowerArmTranslateMultiply', skipSelect=True)
        cmds.connectAttr(stretchCondition+'.outColorR', lowerArmTranslateMultiply+'.input1')
        cmds.setAttr(lowerArmTranslateMultiply+'.input2', lowerArmLengthTranslate)
        lowerArmTranslateBlend = cmds.createNode('blendTwoAttr', \
                                               name=self.namePrefix+'_shldrToElbow_lowerArmTranslateBlend', skipSelect=True)
        cmds.connectAttr(lowerArmTranslateMultiply+'.output', lowerArmTranslateBlend+'.input[0]')
        if lowerArmLengthTranslate < 0:
            lowerArmDistanceReverseNode = cmds.createNode('multiplyDivide', \
                                             name=self.namePrefix+'_elbowToWrist_lowerArmTranslateReverse', skipSelect=True)
            cmds.connectAttr(elbowToWrist_distanceBtwn+'.distance', lowerArmDistanceReverseNode+'.input1X')
            cmds.setAttr(lowerArmDistanceReverseNode+'.input2X', -1)
            cmds.connectAttr(lowerArmDistanceReverseNode+'.outputX', lowerArmTranslateBlend+'.input[1]')
            containedNodes.extend([lowerArmDistanceReverseNode])
        else:
            cmds.connectAttr(elbowToWrist_distanceBtwn+'.distance', lowerArmTranslateBlend+'.input[1]')
        cmds.connectAttr(lowerArmTranslateBlend+'.output', jointSet[1]+'.translate'+jointAxis)
        upperArmTranslateMultiply = cmds.createNode('multDoubleLinear', \
                                            name=self.namePrefix+'_shldrToWrist_upperArmTranslateMultiply', skipSelect=True)
        cmds.connectAttr(stretchCondition+'.outColorR', upperArmTranslateMultiply+'.input1')
        cmds.setAttr(upperArmTranslateMultiply+'.input2', upperArmLengthTranslate)
        upperArmTranslateBlend = cmds.createNode('blendTwoAttr', \
                                               name=self.namePrefix+'_elbowToWrist_upperArmTranslateBlend', skipSelect=True)
        cmds.connectAttr(upperArmTranslateMultiply+'.output', upperArmTranslateBlend+'.input[0]')
        if upperArmLengthTranslate < 0:
            upperArmDistanceReverseNode = cmds.createNode('multiplyDivide', \
                                             name=self.namePrefix+'_elbowToWrist_upperArmTranslateReverse', skipSelect=True)
            cmds.connectAttr(shldrToElbow_distanceBtwn+'.distance', upperArmDistanceReverseNode+'.input1X')
            cmds.setAttr(upperArmDistanceReverseNode+'.input2X', -1)
            cmds.connectAttr(upperArmDistanceReverseNode+'.outputX', upperArmTranslateBlend+'.input[1]')
            containedNodes.extend([upperArmDistanceReverseNode])
        else:
            cmds.connectAttr(shldrToElbow_distanceBtwn+'.distance', upperArmTranslateBlend+'.input[1]')
        cmds.connectAttr(upperArmTranslateBlend+'.output', jointSet[2]+'.translate'+jointAxis)
        cmds.connectAttr(controlHandle[1]+'.Elbow_Blend', lowerArmTranslateBlend+'.attributesBlender')
        cmds.connectAttr(controlHandle[1]+'.Elbow_Blend', upperArmTranslateBlend+'.attributesBlender')
        elbowParentConstraintFK = cmds.parentConstraint(elbow_pv_transform[1], elbowFKTransform, maintainOffset=True, \
                                                                          name=elbow_pv_transform[1]+'_parentConstraint')[0]
        cmds.connectAttr(controlHandle[1]+'.Forearm_FK', elbowParentConstraintFK+'.'+elbow_pv_transform[1]+'W0')
        containedNodes.extend([restLengthFactor, stretchLengthDivide, stretchCondition, lowerArmTranslateMultiply, \
                               upperArmTranslateMultiply, lowerArmTranslateBlend, upperArmTranslateBlend, \
                               shldrToElbow_distanceBtwn, elbowToWrist_distanceBtwn, shldrToWrist_distanceBtwn])

        # Add all the rest of the nodes to the control rig container and publish necessary attributes.
        mfunc.addNodesToContainer(ctrl_container, [controlPreTransform, ctrlGrp, elbow_pv_transform[1]]+containedNodes, \
                                                                                                 includeHierarchyBelow=True)
        cmds.container(ctrl_container, edit=True, publishAndBind=[elbow_pv_transform[1]+'.translate', \
                                                                                            'ik_elbowPV_control_translate'])
        cmds.container(ctrl_container, edit=True, publishAndBind=[controlHandle[1]+'.translate', 'ik_control_translate'])
        cmds.container(ctrl_container, edit=True, publishAndBind=[controlHandle[1]+'.rotate', 'ik_control_rotate'])

        # Create a custom keyable attribute on the character root transform by the control name to adjust the weight
        # of the driver joint layer by using the method "createCtrlRigWeightAttributeOnRootTransform".
        self.createCtrlRigWeightAttributeOnRootTransform(self.ctrlAttrPrefix+'_IK_Control_Stretchy_With_Elbow_Control', \
                                                                                  [controlHandle[1], elbow_pv_transform[1]])
        cmds.select(clear=True)


class SplineControl(BaseJointControl):

    """This hierarchy type is constructed from a spine module, and can be applied with controls useful for posing
    a character spine or a neck."""


    def __init__(self, characterName, rootJoint):
        BaseJointControl.__init__(self, characterName, rootJoint)


    def applyFK_Control(self):

        '''Overridden method, originally inherited from 'BaseJointControl'. It's been modified to include a base
        translation control on top of root FK control.'''

        # Update the naming prefix for the control rig.
        self.namePrefix = self.namePrefix + '_FK_Control'

        # Create the driver joint layer.
        jointSet, driver_constraints, layerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                                 'FK_Control',
                                                                                                 self.characterName,
                                                                                                 True,
                                                                                                 'On',
                                                                                                 True,
                                                                                                 self.controlColour,
                                                                                                 True)
        # Update the instance attribute for the driver joint layer set.
        self.driverJointLayerSet = jointSet

        # Update the instance attribute to contain the driver constraints for the joint hiearachy.
        self.driverConstraintsForInput = driver_constraints

        # Create a control group node to place all DAG nodes (not part of the character joint hierarchy) under it.
        ctrlGrp = cmds.group(empty=True, name=self.namePrefix + '_Grp', \
                                                            parent='MRT_character%s__controlGrp'%(self.characterName))

        # Calculate the size of shape for the FK control.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.35

        # Add the root translation control for the joint layer.
        root_translation_ctl = objects.load_xhandleShape(self.namePrefix+'_rootTranslation_handle', self.controlColour, True)
        root_translation_ctl_grp = cmds.group(empty=True, name=self.namePrefix+'_rootTranslation_handle_preTransform')
        cmds.xform([root_translation_ctl[1], root_translation_ctl_grp], worldSpace=True, translation=\
            cmds.xform(layerRootJoint, query=True, worldSpace=True, translation=True))
        cmds.parent(root_translation_ctl[1], root_translation_ctl_grp, absolute=True)
        cmds.parent(root_translation_ctl_grp, ctrlGrp, absolute=True)
        mfunc.lockHideChannelAttrs(root_translation_ctl[1], 'r', 's', 'v', keyable=False, lock=True)
        cmds.setAttr(root_translation_ctl[0]+'.localScaleX', shapeRadius*2)
        cmds.setAttr(root_translation_ctl[0]+'.localScaleY', shapeRadius*2)
        cmds.setAttr(root_translation_ctl[0]+'.localScaleZ', shapeRadius*2)
        cmds.setAttr(root_translation_ctl[0]+'.drawStyle', 3)

        # Create a parent switch group for the root translation handle.
        ps_groups = self.createParentSwitchGrpForTransform(root_translation_ctl[1], True, 1, True)

        # Create a container for the control rig.
        ctrl_container = cmds.createNode('container', name=self.namePrefix+'_Container', skipSelect=True)

        # Create a parent switch group for the root FK control joint.
        ps_grps = self.createParentSwitchGrpForTransform(layerRootJoint, True)

        # Set the attributes and assign shapes to the control joints.
        for joint in jointSet:
            cmds.setAttr(joint+'.radius', 0)
            mfunc.lockHideChannelAttrs(joint, 't', 's', 'radi', 'v', keyable=False, lock=True)
            cmds.setAttr(joint+'.overrideEnabled', 1)
            cmds.setAttr(joint+'.overrideColor', self.controlColour)
            xhandle = objects.load_xhandleShape(joint, self.controlColour)
            cmds.setAttr(xhandle[0]+'.localScaleX', shapeRadius)
            cmds.setAttr(xhandle[0]+'.localScaleY', shapeRadius)
            cmds.setAttr(xhandle[0]+'.localScaleZ', shapeRadius)
            cmds.setAttr(xhandle[0]+'.drawStyle', 5)

        # Constrain the parent group for the root FK control joint to the root translation control.
        cmds.pointConstraint(root_translation_ctl[1], ps_grps[1], maintainOffset=True, \
                                                                        name=root_translation_ctl[1]+'_pointConstraint')[0]

        # Add the joint layer nodes to the control rig container.
        mfunc.addNodesToContainer(ctrl_container, [ctrlGrp]+ps_grps, includeHierarchyBelow=True)

        # Publish the attributes for joints.
        for joint in jointSet:
            jointName = re.split('MRT_character%s__'%(self.characterName), joint)[1]
            cmds.container(ctrl_container, edit=True, publishAndBind=[joint+'.rotate', jointName+'_rotate'])

        # Publish the root translation handle control attributes.
        handleName = re.split('MRT_character%s__'%(self.characterName), root_translation_ctl[1])[1]
        cmds.container(ctrl_container, edit=True, publishAndBind=\
                                                            [root_translation_ctl[1]+'.translate', handleName+'_translate'])

        # Create a custom keyable attribute on the character root transform by the control name to adjust the weight
        # of the driver joint layer by using the method "createCtrlRigWeightAttributeOnRootTransform".
        self.createCtrlRigWeightAttributeOnRootTransform(self.ctrlAttrPrefix+'_FK_Control', jointSet+[root_translation_ctl[1]])

        cmds.select(clear=True)


    def applyFK_Control_Stretchy(self):

        '''Overridden method, originally inherited from 'BaseJointControl'. It's been modified to include a base
        translation control on top of root FK control.'''

        # Update the naming prefix for the control rig.
        self.namePrefix = self.namePrefix + '_FK_Control_Stretchy'

        # Create the driver joint layer.
        jointSet, driver_constraints, layerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                                 'FK_Control_Stretchy',
                                                                                                  self.characterName,
                                                                                                  True,
                                                                                                  'On',
                                                                                                  True,
                                                                                                  self.controlColour,
                                                                                                  True)
        # Update the instance attribute for the driver joint layer set.
        self.driverJointLayerSet = jointSet

        # Update the instance attribute to contain the driver constraints for the joint hiearachy.
        self.driverConstraintsForInput = driver_constraints

        # Create a control group node to place all DAG nodes (not part of the character joint hierarchy) under it.
        ctrlGrp = cmds.group(empty=True, name=self.namePrefix + '_Grp', \
                                                                    parent='MRT_character%s__controlGrp'%(self.characterName))

        # Calculate the size of shape for the fk control.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.35

        # Add the root translation control for the joint layer.
        root_translation_ctl = objects.load_xhandleShape(self.namePrefix+'_rootTranslation_handle', self.controlColour, True)
        root_translation_ctl_grp = cmds.group(empty=True, name=self.namePrefix+'_rootTranslation_handle_preTransform')
        cmds.xform([root_translation_ctl[1], root_translation_ctl_grp], worldSpace=True, translation=\
            cmds.xform(layerRootJoint, query=True, worldSpace=True, translation=True))
        cmds.parent(root_translation_ctl[1], root_translation_ctl_grp, absolute=True)
        cmds.parent(root_translation_ctl_grp, ctrlGrp, absolute=True)
        mfunc.lockHideChannelAttrs(root_translation_ctl[1], 'r', 's', 'v', keyable=False, lock=True)
        cmds.setAttr(root_translation_ctl[0]+'.localScaleX', shapeRadius*2)
        cmds.setAttr(root_translation_ctl[0]+'.localScaleY', shapeRadius*2)
        cmds.setAttr(root_translation_ctl[0]+'.localScaleZ', shapeRadius*2)
        cmds.setAttr(root_translation_ctl[0]+'.drawStyle', 3)

        # Create a parent switch grp for the root translation handle.
        ps_groups = self.createParentSwitchGrpForTransform(root_translation_ctl[1], True, 1, True)

        # Create a container for the control rig.
        ctrl_container = cmds.createNode('container', name=self.namePrefix+'_Container', skipSelect=True)

        # Create a parent switch group for the root FK control joint.
        ps_grps = self.createParentSwitchGrpForTransform(layerRootJoint, True)

        # Set the attributes and assign shapes to the control joints.
        for joint in jointSet:
            cmds.setAttr(joint+'.radius', 0)
            mfunc.lockHideChannelAttrs(joint, 't', 'radi', 'v', keyable=False, lock=True)
            cmds.setAttr(joint+'.overrideEnabled', 1)
            cmds.setAttr(joint+'.overrideColor', self.controlColour)
            xhandle = objects.load_xhandleShape(joint, self.controlColour)
            cmds.setAttr(xhandle[0]+'.localScaleX', shapeRadius)
            cmds.setAttr(xhandle[0]+'.localScaleY', shapeRadius)
            cmds.setAttr(xhandle[0]+'.localScaleZ', shapeRadius)
            cmds.connectAttr(self.ch_root_transform+'.globalScale', xhandle[0]+'.addScaleX')
            cmds.connectAttr(self.ch_root_transform+'.globalScale', xhandle[0]+'.addScaleY')
            cmds.connectAttr(self.ch_root_transform+'.globalScale', xhandle[0]+'.addScaleZ')
            cmds.setAttr(xhandle[0]+'.drawStyle', 5)
            cmds.setAttr(xhandle[0]+'.transformScaling', 0)

        # Constrain the parent group for the root FK control joint to the root translation control.
        cmds.pointConstraint(root_translation_ctl[1], ps_grps[1], maintainOffset=True, \
                                                                        name=root_translation_ctl[1]+'_pointConstraint')[0]

        # Add the joint layer nodes to the control rig container.
        mfunc.addNodesToContainer(ctrl_container, [ctrlGrp]+ps_grps, includeHierarchyBelow=True)

        # Publish the attributes for joints.
        for joint in jointSet:
            jointName = re.split('MRT_character%s__'%(self.characterName), joint)[1]
            cmds.container(ctrl_container, edit=True, publishAndBind=[joint+'.rotate', jointName+'_rotate'])
            cmds.container(ctrl_container, edit=True, publishAndBind=[joint+'.scale', jointName+'_scale'])

        # Publish the root translation handle control attributes.
        handleName = re.split('MRT_character%s__'%(self.characterName), root_translation_ctl[1])[1]
        cmds.container(ctrl_container, edit=True, publishAndBind=\
                                                            [root_translation_ctl[1]+'.translate', handleName+'_translate'])

        # Create a custom keyable attribute on the character root transform by the control name to adjust the
        # weight of the driver joint layer by using the method "createCtrlRigWeightAttributeOnRootTransform".
        self.createCtrlRigWeightAttributeOnRootTransform(self.ctrlAttrPrefix+'_FK_Control_Stretchy', \
                                                                                         jointSet+[root_translation_ctl[1]])
        cmds.select(clear=True)


    def applyReverse_Spine_FK_Control(self):

        '''Creates a layer of FK controls for the joint chain created from a spline module in reverse order with
        respect to its current hierarchy.'''

        # Update the naming prefix for the control rig.
        self.namePrefix = self.namePrefix + '_Reverse_Spine_FK_Control'

        # Here we'll create a single joint layer driven by a hierarchy of transforms in reverse order.

        # Create the joint layer.
        jointSet, driver_constraints, layerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                                'Reverse_Spine_FK_Control',
                                                                                                self.characterName,
                                                                                                False,
                                                                                                'None',
                                                                                                True,
                                                                                                False)
        # Create a list with names of the joints in the joint layer in reverse order.
        joints = [layerRootJoint]
        joints.extend(jointSet[-1:1:-1])
        joints.append(jointSet[1])

        # Update the instance attribute for the driver joint layer set.
        self.driverJointLayerSet = jointSet

        # Update the instance attribute to contain the driver constraints for the joint hiearachy.
        self.driverConstraintsForInput = driver_constraints

        # Create a container for the control rig.
        ctrl_container = cmds.createNode('container', name=self.namePrefix+'_Container', skipSelect=True)

        # Create a control group node to place all DAG nodes (not part of the character joint hierarchy) under it.
        ctrlGrp = cmds.group(empty=True, name=self.namePrefix + '_Grp', \
                                                                parent='MRT_character%s__controlGrp'%(self.characterName))

        # Calculate the size of shape for the FK control.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.35

        # Create and position the reverse FK control handles.
        r_fk_handles = []
        r_fk_handle_grps = []
        for i in range(self.numJoints-1, -1, -1):
            if i == self.numJoints-1:
                transform = objects.load_xhandleShape(self.namePrefix+'_root_handle', self.controlColour, True)
            elif i == 0:
                transform = objects.load_xhandleShape(self.namePrefix+'_end_handle', self.controlColour, True)
            else:
                transform = objects.load_xhandleShape(self.namePrefix+'_%s_handle'%(i), self.controlColour, True)
            grp = cmds.group(empty=True, name=transform[1]+'_preTransform')
            cmds.xform([transform[1], grp], worldSpace=True, translation=\
                cmds.xform(joints[i], query=True, worldSpace=True, translation=True))
            cmds.parent(transform[1], grp, absolute=True)
            if i == self.numJoints-1 or i == 0:
                cmds.xform(grp, worldSpace=True, rotation=cmds.xform(joints[i], query=True, worldSpace=True, rotation=True))
            mfunc.lockHideChannelAttrs(transform[1], 't', 's', 'v', keyable=False, lock=True)
            cmds.setAttr(transform[0]+'.localScaleX', shapeRadius)
            cmds.setAttr(transform[0]+'.localScaleY', shapeRadius)
            cmds.setAttr(transform[0]+'.localScaleZ', shapeRadius)
            cmds.setAttr(transform[0]+'.drawStyle', 5)
            r_fk_handles.append(transform[1])
            r_fk_handle_grps.append(grp)
        for i, j in zip(range(self.numJoints-3, -1, -1), range(1, self.numJoints-1)):
            cmds.xform(r_fk_handle_grps[j], worldSpace=True, rotation=\
                cmds.xform(joints[i], query=True, worldSpace=True, rotation=True))
        for i in range(self.numJoints):
            if i > 0:
                cmds.parent(r_fk_handle_grps[i], r_fk_handles[i-1], absolute=True)
        cmds.parent(r_fk_handle_grps[0], ctrlGrp, absolute=True)

        # Create a parent switch group for the reverse FK control.
        ps_groups_r_fk_handle_root = self.createParentSwitchGrpForTransform(r_fk_handle_grps[0], True, 1, True)

        # Constrain the joint layer to the reverse FK handles.
        for i, j in zip(range(self.numJoints), range(self.numJoints-1, -1, -1)):
            cmds.parentConstraint(r_fk_handles[i], joints[j], maintainOffset=True, name=r_fk_handles[i]+'_parentConstraint')

        # Add the root translation control for the joint layer.
        root_translation_ctl = objects.load_xhandleShape(self.namePrefix+'_rootTranslation_handle', self.controlColour, True)
        root_translation_ctl_grp = cmds.group(empty=True, name=self.namePrefix+'_rootTranslation_handle_preTransform')
        cmds.xform([root_translation_ctl[1], root_translation_ctl_grp], worldSpace=True, translation=\
            cmds.xform(r_fk_handles[-1], query=True, worldSpace=True, translation=True))
        cmds.parent(root_translation_ctl[1], root_translation_ctl_grp, absolute=True)
        cmds.parent(root_translation_ctl_grp, ctrlGrp, absolute=True)
        mfunc.lockHideChannelAttrs(root_translation_ctl[1], 'r', 's', 'v', keyable=False, lock=True)
        cmds.setAttr(root_translation_ctl[0]+'.localScaleX', shapeRadius*2)
        cmds.setAttr(root_translation_ctl[0]+'.localScaleY', shapeRadius*2)
        cmds.setAttr(root_translation_ctl[0]+'.localScaleZ', shapeRadius*2)
        cmds.setAttr(root_translation_ctl[0]+'.drawStyle', 3)

        # Create a parent switch grp for the root translation handle.
        ps_groups = self.createParentSwitchGrpForTransform(root_translation_ctl[1], True, 1, True)

        # Constrain the parent group for the root FK control joint to the root translation control.
        cmds.pointConstraint(root_translation_ctl[1], ps_groups_r_fk_handle_root[1], maintainOffset=True, \
                                                                         name=root_translation_ctl[1]+'_pointConstraint')[0]

        # Add the joint layer nodes to the control rig container.
        mfunc.addNodesToContainer(ctrl_container, [ctrlGrp]+jointSet+ps_groups_r_fk_handle_root+r_fk_handle_grps, \
                                                                                              includeHierarchyBelow=True)
        # Publish the reverse FK control attributes.
        for handle in r_fk_handles:
            handleName = re.split('MRT_character%s__'%(self.characterName), handle)[1]
            cmds.container(ctrl_container, edit=True, publishAndBind=[handle+'.rotate', handleName+'_rotate'])

        # Publish the root handle control attributes.
        handleName = re.split('MRT_character%s__'%(self.characterName), root_translation_ctl[1])[1]
        cmds.container(ctrl_container, edit=True, publishAndBind=\
                                                         [root_translation_ctl[1]+'.translate', handleName+'_translate'])

        # Create a custom keyable attribute on the character root transform by the control name to adjust the weight
        # of the driver joint layer by using the method "createCtrlRigWeightAttributeOnRootTransform".
        self.createCtrlRigWeightAttributeOnRootTransform(self.ctrlAttrPrefix+'_Reverse_Spine_FK_Control', \
                                                                                  [root_translation_ctl[1]]+r_fk_handles)
        cmds.select(clear=True)


    def applyReverse_Spine_FK_Control_Stretchy(self):

        '''This control rigging method is same as 'Reverse_Spine_FK_Control' with scalable FK controls.'''

        # Update the naming prefix for the control rig.
        self.namePrefix = self.namePrefix + '_Reverse_Spine_FK_Control_Stretchy'

        # Here we'll create a single joint layer driven by a hierarchy of transforms in reverse order.

        # Create the joint layer.
        jointSet, driver_constraints, layerRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                         'Reverse_Spine_FK_Control_Stretchy',
                                                                                          self.characterName,
                                                                                          False,
                                                                                          'None',
                                                                                          True,
                                                                                          False)
        # Create a list with names of the joints in the joint layer in reverse order.
        joints = [layerRootJoint]
        joints.extend(jointSet[-1:1:-1])
        joints.append(jointSet[1])

        # Update the instance attribute for the driver joint layer set.
        self.driverJointLayerSet = jointSet

        # Update the instance attribute to contain the driver constraints for the joint hiearachy.
        self.driverConstraintsForInput = driver_constraints

        # Create a container for the control rig.
        ctrl_container = cmds.createNode('container', name=self.namePrefix+'_Container', skipSelect=True)

        # Create a control group node to place all DAG nodes (not part of the character joint hierarchy) under it.
        ctrlGrp = cmds.group(empty=True, name=self.namePrefix + '_Grp', \
                                                                parent='MRT_character%s__controlGrp'%(self.characterName))

        # Calculate the size of shape for the FK control.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.35

        # Create and position the reverse FK control handles.
        r_fk_handles = []
        r_fk_handle_grps = []
        for i in range(self.numJoints-1, -1, -1):
            if i == self.numJoints-1:
                transform = objects.load_xhandleShape(self.namePrefix+'_root_handle', self.controlColour, True)
            elif i == 0:
                transform = objects.load_xhandleShape(self.namePrefix+'_end_handle', self.controlColour, True)
            else:
                transform = objects.load_xhandleShape(self.namePrefix+'_%s_handle'%(i), self.controlColour, True)
            grp = cmds.group(empty=True, name=transform[1]+'_preTransform')
            cmds.xform([transform[1], grp], worldSpace=True, translation=\
                cmds.xform(joints[i], query=True, worldSpace=True, translation=True))
            cmds.parent(transform[1], grp, absolute=True)
            if i == self.numJoints-1 or i == 0:
                cmds.xform(grp, worldSpace=True, rotation=cmds.xform(joints[i], query=True, worldSpace=True, rotation=True))
            mfunc.lockHideChannelAttrs(transform[1], 't', 'v', keyable=False, lock=True)
            cmds.setAttr(transform[0]+'.localScaleX', shapeRadius)
            cmds.setAttr(transform[0]+'.localScaleY', shapeRadius)
            cmds.setAttr(transform[0]+'.localScaleZ', shapeRadius)
            cmds.setAttr(transform[0]+'.drawStyle', 5)
            cmds.setAttr(transform[0]+'.transformScaling', 0)
            r_fk_handles.append(transform[1])
            r_fk_handle_grps.append(grp)
        for i, j in zip(range(self.numJoints-3, -1, -1), range(1, self.numJoints-1)):
            cmds.xform(r_fk_handle_grps[j], worldSpace=True, rotation=\
                cmds.xform(joints[i], query=True, worldSpace=True, rotation=True))
        for i in range(self.numJoints):
            if i > 0:
                cmds.parent(r_fk_handle_grps[i], r_fk_handles[i-1], absolute=True)
        cmds.parent(r_fk_handle_grps[0], ctrlGrp, absolute=True)

        # Create a parent switch group for the reverse FK control.
        ps_groups_r_fk_handle_root = self.createParentSwitchGrpForTransform(r_fk_handle_grps[0], True, 1, True)

        # Constrain the joint layer to the reverse FK handles.
        for i, j in zip(range(self.numJoints), range(self.numJoints-1, -1, -1)):
            cmds.parentConstraint(r_fk_handles[i], joints[j], maintainOffset=True, name=r_fk_handles[i]+'_parentConstraint')

        # Add the root translation control for the joint layer.
        root_translation_ctl = objects.load_xhandleShape(self.namePrefix+'_rootTranslation_handle', self.controlColour, True)
        root_translation_ctl_grp = cmds.group(empty=True, name=self.namePrefix+'_rootTranslation_handle_preTransform')
        cmds.xform([root_translation_ctl[1], root_translation_ctl_grp], worldSpace=True, translation=\
            cmds.xform(r_fk_handles[-1], query=True, worldSpace=True, translation=True))
        cmds.parent(root_translation_ctl[1], root_translation_ctl_grp, absolute=True)
        cmds.parent(root_translation_ctl_grp, ctrlGrp, absolute=True)
        mfunc.lockHideChannelAttrs(root_translation_ctl[1], 'r', 's', 'v', keyable=False, lock=True)
        cmds.setAttr(root_translation_ctl[0]+'.localScaleX', shapeRadius*2)
        cmds.setAttr(root_translation_ctl[0]+'.localScaleY', shapeRadius*2)
        cmds.setAttr(root_translation_ctl[0]+'.localScaleZ', shapeRadius*2)
        cmds.setAttr(root_translation_ctl[0]+'.drawStyle', 3)

        # Create a parent switch group for the root translation handle.
        ps_groups = self.createParentSwitchGrpForTransform(root_translation_ctl[1], True, 1, True)

        # Constrain the parent group for the root FK control joint to the root translation control.
        cmds.pointConstraint(root_translation_ctl[1], ps_groups_r_fk_handle_root[1], maintainOffset=True, \
                                                                        name=root_translation_ctl[1]+'_pointConstraint')[0]

        # Add the joint layer nodes to the control rig container.
        mfunc.addNodesToContainer(ctrl_container, [ctrlGrp]+jointSet+ps_groups_r_fk_handle_root+r_fk_handle_grps, \
                                                                                                includeHierarchyBelow=True)

        # Publish the reverse FK control attributes.
        for handle in r_fk_handles:
            handleName = re.split('MRT_character%s__'%(self.characterName), handle)[1]
            cmds.container(ctrl_container, edit=True, publishAndBind=[handle+'.rotate', handleName+'_rotate'])
            cmds.container(ctrl_container, edit=True, publishAndBind=[handle+'.scale', handleName+'_scale'])

        # Publish the root handle control attributes.
        handleName = re.split('MRT_character%s__'%(self.characterName), root_translation_ctl[1])[1]
        cmds.container(ctrl_container, edit=True, publishAndBind=\
                                                            [root_translation_ctl[1]+'.translate', handleName+'_translate'])

        # Create a custom keyable attribute on the character root transform by the control name to adjust the weight
        # of the driver joint layer by using the method "createCtrlRigWeightAttributeOnRootTransform".
        self.createCtrlRigWeightAttributeOnRootTransform(self.ctrlAttrPrefix+'_Reverse_Spine_FK_Control_Stretchy',\
                                                                                     [root_translation_ctl[1]]+r_fk_handles)
        cmds.select(clear=True)


    def applyAuto_Spline_Control(self):

        '''This is an alternative implementation for a IK/FK spine control, without using a splineIK solver. This
        implementation responds better to stretch (without over-shooting the end joint position), has better axial twist
        as opposed to limitations of advanced twist in splineIK, while providing a familiar control interface 
        for an animator.'''

        # Update the naming prefix for the control rig.
        self.namePrefix = self.namePrefix + '_Auto_Spline_Control'

        # Create a control group node to place all DAG nodes (not part of the character joint hierarchy) under it.
        ctrlGrp = cmds.group(empty=True, name=self.namePrefix + '_Grp', \
                                                                parent='MRT_character%s__controlGrp'%(self.characterName))

        # Create a container for the control rig.
        ctrl_container = cmds.createNode('container', name=self.namePrefix+'_Container', skipSelect=True)

        # Create the FK layer driver joints, collect them and add to the control container.
        defJointSet, driver_constraints, defLayerRootJoint = \
        mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy, 'Auto_Spline', self.characterName, \
                                                  False, 'None', True)
        defJoints = [defLayerRootJoint]
        defJoints.extend(defJointSet[-1:1:-1])
        defJoints.append(defJointSet[1])
        mfunc.addNodesToContainer(ctrl_container, defJointSet, includeHierarchyBelow=True)

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
                jointName = cmds.joint(name=self.namePrefix+'_root_fk_handle', radius=jointRadius)
            elif i == (numCtls-1):
                jointName = cmds.joint(name=self.namePrefix+'_end_fk_handle', radius=jointRadius)
            else:
                jointName = cmds.joint(name=self.namePrefix+'_%s_fk_handle'%(i), radius=jointRadius)
            cmds.setAttr(jointName+'.radius', 0, keyable=False, channelBox=False)
            cmds.setAttr(jointName+'.visibility', keyable=False)
            cmds.select(clear=True)
            ctlJoints.append(jointName)
        mfunc.addNodesToContainer(ctrl_container, ctlJoints, includeHierarchyBelow=True)

        # Create and assign the shapes for FK control joints.
        shapeRadius = cmds.getAttr(self.rootJoint+'.radius') * 0.35
        for i in range(numCtls):
            transformShape = objects.load_xhandleShape(ctlJoints[i], self.controlColour)
            cmds.setAttr(transformShape[0]+'.localScaleX', shapeRadius*1.0)
            cmds.setAttr(transformShape[0]+'.localScaleY', shapeRadius*1.0)
            cmds.setAttr(transformShape[0]+'.localScaleZ', shapeRadius*1.0)
            cmds.setAttr(transformShape[0]+'.drawStyle', 5)
            cmds.setAttr(transformShape[0]+'.transformScaling', 0)
            cmds.connectAttr(self.ch_root_transform+'.globalScale', transformShape[0]+'.addScaleX')
            cmds.connectAttr(self.ch_root_transform+'.globalScale', transformShape[0]+'.addScaleY')
            cmds.connectAttr(self.ch_root_transform+'.globalScale', transformShape[0]+'.addScaleZ')

        # Collect the world space positions of the spine joints, starting from the root.
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
        tempCurve = cmds.rename(tempCurve, self.namePrefix+'tempCurve')
        cmds.rebuildCurve(tempCurve, constructionHistory=False, replaceOriginal=True, rebuildType=0, degree=1, \
                          endKnots=True, keepEndPoints=True, keepRange=0, keepControlPoints=True, keepTangents=True, \
                          spans=cmds.getAttr(tempCurve+'.spans'), tolerance=0.01)
        u_offset_mult = (1.0/(numCtls-1))
        tempPointOnCurveInfoNodes = []
        for i, joint in zip(range(numCtls), ctlJoints):
            tempPointOnCurveInfo = cmds.createNode('pointOnCurveInfo', skipSelect=True)
            cmds.connectAttr(tempCurve+'Shape.worldSpace[0]', tempPointOnCurveInfo+'.inputCurve')
            cmds.setAttr(tempPointOnCurveInfo+'.parameter', u_offset_mult*i)
            cmds.connectAttr(tempPointOnCurveInfo+'.position', joint+'.translate')
            tempPointOnCurveInfoNodes.append(tempPointOnCurveInfo)
        cmds.select(clear=True)
        mfunc.updateContainerNodes(ctrl_container)
        mfunc.updateNodeList([tempCurve])
        cmds.delete(tempPointOnCurveInfoNodes)
        cmds.delete(tempCurve)

        # If the spline joints have local orientation, orient the FK control joints as well.
        if cmds.getAttr(self.rootJoint+'.splineOrientation') == '1':
            nodeAxes = cmds.getAttr(self.rootJoint+'.nodeAxes')
            onPlane = cmds.getAttr(self.rootJoint+'.plane')
            aimVector = {'X':[1.0, 0.0, 0.0], 'Y':[0.0, 1.0, 0.0], 'Z':[0.0, 0.0, 1.0]}[nodeAxes[0]]
            upVector = {'X':[1.0, 0.0, 0.0], 'Y':[0.0, 1.0, 0.0], 'Z':[0.0, 0.0, 1.0]}[nodeAxes[1]]
            worldUpVector = {'XY':[0.0, 0.0, 1.0], 'YZ':[1.0, 0.0, 0.0], 'XZ':[0.0, 1.0, 0.0]}[onPlane[1:]]
            if onPlane[0] == '-':
                rotationFunction = cmds.getAttr(self.rootJoint+'.rotationFunction')
                if rotationFunction == 'behaviour':
                    aimVector = [item*-1 for item in aimVector]
            cmds.parent(ctlJoints[0], self.rootJoint, absolute=True)
            cmds.parent(ctlJoints[-1], self.selCharacterHierarchy[0], absolute=True)
            cmds.setAttr(ctlJoints[0]+'.jointOrient', 0, 0, 0, type='double3')
            cmds.setAttr(ctlJoints[-1]+'.jointOrient', 0, 0, 0, type='double3')
            cmds.parent(ctlJoints[0], world=True, absolute=True)
            cmds.parent(ctlJoints[-1], world=True, absolute=True)

            target = cmds.spaceLocator(absolute=True, position=cmds.xform(self.selCharacterHierarchy[0], query=True, \
                                                                                    worldSpace=True, translation=True))[0]
            for i in range(1, 3):
                ##tempConstraint = cmds.aimConstraint(ctlJoints[i+1], ctlJoints[i], aimVector=aimVector, upVector=upVector,
                ##worldUpVector=worldUpVector, name=ctlJoints[i]+'_aimConstraint')
                tempConstraint = cmds.aimConstraint(ctlJoints[i+1], ctlJoints[i], aimVector=aimVector, upVector=upVector, \
                                                                                                worldUpVector=worldUpVector)
                cmds.delete(tempConstraint)
                cmds.makeIdentity(ctlJoints[i], rotate=True, apply=True)
            cmds.delete(target)

        # Parent the FK control joints.
        i = 0
        for joint in ctlJoints[1:]:
            cmds.parent(joint, ctlJoints[i], absolute=True)
            i += 1

        # Place the FK control root, under the 'constrained' parent root joint of the joint hierarchy.
        constrainedHierarchyRoot = cmds.listRelatives(defLayerRootJoint, parent=True, type='joint')[0]
        cmds.parent(ctlJoints[0], constrainedHierarchyRoot, absolute=True)

        # Create a parent switch group for the FK root control.
        ps_groups_fk_handle_root = self.createParentSwitchGrpForTransform(ctlJoints[0])

        # Lock the translation channels for the FK control joints, add control rig display layer visibility.
        for joint in ctlJoints:
            mfunc.lockHideChannelAttrs(joint, 't', keyable=False, lock=True)
            cmds.setAttr(joint+'.overrideEnabled', 1)
            cmds.setAttr(joint+'.overrideColor', self.controlColour)
            cmds.connectAttr('MRT_character'+self.characterName+'_control_rig.visibility', joint+'.overrideVisibility')

        # Add the root translation control for the joint layer.
        root_translation_ctl = objects.load_xhandleShape(self.namePrefix+'_rootTranslation_handle', self.controlColour, True)
        root_translation_ctl_grp = cmds.group(empty=True, name=self.namePrefix+'_rootTranslation_handle_preTransform')
        cmds.xform([root_translation_ctl[1], root_translation_ctl_grp], worldSpace=True, translation=\
            cmds.xform(ctlJoints[0], query=True, worldSpace=True, translation=True))
        cmds.parent(root_translation_ctl[1], root_translation_ctl_grp, absolute=True)
        cmds.parent(root_translation_ctl_grp, ctrlGrp, absolute=True)
        mfunc.lockHideChannelAttrs(root_translation_ctl[1], 'r', 's', 'v', keyable=False, lock=True)
        cmds.setAttr(root_translation_ctl[0]+'.localScaleX', shapeRadius*3)
        cmds.setAttr(root_translation_ctl[0]+'.localScaleY', shapeRadius*3)
        cmds.setAttr(root_translation_ctl[0]+'.localScaleZ', shapeRadius*3)
        cmds.setAttr(root_translation_ctl[0]+'.drawStyle', 3)

        # Create a parent switch group for the root translation handle.
        ps_groups_root_translation_ctl = self.createParentSwitchGrpForTransform(root_translation_ctl[1], True, 1, True)

        # Constrain the parent group for the root FK control joint to the root translation control.
        cmds.pointConstraint(root_translation_ctl[1], ps_groups_fk_handle_root[1], maintainOffset=True, \
                                                                        name=root_translation_ctl[1]+'_pointConstraint')[0]

        # Add the joint layer nodes to the control rig container.
        mfunc.addNodesToContainer(ctrl_container, ps_groups_fk_handle_root+ps_groups_root_translation_ctl, \
                                                                                             includeHierarchyBelow=True)
        # Create and position the guide and up vector locators.
        guide_loc_list = []
        upVec_loc_list = []
        for i in range(numCtls):
            if i == 0:
                g_locName = cmds.spaceLocator(name='%s_splineGuide_root_loc'%(self.namePrefix))[0]
            elif i == (numCtls-1):
                g_locName = cmds.spaceLocator(name='%s_splineGuide_end_loc'%(self.namePrefix))[0]
            else:
                g_locName = cmds.spaceLocator(name='%s_splineGuide_%s_loc'%(self.namePrefix, i))[0]
            guide_loc_list.append(g_locName)
            cmds.setAttr(g_locName+'.visibility', 0)
            cmds.xform(g_locName, worldSpace=True, translation=\
                cmds.xform(ctlJoints[i], query=True, worldSpace=True, translation=True), rotation=\
                    cmds.xform(ctlJoints[i], query=True, worldSpace=True, rotation=True))
            cmds.parent(g_locName, ctrlGrp, absolute=True)
            if i == 0:
                u_locName = cmds.spaceLocator(name='%s_splineUpVec_root_loc'%(self.namePrefix))[0]
            elif i == (numCtls-1):
                u_locName = cmds.spaceLocator(name='%s_splineUpVec_end_loc'%(self.namePrefix))[0]
            else:
                u_locName = cmds.spaceLocator(name='%s_splineUpVec_%s_loc'%(self.namePrefix, i))[0]
            cmds.setAttr(u_locName+'.visibility', 0)
            upVec_loc_list.append(u_locName)
            cmds.xform(u_locName, worldSpace=True, translation=\
                cmds.xform(ctlJoints[i], query=True, worldSpace=True, translation=True), rotation=\
                    cmds.xform(ctlJoints[i], query=True, worldSpace=True, rotation=True))
            cmds.parent(u_locName, ctrlGrp, absolute=True)
            startJointPos = cmds.xform(ctlJoints[0], query=True, worldSpace=True, translation=True)
            endJointPos = cmds.xform(ctlJoints[-1], query=True, worldSpace=True, translation=True)
            spine_direction_vec = map(lambda x,y:x-y, endJointPos, startJointPos)
            spine_direction_vec_magnitude = math.sqrt(reduce(lambda x,y: x+y, [component**2 for component in spine_direction_vec]))
            off_val = spine_direction_vec_magnitude / float(numCtls)
            off_ax_val = {abs(spine_direction_vec[0]): [off_val, 0, 0], \
                          abs(spine_direction_vec[1]): [0, off_val, 0], \
                          abs(spine_direction_vec[2]): [0, 0, off_val]}
            off_ax = off_ax_val[min(off_ax_val)]
            cmds.move(off_ax[0], off_ax[1], off_ax[2], u_locName, relative=True, localSpace=True, worldSpaceDistance=True)

        # Create the 'driver' and the 'up' curve.
        curveCVposString = '['
        jointIt = ctlJoints[0]
        while jointIt:
            pos = cmds.xform(jointIt, query=True, worldSpace=True, translation=True)
            curveCVposString += str(tuple(pos))+','
            jointIt = cmds.listRelatives(jointIt, children=True, type='joint')
        curveCVposString = curveCVposString[:-1] + ']'
        curveCVposList = eval(curveCVposString)
        driverCurve = cmds.curve(degree=2, point=curveCVposList)
        driverCurve = cmds.rename(driverCurve, self.namePrefix + '_driverCurve')
        cmds.setAttr(driverCurve+'.visibility', 0)
        cmds.select(clear=True)
        upVecCurve = cmds.duplicate(driverCurve, returnRootsOnly=True, name=self.namePrefix + '_upVectorCurve')[0]
        cmds.move(off_ax[0], off_ax[1], off_ax[2], upVecCurve, relative=True, localSpace=True, worldSpaceDistance=True)
        cmds.parent(driverCurve, ctrlGrp, absolute=True)
        cmds.parent(upVecCurve, ctrlGrp, absolute=True)

        # Create the clusters for 'driver' and 'up' curve CVs.
        cmds.namespace(setNamespace=':')
        tempNamespaceName = self.namePrefix+'_tempNamespace'
        for i in range(numCtls):
            cmds.namespace(addNamespace=tempNamespaceName)
            cmds.namespace(setNamespace=tempNamespaceName)
            cmds.select(driverCurve+'.cv['+str(i)+']')
            drvClusterNodes = cmds.cluster(relative=True)
            cmds.setAttr(drvClusterNodes[1]+'.visibility', 0)
            cmds.pointConstraint(guide_loc_list[i], drvClusterNodes[1])
            cmds.parent(drvClusterNodes[1], ctrlGrp, absolute=True)
            cmds.select(clear=True)
            namespaceNodes = cmds.namespaceInfo(listOnlyDependencyNodes=True)
            namespaceNodes = [item for item in namespaceNodes if item.endswith('Shape') == False]
            drv_csr_nodes = []
            for node in namespaceNodes:
                nodeName = node.partition(':')[2]
                if nodeName.find('MRT_character') == -1:
                    nameSeq = re.split('\d+', nodeName)
                    name = cmds.rename(node, self.namePrefix+'_driverCurve_%s_csr_%s'%(i, ''.join(nameSeq)))
                    drv_csr_nodes.append(name.partition(':')[2])
            cmds.namespace(setNamespace=':')
            cmds.namespace(moveNamespace=[tempNamespaceName, ':'], force=True)
            cmds.namespace(removeNamespace=tempNamespaceName)
            mfunc.addNodesToContainer(ctrl_container, drv_csr_nodes, includeHierarchyBelow=True)
            cmds.select(clear=True)
        for i in range(numCtls):
            cmds.namespace(addNamespace=tempNamespaceName)
            cmds.namespace(setNamespace=tempNamespaceName)
            cmds.select(upVecCurve+'.cv['+str(i)+']')
            upVecClusterNodes = cmds.cluster(relative=True)
            cmds.setAttr(upVecClusterNodes[1]+'.visibility', 0)
            cmds.pointConstraint(upVec_loc_list[i], upVecClusterNodes[1], name=upVecClusterNodes[1]+'_pointConstraint')
            cmds.parentConstraint(guide_loc_list[i], upVec_loc_list[i], maintainOffset=True, \
                                                                            name=upVec_loc_list[i]+'_parentConstraint')
            cmds.parent(upVecClusterNodes[1], ctrlGrp, absolute=True)
            cmds.select(clear=True)
            namespaceNodes = cmds.namespaceInfo(listOnlyDependencyNodes=True)
            namespaceNodes = [item for item in namespaceNodes if item.endswith('Shape') == False]
            up_csr_nodes = []
            for node in namespaceNodes:
                nodeName = node.partition(':')[2]
                if nodeName.find('MRT_character') == -1:
                    nameSeq = re.split('\d+', nodeName)
                    name = cmds.rename(node, self.namePrefix+'_upVectorCurve_%s_csr_%s'%(i, ''.join(nameSeq)))
                    up_csr_nodes.append(name.partition(':')[2])
            cmds.namespace(setNamespace=':')
            cmds.namespace(moveNamespace=[tempNamespaceName, ':'], force=True)
            cmds.namespace(removeNamespace=tempNamespaceName)
            mfunc.addNodesToContainer(ctrl_container, up_csr_nodes, includeHierarchyBelow=True)
            cmds.select(clear=True)

        # Create the 'IK style' translation control handles.
        ikCtlGrp = cmds.group(empty=True, name=self.namePrefix+'_ik_handle_grp', parent=ctrlGrp)
        cmds.connectAttr(self.ch_root_transform+'.globalScale', ikCtlGrp+'.scaleX')
        cmds.connectAttr(self.ch_root_transform+'.globalScale', ikCtlGrp+'.scaleY')
        cmds.connectAttr(self.ch_root_transform+'.globalScale', ikCtlGrp+'.scaleZ')
        ik_ctls = []
        ik_xhandles = []
        for i in range(numCtls):
            colour = self.controlColour + 2
            if self.controlColour > 29:
                colour = self.controlColour - 2
            if i == 0:
                transform = objects.load_xhandleShape(self.namePrefix+'_root_ik_handle', colour, True)
                cmds.setAttr(transform[0]+'.localScaleX', shapeRadius*2.0)
                cmds.setAttr(transform[0]+'.localScaleY', shapeRadius*2.0)
                cmds.setAttr(transform[0]+'.localScaleZ', shapeRadius*2.0)
            elif i == (numCtls-1):
                transform = objects.load_xhandleShape(self.namePrefix+'_end_ik_handle', colour, True)
                cmds.setAttr(transform[0]+'.localScaleX', shapeRadius*1.7)
                cmds.setAttr(transform[0]+'.localScaleY', shapeRadius*1.7)
                cmds.setAttr(transform[0]+'.localScaleZ', shapeRadius*1.7)
            else:
                transform = objects.load_xhandleShape(self.namePrefix+'_%s_ik_handle'%(i), colour, True)
                cmds.setAttr(transform[0]+'.localScaleX', shapeRadius*1.7)
                cmds.setAttr(transform[0]+'.localScaleY', shapeRadius*1.7)
                cmds.setAttr(transform[0]+'.localScaleZ', shapeRadius*1.7)

            cmds.setAttr(transform[0]+'.drawStyle', 3)
            cmds.setAttr(transform[0]+'.wireframeThickness', 2)

            cmds.setAttr(transform[1]+'.overrideEnabled', 1)
            cmds.connectAttr('MRT_character'+self.characterName+'_control_rig.visibility', transform[1]+'.overrideVisibility')
            # Pre-transform each handle and orient it accordingly.
            ikHandleOriGrp = cmds.group(empty=True, name=transform[1]+'_transOriGrp')
            if self.transOriFunc == 'local_orientation':
                cmds.xform(ikHandleOriGrp, worldSpace=True, translation=\
                    cmds.xform(ctlJoints[i], query=True, worldSpace=True, translation=True), rotation=\
                        cmds.xform(ctlJoints[i], query=True, worldSpace=True, rotation=True))
            if self.transOriFunc == 'world':
                cmds.xform(ikHandleOriGrp, worldSpace=True, translation=\
                    cmds.xform(ctlJoints[i], query=True, worldSpace=True, translation=True))
            cmds.parent(transform[1], ikHandleOriGrp, relative=True)
            cmds.parent(ikHandleOriGrp, ikCtlGrp, absolute=True)
            mfunc.lockHideChannelAttrs(transform[1], 'r', 's', 'v', keyable=False, lock=True)
            cmds.parentConstraint(transform[1], guide_loc_list[i], maintainOffset=True, name=transform[1]+'_parentConstraint')
            cmds.parentConstraint(ctlJoints[i], ikHandleOriGrp, maintainOffset=True, name=ctlJoints[i]+'_parentConstraint')
            ik_xhandles.append(transform[1])
            ik_ctls.append(ikHandleOriGrp)
        cmds.select(clear=True)

        # Create the control joint layer (indirect, since it'll be driven by the curve), where each joint will
        # be unparented and drive the main joint layer using constraints (notice the connectLayer argument is False).
        crvJointSet, null, crvRootJoint = mfunc.createFKlayerDriverOnJointHierarchy(self.selCharacterHierarchy,
                                                                                    'Auto_Spline_Curve',
                                                                                    self.characterName,
                                                                                    False,
                                                                                    'None',
                                                                                    False,
                                                                                    None,
                                                                                    False)
        # No driver constraints are returned here, therefore, 'null'.

        mfunc.addNodesToContainer(ctrl_container, crvJointSet, includeHierarchyBelow=True)
        for joint in crvJointSet:
            cmds.parent(joint, world=True)

        # The control joints will be driven by the 'driver' curve by constraining to it using motionPath for translation,
        # and then their orientation will be guided by offsetted locators on an 'up' vector curve using constraints.
        crvJoints = [crvRootJoint]
        crvJoints.extend(crvJointSet[-1:1:-1])
        crvJoints.append(crvJointSet[1])

        u_offset_mult = (1.0/(self.numJoints-1))
        for i in range(self.numJoints):
            cmds.parent(crvJoints[i], ctrlGrp, absolute=True)
            cmds.select([crvJoints[i], driverCurve])
            mp_node = cmds.pathAnimation(fractionMode=True, follow=False)
            mel.eval('cutKey -t ":" -cl -f ":" -at "u" '+mp_node+';')
            cmds.getAttr(mp_node+'.uValue')
            cmds.setAttr(mp_node+'.uValue', i*u_offset_mult)
            mp_connections = cmds.listConnections(crvJoints[i], destination=True, type='addDoubleLinear')
            mp_connections = list(set(mp_connections))
            mp_node = cmds.rename(mp_node, crvJoints[i]+'_motionPathNode')
            mfunc.addNodesToContainer(ctrl_container, mp_node)
            j = 1
            for node in mp_connections:
                name = cmds.rename(node, '%s_translateAdjust_%s_addDoubleLinear'%(crvJoints[i], j))
                mfunc.addNodesToContainer(ctrl_container, name)
                j += 1

            if i == 0:
                u_crv_locName = cmds.spaceLocator(name='%s_curveUpVec_root_loc'%(self.namePrefix))[0]
            elif i == (self.numJoints-1):
                u_crv_locName = cmds.spaceLocator(name='%s_curveUpVec_end_loc'%(self.namePrefix))[0]
            else:
                u_crv_locName = cmds.spaceLocator(name='%s_curveUpVec_%s_loc'%(self.namePrefix, i))[0]
            cmds.setAttr(u_crv_locName+'.localScale', 0.25, 0.25, 0.25, type='double3')
            cmds.setAttr(u_crv_locName+'.visibility', 0)
            cmds.parent(u_crv_locName, ctrlGrp, absolute=True)
            cmds.select([u_crv_locName, upVecCurve])
            mp_node = cmds.pathAnimation(fractionMode=True, follow=False)
            mel.eval('cutKey -t ":" -cl -f ":" -at "u" '+mp_node+';')
            cmds.getAttr(mp_node+'.uValue')
            cmds.setAttr(mp_node+'.uValue', i*u_offset_mult)
            mp_connections = cmds.listConnections(u_crv_locName, destination=True, type='addDoubleLinear')
            mp_connections = list(set(mp_connections))
            mp_node = cmds.rename(mp_node, u_crv_locName+'_motionPathNode')
            mfunc.addNodesToContainer(ctrl_container, mp_node)
            j = 1
            for node in mp_connections:
                name = cmds.rename(node, '%s_translateAdjust_%s_addDoubleLinear'%(u_crv_locName, j))
                mfunc.addNodesToContainer(ctrl_container, name)
                j += 1
            if i > 0:
                nodeAxes = cmds.getAttr(self.rootJoint+'.nodeAxes')
                onPlane = cmds.getAttr(self.rootJoint+'.plane')
                aimVector={'X':[1.0, 0.0, 0.0], 'Y':[0.0, 1.0, 0.0], 'Z':[0.0, 0.0, 1.0]}[nodeAxes[0]]
                upVector = {'X':[1.0, 0.0, 0.0], 'Y':[0.0, 1.0, 0.0], 'Z':[0.0, 0.0, 1.0]}[nodeAxes[1]]
                if onPlane[0] == '-':
                    rotationFunction = cmds.getAttr(self.rootJoint+'.rotationFunction')
                    if rotationFunction == 'behaviour':
                        aimVector = [item*-1 for item in aimVector]
                aimConstraint = cmds.aimConstraint(crvJoints[i], crvJoints[i-1], maintainOffset=True, aimVector=aimVector, \
                    upVector=upVector, worldUpType='object', worldUpObject=u_crv_locName, name=crvJoints[i]+'_aimConstraint')
            if i == self.numJoints-1:
                orientConstraint = cmds.orientConstraint(ctlJoints[-1], crvJoints[i], maintainOffset=True, \
                                                                        name=crvJoints[-1]+'_orientConstraint')[0]

            cmds.parentConstraint(crvJoints[i], defJoints[i], maintainOffset=True, name=crvJoints[i]+'_parentConstraint')

            # This could be done, but only if the fk control joints equal the number of hierarchy joints; it is not
            # completely necessary. If done, you'd have to create a switch for toggling stretch.
            ##cmds.parentConstraint(ctlJoints[i], defJoints[i], maintainOffset=True)##

            cmds.select(clear=True)

        # Add all the control rig nodes to the container and publish attributes.
        mfunc.addNodesToContainer(ctrl_container, ctrlGrp, includeHierarchyBelow=True)
        for i in range(len(ctlJoints)):
            transformName = re.split('MRT_character%s__'%(self.characterName), ctlJoints[i])[1]
            if i == 0:
                cmds.container(ctrl_container, edit=True, publishAndBind=\
                                                                [ctlJoints[i]+'.translate', transformName+'_translate'])
            cmds.container(ctrl_container, edit=True, publishAndBind=[ctlJoints[i]+'.rotate', transformName+'_rotate'])
            cmds.container(ctrl_container, edit=True, publishAndBind=[ctlJoints[i]+'.scale', transformName+'_scale'])
        for joint in ik_xhandles:
            jointName = re.split('MRT_character%s__'%(self.characterName), joint)[1]
            cmds.container(ctrl_container, edit=True, publishAndBind=[joint+'.translate', jointName+'_translate'])

        # Create a custom keyable attribute on the character root transform by the control name to adjust the weight
        # of the driver joint layer by using the method "createCtrlRigWeightAttributeOnRootTransform".
        self.createCtrlRigWeightAttributeOnRootTransform(self.ctrlAttrPrefix+'_Auto_Spline_Control', \
                                                                    ctlJoints+ik_xhandles+[root_translation_ctl[1]])


## End of file. Do not remove any newline or line breaks after this ##
