# *************************************************************************************************************
#
#    mrt_objects.py - Source for creating all scene objects being used by MRT (except proxy geometry).
#                     These objects are mainly used to create module components and
#                     control objects for control rigging.
#
#    Can be modified or copied for your own purpose.
#
#    Written by Himanish Bhattacharya
#
# *************************************************************************************************************

__moduleName__ = 'mrt_objects'

import maya.cmds as cmds
import maya.mel as mel
import os

# For locking and hiding channel box attributes on input transforms.
from mrt_functions import lockHideChannelAttrs, align


def curve(**kwargs):
    '''
    Convenience function which acts as a wrapper for the maya "curve" command.
    It renames the curve shape properly, and returns it with its parent transform.
    '''
    if 'name' in kwargs:
        name = kwargs['name'] + 'Shape'

    if 'shapeName' in kwargs:
        name = kwargs['shapeName']
        kwargs.pop('shapeName')
        
    crv = cmds.curve(**kwargs)
        
    crvShape = cmds.listRelatives(crv, children=True, shapes=True, type='nurbsCurve')[0]
    crvShape = cmds.rename(crvShape, name)
    
    return crv, crvShape
    

def addShapes(parentTransform, shapeTransform):
    '''
    For adding shape(s) to a given transform. The shapes are added from the transform "shapeTransform"
    to the target transform "parentTransform". The "shapeTransform" is then removed.
    '''
    shapes = cmds.listRelatives(shapeTransform, children=True, shapes=True) or []
    for shape in shapes:
        cmds.parent(shape, parentTransform, relative=True, shape=True)
    if shapes:
        cmds.delete(shapeTransform)


def createRawControlSurface(transformName, modHandleColour, createWithTransform=False):
    '''
    Creates a "rig" dummy surface for a node control handle in a module. This is done since
    the node control (yellow, spherical) is not a true surface shape that can be used, so a dummy
    NURBS spherical shape is used "behind" it for rigging purposes. This dummy shape is hidden later.
    '''
    if createWithTransform:
        handleParent = cmds.createNode('transform', name=transformName+'_control')
        handleShape = cmds.createNode('nurbsSurface', name=handleParent+'Shape', parent=handleParent)
    else:
        handleParent = transformName
        handleShape = cmds.createNode('nurbsSurface', name=handleParent+'_controlShape', parent=handleParent)

    cmds.setAttr('.overrideEnabled', 1)
    cmds.setAttr('.overrideColor', modHandleColour)
    cmds.setAttr('.overrideShading', 0)
    cmds.setAttr('.castsShadows', 0)
    cmds.setAttr('.receiveShadows', 0)
    cmds.setAttr('.motionBlur', 0)
    cmds.setAttr('.primaryVisibility', 0)
    cmds.setAttr('.smoothShading', 0)
    cmds.setAttr('.visibleInReflections', 0)
    cmds.setAttr('.visibleInRefractions', 0)
    cmds.setAttr('.curvePrecision', 3)
    cmds.setAttr('.curvePrecisionShaded', 3)

    mel.eval("""setAttr ".cached" -type "nurbsSurface"
    3 3 0 2 no
    9 0 0 0 1 2 3 4 4 4
    13 -2 -1 0 1 2 3 4 5 6 7 8 9 10

    77
    0.0 -0.0882 0.0
    0.0 -0.0882 0.0
    0.0 -0.0882 0.0
    0.0 -0.0882 0.0
    0.0 -0.0882 0.0
    0.0 -0.0882 0.0
    0.0 -0.0882 0.0
    0.0 -0.0882 0.0
    0.0 -0.0882 0.0
    0.0 -0.0882 0.0
    0.0 -0.0882 0.0
    0.0176 -0.0882 -0.0176
    0.0249 -0.0882 0.0
    0.0176 -0.0882 0.0176
    0.0 -0.0882 0.0249
    -0.0176 -0.0882 0.0176
    -0.0249 -0.0882 0.0
    -0.0176 -0.0882 -0.0176
    0.0 -0.0882 -0.0249
    0.0176 -0.0882 -0.0176
    0.0249 -0.0882 0.0
    0.0176 -0.0882 0.0176
    0.0544 -0.0691 -0.0544
    0.0769 -0.0691 0.0
    0.0544 -0.0691 0.0544
    0.0 -0.0691 0.0769
    -0.0544 -0.0691 0.0544
    -0.0769 -0.0691 0.0
    -0.0544 -0.0691 -0.0544
    0.0 -0.0691 -0.0769
    0.0544 -0.0691 -0.0544
    0.0769 -0.0691 0.0
    0.0544 -0.0691 0.0544
    0.0765 0.0 -0.0765
    0.1082 0.0 0.0
    0.0765 0.0 0.0765
    0.0 0.0 0.1082
    -0.0765 0.0 0.0765
    -0.1082 0.0 0.0
    -0.0765 0.0 -0.0765
    0.0 0.0 -0.1082
    0.0765 0.0 -0.0765
    0.1082 0.0 0.0
    0.0765 0.0 0.0765
    0.0544 0.0691 -0.0544
    0.0769 0.0691 0.0
    0.0544 0.0691 0.0544
    0.0 0.0691 0.0769
    -0.0544 0.0691 0.0544
    -0.0769 0.0691 0.0
    -0.0544 0.0691 -0.0544
    0.0 0.0691 -0.0769
    0.0544 0.0691 -0.0544
    0.0769 0.0691 0.0
    0.0544 0.0691 0.0544
    0.0176 0.0882 -0.0176
    0.0249 0.0882 0.0
    0.0176 0.0882 0.0176
    0.0 0.0882 0.0249
    -0.0176 0.0882 0.0176
    -0.0249 0.0882 0.0
    -0.0176 0.0882 -0.0176
    0.0 0.0882 -0.0249
    0.0176 0.0882 -0.0176
    0.0249 0.0882 0.0
    0.0176 0.0882 0.0176
    0.0 0.0882 0.0
    0.0 0.0882 0.0
    0.0 0.0882 0.0
    0.0 0.0882 0.0
    0.0 0.0882 0.0
    0.0 0.0882 0.0
    0.0 0.0882 0.0
    0.0 0.0882 0.0
    0.0 0.0882 0.0
    0.0 0.0882 0.0
    0.0 0.0882 0.0;""")

    return handleParent, handleShape


def createRawSegmentCurve(modHandleColour):
    '''
    Creates a one degree, 2 CV curve with locators at each ends driving the curve.
    '''
    segment = {}
    
    segment['curve'], segment['curveShape'] = curve(p=([1, 0, 0], [-1, 0, 0]), degree=1, name='segmentCurve')

    lockHideChannelAttrs(segment['curve'], 't', 'r', 's', 'v', keyable=False)

    cmds.setAttr(segment['curveShape']+'.overrideEnabled', 1)
    cmds.setAttr(segment['curveShape']+'.overrideColor', modHandleColour)

    segment['startLoc'] = cmds.spaceLocator(name='segmentCurve_startLocator')[0]
    cmds.xform(segment['startLoc'], worldSpace=True, translation=[1, 0, 0])
    cmds.setAttr(segment['startLoc'] + '.visibility', 0)
    cmds.connectAttr(segment['startLoc']+'.worldPosition', segment['curveShape']+'.controlPoints[0]')
    
    segment['endLoc'] = cmds.spaceLocator(name='segmentCurve_endLocator')[0]
    cmds.xform(segment['endLoc'], worldSpace=True, translation=[-1, 0, 0])
    cmds.setAttr(segment['endLoc'] + '.visibility', 0)
    cmds.connectAttr(segment['endLoc']+'.worldPosition', segment['curveShape']+'.controlPoints[1]')
    
    return segment


