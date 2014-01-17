import maya.cmds as cmds
import maya.mel as mel
import mrt_UI

def moduleSelectionFromTreeView():
	active_selection = []
	selection = cmds.treeView('__MRT_treeView_SceneModulesUI', query=True, selectItem=True)
	if selection:
		for select in selection:
			if 'SplineNode' in select:
				select = select+':splineStartHandleTransform'
			else:
				select = select+':module_transform'
			active_selection.append(select)
		cmds.select(active_selection, replace=True)
		cmds.setToolTo('moveSuperContext')
	else:
		cmds.select(clear=True)

def treeViewButton_1_Action(item, state):
	cmds.lockNode(item+':module_container', lock=False, lockUnpublished=False)
	if state == '0':
		cmds.setAttr(item+':moduleGrp.visibility', 0)
		if cmds.objExists(item+':proxyGeometryGrp'):
			cmds.setAttr(item+':proxyGeometryGrp.visibility', 0)
			cmds.treeView('__MRT_treeView_SceneModulesUI', edit=True, buttonState=[item, 2, 'buttonUp'])
			cmds.treeView('__MRT_treeView_SceneModulesUI', edit=True, buttonTransparencyColor=[item, 2, 0.65, 0.71, 0.90])
		cmds.treeView('__MRT_treeView_SceneModulesUI', edit=True, buttonTransparencyColor=[item, 1, 0.71, 0.66, 0.56])
	if state == '1':
		cmds.setAttr(item+':moduleGrp.visibility', 1)
		if cmds.objExists(item+':proxyGeometryGrp'):
			cmds.setAttr(item+':proxyGeometryGrp.visibility', 1)
			cmds.treeView('__MRT_treeView_SceneModulesUI', edit=True, buttonState=[item, 2, 'buttonDown'])
			cmds.treeView('__MRT_treeView_SceneModulesUI', edit=True, buttonTransparencyColor=[item, 2, 0.57, 0.66, 1.0])
		cmds.treeView('__MRT_treeView_SceneModulesUI', edit=True, buttonTransparencyColor=[item, 1, 0.85, 0.66, 0.27])
	cmds.lockNode(item+':module_container', lock=True, lockUnpublished=True)

def treeViewButton_2_Action(item, state):
	itemVisibility = cmds.getAttr(item+':moduleGrp.visibility')
	if itemVisibility:
		if state == '0':
			cmds.setAttr(item+':proxyGeometryGrp.visibility', 0)
			cmds.treeView('__MRT_treeView_SceneModulesUI', edit=True, buttonTransparencyColor=[item, 2, 0.65, 0.71, 0.90])
		if state == '1':
			cmds.setAttr(item+':proxyGeometryGrp.visibility', 1)
			cmds.treeView('__MRT_treeView_SceneModulesUI', edit=True, buttonTransparencyColor=[item, 2, 0.57, 0.66, 1.0])

def treeViewButton_3_Action(item, state):
	if state == '0':
		cmds.setAttr(item+':proxyGeometryGrp.overrideDisplayType', 0)
		cmds.treeView('__MRT_treeView_SceneModulesUI', edit=True, buttonTransparencyColor=[item, 3, 0.68, 0.85, 0.90])
	if state == '1':
		cmds.setAttr(item+':proxyGeometryGrp.overrideDisplayType', 2)
		cmds.treeView('__MRT_treeView_SceneModulesUI', edit=True, buttonTransparencyColor=[item, 3, 0.42, 0.87, 1.0])

def processItemRenameForTreeViewList(itemName, newName):
	#---USE_THE_UI_FUNCTIONALITY_IN_EDIT_TAB_FOR_RENAMING---#
	#TO_BE_MODIFIED_FOR_FUTURE_RELEASE#
	#cmds.treeView('__MRT_treeView_SceneModulesUI', edit=True, clearSelection=True)
	cmds.warning('Please use the \"Rename Selected Module\" feature below')
	return ""
