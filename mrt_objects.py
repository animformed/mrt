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

import maya.cmds as cmds
import maya.mel as mel
import os

# For locking and hiding channel box attributes on input transforms.
from mrt_functions import lockHideChannelAttrs


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
    
    segment['curve'] = cmds.curve(p=([1, 0, 0], [-1, 0, 0]), degree=1, name='segmentCurve')

    lockHideChannelAttrs(segment['curve'], 't', 'r', 's', 'v', keyable=False)

    shape = cmds.listRelatives(segment['curve'], children=True, shapes=True)[0]
    cmds.setAttr(shape+'.overrideEnabled', 1)
    cmds.setAttr(shape+'.overrideColor', modHandleColour)
    segment['curveShape'] = cmds.rename(shape, 'segmentCurveShape')

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
        cmds.rename(representationZShape, 'orient_repr_transform_Z_Shape')
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
        cmds.rename(representationYShape, 'orient_repr_transform_Y_Shape')
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
        cmds.rename(representationYShape, 'orient_repr_transform_Y_Shape')
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
        cmds.rename(representationXShape, 'orient_repr_transform_X_Shape')
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
        cmds.rename(representationZShape, 'orient_repr_transform_Z_Shape')
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
        cmds.rename(representationXShape, 'orient_repr_transform_X_Shape')
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

    orient_repr_Y = cmds.curve(p=[(0.0, 0.0, 0.0),
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
                                  degree=1,
                                  knot=[142, 162, 166, 175, 184, 188, 192, 201, 210, 215, 221, 227, 232, 236])

    orient_repr_YShape = cmds.listRelatives(orient_repr_Y, children=True, shapes=True)[0]
    cmds.setAttr(orient_repr_YShape+'.overrideEnabled', 1)
    cmds.setAttr(orient_repr_YShape+'.overrideColor', 14)
    addShapes(orientationTransform, orient_repr_Y)

    orient_repr_X = cmds.curve(p=[(0.0, 0.0, 0.0),
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
                                  degree=1,
                                  knot=[142, 162, 166, 175, 184, 188, 192, 201, 210, 215, 221, 227, 232, 236])

    orient_repr_XShape = cmds.listRelatives(orient_repr_X, children=True, shapes=True)[0]
    cmds.setAttr(orient_repr_XShape+'.overrideEnabled', 1)
    cmds.setAttr(orient_repr_XShape+'.overrideColor', 13)
    addShapes(orientationTransform, orient_repr_X)

    orient_repr_Z = cmds.curve(p=[(0.0, -0.0, 0.0),
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
                                  degree=1,
                                  knot=[142, 162, 166, 175, 184, 188, 192, 201, 210, 215, 221, 227, 232, 236])

    orient_repr_ZShape = cmds.listRelatives(orient_repr_Z, children=True, shapes=True)[0]
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

        x_repr = cmds.curve(p=[(0.1191, 0.0, 0.0),
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
                            degree=1,
                            knot=[12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23])

        x_reprShape = cmds.listRelatives(x_repr, children=True, shapes=True)[0]
        cmds.setAttr(x_reprShape+'.overrideEnabled', 1)
        cmds.setAttr(x_reprShape+'.overrideColor', 13)
        addShapes(hierarchyRepresentation, x_repr)

    if aimAxis == 'Y':

        y_repr = cmds.curve(p=[(0.0, 0.1191, 0.0),
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
                            degree=1,
                            knot=[12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23])

        y_reprShape = cmds.listRelatives(y_repr, children=True, shapes=True)[0]
        cmds.setAttr(y_reprShape+'.overrideEnabled', 1)
        cmds.setAttr(y_reprShape+'.overrideColor', 14)
        addShapes(hierarchyRepresentation, y_repr)

    if aimAxis == 'Z':

        z_repr = cmds.curve(p=[(0.0, 0.0, 0.1191),
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
                            degree=1,
                            knot=[12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23])

        z_reprShape = cmds.listRelatives(y_repr, children=True, shapes=True)[0]
        cmds.setAttr(z_reprShape+'.overrideEnabled', 1)
        cmds.setAttr(z_reprShape+'.overrideColor', 6)
        addShapes(hierarchyRepresentation, z_repr)

    return hierarchyRepresentation


def createRawSplineAdjustCurveTransform(modHandleColour):
    '''
    
    '''
    splineAdjustCurvePreTransform = cmds.createNode('transform', name='spline_adjustCurve_preTransform')
    splineAdjustCurveTransform = cmds.curve(name='spline_adjustCurve_transform',
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

    splineAdjustCurveShape = cmds.listRelatives(splineAdjustCurveTransform, children=True, shapes=True)[0]
    cmds.setAttr(splineAdjustCurveShape+'.overrideEnabled', 1)
    cmds.setAttr(splineAdjustCurveShape+'.overrideColor', modHandleColour)
    cmds.rename(splineAdjustCurveShape, 'spline_adjustCurve_transformShape')

    return splineAdjustCurvePreTransform, splineAdjustCurveTransform


def createRawLocalAxesInfoRepresentation():
    axesInfoPreTransform = cmds.createNode('transform', name='localAxesInfoRepr_preTransform')

    axesInfoTransform = cmds.createNode('transform', name='localAxesInfoRepr', parent=axesInfoPreTransform)
    lockHideChannelAttrs(axesInfoTransform, 't', 'r', 's', 'v', keyable=False)

    repr_X = cmds.curve(p=[(-0.0, 0.0, 0.0), (0.8325, 0.0, 0.0)], knot=[0, 0], degree=1)
    repr_X_shape = cmds.listRelatives(repr_X, children=True, shapes=True)[0]
    cmds.setAttr(repr_X_shape+'.overrideEnabled', 1)
    cmds.setAttr(repr_X_shape+'.overrideColor', 13)
    cmds.rename(repr_X_shape, 'localAxesInfoRepr_XShape')
    addShapes(axesInfoTransform, repr_X)

    repr_Y = cmds.curve(p=[(0.0, -0.0, 0.0), (0.0, 0.8325, 0.0)], knot=[0, 0], degree=1)
    repr_Y_shape = cmds.listRelatives(repr_Y, children=True, shapes=True)[0]
    cmds.setAttr(repr_Y_shape+'.overrideEnabled', 1)
    cmds.setAttr(repr_Y_shape+'.overrideColor', 14)
    cmds.rename(repr_Y_shape, 'localAxesInfoRepr_YShape')
    addShapes(axesInfoTransform, repr_Y)

    repr_Z = cmds.curve(p=[(0.0, 0.0, -0.0), (0.0, 0.0, 0.8325)], knot=[0, 0], degree=1)
    repr_Z_shape = cmds.listRelatives(repr_Z, children=True, shapes=True)[0]
    cmds.setAttr(repr_Z_shape+'.overrideEnabled', 1)
    cmds.setAttr(repr_Z_shape+'.overrideColor', 6)
    cmds.rename(repr_Z_shape, 'localAxesInfoRepr_ZShape')
    addShapes(axesInfoTransform, repr_Z)

    return axesInfoPreTransform, axesInfoTransform

def createRawIKPreferredRotationRepresentation(planeAxis):

    representationTransform = cmds.curve(name='IKPreferredRotationRepr', p=[(-0.0, -0.8197, -0.17),
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

    representationShape = cmds.listRelatives(representationTransform, children=True, shapes=True)[0]
    cmds.setAttr(representationShape+'.overrideEnabled', 1)
    if planeAxis == 'X':
        cmds.setAttr(representationShape+'.overrideColor', 13)
    if planeAxis == 'Y':
        cmds.setAttr(representationShape+'.overrideColor', 14)
    if planeAxis == 'Z':
        cmds.setAttr(representationShape+'.overrideColor', 6)
    cmds.rename(representationShape, 'IKPreferredRotationReprShape')

    return representationTransform


def createRawIKhingeAxisRepresenation(upFrontAxes):

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
        cmds.rename(xy_up_repr_shape, 'IKhingeAxisRepresenation_upAxis_Shape')
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
        cmds.rename(xy_hinge_repr_shape, 'IKhingeAxisRepresenation_hingeAxis_Shape')
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
        cmds.rename(xz_up_repr_shape, 'IKhingeAxisRepresenation_upAxis_Shape')
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
        cmds.rename(xz_hinge_repr_shape, 'IKhingeAxisRepresenation_hingeAxis_Shape')
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
        cmds.rename(yx_up_repr_shape, 'IKhingeAxisRepresenation_upAxis_Shape')
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
        cmds.rename(yx_hinge_repr_shape, 'IKhingeAxisRepresenation_hingeAxis_Shape')
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
        cmds.rename(yz_up_repr_shape, 'IKhingeAxisRepresenation_upAxis_Shape')
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
        cmds.rename(yz_hinge_repr_shape, 'IKhingeAxisRepresenation_hingeAxis_Shape')
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
        cmds.rename(zx_up_repr_shape, 'IKhingeAxisRepresenation_upAxis_Shape')
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
        cmds.rename(zx_hinge_repr_shape, 'IKhingeAxisRepresenation_hingeAxis_Shape')
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
        cmds.rename(zy_up_repr_shape, 'IKhingeAxisRepresenation_upAxis_Shape')
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
        cmds.rename(zy_hinge_repr_shape, 'IKhingeAxisRepresenation_hingeAxis_Shape')
        addShapes(representationTransform, zy_hinge_repr)

    return representationTransform


def createRawCharacterTransformControl():

    worldTransform = cmds.curve(name='__world_transform', p=[(-0.0012, 0.0, 0.0),
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

    cmds.setAttr(worldTransform+'.visibility', keyable=False)
    cmds.setAttr(rootTransform+'.visibility', keyable=False, lock=True)

    worldTransform_shape = cmds.listRelatives(worldTransform, children=True, shapes=True)[0]
    cmds.setAttr(worldTransform_shape+'.overrideEnabled', 1)
    cmds.setAttr(worldTransform_shape+'.overrideColor', 3)
    cmds.rename(worldTransform_shape, '__world_transformShape')

    rootTransform = cmds.createNode('transform', name='__root_transform', parent=worldTransform, skipSelect=True)

    root_zd = cmds.curve(p=[(0.0003, -0.0, -0.0003),
                            (0.0002, -0.0, -0.0009),
                            (-0.0002, -0.0, -0.0009),
                            (-0.0003, -0.0, -0.0003)],
                        degree=1,
                        knot=[43, 48, 51, 56])

    root_zd_shape = cmds.listRelatives(root_zd, children=True, shapes=True)[0]
    cmds.setAttr(root_zd_shape+'.overrideEnabled', 1)
    cmds.setAttr(root_zd_shape+'.overrideColor', 6)
    cmds.rename(root_zd_shape, '__root_transform_zdShape')
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
    cmds.rename(root_zu_shape, '__root_transform_zuShape')
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
    cmds.rename(root_xd_shape, '__root_transform_xdShape')
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
    cmds.rename(root_xu_shape, '__root_transform_xuShape')
    addShapes(rootTransform, root_xu)

    return [rootTransform, worldTransform]


def load_xhandleShape(transformName, modHandleColour, createWithTransform=False):
    if createWithTransform:
        xhandle_shape = cmds.createNode('xhandleShape', name=transformName+'Shape', skipSelect=True)
    else:
        xhandle_shape = cmds.createNode('xhandleShape', name=transformName+'Shape', parent=transformName, skipSelect=True)
    cmds.setAttr(xhandle_shape+'.overrideEnabled', 1)
    cmds.setAttr(xhandle_shape+'.overrideColor', modHandleColour)

    lockHideChannelAttrs(xhandle_shape, 'localScale', 'localPosition', keyable=False)

    xhandle_parent = cmds.listRelatives(xhandle_shape, parent=True, type='transform')[0]
    return [xhandle_shape, xhandle_parent]