def createRawOrientationRepresentation(aimAxis):
    '''
    Create the raw curve transform representation which is to be used as a control
    for defining the axial orientation of a module node (used in JointNode and HingeNode modules).
    '''
    representationTransformGroup = cmds.createNode('transform', name='orient_repr_transformGrp')
    representationTransform = cmds.createNode('transform', name='orient_repr_transform', parent='orient_repr_transformGrp')

    lockHideChannelAttrs(representationTransform, 't', 'ry', 'rz', 's', 'v', keyable=False)

    cmds.setAttr(representationTransform+'.rotatePivot', 0.09015, 0, 0, type='double3')
    cmds.setAttr(representationTransform+'.scalePivot', 0.09015, 0, 0, type='double3')

    # For eg., If the node aim axis is 'X', create the representation indicating the Y and Z axes. The control
    # will be used and aligned with the node and then it'll rotate along the aim axis.

    if aimAxis == 'X':

        representationZ = cmds.curve(p=[(0.0901, -0.0, 0.0469),
                                        (1.09, -0.0, 0.0469),
                                        (1.09, -0.0, 0.39),
                                        (0.0901, 0.0, 0.39),
                                        (0.0901, -0.0, 0.0469),
                                        (0.0901, -0.0, -0.0469),
                                        (0.0901, -0.0, -0.1319),
                                        (1.09, -0.0, -0.1319),
                                        (1.09, -0.0, -0.0469),
                                        (0.0901, -0.0, -0.0469)],
                                    degree=1,
                                    knot=[0, 1, 1, 2, 3, 4, 5, 5, 6, 7])

        representationZShape = cmds.listRelatives(representationZ, children=True, shapes=True)[0]
        cmds.setAttr(representationZShape+'.overrideEnabled', 1)
        cmds.setAttr(representationZShape+'.overrideColor', 6)
        cmds.rename(representationZShape, 'orient_repr_transformShape')
        addShapes(representationTransform, representationZ)


        representationY = cmds.curve(p=[(0.0901, -0.0469, 0.0),
                                        (1.09, -0.0469, 0.0),
                                        (1.09, -0.1319, 0.0),
                                        (0.0901, -0.1319, 0.0),
                                        (0.0901, -0.0469, 0.0),
                                        (0.0901, 0.0469, 0.0),
                                        (0.0901, 0.39, 0.0),
                                        (1.09, 0.39, 0.0),
                                        (1.09, 0.0469, 0.0),
                                        (0.0901, 0.0469, 0.0)],
                                    degree=1,
                                    knot=[0, 1, 1, 2, 3, 4, 5, 5, 6, 7])

        representationYShape = cmds.listRelatives(representationY, children=True, shapes=True)[0]
        cmds.setAttr(representationYShape+'.overrideEnabled', 1)
        cmds.setAttr(representationYShape+'.overrideColor', 14)
        cmds.rename(representationYShape, 'orient_repr_transformShape1')
        addShapes(representationTransform, representationY)

    if aimAxis == 'Z':
        representationY = cmds.curve(p=[(-0.0, 0.0469, 0.0901),
                                        (0.0, 0.0469, 1.0901),
                                        (0.0, 0.39, 1.0901),
                                        (0.0, 0.39, 0.0901),
                                        (-0.0, 0.0469, 0.0901),
                                        (-0.0, -0.0469, 0.0901),
                                        (-0.0, -0.1319, 0.0901),
                                        (0.0, -0.1319, 1.0901),
                                        (0.0, -0.0469, 1.0901),
                                        (-0.0, -0.0469, 0.0901)],
                                    degree=1,
                                    knot=[0, 1, 1, 2, 3, 4, 5, 5, 6, 7])

        representationYShape = cmds.listRelatives(representationY, children=True, shapes=True)[0]
        cmds.setAttr(representationYShape+'.overrideEnabled', 1)
        cmds.setAttr(representationYShape+'.overrideColor', 14)
        cmds.rename(representationYShape, 'orient_repr_transformShape')
        addShapes(representationTransform, representationY)

        representationX = cmds.curve(p=[(-0.0469, 0.0, 0.0901),
                                        (-0.0469, 0.0, 1.0901),
                                        (-0.1319, 0.0, 1.0901),
                                        (-0.1319, 0.0, 0.0901),
                                        (-0.0469, 0.0, 0.0901),
                                        (0.0469, 0.0, 0.0901),
                                        (0.39, 0.0, 0.0901),
                                        (0.39, 0.0, 1.0901),
                                        (0.0469, 0.0, 1.0901),
                                        (0.0469, 0.0, 0.0901)],
                                     degree=1,
                                     knot=[0, 1, 1, 2, 3, 4, 5, 5, 6, 7])

        representationXShape = cmds.listRelatives(representationX, children=True, shapes=True)[0]
        cmds.setAttr(representationXShape+'.overrideEnabled', 1)
        cmds.setAttr(representationXShape+'.overrideColor', 13)
        cmds.rename(representationXShape, 'orient_repr_transformShape1')
        addShapes(representationTransform, representationX)

    if aimAxis == 'Y':

        representationZ = cmds.curve(p=[(-0.0, 0.0901, 0.0469),
                                        (0.0, 1.0901, 0.0469),
                                        (0.0, 1.0901, 0.39),
                                        (0.0, 0.0901, 0.39),
                                        (-0.0, 0.0901, 0.0469),
                                        (-0.0, 0.0901, -0.0469),
                                        (-0.0, 0.0901, -0.1319),
                                        (0.0, 1.0901, -0.1319),
                                        (0.0, 1.0901, -0.0469),
                                        (-0.0, 0.0901, -0.0469)],
                                     degree=1,
                                     knot=[0, 1, 1, 2, 3, 4, 5, 5, 6, 7])

        representationZShape = cmds.listRelatives(representationZ, children=True, shapes=True)[0]
        cmds.setAttr(representationZShape+'.overrideEnabled', 1)
        cmds.setAttr(representationZShape+'.overrideColor', 6)
        cmds.rename(representationZShape, 'orient_repr_transformShape')
        addShapes(representationTransform, representationZ)

        representationX = cmds.curve(p=[(-0.0469, 0.0901, 0.0),
                                        (-0.0469, 1.0901, 0.0),
                                        (-0.1319, 1.0901, 0.0),
                                        (-0.1319, 0.0901, 0.0),
                                        (-0.0469, 0.0901, 0.0),
                                        (0.0469, 0.0901, 0.0),
                                        (0.39, 0.0901, 0.0),
                                        (0.39, 1.0901, 0.0),
                                        (0.0469, 1.0901, 0.0),
                                        (0.0469, 0.0901, 0.0)],
                                     degree=1,
                                     knot=[0, 1, 1, 2, 3, 4, 5, 5, 6, 7])

        representationXShape = cmds.listRelatives(representationX, children=True, shapes=True)[0]
        cmds.setAttr(representationXShape+'.overrideEnabled', 1)
        cmds.setAttr(representationXShape+'.overrideColor', 13)
        cmds.rename(representationXShape, 'orient_repr_transformShape1')
        addShapes(representationTransform, representationX)

    cmds.select(clear=True)

    return representationTransform, representationTransformGroup


