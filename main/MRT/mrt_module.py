# *************************************************************************************************************
#
#    mrt_module.py - Source for all module generation for use in maya scene. These scene module are
#                    then further processed for creating a character.
#
#    Can be modified or copied for your own purpose. Please keep updating it for use with future versions
#    of Maya. This was originally written for Maya 2011, and updated for 2013 and then for 2014.
#
#    Written by Himanish Bhattacharya.
#    
#    You may notice that I use rather descriptive variable names. It just makes more sense to me
#    and helps avoid over-commenting.
#
# *************************************************************************************************************

import maya.cmds as cmds
import maya.mel as mel

import mrt_functions as mfunc
import mrt_objects as objects

import math, os, re
from functools import partial

'''
The three module types, Joint Node, Spline Node and Hinge Node modules are defined as methods, 
"createJointNodeModule", "createSplineNodeModule" and "createHingeNodeModule" for the main 
module class, "MRT_Module".
'''

class MRT_Module(object):

    def __init__(self, moduleInfo):
        '''
        Common module creation attributes for all module types. The "moduleInfo"
        is a dictionary which is passed-in, containing the module creation option/values.
        '''
        
        # Attributes to store values from "moduleInfo":
        
        # Module type.
        self.moduleType = moduleInfo['node_type']
        
        # Number of nodes in the module.
        self.numNodes = moduleInfo['num_nodes']
        
        # Length of the module.
        self.moduleLen = moduleInfo['module_length']
        
        # Creation plane.
        self.onPlane = moduleInfo['creation_plane'][-2:]
        
        # Offset from origin.
        self.moduleOffset = moduleInfo['module_offset']
        
        # Node Axes.
        self.nodeAxes = moduleInfo['node_axes']
        
        # Proxy geometry creation on/off.
        self.proxyGeoStatus = moduleInfo['node_compnts'][2]
        
        # Proxy bones.
        self.proxyGeoBones = moduleInfo['proxy_geo_options'][0]
        
        # Proxy elbow.
        self.proxyGeoElbow = moduleInfo['proxy_geo_options'][1]
        self.proxyElbowType = moduleInfo['proxy_geo_options'][2]
        
        # Mirror instance for proxy geometry.
        self.proxyGeoMirrorInstance = moduleInfo['proxy_geo_options'][3]
        
        # Create mirror module on/off.
        self.mirrorModule = moduleInfo['mirrorModule']
        self.mirrorModuleStatus = moduleInfo['mirror_options'][0]
        
        # Translation function for mirroring.
        self.mirrorTranslationFunc = moduleInfo['mirror_options'][1]
        
        # Rotation function for mirroring.
        self.mirrorRotationFunc = moduleInfo['mirror_options'][2]
        
        # Variables to set visibility attributes for hierarchy, orientation representations.
        self.showHierarchy = moduleInfo['node_compnts'][0]
        self.showOrientation = moduleInfo['node_compnts'][1]
        
        # Module handle colour.
        self.modHandleColour = moduleInfo['handle_colour'] - 1
        
        # Module namespace.
        self.moduleTypespace = moduleInfo['module_Namespace']
        
        # Generated mirror module namespace
        self.mirror_moduleNamespace = moduleInfo['mirror_module_Namespace']
        
        # Module container name.
        self.moduleContainer = self.moduleTypespace + ':module_container'
        
        # Attribute to store values for operations:
        
        # To calculate and store the initial "creation" positions of module nodes.
        self.initNodePos = []
        
        # To store node joints.
        self.nodeJoints = []
        
        # To store nodes which are created during module construction so that they can be added to the module container.
        self.collectedNodes = []


    def returnNodeInfoTransformation(self, numNodes):
        '''
        This method calculates the position(s) for module node(s) to be created based on their quantity and 
        provided length from the UI. It also takes into account the offset position of the module from the 
        creation plane, specified in the UI.
        '''
        # Reset initial module node positions.
        self.initNodePos = []
        
        # If the module to be created is a mirrored module. It's a part of a mirrored module pair,
        # to be created on the '-' side of the creation plane.
        if self.mirrorModule:
            self.moduleOffset = self.moduleOffset * -1
        
        # Axis for offset, based on the module creation plane.
        axisForOffset = {'XY':'Z', 'YZ':'X', 'XZ':'Y'}[self.onPlane]
        
        # Record the position of the root node for the module.
        if axisForOffset == 'X':
            self.initNodePos.append([self.moduleOffset, 0, 0])
        if axisForOffset == 'Y':
            self.initNodePos.append([0, self.moduleOffset, 0])
        if axisForOffset == 'Z':
            self.initNodePos.append([0, 0, self.moduleOffset])
            
        # If the module has single node, return.
        if self.moduleLen == 0 or self.numNodes == 1:
            return

        # Increment for subsequent nodes in the module after root.
        increment = self.moduleLen / (numNodes - 1)

        # Calculate and append the node positions.
        incrementAxis = {'XY':'Y', 'YZ':'Y', 'XZ':'X'}[self.onPlane]
        if incrementAxis == 'Y':
            posIncrement = [0, 1, 0]
        if incrementAxis == 'X':
            posIncrement = [1, 0, 0]
        for i in range(numNodes - 1):
            self.initNodePos.append(map(lambda x,y:x+y, [c*increment for c in posIncrement], self.initNodePos[-1]))


    def createOrientationHierarchyReprOnNodes(self):
        '''
        This method creates orientation and hierarchy representations for a module. These
        representations are created between two consecutive nodes in a module.
        '''
        
        # Create representation objects for every module node(s)(joint) except the last in iteration.
        for index, joint in enumerate(self.nodeJoints[:-1]):
        
            # Create raw representation objects.
            hierarchyRepr = objects.createRawHierarchyRepresentation(self.nodeAxes[0])
            orientationReprNodes = objects.createRawOrientationRepresentation(self.nodeAxes[0])
            
            if self.mirrorModule and self.mirrorRotationFunc == 'Behaviour':
                cmds.setAttr(orientationReprNodes[0]+'.scale'+self.nodeAxes[2], -1)
                cmds.makeIdentity(orientationReprNodes[0], scale=True, apply=True)
            
            # Point constrain the orientation representation pre-transform to the joint in iteration.
            cmds.pointConstraint(joint, orientationReprNodes[1], maintainOffset=False,
                                                    name='%s:%s_orient_repr_transformGroup_pointConstraint' \
                                                        % (self.moduleTypespace, mfunc.stripMRTNamespace(joint)[1]))
            
            # Get the name(reference) for the 'start' and 'end' locators(while creating the node segment representations).
            # These locators are on the node handle shape surfaces via CPS.
            startLocator = joint + '_segmentCurve_startLocator'
            endLocator = self.nodeJoints[index+1] + '_segmentCurve_endLocator'
            
            # Point constrain the hierarchy representation to the start and end locators.
            cmds.pointConstraint(startLocator, endLocator, hierarchyRepr, maintainOffset=False,
                                                                            name=joint+'_hierarchy_repr_pointConstraint')
            
            # Scale constrain the hierarchy representation to the joint in iteration.
            cmds.scaleConstraint(joint, hierarchyRepr, maintainOffset=False, name=joint+'_hierarchy_repr_scaleConstraint')
            
            # Aim constrain the orientation representation pre-transform and the hierarchy representation
            # with the next joint in iteration.
            aimVector = {'X':[1.0, 0.0, 0.0], 'Y':[0.0, 1.0, 0.0], 'Z':[0.0, 0.0, 1.0]}[self.nodeAxes[0]]
            upVector = {'X':[1.0, 0.0, 0.0], 'Y':[0.0, 1.0, 0.0], 'Z':[0.0, 0.0, 1.0]}[self.nodeAxes[1]]
            
            cmds.aimConstraint(self.nodeJoints[index+1], orientationReprNodes[1], maintainOffset=False,
                               aimVector=aimVector, upVector=upVector, worldUpVector=upVector, worldUpType='objectRotation',
                               worldUpObject=joint, name='%s:%s_orient_repr_transformGroup_aimConstraint' \
                                                            % (self.moduleTypespace,
                                                               mfunc.stripMRTNamespace(self.nodeJoints[index+1])[1]))
            
            cmds.aimConstraint(self.nodeJoints[index+1], hierarchyRepr, maintainOffset=False, aimVector=aimVector,
                                    upVector=upVector, worldUpVector=upVector, worldUpType='objectRotation', worldUpObject=joint,
                                        name='%s:%s_hierarchy_repr_aimConstraint' \
                                                % (self.moduleTypespace,
                                                   mfunc.stripMRTNamespace(self.nodeJoints[index+1])[1]))
            
            # Parent the orientation representation pre-transform and the hierarchy representation to their appropriate group.
            cmds.parent(hierarchyRepr, self.moduleOrientationHierarchyReprGrp, absolute=True)
            cmds.parent(orientationReprNodes[1], self.moduleOrientationHierarchyReprGrp, absolute=True)
            
            # Point constrain the orientation representation to the start locator, on the surface of the shape
            # node of the joint in iteration.
            cmds.pointConstraint(joint+'_segmentCurve_startLocator', orientationReprNodes[0], maintainOffset=True,
                                            name=self.moduleTypespace+':'+orientationReprNodes[0]+'_basePointConstraint')
                                            
            # Depending on the node aim axis, connect the scale attributes for the orientation representation.
            # The scaling along the aim axis will be the size of the orientation representation, proportional to the arc
            # length of the segment curve between two nodes.
            
            if self.nodeAxes[0] == 'X':
                arclen = cmds.arclen(joint+'_segmentCurve', constructionHistory=True)
                cmds.connectAttr(arclen+'.arcLength', orientationReprNodes[0]+'.scaleX')
                cmds.connectAttr(self.moduleTransform+'.finalScale', orientationReprNodes[0]+'.scaleY')
                cmds.connectAttr(self.moduleTransform+'.finalScale', orientationReprNodes[0]+'.scaleZ')
                cmds.rename(arclen, joint+'_segmentCurve_curveInfo')
                self.collectedNodes.append(joint+'_segmentCurve_curveInfo')
            
            if self.nodeAxes[0] == 'Y':
                arclen = cmds.arclen(joint+'_segmentCurve', constructionHistory=True)
                cmds.connectAttr(arclen+'.arcLength', orientationReprNodes[0]+'.scaleY')
                cmds.connectAttr(self.moduleTransform+'.finalScale', orientationReprNodes[0]+'.scaleX')
                cmds.connectAttr(self.moduleTransform+'.finalScale', orientationReprNodes[0]+'.scaleZ')
                cmds.rename(arclen, joint+'_segmentCurve_curveInfo')
                self.collectedNodes.append(joint+'_segmentCurve_curveInfo')
            
            if self.nodeAxes[0] == 'Z':
                arclen = cmds.arclen(joint+'_segmentCurve', constructionHistory=True)
                cmds.connectAttr(arclen+'.arcLength', orientationReprNodes[0]+'.scaleZ')
                cmds.connectAttr(self.moduleTransform+'.finalScale', orientationReprNodes[0]+'.scaleX')
                cmds.connectAttr(self.moduleTransform+'.finalScale', orientationReprNodes[0]+'.scaleY')
                cmds.rename(arclen, joint+'_segmentCurve_curveInfo')
                self.collectedNodes.append(joint+'_segmentCurve_curveInfo')

            # Rename the hierarchy representation, orientation representation and its pre-transform.
            cmds.rename(hierarchyRepr, joint+'_'+hierarchyRepr)
            cmds.rename(orientationReprNodes[0],
                        self.moduleTypespace+':'+mfunc.stripMRTNamespace(joint)[1]+'_'+orientationReprNodes[0])
            cmds.rename(orientationReprNodes[1],
                        self.moduleTypespace+':'+mfunc.stripMRTNamespace(joint)[1]+'_'+orientationReprNodes[1])


    def createJointNodeControlHandleRepr(self):
        '''
        Creates representation/helper objects on module nodes when called. It also creates segments 
        between node(s) to represent how the module nodes are connected.
        '''
        mfunc.updateAllTransforms()
        
        # Create handle(s) on every module node(s)(joint) in iteration.
        for i, joint in enumerate(self.nodeJoints):
        
            # Create a raw handle object. This is a "dummy" surface object under a module
            # node control for rigging. The module node control(s) are custom locators and thus do
            # not have any shape information on them, so a hidden Nurbs surface is created in order
            # to "rig" with the module nodes.
            handleNodes = objects.createRawControlSurface(joint, self.modHandleColour)
            
            # Parent and then rename their shapes with the joint node.
            handleShape = handleNodes[1]
            
            # Delete the empty transform for the raw handle objects.
            # Select and add a cluster to the joint node, which will affect its shape node. The selection command is
            # important here since it'll update the DG in context to the joint with its new shape node. Otherwise the
            # cluster will report 'no deformable objects' when directly processing the joint or its shape node when
            # passed in as the first argument.
            handleShapeScaleCluster = cmds.cluster(handleShape, relative=True, name=handleShape+'_scaleCluster')
            
            # Parent the cluster handle appropriately and turn off its visibility.
            cmds.parent(handleShapeScaleCluster[1], self.moduleNodeHandleShapeScaleClusterGrp, absolute=True)
            cmds.setAttr(handleShapeScaleCluster[1]+'.visibility', 0)
            
            # Collect the cluster nodes.
            clusterNodes = cmds.listConnections(handleShape, source=True, destination=True)
            
            # Remove the tweak node.
            for node in clusterNodes:
                if cmds.nodeType(node) == 'tweak':
                    cmds.delete(node)
                    break
            
            # Update the cluster node list and collect it.
            clusterNodes = cmds.listConnections(handleShape, source=True, destination=True)
            self.collectedNodes.extend(clusterNodes)
            
            # Create a locator for the joint node in iteration for indicating its
            # world position. This will be needed later for utility purposes.
            worldPosLocator = cmds.createNode('locator', parent=joint, name=joint+'_worldPosLocator')
            
            # Turn off its visibility.
            cmds.setAttr(worldPosLocator + '.visibility', 0)
            cmds.setAttr(handleShape+'.visibility', 0)

    
        # If the module contains more the one node (joint), create segment representations between
        # the joints in hierarchy.
        if len(self.nodeJoints) > 1:

            # Iterate through every joint except the last joint.
            for j, joint in enumerate(self.nodeJoints[:-1]):
            
                # Create a segment curve to be attached between two nodes (current node joint and the next one).
                segment = objects.createRawSegmentCurve(self.modHandleColour)

                # Now set up DG connections with appropriate nodes to help limit the segment curve between the
                # handle surfaces for the two nodes. This is done so that the length of this segment curve can be used
                # to adjust the length of the orientation representation control object between the two nodes, so that
                # it always fits between two node handle surfaces, even if they change in sizes.
                startClosestPointOnSurface = cmds.createNode('closestPointOnSurface',
                                                              name=joint+'_'+segment['startLoc']+'_closestPointOnSurface')
                
                cmds.connectAttr(joint+'_controlShape.worldSpace[0]', startClosestPointOnSurface+'.inputSurface')
                cmds.connectAttr(self.nodeJoints[j+1]+'_worldPosLocator.worldPosition', startClosestPointOnSurface+'.inPosition')
                cmds.connectAttr(startClosestPointOnSurface+'.position', segment['startLoc']+'.translate')
                endClosestPointOnSurface = cmds.createNode('closestPointOnSurface',
                                            name=self.nodeJoints[j+1]+'_'+segment['endLoc']+'_closestPointOnSurface')

                cmds.connectAttr(self.nodeJoints[j+1]+'_controlShape.worldSpace[0]', endClosestPointOnSurface+'.inputSurface')
                cmds.connectAttr(joint+'_worldPosLocator.worldPosition', endClosestPointOnSurface+'.inPosition')
                cmds.connectAttr(endClosestPointOnSurface+'.position', segment['endLoc']+'.translate')
                
                # Parent the segment curve and its related nodes to their associated group.
                cmds.parent([segment['curve'], segment['startLoc'], segment['endLoc']],
                                        self.moduleHandleSegmentGrp, absolute=True)
                
                # Rename the nodes.
                # Rename the curve transform.
                cmds.rename(segment['curve'],
                            self.moduleTypespace+':'+mfunc.stripMRTNamespace(joint)[1]+'_'+segment['curve'])
                            
                # Rename the 'start' and 'end' locators which drive the segment curve.
                cmds.rename(segment['startLoc'], joint+'_'+segment['startLoc'])
                cmds.rename(segment['endLoc'], self.nodeJoints[j+1]+'_'+segment['endLoc'])
                
                # Clear the selection, and force an update on DG.
                cmds.select(clear=True)
                
                # Collect the nodes.
                self.collectedNodes.extend([startClosestPointOnSurface, endClosestPointOnSurface])
    

    def createHierarchySegmentForModuleParentingRepr(self):
        '''
        Creates module parenting representation objects for a module. These objects are visible when
        a module is connected to a parent in the scene. It is indicated by a line segment with
        an arrow showing the parent-child relationship between two modules.
        '''
        
        # Create a segment curve with hierarchy representation (to be attached at the middle position of the curve).
        segment = objects.createRawSegmentCurve(3)
        hierarchyRepr = objects.createRawHierarchyRepresentation('X')

        cmds.setAttr(hierarchyRepr+'.scale', 1.0, 1.0, 1.0, type='double3')
        cmds.makeIdentity(hierarchyRepr, scale=True, apply=True)
        hierarchyReprShape = cmds.listRelatives(hierarchyRepr, children=True, shapes=True)[0]
        cmds.setAttr(hierarchyReprShape+'.overrideColor', 2)
        
        # Place them under the module parenting representation group.
        cmds.parent([segment['curve'], segment['startLoc'], segment['endLoc']], self.moduleParentReprGrp, absolute=True)
                                                        
        # Constrain the start handle for the hierarchy "module parenting" representation
        # to the root node of the current module.
        cmds.pointConstraint(self.nodeJoints[0], segment['startLoc'], maintainOffset=False,
                            name=self.moduleTypespace+':moduleParentRepresentationSegment_startLocator_pointConstraint')
        
        # Constrain the module parenting hierarchy representation arrow (So that it stays at the mid
        # position of the segment curve as created above.
        cmds.pointConstraint(segment['startLoc'], segment['endLoc'], hierarchyRepr, maintainOffset=False,
                                        name=self.moduleTypespace+':moduleParentReprSegment_hierarchyRepr_pointConstraint')

        # Scale constrain the hierarchy representation to the joint in iteration.
        cmds.scaleConstraint(self.nodeJoints[0], hierarchyRepr, maintainOffset=False,
                             name=self.moduleTypespace+':moduleParentReprSegment_hierarchyRepr_scaleConstraint')

        # Aim the hierarchy representation "arrow" with the segment curve's start locator.
        cmds.aimConstraint(segment['startLoc'], hierarchyRepr, maintainOffset=False, aimVector=[1.0, 0.0, 0.0],
                           upVector=[0.0, 1.0, 0.0], worldUpVector=[0.0, 1.0, 0.0], worldUpType='objectRotation',
                           worldUpObject=segment['startLoc'],
                           name=self.moduleTypespace+':moduleParentReprSegment_hierarchyRepr_aimConstraint')

        # Place the hierarchy representation "arrow" under the module parenting representation group.
        cmds.parent(hierarchyRepr, self.moduleParentReprGrp, absolute=True)

        # Rename it.
        cmds.rename(hierarchyRepr, self.moduleTypespace+':moduleParentReprSegment_'+hierarchyRepr)

        # Rename the segment curve.
        cmds.rename(segment['curve'], self.moduleTypespace+':moduleParentReprSegment_'+segment['curve'])
        
        # Rename the 'start' and 'end' locators which drives the segment curve.
        cmds.rename(segment['startLoc'], self.moduleTypespace+':moduleParentReprSegment_'+segment['startLoc'])
        cmds.rename(segment['endLoc'], self.moduleTypespace+':moduleParentReprSegment_'+segment['endLoc'])

        # Clear the selection, and force an update on DG.
        cmds.select(clear=True)
        cmds.setAttr(self.moduleParentReprGrp+'.visibility', 0)


    def createJointNodeModule(self):
        '''
        Create a Joint Node module type.
        '''
        mfunc.updateAllTransforms()

        # Set the current namespace to root.
        cmds.namespace(setNamespace=':')
        
        # Create a new namespace for the module.
        cmds.namespace(add=self.moduleTypespace)
        
        # Create the module container.
        moduleContainer = cmds.container(name=self.moduleContainer)
        
        # Create an empty group for containing module handle segments.
        self.moduleHandleSegmentGrp = cmds.group(empty=True, name=self.moduleTypespace+':moduleHandleSegmentCurveGrp')
        
        # Create an empty group for containing module parenting representations.
        self.moduleParentReprGrp = cmds.group(empty=True, name=self.moduleTypespace+':moduleParentReprGrp')
        
        # Create an empty group for containing module hierarchy/orientation representations.
        self.moduleOrientationHierarchyReprGrp = cmds.group(empty=True,
                                                            name=self.moduleTypespace+':moduleOrientationHierarchyReprGrp')
        
        # Create module representation group containing the above two groups.
        self.moduleReprGrp = cmds.group([self.moduleHandleSegmentGrp, self.moduleOrientationHierarchyReprGrp,
                                                  self.moduleParentReprGrp], name=self.moduleTypespace+':moduleReprObjGrp')
        
        # Create module extras group.
        self.moduleExtrasGrp = cmds.group(empty=True, name=self.moduleTypespace+':moduleExtrasGrp')
        
        # Create group under module extras to keep clusters for scaling node handle shapes.
        self.moduleNodeHandleShapeScaleClusterGrp = cmds.group(empty=True,
                            name=self.moduleTypespace+':moduleNodeHandleShapeScaleClusterGrp', parent=self.moduleExtrasGrp)
        
        # Create main module group.
        self.moduleGrp = cmds.group([self.moduleReprGrp, self.moduleExtrasGrp], name=self.moduleTypespace+':moduleGrp')
        
        # Add a custom attributes to the module group to store module creation attributes.
        cmds.addAttr(self.moduleGrp, attributeType='short', longName='numberOfNodes', defaultValue=self.numNodes, k=False)
        cmds.addAttr(self.moduleGrp, attributeType='float', longName='moduleLength', defaultValue=self.moduleLen, k=False)
        cmds.addAttr(self.moduleGrp, dataType='string', longName='nodeOrient', keyable=False)
        cmds.setAttr(self.moduleGrp+'.nodeOrient', self.nodeAxes, type='string')
        cmds.addAttr(self.moduleGrp, dataType='string', longName='moduleParent', keyable=False)
        cmds.setAttr(self.moduleGrp+'.moduleParent', 'None', type='string')
        cmds.addAttr(self.moduleGrp, dataType='string', longName='onPlane', keyable=False)
        cmds.setAttr(self.moduleGrp+'.onPlane', '+'+self.onPlane, type='string')
        cmds.addAttr(self.moduleGrp, dataType='string', longName='mirrorTranslation', keyable=False)
        cmds.setAttr(self.moduleGrp+'.mirrorTranslation', self.mirrorTranslationFunc, type='string')
        
        # If the current module to be created is a mirror module (on the -ve side of the creation plane).
        if self.mirrorModule:
            cmds.setAttr(self.moduleGrp+'.onPlane', '-'+self.onPlane, type='string')
        
        # If the module is a part of a mirrored module pair. In other words, if module mirroring is turned on.
        # Add module mirroring attributes to the module group. 
        if self.mirrorModuleStatus == 'On':
            cmds.addAttr(self.moduleGrp, dataType='string', longName='mirrorModuleNamespace', keyable=False)
            cmds.setAttr(self.moduleGrp+'.mirrorModuleNamespace', self.mirror_moduleNamespace, type='string')
            cmds.addAttr(self.moduleGrp, dataType='string', longName='mirrorRotation', keyable=False)
            cmds.setAttr(self.moduleGrp+'.mirrorRotation', self.mirrorRotationFunc, type='string')
        
        # Create groups for proxy geometry, if they're enabled.
        if self.proxyGeoStatus:
            if self.proxyGeoElbow or self.proxyGeoBones:
                self.proxyGeoGrp = cmds.group(empty=True, name=self.moduleTypespace+':proxyGeometryGrp')
                cmds.setAttr(self.proxyGeoGrp+'.overrideEnabled', 1)
                cmds.setAttr(self.proxyGeoGrp+'.overrideDisplayType', 2)
                if self.proxyGeoElbow:
                    cmds.addAttr(self.proxyGeoGrp, dataType='string', longName='elbowType', keyable=False)
                    cmds.setAttr(self.proxyGeoGrp+'.elbowType', self.proxyElbowType, type='string', lock=True)
                if self.mirrorModuleStatus == 'On':
                    cmds.addAttr(self.proxyGeoGrp, dataType='string', longName='mirrorInstance', keyable=False)
                    cmds.setAttr(self.proxyGeoGrp+'.mirrorInstance', self.proxyGeoMirrorInstance, type='string', lock=True)

        # Create module nodes group, under the module group.
        self.moduleNodesGrp = cmds.group(empty=True, parent=self.moduleGrp, name=self.moduleTypespace+':moduleNodesGrp')

        # Initialize a list to contain created module node joints.
        self.nodeJoints = []

        # Get the positions of the module nodes, where the called method updates the self.initNodePos.
        self.returnNodeInfoTransformation(self.numNodes)

        # Move the joints group to the start position for the first joint node.
        cmds.xform(self.moduleNodesGrp, worldSpace=True, translation=self.initNodePos[0])

        # Create the module nodes (joints) by their position and name them accordingly.
        for index, nodePos in enumerate(self.initNodePos):
            if index == 0:
                jointName = cmds.joint(name=self.moduleTypespace+':root_node_transform', position=nodePos,
                                                                                radius=0.0, scaleCompensate=False)
            elif nodePos == self.initNodePos[-1]:
                jointName = cmds.joint(name=self.moduleTypespace+':end_node_transform', position=nodePos,
                                                                                radius=0.0, scaleCompensate=False)
            else:
                jointName = cmds.joint(name=self.moduleTypespace+':node_%s_transform'%(index), position=nodePos,
                                                                                radius=0.0, scaleCompensate=False)
            cmds.setAttr(jointName+'.drawStyle', 2)

            mfunc.lockHideChannelAttrs(jointName, 'r', 's', 'v', 'radi', keyable=False)

            self.nodeJoints.append(jointName)

        # Orient the joints.
        cmds.select(self.nodeJoints[0], replace=True)

        # For orientation we'll use the axis perpendicular to the creation plane as the up axis for secondary axis orient.
        secondAxisOrientation = {'XY':'z', 'YZ':'x', 'XZ':'y'}[self.onPlane] + 'up'
        cmds.joint(edit=True, orientJoint=self.nodeAxes.lower(), secondaryAxisOrient=secondAxisOrientation,
                                                                                zeroScaleOrient=True, children=True)
        
        # Orient the end joint node, if the module contains more than one joint node.
        if self.numNodes > 1:
            cmds.setAttr(self.nodeJoints[-1]+'.jointOrientX', 0)
            cmds.setAttr(self.nodeJoints[-1]+'.jointOrientY', 0)
            cmds.setAttr(self.nodeJoints[-1]+'.jointOrientZ', 0)
            
        # Mirror the module node joints (for the mirrored module) if the module mirroring is enabled
        # and the current module to be created is a mirrored module on the -ve side of the creation plane,
        # and if the mirror rotation function is set to "Behaviour".
        if self.mirrorModule:
            mirrorPlane = {'XY':False, 'YZ':False, 'XZ':False}
            mirrorPlane[self.onPlane] = True
            mirroredJoints = cmds.mirrorJoint(self.nodeJoints[0], 
                                              mirrorXY=mirrorPlane['XY'], mirrorYZ=mirrorPlane['YZ'], mirrorXZ=mirrorPlane['XZ'], 
                                              mirrorBehavior=True if self.mirrorRotationFunc == 'Behaviour' else False)
            cmds.delete(self.nodeJoints[0])
            self.nodeJoints = []
            for joint in mirroredJoints:
                newJoint = cmds.rename(joint, self.moduleTypespace+':'+joint)
                self.nodeJoints.append(newJoint)

        # Clear selection after joint orientation.
        cmds.select(clear=True)

        # Create and position the module transform control.
        moduleHandle = objects.createModuleTransform(namespace=self.moduleTypespace, scale=0.26)
        cmds.delete(cmds.pointConstraint(self.nodeJoints[0], moduleHandle['transform'], maintainOffset=False))
        self.moduleTransform = moduleHandle['transform']
        self.collectedNodes.append(moduleHandle['scaleFactor'])

        # Add the module transform to the module group.
        cmds.parent(moduleHandle['preTransform'], self.moduleGrp, absolute=True)

        # Set up constraints for the module transform.
        module_node_parentConstraint = cmds.parentConstraint(self.moduleTransform, self.moduleNodesGrp,
                                maintainOffset=True, name=self.moduleTypespace+':moduleTransform_rootNode_parentConstraint')
        module_node_scaleConstraint = cmds.scaleConstraint(self.moduleTransform, self.moduleNodesGrp,
                                maintainOffset=False, name=self.moduleTypespace+':moduleTransform_rootNode_scaleConstraint')
        
        # Create hierarchy/orientation representation on joint node(s), depending on number of nodes in the module.
        self.createJointNodeControlHandleRepr()
        if len(self.nodeJoints) == 1:
            self.moduleSingleOrientationReprGrp = cmds.group(empty=True,
                                                             name=self.moduleTypespace+':moduleSingleOrientationReprGrp',
                                                             parent=self.moduleReprGrp)
            
            singleOrientationTransform = objects.createRawSingleOrientationRepresentation()
            cmds.setAttr(singleOrientationTransform+'.scale', 0.65, 0.65, 0.65, type='double3')
            cmds.makeIdentity(singleOrientationTransform, scale=True, apply=True)
            cmds.parent(singleOrientationTransform, self.moduleSingleOrientationReprGrp, absolute=True)
            cmds.rename(singleOrientationTransform, self.moduleTypespace+':'+singleOrientationTransform)
            cmds.xform(self.moduleSingleOrientationReprGrp, worldSpace=True, absolute=True,
                                translation=cmds.xform(self.nodeJoints[0], query=True, worldSpace=True, translation=True))
            cmds.parentConstraint(self.nodeJoints[0], self.moduleSingleOrientationReprGrp, maintainOffset=False,
                                                        name=self.moduleSingleOrientationReprGrp+'_parentConstraint')
            cmds.scaleConstraint(self.moduleTransform, self.moduleSingleOrientationReprGrp, maintainOffset=False,
                                                        name=self.moduleSingleOrientationReprGrp+'_scaleConstraint')
        
        nodeHandles = []
        
        # Set the sizes for the module node handle shapes.
        for joint in self.nodeJoints:
        
            handle = objects.load_xhandleShape(transform=joint, colour=self.modHandleColour)
            cmds.setAttr(handle['shape']+'.localScaleX', 0.089)
            cmds.setAttr(handle['shape']+'.localScaleY', 0.089)
            cmds.setAttr(handle['shape']+'.localScaleZ', 0.089)
            cmds.setAttr(handle['shape']+'.ds', 5)

            nodeHandles.append(handle)

        # If there's more than one node, create orientation/hierarchy representations for all joints, except for
        # the end joint. Also unparent the individual joints in the oriented joint chain to the joint group. This
        # is needed only if there are more than one joint in the module; then the unparenting will begin from the
        # second joint, since the first (start) is already under joints group.
        if len(self.nodeJoints) > 1:
            for handle in nodeHandles[1:]:
                cmds.parent(handle['preTransform'], self.moduleNodesGrp, absolute=True)
            self.createOrientationHierarchyReprOnNodes()

        # Clear selection.
        cmds.select(clear=True)

        # If the module contains only one node then delete the handle segment and orientation/hierarchy
        # representation groups, since they're not needed.
        if self.numNodes == 1:
            cmds.delete([self.moduleHandleSegmentGrp, self.moduleOrientationHierarchyReprGrp])

        # Create module parenting representation objects.
        self.createHierarchySegmentForModuleParentingRepr()

        # Create the proxy geometry for the module if it is enabled.
        if self.proxyGeoStatus:
            if self.proxyGeoElbow:
                self.createProxyGeo_elbows(self.proxyElbowType)
            if self.proxyGeoBones:
                self.createProxyGeo_bones()

        # Add the module group to the collected nodes list.
        self.collectedNodes.append(self.moduleGrp)
        
        # Add the collected nodes to the module container.
        mfunc.addNodesToContainer(self.moduleContainer, self.collectedNodes, includeHierarchyBelow=True, includeShapes=True)        
        
        # Publish contents to the container.
        # Publish the orientation representation control for module nodes.
        for joint in self.nodeJoints:
            jointName = mfunc.stripMRTNamespace(joint)[1]   # Nice name for the joint, used as published name.
            cmds.container(self.moduleContainer, edit=True, publishAndBind=[joint+'.translate', jointName+'_translate'])
            if joint != self.nodeJoints[-1]:
                jointOrientationRepr = joint + '_orient_repr_transform'
                jointOrientationRotateAxis = self.nodeAxes[0]
                jointOrientationReprName = mfunc.stripMRTNamespace(jointOrientationRepr)[1]
                cmds.container(self.moduleContainer, edit=True,
                               publishAndBind=[jointOrientationRepr+'.rotate'+jointOrientationRotateAxis,
                                               jointOrientationReprName+'_rotate'+jointOrientationRotateAxis])

        # Publish the attributes for the module transform.
        moduleTransformName = mfunc.stripMRTNamespace(self.moduleTransform)[1]
        cmds.container(self.moduleContainer, edit=True, publishAndBind=[self.moduleTransform+'.translate',
                                                                        moduleTransformName+'_translate'])
        cmds.container(self.moduleContainer, edit=True, publishAndBind=[self.moduleTransform+'.rotate',
                                                                        moduleTransformName+'_rotate'])
        cmds.container(self.moduleContainer, edit=True, publishAndBind=[self.moduleTransform+'.globalScale',
                                                                        moduleTransformName+'_globalScale'])
        cmds.container(self.moduleContainer, edit=True, publishAndBind=[self.moduleTransform+'.scaleFactor',
                                                                        moduleTransformName+'_scaleFactor'])        

        # If the module contains only single node, publish its orientation control.
        if len(self.nodeJoints) == 1:
            singleOrientationTransform = self.moduleTypespace+':single_orient_repr_transform'
            cmds.container(self.moduleContainer, edit=True, publishAndBind=[singleOrientationTransform+'.rotate',
                                                                           'single_orient_repr_transform_rotate'])
        # Add and publish custom attributes on the module transform.
        self.addCustomAttributesOnModuleTransform()
        
        # Connect module orientation representation objects to drive 
        # orientation for module proxy geometry.
        if self.numNodes > 1:
            self.connectCustomOrientationReprToModuleProxies()

        # Set the module pre-scale factor. This is used for adjusting the initial size of the module.
        cmds.setAttr(self.moduleTransform+'.scaleFactor', 30)


    def createSplineNodeModule(self, *args):
        '''
        Create a Spline Node module type.
        Unlike other module node types, the nodes cannot be translated directly.
        '''
        mfunc.updateAllTransforms()
        
        # Set the current namespace to root.
        cmds.namespace(setNamespace=':')
        
        # Create a new namespace for the module.
        cmds.namespace(add=self.moduleTypespace)
        
        # Create the module container.
        moduleContainer = cmds.container(name=self.moduleContainer)
        
        # Create an empty group for containing module handle segments.
        self.moduleSplineCurveGrp = cmds.group(empty=True, name=self.moduleTypespace+':moduleSplineCurveGrp')
        
        # Create an empty group for containing module hierarchy/orientation representations.
        self.moduleHandleGrp = cmds.group(empty=True, name=self.moduleTypespace+':moduleHandleGrp')
        
        # Create an empty group for containing module parenting representations.
        self.moduleParentReprGrp = cmds.group(empty=True, name=self.moduleTypespace+':moduleParentReprGrp')
        
        # Create an empty group for containing splineAdjustCurveTransform.
        self.moduleSplineAdjustCurveGrp = cmds.group(empty=True, name=self.moduleTypespace+':moduleSplineAdjustCurveGrp')
        
        # Create an empty group for containing orientation representation transforms and nodes.
        self.moduleOrientationReprGrp = cmds.group(empty=True, name=self.moduleTypespace+':moduleOrientationReprGrp')
        
        # Create a module representation group containing the above four groups.
        self.moduleReprGrp = cmds.group([self.moduleSplineAdjustCurveGrp, self.moduleSplineCurveGrp, self.moduleHandleGrp, 
                    self.moduleOrientationReprGrp, self.moduleParentReprGrp], name=self.moduleTypespace+':moduleReprObjGrp')

        # Create a main module group, with the representation group as the child.
        self.moduleGrp = cmds.group([self.moduleReprGrp], name=self.moduleTypespace+':moduleGrp')
        
        # Add a custom attributes to the module group to store module creation attributes.
        cmds.addAttr(self.moduleGrp, attributeType='short', longName='numberOfNodes', defaultValue=self.numNodes, keyable=False)
        cmds.addAttr(self.moduleGrp, attributeType='float', longName='moduleLength', defaultValue=self.moduleLen, keyable=False)
        cmds.addAttr(self.moduleGrp, dataType='string', longName='nodeOrient', keyable=False)
        cmds.setAttr(self.moduleGrp+'.nodeOrient', self.nodeAxes, type='string')
        cmds.addAttr(self.moduleGrp, dataType='string', longName='moduleParent', keyable=False)
        cmds.setAttr(self.moduleGrp+'.moduleParent', 'None', type='string')
        cmds.addAttr(self.moduleGrp, dataType='string', longName='onPlane', keyable=False)
        cmds.setAttr(self.moduleGrp+'.onPlane', '+'+self.onPlane, type='string')
        cmds.addAttr(self.moduleGrp, dataType='string', longName='mirrorTranslation', keyable=False)
        cmds.setAttr(self.moduleGrp+'.mirrorTranslation', self.mirrorTranslationFunc, type='string')
        
        self.collectedNodes.append(self.moduleGrp)
        
        # If the current module to be created is a mirror module (on the -ve side of the creation plane).
        if self.mirrorModule:
            cmds.setAttr(self.moduleGrp+'.onPlane', '-'+self.onPlane, type='string')
    
        # If the module is a part of a mirrored module pair. In other words, if module mirroring is turned on.
        # Add module mirroring attributes to the module group. 
        if self.mirrorModuleStatus == 'On':
            cmds.addAttr(self.moduleGrp, dataType='string', longName='mirrorModuleNamespace', keyable=False)
            cmds.setAttr(self.moduleGrp+'.mirrorModuleNamespace', self.mirror_moduleNamespace, type='string')
            cmds.addAttr(self.moduleGrp, dataType='string', longName='mirrorRotation', keyable=False)
            cmds.setAttr(self.moduleGrp+'.mirrorRotation', self.mirrorRotationFunc, type='string')
    
        # Create a group for proxy geometry.
        if self.proxyGeoStatus and self.proxyGeoElbow:
            self.proxyGeoGrp = cmds.group(empty=True, name=self.moduleTypespace+':proxyGeometryGrp')
            cmds.setAttr(self.proxyGeoGrp+'.overrideEnabled', 1)
            cmds.setAttr(self.proxyGeoGrp+'.overrideDisplayType', 2)
            cmds.addAttr(self.proxyGeoGrp, dataType='string', longName='elbowType', keyable=False)
            cmds.setAttr(self.proxyGeoGrp+'.elbowType', self.proxyElbowType, type='string', lock=True)
            if self.mirrorModuleStatus == 'On':
                cmds.addAttr(self.proxyGeoGrp, dataType='string', longName='mirrorInstance', keyable=False)
                cmds.setAttr(self.proxyGeoGrp+'.mirrorInstance', self.proxyGeoMirrorInstance, type='string', lock=True)
        
        # Create a module nodes group, under the module group.
        self.moduleNodesGrp = cmds.group(empty=True, parent=self.moduleGrp, name=self.moduleTypespace+':moduleNodesGrp')
        
        # Initialize a list to contain created module node joints.
        self.nodeJoints = []
        
        # Get the positions of the module nodes, where the called method updates the self.initNodePos.
        self.returnNodeInfoTransformation(numNodes=4)
        
        # Create the spline module curve
        splineNodeCurve = cmds.curve(degree=1, point=self.initNodePos)
        cmds.xform(splineNodeCurve, centerPivots=True)
        cmds.rebuildCurve(splineNodeCurve, constructionHistory=False, replaceOriginal=True, rebuildType=0, degree=3,
                          endKnots=True, keepEndPoints=True, keepRange=0, keepControlPoints=False, keepTangents=False,
                          spans=3, tolerance=0.01)
        splineNodeCurve = cmds.rename(splineNodeCurve, self.moduleTypespace+':splineNode_curve')
        cmds.displaySmoothness(splineNodeCurve, pointsWire=32)
        cmds.toggle(splineNodeCurve, template=True, state=True)
        cmds.parent(splineNodeCurve, self.moduleSplineCurveGrp, absolute=True)
        
        # Get the shape for the module spline curve.
        splineNodeCurveShape = cmds.listRelatives(splineNodeCurve, children=True, type='nurbsCurve')[0]        

        cmds.select(clear=True)

        self.returnNodeInfoTransformation(self.numNodes)
        
        # Create the module node joints, to be attached to the spline module curve.
        self.nodeJoints = []
        for index in range(len(self.initNodePos)):
            if index == 0:
                jointName = cmds.joint(name=self.moduleTypespace+':root_node_transform', position=self.initNodePos[index], radius=0.0)
            elif index == len(self.initNodePos)-1:
                jointName = cmds.joint(name=self.moduleTypespace+':end_node_transform', position=self.initNodePos[index], radius=0.0)
            else:
                jointName = cmds.joint(name=self.moduleTypespace+':node_%s_transform'%(index), position=self.initNodePos[index], radius=0.0)
            self.nodeJoints.append(jointName)

        # Orient the node joints.
        # For orientation we'll use the axis perpendicular to the creation plane as the up axis for secondary axis orient.
        cmds.select(self.nodeJoints[0], replace=True)
        secondAxisOrientation = {'XY':'z', 'YZ':'x', 'XZ':'y'}[self.onPlane] + 'up'
        cmds.joint(edit=True, orientJoint=self.nodeAxes.lower(), secondaryAxisOrient=secondAxisOrientation,
                                                                        zeroScaleOrient=True, children=True)
        cmds.parent(self.nodeJoints[0], self.moduleNodesGrp, absolute=True)
        
        # Orient the end joint node.
        cmds.setAttr(self.nodeJoints[-1]+'.jointOrientX', 0)
        cmds.setAttr(self.nodeJoints[-1]+'.jointOrientY', 0)
        cmds.setAttr(self.nodeJoints[-1]+'.jointOrientZ', 0)
        
        # Mirror the module node joints (for the mirrored module) if the module mirroring is enabled
        # and the current module to be created is a mirrored module on the -ve side of the creation plane,
        # and if the mirror rotation function is set to "Behaviour".
        if self.mirrorModule:
            mirrorPlane = {'XY':False, 'YZ':False, 'XZ':False}
            mirrorPlane[self.onPlane] = True
            mirroredJoints = cmds.mirrorJoint(self.nodeJoints[0], 
                                              mirrorXY=mirrorPlane['XY'], mirrorYZ=mirrorPlane['YZ'], mirrorXZ=mirrorPlane['XZ'], 
                                              mirrorBehavior=True if self.mirrorRotationFunc == 'Behaviour' else False)
            cmds.delete(self.nodeJoints[0])
            self.nodeJoints = []
            for joint in mirroredJoints:
                newJoint = cmds.rename(joint, self.moduleTypespace+':'+joint)
                self.nodeJoints.append(newJoint)

        # Clear selection after joint orientation.
        cmds.select(clear=True)

        # Unparent the spline node joints.
        for joint in self.nodeJoints[1:]:
            cmds.parent(joint, self.moduleNodesGrp, absolute=True)
        
        # Create the start module transform to the module, at the position of the root node.
        startHandle = objects.createModuleTransform(namespace=self.moduleTypespace, name='splineStartHandleTransform',
                                                    scale=0.4, colour=11, drawStyle=3, drawOrtho=1)
        self.moduleTransform = startHandle['transform']
        self.collectedNodes.append(startHandle['scaleFactor'])
        
        # Position the start module transform and constrain the start cluster to it. This is also the main module transform.
        cmds.delete(cmds.pointConstraint(self.nodeJoints[0], startHandle['transform'], maintainOffset=False))
        cmds.parent(startHandle['preTransform'], self.moduleHandleGrp, absolute=True)
        
        # Create the end module transform, at the position of the last node for the module.
        endHandle = objects.createModuleTransform(namespace=self.moduleTypespace, name='splineEndHandleTransform',
                                                    scale=0.35, colour=10, drawStyle=3, drawOrtho=1, isOnlyControl=True)
        
        mfunc.lockHideChannelAttrs(endHandle['transform'], keyable=False)
        
        # Position the end module transform and constrain the end cluster to it.
        cmds.delete(cmds.pointConstraint(self.nodeJoints[-1], endHandle['preTransform'], maintainOffset=False))
    
        # Parent the end handle to the start handle.
        cmds.parent(endHandle['preTransform'], startHandle['transform'], absolute=True)    
        
        # Create the spline module curve adjust control transforms. These are used to modify the 
        # spline curve and hence affect the positions of the module nodes.
        splineAdjustCurveTransformList = []
        
        for (index, startWeight, endWeight) in [(0, 1, 0), (1, 0.66, 0.33), (2, 0.33, 0.66), (3, 0, 1)]:
            
            # Create the curve adjust control transform.
            splineAdjustCurveTransforms = objects.createRawSplineAdjustCurveTransform(self.modHandleColour)
            cmds.setAttr(splineAdjustCurveTransforms[0]+'.scale', 0.8, 0.8, 0.8, type='double3')
            cmds.makeIdentity(splineAdjustCurveTransforms[0], scale=True, apply=True)
            
            splineAdjustCurvePreTransform = cmds.rename(splineAdjustCurveTransforms[0], '%s:%s_%s_%s' \
                                                                            % (self.moduleTypespace,
                                                                               splineAdjustCurveTransforms[0].partition('_')[0],
                                                                               index+1,
                                                                               splineAdjustCurveTransforms[0].partition('_')[2]))
            splineAdjustCurveTransform = cmds.rename(splineAdjustCurveTransforms[1], '%s:%s_%s_%s' \
                                                                         % (self.moduleTypespace,
                                                                            splineAdjustCurveTransforms[1].partition('_')[0],
                                                                            index+1,
                                                                            splineAdjustCurveTransforms[1].partition('_')[2]))
                                                                            
            splineAdjustCurveTransformList.append(splineAdjustCurveTransform)
            
            # Get the world space position for the curve adjust transform to drive the point(s) for the spline module curve.
            splineAdjustCurveWorldPosVectorProduct = cmds.createNode('vectorProduct', name=splineAdjustCurveTransform+'_worldPos_vectorProduct')
            cmds.setAttr(splineAdjustCurveWorldPosVectorProduct+'.operation', 4)
            splineAdjustCurveTransformShape = cmds.listRelatives(splineAdjustCurveTransform, children=True, type='nurbsCurve')[0]
            cmds.connectAttr(splineAdjustCurveTransformShape+'.worldMatrix', splineAdjustCurveWorldPosVectorProduct+'.matrix')            
            self.collectedNodes.append(splineAdjustCurveWorldPosVectorProduct)
            
            if index == 0:
                cmds.connectAttr(splineAdjustCurveWorldPosVectorProduct+'.output', splineNodeCurveShape+'.controlPoints[0]')
                cmds.connectAttr(splineAdjustCurveWorldPosVectorProduct+'.output', splineNodeCurveShape+'.controlPoints[1]')
            elif index == 3:
                cmds.connectAttr(splineAdjustCurveWorldPosVectorProduct+'.output', splineNodeCurveShape+'.controlPoints[4]')
                cmds.connectAttr(splineAdjustCurveWorldPosVectorProduct+'.output', splineNodeCurveShape+'.controlPoints[5]')                
            else:
                cmds.connectAttr(splineAdjustCurveWorldPosVectorProduct+'.output', splineNodeCurveShape+'.controlPoints[%s]'% (index+1))
            
            # Constrain the curve adjust control pre-transform to spline module start and end transforms.
            startPointConstraint = cmds.pointConstraint(startHandle['transform'], splineAdjustCurvePreTransform, maintainOffset=False,
                                                        weight=startWeight, name=splineAdjustCurvePreTransform+'_startHandle_pointConstraint')
            endPointConstraint = cmds.pointConstraint(endHandle['transform'], splineAdjustCurvePreTransform, maintainOffset=False,
                                                        weight=endWeight, name=splineAdjustCurvePreTransform+'_endHandle_pointConstraint')

            cmds.parent(splineAdjustCurvePreTransform, self.moduleSplineAdjustCurveGrp, absolute=True)
            
            # Get the last spline curve adjust transform as the up vector target object for orienting 
            # the module nodes attached to the spline module curve.
            if index == 3:
                tangentConstraintTargetObject = splineAdjustCurveTransform


        # Calculate the u-parameters on the spline module curve for the node positions and attach them.
        temp_cpoc = cmds.createNode('nearestPointOnCurve', skipSelect=True)
        cmds.connectAttr(splineNodeCurveShape+'.worldSpace', temp_cpoc+'.inputCurve')
        
        for nodePos, nodeJoint in zip(self.initNodePos, self.nodeJoints):
            
            cmds.setAttr(temp_cpoc+'.inPosition', *nodePos, type='double3')
            node_u_param = cmds.getAttr(temp_cpoc+'.parameter')
            
            if node_u_param == 0:
                node_u_param = 0.001
            if node_u_param == 1:
                node_u_param = 0.999
                
            pointOnCurveInfo = cmds.createNode('pointOnCurveInfo', name='%s:%s_pointOnCurveInfo' % (self.moduleTypespace,
                                                                                    mfunc.stripMRTNamespace(nodeJoint)[1]))  
            cmds.setAttr(pointOnCurveInfo+'.turnOnPercentage', 1)
            cmds.connectAttr(splineNodeCurveShape+'.worldSpace', pointOnCurveInfo+'.inputCurve')
            cmds.connectAttr(pointOnCurveInfo+'.position', nodeJoint+'.translate')
            cmds.setAttr(pointOnCurveInfo+'.parameter', node_u_param)
            self.collectedNodes.append(pointOnCurveInfo)
            
        cmds.delete(temp_cpoc)
        

        # Set-up / connect orientations for the module node joints attached to the spline module curves.
        worldReferenceTransform = cmds.createNode('transform', name=self.moduleTypespace+':orientationWorldReferenceTransform',
                                                                                            parent=self.moduleOrientationReprGrp)
        aimVector={'X':[1.0, 0.0, 0.0], 'Y':[0.0, 1.0, 0.0], 'Z':[0.0, 0.0, 1.0]}[self.nodeAxes[0]]
        upVector = {'X':[1.0, 0.0, 0.0], 'Y':[0.0, 1.0, 0.0], 'Z':[0.0, 0.0, 1.0]}[self.nodeAxes[1]]
        worldUpVector = {'XY':[0.0, 0.0, 1.0], 'YZ':[1.0, 0.0, 0.0], 'XZ':[0.0, 1.0, 0.0]}[self.onPlane]
        if self.mirrorModule and self.mirrorRotationFunc == 'Behaviour':
            aimVector = [i*-1 for i in aimVector]
        pairBlend_inputDriven = []
        
        for index in range(len(self.nodeJoints)):
            pairBlend = cmds.createNode('pairBlend', name=self.nodeJoints[index]+'_pairBlend', skipSelect=True)
            pairBlend_inputDriven.append(pairBlend)
            
            orientConstraint = cmds.orientConstraint(worldReferenceTransform, self.nodeJoints[index], maintainOffset=False,
                                                                            name=self.nodeJoints[index]+'_orientConstraint')[0]
                                                                            
            cmds.disconnectAttr(orientConstraint+'.constraintRotateX', self.nodeJoints[index]+'.rotateX')
            cmds.disconnectAttr(orientConstraint+'.constraintRotateY', self.nodeJoints[index]+'.rotateY')
            cmds.disconnectAttr(orientConstraint+'.constraintRotateZ', self.nodeJoints[index]+'.rotateZ')
            
            tangentConstraint = cmds.tangentConstraint(self.moduleTypespace+':splineNode_curve', self.nodeJoints[index],
                                                        aimVector=aimVector, upVector=upVector, worldUpType='objectrotation',
                                                            worldUpVector=worldUpVector, worldUpObject=tangentConstraintTargetObject,
                                                                name=self.nodeJoints[index]+'_tangentConstraint')[0]
                                                                
            cmds.disconnectAttr(tangentConstraint+'.constraintRotateX', self.nodeJoints[index]+'.rotateX')
            cmds.disconnectAttr(tangentConstraint+'.constraintRotateY', self.nodeJoints[index]+'.rotateY')
            cmds.disconnectAttr(tangentConstraint+'.constraintRotateZ', self.nodeJoints[index]+'.rotateZ')
            cmds.connectAttr(orientConstraint+'.constraintRotateX', pairBlend+'.inRotateX1')
            cmds.connectAttr(orientConstraint+'.constraintRotateY', pairBlend+'.inRotateY1')
            cmds.connectAttr(orientConstraint+'.constraintRotateZ', pairBlend+'.inRotateZ1')
            cmds.connectAttr(tangentConstraint+'.constraintRotateX', pairBlend+'.inRotateX2')
            cmds.connectAttr(tangentConstraint+'.constraintRotateY', pairBlend+'.inRotateY2')
            cmds.connectAttr(tangentConstraint+'.constraintRotateZ', pairBlend+'.inRotateZ2')
            cmds.connectAttr(pairBlend+'.outRotateX', self.nodeJoints[index]+'.rotateX')
            cmds.connectAttr(pairBlend+'.outRotateY', self.nodeJoints[index]+'.rotateY')
            cmds.connectAttr(pairBlend+'.outRotateZ', self.nodeJoints[index]+'.rotateZ')
            cmds.setAttr(pairBlend+'.rotateMode', 2)
            
        self.collectedNodes.extend(pairBlend_inputDriven)
        
        # Remove all tweaks from spline module curve history.
        clusterNodes = cmds.listConnections(splineNodeCurve+'Shape', source=True, destination=True)
        for node in clusterNodes:
            if cmds.nodeType(node) == 'tweak':
                cmds.delete(node)
                break
        
        # Create the local axes info representation objects for the module nodes.
        # These objects indicate the current orientation of the module nodes.
        rawLocaAxesInfoReprTransforms = []
        for joint in self.nodeJoints:
            rawLocalAxesInfoReprTransforms = objects.createRawLocalAxesInfoRepresentation()
            cmds.setAttr(rawLocalAxesInfoReprTransforms[0]+'.scale', 0.8, 0.8, 0.8, type='double3')
            cmds.makeIdentity(rawLocalAxesInfoReprTransforms[0], scale=True, apply=True)
            cmds.parent(rawLocalAxesInfoReprTransforms[0], self.moduleOrientationReprGrp)

            rawLocaAxesInfoReprPreTransform = cmds.rename(rawLocalAxesInfoReprTransforms[0],
                                                                        joint+'_'+rawLocalAxesInfoReprTransforms[0])
            rawLocaAxesInfoReprTransform = cmds.rename(rawLocalAxesInfoReprTransforms[1],
                                                                        joint+'_'+rawLocalAxesInfoReprTransforms[1])
            
            # Add an attribute to modify the up vector rotation for the axes info object.
            # Can be used to flip the axial orientation for the module node.
            cmds.addAttr(rawLocaAxesInfoReprTransform, attributeType='enum', longName='tangent_Up_vector',
                                                        enumName='Original:Reversed:', defaultValue=0, keyable=True)

            for (driver, driven) in ((1, -1), (0, 1)):
                cmds.setAttr(rawLocaAxesInfoReprTransform+'.tangent_Up_vector', driver)
                cmds.setAttr(joint+'_tangentConstraint.upVector'+self.nodeAxes[1].upper(), driven)
                cmds.setDrivenKeyframe(joint+'_tangentConstraint.upVector'+self.nodeAxes[1].upper(),
                                                currentDriver=rawLocaAxesInfoReprTransform+'.tangent_Up_vector')

            xhandle = objects.load_xhandleShape(transform=joint, colour=2, transformOnly=True)
            cmds.setAttr(xhandle['shape']+'.localScaleX', 0.09)
            cmds.setAttr(xhandle['shape']+'.localScaleY', 0.09)
            cmds.setAttr(xhandle['shape']+'.localScaleZ', 0.09)
            cmds.setAttr(xhandle['shape']+'.ds', 5)

            cmds.pointConstraint(joint, rawLocaAxesInfoReprPreTransform, maintainOffset=False,
                                                        name=rawLocaAxesInfoReprPreTransform+'_pointConstraint')
            cmds.orientConstraint(joint, rawLocaAxesInfoReprPreTransform, maintainOffset=False,
                                                        name=rawLocaAxesInfoReprPreTransform+'_orientConstraint')

            rawLocaAxesInfoReprTransforms.append(rawLocaAxesInfoReprTransform)

        cmds.select(clear=True)
        
        # Create module parenting representation objects.
        self.createHierarchySegmentForModuleParentingRepr()
        
        # Create the proxy geometry for the module if enabled.
        if self.proxyGeoStatus and self.proxyGeoElbow:
            self.createProxyGeo_elbows(self.proxyElbowType)
        
        # Add the collected nodes to the module container.
        mfunc.addNodesToContainer(self.moduleContainer, self.collectedNodes, includeHierarchyBelow=True, includeShapes=True)          

        # Publish the translation attributes for the start (and rotate) and end module transforms.
        cmds.container(self.moduleContainer, edit=True, publishAndBind=[startHandle['transform']+'.translate',
                                                        mfunc.stripMRTNamespace(startHandle['transform'])[1]+'_translate'])
        cmds.container(self.moduleContainer, edit=True, publishAndBind=[startHandle['transform']+'.rotate',
                                                        mfunc.stripMRTNamespace(startHandle['transform'])[1]+'_rotate'])
        cmds.container(self.moduleContainer, edit=True, publishAndBind=[self.moduleTransform+'.globalScale', 'module_globalscale'])
        cmds.container(self.moduleContainer, edit=True, publishAndBind=[self.moduleTransform+'.scaleFactor', 'module_scaleFactor'])
        cmds.container(self.moduleContainer, edit=True, publishAndBind=[endHandle['transform']+'.translate',
                                                        mfunc.stripMRTNamespace(endHandle['transform'])[1]+'_translate'])
        for transform in splineAdjustCurveTransformList:
            cmds.container(self.moduleContainer, edit=True, publishAndBind=[transform+'.translate',
                                                        mfunc.stripMRTNamespace(transform)[1]+'_translate'])
        
        # Add the necessary module attributes on the start module transform.
        self.addCustomAttributesOnModuleTransform()
        
        # Connect the module global scaling to the spline module curve adjust transforms group.
        cmds.connectAttr(self.moduleTransform+'.finalScale', self.moduleSplineAdjustCurveGrp+'.scaleX')
        cmds.connectAttr(self.moduleTransform+'.finalScale', self.moduleSplineAdjustCurveGrp+'.scaleY')
        cmds.connectAttr(self.moduleTransform+'.finalScale', self.moduleSplineAdjustCurveGrp+'.scaleZ')        

        # Connect the module global scaling to the module node joints.
        for joint in self.nodeJoints:
            cmds.connectAttr(self.moduleTransform+'.finalScale', joint+'.scaleX')
            cmds.connectAttr(self.moduleTransform+'.finalScale', joint+'.scaleY')
            cmds.connectAttr(self.moduleTransform+'.finalScale', joint+'.scaleZ')
            cmds.connectAttr(self.moduleTransform+'.finalScale', joint+'_localAxesInfoRepr_preTransform.scaleX')
            cmds.connectAttr(self.moduleTransform+'.finalScale', joint+'_localAxesInfoRepr_preTransform.scaleY')
            cmds.connectAttr(self.moduleTransform+'.finalScale', joint+'_localAxesInfoRepr_preTransform.scaleZ')
        
        # Connect the module node orientation attributes on the start module transform.
        cmds.connectAttr(self.moduleTransform+'.Node_Orientation_Info', self.moduleOrientationReprGrp+'.visibility')
        for transform in rawLocaAxesInfoReprTransforms:
            rotateAxis = self.nodeAxes[0]
            cmds.container(self.moduleContainer, edit=True, publishAndBind=[transform+'.tangent_Up_vector',
                                                        mfunc.stripMRTNamespace(transform)[1]+'_tangent_Up_Vector'])
            cmds.connectAttr(self.moduleTransform+'.Axis_Rotate', transform+'.rotate'+rotateAxis)
            cmds.connectAttr(self.moduleTransform+'.Node_Local_Orientation_Repr_Size', transform+'.scaleX')
            cmds.connectAttr(self.moduleTransform+'.Node_Local_Orientation_Repr_Size', transform+'.scaleY')
            cmds.connectAttr(self.moduleTransform+'.Node_Local_Orientation_Repr_Size', transform+'.scaleZ')

        cmds.setAttr(self.moduleTransform+'.Node_Local_Orientation_Repr_Size', 0.7)
        
        # Add any previous set-driven keyframe nodes to the module container.
        cmds.namespace(setNamespace=self.moduleTypespace)
        namespaceNodes = cmds.namespaceInfo(listOnlyDependencyNodes=True)
        animCurveNodes = cmds.ls(namespaceNodes, type='animCurve')
        mfunc.addNodesToContainer(self.moduleContainer, animCurveNodes)
        
        cmds.namespace(setNamespace=':')
        
        # If orientation representation is turned off for modules, turn off 
        # node orientation representation objects.
        if not self.showOrientation:
            cmds.setAttr(startHandle['transform']+'.Node_Orientation_Info', 0)
            
        # Connect module orientation representation objects to drive 
        # orientation for module proxy geometry.
        self.connectCustomOrientationReprToModuleProxies()
        
        # Set the module pre-scale factor. This is used for adjusting the initial size of the module.
        cmds.setAttr(self.moduleTransform+'.scaleFactor', 30)


    def createHingeNodeModule(self):
        '''
        Create a Hinge Node module type.
        '''
        mfunc.updateAllTransforms()
        
        # Set the current namespace to root.
        cmds.namespace(setNamespace=':')
        
        # Create a new namespace for the module.
        cmds.namespace(add=self.moduleTypespace)
        
        # Clear selection.
        cmds.select(clear=True)
        
        # Create the module container.
        moduleContainer = cmds.container(name=self.moduleContainer)
        
        # Create an empty group for containing module handle segments.
        self.moduleHandleSegmentGrp = cmds.group(empty=True, name=self.moduleTypespace+':moduleHandleSegmentCurveGrp')
        
        # Create an empty group for containing module parenting representations.
        self.moduleParentReprGrp = cmds.group(empty=True, name=self.moduleTypespace+':moduleParentReprGrp')
        
        # Create an empty group for containing module hand hierarchy representations.
        self.moduleHierarchyReprGrp = cmds.group(empty=True, name=self.moduleTypespace+':moduleHierarchyReprGrp')
        
        # Create a module representation group containing the above two groups.
        self.moduleReprGrp = cmds.group([self.moduleHandleSegmentGrp, self.moduleHierarchyReprGrp, self.moduleParentReprGrp],
                                                                                name=self.moduleTypespace+':moduleReprObjGrp')
        
        # Create a module extras group.
        self.moduleExtrasGrp = cmds.group(empty=True, name=self.moduleTypespace+':moduleExtrasGrp')
        
        # Create a group under module extras to keep clusters for scaling node handle shapes.
        self.moduleNodeHandleShapeScaleClusterGrp = cmds.group(empty=True, name=self.moduleTypespace+':moduleNodeHandleShapeScaleClusterGrp',
                                                                                                                    parent=self.moduleExtrasGrp)
        
        # Create a group under module extras to keep the IK segment aim nodes.
        self.moduleIKsegmentMidAimGrp = cmds.group(empty=True, name=self.moduleTypespace+':moduleIKsegmentMidAimGrp',
                                                                                            parent=self.moduleExtrasGrp)
        
        # Create a group to contain the IK nodes and handles.
        self.moduleIKnodesGrp = cmds.group(empty=True, name=self.moduleTypespace+':moduleIKnodesGrp')
        
        # Create a main module group.
        self.moduleGrp = cmds.group([self.moduleReprGrp, self.moduleExtrasGrp, self.moduleIKnodesGrp],
                                                                    name=self.moduleTypespace+':moduleGrp')

        # Add a custom attributes to the module group to store module creation attributes.
        cmds.addAttr(self.moduleGrp, attributeType='short', longName='numberOfNodes', defaultValue=self.numNodes, keyable=False)
        cmds.addAttr(self.moduleGrp, attributeType='float', longName='moduleLength', defaultValue=self.moduleLen, keyable=False)
        cmds.addAttr(self.moduleGrp, dataType='string', longName='nodeOrient', keyable=False)
        cmds.setAttr(self.moduleGrp+'.nodeOrient', self.nodeAxes, type='string')
        cmds.addAttr(self.moduleGrp, dataType='string', longName='moduleParent', keyable=False)
        cmds.setAttr(self.moduleGrp+'.moduleParent', 'None', type='string')
        cmds.addAttr(self.moduleGrp, dataType='string', longName='onPlane', keyable=False)
        cmds.setAttr(self.moduleGrp+'.onPlane', '+'+self.onPlane, type='string')
        cmds.addAttr(self.moduleGrp, dataType='string', longName='mirrorTranslation', keyable=False)
        cmds.setAttr(self.moduleGrp+'.mirrorTranslation', self.mirrorTranslationFunc, type='string')
        
        # If the current module to be created is a mirror module (on the -ve side of the creation plane).
        if self.mirrorModule:
            cmds.setAttr(self.moduleGrp+'.onPlane', '-'+self.onPlane, type='string')
            
        # If the module is a part of a mirrored module pair. In other words, if module mirroring is turned on.
        # Add module mirroring attributes to the module group. 
        if self.mirrorModuleStatus == 'On':
            cmds.addAttr(self.moduleGrp, dataType='string', longName='mirrorModuleNamespace', keyable=False)
            cmds.setAttr(self.moduleGrp+'.mirrorModuleNamespace', self.mirror_moduleNamespace, type='string')
            cmds.addAttr(self.moduleGrp, dataType='string', longName='mirrorRotation', keyable=False)
            cmds.setAttr(self.moduleGrp+'.mirrorRotation', self.mirrorRotationFunc, type='string')
        
        # Create groups for proxy geometry, if they're enabled.
        if self.proxyGeoStatus:
            if self.proxyGeoElbow or self.proxyGeoBones:
                self.proxyGeoGrp = cmds.group(empty=True, name=self.moduleTypespace+':proxyGeometryGrp')
                cmds.setAttr(self.proxyGeoGrp+'.overrideEnabled', 1)
                cmds.setAttr(self.proxyGeoGrp+'.overrideDisplayType', 2)
                if self.proxyGeoElbow:
                    cmds.addAttr(self.proxyGeoGrp, dataType='string', longName='elbowType', keyable=False)
                    cmds.setAttr(self.proxyGeoGrp+'.elbowType', self.proxyElbowType, type='string', lock=True)
                if self.mirrorModuleStatus == 'On':
                    cmds.addAttr(self.proxyGeoGrp, dataType='string', longName='mirrorInstance', keyable=False)
                    cmds.setAttr(self.proxyGeoGrp+'.mirrorInstance', self.proxyGeoMirrorInstance, type='string', lock=True)
        
        # Create a main module nodes group, under the module group.
        self.moduleNodesGrp = cmds.group(empty=True, parent=self.moduleGrp, name=self.moduleTypespace+':moduleNodesGrp')
        
        # Initialize a list to contain created module node joints.
        self.nodeJoints = []
        
        # Get the positions of the module nodes, where the called method updates the self.initNodePos.
        self.returnNodeInfoTransformation(self.numNodes)
        
        # Move the joints group and the nodule IK nodes to the start position for the first joint node.
        cmds.xform(self.moduleNodesGrp, worldSpace=True, translation=self.initNodePos[0])
        cmds.xform(self.moduleIKnodesGrp, worldSpace=True, translation=self.initNodePos[0])
        
        # Calculate the position of the mid hinge node.
        offset = self.moduleLen / 10.0
        hingeOffset = {'YZ':[offset, 0.0, 0.0], 'XZ':[0.0, offset, 0.0], 'XY':[0.0, 0.0, offset]}[self.onPlane]
        self.initNodePos[1] = map(lambda x,y: x+y, self.initNodePos[1], hingeOffset)

        # Create the module nodes (joints) by their position and name them accordingly.
        for index, nodePos in enumerate(self.initNodePos):
            if index == 0:
                jointName = cmds.joint(name=self.moduleTypespace+':root_node_transform', position=nodePos,
                                                                                radius=0.0, scaleCompensate=False)
            elif nodePos == self.initNodePos[-1]:
                jointName = cmds.joint(name=self.moduleTypespace+':end_node_transform', position=nodePos,
                                                                            radius=0.0, scaleCompensate=False)
            else:
                jointName = cmds.joint(name=self.moduleTypespace+':node_%s_transform'%(index), position=nodePos,
                                                                                    radius=0.0, scaleCompensate=False)
            cmds.setAttr(jointName+'.drawStyle', 2)
            self.nodeJoints.append(jointName)
            
        # Orient the joints.
        cmds.select(self.nodeJoints[0], replace=True)
        
        # For orientation we'll use the axis perpendicular to the creation plane as the up axis for secondary axis orient.
        secondAxisOrientation = {'XY':'z', 'YZ':'x', 'XZ':'y'}[self.onPlane] + 'up'
        cmds.joint(edit=True, orientJoint=self.nodeAxes.lower(), secondaryAxisOrient=secondAxisOrientation,
                                                                            zeroScaleOrient=True, children=True)
        
        # Orient the end joint node.
        cmds.setAttr(self.nodeJoints[-1]+'.jointOrientX', 0)
        cmds.setAttr(self.nodeJoints[-1]+'.jointOrientY', 0)
        cmds.setAttr(self.nodeJoints[-1]+'.jointOrientZ', 0)
        
        # Mirror the module node joints (for the mirrored module) if the module mirroring is enabled
        # and the current module to be created is a mirrored module on the -ve side of the creation plane,
        # and if the mirror rotation function is set to "Behaviour".
        if self.mirrorModule:
        
            mirrorPlane = {'XY':False, 'YZ':False, 'XZ':False}
            mirrorPlane[self.onPlane] = True
            mirroredJoints = cmds.mirrorJoint(self.nodeJoints[0], 
                                              mirrorXY=mirrorPlane['XY'], mirrorYZ=mirrorPlane['YZ'], mirrorXZ=mirrorPlane['XZ'], 
                                              mirrorBehavior=True)
                                              
            # While mirroring joints for the hinge module, we want to always mirror in behaviour first. 
            # This is done since we want to keep the aim axis down the module node hierarchy. The aim translation
            # channel will be connected later with an input. Mirroring joints using orientation function will provide
            # incorrect orientation of aim axis down the module nodes. 
            # The actual orientation of the joints as per the rotation function specified in the module creation
            # function is applied while creating a character from hinge module(s).
            
            # Reorient the joints to aim down the node hierarchy for the hinge module.
            if self.mirrorRotationFunc == 'Orientation':
                cmds.joint(mirroredJoints[0], edit=True, orientJoint=self.nodeAxes.lower(), 
                                                         secondaryAxisOrient=secondAxisOrientation,
                                                         zeroScaleOrient=True, children=True)
            cmds.delete(self.nodeJoints[0])
            self.nodeJoints = []
            
            for joint in mirroredJoints:
                newJoint = cmds.rename(joint, self.moduleTypespace+':'+joint)
                self.nodeJoints.append(newJoint)
        
        # Clear selection after joint orientation.
        cmds.select(clear=True)
        
        # Create the IK handle to drive the module nodes.
        ikNodes = cmds.ikHandle(startJoint=self.nodeJoints[0], endEffector=self.nodeJoints[-1],
                                                    name=self.moduleTypespace+':rootToEndNode_ikHandle', solver='ikRPsolver')
        ikEffector = cmds.rename(ikNodes[1], self.moduleTypespace+':rootToEndNode_ikEffector')
        ikHandle = ikNodes[0]
        cmds.parent(ikHandle, self.moduleIKnodesGrp, absolute=True)
        cmds.setAttr(ikHandle + '.visibility', 0)
            
        # Place the IK handle at the last module node position.
        cmds.xform(ikHandle, worldSpace=True, absolute=True, rotation=cmds.xform(self.nodeJoints[-1], query=True,
                                                                    worldSpace=True, absolute=True, rotation=True))
       
        # Create the node handle objects.
        # For hinge module, the nodes will not be translated directly. They will be driven by
        # control handles on top of them.

        # Root node handle.
        rootHandle = objects.createRawControlSurface(self.nodeJoints[0], self.modHandleColour, True)
        mfunc.lockHideChannelAttrs(rootHandle[0], 'r', 's', 'v', keyable=False)
        rootHandlePos = cmds.xform(self.nodeJoints[0], query=True, worldSpace=True, translation=True)
        cmds.xform(rootHandle[0], worldSpace=True, absolute=True, translation=rootHandlePos)
        rootHandleConstraint = cmds.pointConstraint(rootHandle[0], self.nodeJoints[0], maintainOffset=False,
                                                                    name=self.nodeJoints[0]+'_pointConstraint')
        cmds.parent(rootHandle[0], self.moduleIKnodesGrp, absolute=True)

        # Mid hinge or elbow node handle.
        elbowHandle = objects.createRawControlSurface(self.nodeJoints[1], self.modHandleColour, True)
        mfunc.lockHideChannelAttrs(elbowHandle[0], 'r', 's', 'v', keyable=False)
        elbowHandlePos = cmds.xform(self.nodeJoints[1], query=True, worldSpace=True, translation=True)
        cmds.xform(elbowHandle[0], worldSpace=True, absolute=True, translation=elbowHandlePos)
        elbowHandleConstraint = cmds.poleVectorConstraint(elbowHandle[0], ikHandle, name=ikHandle+'_poleVectorConstraint')
        cmds.parent(elbowHandle[0], self.moduleIKnodesGrp, absolute=True)

        # End node handle.
        endHandle = objects.createRawControlSurface(self.nodeJoints[-1], self.modHandleColour, True)
        mfunc.lockHideChannelAttrs(endHandle[0], 'r', 's', 'v', keyable=False)
        endHandlePos = cmds.xform(self.nodeJoints[2], query=True, worldSpace=True, translation=True)
        cmds.xform(endHandle[0], worldSpace=True, absolute=True, translation=endHandlePos)
        endHandleConstraint = cmds.pointConstraint(endHandle[0], ikHandle, maintainOffset=False, name=ikHandle+'_pointConstraint')
        cmds.parent(endHandle[0], self.moduleIKnodesGrp, absolute=True)
            
        # Prepare the module node control handle objects for scaling.
        for i, joint in enumerate(self.nodeJoints):
            
            # Get the "rig" surface for the control handle.
            handleShape = joint+'_controlShape'
            
            # Drive it using a cluster for scaling and parent it accordingly.
            handleShapeScaleCluster = cmds.cluster(handleShape, relative=True, name=handleShape+'_scaleCluster')
            cmds.parent(handleShapeScaleCluster[1], self.moduleNodeHandleShapeScaleClusterGrp, absolute=True)
            cmds.setAttr(handleShapeScaleCluster[1]+'.visibility', 0)
            
            # Collect the cluster nodes.
            clusterNodes = cmds.listConnections(handleShape, source=True, destination=True)
            
            # Remove the tweak node.
            for node in clusterNodes:
                if cmds.nodeType(node) == 'tweak':
                    cmds.delete(node)
                    break
            
            # Update the cluster node list.
            clusterNodes = cmds.listConnections(handleShape, source=True, destination=True)
            self.collectedNodes.extend(clusterNodes)
            
            # Additionally, create a world position locator for the node joint.
            worldPosLocator = cmds.createNode('locator', parent=joint, name=joint+'_worldPosLocator')
            cmds.setAttr(worldPosLocator + '.visibility', 0)
            
            
        # Create the segment curves between the control handle shapes.
        for j, joint in enumerate(self.nodeJoints):
            if joint == self.nodeJoints[-1]:
                break
            
            # Create the raw segment parts (between two consecutive nodes).
            segment = objects.createRawSegmentCurve(self.modHandleColour)
            
            # Connect the segment between two consecutive nodes with their control handle surfaces.
            startClosestPointOnSurface = cmds.createNode('closestPointOnSurface', name='%s_%s_closestPointOnSurface' \
                                                                                        % (joint, segment['startLoc']))

            cmds.connectAttr(joint+'_controlShape.worldSpace[0]', startClosestPointOnSurface+'.inputSurface')
            cmds.connectAttr(self.nodeJoints[j+1]+'_worldPosLocator.worldPosition', startClosestPointOnSurface+'.inPosition')
            cmds.connectAttr(startClosestPointOnSurface+'.position', segment['startLoc']+'.translate')

            endClosestPointOnSurface = cmds.createNode('closestPointOnSurface', name='%s_%s_closestPointOnSurface' \
                                                                        % (self.nodeJoints[j+1], segment['endLoc']))

            cmds.connectAttr(self.nodeJoints[j+1]+'_controlShape.worldSpace[0]', endClosestPointOnSurface+'.inputSurface')
            cmds.connectAttr(joint+'_worldPosLocator.worldPosition', endClosestPointOnSurface+'.inPosition')
            cmds.connectAttr(endClosestPointOnSurface+'.position', segment['endLoc']+'.translate')
            
            # Parent the segment curve parts under "moduleHandleSegmentCurveGrp".
            cmds.parent([segment['curve'], segment['startLoc'], segment['endLoc']], self.moduleHandleSegmentGrp, absolute=True)
            
            # Rename the segment curve.
            cmds.rename(segment['curve'], '%s:%s_%s' \
                                                % (self.moduleTypespace, mfunc.stripMRTNamespace(joint)[1], segment['curve']))
            
            # Rename the segment curve start/end position locators.
            # The start and end description here is the current and the next node, between
            # which the segment curve is connected.             
            cmds.rename(segment['startLoc'], '%s_%s' % (joint, segment['startLoc']))
            cmds.rename(segment['endLoc'], '%s_%s' % (self.nodeJoints[j+1], segment['endLoc']))
            
            # Attach an arclen to measure the length of the segment curve.
            arclen = cmds.arclen(joint+'_segmentCurve', constructionHistory=True)
            namedArclen = cmds.rename(arclen, joint+'_segmentCurve_curveInfo')

            cmds.select(clear=True)
            
            # Add the created nodes to the module container.
            self.collectedNodes.extend([startClosestPointOnSurface, endClosestPointOnSurface, namedArclen])
           
        # Create a segment curve between the root and the end node.
        rootEndSegment = objects.createRawSegmentCurve(3)
        
        # Connect the start and end segment position locators to the node control handle surfaces.
        startClosestPointOnSurface = cmds.createNode('closestPointOnSurface', name='%s:startHandleIKsegment_%s_closestPointOnSurface' \
                                                                                    % (self.moduleTypespace,
                                                                                       rootEndSegment['startLoc']))
                                                                                       
        cmds.connectAttr(self.nodeJoints[0]+'_controlShape.worldSpace[0]', startClosestPointOnSurface+'.inputSurface')
        cmds.connectAttr(self.nodeJoints[-1]+'_worldPosLocator.worldPosition', startClosestPointOnSurface+'.inPosition')
        cmds.connectAttr(startClosestPointOnSurface+'.position', rootEndSegment['startLoc']+'.translate')
        
        endClosestPointOnSurface = cmds.createNode('closestPointOnSurface', name='%s:endHandleIKsegment_%s_closestPointOnSurface' \
                                                                                   % (self.moduleTypespace,
                                                                                      rootEndSegment['endLoc']))
                                                                                      
        cmds.connectAttr(self.nodeJoints[-1]+'_controlShape.worldSpace[0]', endClosestPointOnSurface+'.inputSurface')
        cmds.connectAttr(self.nodeJoints[0]+'_worldPosLocator.worldPosition', endClosestPointOnSurface+'.inPosition')
        cmds.connectAttr(endClosestPointOnSurface+'.position', rootEndSegment['endLoc']+'.translate')
        
        self.collectedNodes.extend([startClosestPointOnSurface, endClosestPointOnSurface])
        
        cmds.parent([rootEndSegment['curve'], rootEndSegment['startLoc'], rootEndSegment['endLoc']],
                                                            self.moduleHandleSegmentGrp, absolute=True)
        
        # Rename the root-end segment curve.
        rootEndHandleIKsegmentCurve = cmds.rename(rootEndSegment['curve'], '%s:rootEndHandleIKsegment_%s' \
                                                                                  % (self.moduleTypespace,
                                                                                     rootEndSegment['curve']))
        # Rename the root-end segment curve start/end position locators.
        cmds.rename(rootEndSegment['startLoc'], '%s:startHandleIKsegment_%s' \
                                                    % (self.moduleTypespace, rootEndSegment['startLoc']))
                                                                         
        cmds.rename(rootEndSegment['endLoc'], '%s:endHandleIKsegment_%s' \
                                                    % (self.moduleTypespace, rootEndSegment['endLoc']))

        cmds.select(clear=True)
        
        
        
        # Create a locator attached at the mid position on the root-end segment curve.
        # This locator will be used to visually identify the mid position of the IK chain,
        # represented here by the hinge module nodes. 
        rootEndHandleIKsegmentMidLocator = cmds.spaceLocator(name='%s:rootEndHandleIKsegmentMidLocator' \
                                                                    % self.moduleTypespace)[0]

        cmds.parent(rootEndHandleIKsegmentMidLocator, self.moduleIKsegmentMidAimGrp, absolute=True)
        
        # Attach the IK segment mid position locator on the start-end segment curve.
        rootEndHandleIKsegmentMidLocator_pointOnCurveInfo = \
            cmds.createNode('pointOnCurveInfo', name='%s:rootEndHandleIKsegmentCurveMidLocator_pointOnCurveInfo' \
                                                        % self.moduleTypespace)
                                                        
        cmds.connectAttr(rootEndHandleIKsegmentCurve+'Shape.worldSpace[0]', 
                         rootEndHandleIKsegmentMidLocator_pointOnCurveInfo+'.inputCurve')
                         
        cmds.setAttr(rootEndHandleIKsegmentMidLocator_pointOnCurveInfo+'.turnOnPercentage', True)
        cmds.setAttr(rootEndHandleIKsegmentMidLocator_pointOnCurveInfo+'.parameter', 0.5)
        cmds.connectAttr(rootEndHandleIKsegmentMidLocator_pointOnCurveInfo+'.position', 
                                            rootEndHandleIKsegmentMidLocator+'.translate')
        self.collectedNodes.append(rootEndHandleIKsegmentMidLocator_pointOnCurveInfo)
        
        # Set the display attributes.
        cmds.setAttr(rootEndHandleIKsegmentMidLocator+'Shape.localScaleX', 0.1)
        cmds.setAttr(rootEndHandleIKsegmentMidLocator+'Shape.localScaleY', 0)
        cmds.setAttr(rootEndHandleIKsegmentMidLocator+'Shape.localScaleZ', 0.1)
        cmds.setAttr(rootEndHandleIKsegmentMidLocator+'Shape.overrideEnabled', 1)
        cmds.setAttr(rootEndHandleIKsegmentMidLocator+'Shape.overrideColor', 2)

        # Manually set-up a segment curve from position of hinge node to the 
        # root-end segment curve. The curve should follow with the translation of the 
        # hinge node. It's simply a representation for how far the hinge node is positioned
        # with respect to the mid position between the root and end module nodes.
        
        # The start position of the segment curve should slide on the root-end segment curve.
        # Create a locator to drive the start position.
        ikSegmentAimStartLocator = cmds.spaceLocator(name=self.moduleTypespace+':ikSegmentAimStartLocator')[0]
        cmds.setAttr(ikSegmentAimStartLocator+'.visibility', 0)
        cmds.parent(ikSegmentAimStartLocator, self.moduleIKsegmentMidAimGrp, absolute=True)
        
        # Attach the locator to the start-end node segment curve.
        cmds.geometryConstraint(rootEndHandleIKsegmentCurve, ikSegmentAimStartLocator, 
                                        name=ikSegmentAimStartLocator+'_geoConstraint')
        
        # Additionally, constrain the locator to the hinge (mid) node control handle.
        cmds.pointConstraint(self.nodeJoints[1]+'_control', ikSegmentAimStartLocator, 
                                maintainOffset=False, name=ikSegmentAimStartLocator+'_pointConstraint')
        
        # Create a CPM node to get the closest point on the hinge node's control handle "rig"
        # surface with respect to the position of the start locator created above.
        ikSegmentAimStartClosestPointOnSurface = cmds.createNode('closestPointOnSurface', 
                                name=self.moduleTypespace+':ikSegmentAimClosestPointOnSurface')
                                
        cmds.connectAttr(self.nodeJoints[1]+'_controlShape.worldSpace[0]', 
                                        ikSegmentAimStartClosestPointOnSurface+'.inputSurface')
                                        
        cmds.connectAttr(ikSegmentAimStartLocator+'Shape.worldPosition[0]', 
                                        ikSegmentAimStartClosestPointOnSurface+'.inPosition')
        
        # Create the locator to drive the end position of the segment curve from
        # root-end node segment curve and the hinge node. It's position will be driven by
        # the CPM node's result position.
        ikSegmentAimEndLocator = cmds.spaceLocator(name=self.moduleTypespace+':ikSegmentAimEndLocator')[0]
        cmds.setAttr(ikSegmentAimEndLocator+'.visibility', 0)
        cmds.parent(ikSegmentAimEndLocator, self.moduleIKsegmentMidAimGrp, absolute=True)
        
        cmds.connectAttr(ikSegmentAimStartClosestPointOnSurface+'.position', ikSegmentAimEndLocator+'.translate')
        
        self.collectedNodes.append(ikSegmentAimStartClosestPointOnSurface)
        
        # Aim the IK segment mid position locator on the start-end segment curve (created before)
        # to the end locator.
        rootEndHandleIKsegmentMidLocatorAimConstraint = \
            cmds.aimConstraint(self.nodeJoints[-1], rootEndHandleIKsegmentMidLocator, maintainOffset=False, 
                               aimVector=[0.0, 1.0, 0.0], upVector=[0.0, 0.0, 1.0], worldUpType='object', 
                               worldUpObject=ikSegmentAimEndLocator, name=rootEndHandleIKsegmentMidLocator+'_aimConstraint')[0]
        
        # Offset its default rotation by 45
        cmds.setAttr(rootEndHandleIKsegmentMidLocatorAimConstraint+'.offsetY', 45)
        
        # Finally, create the segment curve from position of hinge node to the root-end segment curve.
        # Use the start and end locators to drive its two end CVs.
        ikSegmentAimCurve = cmds.curve(p=([0,0,0],[0,0,1]), degree=1, name=self.moduleTypespace+':ikSegmentAimCurve')
        ikSegmentAimCurveShape = cmds.listRelatives(ikSegmentAimCurve, children=True, shapes=True)[0]
        ikSegmentAimCurveShape = cmds.rename(ikSegmentAimCurveShape, self.moduleTypespace+':ikSegmentAimCurveShape')
        cmds.setAttr(ikSegmentAimCurveShape+'.overrideEnabled', 1)
        cmds.setAttr(ikSegmentAimCurveShape+'.overrideColor', 2)
        cmds.connectAttr(ikSegmentAimStartLocator+'Shape.worldPosition[0]', ikSegmentAimCurveShape+'.controlPoints[0]')
        cmds.connectAttr(ikSegmentAimEndLocator+'Shape.worldPosition[0]', ikSegmentAimCurveShape+'.controlPoints[1]')

        cmds.parent(ikSegmentAimCurve, self.moduleIKsegmentMidAimGrp, absolute=True)

        # Add the module transform to the module, at the position of the root node.
        moduleTransform = objects.createModuleTransform(namespace=self.moduleTypespace)
        cmds.delete(cmds.pointConstraint(self.nodeJoints[0], moduleTransform['transform'], maintainOffset=False))
        self.moduleTransform = moduleTransform['transform']
        self.collectedNodes.append(moduleTransform['scaleFactor'])        

        cmds.parent(moduleTransform['preTransform'], self.moduleGrp, absolute=True)
        cmds.parentConstraint(self.moduleTransform, self.moduleIKnodesGrp, maintainOffset=True, 
                                                            name=self.moduleTransform+'_parentConstraint')
        cmds.scaleConstraint(self.moduleTransform, self.moduleIKnodesGrp, maintainOffset=False, 
                                                        name=self.moduleTransform+'_scaleConstraint')
        cmds.scaleConstraint(self.moduleTransform, self.moduleNodesGrp, maintainOffset=False, 
                                                    name=self.moduleTransform+'_scaleConstraint')
        cmds.scaleConstraint(self.moduleTransform, rootEndHandleIKsegmentMidLocator, maintainOffset=False, 
                                                name=self.moduleTransform+'_scaleConstraint')

        # Create the control handles for the module nodes.
        for handle in [rootHandle[0], elbowHandle[0], endHandle[0]]:
            xhandle = objects.load_xhandleShape(transform=handle, name=handle+'X', colour=self.modHandleColour)
            cmds.setAttr(xhandle['shape']+'.localScaleX', 0.089)
            cmds.setAttr(xhandle['shape']+'.localScaleY', 0.089)
            cmds.setAttr(xhandle['shape']+'.localScaleZ', 0.089)
            cmds.setAttr(xhandle['shape']+'.ds', 5)
            cmds.setAttr(handle+'Shape.visibility', 0)
        
        # Use the node handle objects to drive the axial distance for the node joints.
        for startPos, endPos, drivenJoint in [(rootHandle[0], elbowHandle[0], self.nodeJoints[1]),
                                              (elbowHandle[0], endHandle[0], self.nodeJoints[2])]:
                                              
            # Create a distance node to measure the distance between two joint handles, and connect
            # the worldSpace translate values.
            segmentDistance = cmds.createNode('distanceBetween', name=drivenJoint+'_distanceNode')
            
            # Get the world positions of the "start" and "end" control handles,
            # and connect them to the distance between nodes.
            startPosVector = startPos+'_vectorNode'
            
            if not cmds.objExists(startPosVector):
                cmds.createNode('vectorProduct', name=startPosVector)
                cmds.setAttr(startPosVector+'.operation', 4)
                cmds.connectAttr(startPos+'Shape.worldMatrix', startPosVector+'.matrix')
                self.collectedNodes.append(startPosVector)
            
            cmds.connectAttr(startPosVector+'.output', segmentDistance+'.point1')
            
            endPosVector = endPos+'_vectorNode'
            if not cmds.objExists(endPosVector):
                cmds.createNode('vectorProduct', name=endPosVector)
                cmds.setAttr(endPosVector+'.operation', 4)
                cmds.connectAttr(endPos+'Shape.worldMatrix', endPosVector+'.matrix')
                self.collectedNodes.append(endPosVector)
            
            cmds.connectAttr(endPosVector+'.output', segmentDistance+'.point2')
            
            # Normalize the segment length by the "finalScale" attribute on the module transform.
            normalizeDivide = cmds.createNode('multiplyDivide', name=drivenJoint+'_distanceNormNode')
            cmds.setAttr(normalizeDivide+'.operation', 2)
            cmds.connectAttr(segmentDistance+'.distance', normalizeDivide+'.input1X')
            cmds.connectAttr(self.moduleTransform+'.finalScale', normalizeDivide+'.input2X')
            
            # Get the aim axis, the axis down the module node chain.
            aimAxis = self.nodeAxes[0]
            
            # Get the distance factor to multiply the original length of the node joint length.
            distanceDivideFactor = cmds.createNode('multiplyDivide', name=drivenJoint+'_distanceDivideFactor')
            cmds.setAttr(distanceDivideFactor + '.operation', 2)
            originalLength = cmds.getAttr(drivenJoint+'.translate'+aimAxis)
            cmds.connectAttr(normalizeDivide+'.outputX', distanceDivideFactor+'.input1'+aimAxis)
            cmds.setAttr(distanceDivideFactor+'.input2'+aimAxis, originalLength)
            
            # Finally, drive the position of node joints using the multiplied distance.
            drivenJointAimTranslateMultiply = cmds.createNode('multiplyDivide', name=drivenJoint+'_drivenJointAimTranslateMultiply')
            cmds.connectAttr(distanceDivideFactor+'.output'+aimAxis, drivenJointAimTranslateMultiply+'.input1'+aimAxis)
            cmds.setAttr(drivenJointAimTranslateMultiply+'.input2'+aimAxis, math.fabs(originalLength))
            cmds.connectAttr(drivenJointAimTranslateMultiply+'.output'+aimAxis, drivenJoint+'.translate'+aimAxis)
            
            self.collectedNodes.extend([segmentDistance, normalizeDivide, distanceDivideFactor, drivenJointAimTranslateMultiply])
        
        mfunc.updateAllTransforms()      

        # Add the orientation representation control for hinge axes.
        # This control cannot be manipulated directly. It shows the current
        # orientation of the hinge (middle) node.
        hingeAxisRepr = objects.createRawIKhingeAxisRepresenation(self.nodeAxes[1:])
        cmds.setAttr(hingeAxisRepr+'.scale', 2.3, 2.3, 2.3, type='double3')
        cmds.makeIdentity(hingeAxisRepr, scale=True, apply=True)
        hingeAxisRepr = cmds.rename(hingeAxisRepr, self.nodeJoints[1]+'_'+hingeAxisRepr)
        cmds.parent(hingeAxisRepr, self.moduleReprGrp, absolute=True)
        cmds.parentConstraint(self.nodeJoints[1], hingeAxisRepr, maintainOffset=False, 
                                                    name=hingeAxisRepr+'_parentConstraint')
        cmds.scaleConstraint(self.moduleTransform, hingeAxisRepr, maintainOffset=False, 
                                                    name=self.moduleTransform+'_scaleConstraint')
        
        # Create the preferred rotation representation control for the hinge node.
        # It shows the direction of rotation of the IK solver on the joint chain
        # which will be generated from the hinge module.
        ikPreferredRotationRepresentaton = objects.createRawIKPreferredRotationRepresentation(self.nodeAxes[2])
        cmds.setAttr(ikPreferredRotationRepresentaton+'.scale', 0.6, 0.6, 0.6, type='double3')
        cmds.makeIdentity(ikPreferredRotationRepresentaton, scale=True, apply=True)
        ikPreferredRotationRepresentaton = cmds.rename(ikPreferredRotationRepresentaton, 
                                                        self.moduleTypespace+':'+ikPreferredRotationRepresentaton)
        cmds.parent(ikPreferredRotationRepresentaton, self.moduleReprGrp, absolute=True)
        cmds.pointConstraint(self.moduleTypespace+':rootEndHandleIKsegmentMidLocator', 
                                    ikPreferredRotationRepresentaton, maintainOffset=False, 
                                            name=ikPreferredRotationRepresentaton+'_pointConstraint')
        cmds.scaleConstraint(self.moduleTransform, ikPreferredRotationRepresentaton, maintainOffset=False, 
                                name=self.moduleTransform+'_ikPreferredRotRepr_scaleConstraint')
        
        cmds.aimConstraint(self.nodeJoints[-1], ikPreferredRotationRepresentaton, maintainOffset=False, 
                                       aimVector=[0.0, 1.0, 0.0], upVector=[0.0, 0.0, 1.0], worldUpType='object', 
                                       worldUpObject=self.nodeJoints[1], name=ikPreferredRotationRepresentaton+'_aimConstraint')
        
        # Add hierarchy representations between the module nodes.
        for index, joint in enumerate(self.nodeJoints[:-1]):

            hierarchyRepr = objects.createRawHierarchyRepresentation(self.nodeAxes[0])

            startLocator = joint + '_segmentCurve_startLocator'
            endLocator = self.nodeJoints[index+1] + '_segmentCurve_endLocator'
            cmds.pointConstraint(startLocator, endLocator, hierarchyRepr, maintainOffset=False,
                                                        name=joint+'_hierarchy_repr_pointConstraint')
            cmds.scaleConstraint(joint, hierarchyRepr, maintainOffset=False, name=joint+'_hierarchy_repr_scaleConstraint')

            aimVector = {'X':[1.0, 0.0, 0.0], 'Y':[0.0, 1.0, 0.0], 'Z':[0.0, 0.0, 1.0]}[self.nodeAxes[0]]
            upVector = {'X':[1.0, 0.0, 0.0], 'Y':[0.0, 1.0, 0.0], 'Z':[0.0, 0.0, 1.0]}[self.nodeAxes[1]]
            cmds.aimConstraint(self.nodeJoints[index+1], hierarchyRepr, maintainOffset=False, aimVector=aimVector,
                                upVector=upVector, worldUpVector=upVector, worldUpType='objectRotation', worldUpObject=joint,
                                    name='%s:%s_hierarchy_repr_aimConstraint' % (self.moduleTypespace,
                                                                             mfunc.stripMRTNamespace(self.nodeJoints[index+1])[1]))

            cmds.parent(hierarchyRepr, self.moduleHierarchyReprGrp, absolute=True)

            cmds.rename(hierarchyRepr, joint+'_'+hierarchyRepr)


        cmds.select(clear=True)
        
        # Create module parenting representation objects.
        self.createHierarchySegmentForModuleParentingRepr()
        
        # Create the proxy geometry for the module if enabled.
        if self.proxyGeoStatus:
            if self.proxyGeoElbow:
                self.createProxyGeo_elbows(self.proxyElbowType)
            if self.proxyGeoBones:
                self.createProxyGeo_bones()

        # Add the module group to the contained nodes list.
        self.collectedNodes.append(self.moduleGrp)
        
        # Add the collected nodes to the module container.
        mfunc.addNodesToContainer(self.moduleContainer, self.collectedNodes, includeHierarchyBelow=True, includeShapes=True)        
        
        # Publish the module transform attributes for the module container.
        moduleTransformName = mfunc.stripMRTNamespace(self.moduleTransform)[1]
        cmds.container(self.moduleContainer, edit=True, publishAndBind=[self.moduleTransform+'.translate', 
                                                                        moduleTransformName+'_translate'])
        cmds.container(self.moduleContainer, edit=True, publishAndBind=[self.moduleTransform+'.rotate', 
                                                                        moduleTransformName+'_rotate'])
        cmds.container(self.moduleContainer, edit=True, publishAndBind=[self.moduleTransform+'.globalScale', 
                                                                        moduleTransformName+'_globalScale'])
        cmds.container(self.moduleContainer, edit=True, publishAndBind=[self.moduleTransform+'.scaleFactor', 
                                                                                moduleTransformName+'_scaleFactor'])        
        
        # Publish the module node control handle attributes for the module container.
        for handle in (rootHandle[0], elbowHandle[0], endHandle[0]):
            handleName = mfunc.stripMRTNamespace(handle)[1]
            cmds.container(self.moduleContainer, edit=True, publishAndBind=[handle+'.translate', 
                                                                            handleName+'_translate'])
        
        # Publish the module node joint "rotate" attributes.
        for joint in self.nodeJoints:
            jointName = mfunc.stripMRTNamespace(joint)[1]
            cmds.container(self.moduleContainer, edit=True, publishAndBind=[joint+'.rotate', 
                                                                            jointName+'_rotate'])

        # Add hinge module attributes to the module transform.
        self.addCustomAttributesOnModuleTransform()
        if self.onPlane == 'XZ':
            offset = cmds.getAttr(self.moduleTypespace+':node_1_transform_control.translateY')
            cmds.setAttr(self.moduleTypespace+':node_1_transform_control.translateY', 0)
            cmds.setAttr(self.moduleTypespace+':node_1_transform_control.translateZ', offset)
        if self.onPlane == 'XY' and self.mirrorModule:
            offset = cmds.getAttr(self.moduleTypespace+':node_1_transform_control.translateZ')
            cmds.setAttr(self.moduleTypespace+':node_1_transform_control.translateZ', offset*-1)
        if self.onPlane == 'YZ' and self.mirrorModule:
            offset = cmds.getAttr(self.moduleTypespace+':node_1_transform_control.translateX')
            cmds.setAttr(self.moduleTypespace+':node_1_transform_control.translateX', offset*-1)

        # Set the module pre-scale factor. This is used for adjusting the initial size of the module.
        cmds.setAttr(self.moduleTransform+'.scaleFactor', 30)        


    def checkPlaneAxisDirectionForIKhingeForOrientationRepr(self):
        '''
        Checks whether the orientation of the plane axis for middle or hinge node for a hinge module
        is aligned with the creation plane axis for the module.
        '''
        # Creation plane axes, derived from the module creation plane string value.
        offsetAxisVectorTransforms = {'XY':[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]], 
                                      'YZ':[[0.0, 0.0, 0.0], [0.0, 0.0, 1.0]], 
                                      'XZ':[[0.0, 0.0, 0.0], [0.0, 0.0, 1.0]]}[self.onPlane]
        
        # Local axes offset to be applied for the plane axis.
        planeAxisOffset = {'X':[1.0, 0.0, 0.0], 'Y':[0.0, 1.0, 0.0], 'Z':[0.0, 0.0, 1.0]}
        
        IKhingePlaneAxisVectorTransforms = []
        
        # Create a test locator to get the plane axis vector.
        worldTransformLoc_IKhingeOrientationVector = cmds.spaceLocator()[0]
        
        # Align and place the locator under the hinge or middle node for the hinge module.
        cmds.parent(worldTransformLoc_IKhingeOrientationVector, self.nodeJoints[1], relative=True)
        
        # Record its world position.
        IKhingePlaneAxisVectorTransforms.append(cmds.getAttr(worldTransformLoc_IKhingeOrientationVector+'.worldPosition'))
        
        # Move the locator locally with respect to the plane axis value and get its world position.
        cmds.setAttr(worldTransformLoc_IKhingeOrientationVector+'.translate', *planeAxisOffset[self.nodeAxes[2]], type='double3')
        IKhingePlaneAxisVectorTransforms.append(cmds.getAttr(worldTransformLoc_IKhingeOrientationVector+'.worldPosition'))
                                                                            
        cmds.delete(worldTransformLoc_IKhingeOrientationVector)
        
        # Get the dot direction for the local "plane" vector with the module creation plane axis.
        direction_cosine = mfunc.returnDotProductDirection(offsetAxisVectorTransforms[0], offsetAxisVectorTransforms[1],
                                                IKhingePlaneAxisVectorTransforms[0], IKhingePlaneAxisVectorTransforms[1])[0]
        
        # Check if it's aligned with the module creation plane axis.
        hingePreferredOrientationReprAffectDueToIKRotation_directionCheck = {'XY':1.0, 'YZ':-1.0, 'XZ':1.0}[self.onPlane]

        if hingePreferredOrientationReprAffectDueToIKRotation_directionCheck == direction_cosine:
            return True
        else:
            return False

            
    def addCustomAttributesOnModuleTransform(self):
        '''
        Called within a module creation method to add / publish module attributes to its module transform.
        '''
        # If the module type is "JointNode".
        if self.moduleType == 'JointNode':
            
            # If the JointNode module contains multiple nodes.
            if len(self.nodeJoints) > 1:
                
                # Add the switches for node orientation representation control visibility.
                #
                # Add category attribute.
                cmds.addAttr(self.moduleTransform, attributeType='enum', longName='Node_Orientation_Repr_Toggle', enumName=' ')
                cmds.setAttr(self.moduleTransform+'.Node_Orientation_Repr_Toggle', keyable=False, channelBox=True)
                
                # Add the visibility attribute for every node except the last one (The last node derives its
                # orientation from its parent node).
                for joint in self.nodeJoints[:-1]:
                
                    longName = mfunc.stripMRTNamespace(joint)[1]+'_orient_repr_transform'
                    
                    cmds.addAttr(self.moduleTransform, attributeType='enum', longName=longName,
                                            enumName='Off:On:', defaultValue=1, keyable=True)
                                            
                    cmds.connectAttr(self.moduleTransform+'.'+longName, joint+'_orient_repr_transform.visibility')
                    
                    # Set the default value for the visibility switch.
                    if not self.showOrientation:
                        cmds.setAttr(self.moduleTransform+'.'+longName, 0)
                
                    # Publish the attribute to the module container.
                    cmds.container(self.moduleContainer, edit=True,
                                    publishAndBind=[self.moduleTransform+'.'+longName, 'module_transform_'+longName+'_toggle'])
                
                
                # Add the switches for node hierarchy representation visibility. This is used
                # to visibly represent the direction of hierarchy among nodes within a module.
                #
                # Add category attribute.
                cmds.addAttr(self.moduleTransform, attributeType='enum', longName='Node_Hierarchy_Repr_Toggle', enumName=' ')
                cmds.setAttr(self.moduleTransform+'.Node_Hierarchy_Repr_Toggle', keyable=False, channelBox=True)
                
                # Add the visibility attribute for every node except the last one.
                for joint in self.nodeJoints[:-1]:
                
                    longName = mfunc.stripMRTNamespace(joint)[1]+'_hierarchy_repr'
                    
                    cmds.addAttr(self.moduleTransform, attributeType='enum', longName=longName, enumName='Off:On:',
                                                                                defaultValue=1, keyable=True)
                    cmds.connectAttr(self.moduleTransform+'.'+longName, joint+'_hierarchy_repr.visibility')

                    cmds.connectAttr(self.moduleTransform+'.'+longName, joint+'_segmentCurve.visibility')
                    
                    # Set the default value for the visibility switch.
                    if not self.showHierarchy:
                        cmds.setAttr(self.moduleTransform+'.'+longName, 0)
                    
                    # Publish the attribute to the module container.
                    cmds.container(self.moduleContainer, edit=True,
                                    publishAndBind=[self.moduleTransform+'.'+longName, 'module_transform_'+longName+'_toggle'])
        
            # If the JointNode module contains single node.
            if len(self.nodeJoints) == 1:
                
                # Add visibility switch attribute for the orientation control.
                cmds.addAttr(self.moduleTransform, attributeType='enum', longName='Node_Orientation_Repr_Toggle', enumName=' ')
                cmds.setAttr(self.moduleTransform+'.Node_Orientation_Repr_Toggle', keyable=False, channelBox=True)
                
                longName = mfunc.stripMRTNamespace(self.nodeJoints[0])[1]+'_single_orient_repr_transform'
                
                cmds.addAttr(self.moduleTransform, attributeType='enum', longName=longName, enumName='Off:On:', defaultValue=1,
                                                                                                        keyable=True)
                cmds.connectAttr(self.moduleTransform+'.'+longName, '%s:single_orient_repr_transform.visibility' \
                                                                % mfunc.stripMRTNamespace(self.nodeJoints[0])[0])
                # Set the default value for the visibility switch.
                if not self.showOrientation:
                    cmds.setAttr(self.moduleTransform+'.'+longName, 0)
                
                # Publish the attribute to the module container.
                cmds.container(self.moduleContainer, edit=True, publishAndBind=[self.moduleTransform+'.'+longName,
                                                                        'module_transform_'+longName+'_toggle'])


            # Add the attributes for adjusting the module node sizes. These sizes directly affect the
            # the radius of joints that'll be generated from them.
            #
            # Add category attribute.
            cmds.addAttr(self.moduleTransform, attributeType='enum', longName='Node_Handle_Size', enumName=' ')
            cmds.setAttr(self.moduleTransform+'.Node_Handle_Size', keyable=False, channelBox=True)
            
            # Add node handle size attribute for all nodes.
            for joint in self.nodeJoints:
            
                longName = mfunc.stripMRTNamespace(joint)[1]+'_handle_size'
                
                cmds.addAttr(self.moduleTransform, attributeType='float', longName=longName, hasMinValue=True,
                                                                            minValue=0, defaultValue=1, keyable=True)
                
                cmds.connectAttr(self.moduleTransform+'.'+longName, joint+'_controlShape_scaleClusterHandle.scaleX')
                cmds.connectAttr(self.moduleTransform+'.'+longName, joint+'_controlShape_scaleClusterHandle.scaleY')
                cmds.connectAttr(self.moduleTransform+'.'+longName, joint+'_controlShape_scaleClusterHandle.scaleZ')
                
                scaleMult = cmds.createNode('multiplyDivide', name=joint+'_shapeScale_mult', skipSelect=True)
                currentShapeScale = cmds.getAttr(joint+'Shape.localScale')[0]
                cmds.setAttr(scaleMult+'.input1', *currentShapeScale, type='double3')
                cmds.connectAttr(self.moduleTransform+'.'+longName, scaleMult+'.input2X')
                cmds.connectAttr(self.moduleTransform+'.'+longName, scaleMult+'.input2Y')
                cmds.connectAttr(self.moduleTransform+'.'+longName, scaleMult+'.input2Z')
                cmds.connectAttr(scaleMult+'.output', joint+'Shape.localScale')
                
                mfunc.addNodesToContainer(self.moduleContainer, scaleMult)
                
                # Publish the attribute to the module container.
                cmds.container(self.moduleContainer, edit=True, publishAndBind=[self.moduleTransform+'.'+longName,
                                                                                    'module_transform_'+longName])
            
            # Add the attributes for adjusting the rotation order under nodes. These values directly affect the
            # the rotation order of joints that'll be generated from them.
            #
            # Add category attribute.
            cmds.addAttr(self.moduleTransform, attributeType='enum', longName='Node_Rotation_Order', enumName=' ')
            cmds.setAttr(self.moduleTransform+'.Node_Rotation_Order', keyable=False, channelBox=True)
            
            # Add rotation order attribute for all nodes.
            for joint in self.nodeJoints:
            
                longName = mfunc.stripMRTNamespace(joint)[1]+'_rotate_order'
                
                cmds.addAttr(self.moduleTransform, attributeType='enum', longName=longName,
                                                    enumName='xyz:yzx:zxy:xzy:yxz:zyx:', defaultValue=0, keyable=True)
                                                    
                cmds.connectAttr(self.moduleTransform+'.'+longName, joint+'.rotateOrder')
                
                # Publish the attribute to the module container.
                cmds.container(self.moduleContainer, edit=True, publishAndBind=[self.moduleTransform+'.'+longName,
                                                                               'module_transform_'+longName+'_switch'])

        # If the module type is "SplineNode".
        if self.moduleType == 'SplineNode':
            
            # Add node representation attributes.
            cmds.addAttr(self.moduleTransform, attributeType='enum', longName='Node_Repr', enumName=' ')
            cmds.setAttr(self.moduleTransform+'.Node_Repr', keyable=False, channelBox=True)
            
            # Attribute for rotating the axial orientation of nodes along the module spline curve.
            cmds.addAttr(self.moduleTransform, attributeType='float', longName='Axis_Rotate', defaultValue=0, keyable=True)
            
            # Attribute for toggling the visibility of node orientation representation objects (coloured-axes).h
            cmds.addAttr(self.moduleTransform, attributeType='enum', longName='Node_Orientation_Info',
                                                                enumName='Off:On:', defaultValue=1, keyable=True)
            
            # Attribute to toggle the type of orientation for spline nodes, with modes for "World" and "Object".
            cmds.addAttr(self.moduleTransform, attributeType='enum', longName='Node_Orientation_Type',
                                                                    enumName='World:Object:', defaultValue=1, keyable=True)
            
            # Attribute to adjust the orientation representation control sizes for nodes.
            cmds.addAttr(self.moduleTransform, attributeType='float', longName='Node_Local_Orientation_Repr_Size',
                                                            hasMinValue=True, minValue=0.01, defaultValue=1, keyable=True)

            # Publish the new spline module attributes.
            cmds.container(self.moduleContainer, edit=True,
                            publishAndBind=[self.moduleTransform+'.Axis_Rotate', 'module_Axis_Rotate'])                    
            cmds.container(self.moduleContainer, edit=True,
                            publishAndBind=[self.moduleTransform+'.Node_Orientation_Info', 'root_transform_Node_Orientation'])
            cmds.container(self.moduleContainer, edit=True,
                            publishAndBind=[self.moduleTransform+'.Node_Orientation_Type', 'root_transform_Node_Orientation_Type'])
            cmds.container(self.moduleContainer, edit=True,
                            publishAndBind=[self.moduleTransform+'.Node_Local_Orientation_Repr_Size', 'root_transform_Node_Orientation_Repr_Size'])
        
        # If the module type is "HingeNode".
        if self.moduleType == 'HingeNode':
            
            # Attribute for toggling the visibility for hinge orientation representation.
            cmds.addAttr(self.moduleTransform, attributeType='enum', longName='Hinge_Orientation_Repr_Toggle',
                                                            enumName='Off:On:', defaultValue=1, keyable=True)
                                                            
            cmds.connectAttr(self.moduleTransform+'.Hinge_Orientation_Repr_Toggle',
                             self.nodeJoints[1]+'_IKhingeAxisRepresenation.visibility')
                             
            cmds.connectAttr(self.moduleTransform+'.Hinge_Orientation_Repr_Toggle',
                             self.moduleTypespace+':IKPreferredRotationRepr.visibility')
            
            # Publish to module container.
            cmds.container(self.moduleContainer, edit=True, publishAndBind=[self.moduleTransform+'.Hinge_Orientation_Repr_Toggle',
                                                                            mfunc.stripMRTNamespace(self.nodeJoints[1])[1]+'_Hinge_Orientation_Repr_Toggle'])
            # Set its default value.
            if not self.showOrientation:
                cmds.setAttr(self.moduleTransform+'.Hinge_Orientation_Repr_Toggle', 0)
            
            # Attribute for toggling the visibility for node hierarchy representation.
            cmds.addAttr(self.moduleTransform, attributeType='enum', longName='Module_Hierarchy_Repr_Toggle',
                                                                    enumName='Off:On:', defaultValue=1, keyable=True)
            for joint in self.nodeJoints[:-1]:
                cmds.connectAttr(self.moduleTransform+'.Module_Hierarchy_Repr_Toggle', joint+'_hierarchy_repr.visibility')
                cmds.connectAttr(self.moduleTransform+'.Module_Hierarchy_Repr_Toggle', joint+'_segmentCurve.visibility')

            # Publish to module container.
            cmds.container(self.moduleContainer, edit=True, publishAndBind=[self.moduleTransform+'.Module_Hierarchy_Repr_Toggle',
                                                                            'Module_Hierarchy_Repr_Toggle'])
            # Set its default value.
            if not self.showHierarchy:
                cmds.setAttr(self.moduleTransform+'.Module_Hierarchy_Repr_Toggle', 0)

            # Add category attribute for node handle sizes.
            cmds.addAttr(self.moduleTransform, attributeType='enum', longName='Node_Handle_Size', enumName=' ')
            cmds.setAttr(self.moduleTransform+'.Node_Handle_Size', keyable=False, channelBox=True)

            # Create node handle size attributes.
            for joint in self.nodeJoints:
                longName = mfunc.stripMRTNamespace(joint)[1]+'_handle_size'
                cmds.addAttr(self.moduleTransform, attributeType='float', longName=longName, hasMinValue=True,
                                                                            minValue=0, defaultValue=1, keyable=True)
                                                                            
                cmds.connectAttr(self.moduleTransform+'.'+longName, joint+'_controlShape_scaleClusterHandle.scaleX')
                cmds.connectAttr(self.moduleTransform+'.'+longName, joint+'_controlShape_scaleClusterHandle.scaleY')
                cmds.connectAttr(self.moduleTransform+'.'+longName, joint+'_controlShape_scaleClusterHandle.scaleZ')
                
                handleShape = joint + '_controlXShape'
                scaleMult = cmds.createNode('multiplyDivide', name=joint+'_controlScale_mult', skipSelect=True)
                currentShapeScale = cmds.getAttr(handleShape+'.localScale')[0]
                cmds.setAttr(scaleMult+'.input1', *currentShapeScale, type='double3')
                cmds.connectAttr(self.moduleTransform+'.'+longName, scaleMult+'.input2X')
                cmds.connectAttr(self.moduleTransform+'.'+longName, scaleMult+'.input2Y')
                cmds.connectAttr(self.moduleTransform+'.'+longName, scaleMult+'.input2Z')
                cmds.connectAttr(scaleMult+'.output', handleShape+'.localScale')
                
                mfunc.addNodesToContainer(self.moduleContainer, scaleMult)
                
                # Publish to module container.
                cmds.container(self.moduleContainer, edit=True, publishAndBind=[self.moduleTransform+'.'+longName,
                                                                                        'module_transform_'+longName])

            # Add category attribute for adjusting the rotation order under nodes.
            cmds.addAttr(self.moduleTransform, attributeType='enum', longName='Node_Rotation_Order', enumName=' ')
            cmds.setAttr(self.moduleTransform+'.Node_Rotation_Order', keyable=False, channelBox=True)

            # Add rotation order attribute for all nodes.
            for joint in self.nodeJoints:
            
                longName = mfunc.stripMRTNamespace(joint)[1]+'_rotate_order'
                
                cmds.addAttr(self.moduleTransform, attributeType='enum', longName=longName,
                                                enumName='xyz:yzx:zxy:xzy:yxz:zyx:', defaultValue=0, keyable=True)
                                                
                cmds.connectAttr(self.moduleTransform+'.'+longName, joint+'.rotateOrder')
                
                # Publish the attribute to the module container.
                cmds.container(self.moduleContainer, edit=True, publishAndBind=[self.moduleTransform+'.'+longName,
                                                                            'module_transform_'+longName+'_switch'])


        # If the module has proxy geometry, add an attribute for modying its viewport draw style.
        if self.proxyGeoStatus:
        
            cmds.addAttr(self.moduleTransform, attributeType='enum', longName='Proxy_Geometry', enumName=' ')
            cmds.setAttr(self.moduleTransform+'.Proxy_Geometry', keyable=False, channelBox=True)
            
            # Add the attribute to switch the module proxy geometry draw with
            # options for "Opaque" and "Transparent" styles.
            cmds.addAttr(self.moduleTransform, attributeType='enum', longName='proxy_geometry_draw',
                                                        enumName='Opaque:Transparent:', defaultValue=1, keyable=True)
            
            # Publish the attribute to the module container.
            cmds.container(self.moduleContainer, edit=True, publishAndBind=[self.moduleTransform+'.proxy_geometry_draw',
                                                                    'module_transform_proxy_geometry_draw_toggle'])
                

    def createProxyGeo_elbows(self, geoType='sphere'):
        '''
        Creates "elbow" type proxy geometry for all the nodes in a module.
        '''
        # Get the path to the proxy geo primitive, based on the elbow type.
        
        if geoType == 'sphere':
            filePathSuffix = 'MRT/elbow_proxySphereGeo.ma'
        
        if geoType == 'cube':
            filePathSuffix = 'MRT/elbow_proxyCubeGeo.ma'
        
        filePath = cmds.internalVar(userScriptDir=True) + filePathSuffix
        
        # Set to root namespace.
        cmds.namespace(setNamespace=':')
        
        # Create and attach the elbow proxy geo to every node.
        for index, joint in enumerate(self.nodeJoints):
        
            # Import the elbow proxy primitive.
            cmds.file(filePath, i=True, prompt=False, ignoreVersion=True)
            
            # Remove the extra nodes from the import.
            extra_nodes = [u'elbow_proxyGeo_uiConfigurationScriptNode', u'elbow_proxyGeo_sceneConfigurationScriptNode']
            for node in extra_nodes:
                if cmds.objExists(node):
                    cmds.delete(node)
                    
            # Get the names of the proxy geo transforms.
            proxyElbowGeoPreTransform = 'proxy_elbow_preTransform'
            proxyElbowGeoScaleTransform = 'proxy_elbow_scaleTransform'
            proxyElbowTransform = 'proxy_elbow_geo'
            
            # If the current module is a mirrored module (on the -ve side of the creation plane)
            # and part of a mirrored module pair, and if mirror instancing is enabled for module proxy geometry.
            if self.mirrorModule and self.proxyGeoMirrorInstance == 'On':
                
                # Get the original namespace (the module on the +ve side).
                originalNamespace = cmds.getAttr(self.moduleGrp+'.mirrorModuleNamespace')
                
                # Delete the mirrored proxy geometry.
                cmds.delete(proxyElbowTransform)
                
                # Duplicate the "original" elbow proxy geometry as an instance. The original elbow proxy geometry
                # is on the node for its mirror module on the +ve side of the creation plane. 
                originalProxyElbowTransform = '%s:%s_%s' % (originalNamespace, 
                                                            re.findall('(root_node|node_\d+|end_node)', joint)[0], 
                                                            proxyElbowTransform)

                transformInstance = cmds.duplicate(originalProxyElbowTransform, instanceLeaf=True, name='proxy_elbow_geo')[0]
                cmds.parent(transformInstance, proxyElbowGeoScaleTransform, relative=True)
                
                # Set the scale factor for the proxy's scale transform to "mirror" the vertex positions. 
                if self.moduleType != 'HingeNode':
                    scaleFactorAxes = {'XY':[1, 1, -1], 'YZ':[-1, 1, 1], 'XZ':[1, -1, 1]}[self.onPlane]
                else:
                    scaleFactorAxes = {'XY':[1, 1, -1], 'YZ':[-1, 1, 1], 'XZ':[1, -1, 1]}[self.onPlane]
                
                cmds.setAttr(proxyElbowGeoScaleTransform+'.scale', *scaleFactorAxes)
                
            # Set the default colour for the vertices for the elbow proxy geo.
            cmds.select(proxyElbowTransform+'.vtx[*]', replace=True)
            cmds.polyColorPerVertex(alpha=0.3, rgb=[0.663, 0.561, 0.319], notUndoable=True, colorDisplayOption=True)
            
            # Attach the elbow proxy to the node joint.
            cmds.pointConstraint(joint, proxyElbowGeoPreTransform, maintainOffset=False, name=joint+'_pointConstraint')
            cmds.scaleConstraint(joint, proxyElbowGeoPreTransform, maintainOffset=False, name=joint+'_scaleConstraint')
            
            # Now, drive the orientation of the elbow proxy geom based on the module type.
            
            if self.moduleType == 'JointNode' or self.moduleType == 'HingeNode':
                
                # If the JointNode module has multiple nodes, aim the proxy geo to the next node joint,
                # and use the current node joint for up rotation. HingeNode module always has three nodes.
                if self.numNodes > 1:
                    
                    aimConstraints = []
                    
                    aimVector = {'X':[1.0, 0.0, 0.0], 'Y':[0.0, 1.0, 0.0], 'Z':[0.0, 0.0, 1.0]}[self.nodeAxes[0]]
                    upVector = {'X':[1.0, 0.0, 0.0], 'Y':[0.0, 1.0, 0.0], 'Z':[0.0, 0.0, 1.0]}[self.nodeAxes[1]]
                    
                    # If first node, aim it to the next node joint.
                    if index == 0:
                        constraint = cmds.aimConstraint(self.nodeJoints[index+1], proxyElbowGeoPreTransform, 
                                           maintainOffset=True, aimVector=aimVector, upVector=upVector, 
                                           worldUpVector=upVector, worldUpType='objectRotation', worldUpObject=joint,
                                           name=joint+'_'+proxyElbowGeoPreTransform+'_aimConstraint')[0]
                    
                    # Else, aim to the previous node joint.
                    else:
                        constraint = cmds.aimConstraint(self.nodeJoints[index-1], proxyElbowGeoPreTransform, 
                                            maintainOffset=True, aimVector=aimVector, upVector=upVector, 
                                            worldUpVector=upVector, worldUpType='objectRotation', worldUpObject=joint,
                                           name=joint+'_'+proxyElbowGeoPreTransform+'_aimConstraint')[0]
                    
                    aimConstraints.append(constraint)
                
                # If the module consists of a single node (always a JointNode module), orient constrain it to the 
                # orientation representation control.
                if self.numNodes == 1:
                    cmds.orientConstraint(self.moduleTypespace+':single_orient_repr_transform', proxyElbowGeoPreTransform,
                                                    maintainOffset=True, name=proxyElbowGeoPreTransform+'_orientConstraint')
                
                # If the module type is HingeNode.
                if self.moduleType == 'HingeNode':
                
                    # Find and change the aim constraint offset values on hinge nodes 
                    # in order to properly orient the elbow proxy geo.
                    l_val = [0.0, 90.0, 180.0, 270.0, 360.0]
                    for constraint in aimConstraints:
                        for attr in ['X', 'Y', 'Z']:
                            val = cmds.getAttr(constraint+'.offset'+attr)
                            if not round(abs(val),0) in l_val:
                                l_cmp = {}
                                for item in l_val:
                                    l_cmp[abs(item - abs(val))] = item
                                off_value = l_cmp[min(l_cmp)]
                                off_value = math.copysign(off_value, val)
                                cmds.setAttr(constraint+'.offset'+attr, off_value)

            # If the module type is SplineNode, simply orient constrain the proxy elbow geo to the node joint.   
            if self.moduleType == 'SplineNode':
                cmds.orientConstraint(joint, proxyElbowGeoPreTransform, maintainOffset=True,
                                        name=joint+'_'+proxyElbowGeoPreTransform+'_orientConstraint')
            
            # Organise the proxy geo hierarchy for the node.
            cmds.parent(proxyElbowGeoPreTransform, self.proxyGeoGrp, absolute=True)
            cmds.rename(proxyElbowGeoPreTransform, joint.rpartition('transform')[0] + proxyElbowGeoPreTransform)
            cmds.rename(proxyElbowGeoScaleTransform, joint.rpartition('transform')[0] + proxyElbowGeoScaleTransform)
            
            # Rename the proxy elbow geo for the node.
            cmds.rename(proxyElbowTransform, joint.rpartition('transform')[0] + proxyElbowTransform)

        cmds.select(clear=True)


    def createProxyGeo_bones(self):
        '''
        Creates "bone" type proxy geometry for all the nodes in a module.
        '''
        # Get the path to the bone proxy geo primitive.
        filePath = cmds.internalVar(userScriptDir=True) + 'MRT/bone_proxyGeo.ma'
        
        # Set current namespace to root.
        cmds.namespace(setNamespace=':')
        
        # Create and attach the elbow proxy geo to module nodes (except the last one).
        # Bone proxy can be used on modules with two or more nodes.
        for index, joint in enumerate(self.nodeJoints[:-1]):
            
            # Import the proxy bone geo primitive.
            cmds.file(filePath, i=True, prompt=False, ignoreVersion=True)
            
            # Remove the extra nodes from the import.
            extra_nodes = [u'bone_proxyGeo_uiConfigurationScriptNode', u'bone_proxyGeo_sceneConfigurationScriptNode']
            for node in extra_nodes:
                if cmds.objExists(node):
                    cmds.delete(node)
            
            # Get the names of the proxy geo transforms.
            proxyBoneGeoPreTransform = 'proxy_bone_preTransform'
            proxyBoneGeoScaleTransform = 'proxy_bone_scaleTransform'
            proxyBoneTransform = 'proxy_bone_geo'
            
            # Set the rotate and scale pivot for the proxy geo transforms, based on the aim axis for the module node.
            # For eg., if the aim axis for the node is X, set the rotate/scale value along X to 0.
            if self.nodeAxes[0] == 'X':
                cmds.move(0,[proxyBoneGeoPreTransform+'.scalePivot', proxyBoneGeoPreTransform+'.rotatePivot'], moveX=True)
                cmds.move(0,[proxyBoneGeoScaleTransform+'.scalePivot', proxyBoneGeoScaleTransform+'.rotatePivot'], moveX=True)
                cmds.move(0,[proxyBoneTransform+'.scalePivot', proxyBoneTransform+'.rotatePivot'], moveX=True)
            if self.nodeAxes[0] == 'Y':
                cmds.move(0,[proxyBoneGeoPreTransform+'.scalePivot', proxyBoneGeoPreTransform+'.rotatePivot'], moveY=True)
                cmds.move(0,[proxyBoneGeoScaleTransform+'.scalePivot', proxyBoneGeoScaleTransform+'.rotatePivot'], moveY=True)
                cmds.move(0,[proxyBoneTransform+'.scalePivot', proxyBoneTransform+'.rotatePivot'], moveY=True)
            if self.nodeAxes[0] == 'Z':
                cmds.move(0,[proxyBoneGeoPreTransform+'.scalePivot', proxyBoneGeoPreTransform+'.rotatePivot'], moveZ=True)
                cmds.move(0,[proxyBoneGeoScaleTransform+'.scalePivot', proxyBoneGeoScaleTransform+'.rotatePivot'], moveZ=True)
                cmds.move(0,[proxyBoneTransform+'.scalePivot', proxyBoneTransform+'.rotatePivot'], moveZ=True)
            
            # If the current module is a mirrored module (on the -ve side of the creation plane)
            # and part of a mirrored module pair, and if mirror instancing is enabled for module proxy geometry.
            if self.mirrorModule and self.proxyGeoMirrorInstance == 'On':
                
                # Get the original namespace (the module on the +ve side).
                originalNamespace = cmds.getAttr(self.moduleGrp+'.mirrorModuleNamespace')
                
                # Delete the mirrored proxy geometry.
                cmds.delete(proxyBoneTransform)
                
                # Duplicate the "original" bone proxy geometry as an instance. The original elbow proxy geometry
                # is on the node for its mirror module on the +ve side of the creation plane.
                originalProxyBoneTransform = '%s:%s_%s' % (originalNamespace, 
                                                           re.findall('(root_node|node_\d+|end_node)', joint)[0], 
                                                           proxyBoneTransform)                
                
                transformInstance = cmds.duplicate(originalProxyBoneTransform, instanceLeaf=True, name='proxy_bone_geo')[0]
                cmds.parent(transformInstance, proxyBoneGeoScaleTransform, relative=True)
                
                # Now, drive the orientation of the bone proxy geom based on the module type.
                if self.moduleType == 'HingeNode' and self.mirrorRotationFunc == 'Orientation':
                    scaleFactorAxes = {'X':[-1, 1, 1], 'Y':[1, -1, 1], 'Z':[1, 1, -1]}[self.nodeAxes[2]]
                else:
                    scaleFactorAxes = {'X':[-1, 1, 1], 'Y':[1, -1, 1], 'Z':[1, 1, -1]}[self.nodeAxes[1]]
                
                cmds.setAttr(proxyBoneGeoScaleTransform+'.scale', *scaleFactorAxes)
            
            # Set the default colour for the vertices for the bone proxy geo.
            cmds.select(proxyBoneTransform+'.vtx[*]', replace=True)
            cmds.polyColorPerVertex(alpha=0.3, rgb=[0.663, 0.561, 0.319], notUndoable=True, colorDisplayOption=True)
            
            # Shrink the bone proxy geo along the node up and plane axes (skip the aim axis).
            if not self.mirrorModule:
                for axis in self.nodeAxes[1:]:
                    cmds.setAttr(proxyBoneGeoPreTransform+'.scale'+axis, 0.17)
                cmds.makeIdentity(proxyBoneGeoPreTransform, scale=True, apply=True)
            
            # Shrink the bone proxy geo for the mirrored node on the -ve side of the creation plane.
            if self.mirrorModule and self.proxyGeoMirrorInstance == 'Off':
                for axis in self.nodeAxes[1:]:
                    cmds.setAttr(proxyBoneGeoPreTransform+'.scale'+axis, 0.17)
                cmds.makeIdentity(proxyBoneGeoPreTransform, scale=True, apply=True)
            
            # Place the proxy geo under the module proxy geom group.
            cmds.parent(proxyBoneGeoPreTransform, self.proxyGeoGrp, absolute=True)
            
            # Orient the bone proxy geo with the node joint.
            cmds.delete(cmds.orientConstraint(joint, proxyBoneGeoPreTransform, maintainOffset=False))
            
            # Connect the module transform scaling to the proxy bone geom transform.
            for axis in self.nodeAxes[1:]:
                cmds.connectAttr(self.moduleTransform+'.finalScale', proxyBoneGeoPreTransform+'.scale'+axis)
            
            # Drive the aim scaling for the proxy geo by the node segment length (length between two module nodes).
            curveInfo = joint + '_segmentCurve_curveInfo'
            cmds.connectAttr(curveInfo+'.arcLength', proxyBoneGeoPreTransform+'.scale'+self.nodeAxes[0])
            
            # Attach the proxy geo with the start locator for the curve segment for the current node.
            # This start locator is on the "rig" nurbs shape for the node handle.
            cmds.pointConstraint(joint+'_segmentCurve_startLocator', proxyBoneGeoPreTransform, maintainOffset=False,
                                        name=self.moduleTypespace+':'+proxyBoneGeoPreTransform+'_basePointConstraint')
                                        
            aimVector = {'X':[1.0, 0.0, 0.0], 'Y':[0.0, 1.0, 0.0], 'Z':[0.0, 0.0, 1.0]}[self.nodeAxes[0]]
            upVector = {'X':[1.0, 0.0, 0.0], 'Y':[0.0, 1.0, 0.0], 'Z':[0.0, 0.0, 1.0]}[self.nodeAxes[1]]

            cmds.aimConstraint(self.nodeJoints[index+1], proxyBoneGeoPreTransform, maintainOffset=False, aimVector=aimVector,
                                upVector=upVector, worldUpVector=upVector, worldUpType='objectRotation', worldUpObject=joint,
                                                  name=self.nodeJoints[index+1]+'_'+proxyBoneGeoPreTransform+'_aimConstraint')
            
            # Rename the bone proxy geo transforms for node node joint.
            cmds.rename(proxyBoneGeoPreTransform, joint.rpartition('transform')[0] + proxyBoneGeoPreTransform)
            cmds.rename(proxyBoneGeoScaleTransform, joint.rpartition('transform')[0] + proxyBoneGeoScaleTransform)
            cmds.rename(proxyBoneTransform, joint.rpartition('transform')[0] + proxyBoneTransform)

        cmds.select(clear=True)


    def connectCustomOrientationReprToModuleProxies(self):
        '''
        Connects the orientation representation control for module nodes with the module proxy
        geometry on the nodes. This is performed so that the proxy geometry maintains its orientation
        with the orientation representation control as it is rotated manually.
        '''
        # If JointNode.
        if self.moduleType == 'JointNode':
        
            # Get the aim axis for the nodes.
            rotAxis = cmds.getAttr(self.moduleGrp+'.nodeOrient')[0]
            
            # For every node joint, get the orientation representation control.
            for joint in self.nodeJoints[:-1]:
                ori_repr_control = joint+'_orient_repr_transform'
                
                # Connect its rotation to the bone proxy geo for node, if it exists.
                boneProxy_s_transform = joint+'_proxy_bone_geo_scaleTransform'
                if cmds.objExists(boneProxy_s_transform):
                    cmds.connectAttr(ori_repr_control+'.rotate'+rotAxis, boneProxy_s_transform+'.rotate'+rotAxis)
    
        # If SplineNode.
        if self.moduleType == 'SplineNode':
        
            # Get the start module transform (SplineNode has two module transforms).
            startHandle = self.nodeJoints[0].rpartition(':')[0] + ':splineStartHandleTransform'
            
            # For every node joint, connect the "Axis Rotate" attribute to the elbow proxy geo for nodes,
            # if it exists. The "Axis Rotate" rotates the nodes axially on the SplineNode curve.
            for joint in self.nodeJoints:
                elbowProxy_s_transform = joint+'_proxy_elbow_geo_scaleTransform'
                if cmds.objExists(elbowProxy_s_transform):
                    cmds.connectAttr(startHandle+'.Axis_Rotate', elbowProxy_s_transform+'.rotateY')
