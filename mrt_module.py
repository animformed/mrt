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
#    You may notice that I use descriptive variable names. It just makes more sense to me
#    and helps avoid over-commenting.
#
# *************************************************************************************************************

import maya.cmds as cmds
import mrt_functions as mfunc
import mrt_objects as objects
import maya.mel as mel
import math, os
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
        self.moduleName = moduleInfo['node_type']
        
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
        self.moduleNamespace = moduleInfo['module_Namespace']
        
        # Generated mirror module namespace
        self.mirror_moduleNamespace = moduleInfo['mirror_module_Namespace']
        
        # Module container name.
        self.moduleContainer = self.moduleNamespace + ':module_container'
        
        # Attribute to store values for operations:
        
        # To calculate and store the initial "creation" positions of module nodes.
        self.initNodePos = []
        
        # To store node joints.
        self.nodeJoints = []


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
        # List to collect non DAG nodes as they're generated, so that they can be added to the module container.
        containedNodes = []
        
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
            name=self.moduleNamespace+':'+mfunc.stripMRTNamespace(joint)[1]+'_orient_repr_transformGroup_pointConstraint')
            
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
            aimVector=aimVector, upVector=upVector, worldUpVector=upVector, worldUpType='objectRotation', worldUpObject=joint,
            name=self.moduleNamespace+':'+mfunc.stripMRTNamespace(self.nodeJoints[index+1])[1]+'_orient_repr_transformGroup_aimConstraint')
            
            cmds.aimConstraint(self.nodeJoints[index+1], hierarchyRepr, maintainOffset=False, aimVector=aimVector,
            upVector=upVector, worldUpVector=upVector, worldUpType='objectRotation', worldUpObject=joint,
            name=self.moduleNamespace+':'+mfunc.stripMRTNamespace(self.nodeJoints[index+1])[1]+'_hierarchy_repr_aimConstraint')
            
            # Parent the orientation representation pre-transform and the hierarchy representation to their appropriate group.
            cmds.parent(hierarchyRepr, self.moduleOrientationHierarchyReprGrp, absolute=True)
            cmds.parent(orientationReprNodes[1], self.moduleOrientationHierarchyReprGrp, absolute=True)
            
            # Point constrain the orientation representation to the start locator, on the surface of the shape
            # node of the joint in iteration.
            cmds.pointConstraint(joint+'_segmentCurve_startLocator', orientationReprNodes[0], maintainOffset=True,
                                            name=self.moduleNamespace+':'+orientationReprNodes[0]+'_basePointConstraint')
                                            
            # Depending on the node aim axis, connect the scale attributes for the orientation representation.
            # The scaling along the aim axis will be the size of the orientation representation, proportional to the arc
            # length of the segment curve between two nodes.
            
            if self.nodeAxes[0] == 'X':
                arclen = cmds.arclen(joint+'_segmentCurve', constructionHistory=True)
                cmds.connectAttr(arclen+'.arcLength', orientationReprNodes[0]+'.scaleX')
                cmds.connectAttr(self.moduleTransform+'.globalScale', orientationReprNodes[0]+'.scaleY')
                cmds.connectAttr(self.moduleTransform+'.globalScale', orientationReprNodes[0]+'.scaleZ')
                cmds.rename(arclen, joint+'_segmentCurve_curveInfo')
                containedNodes.append(joint+'_segmentCurve_curveInfo')
            
            if self.nodeAxes[0] == 'Y':
                arclen = cmds.arclen(joint+'_segmentCurve', constructionHistory=True)
                cmds.connectAttr(arclen+'.arcLength', orientationReprNodes[0]+'.scaleY')
                cmds.connectAttr(self.moduleTransform+'.globalScale', orientationReprNodes[0]+'.scaleX')
                cmds.connectAttr(self.moduleTransform+'.globalScale', orientationReprNodes[0]+'.scaleZ')
                cmds.rename(arclen, joint+'_segmentCurve_curveInfo')
                containedNodes.append(joint+'_segmentCurve_curveInfo')
            
            if self.nodeAxes[0] == 'Z':
                arclen = cmds.arclen(joint+'_segmentCurve', constructionHistory=True)
                cmds.connectAttr(arclen+'.arcLength', orientationReprNodes[0]+'.scaleZ')
                cmds.connectAttr(self.moduleTransform+'.globalScale', orientationReprNodes[0]+'.scaleX')
                cmds.connectAttr(self.moduleTransform+'.globalScale', orientationReprNodes[0]+'.scaleY')
                cmds.rename(arclen, joint+'_segmentCurve_curveInfo')
                containedNodes.append(joint+'_segmentCurve_curveInfo')

            # Rename the hierarchy representation, orientation representation and its pre-transform.
            cmds.rename(hierarchyRepr, joint+'_'+hierarchyRepr)
            cmds.rename(orientationReprNodes[0],
                        self.moduleNamespace+':'+mfunc.stripMRTNamespace(joint)[1]+'_'+orientationReprNodes[0])
            cmds.rename(orientationReprNodes[1],
                        self.moduleNamespace+':'+mfunc.stripMRTNamespace(joint)[1]+'_'+orientationReprNodes[1])

        return containedNodes


    def createJointNodeControlHandleRepr(self):
        '''
        Creates handle control representation/helper objects on module nodes when called. It also creates segments 
        between node(s) to represent how the module nodes are connected.
        '''
        mfunc.updateAllTransforms()

        # List to collect non DAG nodes as they're generated, so that they can be added to the module container.
        containedNodes = []
        
        # Create handle(s) on every module node(s)(joint) in iteration.
        for i, joint in enumerate(self.nodeJoints):
        
            # Create a raw handle object.
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
            containedNodes.extend(clusterNodes)
            
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
            
                # Create a raw segment object.
                handleSegmentParts = objects.createRawSegmentCurve(self.modHandleColour)
                
                # Rename its associated non DAG nodes and collect them.
                for node in handleSegmentParts[4]:
                    if cmds.objExists(node):
                        containedNodes.append(cmds.rename(node,
                                        self.moduleNamespace+':'+mfunc.stripMRTNamespace(joint)[1]+'_clusterParts_'+node))
            
                # Now set up DG connections with appropriate nodes to help limit the segment curve between the
                # handle surfaces. This is done so that the length of this segment curve can be used to adjust
                # the length of the orientation representation control object, so that it always fits between
                # two node handle surfaces, even if they change in sizes.
                startClosestPointOnSurface = cmds.createNode('closestPointOnSurface',
                                                              name=joint+'_'+handleSegmentParts[5]+'_closestPointOnSurface')
                
                cmds.connectAttr(joint+'_controlShape.worldSpace[0]', startClosestPointOnSurface+'.inputSurface')
                cmds.connectAttr(self.nodeJoints[j+1]+'_worldPosLocator.worldPosition', startClosestPointOnSurface+'.inPosition')
                cmds.connectAttr(startClosestPointOnSurface+'.position', handleSegmentParts[5]+'.translate')
                endClosestPointOnSurface = cmds.createNode('closestPointOnSurface',
                                            name=self.nodeJoints[j+1]+'_'+handleSegmentParts[6]+'_closestPointOnSurface')

                cmds.connectAttr(self.nodeJoints[j+1]+'_controlShape.worldSpace[0]', endClosestPointOnSurface+'.inputSurface')
                cmds.connectAttr(joint+'_worldPosLocator.worldPosition', endClosestPointOnSurface+'.inPosition')
                cmds.connectAttr(endClosestPointOnSurface+'.position', handleSegmentParts[6]+'.translate')
                
                # Parent the segment and its related nodes to their associated group.
                cmds.parent([handleSegmentParts[1], handleSegmentParts[2][1], handleSegmentParts[3][1],
                             handleSegmentParts[5], handleSegmentParts[6]], self.moduleHandleSegmentGrp, absolute=True)
                
                # Rename the nodes.
                # Rename the curve transform.
                cmds.rename(handleSegmentParts[1],
                            self.moduleNamespace+':'+mfunc.stripMRTNamespace(joint)[1]+'_'+handleSegmentParts[1])
                            
                # Rename the 'start' and 'end' locators which constrain the cluster handles.
                cmds.rename(handleSegmentParts[5], joint+'_'+handleSegmentParts[5])
                cmds.rename(handleSegmentParts[6], self.nodeJoints[j+1]+'_'+handleSegmentParts[6])
                
                # Rename the cluster handles.
                startClusterHandle = cmds.rename(handleSegmentParts[2][1],
                                self.moduleNamespace+':'+mfunc.stripMRTNamespace(joint)[1]+'_'+handleSegmentParts[2][1])
                endClusterHandle = cmds.rename(handleSegmentParts[3][1],
                    self.moduleNamespace+':'+mfunc.stripMRTNamespace(self.nodeJoints[j+1])[1]+'_'+handleSegmentParts[3][1])
                
                # Rename the constraints on the cluster handles. Here, it is necessary to specify the
                # constraints by their DAG path.
                cmds.rename(startClusterHandle+'|'+handleSegmentParts[7].rpartition('|')[2],
                                                            joint+'_'+handleSegmentParts[7].rpartition('|')[2])
                cmds.rename(endClusterHandle + '|'+handleSegmentParts[8].rpartition('|')[2],
                                             self.nodeJoints[j+1]+'_'+handleSegmentParts[8].rpartition('|')[2])
                                             
                startClusterGrpParts = cmds.rename('segmentCurve_startClusterGroupParts',
                                                    startClusterHandle+'_clusterGroupParts')
                                                    
                endClusterGrpParts = cmds.rename('segmentCurve_endClusterGroupParts',
                                                  endClusterHandle+'_clusterGroupParts')
                
                # Clear the selection, and force an update on DG.
                cmds.select(clear=True)
                
                # Collect the nodes.
                containedNodes.extend([startClusterHandle+'Cluster', endClusterHandle+'Cluster',
                                       startClosestPointOnSurface, endClosestPointOnSurface,
                                       startClusterGrpParts, endClusterGrpParts])

        return containedNodes
    

    def createHierarchySegmentForModuleParentingRepr(self):
        '''
        Creates module parenting representation objects for a module. These objects are visible when
        a module is connected to a parent in the scene. It is indicated by a line segment with
        an arrow showing the parent-child relationship between two modules.
        '''
        containedNodes  = []
        
        # Create a segment curve with hierarchy representation.
        handleSegmentParts = objects.createRawSegmentCurve(3)
        hierarchyRepr = objects.createRawHierarchyRepresentation('X')
        cmds.setAttr(hierarchyRepr+'.scale', 1.0, 1.0, 1.0, type='double3')
        cmds.makeIdentity(hierarchyRepr, scale=True, apply=True)
        hierarchyReprShape = cmds.listRelatives(hierarchyRepr, children=True, shapes=True)[0]
        cmds.setAttr(hierarchyReprShape+'.overrideColor', 2)
        
        # Add their parts to the module container.
        for node in handleSegmentParts[4]:
            if cmds.objExists(node):
                containedNodes.append(cmds.rename(node, self.moduleNamespace+':moduleParentReprSegment_clusterParts_'+node))
        
        # Place them under the module parenting representation group.
        cmds.parent([handleSegmentParts[1], handleSegmentParts[2][1], handleSegmentParts[3][1], handleSegmentParts[5],
                                                handleSegmentParts[6]], self.moduleParentReprGrp, absolute=True)
                                                        
        # Constrain the start handle for the hierarchy "module parenting" representation
        # to the root node of the current module.
        cmds.pointConstraint(self.nodeJoints[0], handleSegmentParts[5], maintainOffset=False,
                            name=self.moduleNamespace+':moduleParentRepresentationSegment_startLocator_pointConstraint')
        
        # Constrain the module parenting hierarchy representation arrow (So that it stays at the mid
        # position of the segment curve as created above.
        cmds.pointConstraint(handleSegmentParts[5], handleSegmentParts[6], hierarchyRepr, maintainOffset=False,
                                        name=self.moduleNamespace+':moduleParentReprSegment_hierarchyRepr_pointConstraint')
                                        
        # Scale constrain the hierarchy representation to the joint in iteration.
        cmds.scaleConstraint(self.nodeJoints[0], hierarchyRepr, maintainOffset=False,
                             name=self.moduleNamespace+':moduleParentReprSegment_hierarchyRepr_scaleConstraint')
        cmds.aimConstraint(handleSegmentParts[5], hierarchyRepr, maintainOffset=False, aimVector=[1.0, 0.0, 0.0],
                           upVector=[0.0, 1.0, 0.0], worldUpVector=[0.0, 1.0, 0.0], worldUpType='objectRotation',
                           worldUpObject=handleSegmentParts[5],
                           name=self.moduleNamespace+':moduleParentReprSegment_hierarchyRepr_aimConstraint')
                           
        # Parent the orientation representation pre-transform and the hierarchy representation to their appropriate group.
        cmds.parent(hierarchyRepr, self.moduleParentReprGrp, absolute=True)
        cmds.rename(hierarchyRepr, self.moduleNamespace+':moduleParentReprSegment_'+hierarchyRepr)
        tempConstraint = cmds.pointConstraint(self.nodeJoints[0], handleSegmentParts[6], maintainOffset=False)
        cmds.delete(tempConstraint)
        cmds.rename(handleSegmentParts[1], self.moduleNamespace+':moduleParentReprSegment_'+handleSegmentParts[1])
        
        # Rename the 'start' and 'end' locators which constrain the cluster handles.
        cmds.rename(handleSegmentParts[5], self.moduleNamespace+':moduleParentReprSegment_'+handleSegmentParts[5])
        cmds.rename(handleSegmentParts[6], self.moduleNamespace+':moduleParentReprSegment_'+handleSegmentParts[6])
        
        # Rename the cluster handles.
        startClusterHandle = cmds.rename(handleSegmentParts[2][1],
                                            self.moduleNamespace+':moduleParentReprSegment_'+handleSegmentParts[2][1])
        endClusterHandle = cmds.rename(handleSegmentParts[3][1],
                                          self.moduleNamespace+':moduleParentReprSegment_'+handleSegmentParts[3][1])
                                          
        # Rename the constraints on the cluster handles. Here, it is necessary to specify the
        # constraints by their DAG path.
        cmds.rename(startClusterHandle+'|'+handleSegmentParts[7].rpartition('|')[2],
                    self.moduleNamespace+':moduleParentReprSegment_'+handleSegmentParts[7].rpartition('|')[2])
        cmds.rename(endClusterHandle + '|'+handleSegmentParts[8].rpartition('|')[2],
                    self.moduleNamespace+':moduleParentReprSegment_'+handleSegmentParts[8].rpartition('|')[2])
                    
        startClusterGrpParts = cmds.rename('segmentCurve_startClusterGroupParts', startClusterHandle+'_clusterGroupParts')
        endClusterGrpParts = cmds.rename('segmentCurve_endClusterGroupParts', endClusterHandle+'_clusterGroupParts')
        
        # Clear the selection, and force an update on DG.
        cmds.select(clear=True)
        cmds.setAttr(self.moduleParentReprGrp+'.visibility', 0)
        
        # Collect the nodes.
        containedNodes.extend([startClusterHandle+'Cluster', endClusterHandle+'Cluster',
                                                    startClusterGrpParts, endClusterGrpParts])
        return containedNodes


    def createJointNodeModule(self):
        '''
        Create a Joint Node module type.
        '''
        mfunc.updateAllTransforms()

        # Set the current namespace to root.
        cmds.namespace(setNamespace=':')
        
        # Create a new namespace for the module.
        cmds.namespace(add=self.moduleNamespace)
        
        # Create the module container.
        moduleContainer = cmds.container(name=self.moduleContainer)
        
        # Create an empty group for containing module handle segments.
        self.moduleHandleSegmentGrp = cmds.group(empty=True, name=self.moduleNamespace+':moduleHandleSegmentCurveGrp')
        
        # Create an empty group for containing module parenting representations.
        self.moduleParentReprGrp = cmds.group(empty=True, name=self.moduleNamespace+':moduleParentReprGrp')
        
        # Create an empty group for containing module hierarchy/orientation representations.
        self.moduleOrientationHierarchyReprGrp = cmds.group(empty=True,
                                                            name=self.moduleNamespace+':moduleOrientationHierarchyReprGrp')
        
        # Create module representation group containing the above two groups.
        self.moduleReprGrp = cmds.group([self.moduleHandleSegmentGrp, self.moduleOrientationHierarchyReprGrp,
                                                  self.moduleParentReprGrp], name=self.moduleNamespace+':moduleReprObjGrp')
        
        # Create module extras group.
        self.moduleExtrasGrp = cmds.group(empty=True, name=self.moduleNamespace+':moduleExtrasGrp')
        
        # Create group under module extras to keep clusters for scaling node handle shapes.
        self.moduleNodeHandleShapeScaleClusterGrp = cmds.group(empty=True,
                            name=self.moduleNamespace+':moduleNodeHandleShapeScaleClusterGrp', parent=self.moduleExtrasGrp)
        
        # Create main module group.
        self.moduleGrp = cmds.group([self.moduleReprGrp, self.moduleExtrasGrp], name=self.moduleNamespace+':moduleGrp')
        
        # Add a custom attributes to the module group to store module creation attributes.
        cmds.addAttr(self.moduleGrp, attributeType='short', longName='numberOfNodes', defaultValue=self.numNodes, k=False)
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
                self.proxyGeoGrp = cmds.group(empty=True, name=self.moduleNamespace+':proxyGeometryGrp')
                cmds.setAttr(self.proxyGeoGrp+'.overrideEnabled', 1)
                cmds.setAttr(self.proxyGeoGrp+'.overrideDisplayType', 2)
                if self.proxyGeoElbow:
                    cmds.addAttr(self.proxyGeoGrp, dataType='string', longName='elbowType', keyable=False)
                    cmds.setAttr(self.proxyGeoGrp+'.elbowType', self.proxyElbowType, type='string', lock=True)
                if self.mirrorModuleStatus == 'On':
                    cmds.addAttr(self.proxyGeoGrp, dataType='string', longName='mirrorInstance', keyable=False)
                    cmds.setAttr(self.proxyGeoGrp+'.mirrorInstance', self.proxyGeoMirrorInstance, type='string', lock=True)

        # Create module joints group, under the module group.
        self.moduleJointsGrp = cmds.group(empty=True, parent=self.moduleGrp, name=self.moduleNamespace+':moduleJointsGrp')

        # Initialize a list to contain created module node joints.
        self.nodeJoints = []

        # Get the positions of the module nodes, where the called method updates the self.initNodePos.
        self.returnNodeInfoTransformation(self.numNodes)

        # Move the joints group to the start position for the first joint node.
        cmds.xform(self.moduleJointsGrp, worldSpace=True, translation=self.initNodePos[0])

        # Create the module nodes (joints) by their position and name them accordingly.
        for index, nodePos in enumerate(self.initNodePos):
            if index == 0:
                jointName = cmds.joint(name=self.moduleNamespace+':root_node_transform', position=nodePos,
                                                                                radius=0.0, scaleCompensate=False)
            elif nodePos == self.initNodePos[-1]:
                jointName = cmds.joint(name=self.moduleNamespace+':end_node_transform', position=nodePos,
                                                                                radius=0.0, scaleCompensate=False)
            else:
                jointName = cmds.joint(name=self.moduleNamespace+':node_%s_transform'%(index), position=nodePos,
                                                                                radius=0.0, scaleCompensate=False)
            cmds.setAttr(jointName+'.drawStyle', 2)
            cmds.setAttr(jointName+'.rotateX', keyable=False)
            cmds.setAttr(jointName+'.rotateY', keyable=False)
            cmds.setAttr(jointName+'.rotateZ', keyable=False)
            cmds.setAttr(jointName+'.scaleX', keyable=False)
            cmds.setAttr(jointName+'.scaleY', keyable=False)
            cmds.setAttr(jointName+'.scaleZ', keyable=False)
            cmds.setAttr(jointName+'.visibility', keyable=False, channelBox=False)
            cmds.setAttr(jointName+'.radius', keyable=False, channelBox=False)
            self.nodeJoints.append(jointName)

        # Orient the joints.
        cmds.select(self.nodeJoints[0], replace=True)

        # For orientation we'll use the axis perpendicular to the creation plane as the up axis for secondary axis orient.
        secondAxisOrientation = {'XY':'z', 'YZ':'x', 'XZ':'y'}[self.onPlane] + 'up'
        cmds.joint(edit=True, orientJoint=self.nodeAxes.lower(), secondaryAxisOrient=secondAxisOrientation,
                                                                                zeroScaleOrient=True, children=True)
                                                                                
        # Mirror the module node joints (for the mirrored module) if the module mirroring is enabled
        # and the current module to be created is a mirrored module on the -ve side of the creation plane,
        # and if the mirror rotation function is set to "Behaviour".
        if self.mirrorModule and self.mirrorRotationFunc == 'Behaviour':
            mirrorPlane = {'XY':False, 'YZ':False, 'XZ':False}
            mirrorPlane[self.onPlane] = True
            mirroredJoints = cmds.mirrorJoint(self.nodeJoints[0], mirrorXY=mirrorPlane['XY'],
                                                mirrorYZ=mirrorPlane['YZ'], mirrorXZ=mirrorPlane['XZ'], mirrorBehavior=True)
            cmds.delete(self.nodeJoints[0])
            self.nodeJoints = []
            for joint in mirroredJoints:
                newJoint = cmds.rename(joint, self.moduleNamespace+':'+joint)
                self.nodeJoints.append(newJoint)

        # Orient the end joint node, if the module contains more than one joint node.
        if self.numNodes > 1:
            cmds.setAttr(self.nodeJoints[-1]+'.jointOrientX', 0)
            cmds.setAttr(self.nodeJoints[-1]+'.jointOrientY', 0)
            cmds.setAttr(self.nodeJoints[-1]+'.jointOrientZ', 0)

        # Clear selection after joint orientation.
        cmds.select(clear=True)

        # Add the module transform to the module, at the position of the root node.
        # Add custom attributes to it.
        moduleTransform = objects.load_xhandleShape(self.moduleNamespace+'_handle', 24, True)
        cmds.setAttr(moduleTransform[0]+'.localScaleX', 0.26)
        cmds.setAttr(moduleTransform[0]+'.localScaleY', 0.26)
        cmds.setAttr(moduleTransform[0]+'.localScaleZ', 0.26)
        cmds.setAttr(moduleTransform[0]+'.drawStyle', 8)
        cmds.setAttr(moduleTransform[0]+'.drawOrtho', 0)
        cmds.setAttr(moduleTransform[0]+'.wireframeThickness', 2)
        cmds.setAttr(moduleTransform[1]+'.scaleX', keyable=False)
        cmds.setAttr(moduleTransform[1]+'.scaleY', keyable=False)
        cmds.setAttr(moduleTransform[1]+'.scaleZ', keyable=False)
        cmds.setAttr(moduleTransform[1]+'.visibility', keyable=False)
        cmds.addAttr(moduleTransform[1], attributeType='float', longName='globalScale',
                                                        hasMinValue=True, minValue=0, defaultValue=1, keyable=True)
        self.moduleTransform = cmds.rename(moduleTransform[1], self.moduleNamespace+':module_transform')
        tempConstraint = cmds.pointConstraint(self.nodeJoints[0], self.moduleTransform, maintainOffset=False)
        cmds.delete(tempConstraint)

        # Add the module transform to the module group.
        cmds.parent(self.moduleTransform, self.moduleGrp, absolute=True)

        # Set up constraints for the module transform.
        module_node_parentConstraint = cmds.parentConstraint(self.moduleTransform, self.moduleJointsGrp,
                                maintainOffset=True, name=self.moduleNamespace+':moduleTransform_rootNode_parentConstraint')
        module_node_scaleConstraint = cmds.scaleConstraint(self.moduleTransform, self.moduleJointsGrp,
                                maintainOffset=False, name=self.moduleNamespace+':moduleTransform_rootNode_scaleConstraint')
        cmds.connectAttr(self.moduleTransform+'.globalScale', self.moduleTransform+'.scaleX')
        cmds.connectAttr(self.moduleTransform+'.globalScale', self.moduleTransform+'.scaleY')
        cmds.connectAttr(self.moduleTransform+'.globalScale', self.moduleTransform+'.scaleZ')

        # Connect the scale attributes to an aliased 'globalScale' attribute (This could've been done on the raw def itself,
        # but it was issuing a cycle; not sure why. But the DG eval was not cyclic).
        # Create hierarchy/orientation representation on joint node(s), depending on number of nodes in the module.
        containedNodes = self.createJointNodeControlHandleRepr()
        if len(self.nodeJoints) == 1:
            self.moduleSingleOrientationReprGrp = cmds.group(empty=True,
                                                             name=self.moduleNamespace+':moduleSingleOrientationReprGrp',
                                                             parent=self.moduleReprGrp)
                                                             
            singleOrientationTransform = objects.createRawSingleOrientationRepresentation()
            cmds.setAttr(singleOrientationTransform+'.scale', 0.65, 0.65, 0.65, type='double3')
            cmds.makeIdentity(singleOrientationTransform, scale=True, apply=True)
            cmds.parent(singleOrientationTransform, self.moduleSingleOrientationReprGrp, absolute=True)
            cmds.rename(singleOrientationTransform, self.moduleNamespace+':'+singleOrientationTransform)
            cmds.xform(self.moduleSingleOrientationReprGrp, worldSpace=True, absolute=True,
                                translation=cmds.xform(self.nodeJoints[0], query=True, worldSpace=True, translation=True))
            cmds.parentConstraint(self.nodeJoints[0], self.moduleSingleOrientationReprGrp, maintainOffset=False,
                                                        name=self.moduleSingleOrientationReprGrp+'_parentConstraint')
            cmds.scaleConstraint(self.moduleTransform, self.moduleSingleOrientationReprGrp, maintainOffset=False,
                                                        name=self.moduleSingleOrientationReprGrp+'_scaleConstraint')
        
        # Set the sizes for the module node handle shapes.
        for joint in self.nodeJoints:
            xhandle = objects.load_xhandleShape(joint, self.modHandleColour)
            cmds.setAttr(xhandle[0]+'.localScaleX', 0.089)
            cmds.setAttr(xhandle[0]+'.localScaleY', 0.089)
            cmds.setAttr(xhandle[0]+'.localScaleZ', 0.089)
            cmds.setAttr(xhandle[0]+'.ds', 5)

        # If there's more than one node, create orientation/hierarchy representations for all joints, except for
        # the end joint. Also unparent the individual joints in the oriented joint chain to the joint group. This
        # is needed only if there are more than one joint in the module; then the unparenting will begin from the
        # second joint, since the first (start) is already under joints group.
        if len(self.nodeJoints) > 1:
            for joint in self.nodeJoints[1:]:
                cmds.parent(joint, self.moduleJointsGrp, absolute=True)
            containedNodes += self.createOrientationHierarchyReprOnNodes()

        # Clear selection.
        cmds.select(clear=True)

        # If the module contains only one node then delete the handle segment and orientation/hierarchy
        # representation groups, since they're not needed.
        if self.numNodes == 1:
            cmds.delete([self.moduleHandleSegmentGrp, self.moduleOrientationHierarchyReprGrp])
        
        # Create module parenting representation objects.
        containedNodes += self.createHierarchySegmentForModuleParentingRepr()
        
        # Create the proxy geometry for the module if it is enabled.
        if self.proxyGeoStatus:
            if self.proxyGeoElbow:
                self.createProxyGeo_elbows(self.proxyElbowType)
            if self.proxyGeoBones:
                self.createProxyGeo_bones()

        # Add the module group to the contained nodes list.
        containedNodes += [self.moduleGrp]

        # Add the contained nodes to the module container.
        mfunc.addNodesToContainer(self.moduleContainer, containedNodes, includeHierarchyBelow=True, includeShapes=True)

        # Publish contents to the container.
        # Publish the orientation representation control for module joints.
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

        # If the module contains only single node, publish its orientation control.
        if len(self.nodeJoints) == 1:
            singleOrientationTransform = self.moduleNamespace+':single_orient_repr_transform'
            cmds.container(self.moduleContainer, edit=True, publishAndBind=[singleOrientationTransform+'.rotate',
                                                                           'single_orient_repr_transform_rotate'])
        # Add and publish custom attributes on the module transform.
        self.addCustomAttributesOnModuleTransform()
        
        if self.numNodes > 1:
            self.connectCustomOrientationReprToModuleProxies()


    def createSplineNodeModule(self, *args):
        '''
        Create a Spline Node module type.
        Unlike other module node types, the nodes cannot be translated directly.
        '''
        mfunc.updateAllTransforms()
        
        # Set the current namespace to root.
        cmds.namespace(setNamespace=':')
        
        # Create a new namespace for the module.
        cmds.namespace(add=self.moduleNamespace)
        
        # Create the module container.
        moduleContainer = cmds.container(name=self.moduleContainer)
        
        # Initialize a list to collect non DAG nodes, for adding to the module container.
        collectedNodes = []
        
        # Create an empty group for containing module handle segments.
        self.moduleSplineCurveGrp = cmds.group(empty=True, name=self.moduleNamespace+':moduleSplineCurveGrp')
        
        # Create an empty group for containing module hierarchy/orientation representations.
        self.moduleHandleGrp = cmds.group(empty=True, name=self.moduleNamespace+':moduleHandleGrp')
        
        # Create an empty group for containing module parenting representations.
        self.moduleParentReprGrp = cmds.group(empty=True, name=self.moduleNamespace+':moduleParentReprGrp')
        
        # Create an empty group for containing splineAdjustCurveTransform.
        self.moduleSplineAdjustCurveGrp = cmds.group(empty=True, name=self.moduleNamespace+':moduleSplineAdjustCurveGrp')
        
        # Create an empty group for containing orientation representation transforms and nodes.
        self.moduleOrientationReprGrp = cmds.group(empty=True, name=self.moduleNamespace+':moduleOrientationReprGrp')
        
        # Create a module representation group containing the above four groups.
        self.moduleReprGrp = cmds.group([self.moduleSplineAdjustCurveGrp, self.moduleSplineCurveGrp, self.moduleHandleGrp, 
                    self.moduleOrientationReprGrp, self.moduleParentReprGrp], name=self.moduleNamespace+':moduleReprObjGrp')

        # Create a main module group, with the representation group as the child.
        self.moduleGrp = cmds.group([self.moduleReprGrp], name=self.moduleNamespace+':moduleGrp')
        
        # Add a custom attributes to the module group to store module creation attributes.
        cmds.addAttr(self.moduleGrp, attributeType='short', longName='numberOfNodes', defaultValue=self.numNodes, keyable=False)
        cmds.addAttr(self.moduleGrp, dataType='string', longName='nodeOrient', keyable=False)
        cmds.setAttr(self.moduleGrp+'.nodeOrient', self.nodeAxes, type='string')
        cmds.addAttr(self.moduleGrp, dataType='string', longName='moduleParent', keyable=False)
        cmds.setAttr(self.moduleGrp+'.moduleParent', 'None', type='string')
        cmds.addAttr(self.moduleGrp, dataType='string', longName='onPlane', keyable=False)
        cmds.setAttr(self.moduleGrp+'.onPlane', '+'+self.onPlane, type='string')
        cmds.addAttr(self.moduleGrp, dataType='string', longName='mirrorTranslation', keyable=False)
        cmds.setAttr(self.moduleGrp+'.mirrorTranslation', self.mirrorTranslationFunc, type='string')
        
        collectedNodes.append(self.moduleGrp)
        
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
            self.proxyGeoGrp = cmds.group(empty=True, name=self.moduleNamespace+':proxyGeometryGrp')
            cmds.setAttr(self.proxyGeoGrp+'.overrideEnabled', 1)
            cmds.setAttr(self.proxyGeoGrp+'.overrideDisplayType', 2)
            cmds.addAttr(self.proxyGeoGrp, dataType='string', longName='elbowType', keyable=False)
            cmds.setAttr(self.proxyGeoGrp+'.elbowType', self.proxyElbowType, type='string', lock=True)
            if self.mirrorModuleStatus == 'On':
                cmds.addAttr(self.proxyGeoGrp, dataType='string', longName='mirrorInstance', keyable=False)
                cmds.setAttr(self.proxyGeoGrp+'.mirrorInstance', self.proxyGeoMirrorInstance, type='string', lock=True)
        
        # Create a module joints group, under the module group.
        self.moduleJointsGrp = cmds.group(empty=True, parent=self.moduleGrp, name=self.moduleNamespace+':moduleJointsGrp')
        
        # Initialize a list to contain created module node joints.
        self.nodeJoints = []
        
        # Get the positions of the module nodes, where the called method updates the self.initNodePos.
        self.returnNodeInfoTransformation(numNodes=4)
        
        # Create the spline module curve
        splineNodeCurve = cmds.curve(degree=3, point=self.initNodePos, worldSpace=True)
        cmds.xform(splineNodeCurve, centerPivots=True)
        cmds.rebuildCurve(splineNodeCurve, constructionHistory=False, replaceOriginal=True, rebuildType=0, degree=3,
                          endKnots=True, keepEndPoints=True, keepRange=0, keepControlPoints=False, keepTangents=False,
                          spans=cmds.getAttr(splineNodeCurve+'.spans'), tolerance=0.01)
        splineNodeCurve = cmds.rename(splineNodeCurve, self.moduleNamespace+':splineNode_curve')
        cmds.displaySmoothness(splineNodeCurve, pointsWire=32)
        cmds.toggle(splineNodeCurve, template=True, state=True)
        cmds.parent(splineNodeCurve, self.moduleSplineCurveGrp, absolute=True)

        cmds.select(clear=True)

        self.returnNodeInfoTransformation(self.numNodes)
        
        # Create the module node joints, to be attached to the spline module curve.
        self.nodeJoints = []
        for index in range(len(self.initNodePos)):
            if index == 0:
                jointName = cmds.joint(name=self.moduleNamespace+':root_node_transform', position=self.initNodePos[index], radius=0.0)
            elif index == len(self.initNodePos)-1:
                jointName = cmds.joint(name=self.moduleNamespace+':end_node_transform', position=self.initNodePos[index], radius=0.0)
            else:
                jointName = cmds.joint(name=self.moduleNamespace+':node_%s_transform'%(index), position=self.initNodePos[index], radius=0.0)
            self.nodeJoints.append(jointName)

        # Orient the node joints.
        # For orientation we'll use the axis perpendicular to the creation plane as the up axis for secondary axis orient.
        cmds.select(self.nodeJoints[0], replace=True)
        secondAxisOrientation = {'XY':'z', 'YZ':'x', 'XZ':'y'}[self.onPlane] + 'up'
        cmds.joint(edit=True, orientJoint=self.nodeAxes.lower(), secondaryAxisOrient=secondAxisOrientation,
                                                                        zeroScaleOrient=True, children=True)
        cmds.parent(self.nodeJoints[0], self.moduleJointsGrp, absolute=True)

        # Mirror the module node joints (for the mirrored module) if the module mirroring is enabled
        # and the current module to be created is a mirrored module on the -ve side of the creation plane,
        # and if the mirror rotation function is set to "Behaviour".
        if self.mirrorModule and self.mirrorRotationFunc == 'Behaviour':
            mirrorPlane = {'XY':False, 'YZ':False, 'XZ':False}
            mirrorPlane[self.onPlane] = True
            mirroredJoints = cmds.mirrorJoint(self.nodeJoints[0], mirrorXY=mirrorPlane['XY'], mirrorYZ=mirrorPlane['YZ'],
                                                                        mirrorXZ=mirrorPlane['XZ'], mirrorBehavior=True)
            cmds.delete(self.nodeJoints[0])
            self.nodeJoints = []
            for joint in mirroredJoints:
                newJoint = cmds.rename(joint, self.moduleNamespace+':'+joint)
                self.nodeJoints.append(newJoint)

        # Orient the end joint node.
        cmds.setAttr(self.nodeJoints[-1]+'.jointOrientX', 0)
        cmds.setAttr(self.nodeJoints[-1]+'.jointOrientY', 0)
        cmds.setAttr(self.nodeJoints[-1]+'.jointOrientZ', 0)

        # Clear selection after joint orientation.
        cmds.select(clear=True)

        # Unparent the spline node joints.
        for joint in self.nodeJoints[1:]:
            cmds.parent(joint, self.moduleJointsGrp, absolute=True)

        # Attach the module nodes to the spline module curve.
        u_parametersOnCurve = [1.0/(len(self.nodeJoints)-1)*c for c in xrange(len(self.nodeJoints))]
        for index in range(len(self.nodeJoints)):
            pointOnCurveInfo = cmds.createNode('pointOnCurveInfo', name='%s:%s_pointOnCurveInfo' % (self.moduleNamespace,
                                                                        mfunc.stripMRTNamespace(self.nodeJoints[index])[1]))
            cmds.connectAttr(self.moduleNamespace+':splineNode_curveShape.worldSpace', pointOnCurveInfo+'.inputCurve')
            cmds.connectAttr(pointOnCurveInfo+'.position', self.nodeJoints[index]+'.translate')
            cmds.setAttr(pointOnCurveInfo+'.parameter', u_parametersOnCurve[index])
            collectedNodes.append(pointOnCurveInfo)
        
        # Create the weighted clusters on the spline module curve for the start and end module transform handles.
        # The spline module has two module transforms at either end of the spline module curve.
        clusterWeights = sorted([1.0/3*c for c in xrange(4)], reverse=True)[:-1]
        # Start cluster at the root node position
        startCluster = cmds.cluster([splineNodeCurve+'.cv[%s]'%(cv) for cv in xrange(0, 3)], relative=True, name=splineNodeCurve+'_startCluster')
        cmds.setAttr(startCluster[1]+'.visibility', 0)
        cmds.parent(startCluster[1], self.moduleSplineCurveGrp, absolute=True)
        for (cv, weight) in zip(xrange(0, 3), clusterWeights):
            cmds.percent(startCluster[0], '%s.cv[%s]'%(splineNodeCurve, cv), value=weight)
        # End cluster at the end (last) node position.
        endCluster = cmds.cluster([splineNodeCurve+'.cv[%s]'%(cv) for cv in xrange(3, 0, -1)], relative=True, name=splineNodeCurve+'_endCluster')
        cmds.setAttr(endCluster[1]+'.visibility', 0)
        cmds.parent(endCluster[1], self.moduleSplineCurveGrp, absolute=True)
        for (cv, weight) in zip(xrange(3, 0, -1), clusterWeights):
            cmds.percent(endCluster[0], '%s.cv[%s]'%(splineNodeCurve, cv), value=weight)
        collectedNodes.extend([startCluster[0], endCluster[0]])

        # Create the start module transform to the module, at the position of the root node.
        startHandle = objects.load_xhandleShape(self.moduleNamespace+'_startHandle', 11, True)
        cmds.setAttr(startHandle[0]+'.localScaleX', 0.4)
        cmds.setAttr(startHandle[0]+'.localScaleY', 0.4)
        cmds.setAttr(startHandle[0]+'.localScaleZ', 0.4)
        cmds.setAttr(startHandle[0]+'.drawStyle', 3)
        cmds.setAttr(startHandle[0]+'.wireframeThickness', 2)
        cmds.setAttr(startHandle[1]+'.rotateX', keyable=False)
        cmds.setAttr(startHandle[1]+'.rotateY', keyable=False)
        cmds.setAttr(startHandle[1]+'.rotateZ', keyable=False)
        cmds.setAttr(startHandle[1]+'.scaleX', keyable=False)
        cmds.setAttr(startHandle[1]+'.scaleY', keyable=False)
        cmds.setAttr(startHandle[1]+'.scaleZ', keyable=False)
        cmds.setAttr(startHandle[1]+'.visibility', keyable=False)
        startHandle = cmds.rename(startHandle[1], self.moduleNamespace+':splineStartHandleTransform')
        
        # Position the start module transform and constrain the start cluster to it.
        tempConstraint = cmds.pointConstraint(self.nodeJoints[0], startHandle, maintainOffset=False)
        cmds.delete(tempConstraint)
        cmds.pointConstraint(startHandle, startCluster[1], maintainOffset=True, name=startCluster[1]+'_parentConstraint')
        cmds.parent(startHandle, self.moduleHandleGrp, absolute=True)
        
        # Create the end module transform, at the position of the last node for the module.
        endHandle = objects.load_xhandleShape(self.moduleNamespace+'_endHandle', 10, True)
        cmds.setAttr(endHandle[0]+'.localScaleX', 0.35)
        cmds.setAttr(endHandle[0]+'.localScaleY', 0.35)
        cmds.setAttr(endHandle[0]+'.localScaleZ', 0.35)
        cmds.setAttr(endHandle[0]+'.drawStyle', 3)
        cmds.setAttr(endHandle[0]+'.wireframeThickness', 2)
        cmds.setAttr(endHandle[1]+'.rotateX', keyable=False)
        cmds.setAttr(endHandle[1]+'.rotateY', keyable=False)
        cmds.setAttr(endHandle[1]+'.rotateZ', keyable=False)
        cmds.setAttr(endHandle[1]+'.scaleX', keyable=False)
        cmds.setAttr(endHandle[1]+'.scaleY', keyable=False)
        cmds.setAttr(endHandle[1]+'.scaleZ', keyable=False)
        cmds.setAttr(endHandle[1]+'.visibility', keyable=False)
        endHandle = cmds.rename(endHandle[1], self.moduleNamespace+':splineEndHandleTransform')

        # Position the end module transform and constrain the end cluster to it.
        tempConstraint = cmds.pointConstraint(self.nodeJoints[-1], endHandle, maintainOffset=False)
        cmds.delete(tempConstraint)
        cmds.pointConstraint(endHandle, endCluster[1], maintainOffset=True, name=endCluster[1]+'_parentConstraint')
        cmds.parent(endHandle, self.moduleHandleGrp, absolute=True)
        
        # Create the spline module curve adjust control transforms. These are used to modify the 
        # spline curve and hence affect the positions of the module nodes.
        splineAdjustCurveTransformList = []
        for (index, startWeight, endWeight) in [(0, 1, 0), (1, 0.66, 0.33), (2, 0.33, 0.66), (3, 0, 1)]:
            
            # Create the curve adjust control transform.
            splineAdjustCurveTransforms = objects.createRawSplineAdjustCurveTransform(self.modHandleColour)
            cmds.setAttr(splineAdjustCurveTransforms[0]+'.scale', 0.8, 0.8, 0.8, type='double3')
            cmds.makeIdentity(splineAdjustCurveTransforms[0], scale=True, apply=True)
            splineAdjustCurvePreTransform = cmds.rename(splineAdjustCurveTransforms[0], self.moduleNamespace+':'+splineAdjustCurveTransforms[0].partition('_')[0]+'_'+str(index+1)+'_'+splineAdjustCurveTransforms[0].partition('_')[2])
            splineAdjustCurveTransform = cmds.rename(splineAdjustCurveTransforms[1], self.moduleNamespace+':'+splineAdjustCurveTransforms[1].partition('_')[0]+'_'+str(index+1)+'_'+splineAdjustCurveTransforms[1].partition('_')[2])
            splineAdjustCurveTransformList.append(splineAdjustCurveTransform)
            
            # Create the cluster on spline module curve to be driven by curve adjust control transform.
            splineAdjustCurveCluster = cmds.cluster('%s.cv[%s]'%(splineNodeCurve, index), relative=True, name=splineAdjustCurveTransform+'_Cluster')
            cmds.setAttr(splineAdjustCurveCluster[1]+'.visibility', 0)
            collectedNodes.append(splineAdjustCurveCluster[0])
            
            # Position the curve adjust control transform.
            tempConstraint = cmds.pointConstraint(splineAdjustCurveCluster[1], splineAdjustCurvePreTransform, maintainOffset=False)
            cmds.delete(tempConstraint)
            
            # Constrain the curve adjust control pre-transform to spline module start and end transforms.
            startPointConstraint = cmds.pointConstraint(startHandle, splineAdjustCurvePreTransform, maintainOffset=False, weight=startWeight, name=splineAdjustCurvePreTransform+'_startHandle_pointConstraint')
            endPointConstraint = cmds.pointConstraint(endHandle, splineAdjustCurvePreTransform, maintainOffset=False, weight=endWeight, name=splineAdjustCurvePreTransform+'_endHandle_pointConstraint')
            
            # Constrain the adjust curve cluster to its control transform as created above.
            clusterGroup = cmds.group(splineAdjustCurveCluster[1], name=splineAdjustCurveCluster[1]+'_preTransform')
            cmds.parent(clusterGroup, splineAdjustCurvePreTransform, absolute=True)
            cmds.pointConstraint(splineAdjustCurveTransform, splineAdjustCurveCluster[1], maintainOffset=True, name=splineAdjustCurveCluster[1]+'_pointConstraint')

            cmds.parent(splineAdjustCurvePreTransform, self.moduleSplineAdjustCurveGrp, absolute=True)
            
            # Get the last spline curve adjust transform as the up vector target object for orienting 
            # the module nodes attached to the spline module curve.
            if index == 3:
                tangentConstraintTargetObject = splineAdjustCurveTransform
        
        # Set-up / connect orientations for the module node joints attached to the spline module curves.
        worldReferenceTransform = cmds.createNode('transform', name=self.moduleNamespace+':orientationWorldReferenceTransform', parent=self.moduleOrientationReprGrp)
        aimVector={'X':[1.0, 0.0, 0.0], 'Y':[0.0, 1.0, 0.0], 'Z':[0.0, 0.0, 1.0]}[self.nodeAxes[0]]
        upVector = {'X':[1.0, 0.0, 0.0], 'Y':[0.0, 1.0, 0.0], 'Z':[0.0, 0.0, 1.0]}[self.nodeAxes[1]]
        worldUpVector = {'XY':[0.0, 0.0, 1.0], 'YZ':[1.0, 0.0, 0.0], 'XZ':[0.0, 1.0, 0.0]}[self.onPlane]
        if self.mirrorModule and self.mirrorRotationFunc == 'Behaviour':
            aimVector = [i*-1 for i in aimVector]
        pairBlend_inputDriven = []
        for index in range(len(self.nodeJoints)):
            pairBlend = cmds.createNode('pairBlend', name=self.nodeJoints[index]+'_pairBlend', skipSelect=True)
            pairBlend_inputDriven.append(pairBlend)
            orientConstraint = cmds.orientConstraint(worldReferenceTransform, self.nodeJoints[index], maintainOffset=False, name=self.nodeJoints[index]+'_orientConstraint')[0]
            cmds.disconnectAttr(orientConstraint+'.constraintRotateX', self.nodeJoints[index]+'.rotateX')
            cmds.disconnectAttr(orientConstraint+'.constraintRotateY', self.nodeJoints[index]+'.rotateY')
            cmds.disconnectAttr(orientConstraint+'.constraintRotateZ', self.nodeJoints[index]+'.rotateZ')
            tangentConstraint = cmds.tangentConstraint(self.moduleNamespace+':splineNode_curve', self.nodeJoints[index], aimVector=aimVector, upVector=upVector, worldUpType='objectrotation', worldUpVector=worldUpVector, worldUpObject=tangentConstraintTargetObject, name=self.nodeJoints[index]+'_tangentConstraint')[0]
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
        collectedNodes.extend(pairBlend_inputDriven)
        
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

            rawLocaAxesInfoReprPreTransform = cmds.rename(rawLocalAxesInfoReprTransforms[0], joint+'_'+rawLocalAxesInfoReprTransforms[0])
            rawLocaAxesInfoReprTransform = cmds.rename(rawLocalAxesInfoReprTransforms[1], joint+'_'+rawLocalAxesInfoReprTransforms[1])
            
            # Add an attribute to modify the up vector rotation for the axes info object.
            # Can be used to flip the axial orientation for the module node.
            cmds.addAttr(rawLocaAxesInfoReprTransform, attributeType='enum', longName='tangent_Up_vector', enumName='Original:Reversed:', defaultValue=0, keyable=True)

            for (driver, driven) in ((1, -1), (0, 1)):
                cmds.setAttr(rawLocaAxesInfoReprTransform+'.tangent_Up_vector', driver)
                cmds.setAttr(joint+'_tangentConstraint.upVector'+self.nodeAxes[1].upper(), driven)
                cmds.setDrivenKeyframe(joint+'_tangentConstraint.upVector'+self.nodeAxes[1].upper(), currentDriver=rawLocaAxesInfoReprTransform+'.tangent_Up_vector')

            xhandle = objects.load_xhandleShape(joint, 2)
            cmds.setAttr(xhandle[0]+'.localScaleX', 0.09)
            cmds.setAttr(xhandle[0]+'.localScaleY', 0.09)
            cmds.setAttr(xhandle[0]+'.localScaleZ', 0.09)
            cmds.setAttr(xhandle[0]+'.ds', 5)

            cmds.pointConstraint(joint, rawLocaAxesInfoReprPreTransform, maintainOffset=False, name=rawLocaAxesInfoReprPreTransform+'_pointConstraint')
            cmds.orientConstraint(joint, rawLocaAxesInfoReprPreTransform, maintainOffset=False, name=rawLocaAxesInfoReprPreTransform+'_orientConstraint')

            rawLocaAxesInfoReprTransforms.append(rawLocaAxesInfoReprTransform)

        cmds.select(clear=True)
        
        # Create module parenting representation objects.
        collectedNodes += self.createHierarchySegmentForModuleParentingRepr()
        
        # Create the proxy geometry for the module if enabled.
        if self.proxyGeoStatus and self.proxyGeoElbow:
            self.createProxyGeo_elbows(self.proxyElbowType)

        mfunc.addNodesToContainer(self.moduleContainer, collectedNodes, includeHierarchyBelow=True, includeShapes=True)
        
        # Publish the translation attributes for the start and end module transforms.
        cmds.container(self.moduleContainer, edit=True, publishAndBind=[startHandle+'.translate', mfunc.stripMRTNamespace(startHandle)[1]+'_translate'])
        cmds.container(self.moduleContainer, edit=True, publishAndBind=[endHandle+'.translate', mfunc.stripMRTNamespace(endHandle)[1]+'_translate'])
        for transform in splineAdjustCurveTransformList:
            cmds.container(self.moduleContainer, edit=True, publishAndBind=[transform+'.translate', mfunc.stripMRTNamespace(transform)[1]+'_translate'])
        
        # Add the necessary module attributes on the start module transform.
        self.addCustomAttributesOnModuleTransform()
        cmds.connectAttr(startHandle+'.Global_size', startHandle+'.scaleX')
        cmds.connectAttr(startHandle+'.Global_size', startHandle+'.scaleY')
        cmds.connectAttr(startHandle+'.Global_size', startHandle+'.scaleZ')
        cmds.connectAttr(startHandle+'.Global_size', endHandle+'.scaleX')
        cmds.connectAttr(startHandle+'.Global_size', endHandle+'.scaleY')
        cmds.connectAttr(startHandle+'.Global_size', endHandle+'.scaleZ')
        
        # Connect the module global scaling to the spline module curve adjust transforms.
        for i in range(1, 5):
            for j in ['X', 'Y', 'Z']:
                cmds.connectAttr(startHandle+'.Global_size', self.moduleNamespace+':spline_'+str(i)+'_adjustCurve_transform.scale'+str(j))
        
        # Connect the module global scaling to the module node joints.
        for joint in self.nodeJoints:
            cmds.connectAttr(startHandle+'.Global_size', joint+'Shape.addScaleX')
            cmds.connectAttr(startHandle+'.Global_size', joint+'Shape.addScaleY')
            cmds.connectAttr(startHandle+'.Global_size', joint+'Shape.addScaleZ')
            cmds.connectAttr(startHandle+'.Global_size', joint+'_localAxesInfoRepr_preTransform.scaleX')
            cmds.connectAttr(startHandle+'.Global_size', joint+'_localAxesInfoRepr_preTransform.scaleY')
            cmds.connectAttr(startHandle+'.Global_size', joint+'_localAxesInfoRepr_preTransform.scaleZ')
            
            # Connect the module global scaling to the proxy elbow transforms. 
            if self.proxyGeoStatus and self.proxyGeoElbow:
                cmds.connectAttr(startHandle+'.Global_size', joint+'_proxy_elbow_geo_scaleTransform.scaleX')
                cmds.connectAttr(startHandle+'.Global_size', joint+'_proxy_elbow_geo_scaleTransform.scaleY')
                cmds.connectAttr(startHandle+'.Global_size', joint+'_proxy_elbow_geo_scaleTransform.scaleZ')
        
        # Connect the module node orientation attributes on the start module transform.
        cmds.connectAttr(startHandle+'.Node_Orientation_Info', self.moduleOrientationReprGrp+'.visibility')
        for transform in rawLocaAxesInfoReprTransforms:
            rotateAxis = self.nodeAxes[0]
            cmds.container(self.moduleContainer, edit=True, publishAndBind=[transform+'.tangent_Up_vector', mfunc.stripMRTNamespace(transform)[1]+'_tangent_Up_Vector'])
            cmds.connectAttr(startHandle+'.Axis_Rotate', transform+'.rotate'+rotateAxis)
            cmds.connectAttr(startHandle+'.Node_Local_Orientation_Repr_Size', transform+'.scaleX')
            cmds.connectAttr(startHandle+'.Node_Local_Orientation_Repr_Size', transform+'.scaleY')
            cmds.connectAttr(startHandle+'.Node_Local_Orientation_Repr_Size', transform+'.scaleZ')

        cmds.setAttr(startHandle+'.Node_Local_Orientation_Repr_Size', 0.7)
        
        # Add any previous set-driven keyframe nodes to the module container.
        cmds.namespace(setNamespace=self.moduleNamespace)
        namespaceNodes = cmds.namespaceInfo(listOnlyDependencyNodes=True)
        animCurveNodes = cmds.ls(namespaceNodes, type='animCurve')
        mfunc.addNodesToContainer(self.moduleContainer, animCurveNodes)
        
        cmds.namespace(setNamespace=':')
        
        # If orientation representation is turned off for modules, turn off 
        # node orientation representation objects.
        if not self.showOrientation:
            cmds.setAttr(startHandle+'.Node_Orientation_Info', 0)
            
        # Connect module orientation representation objects to drive 
        # orientation for module proxy geometry.
        self.connectCustomOrientationReprToModuleProxies()
        

    def createHingeNodeModule(self):
        '''
        Create a Hinge Node module type.
        '''
        mfunc.updateAllTransforms()
        
        # Set the current namespace to root.
        cmds.namespace(setNamespace=':')
        
        # Create a new namespace for the module.
        cmds.namespace(add=self.moduleNamespace)
        
        # Clear selection.
        cmds.select(clear=True)
        
        # Create the module container.
        moduleContainer = cmds.container(name=self.moduleContainer)
        
        # Create an empty group for containing module handle segments.
        self.moduleHandleSegmentGrp = cmds.group(empty=True, name=self.moduleNamespace+':moduleHandleSegmentCurveGrp')
        
        # Create an empty group for containing module parenting representations.
        self.moduleParentReprGrp = cmds.group(empty=True, name=self.moduleNamespace+':moduleParentReprGrp')
        
        # Create an empty group for containing module hand hierarchy representations.
        self.moduleHierarchyReprGrp = cmds.group(empty=True, name=self.moduleNamespace+':moduleHierarchyReprGrp')
        
        # Create a module representation group containing the above two groups.
        self.moduleReprGrp = cmds.group([self.moduleHandleSegmentGrp, self.moduleHierarchyReprGrp, self.moduleParentReprGrp], name=self.moduleNamespace+':moduleReprObjGrp')
        
        # Create a module extras group.
        self.moduleExtrasGrp = cmds.group(empty=True, name=self.moduleNamespace+':moduleExtrasGrp')
        
        # Create a group under module extras to keep clusters for scaling node handle shapes.
        self.moduleNodeHandleShapeScaleClusterGrp = cmds.group(empty=True, name=self.moduleNamespace+':moduleNodeHandleShapeScaleClusterGrp', parent=self.moduleExtrasGrp)
        
        # Create a group under module extras to keep the IK segment aim nodes.
        self.moduleIKsegmentMidAimGrp = cmds.group(empty=True, name=self.moduleNamespace+':moduleIKsegmentMidAimGrp', parent=self.moduleExtrasGrp)
        
        # Create a group to contain the IK nodes and handles.
        self.moduleIKnodesGrp = cmds.group(empty=True, name=self.moduleNamespace+':moduleIKnodesGrp')
        
        # Create a main module group.
        self.moduleGrp = cmds.group([self.moduleReprGrp, self.moduleExtrasGrp, self.moduleIKnodesGrp], name=self.moduleNamespace+':moduleGrp')

        # Add a custom attributes to the module group to store module creation attributes.
        cmds.addAttr(self.moduleGrp, attributeType='short', longName='numberOfNodes', defaultValue=self.numNodes, keyable=False)
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
                self.proxyGeoGrp = cmds.group(empty=True, name=self.moduleNamespace+':proxyGeometryGrp')
                cmds.setAttr(self.proxyGeoGrp+'.overrideEnabled', 1)
                cmds.setAttr(self.proxyGeoGrp+'.overrideDisplayType', 2)
                if self.proxyGeoElbow:
                    cmds.addAttr(self.proxyGeoGrp, dataType='string', longName='elbowType', keyable=False)
                    cmds.setAttr(self.proxyGeoGrp+'.elbowType', self.proxyElbowType, type='string', lock=True)
                if self.mirrorModuleStatus == 'On':
                    cmds.addAttr(self.proxyGeoGrp, dataType='string', longName='mirrorInstance', keyable=False)
                    cmds.setAttr(self.proxyGeoGrp+'.mirrorInstance', self.proxyGeoMirrorInstance, type='string', lock=True)
        
        # Create a main module joints group, under the module group.
        self.moduleJointsGrp = cmds.group(empty=True, parent=self.moduleGrp, name=self.moduleNamespace+':moduleJointsGrp')
        
        # Initialize a list to contain created module node joints.
        self.nodeJoints = []
        
        # Get the positions of the module nodes, where the called method updates the self.initNodePos.
        self.returnNodeInfoTransformation(self.numNodes)
        
        # Move the joints group and the nodule IK nodes to the start position for the first joint node.
        cmds.xform(self.moduleJointsGrp, worldSpace=True, translation=self.initNodePos[0])
        cmds.xform(self.moduleIKnodesGrp, worldSpace=True, translation=self.initNodePos[0])
        
        # Calculate the position of the mid hinge node.
        containedNodes = []
        offset = self.moduleLen / 10.0
        hingeOffset = {'YZ':[offset, 0.0, 0.0], 'XZ':[0.0, offset, 0.0], 'XY':[0.0, 0.0, offset]}[self.onPlane]
        self.initNodePos[1] = map(lambda x,y: x+y, self.initNodePos[1], hingeOffset)

        # Create the module nodes (joints) by their position and name them accordingly.
        index = 0
        for nodePos in self.initNodePos:
            if index == 0:
                jointName = cmds.joint(name=self.moduleNamespace+':root_node_transform', position=nodePos, radius=0.0, scaleCompensate=False)
            elif nodePos == self.initNodePos[-1]:
                jointName = cmds.joint(name=self.moduleNamespace+':end_node_transform', position=nodePos, radius=0.0, scaleCompensate=False)
            else:
                jointName = cmds.joint(name=self.moduleNamespace+':node_%s_transform'%(index), position=nodePos, radius=0.0, scaleCompensate=False)
            cmds.setAttr(jointName+'.drawStyle', 2)
            self.nodeJoints.append(jointName)
            index += 1
            
        # Orient the joints.
        cmds.select(self.nodeJoints[0], replace=True)
        
        # For orientation we'll use the axis perpendicular to the creation plane as the up axis for secondary axis orient.
        secondAxisOrientation = {'XY':'z', 'YZ':'x', 'XZ':'y'}[self.onPlane] + 'up'
        cmds.joint(edit=True, orientJoint=self.nodeAxes.lower(), secondaryAxisOrient=secondAxisOrientation, zeroScaleOrient=True, children=True)
        
        # Mirror the module node joints (for the mirrored module) if the module mirroring is enabled
        # and the current module to be created is a mirrored module on the -ve side of the creation plane,
        # and if the mirror rotation function is set to "Behaviour".
        if self.mirrorModule and self.mirrorRotationFunc == 'Behaviour':
            mirrorPlane = {'XY':False, 'YZ':False, 'XZ':False}
            mirrorPlane[self.onPlane] = True
            mirroredJoints = cmds.mirrorJoint(self.nodeJoints[0], mirrorXY=mirrorPlane['XY'], mirrorYZ=mirrorPlane['YZ'],
                                                                        mirrorXZ=mirrorPlane['XZ'], mirrorBehavior=True)
            cmds.delete(self.nodeJoints[0])
            self.nodeJoints = []
            for joint in mirroredJoints:
                newJoint = cmds.rename(joint, self.moduleNamespace+':'+joint)
                self.nodeJoints.append(newJoint)
                
        # Orient the end joint node.
        cmds.setAttr(self.nodeJoints[-1]+'.jointOrientX', 0)
        cmds.setAttr(self.nodeJoints[-1]+'.jointOrientY', 0)
        cmds.setAttr(self.nodeJoints[-1]+'.jointOrientZ', 0)
        
        # Clear selection after joint orientation.
        cmds.select(clear=True)
        
        # Create the IK handle to drive the module nodes.
        ikNodes = cmds.ikHandle(startJoint=self.nodeJoints[0], endEffector=self.nodeJoints[-1],
                                                    name=self.moduleNamespace+':rootToEndNode_ikHandle', solver='ikRPsolver')
        ikEffector = cmds.rename(ikNodes[1], self.moduleNamespace+':rootToEndNode_ikEffector')
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

        cmds.setAttr(rootHandle[0]+'.rotateX', keyable=False)
        cmds.setAttr(rootHandle[0]+'.rotateY', keyable=False)
        cmds.setAttr(rootHandle[0]+'.rotateZ', keyable=False)
        cmds.setAttr(rootHandle[0]+'.scaleX', keyable=False)
        cmds.setAttr(rootHandle[0]+'.scaleY', keyable=False)
        cmds.setAttr(rootHandle[0]+'.scaleZ', keyable=False)
        cmds.setAttr(rootHandle[0]+'.visibility', keyable=False)
        cmds.xform(rootHandle[0], worldSpace=True, absolute=True, translation=self.initNodePos[0])
        rootHandleConstraint = cmds.pointConstraint(rootHandle[0], self.nodeJoints[0], maintainOffset=False,
                                                                    name=self.nodeJoints[0]+'_pointConstraint')
        cmds.parent(rootHandle[0], self.moduleIKnodesGrp, absolute=True)

        # Mid hinge or elbow node handle.
        elbowHandle = objects.createRawControlSurface(self.nodeJoints[1], self.modHandleColour, True)

        cmds.setAttr(elbowHandle[0]+'.rotateX', keyable=False)
        cmds.setAttr(elbowHandle[0]+'.rotateY', keyable=False)
        cmds.setAttr(elbowHandle[0]+'.rotateZ', keyable=False)
        cmds.setAttr(elbowHandle[0]+'.scaleX', keyable=False)
        cmds.setAttr(elbowHandle[0]+'.scaleY', keyable=False)
        cmds.setAttr(elbowHandle[0]+'.scaleZ', keyable=False)
        cmds.setAttr(elbowHandle[0]+'.visibility', keyable=False)
        cmds.xform(elbowHandle[0], worldSpace=True, absolute=True, translation=self.initNodePos[1])
        elbowHandleConstraint = cmds.poleVectorConstraint(elbowHandle[0], ikHandle, name=ikHandle+'_poleVectorConstraint')
        cmds.parent(elbowHandle[0], self.moduleIKnodesGrp, absolute=True)

        # End node handle.
        endHandle = objects.createRawControlSurface(self.nodeJoints[-1], self.modHandleColour, True)

        cmds.setAttr(endHandle[0]+'.rotateX', keyable=False)
        cmds.setAttr(endHandle[0]+'.rotateY', keyable=False)
        cmds.setAttr(endHandle[0]+'.rotateZ', keyable=False)
        cmds.setAttr(endHandle[0]+'.scaleX', keyable=False)
        cmds.setAttr(endHandle[0]+'.scaleY', keyable=False)
        cmds.setAttr(endHandle[0]+'.scaleZ', keyable=False)
        cmds.setAttr(endHandle[0]+'.visibility', keyable=False)
        cmds.xform(endHandle[0], worldSpace=True, absolute=True, translation=self.initNodePos[2])
        endHandleConstraint = cmds.pointConstraint(endHandle[0], ikHandle, maintainOffset=False, name=ikHandle+'_pointConstraint')
        cmds.parent(endHandle[0], self.moduleIKnodesGrp, absolute=True)
        
        # Use the node handle objects to drive the axial distance for the node joints.
        for startPos, endPos, drivenJoint in [(rootHandle[0], elbowHandle[0], self.nodeJoints[1]),
                                              (elbowHandle[0], endHandle[0], self.nodeJoints[2])]:
                                              
            # Create a distance node to measure the distance between two joint handles, and connect
            # the worldSpace translate values.
            segmentDistance = cmds.createNode('distanceBetween', name=drivenJoint+'_distanceNode')
            cmds.connectAttr(startPos+'.translate', segmentDistance+'.point1')
            cmds.connectAttr(endPos+'.translate', segmentDistance+'.point2')
            
            # Get the aim axis, the axis down the module node chain.
            aimAxis = self.nodeAxes[0]
            
            # Get the distance factor to multiply the original length of the node joint length.
            distanceDivideFactor = cmds.createNode('multiplyDivide', name=drivenJoint+'_distanceDivideFactor')
            cmds.setAttr(distanceDivideFactor + '.operation', 2)
            originalLength = cmds.getAttr(drivenJoint+'.translate'+aimAxis)
            cmds.connectAttr(segmentDistance+'.distance', distanceDivideFactor+'.input1'+aimAxis)
            cmds.setAttr(distanceDivideFactor+'.input2'+aimAxis, originalLength)
            
            # Finally, drive the position of node joints using the multiplied distance.
            drivenJointAimTranslateMultiply = cmds.createNode('multiplyDivide', name=drivenJoint+'_drivenJointAimTranslateMultiply')
            cmds.connectAttr(distanceDivideFactor+'.output'+aimAxis, drivenJointAimTranslateMultiply+'.input1'+aimAxis)
            cmds.setAttr(drivenJointAimTranslateMultiply+'.input2'+aimAxis, math.fabs(originalLength))
            cmds.connectAttr(drivenJointAimTranslateMultiply+'.output'+aimAxis, drivenJoint+'.translate'+aimAxis)
            containedNodes.extend([segmentDistance, distanceDivideFactor, drivenJointAimTranslateMultiply])
            
        mfunc.updateAllTransforms()
        
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
            containedNodes.extend(clusterNodes)
            
            # Additionally, create a world position locator for the node joint.
            worldPosLocator = cmds.createNode('locator', parent=joint, name=joint+'_worldPosLocator')
            cmds.setAttr(worldPosLocator + '.visibility', 0)
            
            
        # Create the segment curves between the control handle shapes.
        for j, joint in enumerate(self.nodeJoints):
            if joint == self.nodeJoints[-1]:
                break
            
            # Create the raw segment parts (between two consecutive nodes).
            handleSegmentParts = objects.createRawSegmentCurve(self.modHandleColour)
            extra_nodes = []
            
            # Rename the parts.
            for node in handleSegmentParts[4]:
                if cmds.objExists(node):
                    extra_nodes.append(cmds.rename(node, '%s:%s_clusterParts_%s' \
                                                    % (self.moduleNamespace, mfunc.stripMRTNamespace(joint)[1], node)))
            containedNodes.extend(extra_nodes)
            
            # Connect the segment between two consecutive nodes with their control handle surfaces.
            startClosestPointOnSurface = cmds.createNode('closestPointOnSurface', name='%s_%s_closestPointOnSurface' \
                                                                                        % (joint, handleSegmentParts[5]))

            cmds.connectAttr(joint+'_controlShape.worldSpace[0]', startClosestPointOnSurface+'.inputSurface')
            cmds.connectAttr(self.nodeJoints[j+1]+'_worldPosLocator.worldPosition', startClosestPointOnSurface+'.inPosition')
            cmds.connectAttr(startClosestPointOnSurface+'.position', handleSegmentParts[5]+'.translate')
            endClosestPointOnSurface = cmds.createNode('closestPointOnSurface', name='%s_%s_closestPointOnSurface' \
                                                                        % (self.nodeJoints[j+1], handleSegmentParts[6]))

            cmds.connectAttr(self.nodeJoints[j+1]+'_controlShape.worldSpace[0]', endClosestPointOnSurface+'.inputSurface')
            cmds.connectAttr(joint+'_worldPosLocator.worldPosition', endClosestPointOnSurface+'.inPosition')
            cmds.connectAttr(endClosestPointOnSurface+'.position', handleSegmentParts[6]+'.translate')
            
            # Parent the segment curve parts under "moduleHandleSegmentCurveGrp".
            cmds.parent([handleSegmentParts[1], handleSegmentParts[2][1], handleSegmentParts[3][1], handleSegmentParts[5],
                                                        handleSegmentParts[6]], self.moduleHandleSegmentGrp, absolute=True)
            
            # Rename the segment curve.
            cmds.rename(handleSegmentParts[1], '%s:%s_%s' \
                                                % (self.moduleNamespace, mfunc.stripMRTNamespace(joint)[1], handleSegmentParts[1]))
            
            # Rename the segment curve start/end position locators.
            # The start and end description here is the current and the next node, between
            # which the segment curve is connected.             
            cmds.rename(handleSegmentParts[5], '%s_%s' % (joint, handleSegmentParts[5]))
            cmds.rename(handleSegmentParts[6], '%s_%s' % (self.nodeJoints[j+1], handleSegmentParts[6]))
            
            # Rename the cluster handles for start and end positions (clusters for their control handle shapes).
            startClusterHandle = cmds.rename(handleSegmentParts[2][1], '%s:%s_%s' \
                                                                            % (self.moduleNamespace, 
                                                                               mfunc.stripMRTNamespace(joint)[1], 
                                                                               handleSegmentParts[2][1]))
                                                                               
            endClusterHandle = cmds.rename(handleSegmentParts[3][1], '%s:%s_%s' \
                                                                            % (self.moduleNamespace, 
                                                                               mfunc.stripMRTNamespace(self.nodeJoints[j+1])[1], 
                                                                               handleSegmentParts[3][1]))
                                                                               
            # Rename the constraints for the cluster handles (from the start and end position locators).                                  
            cmds.rename('%s|%s' % (startClusterHandle, handleSegmentParts[7].rpartition('|')[2]), 
                                    '%s_%s' % (joint, handleSegmentParts[7].rpartition('|')[2]))
                                    
            cmds.rename('%s|%s' % (endClusterHandle, handleSegmentParts[8].rpartition('|')[2]), 
                                    '%s_%s' % (self.nodeJoints[j+1], handleSegmentParts[8].rpartition('|')[2]))
            
            # Rename the groupParts for the start and end clusters.
            startClusterGrpParts = cmds.rename('segmentCurve_startClusterGroupParts', startClusterHandle+'_clusterGroupParts')
            endClusterGrpParts = cmds.rename('segmentCurve_endClusterGroupParts', endClusterHandle+'_clusterGroupParts')
            
            # Attach an arclen to measure the length of the segment curve.
            arclen = cmds.arclen(joint+'_segmentCurve', constructionHistory=True)
            namedArclen = cmds.rename(arclen, joint+'_segmentCurve_curveInfo')

            cmds.select(clear=True)
            
            # Add the created nodes to the module container.
            containedNodes.extend([startClusterHandle, endClusterHandle, startClusterHandle+'Cluster', 
                                   endClusterHandle+'Cluster', startClosestPointOnSurface, endClosestPointOnSurface, 
                                   namedArclen, startClusterGrpParts, endClusterGrpParts])
        
        # Create a segment curve between the root and the end node.
        rootEndHandleSegmentParts = objects.createRawSegmentCurve(3)
        extra_nodes = []
        for node in rootEndHandleSegmentParts[4]:
            if cmds.objExists(node):
                extra_nodes.append(cmds.rename(node, self.moduleNamespace+':'+'rootEndHandleIKsegment_clusterParts_'+node))
        containedNodes.extend(extra_nodes)
        
        # Connect the start and end segment position locators to the node control handle surfaces.
        startClosestPointOnSurface = cmds.createNode('closestPointOnSurface', name='%s:startHandleIKsegment_%s_closestPointOnSurface' \
                                                                                    % (self.moduleNamespace,
                                                                                       rootEndHandleSegmentParts[5]))
                                                                                       
        cmds.connectAttr(self.nodeJoints[0]+'_controlShape.worldSpace[0]', startClosestPointOnSurface+'.inputSurface')
        cmds.connectAttr(self.nodeJoints[-1]+'_worldPosLocator.worldPosition', startClosestPointOnSurface+'.inPosition')
        cmds.connectAttr(startClosestPointOnSurface+'.position', rootEndHandleSegmentParts[5]+'.translate')
        
        endClosestPointOnSurface = cmds.createNode('closestPointOnSurface', name='%s:endHandleIKsegment_%s_closestPointOnSurface' \
                                                                                   % (self.moduleNamespace,
                                                                                      rootEndHandleSegmentParts[6]))
                                                                                      
        cmds.connectAttr(self.nodeJoints[-1]+'_controlShape.worldSpace[0]', endClosestPointOnSurface+'.inputSurface')
        cmds.connectAttr(self.nodeJoints[0]+'_worldPosLocator.worldPosition', endClosestPointOnSurface+'.inPosition')
        cmds.connectAttr(endClosestPointOnSurface+'.position', rootEndHandleSegmentParts[6]+'.translate')

        cmds.parent([rootEndHandleSegmentParts[1], rootEndHandleSegmentParts[2][1], rootEndHandleSegmentParts[3][1], 
                     rootEndHandleSegmentParts[5], rootEndHandleSegmentParts[6]], self.moduleHandleSegmentGrp, absolute=True)
        
        # Rename the root-end segment curve.
        rootEndHandleIKsegmentCurve = cmds.rename(rootEndHandleSegmentParts[1], '%s:rootEndHandleIKsegment_%s' \
                                                                                  % (self.moduleNamespace,
                                                                                     rootEndHandleSegmentParts[1]))
        # Rename the root-end segment curve start/end position locators.
        newStartLocator = cmds.rename(rootEndHandleSegmentParts[5], '%s:startHandleIKsegment_%s' \
                                                                      % (self.moduleNamespace,
                                                                         rootEndHandleSegmentParts[5]))
                                                                         
        newEndLocator = cmds.rename(rootEndHandleSegmentParts[6], '%s:endHandleIKsegment_%s' \
                                                                      % (self.moduleNamespace,
                                                                         rootEndHandleSegmentParts[6]))
                                                                         
        # Rename the cluster handles for start and end positions (clusters for their control handle shapes).
        startClusterHandle = cmds.rename(rootEndHandleSegmentParts[2][1], '%s:startHandleIKsegment_%s' \
                                                                            % (self.moduleNamespace,
                                                                               rootEndHandleSegmentParts[2][1]))
                                                                               
        endClusterHandle = cmds.rename(rootEndHandleSegmentParts[3][1], '%s:endHandleIKsegment_%s' \
                                                                          % (self.moduleNamespace,
                                                                             rootEndHandleSegmentParts[3][1]))
        
        # Rename the constraints for the cluster handles (from the start and end position locators).      
        cmds.rename('%s|%s' % (startClusterHandle, rootEndHandleSegmentParts[7].rpartition('|')[2]),
                    '%s:startHandleIKsegment_%s' % (self.moduleNamespace, rootEndHandleSegmentParts[7].rpartition('|')[2]))
        cmds.rename('%s|%s' % (endClusterHandle, rootEndHandleSegmentParts[8].rpartition('|')[2]), 
                    '%s:endHandleIKsegment_%s' % (self.moduleNamespace, rootEndHandleSegmentParts[8].rpartition('|')[2]))
        
        # Rename the groupParts for the start and end clusters.
        startClusterGrpParts = cmds.rename('segmentCurve_startClusterGroupParts', startClusterHandle+'_clusterGroupParts')
        endClusterGrpParts = cmds.rename('segmentCurve_endClusterGroupParts', endClusterHandle+'_clusterGroupParts')

        cmds.select(clear=True)
        
        # Add the created nodes to the module container.
        containedNodes.extend([startClusterHandle, endClusterHandle, startClusterHandle+'Cluster', 
                               endClusterHandle+'Cluster', startClosestPointOnSurface, endClosestPointOnSurface, 
                               startClusterGrpParts, endClusterGrpParts])
        
        # Create a locator attached at the mid position on the root-end segment curve.
        # This locator will be used to visually identify the mid position of the IK chain,
        # represented here by the hinge module nodes. 
        rootEndHandleIKsegmentMidLocator = cmds.spaceLocator(name='%s:rootEndHandleIKsegmentMidLocator' \
                                                                    % self.moduleNamespace)[0]
        cmds.setAttr(rootEndHandleIKsegmentMidLocator+'.translateX', keyable=False)
        cmds.setAttr(rootEndHandleIKsegmentMidLocator+'.translateY', keyable=False)
        cmds.setAttr(rootEndHandleIKsegmentMidLocator+'.translateZ', keyable=False)
        cmds.setAttr(rootEndHandleIKsegmentMidLocator+'.rotateX', keyable=False)
        cmds.setAttr(rootEndHandleIKsegmentMidLocator+'.rotateY', keyable=False)
        cmds.setAttr(rootEndHandleIKsegmentMidLocator+'.rotateZ', keyable=False)
        cmds.setAttr(rootEndHandleIKsegmentMidLocator+'.scaleX', keyable=False)
        cmds.setAttr(rootEndHandleIKsegmentMidLocator+'.scaleY', keyable=False)
        cmds.setAttr(rootEndHandleIKsegmentMidLocator+'.scaleZ', keyable=False)
        cmds.setAttr(rootEndHandleIKsegmentMidLocator+'.visibility', keyable=False)

        cmds.parent(rootEndHandleIKsegmentMidLocator, self.moduleIKsegmentMidAimGrp, absolute=True)
        
        # Attach the IK segment mid position locator on the start-end segment curve.
        rootEndHandleIKsegmentMidLocator_pointOnCurveInfo = \
            cmds.createNode('pointOnCurveInfo', name='%s:rootEndHandleIKsegmentCurveMidLocator_pointOnCurveInfo' \
                                                        % self.moduleNamespace)
                                                        
        cmds.connectAttr(rootEndHandleIKsegmentCurve+'Shape.worldSpace[0]', 
                         rootEndHandleIKsegmentMidLocator_pointOnCurveInfo+'.inputCurve')
                         
        cmds.setAttr(rootEndHandleIKsegmentMidLocator_pointOnCurveInfo+'.turnOnPercentage', True)
        cmds.setAttr(rootEndHandleIKsegmentMidLocator_pointOnCurveInfo+'.parameter', 0.5)
        cmds.connectAttr(rootEndHandleIKsegmentMidLocator_pointOnCurveInfo+'.position', 
                                            rootEndHandleIKsegmentMidLocator+'.translate')
        containedNodes.append(rootEndHandleIKsegmentMidLocator_pointOnCurveInfo)
        
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
        
        # The start position of the curve should slide on the root-end segment curve.
        ikSegmentAimStartLocator = cmds.spaceLocator(name=self.moduleNamespace+':ikSegmentAimStartLocator')[0]
        cmds.setAttr(ikSegmentAimStartLocator+'.visibility', 0)
        
        cmds.parent(ikSegmentAimStartLocator, self.moduleIKsegmentMidAimGrp, absolute=True)
        
        cmds.geometryConstraint(rootEndHandleIKsegmentCurve, ikSegmentAimStartLocator, 
                                        name=ikSegmentAimStartLocator+'_geoConstraint')
                                        
        cmds.pointConstraint(self.nodeJoints[1]+'_control', ikSegmentAimStartLocator, 
                                maintainOffset=False, name=ikSegmentAimStartLocator+'_pointConstraint')
                                
        ikSegmentAimStartClosestPointOnSurface = cmds.createNode('closestPointOnSurface', 
                                name=self.moduleNamespace+':ikSegmentAimClosestPointOnSurface')
                                
        cmds.connectAttr(self.nodeJoints[1]+'_controlShape.worldSpace[0]', 
                                        ikSegmentAimStartClosestPointOnSurface+'.inputSurface')
                                        
        cmds.connectAttr(ikSegmentAimStartLocator+'Shape.worldPosition[0]', 
                                        ikSegmentAimStartClosestPointOnSurface+'.inPosition')
        
        ikSegmentAimEndLocator = cmds.spaceLocator(name=self.moduleNamespace+':ikSegmentAimEndLocator')[0]
        cmds.setAttr(ikSegmentAimEndLocator+'.visibility', 0)
        cmds.parent(ikSegmentAimEndLocator, self.moduleIKsegmentMidAimGrp, absolute=True)
        
        cmds.connectAttr(ikSegmentAimStartClosestPointOnSurface+'.position', ikSegmentAimEndLocator+'.translate')
        
        containedNodes.append(ikSegmentAimStartClosestPointOnSurface)

        ikSegmentAimCurve = cmds.createNode('transform', name=self.moduleNamespace+':ikSegmentAimCurve')
        cmds.setAttr(ikSegmentAimCurve+'.translateX', keyable=False)
        cmds.setAttr(ikSegmentAimCurve+'.translateY', keyable=False)
        cmds.setAttr(ikSegmentAimCurve+'.translateZ', keyable=False)
        cmds.setAttr(ikSegmentAimCurve+'.rotateX', keyable=False)
        cmds.setAttr(ikSegmentAimCurve+'.rotateY', keyable=False)
        cmds.setAttr(ikSegmentAimCurve+'.rotateZ', keyable=False)
        cmds.setAttr(ikSegmentAimCurve+'.scaleX', keyable=False)
        cmds.setAttr(ikSegmentAimCurve+'.scaleY', keyable=False)
        cmds.setAttr(ikSegmentAimCurve+'.scaleZ', keyable=False)
        cmds.setAttr(ikSegmentAimCurve+'.visibility', keyable=False)
        cmds.createNode('nurbsCurve', name=self.moduleNamespace+':ikSegmentAimCurveShape', parent=ikSegmentAimCurve)
        cmds.setAttr('.overrideEnabled', 1)
        cmds.setAttr('.overrideColor', 2)
        mel.eval('''setAttr ".cached" -type "nurbsCurve"
        1 1 0 no 3
        2 0 1
        2
        0 0 0
        1 0 0;''')
        cmds.parent(ikSegmentAimCurve, self.moduleIKsegmentMidAimGrp, absolute=True)

        cmds.pointConstraint(ikSegmentAimStartLocator, ikSegmentAimCurve, maintainOffset=False, 
                                                        name=ikSegmentAimCurve+'_pointConstraint')
        cmds.aimConstraint(ikSegmentAimEndLocator, ikSegmentAimCurve, maintainOffset=False, aimVector=[1.0, 0.0, 0.0], 
                                upVector=[0.0, 1.0, 0.0], worldUpType='scene', name=ikSegmentAimCurve+'_aimConstraint')

        rootEndHandleIKsegmentMidLocatorAimConstraint = \
            cmds.aimConstraint(self.nodeJoints[-1], rootEndHandleIKsegmentMidLocator, maintainOffset=False, 
                               aimVector=[0.0, 1.0, 0.0], upVector=[0.0, 0.0, 1.0], worldUpType='object', 
                               worldUpObject=ikSegmentAimEndLocator, name=rootEndHandleIKsegmentMidLocator+'_aimConstraint')[0]
                               
        cmds.setAttr(rootEndHandleIKsegmentMidLocatorAimConstraint+'.offsetY', 45)

        ikSegmentAimCurveLength_distance = cmds.createNode('distanceBetween', 
                                                            name=self.moduleNamespace+':ikSegmentAimCurveLength_distanceNode')
        cmds.connectAttr(ikSegmentAimStartLocator+'Shape.worldPosition[0]', ikSegmentAimCurveLength_distance+'.point1')
        cmds.connectAttr(ikSegmentAimEndLocator+'Shape.worldPosition[0]', ikSegmentAimCurveLength_distance+'.point2')
        cmds.connectAttr(ikSegmentAimCurveLength_distance+'.distance', ikSegmentAimCurve+'.scaleX')
        containedNodes.append(ikSegmentAimCurveLength_distance)

        # Add the module transform to the module, at the position of the root node.
        moduleTransform = objects.load_xhandleShape(self.moduleNamespace+'_handle', 24, True)
        cmds.setAttr(moduleTransform[0]+'.localScaleX', 0.26)
        cmds.setAttr(moduleTransform[0]+'.localScaleY', 0.26)
        cmds.setAttr(moduleTransform[0]+'.localScaleZ', 0.26)
        cmds.setAttr(moduleTransform[0]+'.drawStyle', 8)
        cmds.setAttr(moduleTransform[0]+'.drawOrtho', 0)
        cmds.setAttr(moduleTransform[0]+'.wireframeThickness', 2)
        cmds.setAttr(moduleTransform[1]+'.scaleX', keyable=False)
        cmds.setAttr(moduleTransform[1]+'.scaleY', keyable=False)
        cmds.setAttr(moduleTransform[1]+'.scaleZ', keyable=False)
        cmds.setAttr(moduleTransform[1]+'.visibility', keyable=False)
        cmds.addAttr(moduleTransform[1], attributeType='float', longName='globalScale', 
                                        hasMinValue=True, minValue=0, defaultValue=1, keyable=True)
        self.moduleTransform = cmds.rename(moduleTransform[1], self.moduleNamespace+':module_transform')
        tempConstraint = cmds.pointConstraint(self.nodeJoints[0], self.moduleTransform, maintainOffset=False)
        cmds.delete(tempConstraint)

        cmds.parent(self.moduleTransform, self.moduleGrp, absolute=True)
        cmds.parentConstraint(self.moduleTransform, self.moduleIKnodesGrp, maintainOffset=True, 
                                                            name=self.moduleTransform+'_parentConstraint')
        cmds.scaleConstraint(self.moduleTransform, self.moduleIKnodesGrp, maintainOffset=False, 
                                                        name=self.moduleTransform+'_scaleConstraint')
        cmds.scaleConstraint(self.moduleTransform, self.moduleJointsGrp, maintainOffset=False, 
                                                    name=self.moduleTransform+'_scaleConstraint')
        cmds.scaleConstraint(self.moduleTransform, rootEndHandleIKsegmentMidLocator, maintainOffset=False, 
                                                name=self.moduleTransform+'_scaleConstraint')

        # Connect the scale attributes to an aliased 'globalScale' attribute.
        # (This could've been done on the raw def itself, but it was issuing a cycle; not sure why. 
        # But the DG eval was not cyclic).
        cmds.connectAttr(self.moduleTransform+'.globalScale', self.moduleTransform+'.scaleX')
        cmds.connectAttr(self.moduleTransform+'.globalScale', self.moduleTransform+'.scaleY')
        cmds.connectAttr(self.moduleTransform+'.globalScale', self.moduleTransform+'.scaleZ')

        # Connect the globalScale attribute of the module transform to the 
        # control handles for the module nodes.
        for handle in [rootHandle[0], elbowHandle[0], endHandle[0]]:
            xhandle = objects.load_xhandleShape(handle+'X', self.modHandleColour, True)
            cmds.setAttr(xhandle[0]+'.localScaleX', 0.089)
            cmds.setAttr(xhandle[0]+'.localScaleY', 0.089)
            cmds.setAttr(xhandle[0]+'.localScaleZ', 0.089)
            cmds.parent(xhandle[0], handle, shape=True, relative=True)
            cmds.delete(xhandle[1])
            cmds.setAttr(xhandle[0]+'.ds', 5)
            cmds.setAttr(handle+'Shape.visibility', 0)
        
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
                                                        self.moduleNamespace+':'+ikPreferredRotationRepresentaton)
        cmds.parent(ikPreferredRotationRepresentaton, self.moduleReprGrp, absolute=True)
        cmds.pointConstraint(self.moduleNamespace+':rootEndHandleIKsegmentMidLocator', 
                                    ikPreferredRotationRepresentaton, maintainOffset=False, 
                                            name=ikPreferredRotationRepresentaton+'_pointConstraint')
        cmds.scaleConstraint(self.moduleTransform, ikPreferredRotationRepresentaton, maintainOffset=False, 
                                name=self.moduleTransform+'_ikPreferredRotRepr_scaleConstraint')
        orientConstraint = cmds.orientConstraint(self.moduleNamespace+':rootEndHandleIKsegmentMidLocator', 
                                                    ikPreferredRotationRepresentaton, maintainOffset=False, 
                                                        name=ikPreferredRotationRepresentaton+'_orientConstraint')[0]
        cmds.setAttr(orientConstraint+'.offsetY', -45)
        
        # Add hierarchy representations between the module nodes.
        for index, joint in enumerate(self.nodeJoints[:-1]):

            hierarchyRepr = objects.createRawHierarchyRepresentation(self.nodeAxes[0])

            startLocator = joint + '_segmentCurve_startLocator'
            endLocator = self.nodeJoints[index+1] + '_segmentCurve_endLocator'
            cmds.pointConstraint(startLocator, endLocator, hierarchyRepr, maintainOffset=False, name=joint+'_hierarchy_repr_pointConstraint')
            cmds.scaleConstraint(joint, hierarchyRepr, maintainOffset=False, name=joint+'_hierarchy_repr_scaleConstraint')

            aimVector = {'X':[1.0, 0.0, 0.0], 'Y':[0.0, 1.0, 0.0], 'Z':[0.0, 0.0, 1.0]}[self.nodeAxes[0]]
            upVector = {'X':[1.0, 0.0, 0.0], 'Y':[0.0, 1.0, 0.0], 'Z':[0.0, 0.0, 1.0]}[self.nodeAxes[1]]
            cmds.aimConstraint(self.nodeJoints[index+1], hierarchyRepr, maintainOffset=False, aimVector=aimVector, upVector=upVector, worldUpVector=upVector, worldUpType='objectRotation', worldUpObject=joint, name=self.moduleNamespace+':'+mfunc.stripMRTNamespace(self.nodeJoints[index+1])[1]+'_hierarchy_repr_aimConstraint')

            cmds.parent(hierarchyRepr, self.moduleHierarchyReprGrp, absolute=True)

            cmds.rename(hierarchyRepr, joint+'_'+hierarchyRepr)


        cmds.select(clear=True)
        
        # Create module parenting representation objects.
        containedNodes += self.createHierarchySegmentForModuleParentingRepr()
        
        # Create the proxy geometry for the module if enabled.
        if self.proxyGeoStatus:
            if self.proxyGeoElbow:
                self.createProxyGeo_elbows(self.proxyElbowType)
            if self.proxyGeoBones:
                self.createProxyGeo_bones()

        # Add the module group to the contained nodes list.
        containedNodes += [self.moduleGrp]
        
        # Add the contained nodes to the module container.
        mfunc.addNodesToContainer(self.moduleContainer, containedNodes, includeHierarchyBelow=True, includeShapes=True)
        
        # Publish the module transform attributes for the module container.
        moduleTransformName = mfunc.stripMRTNamespace(self.moduleTransform)[1]
        cmds.container(self.moduleContainer, edit=True, publishAndBind=[self.moduleTransform+'.translate', 
                                                                        moduleTransformName+'_translate'])
        cmds.container(self.moduleContainer, edit=True, publishAndBind=[self.moduleTransform+'.rotate', 
                                                                        moduleTransformName+'_rotate'])
        cmds.container(self.moduleContainer, edit=True, publishAndBind=[self.moduleTransform+'.globalScale', 
                                                                        moduleTransformName+'_globalScale'])
        
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
            offset = cmds.getAttr(self.moduleNamespace+':node_1_transform_control.translateY')
            cmds.setAttr(self.moduleNamespace+':node_1_transform_control.translateY', 0)
            cmds.setAttr(self.moduleNamespace+':node_1_transform_control.translateZ', offset)
        if self.onPlane == 'XY' and self.mirrorModule:
            offset = cmds.getAttr(self.moduleNamespace+':node_1_transform_control.translateZ')
            cmds.setAttr(self.moduleNamespace+':node_1_transform_control.translateZ', offset*-1)
        if self.onPlane == 'YZ' and self.mirrorModule:
            offset = cmds.getAttr(self.moduleNamespace+':node_1_transform_control.translateX')
            cmds.setAttr(self.moduleNamespace+':node_1_transform_control.translateX', offset*-1)


    def checkPlaneAxisDirectionForIKhingeForOrientationRepr(self):
        offsetAxisVectorTransforms = {'XY':[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]], 
                                      'YZ':[[0.0, 0.0, 0.0], [0.0, 0.0, 1.0]], 
                                      'XZ':[[0.0, 0.0, 0.0], [0.0, 0.0, 1.0]]}[self.onPlane]
        planeAxisOffset = {'X':[1.0, 0.0, 0.0], 'Y':[0.0, 1.0, 0.0], 'Z':[0.0, 0.0, 1.0]}
        IKhingePlaneAxisVectorTransforms = []
        tempLocatorForWorldTransformInfo_IKhingeOrientationVector = cmds.spaceLocator()[0]
        tempConstraint = cmds.parentConstraint(self.nodeJoints[1], tempLocatorForWorldTransformInfo_IKhingeOrientationVector, maintainOffset=False)
        cmds.delete(tempConstraint)
        cmds.parent(tempLocatorForWorldTransformInfo_IKhingeOrientationVector, self.nodeJoints[1])
        IKhingePlaneAxisVectorTransforms.append(cmds.xform(tempLocatorForWorldTransformInfo_IKhingeOrientationVector, query=True, worldSpace=True, translation=True))
        cmds.xform(tempLocatorForWorldTransformInfo_IKhingeOrientationVector, objectSpace=True, relative=True, translation=planeAxisOffset[self.nodeAxes[2]])
        IKhingePlaneAxisVectorTransforms.append(cmds.xform(tempLocatorForWorldTransformInfo_IKhingeOrientationVector, query=True, worldSpace=True, translation=True))
        cmds.delete(tempLocatorForWorldTransformInfo_IKhingeOrientationVector)

        direction_cosine = mfunc.returnDotProductDirection(offsetAxisVectorTransforms[0], offsetAxisVectorTransforms[1], IKhingePlaneAxisVectorTransforms[0], IKhingePlaneAxisVectorTransforms[1])[0]

        hingePreferredOrientationReprAffectDueToIKRotation_directionCheck = {'XY':1.0, 'YZ':-1.0, 'XZ':1.0}[self.onPlane]

        if hingePreferredOrientationReprAffectDueToIKRotation_directionCheck == direction_cosine:
            return True
        else:
            return False

            
    def addCustomAttributesOnModuleTransform(self):
        if self.moduleName == 'JointNode':

            moduleNode = '|' + self.moduleGrp + '|' + self.moduleTransform

            if len(self.nodeJoints) > 1:
                cmds.addAttr(moduleNode, attributeType='enum', longName='Node_Orientation_Repr_Toggle', enumName=' ')
                cmds.setAttr(moduleNode+'.Node_Orientation_Repr_Toggle', keyable=False, channelBox=True)
                
                for joint in self.nodeJoints[:-1]:
                    longName = mfunc.stripMRTNamespace(joint)[1]+'_orient_repr_transform'
                    cmds.addAttr(moduleNode, attributeType='enum', longName=longName, enumName='Off:On:', defaultValue=1, keyable=True)
                    cmds.connectAttr(moduleNode+'.'+longName, joint+'_orient_repr_transform.visibility')
                    if not self.showOrientation:
                        cmds.setAttr(moduleNode+'.'+longName, 0)
                    cmds.container(self.moduleContainer, edit=True, publishAndBind=[moduleNode+'.'+longName, 'module_transform_'+longName+'_toggle'])

                cmds.addAttr(moduleNode, attributeType='enum', longName='Node_Hierarchy_Repr_Toggle', enumName=' ')
                cmds.setAttr(moduleNode+'.Node_Hierarchy_Repr_Toggle', keyable=False, channelBox=True)
                
                for joint in self.nodeJoints[:-1]:
                    longName = mfunc.stripMRTNamespace(joint)[1]+'_hierarchy_repr'
                    cmds.addAttr(moduleNode, attributeType='enum', longName=longName, enumName='Off:On:', defaultValue=1, keyable=True)
                    cmds.connectAttr(moduleNode+'.'+longName, joint+'_hierarchy_repr.visibility')
                    ##cmds.connectAttr(moduleNode+'.'+longName, joint+'_handleControlSegmentCurve.visibility')
                    cmds.connectAttr(moduleNode+'.'+longName, joint+'_segmentCurve.visibility')
                    if not self.showHierarchy:
                        cmds.setAttr(moduleNode+'.'+longName, 0)
                    cmds.container(self.moduleContainer, edit=True, publishAndBind=[moduleNode+'.'+longName, 'module_transform_'+longName+'_toggle'])

            if len(self.nodeJoints) == 1:
                cmds.addAttr(moduleNode, attributeType='enum', longName='Node_Orientation_Repr_Toggle', enumName=' ')
                cmds.setAttr(moduleNode+'.Node_Orientation_Repr_Toggle', keyable=False, channelBox=True)
                
                longName = mfunc.stripMRTNamespace(self.nodeJoints[0])[1]+'_single_orient_repr_transform'
                cmds.addAttr(moduleNode, attributeType='enum', longName=longName, enumName='Off:On:', defaultValue=1, keyable=True)
                cmds.connectAttr(moduleNode+'.'+longName, mfunc.stripMRTNamespace(self.nodeJoints[0])[0]+':single_orient_repr_transform.visibility')
                if not self.showOrientation:
                    cmds.setAttr(moduleNode+'.'+longName, 0)
                cmds.container(self.moduleContainer, edit=True, publishAndBind=[moduleNode+'.'+longName, 'module_transform_'+longName+'_toggle'])

            cmds.addAttr(moduleNode, attributeType='enum', longName='Node_Handle_Size', enumName=' ')
            cmds.setAttr(moduleNode+'.Node_Handle_Size', keyable=False, channelBox=True)
            
            for joint in self.nodeJoints:
                longName = mfunc.stripMRTNamespace(joint)[1]+'_handle_size'
                cmds.addAttr(moduleNode, attributeType='float', longName=longName, hasMinValue=True, minValue=0, defaultValue=1, keyable=True)
                cmds.connectAttr(moduleNode+'.'+longName, joint+'_controlShape_scaleClusterHandle.scaleX')
                cmds.connectAttr(moduleNode+'.'+longName, joint+'_controlShape_scaleClusterHandle.scaleY')
                cmds.connectAttr(moduleNode+'.'+longName, joint+'_controlShape_scaleClusterHandle.scaleZ')
                cmds.connectAttr(moduleNode+'.'+longName, joint+'Shape.addScaleX')
                cmds.connectAttr(moduleNode+'.'+longName, joint+'Shape.addScaleY')
                cmds.connectAttr(moduleNode+'.'+longName, joint+'Shape.addScaleZ')
                #cmds.setAttr(moduleNode+'.'+longName, 0.2)
                cmds.container(self.moduleContainer, edit=True, publishAndBind=[moduleNode+'.'+longName, 'module_transform_'+longName])

            cmds.addAttr(moduleNode, attributeType='enum', longName='Node_Rotation_Order', enumName=' ')
            cmds.setAttr(moduleNode+'.Node_Rotation_Order', keyable=False, channelBox=True)
            
            for joint in self.nodeJoints:
                longName = mfunc.stripMRTNamespace(joint)[1]+'_rotate_order'
                cmds.addAttr(moduleNode, attributeType='enum', longName=longName, enumName='xyz:yzx:zxy:xzy:yxz:zyx:', defaultValue=0, keyable=True)
                cmds.connectAttr(moduleNode+'.'+longName, joint+'.rotateOrder')
                cmds.container(self.moduleContainer, edit=True, publishAndBind=[moduleNode+'.'+longName, 'module_transform_'+longName+'_switch'])

            if self.proxyGeoStatus:
                cmds.addAttr(moduleNode, attributeType='enum', longName='Proxy_Geometry', enumName=' ')
                cmds.setAttr(moduleNode+'.Proxy_Geometry', keyable=False, channelBox=True)
                
                cmds.addAttr(moduleNode, attributeType='enum', longName='proxy_geometry_draw', enumName='Opaque:Transparent:', defaultValue=1, keyable=True)
                cmds.container(self.moduleContainer, edit=True, publishAndBind=[moduleNode+'.proxy_geometry_draw', 'module_transform_proxy_geometry_draw_toggle'])

        if self.moduleName == 'SplineNode':

            moduleNode = self.moduleNamespace + ':splineStartHandleTransform'

            cmds.addAttr(moduleNode, attributeType='enum', longName='Node_Repr', enumName=' ')
            cmds.setAttr(moduleNode+'.Node_Repr', keyable=False, channelBox=True)
            
            cmds.addAttr(moduleNode, attributeType='float', longName='Global_size', hasMinValue=True, minValue=0, defaultValue=1, keyable=True)
            cmds.addAttr(moduleNode, attributeType='float', longName='Axis_Rotate', defaultValue=0, keyable=True)
            cmds.addAttr(moduleNode, attributeType='enum', longName='Node_Orientation_Info', enumName='Off:On:', defaultValue=1, keyable=True)
            cmds.addAttr(moduleNode, attributeType='enum', longName='Node_Orientation_Type', enumName='World:Object:', defaultValue=1, keyable=True)
            cmds.addAttr(moduleNode, attributeType='float', longName='Node_Local_Orientation_Repr_Size', hasMinValue=True, minValue=0.01, defaultValue=1, keyable=True)
            cmds.container(self.moduleContainer, edit=True, publishAndBind=[moduleNode+'.Global_size', 'module_globalRepr_Size'])
            cmds.container(self.moduleContainer, edit=True, publishAndBind=[moduleNode+'.Axis_Rotate', 'module_Axis_Rotate'])
            cmds.container(self.moduleContainer, edit=True, publishAndBind=[moduleNode+'.Node_Orientation_Info', 'root_transform_Node_Orientation'])
            cmds.container(self.moduleContainer, edit=True, publishAndBind=[moduleNode+'.Node_Orientation_Type', 'root_transform_Node_Orientation_Type'])
            cmds.container(self.moduleContainer, edit=True, publishAndBind=[moduleNode+'.Node_Local_Orientation_Repr_Size', 'root_transform_Node_Orientation_Repr_Size'])

            if self.proxyGeoStatus:
                cmds.addAttr(moduleNode, attributeType='enum', longName='Proxy_Geometry', enumName=' ')
                cmds.setAttr(moduleNode+'.Proxy_Geometry', keyable=False, channelBox=True)
                
                cmds.addAttr(moduleNode, attributeType='enum', longName='proxy_geometry_draw', enumName='Opaque:Transparent:', defaultValue=1, keyable=True)
                cmds.container(self.moduleContainer, edit=True, publishAndBind=[moduleNode+'.proxy_geometry_draw', 'module_transform_proxy_geometry_draw_toggle'])

        if self.moduleName == 'HingeNode':

            moduleNode = '|' + self.moduleGrp + '|' + self.moduleTransform

            cmds.addAttr(moduleNode, attributeType='enum', longName='Hinge_Orientation_Repr_Toggle', enumName='Off:On:', defaultValue=1, keyable=True)
            cmds.connectAttr(moduleNode+'.Hinge_Orientation_Repr_Toggle', self.nodeJoints[1]+'_IKhingeAxisRepresenation.visibility')
            cmds.connectAttr(moduleNode+'.Hinge_Orientation_Repr_Toggle', self.moduleNamespace+':IKPreferredRotationRepr.visibility')
            cmds.container(self.moduleContainer, edit=True, publishAndBind=[moduleNode+'.Hinge_Orientation_Repr_Toggle', mfunc.stripMRTNamespace(self.nodeJoints[1])[1]+'_Hinge_Orientation_Repr_Toggle'])
            if not self.showOrientation:
                cmds.setAttr(moduleNode+'.Hinge_Orientation_Repr_Toggle', 0)

            cmds.addAttr(moduleNode, attributeType='enum', longName='Module_Hierarchy_Repr_Toggle', enumName='Off:On:', defaultValue=1, keyable=True)
            for joint in self.nodeJoints[:-1]:
                cmds.connectAttr(moduleNode+'.Module_Hierarchy_Repr_Toggle', joint+'_hierarchy_repr.visibility')
                cmds.connectAttr(moduleNode+'.Module_Hierarchy_Repr_Toggle', joint+'_segmentCurve.visibility')
            cmds.container(self.moduleContainer, edit=True, publishAndBind=[moduleNode+'.Module_Hierarchy_Repr_Toggle', 'Module_Hierarchy_Repr_Toggle'])
            if not self.showHierarchy:
                cmds.setAttr(moduleNode+'.Module_Hierarchy_Repr_Toggle', 0)

            cmds.addAttr(moduleNode, attributeType='enum', longName='Node_Handle_Size', enumName=' ')
            cmds.setAttr(moduleNode+'.Node_Handle_Size', keyable=False, channelBox=True)

            for joint in self.nodeJoints:
                longName = mfunc.stripMRTNamespace(joint)[1]+'_handle_size'
                cmds.addAttr(moduleNode, attributeType='float', longName=longName, hasMinValue=True, minValue=0, defaultValue=1, keyable=True)
                cmds.connectAttr(moduleNode+'.'+longName, joint+'_controlShape_scaleClusterHandle.scaleX')
                cmds.connectAttr(moduleNode+'.'+longName, joint+'_controlShape_scaleClusterHandle.scaleY')
                cmds.connectAttr(moduleNode+'.'+longName, joint+'_controlShape_scaleClusterHandle.scaleZ')
                cmds.connectAttr(moduleNode+'.'+longName, joint+'_controlXShape.addScaleX')
                cmds.connectAttr(moduleNode+'.'+longName, joint+'_controlXShape.addScaleY')
                cmds.connectAttr(moduleNode+'.'+longName, joint+'_controlXShape.addScaleZ')
                #cmds.setAttr(moduleNode+'.'+longName, 0.2)
                cmds.container(self.moduleContainer, edit=True, publishAndBind=[moduleNode+'.'+longName, 'module_transform_'+longName])

            cmds.addAttr(moduleNode, attributeType='enum', longName='Node_Rotation_Order', enumName=' ')
            cmds.setAttr(moduleNode+'.Node_Rotation_Order', keyable=False, channelBox=True)

            for joint in self.nodeJoints:
                longName = mfunc.stripMRTNamespace(joint)[1]+'_rotate_order'
                cmds.addAttr(moduleNode, attributeType='enum', longName=longName, enumName='xyz:yzx:zxy:xzy:yxz:zyx:', defaultValue=0, keyable=True)
                cmds.connectAttr(moduleNode+'.'+longName, joint+'.rotateOrder')
                cmds.container(self.moduleContainer, edit=True, publishAndBind=[moduleNode+'.'+longName, 'module_transform_'+longName+'_switch'])

            if self.proxyGeoStatus:
                cmds.addAttr(moduleNode, attributeType='enum', longName='Proxy_Geometry', enumName=' ')
                cmds.setAttr(moduleNode+'.Proxy_Geometry', keyable=False, channelBox=True)
                
                cmds.addAttr(moduleNode, attributeType='enum', longName='proxy_geometry_draw', enumName='Opaque:Transparent:', defaultValue=1, keyable=True)
                cmds.container(self.moduleContainer, edit=True, publishAndBind=[moduleNode+'.proxy_geometry_draw', 'module_transform_proxy_geometry_draw_toggle'])

    def createProxyGeo_elbows(self, geoType='sphere'):
        if geoType == 'sphere':
            filePathSuffix = 'MRT/elbow_proxySphereGeo.ma'
        if geoType == 'cube':
            filePathSuffix = 'MRT/elbow_proxyCubeGeo.ma'
        filePath = cmds.internalVar(userScriptDir=True) + filePathSuffix
        if self.mirrorModule:
            originalNamespace = cmds.getAttr(self.moduleGrp+'.mirrorModuleNamespace')
        index = 0
        hingeAimConstraints = []
        for joint in self.nodeJoints:
            cmds.file(filePath, i=True, prompt=False, ignoreVersion=True)
            proxyElbowGeoPreTransform = '_proxy_elbow_geo_preTransform'
            proxyElbowGeoScaleTransform = '_proxy_elbow_geo_scaleTransform'
            proxyElbowTransform = '_proxy_elbow_geo'
            if self.mirrorModule and self.proxyGeoMirrorInstance == 'On':
                originalNamespace = cmds.getAttr(self.moduleGrp+'.mirrorModuleNamespace')
                originalProxyElbowTransform = originalNamespace+':'+mfunc.stripMRTNamespace(joint)[1]+proxyElbowTransform
                cmds.delete(proxyElbowTransform)
                transformInstance = cmds.duplicate(originalProxyElbowTransform, instanceLeaf=True, name='_proxy_elbow_geo')[0]
                cmds.parent(transformInstance, proxyElbowGeoScaleTransform, relative=True)
                if self.moduleName != 'HingeNode':
                    scaleFactorAxes = {'XY':[1, 1, -1], 'YZ':[-1, 1, 1], 'XZ':[1, -1, 1]}[self.onPlane]
                else:
                    scaleFactorAxes = {'XY':[-1, 1, 1], 'YZ':[1, 1, -1], 'XZ':[1, 1, -1]}[self.onPlane]
                cmds.setAttr(proxyElbowGeoScaleTransform+'.scale', *scaleFactorAxes)
            cmds.select(proxyElbowTransform+'.vtx[*]', replace=True)
            cmds.polyColorPerVertex(alpha=0.3, rgb=[0.663, 0.561, 0.319], notUndoable=True, colorDisplayOption=True)
            cmds.pointConstraint(joint, proxyElbowGeoPreTransform, maintainOffset=False, name=joint+'_pointConstraint')
            cmds.scaleConstraint(joint, proxyElbowGeoPreTransform, maintainOffset=False, name=joint+'_scaleConstraint')
            if self.moduleName == 'JointNode':
                aimVector = {'X':[1.0, 0.0, 0.0], 'Y':[0.0, 1.0, 0.0], 'Z':[0.0, 0.0, 1.0]}[self.nodeAxes[0]]
                upVector = {'X':[1.0, 0.0, 0.0], 'Y':[0.0, 1.0, 0.0], 'Z':[0.0, 0.0, 1.0]}[self.nodeAxes[1]]
                if self.numNodes > 1:
                    if index == 0:
                        cmds.aimConstraint(self.nodeJoints[index+1], proxyElbowGeoPreTransform, maintainOffset=True, aimVector=aimVector, upVector=upVector, worldUpVector=upVector, worldUpType='objectRotation', worldUpObject=joint, name=joint+'_'+proxyElbowGeoPreTransform+'_aimConstraint')
                    else:
                        cmds.aimConstraint(self.nodeJoints[index-1], proxyElbowGeoPreTransform, maintainOffset=True, aimVector=aimVector, upVector=upVector, worldUpVector=upVector, worldUpType='objectRotation', worldUpObject=joint, name=joint+'_'+proxyElbowGeoPreTransform+'_aimConstraint')
                if self.numNodes == 1:
                    cmds.orientConstraint(self.moduleNamespace+':single_orient_repr_transform', proxyElbowGeoPreTransform, maintainOffset=True, name=proxyElbowGeoPreTransform+'_orientConstraint')
            if self.moduleName == 'HingeNode':
                aimVector = {'X':[1.0, 0.0, 0.0], 'Y':[0.0, 1.0, 0.0], 'Z':[0.0, 0.0, 1.0]}[self.nodeAxes[0]]
                upVector = {'X':[1.0, 0.0, 0.0], 'Y':[0.0, 1.0, 0.0], 'Z':[0.0, 0.0, 1.0]}[self.nodeAxes[1]]
                if index == 0:
                    aimConstraint = cmds.aimConstraint(self.nodeJoints[index+1], proxyElbowGeoPreTransform, maintainOffset=True, aimVector=aimVector, upVector=upVector, worldUpVector=upVector, worldUpType='objectRotation', worldUpObject=joint, name=joint+'_'+proxyElbowGeoPreTransform+'_aimConstraint')[0]
                else:
                    aimConstraint = cmds.aimConstraint(self.nodeJoints[index-1], proxyElbowGeoPreTransform, maintainOffset=True, aimVector=aimVector, upVector=upVector, worldUpVector=upVector, worldUpType='objectRotation', worldUpObject=joint, name=joint+'_'+proxyElbowGeoPreTransform+'_aimConstraint')[0]
                hingeAimConstraints.append(aimConstraint)

            if self.moduleName == 'SplineNode':
                cmds.orientConstraint(joint, proxyElbowGeoPreTransform, maintainOffset=True, name=joint+'_'+proxyElbowGeoPreTransform+'_orientConstraint')
            cmds.parent(proxyElbowGeoPreTransform, self.proxyGeoGrp, absolute=True)
            cmds.rename(proxyElbowGeoPreTransform, joint+proxyElbowGeoPreTransform)
            cmds.rename(proxyElbowGeoScaleTransform, joint+proxyElbowGeoScaleTransform)
            cmds.rename(proxyElbowTransform, joint+proxyElbowTransform)
            extra_nodes = [u'elbow_proxyGeo_uiConfigurationScriptNode', u'elbow_proxyGeo_sceneConfigurationScriptNode']
            for node in extra_nodes:
                if cmds.objExists(node):
                    cmds.delete(node)
            index += 1

        # Find and change the aim constraint offset values on hinge node in order to properly orient the elbow proxy geo.
        if hingeAimConstraints:
            l_val = [0.0, 90.0, 180.0, 270.0, 360.0]
            for constraint in hingeAimConstraints:
                for attr in ['X', 'Y', 'Z']:
                    val = cmds.getAttr(constraint+'.offset'+attr)
                    if not round(abs(val),0) in l_val:
                        l_cmp = {}
                        for item in l_val:
                            l_cmp[abs(item - abs(val))] = item
                        off_value = l_cmp[min(l_cmp)]
                        off_value = math.copysign(off_value, val)
                        cmds.setAttr(constraint+'.offset'+attr, off_value)

        cmds.select(clear=True)

    def createProxyGeo_bones(self):
        filePath = cmds.internalVar(userScriptDir=True) + 'MRT/bone_proxyGeo.ma'
        index = 0
        for joint in self.nodeJoints[:-1]:
            cmds.namespace(setNamespace=':')
            cmds.file(filePath, i=True, prompt=False, ignoreVersion=True)
            proxyBoneGeoPreTransform = 'proxy_bone_geo_preTransform'
            proxyBoneGeoScaleTransform = 'proxy_bone_geo_scaleTransform'
            proxyBoneTransform = 'proxy_bone_geo'

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

            if self.mirrorModule and self.proxyGeoMirrorInstance == 'On':
                originalNamespace = cmds.getAttr(self.moduleGrp+'.mirrorModuleNamespace')
                originalProxyBoneTransform = originalNamespace+':'+mfunc.stripMRTNamespace(joint)[1]+'_'+proxyBoneTransform
                cmds.delete(proxyBoneTransform)
                transformInstance = cmds.duplicate(originalProxyBoneTransform, instanceLeaf=True, name='proxy_bone_geo')[0]
                cmds.parent(transformInstance, proxyBoneGeoScaleTransform, relative=True)
                if self.moduleName == 'HingeNode' and self.mirrorRotationFunc == 'Orientation':
                    scaleFactorAxes = {'X':[-1, 1, 1], 'Y':[1, -1, 1], 'Z':[1, 1, -1]}[self.nodeAxes[2]]
                else:
                    scaleFactorAxes = {'X':[-1, 1, 1], 'Y':[1, -1, 1], 'Z':[1, 1, -1]}[self.nodeAxes[1]]
                cmds.setAttr(proxyBoneGeoScaleTransform+'.scale', *scaleFactorAxes)

            cmds.select(proxyBoneTransform+'.vtx[*]', replace=True)
            cmds.polyColorPerVertex(alpha=0.3, rgb=[0.663, 0.561, 0.319], notUndoable=True, colorDisplayOption=True)
            if not self.mirrorModule:
                for axis in self.nodeAxes[1:]:
                    cmds.setAttr(proxyBoneGeoPreTransform+'.scale'+axis, 0.17)
                cmds.makeIdentity(proxyBoneGeoPreTransform, scale=True, apply=True)
            if self.mirrorModule and self.proxyGeoMirrorInstance == 'Off':
                for axis in self.nodeAxes[1:]:
                    cmds.setAttr(proxyBoneGeoPreTransform+'.scale'+axis, 0.17)
                cmds.makeIdentity(proxyBoneGeoPreTransform, scale=True, apply=True)

            cmds.parent(proxyBoneGeoPreTransform, self.proxyGeoGrp, absolute=True)

            tempConstraint = cmds.orientConstraint(joint, proxyBoneGeoPreTransform, maintainOffset=False)
            cmds.delete(tempConstraint)

            for axis in self.nodeAxes[1:]:
                cmds.connectAttr(self.moduleTransform+'.globalScale', proxyBoneGeoPreTransform+'.scale'+axis)
            ##curveInfo = joint + '_handleControlSegmentCurve_curveInfo'
            curveInfo = joint + '_segmentCurve_curveInfo'
            cmds.connectAttr(curveInfo+'.arcLength', proxyBoneGeoPreTransform+'.scale'+self.nodeAxes[0])
            ##cmds.pointConstraint(joint+'_handleControlSegmentCurve_startLocator', proxyBoneGeoPreTransform, maintainOffset=False, name=self.moduleNamespace+':'+proxyBoneGeoPreTransform+'_basePointConstraint')
            cmds.pointConstraint(joint+'_segmentCurve_startLocator', proxyBoneGeoPreTransform, maintainOffset=False, name=self.moduleNamespace+':'+proxyBoneGeoPreTransform+'_basePointConstraint')
            aimVector = {'X':[1.0, 0.0, 0.0], 'Y':[0.0, 1.0, 0.0], 'Z':[0.0, 0.0, 1.0]}[self.nodeAxes[0]]
            upVector = {'X':[1.0, 0.0, 0.0], 'Y':[0.0, 1.0, 0.0], 'Z':[0.0, 0.0, 1.0]}[self.nodeAxes[1]]

            cmds.aimConstraint(self.nodeJoints[index+1], proxyBoneGeoPreTransform, maintainOffset=False, aimVector=aimVector, upVector=upVector, worldUpVector=upVector, worldUpType='objectRotation', worldUpObject=joint, name=self.nodeJoints[index+1]+'_'+proxyBoneGeoPreTransform+'_aimConstraint')
            cmds.rename(proxyBoneGeoPreTransform, joint+'_'+proxyBoneGeoPreTransform)
            cmds.rename(proxyBoneGeoScaleTransform, joint+'_'+proxyBoneGeoScaleTransform)
            cmds.rename(proxyBoneTransform, joint+'_'+proxyBoneTransform)
            extra_nodes = [u'bone_proxyGeo_uiConfigurationScriptNode', u'bone_proxyGeo_sceneConfigurationScriptNode']
            for node in extra_nodes:
                if cmds.objExists(node):
                    cmds.delete(node)
            index += 1
        cmds.select(clear=True)

    def connectCustomOrientationReprToModuleProxies(self):
        if self.moduleName == 'JointNode':
            rotAxis = cmds.getAttr(self.moduleGrp+'.nodeOrient')
            rotAxis = rotAxis[0]
            for joint in self.nodeJoints[:-1]:
                ori_repr_control = joint+'_orient_repr_transform'
                boneProxy_s_transform = joint+'_proxy_bone_geo_scaleTransform'
                if cmds.objExists(boneProxy_s_transform):
                    cmds.connectAttr(ori_repr_control+'.rotate'+rotAxis, boneProxy_s_transform+'.rotate'+rotAxis)
        if self.moduleName == 'SplineNode':
            startHandle = self.nodeJoints[0].rpartition(':')[0] + ':splineStartHandleTransform'
            for joint in self.nodeJoints:
                elbowProxy_s_transform = joint+'_proxy_elbow_geo_scaleTransform'
                if cmds.objExists(elbowProxy_s_transform):
                    cmds.connectAttr(startHandle+'.Axis_Rotate', elbowProxy_s_transform+'.rotateY')