def createRawSingleOrientationRepresentation():
    '''
    Create a raw curve transform representation to be used as a control
    for defining the orientation of a JointNode module with a single node.

    This creates the transform with three curve arrows along the X, Y and Z axes.
    '''
    orientationTransform = cmds.createNode('transform', name='single_orient_repr_transform')

    lockHideChannelAttrs(orientationTransform, 't', 's', 'v', keyable=False)

    orient_repr_Y, \
    orient_repr_YShape = curve(p=[(0.0, 0.0, 0.0),
                                  (0.0, 0.5349, 0.0),
                                  (0.0, 0.5349, 0.0472),
                                  (0.0, 0.6903, 0.0),
                                  (0.0, 0.5349, -0.0472),
                                  (0.0, 0.5349, 0.0),
                                  (0.0472, 0.5349, 0.0),
                                  (0.0, 0.6903, 0.0),
                                  (-0.0472, 0.5349, 0.0),
                                  (0.0, 0.5349, 0.0472),
                                  (0.0472, 0.5349, 0.0),
                                  (0.0, 0.5349, -0.0472),
                                  (-0.0472, 0.5349, 0.0),
                                  (0.0, 0.5349, 0.0)],
                                  shapeName='single_orient_repr_transformShape',
                                  degree=1,
                                  knot=[142, 162, 166, 175, 184, 188, 192, 201, 210, 215, 221, 227, 232, 236])

    cmds.setAttr(orient_repr_YShape+'.overrideEnabled', 1)
    cmds.setAttr(orient_repr_YShape+'.overrideColor', 14)
    addShapes(orientationTransform, orient_repr_Y)

    orient_repr_X, \
    orient_repr_XShape = curve(p=[(0.0, 0.0, 0.0),
                                  (0.5349, 0.0, 0.0),
                                  (0.5349, 0.0, 0.0472),
                                  (0.6903, 0.0, 0.0),
                                  (0.5349, 0.0, -0.0472),
                                  (0.5349, 0.0, 0.0),
                                  (0.5349, -0.0472, 0.0),
                                  (0.6903, 0.0, 0.0),
                                  (0.5349, 0.0472, 0.0),
                                  (0.5349, 0.0, 0.0472),
                                  (0.5349, -0.0472, 0.0),
                                  (0.5349, 0.0, -0.0472),
                                  (0.5349, 0.0472, 0.0),
                                  (0.5349, 0.0, 0.0)],
                                  shapeName='single_orient_repr_transformShape1',
                                  degree=1,
                                  knot=[142, 162, 166, 175, 184, 188, 192, 201, 210, 215, 221, 227, 232, 236])

    cmds.setAttr(orient_repr_XShape+'.overrideEnabled', 1)
    cmds.setAttr(orient_repr_XShape+'.overrideColor', 13)
    addShapes(orientationTransform, orient_repr_X)

    orient_repr_Z, \
    orient_repr_ZShape = curve(p=[(0.0, -0.0, 0.0),
                                  (0.0, -0.0, 0.5349),
                                  (-0.0472, -0.0, 0.5349),
                                  (0.0, -0.0, 0.6903),
                                  (0.0472, -0.0, 0.5349),
                                  (0.0, -0.0, 0.5349),
                                  (0.0, -0.0472, 0.5349),
                                  (0.0, -0.0, 0.6903),
                                  (0.0, 0.0472, 0.5349),
                                  (-0.0472, -0.0, 0.5349),
                                  (0.0, -0.0472, 0.5349),
                                  (0.0472, -0.0, 0.5349),
                                  (0.0, 0.0472, 0.5349),
                                  (0.0, -0.0, 0.5349)],
                                  shapeName='single_orient_repr_transformShape2',
                                  degree=1,
                                  knot=[142, 162, 166, 175, 184, 188, 192, 201, 210, 215, 221, 227, 232, 236])

    cmds.setAttr(orient_repr_ZShape+'.overrideEnabled', 1)
    cmds.setAttr(orient_repr_ZShape+'.overrideColor', 6)
    addShapes(orientationTransform, orient_repr_Z)

    return orientationTransform


def createRawHierarchyRepresentation(aimAxis):
    '''
    Creates an 'arrow' curve aligned (along world) with the specified aim axis. This is used
    to represent the direction of hierarchy for nodes in JointNode and HingeNode modules.

    This is also used to create hierarchy representation for module parenting.
    '''
    hierarchyRepresentation = cmds.createNode('transform', name='hierarchy_repr')

    lockHideChannelAttrs(hierarchyRepresentation, 't', 'r', 's', 'v', keyable=False)

    if aimAxis == 'X':

        x_repr, \
        x_reprShape = curve(p=[(0.1191, 0.0, 0.0),
                               (-0.088, 0.039, 0.039),
                               (-0.088, 0.039, -0.039),
                               (0.1191, 0.0, 0.0),
                               (-0.088, 0.039, -0.039),
                               (-0.088, -0.039, -0.039),
                               (0.1191, 0.0, 0.0),
                               (-0.088, -0.039, -0.039),
                               (-0.088, -0.039, 0.039),
                               (0.1191, 0.0, 0.0),
                               (-0.088, -0.039, 0.039),
                               (-0.088, 0.039, 0.039)],
                            shapeName='hierarchy_reprShape',
                            degree=1,
                            knot=[12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23])

        cmds.setAttr(x_reprShape+'.overrideEnabled', 1)
        cmds.setAttr(x_reprShape+'.overrideColor', 13)
        addShapes(hierarchyRepresentation, x_repr)

    if aimAxis == 'Y':

        y_repr, \
        y_reprShape = curve(p=[(0.0, 0.1191, 0.0),
                               (-0.039, -0.088, 0.039),
                               (-0.039, -0.088, -0.039),
                               (0.0, 0.1191, 0.0),
                               (-0.039, -0.088, -0.039),
                               (0.039, -0.088, -0.039),
                               (0.0, 0.1191, 0.0),
                               (0.039, -0.088, -0.039),
                               (0.039, -0.088, 0.039),
                               (0.0, 0.1191, 0.0),
                               (0.039, -0.088, 0.039),
                               (-0.039, -0.088, 0.039)],
                            shapeName='hierarchy_reprShape',
                            degree=1,
                            knot=[12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23])

        cmds.setAttr(y_reprShape+'.overrideEnabled', 1)
        cmds.setAttr(y_reprShape+'.overrideColor', 14)
        addShapes(hierarchyRepresentation, y_repr)

    if aimAxis == 'Z':

        z_repr, \
        z_reprShape = curve(p=[(0.0, 0.0, 0.1191),
                               (-0.039, 0.039, -0.088),
                               (0.039, 0.039, -0.088),
                               (0.0, 0.0, 0.1191),
                               (0.039, 0.039, -0.088),
                               (0.039, -0.039, -0.088),
                               (0.0, 0.0, 0.1191),
                               (0.039, -0.039, -0.088),
                               (-0.039, -0.039, -0.088),
                               (0.0, 0.0, 0.1191),
                               (-0.039, -0.039, -0.088),
                               (-0.039, 0.039, -0.088)],
                            shapeName='hierarchy_reprShape',
                            degree=1,
                            knot=[12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23])

        cmds.setAttr(z_reprShape+'.overrideEnabled', 1)
        cmds.setAttr(z_reprShape+'.overrideColor', 6)
        addShapes(hierarchyRepresentation, z_repr)

    return hierarchyRepresentation


def createRawSplineAdjustCurveTransform(modHandleColour):
    '''
    Creates a "cube" curve transform, which is later used in a SplineNode module as one of the 
    controls to adjust the spline curve for adjusting the node positions.
    '''
    splineAdjustCurvePreTransform = cmds.createNode('transform', name='spline_adjustCurve_preTransform')
    
    splineAdjustCurveTransform, \
    splineAdjustCurveShape = curve(name='spline_adjustCurve_transform',
                                            p=[(-0.2929, 0.2929, 0.2929),
                                               (-0.2929, 0.2929, -0.2929),
                                               (0.2929, 0.2929, -0.2929),
                                               (0.2929, 0.2929, 0.2929),
                                               (-0.2929, 0.2929, 0.2929),
                                               (-0.2929, -0.2929, 0.2929),
                                               (-0.2929, -0.2929, -0.2929),
                                               (-0.2929, 0.2929, -0.2929),
                                               (-0.2929, 0.2929, 0.2929),
                                               (-0.2929, -0.2929, 0.2929),
                                               (0.2929, -0.2929, 0.2929),
                                               (0.2929, 0.2929, 0.2929),
                                               (0.2929, 0.2929, -0.2929),
                                               (0.2929, -0.2929, -0.2929),
                                               (0.2929, -0.2929, 0.2929),
                                               (0.2929, -0.2929, -0.2929),
                                               (-0.2929, -0.2929, -0.2929)],
                                            degree=1,
                                            knot=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16])

    cmds.parent(splineAdjustCurveTransform, splineAdjustCurvePreTransform, relative=True)

    lockHideChannelAttrs(splineAdjustCurveTransform, 'r', 's', 'v', keyable=False)

    cmds.setAttr(splineAdjustCurveShape+'.overrideEnabled', 1)
    cmds.setAttr(splineAdjustCurveShape+'.overrideColor', modHandleColour)
    cmds.rename(splineAdjustCurveShape, 'spline_adjustCurve_transformShape')

    return splineAdjustCurvePreTransform, splineAdjustCurveTransform


def createRawLocalAxesInfoRepresentation():
    '''
    Creates a three-axes curve transform to be used as a representation for node orientations
    in a SplineNode module type. 
    '''
    axesInfoPreTransform = cmds.createNode('transform', name='localAxesInfoRepr_preTransform')

    axesInfoTransform = cmds.createNode('transform', name='localAxesInfoRepr', parent=axesInfoPreTransform)
    lockHideChannelAttrs(axesInfoTransform, 't', 'r', 's', 'v', keyable=False)

    repr_X, repr_X_shape = curve(p=[(-0.0, 0.0, 0.0), (0.8325, 0.0, 0.0)], shapeName='localAxesInfoRepr_XShape', 
                                    knot=[0, 0], degree=1)
                                    
    cmds.setAttr(repr_X_shape+'.overrideEnabled', 1)
    cmds.setAttr(repr_X_shape+'.overrideColor', 13)
    addShapes(axesInfoTransform, repr_X)

    repr_Y, repr_Y_shape = curve(p=[(0.0, -0.0, 0.0), (0.0, 0.8325, 0.0)], shapeName='localAxesInfoRepr_YShape',
                                    knot=[0, 0], degree=1)
                                    
    cmds.setAttr(repr_Y_shape+'.overrideEnabled', 1)
    cmds.setAttr(repr_Y_shape+'.overrideColor', 14)
    addShapes(axesInfoTransform, repr_Y)

    repr_Z, repr_Z_shape = curve(p=[(0.0, 0.0, -0.0), (0.0, 0.0, 0.8325)], shapeName='localAxesInfoRepr_ZShape',
                        knot=[0, 0], degree=1)

    cmds.setAttr(repr_Z_shape+'.overrideEnabled', 1)
    cmds.setAttr(repr_Z_shape+'.overrideColor', 6)
    addShapes(axesInfoTransform, repr_Z)

    return axesInfoPreTransform, axesInfoTransform


def createRawIKPreferredRotationRepresentation(planeAxis):
    '''
    Creates a "curved" arrow transform to be used as a representation for indicating the direction
    of rotation of the hinge joint for a two bone joint chain to be generated from HingeNode module.
    '''
    representationTransform, representationShape = curve(name='IKPreferredRotationRepr', 
                                                         p=[(-0.0, -0.8197, -0.17),
                                                            (0.0371, -0.5773, -0.3753),
                                                            (0.0371, -0.5363, -0.3136),
                                                            (-0.0, -0.8197, -0.17),
                                                            (0.0371, -0.5363, -0.3136),
                                                            (-0.0371, -0.5363, -0.3136),
                                                            (-0.0, -0.8197, -0.17),
                                                            (-0.0371, -0.5363, -0.3136),
                                                            (-0.0371, -0.5773, -0.3753),
                                                            (-0.0, -0.8197, -0.17),
                                                            (0.0371, -0.5773, -0.3753),
                                                            (-0.0371, -0.5773, -0.3753),
                                                            (-0.0, -0.8197, -0.17),
                                                            (0.0, -0.4648, -0.4034),
                                                            (0.0, -0.2866, -0.4948),
                                                            (0.0, -0.0925, -0.5442),
                                                            (0.0, 0.1077, -0.5492),
                                                            (0.0, 0.3041, -0.5096),
                                                            (0.0, 0.4866, -0.4272),
                                                            (0.0, 0.6463, -0.3063),
                                                            (0.0, 0.7751, -0.1529)],
                                        degree=1,
                                        knot=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20])

    lockHideChannelAttrs(representationTransform, 't', 'r', 's', 'v', keyable=False)
    cmds.setAttr(representationShape+'.overrideEnabled', 1)
    
    if planeAxis == 'X':
        cmds.setAttr(representationShape+'.overrideColor', 13)
    if planeAxis == 'Y':
        cmds.setAttr(representationShape+'.overrideColor', 14)
    if planeAxis == 'Z':
        cmds.setAttr(representationShape+'.overrideColor', 6)

    return representationTransform


def createRawIKhingeAxisRepresenation(upFrontAxes):
    '''
    Creates two perpendicular arrow curves under a transform which is used to indicate the
    up-axis and the plane-axis (the axis normal to the module creation plane, also called
    front axis) for the hinge node in a HingeNode module. 
    '''
    representationTransform = cmds.createNode('transform', name='IKhingeAxisRepresenation')
    lockHideChannelAttrs(representationTransform, 't', 'r', 's', 'v', keyable=False)

    if upFrontAxes == 'XY':
        xy_up_repr = cmds.curve(p=[(0.0, -0.0, 0.0),
                                   (0.1833, -0.0, 0.0),
                                   (0.1833, 0.0225, 0.0),
                                   (0.2451, -0.0, 0.0),
                                   (0.1833, -0.0225, 0.0),
                                   (0.1833, -0.0, 0.0),
                                   (0.1833, -0.0, 0.0225),
                                   (0.2451, -0.0, 0.0),
                                   (0.1833, -0.0, -0.0225),
                                   (0.1833, 0.0225, 0.0),
                                   (0.1833, -0.0, 0.0225),
                                   (0.1833, -0.0225, 0.0),
                                   (0.1833, -0.0, -0.0225),
                                   (0.1833, -0.0, 0.0)],
                               degree=1,
                               knot=[142, 162, 166, 175, 184, 188, 192, 201, 210, 215, 221, 227, 232, 236])

        xy_up_repr_shape = cmds.listRelatives(xy_up_repr, children=True, shapes=True)[0]
        cmds.setAttr(xy_up_repr_shape+'.overrideEnabled', 1)
        cmds.setAttr(xy_up_repr_shape+'.overrideColor', 13)
        cmds.rename(xy_up_repr_shape, 'IKhingeAxisRepresenationShape')
        addShapes(representationTransform, xy_up_repr)

        xy_hinge_repr = cmds.curve(p=[(0.0, 0.0, 0.0),
                                      (0.0, 0.1833, 0.0),
                                      (-0.0225, 0.1833, 0.0),
                                      (0.0, 0.2451, 0.0),
                                      (0.0225, 0.1833, 0.0),
                                      (0.0, 0.1833, 0.0),
                                      (0.0, 0.1833, 0.0225),
                                      (0.0, 0.2451, 0.0),
                                      (0.0, 0.1833, -0.0225),
                                      (-0.0225, 0.1833, 0.0),
                                      (0.0, 0.1833, 0.0225),
                                      (0.0225, 0.1833, 0.0),
                                      (0.0, 0.1833, -0.0225),
                                      (0.0, 0.1833, 0.0)],
                               degree=1,
                               knot=[142, 162, 166, 175, 184, 188, 192, 201, 210, 215, 221, 227, 232, 236])

        xy_hinge_repr_shape = cmds.listRelatives(xy_hinge_repr, children=True, shapes=True)[0]
        cmds.setAttr(xy_hinge_repr_shape+'.overrideEnabled', 1)
        cmds.setAttr(xy_hinge_repr_shape+'.overrideColor', 14)
        cmds.rename(xy_hinge_repr_shape, 'IKhingeAxisRepresenationShape1')
        addShapes(representationTransform, xy_hinge_repr)

    if upFrontAxes == 'XZ':
        xz_up_repr = cmds.curve(p=[(0.0, -0.0, -0.0),
                                   (0.2133, -0.0, -0.0),
                                   (0.2133, -0.0, 0.0225),
                                   (0.2751, -0.0, -0.0),
                                   (0.2133, -0.0, -0.0225),
                                   (0.2133, -0.0, -0.0),
                                   (0.2133, -0.0225, -0.0),
                                   (0.2751, -0.0, -0.0),
                                   (0.2133, 0.0225, -0.0),
                                   (0.2133, -0.0, 0.0225),
                                   (0.2133, -0.0225, -0.0),
                                   (0.2133, -0.0, -0.0225),
                                   (0.2133, 0.0225, -0.0),
                                   (0.2133, -0.0, -0.0)],
                               degree=1,
                               knot=[142, 162, 166, 175, 184, 188, 192, 201, 210, 215, 221, 227, 232, 236])

        xz_up_repr_shape = cmds.listRelatives(xz_up_repr, children=True, shapes=True)[0]
        cmds.setAttr(xz_up_repr_shape+'.overrideEnabled', 1)
        cmds.setAttr(xz_up_repr_shape+'.overrideColor', 13)
        cmds.rename(xz_up_repr_shape, 'IKhingeAxisRepresenationShape')
        addShapes(representationTransform, xz_up_repr)

        xz_hinge_repr = cmds.curve(p=[(0.0, 0.0, 0.0),
                                      (0.0, -0.0, 0.2133),
                                      (-0.0225, -0.0, 0.2133),
                                      (0.0, -0.0, 0.2751),
                                      (0.0225, -0.0, 0.2133),
                                      (0.0, -0.0, 0.2133),
                                      (0.0, -0.0225, 0.2133),
                                      (0.0, -0.0, 0.2751),
                                      (0.0, 0.0225, 0.2133),
                                      (-0.0225, -0.0, 0.2133),
                                      (0.0, -0.0225, 0.2133),
                                      (0.0225, -0.0, 0.2133),
                                      (0.0, 0.0225, 0.2133),
                                      (0.0, -0.0, 0.2133)],
                                   degree=1,
                                   knot=[142, 162, 166, 175, 184, 188, 192, 201, 210, 215, 221, 227, 232, 236])

        xz_hinge_repr_shape = cmds.listRelatives(xz_up_repr, children=True, shapes=True)[0]
        cmds.setAttr(xz_hinge_repr_shape+'.overrideEnabled', 1)
        cmds.setAttr(xz_hinge_repr_shape+'.overrideColor', 6)
        cmds.rename(xz_hinge_repr_shape, 'IKhingeAxisRepresenationShape1')
        addShapes(representationTransform, xz_hinge_repr)

    if upFrontAxes == 'YX':
        yx_up_repr = cmds.curve(p=[(-0.0, 0.0, 0.0),
                                   (-0.0, 0.2133, 0.0),
                                   (0.0225, 0.2133, -0.0),
                                   (-0.0, 0.2751, 0.0),
                                   (-0.0225, 0.2133, 0.0),
                                   (-0.0, 0.2133, 0.0),
                                   (-0.0, 0.2133, -0.0225),
                                   (-0.0, 0.2751, 0.0),
                                   (-0.0, 0.2133, 0.0225),
                                   (0.0225, 0.2133, -0.0),
                                   (-0.0, 0.2133, -0.0225),
                                   (-0.0225, 0.2133, 0.0),
                                   (-0.0, 0.2133, 0.0225),
                                   (-0.0, 0.2133, 0.0)],
                               degree=1,
                               knot=[142, 162, 166, 175, 184, 188, 192, 201, 210, 215, 221, 227, 232, 236])

        yx_up_repr_shape = cmds.listRelatives(yx_up_repr, children=True, shapes=True)[0]
        cmds.setAttr(yx_up_repr_shape+'.overrideEnabled', 1)
        cmds.setAttr(yx_up_repr_shape+'.overrideColor', 14)
        cmds.rename(yx_up_repr_shape, 'IKhingeAxisRepresenationShape')
        addShapes(representationTransform, yx_up_repr)

        yx_hinge_repr = cmds.curve(p=[(0.0, 0.0, 0.0),
                                      (0.2133, 0.0, -0.0),
                                      (0.2133, -0.0225, -0.0),
                                      (0.2751, 0.0, -0.0),
                                      (0.2133, 0.0225, -0.0),
                                      (0.2133, 0.0, -0.0),
                                      (0.2133, 0.0, -0.0225),
                                      (0.2751, 0.0, -0.0),
                                      (0.2133, 0.0, 0.0225),
                                      (0.2133, -0.0225, -0.0),
                                      (0.2133, 0.0, -0.0225),
                                      (0.2133, 0.0225, -0.0),
                                      (0.2133, 0.0, 0.0225),
                                      (0.2133, 0.0, -0.0)],
                                   degree=1,
                                   knot=[142, 162, 166, 175, 184, 188, 192, 201, 210, 215, 221, 227, 232, 236])

        yx_hinge_repr_shape = cmds.listRelatives(yx_up_repr, children=True, shapes=True)[0]
        cmds.setAttr(yx_hinge_repr_shape+'.overrideEnabled', 1)
        cmds.setAttr(yx_hinge_repr_shape+'.overrideColor', 13)
        cmds.rename(yx_hinge_repr_shape, 'IKhingeAxisRepresenationShape1')
        addShapes(representationTransform, yx_hinge_repr)

    if upFrontAxes == 'YZ':
        yz_up_repr = cmds.curve(p=[(0.0, 0.0, 0.0),
                                   (0.0, 0.2133, 0.0),
                                   (0.0, 0.2133, 0.0225),
                                   (0.0, 0.2751, 0.0),
                                   (0.0, 0.2133, -0.0225),
                                   (0.0, 0.2133, 0.0),
                                   (0.0225, 0.2133, 0.0),
                                   (0.0, 0.2751, 0.0),
                                   (-0.0225, 0.2133, 0.0),
                                   (0.0, 0.2133, 0.0225),
                                   (0.0225, 0.2133, 0.0),
                                   (0.0, 0.2133, -0.0225),
                                   (-0.0225, 0.2133, 0.0),
                                   (0.0, 0.2133, 0.0)],
                               degree=1,
                               knot=[142, 162, 166, 175, 184, 188, 192, 201, 210, 215, 221, 227, 232, 236])

        yz_up_repr_shape = cmds.listRelatives(yz_up_repr, children=True, shapes=True)[0]
        cmds.setAttr(yz_up_repr_shape+'.overrideEnabled', 1)
        cmds.setAttr(yz_up_repr_shape+'.overrideColor', 14)
        cmds.rename(yz_up_repr_shape, 'IKhingeAxisRepresenationShape')
        addShapes(representationTransform, yz_up_repr)

        yz_hinge_repr = cmds.curve(p=[(0.0, 0.0, 0.0),
                                      (0.0, 0.0, 0.2133),
                                      (0.0, -0.0225, 0.2133),
                                      (0.0, 0.0, 0.2751),
                                      (0.0, 0.0225, 0.2133),
                                      (0.0, 0.0, 0.2133),
                                      (0.0225, 0.0, 0.2133),
                                      (0.0, 0.0, 0.2751),
                                      (-0.0225, 0.0, 0.2133),
                                      (0.0, -0.0225, 0.2133),
                                      (0.0225, 0.0, 0.2133),
                                      (0.0, 0.0225, 0.2133),
                                      (-0.0225, 0.0, 0.2133),
                                      (0.0, 0.0, 0.2133)],
                                   degree=1,
                                   knot=[142, 162, 166, 175, 184, 188, 192, 201, 210, 215, 221, 227, 232, 236])

        yz_hinge_repr_shape = cmds.listRelatives(yz_up_repr, children=True, shapes=True)[0]
        cmds.setAttr(yz_hinge_repr_shape+'.overrideEnabled', 1)
        cmds.setAttr(yz_hinge_repr_shape+'.overrideColor', 6)
        cmds.rename(yz_hinge_repr_shape, 'IKhingeAxisRepresenationShape1')
        addShapes(representationTransform, yz_hinge_repr)

    if upFrontAxes == 'ZX':
        zx_up_repr = cmds.curve(p=[(-0.0, 0.0, 0.0),
                                   (-0.0, 0.0, 0.2133),
                                   (0.0225, 0.0, 0.2133),
                                   (-0.0, 0.0, 0.2751),
                                   (-0.0225, 0.0, 0.2133),
                                   (-0.0, 0.0, 0.2133),
                                   (-0.0, 0.0225, 0.2133),
                                   (-0.0, 0.0, 0.2751),
                                   (-0.0, -0.0225, 0.2133),
                                   (0.0225, 0.0, 0.2133),
                                   (-0.0, 0.0225, 0.2133),
                                   (-0.0225, 0.0, 0.2133),
                                   (-0.0, -0.0225, 0.2133),
                                   (-0.0, 0.0, 0.2133)],
                               degree=1,
                               knot=[142, 162, 166, 175, 184, 188, 192, 201, 210, 215, 221, 227, 232, 236])

        zx_up_repr_shape = cmds.listRelatives(zx_up_repr, children=True, shapes=True)[0]
        cmds.setAttr(zx_up_repr_shape+'.overrideEnabled', 1)
        cmds.setAttr(zx_up_repr_shape+'.overrideColor', 6)
        cmds.rename(zx_up_repr_shape, 'IKhingeAxisRepresenationShape')
        addShapes(representationTransform, zx_up_repr)

        zx_hinge_repr = cmds.curve(p=[(0.0, 0.0, 0.0),
                                      (0.2133, 0.0, 0.0),
                                      (0.2133, 0.0, -0.0225),
                                      (0.2751, 0.0, 0.0),
                                      (0.2133, 0.0, 0.0225),
                                      (0.2133, 0.0, 0.0),
                                      (0.2133, 0.0225, 0.0),
                                      (0.2751, 0.0, 0.0),
                                      (0.2133, -0.0225, 0.0),
                                      (0.2133, 0.0, -0.0225),
                                      (0.2133, 0.0225, 0.0),
                                      (0.2133, 0.0, 0.0225),
                                      (0.2133, -0.0225, 0.0),
                                      (0.2133, 0.0, 0.0)],
                                   degree=1,
                                   knot=[142, 162, 166, 175, 184, 188, 192, 201, 210, 215, 221, 227, 232, 236])

        zx_hinge_repr_shape = cmds.listRelatives(zx_up_repr, children=True, shapes=True)[0]
        cmds.setAttr(zx_hinge_repr_shape+'.overrideEnabled', 1)
        cmds.setAttr(zx_hinge_repr_shape+'.overrideColor', 13)
        cmds.rename(zx_hinge_repr_shape, 'IKhingeAxisRepresenationShape1')
        addShapes(representationTransform, zx_hinge_repr)

    if upFrontAxes == 'ZY':
        zy_up_repr = cmds.curve(p=[(-0.0, -0.0, 0.0),
                                   (-0.0, -0.0, 0.2133),
                                   (0.0, 0.0225, 0.2133),
                                   (-0.0, -0.0, 0.2751),
                                   (-0.0, -0.0225, 0.2133),
                                   (-0.0, -0.0, 0.2133),
                                   (-0.0225, -0.0, 0.2133),
                                   (-0.0, -0.0, 0.2751),
                                   (0.0225, -0.0, 0.2133),
                                   (0.0, 0.0225, 0.2133),
                                   (-0.0225, -0.0, 0.2133),
                                   (-0.0, -0.0225, 0.2133),
                                   (0.0225, -0.0, 0.2133),
                                   (-0.0, -0.0, 0.2133)],
                               degree=1,
                               knot=[142, 162, 166, 175, 184, 188, 192, 201, 210, 215, 221, 227, 232, 236])

        zy_up_repr_shape = cmds.listRelatives(zy_up_repr, children=True, shapes=True)[0]
        cmds.setAttr(zy_up_repr_shape+'.overrideEnabled', 1)
        cmds.setAttr(zy_up_repr_shape+'.overrideColor', 6)
        cmds.rename(zy_up_repr_shape, 'IKhingeAxisRepresenationShape')
        addShapes(representationTransform, zy_up_repr)

        zy_hinge_repr = cmds.curve(p=[(0.0, 0.0, 0.0),
                                      (-0.0, 0.2133, 0.0),
                                      (-0.0, 0.2133, -0.0225),
                                      (-0.0, 0.2751, 0.0),
                                      (-0.0, 0.2133, 0.0225),
                                      (-0.0, 0.2133, 0.0),
                                      (-0.0225, 0.2133, 0.0),
                                      (-0.0, 0.2751, 0.0),
                                      (0.0225, 0.2133, 0.0),
                                      (-0.0, 0.2133, -0.0225),
                                      (-0.0225, 0.2133, 0.0),
                                      (-0.0, 0.2133, 0.0225),
                                      (0.0225, 0.2133, 0.0),
                                      (-0.0, 0.2133, 0.0)],
                                   degree=1,
                                   knot=[142, 162, 166, 175, 184, 188, 192, 201, 210, 215, 221, 227, 232, 236])

        zy_hinge_repr_shape = cmds.listRelatives(zy_up_repr, children=True, shapes=True)[0]
        cmds.setAttr(zy_hinge_repr_shape+'.overrideEnabled', 1)
        cmds.setAttr(zy_hinge_repr_shape+'.overrideColor', 14)
        cmds.rename(zy_hinge_repr_shape, 'IKhingeAxisRepresenationShape1')
        addShapes(representationTransform, zy_hinge_repr)

    return representationTransform


def createRawCharacterTransformControl():
    '''
    Creates a raw curve control transform hierarchy to be used as the character root and world
    transform controls. It creates the world transform with the root transform below in hierarchy.
    '''
    worldTransform = cmds.curve(name='WORLD_CNTL', p=[(-0.0012, 0.0, 0.0),
                                                              (-0.0009, 0.0, -0.0005),
                                                              (-0.0009, 0.0, -0.0003),
                                                              (-0.0004, 0.0, -0.0004),
                                                              (-0.0003, 0.0, -0.0009),
                                                              (-0.0005, 0.0, -0.0009),
                                                              (0.0, 0.0, -0.0012),
                                                              (0.0005, 0.0, -0.0009),
                                                              (0.0003, 0.0, -0.0009),
                                                              (0.0004, 0.0, -0.0004),
                                                              (0.0009, 0.0, -0.0003),
                                                              (0.0009, 0.0, -0.0005),
                                                              (0.0013, 0.0, 0.0),
                                                              (0.0009, 0.0, 0.0005),
                                                              (0.0009, 0.0, 0.0003),
                                                              (0.0004, 0.0, 0.0004),
                                                              (0.0003, 0.0, 0.0009),
                                                              (0.0005, 0.0, 0.0009),
                                                              (0.0, 0.0, 0.0012),
                                                              (-0.0005, 0.0, 0.0009),
                                                              (-0.0003, 0.0, 0.0009),
                                                              (-0.0004, 0.0, 0.0004),
                                                              (-0.0009, 0.0, 0.0003),
                                                              (-0.0009, 0.0, 0.0005),
                                                              (-0.0012, 0.0, 0.0)],
                        degree=1,
                        knot=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24])

    cmds.setAttr(worldTransform+'.visibility', keyable=False, lock=True)

    worldTransform_shape = cmds.listRelatives(worldTransform, children=True, shapes=True)[0]
    cmds.setAttr(worldTransform_shape+'.overrideEnabled', 1)
    cmds.setAttr(worldTransform_shape+'.overrideColor', 3)
    cmds.rename(worldTransform_shape, 'world_cntrlShape')

    rootTransform = cmds.createNode('transform', name='ROOT_CNTL', parent=worldTransform, skipSelect=True)
    cmds.setAttr(rootTransform+'.visibility', keyable=False, lock=True)
    
    root_zd = cmds.curve(p=[(0.0003, -0.0, -0.0003),
                            (0.0002, -0.0, -0.0009),
                            (-0.0002, -0.0, -0.0009),
                            (-0.0003, -0.0, -0.0003)],
                        degree=1,
                        knot=[43, 48, 51, 56])

    root_zd_shape = cmds.listRelatives(root_zd, children=True, shapes=True)[0]
    cmds.setAttr(root_zd_shape+'.overrideEnabled', 1)
    cmds.setAttr(root_zd_shape+'.overrideColor', 6)
    cmds.rename(root_zd_shape, 'root_cntlZdShape')
    addShapes(rootTransform, root_zd)

    root_zu = cmds.curve(p=[(-0.0003, 0.0, 0.0003),
                            (-0.0002, 0.0, 0.0009),
                            (0.0002, 0.0, 0.0009),
                            (0.0003, 0.0, 0.0003)],
                        degree=1,
                        knot=[17, 22, 25, 30])

    root_zu_shape = cmds.listRelatives(root_zu, children=True, shapes=True)[0]
    cmds.setAttr(root_zu_shape+'.overrideEnabled', 1)
    cmds.setAttr(root_zu_shape+'.overrideColor', 6)
    cmds.rename(root_zu_shape, 'root_cntlZuShape')
    addShapes(rootTransform, root_zu)

    root_xd = cmds.curve(p=[(-0.0003, -0.0, -0.0003),
                            (-0.0009, -0.0, -0.0002),
                            (-0.0009, 0.0, 0.0002),
                            (-0.0003, 0.0, 0.0003)],
                        degree=1,
                        knot=[4, 9, 12, 17])

    root_xd_shape = cmds.listRelatives(root_xd, children=True, shapes=True)[0]
    cmds.setAttr(root_xd_shape+'.overrideEnabled', 1)
    cmds.setAttr(root_xd_shape+'.overrideColor', 13)
    cmds.rename(root_xd_shape, 'root_cntlXdShape')
    addShapes(rootTransform, root_xd)

    root_xu = cmds.curve(p=[(0.0003, 0.0, 0.0003),
                            (0.0009, 0.0, 0.0002),
                            (0.0009, -0.0, -0.0002),
                            (0.0003, -0.0, -0.0003)],
                        degree=1,
                        knot=[30, 35, 38, 43])

    root_xu_shape = cmds.listRelatives(root_xu, children=True, shapes=True)[0]
    cmds.setAttr(root_xu_shape+'.overrideEnabled', 1)
    cmds.setAttr(root_xu_shape+'.overrideColor', 13)
    cmds.rename(root_xu_shape, 'root_cntlXuShape')
    addShapes(rootTransform, root_xu)

    return [rootTransform, worldTransform]


def createModuleTransform(**kwargs):
    '''
    Creates the module transform control with standard attributes.
    Accepts attribute parameters if necessary.
    '''
    # Get the attribute values.
    namespace = kwargs['namespace'] if 'namespace' in kwargs else 'namespace'
    name = kwargs['name'] if 'name' in kwargs else 'module_transform'
    colour = kwargs['colour'] if 'colour' in kwargs else 10
    scale = kwargs['scale'] if 'scale' in kwargs else 0.26
    drawStyle = kwargs['drawStyle'] if 'drawStyle' in kwargs else 8
    drawOrtho = kwargs['drawOrtho'] if 'drawOrtho' in kwargs else 0
    drawThickness = kwargs['drawThickness'] if 'drawThickness' in kwargs else 2
    isOnlyControl = kwargs['isOnlyControl'] if 'isOnlyControl' in kwargs else False
    
    # Create the raw module transform.
    moduleHandle = load_xhandleShape(name='%s:%s' % (namespace, name), colour=24)
    cmds.setAttr(moduleHandle['shape']+'.localScaleX', scale)
    cmds.setAttr(moduleHandle['shape']+'.localScaleY', scale)
    cmds.setAttr(moduleHandle['shape']+'.localScaleZ', scale)
    cmds.setAttr(moduleHandle['shape']+'.drawStyle', drawStyle)
    cmds.setAttr(moduleHandle['shape']+'.drawOrtho', drawOrtho)
    cmds.setAttr(moduleHandle['shape']+'.wireframeThickness', drawThickness)
    
    # If the transform is to be created as a module transform control and not a simple control,
    if not isOnlyControl:
        
        # Add the scaling attributes to the module transform.
        cmds.addAttr(moduleHandle['transform'], attributeType='float', longName='globalScale',
                                                        hasMinValue=True, minValue=0.01, defaultValue=1, keyable=True)
        cmds.addAttr(moduleHandle['transform'], attributeType='float', longName='scaleFactor',
                                                                hasMinValue=True, minValue=0.01, defaultValue=1)
        # The 'finalScale' attribute outputs the result scale.
        cmds.addAttr(moduleHandle['transform'], attributeType='float', longName='finalScale')
        
        # Add the scaling factor to be used with "globalScale".
        moduleHandle['scaleFactor'] = cmds.createNode('multDoubleLinear', name='%s:moduleScalingFactor_mult' % namespace)
        cmds.connectAttr(moduleHandle['transform']+'.globalScale', moduleHandle['scaleFactor']+'.input1')
        cmds.connectAttr(moduleHandle['transform']+'.scaleFactor', moduleHandle['scaleFactor']+'.input2')
        cmds.connectAttr(moduleHandle['scaleFactor']+'.output', moduleHandle['transform']+'.finalScale')
        
        # Connect the size for the transform.
        cmds.connectAttr(moduleHandle['transform']+'.finalScale', moduleHandle['transform']+'.scaleX')
        cmds.connectAttr(moduleHandle['transform']+'.finalScale', moduleHandle['transform']+'.scaleY')
        cmds.connectAttr(moduleHandle['transform']+'.finalScale', moduleHandle['transform']+'.scaleZ')
    
    lockHideChannelAttrs(moduleHandle['transform'], 's', 'v', keyable=False)
    
    return moduleHandle
    
    
def load_xhandleShape(*args, **kwargs):
    '''
    Creates a custom locator control shape. This shape can be parented to an input transform
    "transformName" or else a new one can be created for it.
    '''
    if 'transform' in kwargs:
        transform = kwargs['transform'] # If the xhandleShape is to be created under an input transform.
    elif len(args) > 0:
        transform = args[0]
    else:
        transform = None
    
    if 'name' in kwargs:
        name = kwargs['name']
    elif len(args) > 1:
        name = args[1]
    elif transform != None:
        name = transform
    else:
        name = 'xhandle'
        
    if not cmds.objExists(transform or ''):     # If transform is set to None, there'll be an error.
        transform = None
        
    if 'colour' in kwargs:
        colour = kwargs['colour']
    elif len(args) > 2:
        colour = args[2]
    else:
        colour = 1
        
    if 'transformOnly' in kwargs:
        transformOnly = kwargs['transformOnly']
    else:
        transformOnly = False
    
    xhandle = {}
    
    xhandle['shape'] = cmds.createNode('xhandleShape', name=name+'Shape', parent=transform, skipSelect=True)

    cmds.setAttr(xhandle['shape']+'.overrideEnabled', 1)
    cmds.setAttr(xhandle['shape']+'.overrideColor', colour)
    cmds.setAttr(xhandle['shape']+'.wireframeThickness', 3)

    lockHideChannelAttrs(xhandle['shape'], 'localScale', 'localPosition', keyable=False)
    
    # Get the transform above the xhandleShape.
    xhandle['transform'] = cmds.listRelatives(xhandle['shape'], parent=True, type='transform')[0]
    
    # Create the pre-transform for the xhandleShape's transform.
    if not transformOnly:
        
        # Set the name for the pre-transform.
        nameTokens = transform.split(':') if transform else name.split(':') 
        
        # Get the namespace.
        namespace = nameTokens[0] if len(nameTokens) > 1 else ''
        
        # Get the node name tokens (separated by underscores)
        nodeNameTokens = nameTokens[-1].split('_')
        
        # Modify the last name token with a "pre" prefix.
        partName = 'pre%s' % nodeNameTokens[-1].capitalize()
        
        # Get the new node name to be used.
        nodeName = '%s_%s' % ('_'.join(nodeNameTokens[:-1]), partName) if len(nodeNameTokens) > 1 else partName
        
        # Set the new full name for the pre-transform.
        fullName = '%s:%s' % (namespace, nodeName)
        
        # Create the pre-transform for the xhandle.
        xhandle['preTransform'] = cmds.createNode('transform', name=fullName)
        align(xhandle['transform'], xhandle['preTransform'])
    
        # Get the existing parent for the transform for xhandleShape, if it exists (for input transform).
        parent = cmds.listRelatives(xhandle['transform'], parent=True, type='transform')
        if parent:
            cmds.parent(xhandle['preTransform'], parent[0])
        
        # Parent the xhandle.
        cmds.parent(xhandle['transform'], xhandle['preTransform'])
    
    
    return xhandle