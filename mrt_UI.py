# *************************************************************************************************************
#
#    mrt_UI.py - Main UI source for modular rigging tools for maya. Contains the UI class, and its methods
#                called during runtime events and user commands.
#
#    Can be modified or copied for your own purpose. Please keep updating it for use with future versions
#    of Maya. This was originally written for Maya 2011, and updated for 2013 and then for 2014.
#
#    Written by Himanish Bhattacharya 
#
# *************************************************************************************************************

import maya.cmds as cmds
import maya.mel as mel

import mrt_module
import mrt_objects as objects
import mrt_functions as mfunc
import mrt_controlRig

import time, math, re, os, fnmatch, cPickle, copy, sys, random, webbrowser
from functools import partial


_maya_version = mfunc.returnMayaVersion()

# Define callbacks for "treeView" UI commands. For maya versions < 2013, the callbacks
# had to be in MEL. This was updated in 2013. I'm defining them here since they'll be
# available globally.

def treeViewButton_1_Action(item, state):
    '''
    Callback for first left button for the scene module list treeView item. It toggles
    the visibility of the scene module item and its proxy geometry, if it exists.
    '''
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
    '''
    Callback for middle button for the scene module list treeView item. It specifically
    toggles the visibility of proxy geometry for the scene module module item. The button for
    this callback is enabled only if the proxy geometry exists for the module item.
    '''
	itemVisibility = cmds.getAttr(item+':moduleGrp.visibility')
    
	if itemVisibility:
		if state == '0':
			cmds.setAttr(item+':proxyGeometryGrp.visibility', 0)
			cmds.treeView('__MRT_treeView_SceneModulesUI', edit=True, buttonTransparencyColor=[item, 2, 0.65, 0.71, 0.90])
		if state == '1':
			cmds.setAttr(item+':proxyGeometryGrp.visibility', 1)
			cmds.treeView('__MRT_treeView_SceneModulesUI', edit=True, buttonTransparencyColor=[item, 2, 0.57, 0.66, 1.0])


def treeViewButton_3_Action(item, state):
    '''
    Callback for right button for the scene module list treeView item. It changes the 
    display type for the module item's proxy geometry between "Normal" and "Reference".
    Used to enable / disable the selection for a module's proxy geometry, if it exists.
    '''
	if state == '0':
		cmds.setAttr(item+':proxyGeometryGrp.overrideDisplayType', 0)
		cmds.treeView('__MRT_treeView_SceneModulesUI', edit=True, buttonTransparencyColor=[item, 3, 0.68, 0.85, 0.90])
	if state == '1':
		cmds.setAttr(item+':proxyGeometryGrp.overrideDisplayType', 2)
		cmds.treeView('__MRT_treeView_SceneModulesUI', edit=True, buttonTransparencyColor=[item, 3, 0.42, 0.87, 1.0])


def processItemRenameForTreeViewList(itemName, newName):
    '''
    Called when a user edits a module item's name in the scene module list treeView.
    To be implemented.
    '''
	#---USE_THE_UI_FUNCTIONALITY_IN_EDIT_TAB_FOR_RENAMING---#
	#TO_BE_MODIFIED_FOR_FUTURE_RELEASE#
	#cmds.treeView('__MRT_treeView_SceneModulesUI', edit=True, clearSelection=True)
	cmds.warning('Please use the \"Rename Selected Module\" feature below')
	return ""

def moduleSelectionFromTreeView():
    '''
    Runs when a module's entry in the scene modules treeView is selected. Selects the module
    in the entry by selecting its module transform.
    '''
    active_selection = []
    selection = cmds.treeView('__MRT_treeView_SceneModulesUI', query=True, selectItem=True)
    
    if len(selection):
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

# Now declare Mel and Python UI callbacks calling the defined functions above,
# depending on the maya's version.

if _maya_version >=2013:
    from mrt_sceneCallbacks import *
    def moduleSelectionFromTreeViewCallback():
        moduleSelectionFromTreeView()
    def treeViewButton_1_ActionCallback(item, state):
        treeViewButton_1_Action(item, state)
    def treeViewButton_2_ActionCallback(item, state):
        treeViewButton_2_Action(item, state)
    def treeViewButton_3_ActionCallback(item, state):
        treeViewButton_3_Action(item, state)
    def processItemRenameForTreeViewListCallback(itemName, newName):
        cmds.warning('MRT Error: Please use the \"Rename Selected Module\" feature below')
        returnStr = processItemRenameForTreeViewList(itemName, newName)
        return returnStr
else:
    mel.eval('python("try:\\n\\tfrom MRT.mrt_sceneCallbacks import *\\nexcept ImportError:\\n\\tpass");')

    mel.eval('global proc moduleSelectionFromTreeViewCallback(){python("moduleSelectionFromTreeView()");}')
    mel.eval('global proc treeViewButton_1_ActionCallback(string $item, int $state) \
    {python("treeViewButton_1_Action(\'" + $item + "\', \'" + $state + "\')");}')
    mel.eval('global proc treeViewButton_2_ActionCallback(string $item, int $state) \
    {python("treeViewButton_2_Action(\'" + $item + "\', \'" + $state + "\')");}')
    mel.eval('global proc treeViewButton_3_ActionCallback(string $item, int $state) \
    {python("treeViewButton_3_Action(\'" + $item + "\', \'" + $state + "\')");}')
    mel.eval('global proc string processItemRenameForTreeViewListCallback(string $itemName, string $newName) \
    {string $returnStr = python("processItemRenameForTreeViewList(\'" + $itemName + "\', \'" + $newName + "\')");\
                                                                                            return $returnStr;}')

class MRT_UI(object):
    '''
    Main UI class
    '''
    def __init__(self):
        cmds.undoInfo(stateWithoutFlush=False)
        # Dictionary to hold UI elements by key.
        self.module_collectionList = {}
        self.charTemplateList = {}
        self.uiVars = {}
        self.createTabFrames = []
        self.editTabFrames = []
        self.animateTabFrames = []
        self.treeViewSelection_list = {}
        self.controlRiggingOptionsList = {}
        self.controlParentSwitchGrp = None
        self.existingParentSwitchTargets = []
        self.c_jobNum = None
        # Dictionary to hold module creation queue.
        self.modules = {}
        # Check if the main UI window exists; if true, delete it.
        for ui in ['mrt_UI_window',
                   'mrt_collectionDescription_input_UI_window',
                   'mrt_collection_noDescpError_UI_window',
                   'mrt_loadCollectionClearMode_setting_UI_window',
                   'mrt_loadCollectionDirectoryClearMode_setting_UI_window',
                   'mrt_collectionDescription_edit_UI_window',
                   'mrt_editCollection_noDescpError_UI_window',
                   'mrt_deleteCollection_UI_window',
                   'mrt_installModuleCollection_UI_window',
                   'mrt_autoLoadSettingsUI_window',
                   'mrt_duplicateModuleAction_UI_window',
                   'mrt_charTemplateDescription_UI_window',
                   'mrt_charTemplate_noDescpError_UI_window',
                   'mrt_charTemplateLoadSettingsUI_window',
                   'mrt_displayCtrlRigOptions_UI_window',
                   'mrt_about_UI_window',
                   'mrt_displayIssues_UI_window']:
            try:
                cmds.deleteUI(ui)
            except:
                pass
    
        # Specify the width/height of the main window.
        self.width_Height = [400, 300]
        
        # Create the main window.
        self.uiVars['window'] = cmds.window('mrt_UI_window', title='Modular Rigging Tools', \
                                            widthHeight=self.width_Height, resizeToFitChildren=True, maximizeButton=False)
        try:
            cmds.windowPref('mrt_UI_window', remove=True)
        except:
            pass
        # Create a menu bar under main window, with two menu elements, 'File' and 'Help'.
        cmds.menuBarLayout()
        # The 'File' menu will have saving and loading file operations.
        self.uiVars['fileMenu_windowBar'] = cmds.menu(label='File')
        self.uiVars['autoLoad_moduleCollection_check'] = \
            cmds.menuItem(label='Auto-load settings for module collection(s)', command=self.autoLoadSettingsUIforCollections)
        cmds.menuItem(divider=True)
        self.uiVars['autoLoad_moduleCollection_selectDir'] = \
            cmds.menuItem(label='Select directory for loading saved collection(s)', \
                                    command=self.selectDirectoryForLoadingCollections)
        cmds.menuItem(optionBox=True, command=self.changeLoadCollectionDirectoryClearMode)
        cmds.menuItem(label='Select and load saved module collection(s)', command=self.loadSavedModuleCollections)
        cmds.menuItem(optionBox=True, command=self.changeLoadCollectionListClearMode)
        cmds.menuItem(divider=True)
        cmds.menuItem(label='Save selected module(s) as a collection', command=self.makeCollectionFromSceneTreeViewModulesUI)
        cmds.menuItem(label='Save all modules as a collection', \
                                  command=partial(self.makeCollectionFromSceneTreeViewModulesUI, allModules=True, auto=None))
        cmds.menuItem(divider=True)
        cmds.menuItem(label='Load saved character template(s)', command=self.loadSavedCharTemplates)
        cmds.menuItem(optionBox=True, command=self.changeLoadSettingsForCharTemplates)
        cmds.menuItem(divider=True)
        ##cmds.menuItem(label='Exit', command=('cmds.deleteUI(\"'+self.uiVars['window']+'\")'))
        cmds.menuItem(label='Exit', command=partial(self.closeWindow, self.uiVars['window']))
        # The 'window' menu will contains basic UI window operations.
        cmds.menu(label='Window')
        cmds.menuItem(label='Collapse all frames', command=self.collapseAllUIframes)
        cmds.menuItem(label='Expand all frames', command=self.expandAllUIframes)
        cmds.menuItem(divider=True)
        cmds.menuItem(label='Install shelf button', command=self.putShelfButtonForUI)
        cmds.menu(label='Misc')
        cmds.menuItem(label='Swap hinge node root and end handle positions', command=self.swapHingeNodeRootEndHandlePos)
        cmds.menuItem(label='Delete selected module proxy geometry', command=self.deleteSelectedProxyGeo)
        cmds.menuItem(label='Delete all proxy geometry for selected module', command=self.deleteAllProxyGeoForModule)
        cmds.menuItem(label='Delete history on all proxy geometry', command=self.deleteHistoryAllProxyGeo)
        cmds.menuItem(label='Purge auto-collection files on disk', command=self.purgeAutoCollections)
        cmds.menuItem(label='Create parent switch group for selected control handle', \
                                                                        command=self.createParentSwitchGroupforControlHandle)
        # The 'Help' menu will have general help options.
        cmds.menu(label='Help', helpMenu=True)
        cmds.menuItem(label='Documentation', \
                                      command=partial(self.openWebPage, 'http://www.animformed.net/home/mrt-documentation/'))
        cmds.menuItem(label='Tutorial/How To\'s', \
               command=partial(self.openWebPage, 'http://www.animformed.net/home/using-modular-rigging-tools-for-maya-p-i/'))
        cmds.menuItem(divider=True)
        cmds.menuItem(label='Extending MRT - Writing custom control rigs', \
                                          command=partial(self.openWebPage, 'http://www.animformed.net/home/extending-mrt/'))
        cmds.menuItem(divider=True)
        cmds.menuItem(label='Known Issues / Workarounds', command=self.display_mrt_issues)
        cmds.menuItem(divider=True)
        cmds.menuItem(label='About', command=self.display_mrt_about)

        # Set the parent to main window to create the main column layout.
        cmds.setParent(self.uiVars['window'])

        # Create the top level column layout.
        self.uiVars['topLevelColumnScroll'] = \
            cmds.scrollLayout(visible=True, childResizable=True, horizontalScrollBarThickness=0, width=430)
        self.uiVars['topLevelColumn'] = cmds.columnLayout(adjustableColumn=True, rowSpacing=3)

        # Create the tab layout to contain the 'create', 'edit' and 'animate' tabs.
        self.uiVars['tabs'] = cmds.tabLayout(innerMarginWidth=5, innerMarginHeight=5, childResizable=True, \
                                                                                tabsVisible=True, width=self.width_Height[0])
        # Call method to create items for the 'Create' tab.
        self.makeCreateTabControls()
        self.updateDefaultUserSpecifiedNameField()
        cmds.setParent(self.uiVars['tabs'])
        self.makeEditTabControls()
        cmds.setParent(self.uiVars['tabs'])
        self.makeRigTabControls()
        cmds.setParent(self.uiVars['tabs'])
        
        # FOR FUTURE #
        # self.makeAnimateTabControls()
        
        # Edit the tab layout for the tab labels.
        cmds.tabLayout(self.uiVars['tabs'], edit=True, tabLabelIndex=([1, 'Create'], [2, 'Edit'], [3, 'Rig']))

        cmds.showWindow(self.uiVars['window'])

        # DEPRECATED #
        # I didn't like the dock control on this haha. You want it? Enable and test it.
        # self.uiVars['dockWindow'] = cmds.dockControl('mrt_UI_dockWindow', label='Modular Rigging Tools',
        #                                                    area='left', content=self.uiVars['window'],
        #                                                    allowedArea=['left', 'right'])

        # Remove the main window from preferences.
        self.resetListHeightForSceneModulesUI()
        self.updateListForSceneModulesInUI()
        self.selectModuleInTreeViewUIfromViewport()
        self.createUIutilityScriptJobs()
        self.autoCollections_path = \
                           cmds.internalVar(userScriptDir=True)+'MRT/module_collections/auto-generated_character_collections'
        self.ui_preferences_path = cmds.internalVar(userScriptDir=True)+'MRT/mrt_uiPrefs'
        self.module_collectionList_path = cmds.internalVar(userScriptDir=True)+'MRT/mrt_collectionList'
        self.charTemplateList_path = cmds.internalVar(userScriptDir=True)+'MRT/mrt_charTemplateList'
        try:
            ui_preferences_file = open(self.ui_preferences_path, 'rb')
            ui_preferences = cPickle.load(ui_preferences_file)
            ui_preferences_file.close()
        except IOError:
            ui_preferences_file = open(self.ui_preferences_path, 'wb')
            ui_preferences = {}
            ui_preferences['startDirectoryForCollectionSave'] = \
                                               cmds.internalVar(userScriptDir=True)+'MRT/module_collections/user_collections'
            ui_preferences['defaultStartDirectoryForCollectionSave'] = \
                                               cmds.internalVar(userScriptDir=True)+'MRT/module_collections/user_collections'
            ui_preferences['directoryForAutoLoadingCollections'] = \
                                               cmds.internalVar(userScriptDir=True)+'MRT/module_collections/user_collections'
            ui_preferences['defaultDirectoryForAutoLoadingCollections'] = \
                                               cmds.internalVar(userScriptDir=True)+'MRT/module_collections/user_collections'
            ui_preferences['lastDirectoryForLoadingCollections'] = \
                                               cmds.internalVar(userScriptDir=True)+'MRT/module_collections/user_collections'
            ui_preferences['defaultLastDirectoryForLoadingCollections'] = \
                                               cmds.internalVar(userScriptDir=True)+'MRT/module_collections/user_collections'
            ui_preferences['directoryForSavingCharacterTemplates'] = \
                                               cmds.internalVar(userScriptDir=True)+'MRT/character_templates'
            ui_preferences['defaultDirectoryForSavingCharacterTemplates'] = \
                                               cmds.internalVar(userScriptDir=True)+'MRT/character_templates'
            ui_preferences['directoryForCharacterTemplates'] = cmds.internalVar(userScriptDir=True)+'MRT/character_templates'
            ui_preferences['defaultDirectoryForCharacterTemplates'] = \
                                               cmds.internalVar(userScriptDir=True)+'MRT/character_templates'
            ui_preferences['loadCharTemplateClearModeStatus'] = True
            ui_preferences['loadNewCharTemplatesToCurrentList'] = True
            ui_preferences['autoLoadPreviousCharTemplateListAtStartupStatus'] = True
            ui_preferences['autoLoadPreviousCollectionListAtStartupStatus'] = True
            ui_preferences['autoLoadNewSavedModuleCollectionToListStatus'] = True
            ui_preferences['loadCollectionDirectoryClearModeStatus'] = True
            ui_preferences['loadCollectionClearModeStatus'] = True
            cPickle.dump(ui_preferences, ui_preferences_file, cPickle.HIGHEST_PROTOCOL)
            ui_preferences_file.close()
        try:
            module_collectionList_file = open(self.module_collectionList_path, 'rb')
            module_collectionList = cPickle.load(module_collectionList_file)
            module_collectionList_file.close()
            if len(module_collectionList):
                if ui_preferences['autoLoadPreviousCollectionListAtStartupStatus']:
                    for (key, value) in module_collectionList.items():
                        if os.path.exists(value):
                            self.loadModuleCollectionsForUI([value])
                        else:
                            module_collectionList.pop(key)
            module_collectionList_file = open(self.module_collectionList_path, 'wb')
            cPickle.dump(module_collectionList, module_collectionList_file, cPickle.HIGHEST_PROTOCOL)
            module_collectionList_file.close()
        except IOError:
            module_collectionList = {}
            module_collectionList_file = open(self.module_collectionList_path, 'wb')
            cPickle.dump(module_collectionList, module_collectionList_file, cPickle.HIGHEST_PROTOCOL)
            module_collectionList_file.close()
        try:
            charTemplateList_file = open(self.charTemplateList_path, 'rb')
            charTemplateList = cPickle.load(charTemplateList_file)
            charTemplateList_file.close()
            if len(charTemplateList):
                if ui_preferences['autoLoadPreviousCharTemplateListAtStartupStatus']:
                    for (key, value) in charTemplateList.items():
                        if os.path.exists(value):
                            self.loadCharTemplatesForUI([value])
                        else:
                            charTemplateList.pop(key)
            charTemplateList_file = open(self.charTemplateList_path, 'wb')
            cPickle.dump(charTemplateList, charTemplateList_file, cPickle.HIGHEST_PROTOCOL)
            charTemplateList_file.close()
        except IOError:
            charTemplateList = {}
            charTemplateList_file = open(self.charTemplateList_path, 'wb')
            cPickle.dump(charTemplateList, charTemplateList_file, cPickle.HIGHEST_PROTOCOL)
            charTemplateList_file.close()
        selection = cmds.ls(selection=True)
        if selection:
            cmds.select(selection)
        cmds.undoInfo(stateWithoutFlush=True)

    def createParentSwitchGroupforControlHandle(self, *args):
        selection = cmds.ls(selection=True)
        if selection:
            selection = selection[-1]
        else:
            return
        if re.match('^MRT_character[A-Za-z0-9]*__\w+_handle$', selection):
            transformParent = cmds.listRelatives(selection, parent=True)
            if transformParent:
                if re.match(selection+'_grp', transformParent[0]):
                    cmds.warning('MRT Error: The selected control handle already has parent switch group. Skipping')
                    return
        else:
            cmds.warning('MRT Error: Invalid selection. Please select a valid control handle')
            return

        characterName = selection.partition('__')[0].partition('MRT_character')[2]
        selectionName = selection.partition('__')[2]
        selectionUserSpecName = re.split('_[A-Z]', selectionName)[0]
        rootJoint = 'MRT_character%s__%s_root_node_transform'%(characterName, selectionUserSpecName)

        # Create the group node which will receive the constraints from parent transforms.
        parentSwitch_grp = cmds.group(empty=True, name=selection + '_parentSwitch_grp')
        tempConstraint = cmds.parentConstraint(selection, parentSwitch_grp, maintainOffset=False)[0]
        cmds.delete(tempConstraint)
        # Add custom attributes to the group node, and create a child transform to contain the main transform
        # (for which the parent switch group is being created).
        cmds.addAttr(selection, attributeType='enum', longName='targetParents', enumName=' ', keyable=True)
        cmds.setAttr(selection+'.targetParents', lock=True)
        cmds.addAttr(parentSwitch_grp, dataType='string', longName='parentTargetList', keyable=False)
        cmds.setAttr(parentSwitch_grp+'.parentTargetList', 'None', type='string', lock=True)
        transform_grp = cmds.duplicate(parentSwitch_grp, parentOnly=True, name=selection+'_grp')[0]
        transformParent = cmds.listRelatives(selection, parent=True)
        if transformParent:
            cmds.parent(parentSwitch_grp, transformParent[0], absolute=True)
        cmds.parent(transform_grp, parentSwitch_grp, absolute=True)
        cmds.parent(selection, transform_grp, absolute=True)
        controlContainer = cmds.container(selection, query=True, findContainer=True)
        mfunc.addNodesToContainer(controlContainer, [parentSwitch_grp, transform_grp])

    def display_mrt_issues(self, *args):
    
        printString1 = ' Known Issues with Modular Rigging Tools for Maya' \
            '\n ------------------------------------------------'
        
        printString2 = '\n\n 1. If \'Mirror Instancing\' option is used for proxy geometry while creating mirrored modules,' \
            '\n it will yield mirrored geometry with opposing face normals after creating a character. Maya will issue' \
            '\n warning(s) while creating a character from modules, which is expected - Warning: Freeze transform with' \
            '\n negative scale will set the \'opposite\' attribute for these nodes. I haven\'t found a way around this yet,'\
            '\n but I suppose this is not a problem since this is only a display issue. You can avoid it by enabling' \
            '\n two-sided lighting by using lighting options under the viewport panel.'
        
        printString3 = '\n\n 2. When changing the \'proxy geometry draw\' attribute on a module transform for mirrored' \
            '\n modules, while using Maya 2013, I\'ve noticed the draw style sometimes doesn\'t update correctly for both' \
            '\n the mirrored modules in the viewport (Changing an attribute on one of the modules should automatically' \
            '\n affect its mirrored module). To fix this, simply try to set the attribute separately on the mirrored module.'
        
        printString4 = '\n\n 2. It is recommended that you put keyframes to assigned control(s) for a character hierarchy' \
            '\n while they\'re in reference only. MRT doesn\'t take into account if a control has keyframes and while' \
            '\n removing and reassigning a control rig to a character joint hiearachy, such keyframes would be lost.' \
            '\n Controls rigs are assigned to character hierarchies in its original scene file which is referenced and' \
            '\n then animated.'
        
        printString5 = '\n\n 4. MRT uses script jobs which are executed when you start Maya. These script jobs are run' \
            '\n from userSetup file, and so if they fail to run, please check if the userSetup file has any error. These' \
            '\n script jobs are necessary for e.g, when you\'re trying to modify some of the attributes on a module transform.'
        
        printString6 = '\n\n 5. Some of the control rig functionality uses the hair system (one with \"Dynamic prefix\").' \
            '\n For Maya 2013 and above, the classic maya hair has been replaced by nHair. Because of this, if you wish to' \
            '\n use any nDynamics, please check if there\'s an existing nucleus node in the scene, and then create a new' \
            '\n one for safer DG evaluation.'
        
        printString7 = '\n\n 6. While renaming a module, if an attribute editor is active/open (even if it\'s tabbed), you' \
            '\n might get an error in the command output, such as,\"showEditor.mel line ####: Value is out of range: 3\".' \
            '\n This is not a malfunction within Modular Rigging Tools, but the way the AE is updated within the Maya UI.' \
            '\n The module renaming will still work correctly.'
        
        printString8 = '\n\n 7. While adjusting the weight of control rig attributes on the character root transform, the' \
            '\n weight blending doesn\'t, work correctly as expected; it snaps to its full weight at between 0.1 ~ 0.3.' \
            '\n As far as I know, this is an issue with how the parent constraint is currently implemented, which is used' \
            '\n to connect the driver joint layer to its main joint hierarchy.'
        
        printString9 = '\n\n 8. At times, the Reverse IK Control might not behave correctly when applied to a leg joint' \
            '\n hierarchy in a character, where the joints may not transform as desired as you translate the IK control' \
            '\n handle. To fix it, simply detach and re-apply the control rig to the leg joint hierarchy.'
        
        printString10 = '\n\n 8. All Errors are reported as warnings here, since, an error would bring up the stack trace' \
            '\n if enabled, and it may confuse some users.'

        try:
            cmds.deleteUI('mrt_displayIssues_UI_window')
        except:
            pass
        self.uiVars['displayMrtIssuesWindow'] = cmds.window('mrt_displayIssues_UI_window', title='Known Issues', \
                                                                                        maximizeButton=False, sizeable=False)
        try:
            cmds.windowPref(self.uiVars['displayMrtIssuesWindow'], remove=True)
        except:
            pass
        self.uiVars['displayMrtIssues_columnLayout'] = cmds.columnLayout()
        self.uiVars['displayMrtIssues_scrollField'] = cmds.scrollField(text=printString1+
                                                                            printString2+
                                                                            printString3+
                                                                            printString4+
                                                                            printString5+
                                                                            printString6+
                                                                            printString7+
                                                                            printString8+
                                                                            printString9+
                                                                            printString10, editable=False, width=850,   \
                                                                            enableBackground=True, height=400, wordWrap=False)
        cmds.showWindow(self.uiVars['displayMrtIssuesWindow'])

    def display_mrt_about(self, *args):
        printString1 = '\n\t\t\tModular Rigging Tools v1.0\n\t\t\tfor Maya 2011 - 2013'
        printString2 = '\n\n\tWritten by Himanish Bhattacharya' \
            '\n\thimanish@animformed.net' \
            '\n\n\t________________________________________________' \
            '\n\n\tFor annoyances or bugs, contact me at, bugs@animformed.net\n'
        try:
            cmds.deleteUI('mrt_about_UI_window')
        except:
            pass
        self.uiVars['displayMrtAboutWindow'] = cmds.window('mrt_about_UI_window', title='About', maximizeButton=False, \
                                                                                                            sizeable=False)
        try:
            cmds.windowPref(self.uiVars['displayMrtAboutWindow'], remove=True)
        except:
            pass
        self.uiVars['displayMrtAbout_columnLayout'] = cmds.columnLayout()
        cmds.text(label=printString1, font='boldLabelFont')
        cmds.text(label=printString2)
        cmds.showWindow(self.uiVars['displayMrtAboutWindow'])

    def closeWindow(self, windowName, *args):
        cmds.deleteUI(windowName)

    def openWebPage(self, urlString, *args):
        webbrowser.open(urlString)

    def createUIutilityScriptJobs(self):
        mainWin = self.uiVars['window']
        cmds.scriptJob(event=['SelectionChanged', self.toggleEditMenuButtonsOnModuleSelection], parent=mainWin)
        cmds.scriptJob(event=['DagObjectCreated', self.updateListForSceneModulesInUI], parent=mainWin)
        cmds.scriptJob(event=['deleteAll', self.updateListForSceneModulesInUI], parent=mainWin)
        cmds.scriptJob(event=['SceneOpened', self.updateListForSceneModulesInUI], parent=mainWin)
        cmds.scriptJob(event=['SceneOpened', self.clearParentSwitchControlField], parent=mainWin)
        cmds.scriptJob(event=['deleteAll', self.clearParentSwitchControlField], parent=mainWin)
        cmds.scriptJob(event=['DagObjectCreated', self.clearParentSwitchControlField], parent=mainWin)
        cmds.scriptJob(event=['Undo', self.updateListForSceneModulesInUI], parent=mainWin)
        cmds.scriptJob(event=['Redo', self.updateListForSceneModulesInUI], parent=mainWin)
        cmds.scriptJob(conditionFalse=['SomethingSelected', self.updateListForSceneModulesInUI], parent=mainWin)
        cmds.scriptJob(event=['SelectionChanged', self.selectModuleInTreeViewUIfromViewport], parent=mainWin)
        cmds.scriptJob(event=['SelectionChanged', self.viewControlRigOptionsOnHierarchySelection], parent=mainWin)
        self.c_jobNum = cmds.scriptJob(uiDeleted=[mainWin, partial(mfunc.cleanup_MRT_actions, self.c_jobNum)])

    def purgeAutoCollections(self, *args):
        autoCollectionFiles = filter(lambda fileName:re.match('^character__[0-9]*\.mrtmc$', fileName), \
                                                                                    os.listdir(self.autoCollections_path))
        if len(autoCollectionFiles):
            for item in autoCollectionFiles:
                itemPath = self.autoCollections_path + '/' + item
                os.remove(itemPath)
            sys.stderr.write('%s file(s) were removed.\n'%(len(autoCollectionFiles)))
        else:
            sys.stderr.write('No auto-collection file(s) found.\n')

    def deleteSelectedProxyGeo(self, *args):
        selection = cmds.ls(selection=True)
        moduleProxies = []
        check = False
        if selection:
            for item in selection:
                if re.match('^MRT_\D+__\w+:\w+_transform_proxy_(bone|elbow)_geo$', item):
                    check = True
                    cmds.delete(item+'_preTransform')
                    moduleProxies.append(item)
            if moduleProxies:
                for item in moduleProxies:
                    parentProxyGrp = item.partition(':')[0]+':proxyGeometryGrp'
                    children = cmds.listRelatives(parentProxyGrp, allDescendents=True)
                    if not children:
                        cmds.delete(parentProxyGrp)
        if not check:
            cmds.warning('MRT Error: Please select a module proxy geometry.')

    def deleteAllProxyGeoForModule(self, *args):
        modules = []
        selection = cmds.ls(selection=True)
        if selection:
            for item in selection:
                moduleInfo = mfunc.stripMRTNamespace(item)
                if moduleInfo:
                    modules.append(moduleInfo)
            if modules:
                check = False
                for item in modules:
                    if cmds.objExists(item[0]+':proxyGeometryGrp'):
                        cmds.delete(item[0]+':proxyGeometryGrp')
                        check = True
                if not check:
                    cmds.warning('MRT Error: The module "%s" does not have proxy geometry. Skipping.'%item[0])
            else:
                cmds.warning('MRT Error: Please select a module.')
        else:
            cmds.warning('MRT Error: Please select a module.')

    def deleteHistoryAllProxyGeo(self, *args):
        proxyGrpList = []
        all_transforms = cmds.ls(type='transform')
        for transform in all_transforms:
            if re.match('\w+(:proxyGeometryGrp)', transform):
                proxyGrpList.append(transform)
        if proxyGrpList:
            cmds.delete(proxyGrpList, constructionHistory=True)
            cmds.warning('MRT Error: History deleted on all module proxy geometries.')
        else:
            cmds.warning('MRT Error: No module proxy geometry found.')

    def swapHingeNodeRootEndHandlePos(self, *args):
        selection = cmds.ls(selection=True)
        if not selection:
            sys.stderr.write('Please select a hinge node module.\n')
            return
        if selection:
            selection.reverse()
            selection = selection[0]
            namespaceInfo = mfunc.stripMRTNamespace(selection)
            if namespaceInfo:
                if not 'HingeNode' in namespaceInfo[0]:
                    sys.stderr.write('Please select a hinge node module.\n')
                    return
                
                rootPos = \
                cmds.xform(namespaceInfo[0]+':root_node_transform_control', query=True, worldSpace=True, translation=True)
                
                endPos = \
                cmds.xform(namespaceInfo[0]+':end_node_transform_control', query=True, worldSpace=True, translation=True)
                
                cmds.xform(namespaceInfo[0]+':root_node_transform_control', worldSpace=True, translation=endPos)
                cmds.xform(namespaceInfo[0]+':end_node_transform_control', worldSpace=True, translation=rootPos)
                for item in [namespaceInfo[0]+':root_node_transform_control', \
                             namespaceInfo[0]+':end_node_transform_control', \
                             namespaceInfo[0]+':node_1_transform_control']:
                    cmds.evalDeferred(partial(self.deferredSelectionUpdate, item), lowestPriority=True)
            else:
                sys.stderr.write('Please select a hinge node module.\n')
                return

    def deferredSelectionUpdate(self, selection):
        cmds.select(selection, replace=True)

    def autoLoadSettingsUIforCollections(self, *args):
        def setAutoLoadSettingsValues(*args):
            ui_preferences_file = open(self.ui_preferences_path, 'rb')
            ui_preferences = cPickle.load(ui_preferences_file)
            ui_preferences_file.close()
            
            loadAtStartup = \
            cmds.checkBox(self.uiVars['autoLoadPreviousCollectionListAtStartup_checkBox'], query=True, value=True)
            
            loadNewCollections = \
            cmds.checkBox(self.uiVars['autoLoadNewSavedModuleCollectionToList_checkBox'], query=True, value=True)
            
            ui_preferences['autoLoadPreviousCollectionListAtStartupStatus'] = loadAtStartup
            ui_preferences['autoLoadNewSavedModuleCollectionToListStatus'] = loadNewCollections
            ui_preferences_file = open(self.ui_preferences_path, 'wb')
            cPickle.dump(ui_preferences, ui_preferences_file, cPickle.HIGHEST_PROTOCOL)
            ui_preferences_file.close()
        try:
            cmds.deleteUI('mrt_autoLoadSettingsUI_window')
        except:
            pass
        self.uiVars['autoLoadSettingsUIwindow'] = cmds.window('mrt_autoLoadSettingsUI_window', \
                                                                    title='Auto-load settings for module collections', \
                                                                    width=90, maximizeButton=False, sizeable=False)
        try:
            cmds.windowPref('mrt_autoLoadSettingsUI_window', remove=True)
        except:
            pass
        self.uiVars['autoLoadSettingsWindowColumn'] = cmds.columnLayout(adjustableColumn=True)
        cmds.text(label='')
        ui_preferences_file = open(self.ui_preferences_path, 'rb')
        ui_preferences = cPickle.load(ui_preferences_file)
        ui_preferences_file.close()
        loadAtStartup = ui_preferences['autoLoadPreviousCollectionListAtStartupStatus']
        loadNewCollections = ui_preferences['autoLoadNewSavedModuleCollectionToListStatus']
        cmds.rowLayout(numberOfColumns=1, columnAttach=([1, 'left', 57]))
        self.uiVars['autoLoadPreviousCollectionListAtStartup_checkBox'] = \
            cmds.checkBox(label='Preserve and load current list at next startup', value=loadAtStartup, \
                                                                                changeCommand=setAutoLoadSettingsValues)
        cmds.setParent(self.uiVars['autoLoadSettingsWindowColumn'])
        cmds.rowLayout(numberOfColumns=1, columnAttach=([1, 'both', 60]), rowAttach=([1, 'top', 5]))
        self.uiVars['autoLoadNewSavedModuleCollectionToList_checkBox'] = \
            cmds.checkBox(label='Load new saved collection(s) to current list', value=loadNewCollections, \
                                                                                changeCommand=setAutoLoadSettingsValues)
        cmds.setParent(self.uiVars['autoLoadSettingsWindowColumn'])
        cmds.text(label='')
        cmds.rowLayout(numberOfColumns=1, columnAttach=([1, 'left', 120]))

        cmds.button(label='Close', width=120, command=partial(self.closeWindow, self.uiVars['autoLoadSettingsUIwindow']))
        cmds.setParent(self.uiVars['autoLoadSettingsWindowColumn'])
        cmds.text(label='')
        cmds.showWindow(self.uiVars['autoLoadSettingsUIwindow'])

    def changeLoadCollectionListClearMode(self, *args):
        def loadCollectionsFromSettingsWindow(*args):
            try:
                cmds.deleteUI('mrt_loadCollectionClearMode_setting_UI_window')
            except:
                pass
            self.loadSavedModuleCollections()

        def setLoadCollectionClearModeValue(*args):
            value = cmds.checkBox(self.uiVars['loadCollectionClearMode_checkBox'], query=True, value=True)
            ui_preferences_file = open(self.ui_preferences_path, 'rb')
            ui_preferences = cPickle.load(ui_preferences_file)
            ui_preferences_file.close()
            ui_preferences['loadCollectionClearModeStatus'] = value
            ui_preferences_file = open(self.ui_preferences_path, 'wb')
            cPickle.dump(ui_preferences, ui_preferences_file, cPickle.HIGHEST_PROTOCOL)
            ui_preferences_file.close()
        try:
            cmds.deleteUI('mrt_loadCollectionClearMode_setting_UI_window')
        except:
            pass
        self.uiVars['loadCollectionClearModeWindow'] = cmds.window('mrt_loadCollectionClearMode_setting_UI_window',  \
                                                                        title='Load module collections selectively', \
                                                                        height=50, maximizeButton=False, sizeable=False)
        try:
            cmds.windowPref('mrt_loadCollectionClearMode_setting_UI_window', remove=True)
        except:
            pass
        self.uiVars['loadCollectionClearModeWindowColumn'] = cmds.columnLayout(adjustableColumn=True)
        cmds.text(label='')
        cmds.frameLayout(visible=True, borderVisible=False, collapsable=False, labelVisible=False, height=40, width=330, \
                                                                                             marginWidth=5, marginHeight=5)
        cmds.rowLayout(numberOfColumns=1, columnAttach=([1, 'left', 55]), rowAttach=([1, 'top', 0]))
        ui_preferences_file = open(self.ui_preferences_path, 'rb')
        ui_preferences = cPickle.load(ui_preferences_file)
        ui_preferences_file.close()
        value = ui_preferences['loadCollectionClearModeStatus']
        self.uiVars['loadCollectionClearMode_checkBox'] = \
            cmds.checkBox(label='Clear current collection list before loading', value=value, \
                                                                            changeCommand=setLoadCollectionClearModeValue)
        cmds.setParent(self.uiVars['loadCollectionClearModeWindowColumn'])
        cmds.rowLayout(numberOfColumns=2, columnAttach=([1, 'left', 38], [2, 'left', 30]))
        cmds.button(label='Load collection(s)', width=130, command=loadCollectionsFromSettingsWindow)

        cmds.button(label='Close', width=90, command=partial(self.closeWindow, \
                                                                        self.uiVars['loadCollectionClearModeWindow']))
        cmds.setParent(self.uiVars['loadCollectionClearModeWindowColumn'])
        cmds.text(label='')
        cmds.showWindow(self.uiVars['loadCollectionClearModeWindow'])

    def changeLoadCollectionDirectoryClearMode(self, *args):
        def loadCollectionsFromSettingsWindow(*args):
            try:
                cmds.deleteUI('mrt_loadCollectionDirectoryClearMode_setting_UI_window')
            except:
                pass
            self.selectDirectoryForLoadingCollections()

        def setLoadCollectionDirectoryClearModeValue(*args):
            value = cmds.checkBox(self.uiVars['loadCollectionDirectoryClearMode_checkBox'], query=True, value=True)
            ui_preferences_file = open(self.ui_preferences_path, 'rb')
            ui_preferences = cPickle.load(ui_preferences_file)
            ui_preferences['loadCollectionDirectoryClearModeStatus'] = value
            ui_preferences_file.close()
            ui_preferences_file = open(self.ui_preferences_path, 'wb')
            cPickle.dump(ui_preferences, ui_preferences_file, cPickle.HIGHEST_PROTOCOL)
            ui_preferences_file.close()
        try:
            cmds.deleteUI('mrt_loadCollectionDirectoryClearMode_setting_UI_window')
        except:
            pass
        self.uiVars['loadCollectionDirectoryClearModeWindow'] = \
            cmds.window('mrt_loadCollectionDirectoryClearMode_setting_UI_window', \
                         title='Load module collections from directory', height=50, maximizeButton=False, sizeable=False)
        try:
            cmds.windowPref('mrt_loadCollectionDirectoryClearMode_setting_UI_window', remove=True)
        except:
            pass
        self.uiVars['loadCollectionDirectoryClearModeWindowColumn'] = cmds.columnLayout(adjustableColumn=True)
        cmds.text(label='')
        cmds.frameLayout(visible=True, borderVisible=False, collapsable=False, labelVisible=False, height=40, width=350, \
                                                                                               marginWidth=5, marginHeight=5)
        cmds.rowLayout(numberOfColumns=1, columnAttach=([1, 'left', 62]), rowAttach=([1, 'top', 0]))
        ui_preferences_file = open(self.ui_preferences_path, 'rb')
        ui_preferences = cPickle.load(ui_preferences_file)
        value = ui_preferences['loadCollectionDirectoryClearModeStatus']
        ui_preferences_file.close()
        self.uiVars['loadCollectionDirectoryClearMode_checkBox'] = \
            cmds.checkBox(label='Clear current collection list before loading', value=value, \
                                                                    changeCommand=setLoadCollectionDirectoryClearModeValue)

        cmds.setParent(self.uiVars['loadCollectionDirectoryClearModeWindowColumn'])
        cmds.rowLayout(numberOfColumns=2, columnAttach=([1, 'left', 22], [2, 'left', 14]))
        cmds.button(label='Load collection(s) from directory', width=200, command=loadCollectionsFromSettingsWindow)

        cmds.button(label='Close', width=90, command=partial(self.closeWindow, \
                                                                self.uiVars['loadCollectionDirectoryClearModeWindow']))
        cmds.setParent(self.uiVars['loadCollectionDirectoryClearModeWindowColumn'])
        cmds.text(label='')
        cmds.showWindow(self.uiVars['loadCollectionDirectoryClearModeWindow'])

    def loadSavedCharTemplates(self, *args):
        ui_preferences_file = open(self.ui_preferences_path, 'rb')
        ui_preferences = cPickle.load(ui_preferences_file)
        ui_preferences_file.close()
        startDir = ui_preferences['directoryForCharacterTemplates']
        if not os.path.exists(startDir):
            startDir = ui_preferences['defaultDirectoryForCharacterTemplates']
        fileFilter = 'MRT Character Template Files (*.mrtct)'
        mrtct_files = cmds.fileDialog2(caption='Load character template(s)', fileFilter=fileFilter, okCaption='Load', \
                                                                      startingDirectory=startDir, fileMode=4, dialogStyle=2)
        if mrtct_files == None:
            return
        clearStatus = ui_preferences['loadCharTemplateClearModeStatus']
        self.loadCharTemplatesForUI(mrtct_files, clearStatus)
        ui_preferences['directoryForCharacterTemplates'] = mrtct_files[0].rpartition('/')[0]
        ui_preferences_file = open(self.ui_preferences_path, 'wb')
        cPickle.dump(ui_preferences, ui_preferences_file, cPickle.HIGHEST_PROTOCOL)
        ui_preferences_file.close()

    def changeLoadSettingsForCharTemplates(self, *args):
        def setCharTemplateLoadSettingsValues(*args):
            ui_preferences_file = open(self.ui_preferences_path, 'rb')
            ui_preferences = cPickle.load(ui_preferences_file)
            ui_preferences_file.close()
            clearListStatus = cmds.checkBox(self.uiVars['clearCharTemplateListOnLoad_checkBox'], query=True, value=True)
            loadPreviousListAtStartup = cmds.checkBox(self.uiVars['charTemplateLoadAtStartup_checkBox'], query=True, \
                                                                                                                  value=True)
            loadNewTemplatesToList = cmds.checkBox(self.uiVars['newCharTemplateLoadToList_checkBox'], query=True, \
                                                                                                                  value=True)
            ui_preferences['loadCharTemplateClearModeStatus'] = clearListStatus
            ui_preferences['autoLoadPreviousCharTemplateListAtStartupStatus'] = loadPreviousListAtStartup
            ui_preferences['loadNewCharTemplatesToCurrentList'] = loadNewTemplatesToList
            ui_preferences_file = open(self.ui_preferences_path, 'wb')
            cPickle.dump(ui_preferences, ui_preferences_file, cPickle.HIGHEST_PROTOCOL)
            ui_preferences_file.close()
        def loadTemplatesFromSettingsWindow(*args):
            try:
                cmds.deleteUI('mrt_charTemplateLoadSettingsUI_window')
            except:
                pass
            self.loadSavedCharTemplates()
        try:
            cmds.deleteUI('mrt_charTemplateLoadSettingsUI_window')
        except:
            pass
        self.uiVars['charTemplateLoadSettingsUIwindow'] = cmds.window('mrt_charTemplateLoadSettingsUI_window', \
                         title='Settings for loading character templates(s)', width=90, maximizeButton=False, sizeable=False)
        try:
            cmds.windowPref('mrt_charTemplateLoadSettingsUI_window', remove=True)
        except:
            pass
        self.uiVars['charTemplateLoadSettingsWindowColumn'] = cmds.columnLayout(adjustableColumn=True)
        cmds.text(label='')
        ui_preferences_file = open(self.ui_preferences_path, 'rb')
        ui_preferences = cPickle.load(ui_preferences_file)
        ui_preferences_file.close()
        clearListStatus = ui_preferences['loadCharTemplateClearModeStatus']
        loadPreviousListAtStartup = ui_preferences['autoLoadPreviousCharTemplateListAtStartupStatus']
        loadNewTemplatesToList = ui_preferences['loadNewCharTemplatesToCurrentList']
        cmds.rowLayout(numberOfColumns=1, columnAttach=([1, 'left', 57]))
        
        self.uiVars['charTemplateLoadAtStartup_checkBox'] = \
            cmds.checkBox(label='Preserve and load current list at next startup', value=loadPreviousListAtStartup, \
                                                                             changeCommand=setCharTemplateLoadSettingsValues)
        cmds.setParent(self.uiVars['charTemplateLoadSettingsWindowColumn'])
        cmds.rowLayout(numberOfColumns=1, columnAttach=([1, 'both', 60]), rowAttach=([1, 'top', 5]))
        
        self.uiVars['newCharTemplateLoadToList_checkBox'] = \
            cmds.checkBox(label='Load new saved templates(s) to current list', value=loadNewTemplatesToList, \
                                                                             changeCommand=setCharTemplateLoadSettingsValues)

        cmds.setParent(self.uiVars['charTemplateLoadSettingsWindowColumn'])
        cmds.rowLayout(numberOfColumns=1, columnAttach=([1, 'left', 65]), rowAttach=([1, 'top', 5]))

        self.uiVars['clearCharTemplateListOnLoad_checkBox'] = \
            cmds.checkBox(label='Clear current template list before loading', value=clearListStatus, \
                                                                             changeCommand=setCharTemplateLoadSettingsValues)

        cmds.setParent(self.uiVars['charTemplateLoadSettingsWindowColumn'])
        cmds.text(label='')
        cmds.rowLayout(numberOfColumns=2, columnAttach=([1, 'left', 58], [2, 'left', 30]))
        cmds.button(label='Load templates(s)', width=130, command=loadTemplatesFromSettingsWindow)

        cmds.button(label='Close', width=90, command=partial(self.closeWindow, \
                                                                       self.uiVars['charTemplateLoadSettingsUIwindow']))
        cmds.setParent(self.uiVars['charTemplateLoadSettingsWindowColumn'])
        cmds.text(label='')
        cmds.showWindow(self.uiVars['charTemplateLoadSettingsUIwindow'])

    def loadCharTemplatesForUI(self, charTemplatesFileList, clearCurrentList=False):
        cmds.textScrollList(self.uiVars['charTemplates_txScList'], edit=True, height=32, removeAll=True)
        if clearCurrentList:
            self.charTemplateList = {}
        if len(charTemplatesFileList):
            for template in charTemplatesFileList:
                templateName = re.split(r'\/|\\', template)[-1].rpartition('.')[0]
                if template in self.charTemplateList.values():
                    continue
                if templateName in self.charTemplateList:
                    suffix = mfunc.findHighestCommonTextScrollListNameSuffix(templateName, self.charTemplateList.keys())
                    suffix = suffix + 1
                    templateName = '%s (%s)'%(templateName, suffix)
                self.charTemplateList[templateName] = template
            scrollHeight = len(self.charTemplateList) * 20
            if scrollHeight > 200:
                scrollHeight = 200
            if scrollHeight == 20:
                scrollHeight = 40
            for templateName in sorted(self.charTemplateList):
                cmds.textScrollList(self.uiVars['charTemplates_txScList'], edit=True, enable=True, \
                                    height=scrollHeight, append=templateName, font='plainLabelFont', \
                                    selectCommand=self.printCharTemplateInfoForUI)
            cmds.textScrollList(self.uiVars['charTemplates_txScList'], edit=True, selectIndexedItem=1)
            self.printCharTemplateInfoForUI()
        if len(self.charTemplateList):
            charTemplateList_file = open(self.charTemplateList_path, 'rb')
            charTemplateList = cPickle.load(charTemplateList_file)
            charTemplateList_file.close()
            for key in copy.copy(charTemplateList):
                charTemplateList.pop(key)
            for (key, value) in enumerate(self.charTemplateList.values()):
                charTemplateList[str(key)] = value
            charTemplateList_file = open(self.charTemplateList_path, 'wb')
            cPickle.dump(charTemplateList, charTemplateList_file, cPickle.HIGHEST_PROTOCOL)
            charTemplateList_file.close()
            cmds.button(self.uiVars['charTemplate_button_import'], edit=True, enable=True)
            cmds.button(self.uiVars['charTemplate_button_edit'], edit=True, enable=True)
            cmds.button(self.uiVars['charTemplate_button_delete'], edit=True, enable=True)
        if not len(self.charTemplateList):
            charTemplateList_file = open(self.charTemplateList_path, 'rb')
            charTemplateList = cPickle.load(charTemplateList_file)
            charTemplateList_file.close()
            for key in copy.copy(charTemplateList):
                charTemplateList.pop(key)
            charTemplateList_file = open(self.charTemplateList_path, 'wb')
            cPickle.dump(charTemplateList, charTemplateList_file, cPickle.HIGHEST_PROTOCOL)
            charTemplateList_file.close()
            cmds.textScrollList(self.uiVars['charTemplates_txScList'], edit=True, enable=False, \
                                height=32, append=['              < no character template(s) loaded >'], font='boldLabelFont')
            cmds.scrollField(self.uiVars['charTemplateDescrp_scrollField'], edit=True, \
                             text='< no collection info >', font='obliqueLabelFont', editable=False, height=32)
            cmds.button(self.uiVars['charTemplate_button_import'], edit=True, enable=False)
            cmds.button(self.uiVars['charTemplate_button_edit'], edit=True, enable=False)
            cmds.button(self.uiVars['charTemplate_button_delete'], edit=True, enable=False)

    def printCharTemplateInfoForUI(self, *args):
        selectedItem = cmds.textScrollList(self.uiVars['charTemplates_txScList'], query=True, selectItem=True)[0]
        templateFile = self.charTemplateList[selectedItem]
        if os.path.exists(templateFile):
            templateFileObj = open(templateFile, 'rb')
            templateFileData = cPickle.load(templateFileObj)
            templateFileObj.close()
            templateDescrp = templateFileData['templateDescription']
            infoScrollheight = 32
            if re.match('\w+', templateDescrp):
                if len(templateDescrp) > 60:
                    infoScrollheight = (len(templateDescrp)/40.0) * 16
                if templateDescrp.endswith('\n'):
                    infoScrollheight += 16
                if infoScrollheight > 64:
                    infoScrollheight = 64
                if infoScrollheight < 33:
                    infoScrollheight = 32
                cmds.scrollField(self.uiVars['charTemplateDescrp_scrollField'], edit=True, text=templateDescrp, \
                                                                        font='smallPlainLabelFont', height=infoScrollheight)
            else:
                cmds.scrollField(self.uiVars['charTemplateDescrp_scrollField'], edit=True, text='< no template info >', \
                                                                          font='obliqueLabelFont', editable=False, height=32)
            return True
        else:
            cmds.warning('MRT Error: Character template error. The selected character template file, "%s" cannot be found \
                                                                                                    on disk.'%(templateFile))
                                                                                                    
            cmds.textScrollList(self.uiVars['charTemplateDescrp_scrollField'], edit=True, removeItem=selectedItem)
            self.charTemplateList.pop(selectedItem)
            charTemplateList_file = open(self.charTemplateList_path, 'rb')
            charTemplateList = cPickle.load(charTemplateList_file)
            charTemplateList_file.close()
            for key in copy.copy(charTemplateList):
                if charTemplateList[key] == templateFile:
                    charTemplateList.pop(key)
                    break
            charTemplateList_file = open(self.charTemplateList_path, 'wb')
            cPickle.dump(charTemplateList, charTemplateList_file, cPickle.HIGHEST_PROTOCOL)
            charTemplateList_file.close()
            cmds.scrollField(self.uiVars['charTemplateDescrp_scrollField'], edit=True, text='< no template info >', \
                                                                          font='obliqueLabelFont', editable=False, height=32)
            allItems = cmds.textScrollList(self.uiVars['charTemplates_txScList'], query=True, allItems=True)
            if not allItems:
                cmds.textScrollList(self.uiVars['charTemplates_txScList'], edit=True, enable=False, height=32, \
                                          append=['              < no character template(s) loaded >'], font='boldLabelFont')
            cmds.button(self.uiVars['charTemplate_button_import'], edit=True, enable=False)
            cmds.button(self.uiVars['charTemplate_button_edit'], edit=True, enable=False)
            cmds.button(self.uiVars['charTemplate_button_delete'], edit=True, enable=False)
            return False

    def importSelectedCharTemplate(self, *args):
        namespace = cmds.namespaceInfo(currentNamespace=True)
        cmds.namespace(setNamespace=':')
        transforms = cmds.ls(type='transform')
        for transform in transforms:
            characterName = re.findall('^MRT_character(\D+)__mainGrp$', transform)
            if characterName:
                cmds.warning('MRT Error: The character "%s" exists in the scene. \
                                                                    Unable to import a template.'%(characterName[0]))
                return
        moduleContainers = [item for item in cmds.ls(type='container') if mfunc.stripMRTNamespace(item)]
        if moduleContainers:
            cmds.warning('MRT Error: Module(s) were found in the scene; cannot import a character template. \
                                                                                Try importing it in a new scene.')
            return
        selectedItem = cmds.textScrollList(self.uiVars['charTemplates_txScList'], query=True, selectItem=True)[0]
        templateFile = self.charTemplateList[selectedItem]
        templateFileObj = open(templateFile, 'rb')
        templateFileData = cPickle.load(templateFileObj)
        templateFileObj.close()
        tempFilePath = templateFile.rpartition('.mrtct')[0]+'_temp.ma'
        tempFileObj = open(tempFilePath, 'w')
        for i in range(1, len(templateFileData)):
            tempFileObj.write(templateFileData['templateData_line_'+str(i)])
        tempFileObj.close()
        del templateFileData
        cmds.file(tempFilePath, i=True, type='mayaAscii', prompt=False, ignoreVersion=True)
        os.remove(tempFilePath)

    def editSelectedCharTemplateDescriptionFromUI(self, *args):
        def editDescriptionForSelectedCharTemplate(templateDescription, *args):
            cancelEditCharTemplateNoDescrpErrorWindow()
            selectedItem = cmds.textScrollList(self.uiVars['charTemplates_txScList'], query=True, \
                                                                                                    selectItem=True)[0]
            templateFile = self.charTemplateList[selectedItem]
            templateFileObj = open(templateFile, 'rb')
            templateFileData = cPickle.load(templateFileObj)
            templateFileObj.close()
            templateFileData['templateDescription'] = templateDescription
            templateFileObj = open(templateFile, 'wb')
            cPickle.dump(templateFileData, templateFileObj, cPickle.HIGHEST_PROTOCOL)
            templateFileObj.close()
            self.printCharTemplateInfoForUI()
        def cancelEditCharTemplateNoDescrpErrorWindow(*args):
            cmds.deleteUI(self.uiVars['editCharTemplateDescrpWindow'])
            try:
                cmds.deleteUI(self.uiVars['editCharTemplateNoDescrpErrorWindow'])
            except:
                pass
        def checkEditDescriptionForSelectedCharTemplate(*args):
            templateDescription = cmds.scrollField(self.uiVars['editCharTemplateDescrpWindowScrollField'], \
                                                                                                       query=True, text=True)
            if templateDescription == '':
            
                self.uiVars['editCharTemplateNoDescrpErrorWindow'] = \
                    cmds.window('mrt_editCharTemplate_noDescrpError_UI_window', title='Character template warning', \
                                                                                        maximizeButton=False, sizeable=False)
                try:
                    cmds.windowPref('mrt_editCharTemplate_noDescrpError_UI_window', remove=True)
                except:
                    pass
                cmds.frameLayout(visible=True, borderVisible=False, collapsable=False, labelVisible=False, height=90, \
                                                                                  width=220, marginWidth=20, marginHeight=15)
                cmds.text(label='Are you sure you want to continue with an empty description?')
                cmds.rowLayout(numberOfColumns=2, columnAttach=([1, 'left', 55], [2, 'left', 20]), \
                                                                                    rowAttach=([1, 'top', 8], [2, 'top', 8]))
                cmds.button(label='Continue', width=90, \
                                                command=partial(editDescriptionForSelectedCharTemplate, templateDescription))
                cmds.button(label='Cancel', width=90, command=cancelEditCharTemplateNoDescrpErrorWindow)
                cmds.showWindow(self.uiVars['editCharTemplateNoDescrpErrorWindow'])
            else:
                editDescriptionForSelectedCharTemplate(templateDescription)
        validItem = self.printCharTemplateInfoForUI()
        if not validItem:
            return
        try:
            cmds.deleteUI('mrt_charTemplateDescription_edit_UI_window')
        except:
            pass
        self.uiVars['editCharTemplateDescrpWindow'] = cmds.window('mrt_charTemplateDescription_edit_UI_window', \
                                    title='Character template description', height=150, maximizeButton=False, sizeable=False)
        try:
            cmds.windowPref('mrt_charTemplateDescription_edit_UI_window', remove=True)
        except:
            pass
        self.uiVars['editCharTemplateDescrpWindowColumn'] = cmds.columnLayout(adjustableColumn=True)
        cmds.text(label='')
        cmds.text('Enter new description for character template', align='center', font='boldLabelFont')
        cmds.frameLayout(visible=True, borderVisible=False, collapsable=False, labelVisible=False, height=75, width=320, \
                                                                                              marginWidth=5, marginHeight=10)
        selectedItem = cmds.textScrollList(self.uiVars['charTemplates_txScList'], query=True, selectItem=True)[0]
        templateFile = self.charTemplateList[selectedItem]
        templateFileObj = open(templateFile, 'rb')
        templateFileData = cPickle.load(templateFileObj)
        currentDescriptionText = templateFileData['templateDescription']
        templateFileObj.close()
        self.uiVars['editCharTemplateDescrpWindowScrollField'] = cmds.scrollField(preventOverride=True, wordWrap=True, \
                                                                                                 text=currentDescriptionText)
        cmds.setParent(self.uiVars['editCharTemplateDescrpWindowColumn'])
        cmds.rowLayout(numberOfColumns=2, columnAttach=([1, 'left', 34], [2, 'left', 26]))
        cmds.button(label='Save description', width=130, command=checkEditDescriptionForSelectedCharTemplate)

        cmds.button(label='Cancel', width=90, command=partial(self.closeWindow, self.uiVars['editCharTemplateDescrpWindow']))
        cmds.setParent(self.uiVars['editCharTemplateDescrpWindowColumn'])
        cmds.text(label='')
        cmds.showWindow(self.uiVars['editCharTemplateDescrpWindow'])

    def deleteSelectedCharTemplate(self, *args):
        def deleteCharTemplate(deleteFromDisk=False, *args):
            cmds.deleteUI('mrt_deleteCharTemplate_UI_window')
            selectedItem = cmds.textScrollList(self.uiVars['charTemplates_txScList'], query=True, selectItem=True)[0]
            templateFile = self.charTemplateList[selectedItem]
            cmds.textScrollList(self.uiVars['charTemplates_txScList'], edit=True, removeItem=selectedItem)
            self.charTemplateList.pop(selectedItem)
            charTemplateList_file = open(self.charTemplateList_path, 'rb')
            charTemplateList = cPickle.load(charTemplateList_file)
            charTemplateList_file.close()
            for key in copy.copy(charTemplateList):
                if charTemplateList[key] == templateFile:
                    charTemplateList.pop(key)
                    break
            charTemplateList_file = open(self.charTemplateList_path, 'wb')
            cPickle.dump(charTemplateList, charTemplateList_file, cPickle.HIGHEST_PROTOCOL)
            charTemplateList_file.close()
            if deleteFromDisk:
                os.remove(templateFile)
            allItems = cmds.textScrollList(self.uiVars['charTemplates_txScList'], query=True, allItems=True) or []
            if len(allItems):
                scrollHeight = len(allItems)* 20
                if scrollHeight > 100:
                    scrollHeight = 100
                if scrollHeight == 20:
                    scrollHeight = 40
                cmds.textScrollList(self.uiVars['charTemplates_txScList'], edit=True, height=scrollHeight)
                cmds.textScrollList(self.uiVars['charTemplates_txScList'], edit=True, selectIndexedItem=1)
                self.printCharTemplateInfoForUI()
            else:
                cmds.textScrollList(self.uiVars['charTemplates_txScList'], edit=True, enable=False, \
                                height=32, append=['              < no character template(s) loaded >'], font='boldLabelFont')
                cmds.scrollField(self.uiVars['charTemplateDescrp_scrollField'], edit=True, text='< no template info >', \
                                                                           font='obliqueLabelFont', editable=False, height=32)
                cmds.button(self.uiVars['charTemplate_button_import'], edit=True, enable=False)
                cmds.button(self.uiVars['charTemplate_button_edit'], edit=True, enable=False)
                cmds.button(self.uiVars['charTemplate_button_delete'], edit=True, enable=False)

        validItem = self.printCharTemplateInfoForUI()
        if not validItem:
            return
        try:
            cmds.deleteUI('mrt_deleteCharTemplate_UI_window')
        except:
            pass
        self.uiVars['deleteCharTemplateWindow'] = cmds.window('mrt_deleteCharTemplate_UI_window', \
                                                     title='Delete character template', maximizeButton=False, sizeable=False)
        try:
            cmds.windowPref('mrt_deleteCharTemplate_UI_window', remove=True)
        except:
            pass
        cmds.frameLayout(visible=True, borderVisible=False, collapsable=False, labelVisible=False, height=90, width=220, \
                                                                                              marginWidth=20, marginHeight=15)
        cmds.rowLayout(numberOfColumns=2, columnAttach=([1, 'left', 0], [2, 'left', 20]))
        cmds.button(label='From disk', width=90, command=partial(deleteCharTemplate, True))
        cmds.button(label='Remove from list', width=120, command=deleteCharTemplate)
        cmds.showWindow(self.uiVars['deleteCharTemplateWindow'])

    def selectDirectoryForLoadingCollections(self, *args):
        ui_preferences_file = open(self.ui_preferences_path, 'rb')
        ui_preferences = cPickle.load(ui_preferences_file)
        ui_preferences_file.close()
        startDir = ui_preferences['directoryForAutoLoadingCollections']
        if not os.path.exists(startDir):
            startDir = ui_preferences['defaultDirectoryForAutoLoadingCollections']
        fileFilter = 'MRT Module Collection Files (*.mrtmc)'
        directoryPath = cmds.fileDialog2(caption='Select directory for loading module collections', okCaption='Select', \
                                                fileFilter=fileFilter, startingDirectory=startDir, fileMode=2, dialogStyle=2)
        if directoryPath:
            ui_preferences['directoryForAutoLoadingCollections'] = directoryPath[0]
            value = ui_preferences['loadCollectionDirectoryClearModeStatus']
            mrtmc_files = []
            for file in os.listdir(directoryPath[0]):
                if fnmatch.fnmatch(file, '*mrtmc'):
                    mrtmc_files.append('%s/%s'%(directoryPath[0], file))
            self.loadModuleCollectionsForUI(mrtmc_files, value)
        ui_preferences_file = open(self.ui_preferences_path, 'wb')
        cPickle.dump(ui_preferences, ui_preferences_file, cPickle.HIGHEST_PROTOCOL)
        ui_preferences_file.close()

    def loadSavedModuleCollections(self, *args):
        ui_preferences_file = open(self.ui_preferences_path, 'rb')
        ui_preferences = cPickle.load(ui_preferences_file)
        ui_preferences_file.close()
        startDir = ui_preferences['lastDirectoryForLoadingCollections']
        if not os.path.exists(startDir):
            startDir = ui_preferences['defaultLastDirectoryForLoadingCollections']
        fileFilter = 'MRT Module Collection Files (*.mrtmc)'
        mrtmc_files = cmds.fileDialog2(caption='Select module collection files(s) for loading', okCaption='Load', \
                                                fileFilter=fileFilter, startingDirectory=startDir, fileMode=4, dialogStyle=2)
        if not mrtmc_files:
            return
        value = ui_preferences['loadCollectionClearModeStatus']
        self.loadModuleCollectionsForUI(mrtmc_files, value)
        directory = mrtmc_files[0].rpartition('/')[0]
        ui_preferences['lastDirectoryForLoadingCollections'] = directory
        ui_preferences_file = open(self.ui_preferences_path, 'wb')
        cPickle.dump(ui_preferences, ui_preferences_file, cPickle.HIGHEST_PROTOCOL)
        ui_preferences_file.close()

    def loadModuleCollectionsForUI(self, moduleCollectionFileList, clearCurrentList=False):
        cmds.textScrollList(self.uiVars['moduleCollection_txScList'], edit=True, height=32, removeAll=True)
        if clearCurrentList:
            self.module_collectionList = {}
        if len(moduleCollectionFileList):
            for collection in moduleCollectionFileList:
                collectionName = re.split(r'\/|\\', collection)[-1].rpartition('.')[0]
                if collection in self.module_collectionList.values():
                    continue
                if collectionName in self.module_collectionList:
                    suffix = mfunc.findHighestCommonTextScrollListNameSuffix(collectionName, self.module_collectionList.keys())
                    suffix = suffix + 1
                    collectionName = '%s (%s)'%(collectionName, suffix)
                self.module_collectionList[collectionName] = collection
            scrollHeight = len(self.module_collectionList) * 20
            if scrollHeight > 200:
                scrollHeight = 200
            if scrollHeight == 20:
                scrollHeight = 40
            for collectionName in sorted(self.module_collectionList):
                cmds.textScrollList(self.uiVars['moduleCollection_txScList'], edit=True, enable=True, \
                height=scrollHeight, append=collectionName, font='plainLabelFont', selectCommand=self.printCollectionInfoForUI)
            cmds.textScrollList(self.uiVars['moduleCollection_txScList'], edit=True, selectIndexedItem=1)
            self.printCollectionInfoForUI()
        if len(self.module_collectionList):
            module_collectionList_file = open(self.module_collectionList_path, 'rb')
            module_collectionList = cPickle.load(module_collectionList_file)
            module_collectionList_file.close()
            for key in copy.copy(module_collectionList):
                module_collectionList.pop(key)
            for (key, value) in enumerate(self.module_collectionList.values()):
                module_collectionList[str(key)] = value
            module_collectionList_file = open(self.module_collectionList_path, 'wb')
            cPickle.dump(module_collectionList, module_collectionList_file, cPickle.HIGHEST_PROTOCOL)
            module_collectionList_file.close()
            cmds.button(self.uiVars['loadedCollections_button_install'], edit=True, enable=True)
            cmds.button(self.uiVars['loadedCollections_button_edit'], edit=True, enable=True)
            cmds.button(self.uiVars['loadedCollections_button_delete'], edit=True, enable=True)
        if not len(self.module_collectionList):
            module_collectionList_file = open(self.module_collectionList_path, 'rb')
            module_collectionList = cPickle.load(module_collectionList_file)
            module_collectionList_file.close()
            for key in copy.copy(module_collectionList):
                module_collectionList.pop(key)
            module_collectionList_file = open(self.module_collectionList_path, 'wb')
            cPickle.dump(module_collectionList, module_collectionList_file, cPickle.HIGHEST_PROTOCOL)
            module_collectionList_file.close()
            cmds.textScrollList(self.uiVars['moduleCollection_txScList'], edit=True, enable=False, height=32, \
                                            append=['              < no module collection(s) loaded >'], font='boldLabelFont')
            cmds.scrollField(self.uiVars['collectionDescrp_scrollField'], edit=True, text='< no collection info >', \
                                                                           font='obliqueLabelFont', editable=False, height=32)
            cmds.button(self.uiVars['loadedCollections_button_install'], edit=True, enable=False)
            cmds.button(self.uiVars['loadedCollections_button_edit'], edit=True, enable=False)
            cmds.button(self.uiVars['loadedCollections_button_delete'], edit=True, enable=False)

    def printCollectionInfoForUI(self):
        selectedItem = cmds.textScrollList(self.uiVars['moduleCollection_txScList'], query=True, selectItem=True)[0]
        collectionFile = self.module_collectionList[selectedItem]
        if os.path.exists(collectionFile):
            collectionFileObj_file = open(collectionFile, 'rb')
            collectionFileObj = cPickle.load(collectionFileObj_file)
            collectionFileObj_file.close()
            collectionDescrp = collectionFileObj['collectionDescrp']
            infoScrollheight = 32
            if re.match('\w+', collectionDescrp):
                if len(collectionDescrp) > 60:
                    infoScrollheight = (len(collectionDescrp)/40.0) * 16
                if collectionDescrp.endswith('\n'):
                    infoScrollheight += 16
                if infoScrollheight > 64:
                    infoScrollheight = 64
                if infoScrollheight < 33:
                    infoScrollheight = 32
                cmds.scrollField(self.uiVars['collectionDescrp_scrollField'], edit=True, text=collectionDescrp, \
                                                                          font='smallPlainLabelFont', height=infoScrollheight)
            else:
                cmds.scrollField(self.uiVars['collectionDescrp_scrollField'], edit=True, \
                                      text='< no valid collection info >', font='obliqueLabelFont', editable=False, height=32)
            return True
        else:
            cmds.warning('MRT Error: Module collection error. \
                                         The selected module collection file, "%s" cannot be found on disk.'%(collectionFile))
            cmds.textScrollList(self.uiVars['moduleCollection_txScList'], edit=True, removeItem=selectedItem)
            self.module_collectionList.pop(selectedItem)
            module_collectionList_file = open(self.module_collectionList_path, 'rb')
            module_collectionList = cPickle.load(module_collectionList_file)
            module_collectionList_file.close()
            for key in copy.copy(module_collectionList):
                if module_collectionList[key] == collectionFile:
                    module_collectionList.pop(key)
                    break
            module_collectionList_file = open(self.module_collectionList_path, 'wb')
            cPickle.dump(module_collectionList, module_collectionList_file, cPickle.HIGHEST_PROTOCOL)
            module_collectionList_file.close()
            cmds.scrollField(self.uiVars['collectionDescrp_scrollField'], edit=True, text='< no collection info >', \
                                                                           font='obliqueLabelFont', editable=False, height=32)
            allItems = cmds.textScrollList(self.uiVars['moduleCollection_txScList'], query=True, allItems=True)
            if not allItems:
                cmds.textScrollList(self.uiVars['moduleCollection_txScList'], edit=True, enable=False, height=32, \
                                            append=['              < no module collection(s) loaded >'], font='boldLabelFont')
            cmds.button(self.uiVars['loadedCollections_button_install'], edit=True, enable=False)
            cmds.button(self.uiVars['loadedCollections_button_edit'], edit=True, enable=False)
            cmds.button(self.uiVars['loadedCollections_button_delete'], edit=True, enable=False)
            return False

    def deleteSelectedModuleCollection(self, *args):
        def deleteModuleCollection(deleteFromDisk=False, *args):
            cmds.deleteUI('mrt_deleteCollection_UI_window')
            selectedItem = cmds.textScrollList(self.uiVars['moduleCollection_txScList'], query=True, \
                                                                                                          selectItem=True)[0]
            collectionFile = self.module_collectionList[selectedItem]
            cmds.textScrollList(self.uiVars['moduleCollection_txScList'], edit=True, removeItem=selectedItem)

            self.module_collectionList.pop(selectedItem)
            module_collectionList_file = open(self.module_collectionList_path, 'rb')
            module_collectionList = cPickle.load(module_collectionList_file)
            module_collectionList_file.close()
            for key in copy.copy(module_collectionList):
                if module_collectionList[key] == collectionFile:
                    module_collectionList.pop(key)
                    break
            module_collectionList_file = open(self.module_collectionList_path, 'wb')
            cPickle.dump(module_collectionList, module_collectionList_file, cPickle.HIGHEST_PROTOCOL)
            module_collectionList_file.close()
            if deleteFromDisk:
                os.remove(collectionFile)
            allItems = cmds.textScrollList(self.uiVars['moduleCollection_txScList'], query=True, allItems=True) or []
            if len(allItems):
                scrollHeight = len(allItems)* 20
                if scrollHeight > 200:
                    scrollHeight = 200
                if scrollHeight == 20:
                    scrollHeight = 40
                cmds.textScrollList(self.uiVars['moduleCollection_txScList'], edit=True, height=scrollHeight)
                cmds.textScrollList(self.uiVars['moduleCollection_txScList'], edit=True, selectIndexedItem=1)
                self.printCollectionInfoForUI()
            else:
                cmds.textScrollList(self.uiVars['moduleCollection_txScList'], edit=True, enable=False, height=32, \
                                            append=['              < no module collection(s) loaded >'], font='boldLabelFont')
                cmds.scrollField(self.uiVars['collectionDescrp_scrollField'], edit=True, text='< no collection info >', \
                                                                           font='obliqueLabelFont', editable=False, height=32)
                cmds.button(self.uiVars['loadedCollections_button_install'], edit=True, enable=False)
                cmds.button(self.uiVars['loadedCollections_button_edit'], edit=True, enable=False)
                cmds.button(self.uiVars['loadedCollections_button_delete'], edit=True, enable=False)

        validItem = self.printCollectionInfoForUI()
        if not validItem:
            return
        try:
            cmds.deleteUI('mrt_deleteCollection_UI_window')
        except:
            pass
        self.uiVars['deleteCollectionWindow'] = cmds.window('mrt_deleteCollection_UI_window', \
                                                       title='Delete module collection', maximizeButton=False, sizeable=False)
        try:
            cmds.windowPref('mrt_deleteCollection_UI_window', remove=True)
        except:
            pass
        cmds.frameLayout(visible=True, borderVisible=False, collapsable=False, labelVisible=False, height=90, width=220, \
                                                                                             marginWidth=20, marginHeight=15)
        cmds.rowLayout(numberOfColumns=2, columnAttach=([1, 'left', 0], [2, 'left', 20]))
        cmds.button(label='From disk', width=90, command=partial(deleteModuleCollection, True))
        cmds.button(label='Remove from list', width=120, command=deleteModuleCollection)
        cmds.showWindow(self.uiVars['deleteCollectionWindow'])

    def installSelectedModuleCollectionToScene(self, *args, autoInstallFile=None):
        if not autoInstallFile:
            validItem = self.printCollectionInfoForUI()
            if not validItem:
                return
            selectedItem = cmds.textScrollList(self.uiVars['moduleCollection_txScList'], query=True, \
                                                                                                          selectItem=True)[0]
            collectionFile = self.module_collectionList[selectedItem]
        if autoInstallFile:
            collectionFile = autoInstallFile
        mrtmc_fObject_file = open(collectionFile, 'rb')
        mrtmc_fObject = cPickle.load(mrtmc_fObject_file)
        mrtmc_fObject_file.close()
        currentNamespace = cmds.namespaceInfo(currentNamespace=True)
        cmds.namespace(setNamespace=':')
        cmds.namespace(addNamespace='MRT_tempNamespaceForImport')
        cmds.namespace(setNamespace='MRT_tempNamespaceForImport')
        tempFilePath = collectionFile.rpartition('.mrtmc')[0]+'_temp.ma'
        tempFile_fObject = open(tempFilePath, 'w')
        for i in range(1, len(mrtmc_fObject)):
            tempFile_fObject.write(mrtmc_fObject['collectionData_line_'+str(i)])
        tempFile_fObject.close()
        del mrtmc_fObject
        cmds.file(tempFilePath, i=True, type="mayaAscii", prompt=False, ignoreVersion=True)
        os.remove(tempFilePath)
        # Get the names in the temporary namespace.
        namesInTemp = mfunc.returnMRT_Namespaces(cmds.namespaceInfo(listOnlyNamespaces=True))
        # Filter the module names from the temporary namespace.
        namespacesInTemp = []
        for name in namesInTemp:
            namespacesInTemp.append(name.partition(':')[2])
        # Get the module names in the root namespace, if any.
        cmds.namespace(setNamespace=':')
        moduleNamespaces = mfunc.returnMRT_Namespaces(cmds.namespaceInfo(listOnlyNamespaces=True))
        if moduleNamespaces:
            # Get the user specified names of the module names, if any.
            userSpecNamesForSceneModules = mfunc.returnModuleUserSpecNames(moduleNamespaces)[1]
            # Get the user specified names of the modules in the temporary namespaces.
            userSpecNamesInTemp = mfunc.returnModuleUserSpecNames(namespacesInTemp)
            cmds.namespace(setNamespace='MRT_tempNamespaceForImport')
            allUserSpecNames = set(userSpecNamesInTemp[1] + userSpecNamesForSceneModules)
        # If there're existing modules in the scene, check and rename module(s) in the temporary namespaces to resolve name clashes.
            for (name, userSpecName) in zip(userSpecNamesInTemp[0], userSpecNamesInTemp[1]):
                if userSpecName in userSpecNamesForSceneModules:
                    underscore_search = '_'
                    if re.match('^\w+_[0-9]*$', userSpecName):
                        underscore_search = re.findall('_*', userSpecName)
                        underscore_search.reverse()
                        for item in underscore_search:
                            if '_' in item:
                                underscore_search = item
                                break
                        userSpecNameBase = userSpecName.rpartition(underscore_search)[0]
                    else:
                        userSpecNameBase = userSpecName
                    suffix = mfunc.findHighestNumSuffix(userSpecNameBase, list(allUserSpecNames))
                    newUserSpecName = '{0}{1}{2}'.format(userSpecName, underscore_search, suffix+1)
                    namespace = '%s__%s'%(name, userSpecName)
                    newNamespace = '%s__%s'%(name, newUserSpecName)
                    cmds.namespace(addNamespace=newNamespace)
                    cmds.namespace(moveNamespace=[':MRT_tempNamespaceForImport:'+namespace, \
                                                                                ':MRT_tempNamespaceForImport:'+newNamespace])
                    cmds.namespace(removeNamespace=namespace)
                    allUserSpecNames.add(newUserSpecName)
                    if cmds.attributeQuery('mirrorModuleNamespace', \
                                            node=':MRT_tempNamespaceForImport:'+newNamespace+':moduleGrp', exists=True):
                        mirrorModuleNamespace = \
                            cmds.getAttr(':MRT_tempNamespaceForImport:'+newNamespace+':moduleGrp.mirrorModuleNamespace')
                        cmds.lockNode(':MRT_tempNamespaceForImport:'+mirrorModuleNamespace+':module_container', \
                                                                                           lock=False, lockUnpublished=False)
                        cmds.setAttr(':MRT_tempNamespaceForImport:'+mirrorModuleNamespace+':moduleGrp.mirrorModuleNamespace', \
                                                                                                newNamespace, type='string')
                        cmds.lockNode(':MRT_tempNamespaceForImport:'+mirrorModuleNamespace+':module_container', lock=True, \
                                                                                                        lockUnpublished=True)
        cmds.namespace(setNamespace=':')
        cmds.namespace(moveNamespace=['MRT_tempNamespaceForImport', ':'], force=True)
        cmds.namespace(removeNamespace='MRT_tempNamespaceForImport')
        cmds.namespace(setNamespace=currentNamespace)
        self.clearParentModuleField()
        self.clearChildModuleField()

    def editSelectedModuleCollectionDescriptionFromUI(self, *args):
        def editDescriptionForSelectedModuleCollection(collectionDescription, *args):
            cancelEditCollectionNoDescpErrorWindow()
            selectedItem = cmds.textScrollList(self.uiVars['moduleCollection_txScList'], query=True, \
                                                                                                        selectItem=True)[0]
            collectionFile = self.module_collectionList[selectedItem]
            collectionFileObj_file = open(collectionFile, 'rb')
            collectionFileObj = cPickle.load(collectionFileObj_file)
            collectionFileObj_file.close()
            collectionFileObj['collectionDescrp'] = collectionDescription
            collectionFileObj_file = open(collectionFile, 'wb')
            cPickle.dump(collectionFileObj, collectionFileObj_file, cPickle.HIGHEST_PROTOCOL)
            collectionFileObj_file.close()
            self.printCollectionInfoForUI()

        def cancelEditCollectionNoDescpErrorWindow(*args):
            cmds.deleteUI(self.uiVars['editCollectionDescpWindow'])
            try:
                cmds.deleteUI(self.uiVars['editCollectionNoDescpErrorWindow'])
            except:
                pass
        def checkEditDescriptionForSelectedModuleCollection(*args):
            collectionDescription = cmds.scrollField(self.uiVars['editCollectionDescpWindowScrollField'], \
                                                                                                    query=True, text=True)
            if collectionDescription == '':
                self.uiVars['editCollectionNoDescpErrorWindow'] = \
                    cmds.window('mrt_editCollection_noDescpError_UI_window', title='Module collection warning', \
                                                                                     maximizeButton=False, sizeable=False)
                try:
                    cmds.windowPref('mrt_editCollection_noDescpError_UI_window', remove=True)
                except:
                    pass
                cmds.frameLayout(visible=True, borderVisible=False, collapsable=False, labelVisible=False, height=90, \
                                                                                width=220, marginWidth=20, marginHeight=15)
                cmds.text(label='Are you sure you want to continue with an empty description?')
                cmds.rowLayout(numberOfColumns=2, columnAttach=([1, 'left', 55], [2, 'left', 20]), \
                                                                                  rowAttach=([1, 'top', 8], [2, 'top', 8]))
                cmds.button(label='Continue', width=90, \
                                        command=partial(editDescriptionForSelectedModuleCollection, collectionDescription))
                cmds.button(label='Cancel', width=90, command=cancelEditCollectionNoDescpErrorWindow)
                cmds.showWindow(self.uiVars['editCollectionNoDescpErrorWindow'])
            else:
                editDescriptionForSelectedModuleCollection(collectionDescription)
        validItem = self.printCollectionInfoForUI()
        if not validItem:
            return
        try:
            cmds.deleteUI('mrt_collectionDescription_edit_UI_window')
        except:
            pass
        self.uiVars['editCollectionDescpWindow'] = cmds.window('mrt_collectionDescription_edit_UI_window', \
                                     title='Module collection description', height=150, maximizeButton=False, sizeable=False)
        try:
            cmds.windowPref('mrt_collectionDescription_edit_UI_window', remove=True)
        except:
            pass
        self.uiVars['editCollectionDescpWindowColumn'] = cmds.columnLayout(adjustableColumn=True)
        cmds.text(label='')
        cmds.text('Enter new description for module collection', align='center', font='boldLabelFont')
        cmds.frameLayout(visible=True, borderVisible=False, collapsable=False, labelVisible=False, height=75, width=320, \
                                                                                              marginWidth=5, marginHeight=10)
        selectedItem = cmds.textScrollList(self.uiVars['moduleCollection_txScList'], query=True, selectItem=True)[0]
        collectionFile = self.module_collectionList[selectedItem]
        collectionFileObj_file = open(collectionFile, 'rb')
        collectionFileObj = cPickle.load(collectionFileObj_file)
        currentDescriptionText = collectionFileObj['collectionDescrp']
        collectionFileObj_file.close()
        self.uiVars['editCollectionDescpWindowScrollField'] = cmds.scrollField(preventOverride=True, wordWrap=True, \
                                                                                                 text=currentDescriptionText)
        cmds.setParent(self.uiVars['editCollectionDescpWindowColumn'])
        cmds.rowLayout(numberOfColumns=2, columnAttach=([1, 'left', 34], [2, 'left', 26]))
        cmds.button(label='Save description', width=130, command=checkEditDescriptionForSelectedModuleCollection)

        cmds.button(label='Cancel', width=90, command=partial(self.closeWindow, self.uiVars['editCollectionDescpWindow']))
        cmds.setParent(self.uiVars['editCollectionDescpWindowColumn'])
        cmds.text(label='')
        cmds.showWindow(self.uiVars['editCollectionDescpWindow'])

    def putShelfButtonForUI(self, *args):
        currentTab = cmds.tabLayout('ShelfLayout', query=True, selectTab=True)
        shelfTabButtons = cmds.shelfLayout(currentTab, query=True, childArray=True)
        if shelfTabButtons:
            for button in shelfTabButtons:
                annotation = cmds.shelfButton(button, query=True, annotation=True)
                if annotation == 'Modular Rigging Tools':
                    return
        imagePath = cmds.internalVar(userScriptDir=True)+'MRT/mrt_shelfLogo.png'
        cmds.shelfButton(annotation='Modular Rigging Tools', commandRepeatable=True,
                         image1=imagePath, parent=currentTab, sourceType='mel', command='MRT')

    def selectModuleInTreeViewUIfromViewport(self):
        cmds.undoInfo(stateWithoutFlush=False)
        active_UI_selection = {}
        selection = mel.eval("ls -sl -type dagNode")
        if selection == None:
            self.treeViewSelection_list = {}
        else:
            for item in copy.copy(self.treeViewSelection_list):
                if not item in selection:
                    self.treeViewSelection_list.pop(item)
        if selection != None:
            for select in selection:
                namespaceInfo = mfunc.stripMRTNamespace(select)
                if namespaceInfo != None:
                    moduleNamespace = namespaceInfo[0]
                    self.treeViewSelection_list[select] = moduleNamespace
        cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True, clearSelection=True)
        if len(self.treeViewSelection_list):
            for item in self.treeViewSelection_list:
                if item in selection:
                    active_UI_selection[item] = self.treeViewSelection_list[item]
            for item in active_UI_selection:
                cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True, selectItem=[active_UI_selection[item], 1])
        else:
            # This clears the selection
            self.updateListForSceneModulesInUI()
        cmds.undoInfo(stateWithoutFlush=True)

    def updateListForSceneModulesInUI_runIdle(self, *args):
        cmds.evalDeferred(self.updateListForSceneModulesInUI, lowestPriority=True)

    def toggleSceneModuleListSortTypeFromUI(self, *args):
        selection = cmds.ls(selection=True)
        self.updateListForSceneModulesInUI()
        if selection:
            cmds.select(selection, replace=True)

    def resetListHeightForSceneModulesUI(self, *args):
        sceneNamespaces = cmds.namespaceInfo(listOnlyNamespaces=True)
        MRT_namespaces = mfunc.returnMRT_Namespaces(sceneNamespaces)
        if MRT_namespaces != None:
            treeLayoutHeight = len(MRT_namespaces) * 22
            if treeLayoutHeight > 200:
                treeLayoutHeight = 200
            cmds.scrollLayout(self.uiVars['moduleList_Scroll'], edit=True, height=treeLayoutHeight+8)
            cmds.frameLayout(self.uiVars['moduleList_fLayout'], edit=True, height=treeLayoutHeight)

    def updateListForSceneModulesInUI(self, *args):
        cmds.undoInfo(stateWithoutFlush=False)
        selection = mel.eval("ls -sl -type dagNode")
        if selection == None:
            self.treeViewSelection_list = {}
        currentNamespace = cmds.namespaceInfo(currentNamespace=True)
        cmds.namespace(setNamespace=':')
        sceneNamespaces = cmds.namespaceInfo(listOnlyNamespaces=True)
        MRT_namespaces = mfunc.returnMRT_Namespaces(sceneNamespaces)
        cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True, removeAll=True)
        listNames = {}

        if MRT_namespaces != None:
            cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True, enable=True)
            cmds.rowLayout(self.uiVars['sortModuleList_row'], edit=True, enable=True)
            for name in MRT_namespaces:
                userSpecifiedName = name.partition('__')[2]
                moduleType = name.partition('__')[0].partition('_')[2].partition('Node')[0]
                if cmds.attributeQuery('mirrorModuleNamespace', node=name+':moduleGrp', exists=True):
                    mirrorModuleNamespace = cmds.getAttr(name+':moduleGrp.mirrorModuleNamespace')
                else:
                    mirrorModuleNamespace = None
                listNames[userSpecifiedName] = [name, moduleType, mirrorModuleNamespace]
            defTreeLayoutHeight = cmds.frameLayout(self.uiVars['moduleList_fLayout'], query=True, height=True)
            treeLayoutHeight = len(MRT_namespaces) * 22
            if defTreeLayoutHeight > treeLayoutHeight:
                treeLayoutHeight = defTreeLayoutHeight

            cmds.scrollLayout(self.uiVars['moduleList_Scroll'], edit=True, height=treeLayoutHeight+8)
            cmds.frameLayout(self.uiVars['moduleList_fLayout'], edit=True, height=treeLayoutHeight)
            listStatus = cmds.radioCollection(self.uiVars['sortModuleList_radioColl'], query=True, select=True)

            if listStatus == 'Alphabetically':
                for name in sorted(listNames):
                    if _maya_version >=2013:
                    
                        cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True, numberOfButtons=3,
                                      addItem=(listNames[name][0], ''),
                                      selectionChangedCommand=moduleSelectionFromTreeViewCallback,
                                      editLabelCommand=processItemRenameForTreeViewListCallback)
                                      
                        if cmds.objExists(listNames[name][0]+':proxyGeometryGrp'):
                            cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True,
                                          buttonTextIcon=([listNames[name][0], 1, 'V'],
                                                          [listNames[name][0], 2, 'P'],
                                                          [listNames[name][0], 3, 'R']),
                                          buttonStyle=([listNames[name][0], 1, '2StateButton'],
                                                       [listNames[name][0], 2, '2StateButton'],
                                                       [listNames[name][0], 3, '2StateButton']),
                                          buttonState=([listNames[name][0], 1, 'buttonDown'],
                                                       [listNames[name][0], 2, 'buttonDown'],
                                                       [listNames[name][0], 3, 'buttonDown']),
                                          pressCommand=([1, treeViewButton_1_ActionCallback],
                                                        [2, treeViewButton_2_ActionCallback],
                                                        [3, treeViewButton_3_ActionCallback]),
                                          enableButton=([listNames[name][0], 1, 1],
                                                        [listNames[name][0], 2, 1],
                                                        [listNames[name][0], 3, 1]),
                                          buttonTooltip=([listNames[name][0], 1, 'Module visibility'],
                                                         [listNames[name][0], 2, 'Proxy geometry visibility'],
                                                         [listNames[name][0], 3, 'Reference proxy geometry']))
                        else:
                            cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True,
                                          buttonTextIcon=[listNames[name][0], 1, 'V'],
                                          buttonStyle=[listNames[name][0], 1, '2StateButton'],
                                          buttonState=[listNames[name][0], 1, 'buttonDown'],
                                          pressCommand=[1, treeViewButton_1_ActionCallback],
                                          enableButton=([listNames[name][0], 1, 1],
                                                        [listNames[name][0], 2, 0],
                                                        [listNames[name][0], 3, 0]),
                                          buttonTooltip=[listNames[name][0], 1, 'Module visibility'])
                    else:
                        cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True, numberOfButtons=3,
                                      addItem=(listNames[name][0], ''),
                                      selectionChangedCommand='moduleSelectionFromTreeViewCallback',
                                      editLabelCommand='processItemRenameForTreeViewListCallback')
                                      
                        if cmds.objExists(listNames[name][0]+':proxyGeometryGrp'):
                        
                            cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True,
                                          buttonTextIcon=([listNames[name][0], 1, 'V'],
                                                          [listNames[name][0], 2, 'P'],
                                                          [listNames[name][0], 3, 'R']),
                                          buttonStyle=([listNames[name][0], 1, '2StateButton'],
                                                       [listNames[name][0], 2, '2StateButton'],
                                                       [listNames[name][0], 3, '2StateButton']),
                                          buttonState=([listNames[name][0], 1, 'buttonDown'],
                                                       [listNames[name][0], 2, 'buttonDown'],
                                                       [listNames[name][0], 3, 'buttonDown']),
                                          pressCommand=([1, 'treeViewButton_1_ActionCallback'],
                                                        [2, 'treeViewButton_2_ActionCallback'],
                                                        [3, 'treeViewButton_3_ActionCallback']),
                                          enableButton=([listNames[name][0], 1, 1],
                                                        [listNames[name][0], 2, 1],
                                                        [listNames[name][0], 3, 1]),
                                          buttonTooltip=([listNames[name][0], 1, 'Module visibility'],
                                                         [listNames[name][0], 2, 'Proxy geometry visibility'],
                                                         [listNames[name][0], 3, 'Reference proxy geometry']))
                        else:
                            cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True,
                                          buttonTextIcon=[listNames[name][0], 1, 'V'],
                                          buttonStyle=[listNames[name][0], 1, '2StateButton'],
                                          buttonState=[listNames[name][0], 1, 'buttonDown'],
                                          pressCommand=[1, 'treeViewButton_1_ActionCallback'],
                                          enableButton=([listNames[name][0], 1, 1],
                                                        [listNames[name][0], 2, 0],
                                                        [listNames[name][0], 3, 0]),
                                          buttonTooltip=[listNames[name][0], 1, 'Module visibility'])

                    # Display the text label as oblique if it's a mirror module.
                    if listNames[name][2] == None:
                        cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True,
                                      displayLabel=[listNames[name][0], name],
                                      displayLabelSuffix=[listNames[name][0], ' (%s node module)'%listNames[name][1]])
                    else:
                        cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True,
                                      displayLabel=[listNames[name][0], name],
                                      displayLabelSuffix=[listNames[name][0], ' (%s node mirror module)'%listNames[name][1]],
                                      fontFace=[listNames[name][0], 2])
                            
                for name in sorted(listNames):
                    v_state = cmds.getAttr(listNames[name][0]+':moduleGrp.visibility')
                    
                    if cmds.objExists(listNames[name][0]+':proxyGeometryGrp'):
                        cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True,
                                      buttonTransparencyColor=([listNames[name][0], 1, 0.85, 0.66, 0.27],
                                                               [listNames[name][0], 2, 0.57, 0.66, 1.0],
                                                               [listNames[name][0], 3, 0.42, 0.87, 1.0]))
                                                               
                        p_state = cmds.getAttr(listNames[name][0]+':proxyGeometryGrp.visibility')
                        r_state = cmds.getAttr(listNames[name][0]+':proxyGeometryGrp.overrideDisplayType')
                        
                        if p_state == 0:
                            cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True,
                                          buttonTransparencyColor=[listNames[name][0], 2, 0.65, 0.71, 0.90],
                                          buttonState=[listNames[name][0], 2, 'buttonUp'])
                        if r_state == 0:
                            cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True,
                                          buttonTransparencyColor=[listNames[name][0], 3, 0.68, 0.85, 0.90],
                                          buttonState=[listNames[name][0], 3, 'buttonUp'])
                        if v_state == 0:
                            cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True,
                                          buttonTransparencyColor=[listNames[name][0], 1, 0.71, 0.66, 0.56],
                                          buttonState=[listNames[name][0], 1, 'buttonUp'])
                    else:
                        cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True,
                                      buttonTransparencyColor=([listNames[name][0], 1, 0.85, 0.66, 0.27],
                                                               [listNames[name][0], 2, 0.39, 0.39, 0.39],
                                                               [listNames[name][0], 3, 0.39, 0.39, 0.39]))
                        if v_state == 0:
                            cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True,
                                          buttonTransparencyColor=[listNames[name][0], 1, 0.71, 0.66, 0.56],
                                          buttonState=[listNames[name][0], 1, 'buttonUp'])

            if listStatus == 'By_hierarchy':
                parentTraverseForModules = {}
                for namespace in MRT_namespaces:
                    parentTraverseLength = mfunc.traverseParentModules(namespace)
                    parentTraverseLength = parentTraverseLength[1]
                    if not parentTraverseLength in parentTraverseForModules:
                        parentTraverseForModules[parentTraverseLength] = [namespace.partition('__')[2]]
                    else:
                        parentTraverseForModules[parentTraverseLength].append(namespace.partition('__')[2])
            
                for value in sorted(parentTraverseForModules):
                
                    for name in sorted(parentTraverseForModules[value]):
                    
                        if _maya_version >=2013:
                            parentModuleNode = cmds.getAttr(listNames[name][0]+':moduleGrp.moduleParent')
                            
                            if parentModuleNode == 'None':
                            
                                cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True, numberOfButtons=3,
                                              addItem=(listNames[name][0], ''),
                                              selectionChangedCommand=moduleSelectionFromTreeViewCallback,
                                              editLabelCommand=processItemRenameForTreeViewListCallback)
                            else:
                                parentModuleNode = parentModuleNode.split(',')[0]
                                parentModule = mfunc.stripMRTNamespace(parentModuleNode)[0]
                                cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True, numberOfButtons=3,
                                              addItem=(listNames[name][0], parentModule),
                                              selectionChangedCommand=moduleSelectionFromTreeViewCallback,
                                              editLabelCommand=processItemRenameForTreeViewListCallback)

                            if cmds.objExists(listNames[name][0]+':proxyGeometryGrp'):
                                cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True,
                                              buttonTextIcon=([listNames[name][0], 1, 'V'],
                                                              [listNames[name][0], 2, 'P'],
                                                              [listNames[name][0], 3, 'R']),
                                              buttonStyle=([listNames[name][0], 1, '2StateButton'],
                                                           [listNames[name][0], 2, '2StateButton'],
                                                           [listNames[name][0], 3, '2StateButton']),
                                              buttonState=([listNames[name][0], 1, 'buttonDown'],
                                                           [listNames[name][0], 2, 'buttonDown'],
                                                           [listNames[name][0], 3, 'buttonDown']),
                                              pressCommand=([1, treeViewButton_1_ActionCallback],
                                                            [2, treeViewButton_2_ActionCallback],
                                                            [3, treeViewButton_3_ActionCallback]),
                                              enableButton=([listNames[name][0], 1, 1],
                                                            [listNames[name][0], 2, 1],
                                                            [listNames[name][0], 3, 1]),
                                              buttonTooltip=([listNames[name][0], 1, 'Module visibility'],
                                                             [listNames[name][0], 2, 'Proxy geometry visibility'],
                                                             [listNames[name][0], 3, 'Reference proxy geometry']))
                            else:
                                cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True,
                                              buttonTextIcon=[listNames[name][0], 1, 'V'],
                                              buttonStyle=[listNames[name][0], 1, '2StateButton'],
                                              buttonState=[listNames[name][0], 1, 'buttonDown'],
                                              pressCommand=[1, treeViewButton_1_ActionCallback],
                                              enableButton=([listNames[name][0], 1, 1],
                                                            [listNames[name][0], 2, 0],
                                                            [listNames[name][0], 3, 0]),
                                              buttonTooltip=[listNames[name][0], 1, 'Module visibility'])
                        else:
                            parentModuleNode = cmds.getAttr(listNames[name][0]+':moduleGrp.moduleParent')
                            
                            if parentModuleNode == 'None':
                            
                                cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True, numberOfButtons=3,
                                              addItem=(listNames[name][0], ''),
                                              selectionChangedCommand='moduleSelectionFromTreeViewCallback',
                                              editLabelCommand='processItemRenameForTreeViewListCallback')
                            else:
                                parentModuleNode = parentModuleNode.split(',')[0]
                                parentModule = mfunc.stripMRTNamespace(parentModuleNode)[0]
                                cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True, numberOfButtons=3,
                                              addItem=(listNames[name][0], parentModule), selectionChangedCommand='moduleSelectionFromTreeViewCallback', editLabelCommand='processItemRenameForTreeViewListCallback')

                            if cmds.objExists(listNames[name][0]+':proxyGeometryGrp'):
                                cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True,
                                              buttonTextIcon=([listNames[name][0], 1, 'V'], [listNames[name][0], 2, 'P'], [listNames[name][0], 3, 'R']),
                                              buttonStyle=([listNames[name][0], 1, '2StateButton'], [listNames[name][0], 2, '2StateButton'], [listNames[name][0], 3, '2StateButton']),
                                              buttonState=([listNames[name][0], 1, 'buttonDown'], [listNames[name][0], 2, 'buttonDown'], [listNames[name][0], 3, 'buttonDown']),
                                              pressCommand=([1, 'treeViewButton_1_ActionCallback'], [2, 'treeViewButton_2_ActionCallback'], [3, 'treeViewButton_3_ActionCallback']),
                                              enableButton=([listNames[name][0], 1, 1], [listNames[name][0], 2, 1], [listNames[name][0], 3, 1]),
                                              buttonTooltip=([listNames[name][0], 1, 'Module visibility'], [listNames[name][0], 2, 'Proxy geometry visibility'], [listNames[name][0], 3, 'Reference proxy geometry']))
                            else:
                                cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True,
                                              buttonTextIcon=[listNames[name][0], 1, 'V'],
                                              buttonStyle=[listNames[name][0], 1, '2StateButton'],
                                              buttonState=[listNames[name][0], 1, 'buttonDown'],
                                              pressCommand=[1, 'treeViewButton_1_ActionCallback'],
                                              enableButton=([listNames[name][0], 1, 1], [listNames[name][0], 2, 0], [listNames[name][0], 3, 0]),
                                              buttonTooltip=[listNames[name][0], 1, 'Module visibility'])


                        if listNames[name][2] == None:
                            cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True,
                                          displayLabel=[listNames[name][0], name],
                                          displayLabelSuffix=[listNames[name][0], ' (%s node module)'%listNames[name][1]])
                        else:
                            cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True,
                                          displayLabel=[listNames[name][0], name],
                                          displayLabelSuffix=[listNames[name][0], ' (%s node mirror module)'%listNames[name][1]],
                                          fontFace=[listNames[name][0], 2])
                for name in sorted(listNames):
                    v_state = cmds.getAttr(listNames[name][0]+':moduleGrp.visibility')
                    if cmds.objExists(listNames[name][0]+':proxyGeometryGrp'):
                        cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True,
                                      buttonTransparencyColor=([listNames[name][0], 1, 0.85, 0.66, 0.27], [listNames[name][0], 2, 0.57, 0.66, 1.0], [listNames[name][0], 3, 0.42, 0.87, 1.0]))
                        p_state = cmds.getAttr(listNames[name][0]+':proxyGeometryGrp.visibility')
                        r_state = cmds.getAttr(listNames[name][0]+':proxyGeometryGrp.overrideDisplayType')
                        if p_state == 0:
                            cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True,
                                          buttonTransparencyColor=[listNames[name][0], 2, 0.65, 0.71, 0.90], buttonState=[listNames[name][0], 2, 'buttonUp'])
                        if r_state == 0:
                            cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True,
                                          buttonTransparencyColor=[listNames[name][0], 3, 0.68, 0.85, 0.90], buttonState=[listNames[name][0], 3, 'buttonUp'])
                        if v_state == 0:
                            cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True,
                                          buttonTransparencyColor=[listNames[name][0], 1, 0.71, 0.66, 0.56], buttonState=[listNames[name][0], 1, 'buttonUp'])
                    else:
                        cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True,
                                      buttonTransparencyColor=([listNames[name][0], 1, 0.85, 0.66, 0.27], [listNames[name][0], 2, 0.39, 0.39, 0.39], [listNames[name][0], 3, 0.39, 0.39, 0.39]))
                        if v_state == 0:
                            cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True,
                                          buttonTransparencyColor=[listNames[name][0], 1, 0.71, 0.66, 0.56], buttonState=[listNames[name][0], 1, 'buttonUp'])
        else:
            if _maya_version >=2013:
                cmds.scrollLayout(self.uiVars['moduleList_Scroll'], edit=True, height=40)
                cmds.frameLayout(self.uiVars['moduleList_fLayout'], edit=True, height=32)
                cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True, numberOfButtons=1, addItem=('< no current module in scene >', ''), hideButtons=True)
                cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True, font=['< no current module in scene >', 'boldLabelFont'], editLabelCommand=processItemRenameForTreeViewListCallback, enable=False)
                cmds.rowLayout(self.uiVars['sortModuleList_row'], edit=True, enable=False)
            else:
                cmds.scrollLayout(self.uiVars['moduleList_Scroll'], edit=True, height=40)
                cmds.frameLayout(self.uiVars['moduleList_fLayout'], edit=True, height=32)
                cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True, numberOfButtons=1, addItem=('< no current module in scene >', ''), hideButtons=True)
                cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True, font=['< no current module in scene >', 'boldLabelFont'], editLabelCommand='processItemRenameForTreeViewListCallback', enable=False)
                cmds.rowLayout(self.uiVars['sortModuleList_row'], edit=True, enable=False)

        cmds.namespace(setNamespace=currentNamespace)
        cmds.undoInfo(stateWithoutFlush=True)

    def makeCollectionFromSceneTreeViewModulesUI(self, *args, allModules=False, auto=None):
        # NESTED_DEF_1 #
        def saveModuleCollectionFromDescription(collectionDescription, treeViewSelection, *args):
            # Create a module collection from the passed-in information.
            # Close the windows for module description and its error prompt window.
            try:
                cmds.deleteUI('mrt_collection_noDescpError_UI_window')
            except:
                pass
            try:
                cmds.deleteUI('mrt_collectionDescription_input_UI_window')
            except:
                pass
            # Get the last directory for module collection save. If error, get the default directory.
            fileFilter = 'MRT Module Collection Files (*.mrtmc)'
            ui_preferences_file = open(self.ui_preferences_path, 'rb')
            ui_preferences = cPickle.load(ui_preferences_file)
            ui_preferences_file.close()
            startDir = ui_preferences['startDirectoryForCollectionSave']
            if not os.path.exists(startDir):
                startDir = ui_preferences['defaultStartDirectoryForCollectionSave']
            # Get the file path for saving the collection. Save it as the new preferred location for saving module collections.
            if not auto:
                fileReturn = cmds.fileDialog2(caption='Save module collection', fileFilter=fileFilter, startingDirectory=startDir, dialogStyle=2)
                if fileReturn == None:
                    return
                ui_preferences['startDirectoryForCollectionSave'] = fileReturn[0].rpartition('/')[0]
                ui_preferences_file = open(self.ui_preferences_path, 'wb')
                cPickle.dump(ui_preferences, ui_preferences_file, cPickle.HIGHEST_PROTOCOL)
                ui_preferences_file.close()
            if auto:
                fileReturn = [auto]

            for module in treeViewSelection[:]:
                if cmds.attributeQuery('mirrorModuleNamespace', node=module+':moduleGrp', exists=True):
                    mirrorModule = cmds.getAttr(module+':moduleGrp.mirrorModuleNamespace')
                    treeViewSelection.append(mirrorModule)

            modulesToBeCollected = treeViewSelection[:]

            parentCollectStatus = cmds.radioCollection(self.uiVars['moduleSaveColl_options_parentsCheckRadioCollection'], query=True, select=True)
            if parentCollectStatus == 'Direct_Parent':
                for module in treeViewSelection:
                    parentModuleNode = cmds.getAttr(module+':moduleGrp.moduleParent')
                    if parentModuleNode != 'None':
                        parentModuleNode = parentModuleNode.split(',')[0]
                        parentModule = mfunc.stripMRTNamespace(parentModuleNode)[0]
                        modulesToBeCollected.append(parentModule)

            if parentCollectStatus == 'All_Parents':
                for module in treeViewSelection:
                    allParentsModuleList = mfunc.traverseParentModules(module)[0]
                    if len(allParentsModuleList):
                        modulesToBeCollected = mfunc.concatenateCommonNamesFromHierarchyData(allParentsModuleList, modulesToBeCollected)

            if parentCollectStatus == 'None':
                pass

            childrenCollectStatus = cmds.radioCollection(self.uiVars['moduleSaveColl_options_childrenCheckRadioCollection'], query=True, select=True)
            if childrenCollectStatus == 'Direct_Children':
                for module in treeViewSelection:
                    childrenModuleDict = mfunc.traverseChildrenModules(module)
                    if childrenModuleDict:
                        modulesToBeCollected += [module for module in childrenModuleDict]
            if childrenCollectStatus == 'All_Children':
                for module in treeViewSelection:
                    allChildrenModuleDict = mfunc.traverseChildrenModules(module, allChildren=True)
                    if allChildrenModuleDict:
                        modulesToBeCollected = mfunc.concatenateCommonNamesFromHierarchyData(allChildrenModuleDict, modulesToBeCollected)
            if childrenCollectStatus == 'None':
                pass

            for module in copy.copy(modulesToBeCollected):
                if cmds.attributeQuery('mirrorModuleNamespace', node=module+':moduleGrp', exists=True):
                    mirrorModule = cmds.getAttr(module+':moduleGrp.mirrorModuleNamespace')
                    modulesToBeCollected.append(mirrorModule)

            currentNamespace = cmds.namespaceInfo(currentNamespace=True)
            cmds.namespace(setNamespace=':')

            modulesToBeUnparented = {}
            allModuleNamespaces = mfunc.returnMRT_Namespaces(cmds.namespaceInfo(listOnlyNamespaces=True))
            for module in modulesToBeCollected:
                moduleParentNode = cmds.getAttr(module+':moduleGrp.moduleParent')
                if moduleParentNode != 'None':
                    parentModuleNodeAttr = moduleParentNode.split(',')
                    moduleParent = mfunc.stripMRTNamespace(parentModuleNodeAttr[0])[0]
                    if not moduleParent in modulesToBeCollected:
                        modulesToBeUnparented[module] = parentModuleNodeAttr[0]
            if modulesToBeUnparented:
                for module in modulesToBeUnparented:
                    cmds.lockNode(module+':module_container', lock=False, lockUnpublished=False)
                    #cmds.delete(module+':moduleParentRepresentationSegment_endLocator_pointConstraint')
                    constraint = cmds.listRelatives(module+':moduleParentRepresentationSegment_segmentCurve_endLocator', children=True, fullPath=True, type='constraint')
                    cmds.delete(constraint)
                    cmds.setAttr(module+':moduleGrp.moduleParent', 'None', type='string')
                    cmds.setAttr(module+':moduleParentRepresentationGrp.visibility', 0)
                    cmds.lockNode(module+':module_container', lock=True, lockUnpublished=True)

            # Get the previous selection.
            selection = cmds.ls(selection=True)

            moduleObjectsToBeCollected = []
            for module in modulesToBeCollected:
                moduleObjectsToBeCollected.append(module+':module_container')
                if cmds.objExists(module+':proxyGeometryGrp'):
                    moduleObjectsToBeCollected.append(module+':proxyGeometryGrp')

            if os.path.exists(fileReturn[0]):
                os.remove(fileReturn[0])
            mrtmc_fObject = {}
            mrtmc_fObject['collectionDescrp'] = collectionDescription
            cmds.select(moduleObjectsToBeCollected, replace=True)
            mfunc.deleteMirrorMoveConnections()
            tempFilePath = fileReturn[0].rpartition('.mrtmc')[0]+'_temp.ma'
            cmds.file(tempFilePath, force=True, options='v=1', type='mayaAscii', exportSelected=True, pr=True)
            tempFile_fObject = open(tempFilePath)
            i = 1
            for line in tempFile_fObject:
                mrtmc_fObject['collectionData_line_'+str(i)] = line
                i +=1
            tempFile_fObject.close()
            os.remove(tempFilePath)
            mrtmc_fObject_file = open(fileReturn[0], 'wb')
            cPickle.dump(mrtmc_fObject, mrtmc_fObject_file, cPickle.HIGHEST_PROTOCOL)
            mrtmc_fObject_file.close()
            del mrtmc_fObject

            if not auto:
                ui_preferences_file = open(self.ui_preferences_path, 'rb')
                ui_preferences = cPickle.load(ui_preferences_file)
                ui_preferences_file.close()
                loadNewCollections = ui_preferences['autoLoadNewSavedModuleCollectionToListStatus']
                if loadNewCollections:
                    self.loadModuleCollectionsForUI([fileReturn[0]])

            if modulesToBeUnparented:
                for module in modulesToBeUnparented:
                    cmds.lockNode(module+':module_container', lock=False, lockUnpublished=False)
                    pointConstraint = cmds.pointConstraint(modulesToBeUnparented[module], module+':moduleParentRepresentationSegment_segmentCurve_endLocator', maintainOffset=False, name=module+':moduleParentRepresentationSegment_endLocator_pointConstraint')[0]
                    mfunc.addNodesToContainer(module+':module_container', [pointConstraint])
                    cmds.setAttr(module+':moduleGrp.moduleParent', modulesToBeUnparented[module], type='string')
                    cmds.setAttr(module+':moduleParentRepresentationGrp.visibility', 1)
                    cmds.lockNode(module+':module_container', lock=True, lockUnpublished=True)

            if len(selection):
                cmds.select(selection, replace=True)
            else:
                cmds.select(clear=True)
            cmds.namespace(setNamespace=currentNamespace)
        # NESTED_DEF_2 #
        def saveModuleCollectionFromDescriptionProcessInputUI(*args):
            # Process the module collection description input before proceeding with creating a module collection.
            if allModules:
                treeViewSelection = mrt_namespaces
            else:
                # During the proces of entering a description, if the selection changes.
                treeViewSelection = cmds.treeView(self.uiVars['sceneModuleList_treeView'], query=True, selectItem=True)
                if treeViewSelection == None:
                    cmds.warning('MRT Error: Module collection error. No module(s) selected for making a collection.')
                    return
            # Check the description. if empty, notify the user, or proceed.
            if not auto:
                collectionDescription = cmds.scrollField(self.uiVars['collectionDescpWindowScrollField'], query=True, text=True)
                if collectionDescription == '':
                    try:
                        cmds.deleteUI('mrt_collection_noDescpError_UI_window')
                    except:
                        pass
                    self.uiVars['collectionNoDescpErrorWindow'] = cmds.window('mrt_collection_noDescpError_UI_window', title='Module collection warning', maximizeButton=False, sizeable=False)
                    try:
                        cmds.windowPref('mrt_collection_noDescpError_UI_window', remove=True)
                    except:
                        pass
                    cmds.frameLayout(visible=True, borderVisible=False, collapsable=False, labelVisible=False, height=90, width=220, marginWidth=20, marginHeight=15)
                    cmds.text(label='Are you sure you want to continue saving a collection with an empty description?')
                    cmds.rowLayout(numberOfColumns=2, columnAttach=([1, 'left', 90], [2, 'left', 30]), rowAttach=([1, 'top', 8], [2, 'top', 8]))
                    cmds.button(label='Continue', width=90, command=partial(saveModuleCollectionFromDescription, collectionDescription, treeViewSelection))
                    ##cmds.button(label='Revert', width=90, command=('cmds.deleteUI(\"'+self.uiVars['collectionNoDescpErrorWindow']+'\")'))
                    cmds.button(label='Revert', width=90, command=partial(self.closeWindow, self.uiVars['collectionNoDescpErrorWindow']))
                    cmds.showWindow(self.uiVars['collectionNoDescpErrorWindow'])
                else:
                    saveModuleCollectionFromDescription(collectionDescription, treeViewSelection)
            if auto:
                saveModuleCollectionFromDescription('Auto generated collection', treeViewSelection)
        # MAIN DEF_BEGINS #
        mrt_namespaces = []
        if allModules:
            # If all modules are to be included in the collection.
            currentNamespace = cmds.namespaceInfo(currentNamespace=True)
            cmds.namespace(setNamespace=':')
            namespaces = cmds.namespaceInfo(listOnlyNamespaces=True)
            cmds.namespace(setNamespace=currentNamespace)
            mrt_namespaces = mfunc.returnMRT_Namespaces(namespaces)
            if mrt_namespaces == None:
                # If no modules exist in the scene.
                cmds.warning('MRT Error: Module collection error. No module(s) in the scene for making a collection.')
                return
        else:
            # If selected modules are to be in a collection.
            treeViewSelection = cmds.treeView(self.uiVars['sceneModuleList_treeView'], query=True, selectItem=True)
            if treeViewSelection == None:
                # If no modules are selected.
                cmds.warning('MRT Error: Module collection error. No module(s) selected for making a collection.')
                return
        # Create a window UI for entering the module collection description.
        if not auto:
            try:
                cmds.deleteUI('mrt_collectionDescription_input_UI_window')
            except:
                pass
            self.uiVars['collectionDescpWindow'] = cmds.window('mrt_collectionDescription_input_UI_window', title='Module collection description', height=150, maximizeButton=False, sizeable=False)
            try:
                cmds.windowPref('mrt_collectionDescription_input_UI_window', remove=True)
            except:
                pass
            self.uiVars['collectionDescpWindowColumn'] = cmds.columnLayout(adjustableColumn=True)
            cmds.text(label='')
            cmds.text('Enter description for module collection', align='center', font='boldLabelFont')
            cmds.frameLayout(visible=True, borderVisible=False, collapsable=False, labelVisible=False, height=75, width=300, marginWidth=5, marginHeight=10)
            self.uiVars['collectionDescpWindowScrollField'] = cmds.scrollField(preventOverride=True, wordWrap=True)
            cmds.setParent(self.uiVars['collectionDescpWindowColumn'])
            cmds.rowLayout(numberOfColumns=2, columnAttach=([1, 'left', 28], [2, 'left', 20]))
            cmds.button(label='Save collection', width=130, command=saveModuleCollectionFromDescriptionProcessInputUI)
            ##cmds.button(label='Cancel', width=90, command=('cmds.deleteUI(\"'+self.uiVars['collectionDescpWindow']+'\")'))
            cmds.button(label='Cancel', width=90, command=partial(self.closeWindow, self.uiVars['collectionDescpWindow']))
            cmds.setParent(self.uiVars['collectionDescpWindowColumn'])
            cmds.text(label='')
            cmds.showWindow(self.uiVars['collectionDescpWindow'])
        if auto:
            saveModuleCollectionFromDescriptionProcessInputUI()

    def performModuleRename(self, *args):
        mfunc.deleteMirrorMoveConnections()
        newUserSpecifiedName = cmds.textField(self.uiVars['moduleRename_textField'], query=True, text=True)
        newUserSpecifiedName = newUserSpecifiedName.lower()
        selectedModule = cmds.ls(selection=True)
        selectedModule.reverse()
        selectedModule = selectedModule[0]
        currentNamespaceForSelectedModule = mfunc.stripMRTNamespace(selectedModule)[0]
        newNamespace = currentNamespaceForSelectedModule.rpartition('__')[0] + '__' + newUserSpecifiedName
        currentNamespace = cmds.namespaceInfo(currentNamespace=True)
        cmds.namespace(setNamespace=':')
        sceneNamespaces = mfunc.returnMRT_Namespaces(cmds.namespaceInfo(listOnlyNamespaces=True))
        currentModuleUserNames = []
        if newNamespace == currentNamespaceForSelectedModule:
            return
        if sceneNamespaces:
            for namespace in sceneNamespaces:
                userSpecifiedName = namespace.partition('__')[2]
                if newUserSpecifiedName == userSpecifiedName:
                    cmds.warning('MRT Error: Namespace conflict. The module name "%s" already exists in the scene.'%newUserSpecifiedName)
                    return
        if len(self.modules):
            for (key, value) in self.modules.items():
                i = 0
                for item in value:
                    if item == currentNamespaceForSelectedModule:
                        self.modules[key][i] = newNamespace
                        break
                    i += 1
        children = mfunc.traverseChildrenModules(currentNamespaceForSelectedModule)
        if children:
            for childNamespace in children:
                cmds.lockNode(childNamespace+':module_container', lock=False, lockUnpublished=False)
                currentParentInfo = cmds.getAttr(childNamespace+':moduleGrp.moduleParent')
                currentParentInfo = currentParentInfo.split(',')
                currentParentNamespaceInfo = mfunc.stripMRTNamespace(currentParentInfo[0])
                newParentNode = newNamespace+':'+currentParentNamespaceInfo[1]
                newParentInfo = str(newParentNode)+','+str(currentParentInfo[1])
                cmds.setAttr(childNamespace+':moduleGrp.moduleParent', newParentInfo, type='string')
                cmds.lockNode(childNamespace+':module_container', lock=True, lockUnpublished=True)

        cmds.namespace(addNamespace=newNamespace)
        cmds.lockNode(currentNamespaceForSelectedModule+':module_container', lock=False, lockUnpublished=False)
        cmds.namespace(setNamespace=':')
        cmds.namespace(moveNamespace=[currentNamespaceForSelectedModule, newNamespace])
        cmds.namespace(removeNamespace=currentNamespaceForSelectedModule)
        if cmds.attributeQuery('mirrorModuleNamespace', node=newNamespace+':moduleGrp', exists=True):
            mirrorModuleNamespace = cmds.getAttr(newNamespace+':moduleGrp.mirrorModuleNamespace')
            cmds.lockNode(mirrorModuleNamespace+':module_container', lock=False, lockUnpublished=False)
            cmds.setAttr(mirrorModuleNamespace+':moduleGrp.mirrorModuleNamespace', newNamespace, type='string')
            cmds.lockNode(mirrorModuleNamespace+':module_container', lock=True, lockUnpublished=True)
        cmds.lockNode(newNamespace+':module_container', lock=True, lockUnpublished=True)

        selection = newNamespace+':'+mfunc.stripMRTNamespace(selectedModule)[1]
        cmds.select(selection, replace=True)
        self.updateListForSceneModulesInUI()
        self.clearParentModuleField()
        self.clearChildModuleField()
        if cmds.namespace(exists=currentNamespace):
            cmds.namespace(setNamespace=currentNamespace)

    def performModuleDuplicate_UI_wrapper(self, *args):
        try:
            cmds.deleteUI('mrt_duplicateModuleAction_UI_window')
        except:
            pass
        self.uiVars['duplicateActionWindow'] = cmds.window('mrt_duplicateModuleAction_UI_window', title='Duplicate Module', widthHeight=(300, 150), maximizeButton=False, sizeable=False)
        try:
            cmds.windowPref('mrt_duplicateModuleAction_UI_window', remove=True)
        except:
            pass
        self.uiVars['duplicateActionWindowColumn'] = cmds.columnLayout(adjustableColumn=True)
        cmds.text(label='')
        cmds.text('Enter relative offset for duplication (translation)', align='center', font='boldLabelFont')
        self.uiVars['duplicateActionWindowFloatfieldGrp'] = cmds.floatFieldGrp(numberOfFields=3, label='Offset (world units)', value1=1.0, value2=1.0, value3=1.0, columnAttach=([1, 'left', 15], [2, 'left', 1], [3, 'left', 1], [4, 'right', 12]), columnWidth4=[120, 80, 80, 90], rowAttach=([1, 'top', 14], [2, 'top', 10], [3, 'top', 10], [4, 'top', 10]))
        cmds.rowLayout(numberOfColumns=1, columnAttach=[1, 'left', 110], rowAttach=[1, 'top', 2])
        self.uiVars['duplicateAction_maintainParentCheckbox'] = cmds.checkBox(label='Maintain parent connections', enable=True, value=True)
        cmds.setParent(self.uiVars['duplicateActionWindowColumn'])
        cmds.rowLayout(numberOfColumns=1, columnAttach=[1, 'left', 115], rowAttach=[1, 'top', 5])
        cmds.button(label='OK', width=150, command=self.performModuleDuplicate)
        cmds.setParent(self.uiVars['duplicateActionWindowColumn'])
        cmds.text(label='')
        cmds.showWindow(self.uiVars['duplicateActionWindow'])

    def performModuleDuplicate(self, *args):
        selection = cmds.ls(selection=True)
        if not selection:
            cmds.warning('MRT Error: Duplicate Module Error. Nothing is selected. Please select a module to perform duplication.')
            return
        selection.reverse()
        selection = selection[0]
        if mfunc.stripMRTNamespace(selection) == None:
            cmds.warning('MRT Error: Duplicate Module Error. Invalid selection. Please select a module.')
            return
        moduleNamespace = mfunc.stripMRTNamespace(selection)[0]
        moduleAttrsDict = mfunc.returnModuleAttrsFromScene(moduleNamespace)
        mfunc.createModuleFromAttributes(moduleAttrsDict)
        cmds.select(clear=True)
        if cmds.checkBox(self.uiVars['duplicateAction_maintainParentCheckbox'], query=True, value=True):
            for (module, parentModuleNode) in moduleAttrsDict['moduleParentInfo']:
                if module != None and parentModuleNode != 'None':
                    parentModuleNodeAttr = parentModuleNode.split(',')
                    cmds.lockNode(module+':module_container', lock=False, lockUnpublished=False)
                    pointConstraint = cmds.pointConstraint(parentModuleNodeAttr[0], module+':moduleParentRepresentationSegment_segmentCurve_endLocator', maintainOffset=False, name=module+':moduleParentRepresentationSegment_endLocator_pointConstraint')[0]
                    mfunc.addNodesToContainer(module+':module_container', [pointConstraint])
                    cmds.setAttr(module+':moduleGrp.moduleParent', parentModuleNode, type='string')
                    cmds.setAttr(module+':moduleParentRepresentationGrp.visibility', 1)
                    if parentModuleNodeAttr[1] == 'Hierarchical':
                        cmds.setAttr(module+':moduleParentRepresentationSegment_hierarchy_representationShape.overrideColor', 16)
                    cmds.lockNode(module+':module_container', lock=True, lockUnpublished=True)
        cmds.select(clear=True)
        # If proxy geometry is enabled.
        if moduleAttrsDict['node_compnts'][2] == True:
            # If elbow proxy is enabled.
            if moduleAttrsDict['proxy_geo_options'][1] == True:
                for i in range(moduleAttrsDict['num_nodes']):
                    if i == 0:
                        orig_proxy_elbow_transform = moduleAttrsDict['orig_module_Namespace']+':root_node_transform_proxy_elbow_geo'
                        proxy_elbow_transform = moduleAttrsDict['module_Namespace']+':root_node_transform_proxy_elbow_geo'
                        if cmds.objExists(orig_proxy_elbow_transform+'_preTransform'):
                            cmds.delete(proxy_elbow_transform)
                            duplicatedTransform = cmds.duplicate(orig_proxy_elbow_transform, name=moduleAttrsDict['module_Namespace']+':root_node_transform_proxy_elbow_geo')[0]
                            cmds.parent(duplicatedTransform, proxy_elbow_transform+'_scaleTransform', relative=True)
                        else:
                            cmds.delete(proxy_elbow_transform+'_preTransform')
                    elif i == moduleAttrsDict['num_nodes']-1:
                        orig_proxy_elbow_transform = moduleAttrsDict['orig_module_Namespace']+':end_node_transform_proxy_elbow_geo'
                        proxy_elbow_transform = moduleAttrsDict['module_Namespace']+':end_node_transform_proxy_elbow_geo'
                        if cmds.objExists(orig_proxy_elbow_transform+'_preTransform'):
                            cmds.delete(proxy_elbow_transform)
                            duplicatedTransform = cmds.duplicate(orig_proxy_elbow_transform, name=moduleAttrsDict['module_Namespace']+':end_node_transform_proxy_elbow_geo')[0]
                            cmds.parent(duplicatedTransform, proxy_elbow_transform+'_scaleTransform', relative=True)
                        else:
                            cmds.delete(proxy_elbow_transform+'_preTransform')
                    else:
                        proxy_elbow_transform = moduleAttrsDict['module_Namespace']+':node_'+str(i)+'_transform_proxy_elbow_geo'
                        orig_proxy_elbow_transform = moduleAttrsDict['orig_module_Namespace']+':node_'+str(i)+'_transform_proxy_elbow_geo'
                        if cmds.objExists(orig_proxy_elbow_transform+'_preTransform'):
                            cmds.delete(proxy_elbow_transform)
                            duplicatedTransform = cmds.duplicate(orig_proxy_elbow_transform, name=moduleAttrsDict['module_Namespace']+':node_'+str(i)+'_transform_proxy_elbow_geo')[0]
                            cmds.parent(duplicatedTransform, proxy_elbow_transform+'_scaleTransform', relative=True)
                        else:
                            cmds.delete(proxy_elbow_transform+'_preTransform')
            # If bone proxy is enabled.
            if moduleAttrsDict['proxy_geo_options'][0] == True:
                for i in range(moduleAttrsDict['num_nodes']-1):
                    if i == 0:
                        orig_proxy_bone_transform = moduleAttrsDict['orig_module_Namespace']+':root_node_transform_proxy_bone_geo'
                        proxy_bone_transform = moduleAttrsDict['module_Namespace']+':root_node_transform_proxy_bone_geo'
                        if cmds.objExists(orig_proxy_bone_transform+'_preTransform'):
                            cmds.delete(proxy_bone_transform)
                            duplicatedTransform = cmds.duplicate(orig_proxy_bone_transform, name=moduleAttrsDict['module_Namespace']+':root_node_transform_proxy_bone_geo')[0]
                            cmds.parent(duplicatedTransform, proxy_bone_transform+'_scaleTransform', relative=True)
                        else:
                            cmds.delete(proxy_bone_transform+'_preTransform')
                    else:
                        proxy_bone_transform = moduleAttrsDict['module_Namespace']+':node_'+str(i)+'_transform_proxy_bone_geo'
                        orig_proxy_bone_transform = moduleAttrsDict['orig_module_Namespace']+':node_'+str(i)+'_transform_proxy_bone_geo'
                        if cmds.objExists(orig_proxy_bone_transform+'_preTransform'):
                            cmds.delete(proxy_bone_transform)
                            duplicatedTransform = cmds.duplicate(orig_proxy_bone_transform, name=moduleAttrsDict['module_Namespace']+':node_'+str(i)+'_transform_proxy_bone_geo')[0]
                            cmds.parent(duplicatedTransform, proxy_bone_transform+'_scaleTransform', relative=True)
                        else:
                            cmds.delete(proxy_bone_transform+'_preTransform')
            # If mirror is enabled, options for the proxies in the mirror module.
            if moduleAttrsDict['mirror_options'][0] == 'On':
                # If elbow proxy is enabled.
                if moduleAttrsDict['proxy_geo_options'][1] == True:
                    for i in range(moduleAttrsDict['num_nodes']):
                        if i == 0:
                            orig_proxy_elbow_transform = moduleAttrsDict['orig_mirror_module_Namespace']+':root_node_transform_proxy_elbow_geo'
                            proxy_elbow_transform = moduleAttrsDict['mirror_module_Namespace']+':root_node_transform_proxy_elbow_geo'
                            if moduleAttrsDict['proxy_geo_options'][3] == 'Off':
                                if cmds.objExists(orig_proxy_elbow_transform+'_preTransform'):
                                    cmds.delete(proxy_elbow_transform)
                                    duplicatedTransform = cmds.duplicate(orig_proxy_elbow_transform, name=moduleAttrsDict['mirror_module_Namespace']+':root_node_transform_proxy_elbow_geo')[0]
                                    cmds.parent(duplicatedTransform, proxy_elbow_transform+'_scaleTransform', relative=True)
                                else:
                                    cmds.delete(proxy_elbow_transform+'_preTransform')
                            if moduleAttrsDict['proxy_geo_options'][3] == 'On':
                                mirror_proxy_elbow_transform = moduleAttrsDict['module_Namespace']+':root_node_transform_proxy_elbow_geo'
                                if cmds.objExists(mirror_proxy_elbow_transform+'_preTransform'):
                                    cmds.delete(proxy_elbow_transform)
                                    duplicatedTransform = cmds.duplicate(mirror_proxy_elbow_transform, instanceLeaf=True, name=moduleAttrsDict['mirror_module_Namespace']+':root_node_transform_proxy_elbow_geo')[0]
                                    cmds.parent(duplicatedTransform, proxy_elbow_transform+'_scaleTransform', relative=True)
                                else:
                                    cmds.delete(proxy_elbow_transform+'_preTransform')
                        elif i == moduleAttrsDict['num_nodes']-1:
                            orig_proxy_elbow_transform = moduleAttrsDict['orig_mirror_module_Namespace']+':end_node_transform_proxy_elbow_geo'
                            proxy_elbow_transform = moduleAttrsDict['mirror_module_Namespace']+':end_node_transform_proxy_elbow_geo'
                            if moduleAttrsDict['proxy_geo_options'][3] == 'Off':
                                if cmds.objExists(orig_proxy_elbow_transform+'_preTransform'):
                                    cmds.delete(proxy_elbow_transform)
                                    duplicatedTransform = cmds.duplicate(orig_proxy_elbow_transform, name=moduleAttrsDict['mirror_module_Namespace']+':end_node_transform_proxy_elbow_geo')[0]
                                    cmds.parent(duplicatedTransform, proxy_elbow_transform+'_scaleTransform', relative=True)
                                else:
                                    cmds.delete(proxy_elbow_transform+'_preTransform')
                            if moduleAttrsDict['proxy_geo_options'][3] == 'On':
                                mirror_proxy_elbow_transform = moduleAttrsDict['module_Namespace']+':end_node_transform_proxy_elbow_geo'
                                if cmds.objExists(mirror_proxy_elbow_transform+'_preTransform'):
                                    cmds.delete(proxy_elbow_transform)
                                    duplicatedTransform = cmds.duplicate(mirror_proxy_elbow_transform, instanceLeaf=True, name=moduleAttrsDict['mirror_module_Namespace']+':end_node_transform_proxy_elbow_geo')[0]
                                    cmds.parent(duplicatedTransform, proxy_elbow_transform+'_scaleTransform', relative=True)
                                else:
                                    cmds.delete(proxy_elbow_transform+'_preTransform')
                        else:
                            orig_proxy_elbow_transform = moduleAttrsDict['orig_mirror_module_Namespace']+':node_'+str(i)+'_transform_proxy_elbow_geo'
                            proxy_elbow_transform = moduleAttrsDict['mirror_module_Namespace']+':node_'+str(i)+'_transform_proxy_elbow_geo'
                            if moduleAttrsDict['proxy_geo_options'][3] == 'Off':
                                if cmds.objExists(orig_proxy_elbow_transform+'_preTransform'):
                                    cmds.delete(proxy_elbow_transform)
                                    duplicatedTransform = cmds.duplicate(orig_proxy_elbow_transform, name=moduleAttrsDict['mirror_module_Namespace']+':node_'+str(i)+'_transform_proxy_elbow_geo')[0]
                                    cmds.parent(duplicatedTransform, proxy_elbow_transform+'_scaleTransform', relative=True)
                                else:
                                    cmds.delete(proxy_elbow_transform+'_preTransform')
                            if moduleAttrsDict['proxy_geo_options'][3] == 'On':
                                mirror_proxy_elbow_transform = moduleAttrsDict['module_Namespace']+':node_'+str(i)+'_transform_proxy_elbow_geo'
                                if cmds.objExists(mirror_proxy_elbow_transform+'_preTransform'):
                                    cmds.delete(proxy_elbow_transform)
                                    duplicatedTransform = cmds.duplicate(mirror_proxy_elbow_transform, instanceLeaf=True, name=moduleAttrsDict['mirror_module_Namespace']+':node_'+str(i)+'_transform_proxy_elbow_geo')[0]
                                    cmds.parent(duplicatedTransform, proxy_elbow_transform+'_scaleTransform', relative=True)
                                else:
                                    cmds.delete(proxy_elbow_transform+'_preTransform')
                # If bone proxy is enabled.
                if moduleAttrsDict['proxy_geo_options'][0] == True:
                    for i in range(moduleAttrsDict['num_nodes']-1):
                        if i == 0:
                            orig_proxy_bone_transform = moduleAttrsDict['orig_mirror_module_Namespace']+':root_node_transform_proxy_bone_geo'
                            proxy_bone_transform = moduleAttrsDict['mirror_module_Namespace']+':root_node_transform_proxy_bone_geo'
                            if moduleAttrsDict['proxy_geo_options'][3] == 'Off':
                                if cmds.objExists(orig_proxy_bone_transform+'_preTransform'):
                                    cmds.delete(proxy_bone_transform)
                                    duplicatedTransform = cmds.duplicate(orig_proxy_bone_transform, name=moduleAttrsDict['mirror_module_Namespace']+':root_node_transform_proxy_bone_geo')[0]
                                    cmds.parent(duplicatedTransform, proxy_bone_transform+'_scaleTransform', relative=True)
                                else:
                                    cmds.delete(proxy_bone_transform+'_preTransform')
                            if moduleAttrsDict['proxy_geo_options'][3] == 'On':
                                mirror_proxy_bone_transform = moduleAttrsDict['module_Namespace']+':root_node_transform_proxy_bone_geo'
                                if cmds.objExists(mirror_proxy_bone_transform+'_preTransform'):
                                    cmds.delete(proxy_bone_transform)
                                    duplicatedTransform = cmds.duplicate(mirror_proxy_bone_transform, instanceLeaf=True, name=moduleAttrsDict['mirror_module_Namespace']+':root_node_transform_proxy_bone_geo')[0]
                                    cmds.parent(duplicatedTransform, proxy_bone_transform+'_scaleTransform', relative=True)
                                else:
                                    cmds.delete(proxy_bone_transform+'_preTransform')
                        else:
                            orig_proxy_bone_transform = moduleAttrsDict['orig_mirror_module_Namespace']+':node_'+str(i)+'_transform_proxy_bone_geo'
                            proxy_bone_transform = moduleAttrsDict['mirror_module_Namespace']+':node_'+str(i)+'_transform_proxy_bone_geo'
                            if moduleAttrsDict['proxy_geo_options'][3] == 'Off':
                                if cmds.objExists(orig_proxy_bone_transform+'_preTransform'):
                                    cmds.delete(proxy_bone_transform)
                                    duplicatedTransform = cmds.duplicate(orig_proxy_bone_transform, name=moduleAttrsDict['mirror_module_Namespace']+':node_'+str(i)+'_transform_proxy_bone_geo')[0]
                                    cmds.parent(duplicatedTransform, proxy_bone_transform+'_scaleTransform', relative=True)
                                else:
                                    cmds.delete(proxy_bone_transform+'_preTransform')
                            if moduleAttrsDict['proxy_geo_options'][3] == 'On':
                                mirror_proxy_bone_transform = moduleAttrsDict['module_Namespace']+':node_'+str(i)+'_transform_proxy_bone_geo'
                                if cmds.objExists(mirror_proxy_bone_transform+'_preTransform'):
                                    cmds.delete(proxy_bone_transform)
                                    duplicatedTransform = cmds.duplicate(mirror_proxy_bone_transform, instanceLeaf=True, name=moduleAttrsDict['mirror_module_Namespace']+':node_'+str(i)+'_transform_proxy_bone_geo')[0]
                                    cmds.parent(duplicatedTransform, proxy_bone_transform+'_scaleTransform', relative=True)
                                else:
                                    cmds.delete(proxy_bone_transform+'_preTransform')

        self.updateListForSceneModulesInUI()

        offset = cmds.floatFieldGrp(self.uiVars['duplicateActionWindowFloatfieldGrp'], query=True, value=True)
        if moduleAttrsDict['node_type'] != 'SplineNode':
            if cmds.getAttr(moduleAttrsDict['module_Namespace']+':moduleGrp.onPlane')[0] == '+':
                selection = moduleAttrsDict['module_Namespace']+':module_transform'
                cmds.evalDeferred(partial(mfunc.moveSelectionOnIdle, selection, offset), lowestPriority=True)
            else:
                selection = moduleAttrsDict['mirror_module_Namespace']+':module_transform'
                cmds.evalDeferred(partial(mfunc.moveSelectionOnIdle, selection, offset), lowestPriority=True)
        else:
            if cmds.getAttr(moduleAttrsDict['module_Namespace']+':moduleGrp.onPlane')[0] == '+':
                selection = moduleAttrsDict['module_Namespace']+':splineStartHandleTransform'
                cmds.evalDeferred(partial(mfunc.moveSelectionOnIdle, selection, offset), lowestPriority=True)
            else:
                selection = moduleAttrsDict['mirror_module_Namespace']+':splineStartHandleTransform'
                cmds.evalDeferred(partial(mfunc.moveSelectionOnIdle, selection, offset), lowestPriority=True)
            if cmds.getAttr(moduleAttrsDict['module_Namespace']+':moduleGrp.onPlane')[0] == '+':
                selection = moduleAttrsDict['module_Namespace']+':splineEndHandleTransform'
                cmds.evalDeferred(partial(mfunc.moveSelectionOnIdle, selection, offset), lowestPriority=True)
            else:
                selection = moduleAttrsDict['mirror_module_Namespace']+':splineEndHandleTransform'
                cmds.evalDeferred(partial(mfunc.moveSelectionOnIdle, selection, offset), lowestPriority=True)


        cmds.evalDeferred(partial(mfunc.performOnIdle), lowestPriority=True)

    def performModuleDeletion(self, *args):
        currentNamespace = cmds.namespaceInfo(currentNamespace=True)
        cmds.namespace(setNamespace=':')
        selection = mel.eval("ls -sl -type dagNode")
        moduleSelection = selection[0]
        moduleSelectionNamespace = mfunc.stripMRTNamespace(moduleSelection)[0]
        modulesToBeRemoved = [moduleSelectionNamespace]
        if cmds.attributeQuery('mirrorModuleNamespace', node=moduleSelectionNamespace+':moduleGrp', exists=True):
            modulesToBeRemoved.append(cmds.getAttr(moduleSelectionNamespace+':moduleGrp.mirrorModuleNamespace'))
        if len(self.modules):
            for (key, value) in self.modules.items():
                if len(modulesToBeRemoved) == 1:
                    if modulesToBeRemoved[0] in value:
                        self.modules.pop(key)
                        break
                if len(modulesToBeRemoved) == 2:
                    if modulesToBeRemoved[0] in value and modulesToBeRemoved[1] in value:
                        self.modules.pop(key)
                        break
        mfunc.deleteMirrorMoveConnections()
        for namespace in modulesToBeRemoved:
            self.removeChildrenModules(namespace)
            moduleContainer = namespace+':module_container'
            cmds.lockNode(moduleContainer, lock=False, lockUnpublished=False)
            dgNodes = cmds.container(moduleContainer, query=True, nodeList=True)
            for node in dgNodes:
                if node.endswith('_curveInfo'):
                    cmds.delete(node)
            # Delete the proxy geometry for the module if it exists.
            try:
                proxyGeoGrp = namespace+':proxyGeometryGrp'
                cmds.select(proxyGeoGrp, replace=True)
                cmds.delete()
            except:
                pass
            cmds.select(moduleContainer, replace=True)
            cmds.delete()
        for namespace in modulesToBeRemoved:
            cmds.namespace(removeNamespace=namespace)
        cmds.namespace(setNamespace=':')
        if cmds.namespace(exists=currentNamespace):
            cmds.namespace(setNamespace=currentNamespace)
        if not len(self.modules):
            cmds.button(self.uiVars['moduleUndoCreate_button'], edit=True, enable=False)
        mfunc.cleanSceneState()
        #mfunc.updateAllTransforms()
        self.clearParentModuleField()
        self.clearChildModuleField()
        self.resetListHeightForSceneModulesUI()

    def deleteAllSceneModules(self):
        namespacesToBeRemoved = []
        allModules = mfunc.returnMRT_Namespaces(cmds.namespaceInfo(listOnlyNamespaces=True))
        for namespace in allModules:
            self.removeChildrenModules(namespace)
        for namespace in allModules:
            moduleContainer = namespace+':module_container'
            cmds.lockNode(moduleContainer, lock=False, lockUnpublished=False)
            dgNodes = cmds.container(moduleContainer, query=True, nodeList=True)
            for node in dgNodes:
                if node.endswith('_curveInfo'):
                    cmds.delete(node)
            # Delete the proxy geometry for the module if it exists.
            try:
                proxyGeoGrp = namespace+':proxyGeometryGrp'
                cmds.select(proxyGeoGrp, replace=True)
                cmds.delete()
            except:
                pass
            cmds.select(moduleContainer, replace=True)
            cmds.delete()
            cmds.namespace(setNamespace=':')
            namespacesToBeRemoved.append(namespace)
        if namespacesToBeRemoved:
            for namespace in namespacesToBeRemoved:
                cmds.namespace(removeNamespace=namespace)
        mfunc.cleanSceneState()
        cmds.button(self.uiVars['moduleUndoCreate_button'], edit=True, enable=False)
        self.modules = {}
        self.clearParentModuleField()
        self.clearChildModuleField()

    def removeChildrenModules(self, moduleNamespace):
        childrenModules = mfunc.traverseChildrenModules(moduleNamespace)
        if childrenModules:
            for childModule in childrenModules:
                cmds.lockNode(childModule+':module_container', lock=False, lockUnpublished=False)
                #cmds.delete(childModule+':moduleParentRepresentationSegment_endLocator_pointConstraint')
                constraint = cmds.listRelatives(childModule+':moduleParentRepresentationSegment_segmentCurve_endLocator', children=True, fullPath=True, type='constraint')
                cmds.delete(constraint)
                cmds.setAttr(childModule+':moduleGrp.moduleParent', 'None', type='string')
                cmds.setAttr(childModule+':moduleParentRepresentationGrp.visibility', 0)
                cmds.lockNode(childModule+':module_container', lock=True, lockUnpublished=True)

    def toggleEditMenuButtonsOnModuleSelection(self):
        selection = mel.eval("ls -sl -type dagNode")
        if selection:
            lastSelection = selection[-1]
            namespaceInfo = mfunc.stripMRTNamespace(lastSelection)
            if namespaceInfo != None:
                cmds.button(self.uiVars['moduleSaveColl_button'], edit=True, enable=True)
                cmds.rowLayout(self.uiVars['moduleSaveCollOptions_row1'], edit=True, enable=True)
                cmds.rowLayout(self.uiVars['moduleSaveCollOptions_row2'], edit=True, enable=True)
                cmds.button(self.uiVars['moduleRename_button'], edit=True, enable=True)
                cmds.button(self.uiVars['moduleDelete_button'], edit=True, enable=True)
                cmds.button(self.uiVars['moduleDuplicate_button'], edit=True, enable=True)
                text = namespaceInfo[0].rpartition('__')[2]
                cmds.textField(self.uiVars['moduleRename_textField'], edit=True, text=text)
            else:
                cmds.button(self.uiVars['moduleSaveColl_button'], edit=True, enable=False)
                cmds.rowLayout(self.uiVars['moduleSaveCollOptions_row1'], edit=True, enable=False)
                cmds.rowLayout(self.uiVars['moduleSaveCollOptions_row2'], edit=True, enable=False)
                cmds.button(self.uiVars['moduleRename_button'], edit=True, enable=False)
                cmds.button(self.uiVars['moduleDelete_button'], edit=True, enable=False)
                cmds.button(self.uiVars['moduleDuplicate_button'], edit=True, enable=False)
                cmds.textField(self.uiVars['moduleRename_textField'], edit=True, text=None)
        else:
            cmds.button(self.uiVars['moduleSaveColl_button'], edit=True, enable=False)
            cmds.rowLayout(self.uiVars['moduleSaveCollOptions_row1'], edit=True, enable=False)
            cmds.rowLayout(self.uiVars['moduleSaveCollOptions_row2'], edit=True, enable=False)
            cmds.button(self.uiVars['moduleRename_button'], edit=True, enable=False)
            cmds.button(self.uiVars['moduleDelete_button'], edit=True, enable=False)
            cmds.button(self.uiVars['moduleDuplicate_button'], edit=True, enable=False)
            cmds.textField(self.uiVars['moduleRename_textField'], edit=True, text=None)

    def insertChildModuleIntoField(self, *args):
        selection = cmds.ls(selection=True)
        if selection:
            lastSelection = selection[-1]
            namespaceInfo = mfunc.stripMRTNamespace(lastSelection)
            if namespaceInfo != None:
                cmds.textField(self.uiVars['selectedChildModule_textField'], edit=True, text=namespaceInfo[0], font='plainLabelFont')
                parentInfo = cmds.getAttr(namespaceInfo[0]+':moduleGrp.moduleParent')
                if parentInfo != 'None':
                    parentInfo = parentInfo.split(',')[0]
                    cmds.button(self.uiVars['moduleUnparent_button'], edit=True, enable=True)
                    cmds.button(self.uiVars['childSnap_button'], edit=True, enable=True)
                    if not 'MRT_SplineNode' in parentInfo:
                        cmds.button(self.uiVars['parentSnap_button'], edit=True, enable=True)
                else:
                    cmds.button(self.uiVars['moduleUnparent_button'], edit=True, enable=False)
                    cmds.button(self.uiVars['parentSnap_button'], edit=True, enable=False)
                    cmds.button(self.uiVars['childSnap_button'], edit=True, enable=False)
            else:
                cmds.textField(self.uiVars['selectedChildModule_textField'], edit=True, text='< insert child module >', font='obliqueLabelFont')
                cmds.button(self.uiVars['moduleUnparent_button'], edit=True, enable=False)
                cmds.button(self.uiVars['parentSnap_button'], edit=True, enable=False)
                cmds.button(self.uiVars['childSnap_button'], edit=True, enable=False)
                cmds.warning('MRT Error: Please select and insert a module as child.')
        else:
            cmds.textField(self.uiVars['selectedChildModule_textField'], edit=True, text='< insert child module >', font='obliqueLabelFont')
            cmds.button(self.uiVars['moduleUnparent_button'], edit=True, enable=False)
            cmds.button(self.uiVars['parentSnap_button'], edit=True, enable=False)
            cmds.button(self.uiVars['childSnap_button'], edit=True, enable=False)
            cmds.warning('MRT Error: Please select and insert a module as child.')

    def insertParentModuleNodeIntoField(self, *args):
        selection = cmds.ls(selection=True)
        if selection:
            lastSelection = selection[-1]
            namespaceInfo = mfunc.stripMRTNamespace(lastSelection)
            if namespaceInfo != None:
                moduleType = namespaceInfo[0].partition('__')[0]
                if moduleType == 'MRT_JointNode':
                    if cmds.nodeType(lastSelection) == 'joint':
                        cmds.textField(self.uiVars['selectedParent_textField'], edit=True, text=lastSelection, font='plainLabelFont')
                        cmds.button(self.uiVars['moduleParent_button'], edit=True, enable=True)
                    else:
                        cmds.warning('MRT Error: Please select and insert a module node as parent.')
                if moduleType == 'MRT_SplineNode':
                    if cmds.nodeType(lastSelection) == 'joint':
                        cmds.textField(self.uiVars['selectedParent_textField'], edit=True, text=lastSelection, font='plainLabelFont')
                        cmds.button(self.uiVars['moduleParent_button'], edit=True, enable=True)
                    #elif lastSelection.endswith('localAxesInfoRepresentation'):
                        #text = lastSelection.rpartition('_localAxesInfoRepresentation')[0]
                        #cmds.textField(self.uiVars['selectedParent_textField'], edit=True, text=text, font='plainLabelFont')
                        #cmds.button(self.uiVars['moduleParent_button'], edit=True, enable=True)
                    else:
                        cmds.warning('MRT Error: Please select and insert a module node as parent.')
                if moduleType == 'MRT_HingeNode':
                    if lastSelection.endswith('_control'):
                        cmds.textField(self.uiVars['selectedParent_textField'], edit=True, text=lastSelection, font='plainLabelFont')
                        cmds.button(self.uiVars['moduleParent_button'], edit=True, enable=True)
                    else:
                        cmds.warning('MRT Error: Please select and insert a module node as parent.')
            else:
                cmds.textField(self.uiVars['selectedParent_textField'], edit=True, text='< insert parent module node >', font='obliqueLabelFont')
                cmds.button(self.uiVars['moduleParent_button'], edit=True, enable=False)
                cmds.warning('MRT Error: Please select and insert a module node as parent.')
        else:
            cmds.textField(self.uiVars['selectedParent_textField'], edit=True, text='< insert parent module node >', font='obliqueLabelFont')
            cmds.button(self.uiVars['moduleParent_button'], edit=True, enable=False)
            cmds.warning('MRT Error: Please select and insert a module node as parent.')

    def clearParentModuleField(self, *args):
        cmds.textField(self.uiVars['selectedParent_textField'], edit=True, text='< insert parent module node >', font='obliqueLabelFont')
        cmds.button(self.uiVars['moduleParent_button'], edit=True, enable=False)

    def clearChildModuleField(self, *args):
        cmds.textField(self.uiVars['selectedChildModule_textField'], edit=True, text='< insert child module >', font='obliqueLabelFont')
        cmds.button(self.uiVars['moduleUnparent_button'], edit=True, enable=False)
        cmds.button(self.uiVars['parentSnap_button'], edit=True, enable=False)
        cmds.button(self.uiVars['childSnap_button'], edit=True, enable=False)

    def performUnparentForModule(self, *args):
        fieldInfo = cmds.textField(self.uiVars['selectedChildModule_textField'], query=True, text=True)
        currentNamespace = cmds.namespaceInfo(currentNamespace=True)
        cmds.namespace(setNamespace=':')
        moduleNamespaces = mfunc.returnMRT_Namespaces(cmds.namespaceInfo(listOnlyNamespaces=True))
        cmds.namespace(setNamespace=currentNamespace)
        if moduleNamespaces == None:
            cmds.warning('MRT Error: Module parenting conflict. No modules in the scene.')
            self.clearChildModuleField()
            return
        else:
            if not fieldInfo in moduleNamespaces:
                cmds.warning('MRT Error: Module parenting conflict. The child module doesn\'t exist.')
                self.clearChildModuleField()
                return
        cmds.lockNode(fieldInfo+':module_container', lock=False, lockUnpublished=False)
        constraint = cmds.listRelatives(fieldInfo+':moduleParentRepresentationSegment_segmentCurve_endLocator', children=True, fullPath=True, type='constraint')
        #cmds.delete(fieldInfo+':moduleParentRepresentationSegment_endLocator_pointConstraint')
        cmds.delete(constraint)
        cmds.setAttr(fieldInfo+':moduleGrp.moduleParent', 'None', type='string')
        cmds.setAttr(fieldInfo+':moduleParentRepresentationGrp.visibility', 0)
        cmds.setAttr(fieldInfo+':moduleParentRepresentationSegment_hierarchy_representationShape.overrideColor', 2)
        cmds.lockNode(fieldInfo+':module_container', lock=True, lockUnpublished=True)
        cmds.button(self.uiVars['moduleUnparent_button'], edit=True, enable=False)
        cmds.button(self.uiVars['parentSnap_button'], edit=True, enable=False)
        cmds.button(self.uiVars['childSnap_button'], edit=True, enable=False)
        self.updateListForSceneModulesInUI()

    def performParentForModule(self, *args):
        parentFieldInfo = cmds.textField(self.uiVars['selectedParent_textField'], query=True, text=True)
        if 'MRT_HingeNode' in parentFieldInfo:
            parentFieldInfo = parentFieldInfo.rpartition('_control')[0]
        parentModuleNamespace = mfunc.stripMRTNamespace(parentFieldInfo)[0]
        childFieldInfo = cmds.textField(self.uiVars['selectedChildModule_textField'], query=True, text=True)
        if childFieldInfo == '< insert child module >':
            cmds.warning('MRT Error: Module parenting conflict. Insert a child module for parenting.')
            return
        currentNamespace = cmds.namespaceInfo(currentNamespace=True)
        cmds.namespace(setNamespace=':')
        moduleNamespaces = mfunc.returnMRT_Namespaces(cmds.namespaceInfo(listOnlyNamespaces=True))
        cmds.namespace(setNamespace=currentNamespace)
        if moduleNamespaces == None:
            cmds.warning('MRT Error: Module parenting conflict. No modules in the scene.')
            self.clearChildModuleField()
            return
        else:
            if not childFieldInfo in moduleNamespaces:
                cmds.warning('MRT Error: Module parenting conflict. The child module doesn\'t exist.')
                self.clearChildModuleField()
                return
            if not parentModuleNamespace in moduleNamespaces:
                cmds.warning('MRT Error: Module parenting conflict. The parent module doesn\'t exist.')
                self.clearParentModuleField()
                return
        parentModule_moduleParentInfo = cmds.getAttr(parentModuleNamespace+':moduleGrp.moduleParent')
        if parentModule_moduleParentInfo != 'None':
            parentModule_moduleParentInfo = parentModule_moduleParentInfo.split(',')[0]
            parentModule_moduleParentInfo = mfunc.stripMRTNamespace(parentModule_moduleParentInfo)[0]
        if mfunc.stripMRTNamespace(parentFieldInfo)[0] == childFieldInfo:
            cmds.warning('MRT Error: Module parenting conflict. Cannot parent a module on itself.')
            return
        if parentModule_moduleParentInfo == childFieldInfo:
            cmds.warning('MRT Error: Module parenting conflict. The module to be parented is already a child.')
            return
        if cmds.attributeQuery('mirrorModuleNamespace', node=childFieldInfo+':moduleGrp', exists=True):
            if parentModuleNamespace == cmds.getAttr(childFieldInfo+':moduleGrp.mirrorModuleNamespace'):
                cmds.warning('MRT Error: Module parenting conflict. Cannot set up parenting inside mirror modules.')
                return
        if cmds.getAttr(childFieldInfo+':moduleGrp.moduleParent') != 'None':
            self.performUnparentForModule([])
        cmds.lockNode(childFieldInfo+':module_container', lock=False, lockUnpublished=False)
        mfunc.updateContainerNodes(childFieldInfo+':module_container')
        mfunc.updateContainerNodes(parentModuleNamespace+':module_container')
        pointConstraint = cmds.pointConstraint(parentFieldInfo, childFieldInfo+':moduleParentRepresentationSegment_segmentCurve_endLocator', maintainOffset=False, name=childFieldInfo+':moduleParentRepresentationSegment_endLocator_pointConstraint')[0]
        mfunc.addNodesToContainer(childFieldInfo+':module_container', [pointConstraint])
        parentType = cmds.radioCollection(self.uiVars['moduleParent_radioColl'], query=True, select=True)
        if parentType == 'Hierarchical':
            cmds.setAttr(childFieldInfo+':moduleParentRepresentationSegment_hierarchy_representationShape.overrideColor', 16)
        parentInfo = parentFieldInfo + ',' + parentType
        cmds.setAttr(childFieldInfo+':moduleGrp.moduleParent', parentInfo, type='string')
        cmds.setAttr(childFieldInfo+':moduleParentRepresentationGrp.visibility', 1)
        cmds.lockNode(childFieldInfo+':module_container', lock=True, lockUnpublished=True)
        cmds.button(self.uiVars['moduleUnparent_button'], edit=True, enable=True)
        cmds.button(self.uiVars['childSnap_button'], edit=True, enable=True)
        if not 'MRT_SplineNode' in parentFieldInfo:
            cmds.button(self.uiVars['parentSnap_button'], edit=True, enable=True)

    def performSnapParentToChild(self, *args):
        childFieldInfo = cmds.textField(self.uiVars['selectedChildModule_textField'], query=True, text=True)
        childRootNode = childFieldInfo+':root_node_transform'
        parentModuleNode = cmds.getAttr(childFieldInfo+':moduleGrp.moduleParent')
        parentModuleNode = parentModuleNode.split(',')[0]
        if 'MRT_HingeNode' in parentModuleNode:
            parentModuleNode = parentModuleNode + '_control'
        cmds.xform(parentModuleNode, worldSpace=True, absolute=True, translation=cmds.xform(childRootNode, query=True, worldSpace=True, translation=True))

    def performSnapChildToParent(self, *args):
        childFieldInfo = cmds.textField(self.uiVars['selectedChildModule_textField'], query=True, text=True)
        if 'MRT_HingeNode' in childFieldInfo:
            childRootNode = childFieldInfo+':root_node_transform_control'
        elif 'MRT_SplineNode' in childFieldInfo:
            childRootNode = childFieldInfo+ ':spline_1_adjustCurve_transform'
        else:
            childRootNode = childFieldInfo+':root_node_transform'
        parentModuleNode = cmds.getAttr(childFieldInfo+':moduleGrp.moduleParent')
        parentModuleNode = parentModuleNode.split(',')[0]
        cmds.xform(childRootNode, worldSpace=True, absolute=True, translation=cmds.xform(parentModuleNode, query=True, worldSpace=True, translation=True))

    def processCharacterFromScene(self, *args):
        characterStatus = self.checkMRTcharacter()
        currentNamespace = cmds.namespaceInfo(currentNamespace=True)
        cmds.namespace(setNamespace=':')
        if characterStatus[0]:
            characterName = re.findall('^MRT_character(\D+)__mainGrp$', characterStatus[0])
            cmds.warning('MRT Error: Character "%s" exists in the scene, aborting.'%(characterName[0]))
            return
        scene_modules = mfunc.returnMRT_Namespaces(cmds.namespaceInfo(listOnlyNamespaces=True))
        if not scene_modules:
            cmds.warning('MRT Error: No modules found in the scene to create a character.')
            return
        # Sort modules by their mirror namespaces(Mirrored namespaces are appended at the end).
        mrt_modules = []
        for module in scene_modules[:]:
            if cmds.getAttr(module+':moduleGrp.onPlane')[0] != '-':
                mrt_modules.append(module)
                index = scene_modules.index(module)
                scene_modules.pop(index)
        mrt_modules.extend(scene_modules)

        characterName = cmds.textField(self.uiVars['characterName_textField'], query=True, text=True)
        if not str(characterName).isalnum():
            cmds.warning('MRT Error: Please enter a valid name for creating a character.')
            return
        characterName = characterName.title()
        mainGrp = cmds.group(empty=True, name='MRT_character'+characterName+'__mainGrp')
        cmds.addAttr(mainGrp, dataType='string', longName='collectionFileID')
        #cmds.addAttr(mainGrp, dataType='string', longName='translationControlFuncList')
        cmds.addAttr(mainGrp, dataType='string', longName='skinJointList')
        jointsGrp = cmds.group(empty=True, name='MRT_character'+characterName+'__jointsMainGrp', parent=mainGrp)
        geoMainGrp = cmds.group(empty=True, name='MRT_character'+characterName+'__geometryMainGrp', parent=mainGrp)
        skinGeoGrp = cmds.group(empty=True, name='MRT_character'+characterName+'__skinGeometryGrp', parent=geoMainGrp)
        cntlGrp = cmds.group(empty=True, name='MRT_character'+characterName+'__controlGrp', parent=mainGrp)
        miscGrp = cmds.group(empty=True, name='MRT_character'+characterName+'__MiscGrp', parent=mainGrp)
        defGrp = cmds.group(empty=True, name='MRT_character'+characterName+'__DeformersGrp', parent=miscGrp)
        cmds.setAttr(defGrp+'.visibility', 0)
        proxyMainGrp = cmds.group(empty=True, name='MRT_character'+characterName+'__proxyAllGeometryGrp', parent=geoMainGrp)
        skinGeoLayerName = cmds.createDisplayLayer(empty=True, name='MRT_character'+characterName+'_skin_geometry', noRecurse=False)
        skinJointsLayerName = cmds.createDisplayLayer(empty=True, name='MRT_character'+characterName+'_all_joints', noRecurse=True)
        controlRigLayerName = cmds.createDisplayLayer(empty=True, name='MRT_character'+characterName+'_control_rig', noRecurse=False)
        cmds.select(clear=True)
        characterJointSet = []

        fileId = reduce(lambda x,y:x+y, (random.random(), random.random(), random.random()))
        fileId = str(fileId).partition('.')[2]
        cmds.setAttr(mainGrp+'.collectionFileID', fileId, type='string', lock=True)
        autoCharacterFile = self.autoCollections_path + '/character__%s.mrtmc'%(fileId)
        self.makeCollectionFromSceneTreeViewModulesUI(args=True, allModules=True, auto=autoCharacterFile)
        #translationFunctionSet = []
        for module in mrt_modules:
            moduleAttrsDict = mfunc.returnModuleAttrsFromScene(module)
            joints = mfunc.createSkeletonFromModule(moduleAttrsDict, characterName)
            characterJointSet.append((moduleAttrsDict['moduleParentInfo'][0][1], joints[:]))

            if moduleAttrsDict['proxy_geo_options'][3] == 'On':
                proxyGrp = mfunc.createProxyForSkeletonFromModule(characterJointSet, moduleAttrsDict, characterName)
                if proxyGrp:
                    cmds.parent(proxyGrp, proxyMainGrp, absolute=True)

        self.deleteAllSceneModules()

        #worldRefJoints, all_root_joint = mfunc.setupParentingForRawCharacterParts(characterJointSet, jointsGrp, characterName)
        all_root_joints = mfunc.setupParentingForRawCharacterParts(characterJointSet, jointsGrp, characterName)

        characterJoints = cmds.ls(type='joint')
        for joint in characterJoints:
            if joint.startswith('MRT_character'):
                parent = cmds.listRelatives(joint, parent=True)
                if parent == None:
                    cmds.parent(joint, jointsGrp)

        characterJoints = [joint for joint in characterJoints if joint.endswith('_transform')]
        characterJointsAttr = ','.join(characterJoints)
        cmds.setAttr(mainGrp+'.skinJointList', characterJointsAttr, type='string', lock=True)
        #cmds.setAttr(mainGrp+'.translationControlFuncList', translationFunctionSet, type='string', lock=True)
        proxyGrpChildren = cmds.listRelatives(proxyMainGrp, allDescendents=True)
        if proxyGrpChildren == None:
            cmds.delete(proxyMainGrp)
        transforms = objects.createRawCharacterTransformControl()
        avgBound = 6.0
        sumPos = [0.0, 0.0, 0.0]
        startMagPos = 0
        for joint in characterJoints:
            worldPos = cmds.xform(joint, query=True, worldSpace=True, translation=True)
            magWorldPos = math.sqrt(reduce(lambda x,y: x+y, [cmpnt**2 for cmpnt in worldPos]))
            if magWorldPos > avgBound:
                avgBound = magWorldPos
            sumPos = map(lambda x,y:x+y, worldPos, sumPos)
        sumPos = [item/len(characterJoints) for item in sumPos]
        sumPos[1] = 0.0
        scaleAdd = [x*avgBound*320 for x in [1.0, 1.0, 1.0]]
        cmds.setAttr(transforms[1]+'.translate', *sumPos, type='double3')
        cmds.setAttr(transforms[1]+'.scale', *scaleAdd, type='double3')
        cmds.makeIdentity(transforms[1], scale=True, translate=True, apply=True)
        cmds.connectAttr(transforms[0]+'.scaleY', transforms[0]+'.scaleX')
        cmds.connectAttr(transforms[0]+'.scaleY', transforms[0]+'.scaleZ')
        cmds.aliasAttr('globalScale', transforms[0]+'.scaleY')
        cmds.setAttr(transforms[0]+'.scaleX', lock=True, keyable=False, channelBox=False)
        cmds.setAttr(transforms[0]+'.scaleZ', lock=True, keyable=False, channelBox=False)
        cmds.setAttr(transforms[1]+'.scaleX', keyable=False, lock=True)
        cmds.setAttr(transforms[1]+'.scaleY', keyable=False, lock=True)
        cmds.setAttr(transforms[1]+'.scaleZ', keyable=False, lock=True)
        cmds.parent(transforms[1], mainGrp, absolute=True)
        transforms[0] = cmds.rename(transforms[0], 'MRT_character'+characterName+transforms[0])
        transforms[1] = cmds.rename(transforms[1], 'MRT_character'+characterName+transforms[1])

        for joint in all_root_joints:
            cmds.parentConstraint(transforms[0], joint, maintainOffset=True, name=transforms[0]+'_'+joint+'__parentConstraint')

        #cmds.parentConstraint(transforms[0], 'MRT_character'+characterName+'__controlGrp', maintainOffset=True, name=transforms[0]+'_controlGrp_parentConstraint')
        cmds.connectAttr(transforms[0]+'.globalScale', 'MRT_character'+characterName+'__jointsMainGrp.scaleX')
        cmds.connectAttr(transforms[0]+'.globalScale', 'MRT_character'+characterName+'__jointsMainGrp.scaleY')
        cmds.connectAttr(transforms[0]+'.globalScale', 'MRT_character'+characterName+'__jointsMainGrp.scaleZ')
        #cmds.connectAttr(transforms[0]+'.globalScale', 'MRT_character'+characterName+'__controlGrp.scaleX')
        #cmds.connectAttr(transforms[0]+'.globalScale', 'MRT_character'+characterName+'__controlGrp.scaleY')
        #cmds.connectAttr(transforms[0]+'.globalScale', 'MRT_character'+characterName+'__controlGrp.scaleZ')
        cmds.select(clear=True)

        for joint in characterJoints:
            if re.search('_root_node_transform', joint):
                cmds.addAttr(joint, dataType='string', longName='rigLayers', keyable=False)
                cmds.setAttr(joint+'.rigLayers', 'None', type='string', lock=True)
        cmds.editDisplayLayerMembers(skinGeoLayerName, skinGeoGrp)
        cmds.editDisplayLayerMembers(skinJointsLayerName, *characterJoints)
        result = mfunc.createFKlayerDriverOnJointHierarchy(characterJoints, 'FK_bake', characterName, False, 'None', True)
        cmds.addAttr(transforms[0], attributeType='float', longName='FK_Bake_Layer', hasMinValue=True, hasMaxValue=True, minValue=0, maxValue=1, defaultValue=0, keyable=False)
        for joint in result[0]:
            for constraint in result[1]:
                constrainResult = mfunc.returnConstraintWeightIndexForTransform(joint, constraint)
                if constrainResult:
                    cmds.connectAttr(transforms[0]+'.FK_Bake_Layer', constraint+'.'+constrainResult[1])
        cmds.addAttr(transforms[0], attributeType='enum', longName='CONTROL_RIGS', enumName='---------------------------:', keyable=True)
        cmds.setAttr(transforms[0]+'.CONTROL_RIGS', lock=True)

        cmds.select([transforms[1], cntlGrp])
        mel.eval('editDisplayLayerMembers -noRecurse MRT_character'+characterName+'_control_rig `ls -selection`;')
        #cmds.editDisplayLayerMembers(layerName, cmds.ls(selection=True))    # The cmds version didn't work as desired.
        cmds.select(clear=True)
        if cmds.namespace(exists=currentNamespace):
            cmds.namespace(setNamespace=currentNamespace)
        self.clearParentModuleField()
        self.clearChildModuleField()
        cmds.select(characterJoints, replace=True)
        cmds.sets(name='MRT_character'+characterName+'__skinJointSet')
        cmds.select(clear=True)

    def revertModulesFromCharacter(self, *args):
        status = self.checkMRTcharacter()
        if not status[0]:
            cmds.warning('MRT Error: No character in the scene. Aborting.')
            return
        if status[0] and status[1] == '':
            cmds.warning('MRT Error: Cannot find the auto-collection file containing the modules for the current character. Unable to revert. Aborting')
            return
        if status[0] and status[1] != '':
            characterName = status[0].partition('MRT_character')[2].rpartition('__')[0]
            charGeoGrp = 'MRT_character'+characterName + '__geometryMainGrp'
            charSkinGeoGrp = 'MRT_character'+characterName + '__deformersGrp'
            charDefGrp = 'MRT_character'+characterName + '__skinGeometryGrp'
            charMiscGrp = 'MRT_character'+characterName + '__miscGrp'
            proxyGeoGep = 'MRT_character'+characterName + '__proxyAllGeometryGrp'
            for obj in [charDefGrp, charSkinGeoGrp, charMiscGrp, charGeoGrp, proxyGeoGep]:
                if cmds.objExists(obj):
                    allChildren = cmds.listRelatives(obj, children=True) or []
                    if allChildren:
                        for child in allChildren:
                            if not re.match('^MRT_character\w+(DeformersGrp|skinGeometryGrp|proxyAllGeometryGrp|proxyGeoGrp)$', child):
                                cmds.parent(child, world=True)
            cmds.delete(status[0])
            displayLayers = [item for item in cmds.ls(type='displayLayer') if re.match('^MRT_character[a-zA-Z0-9]*_\w+', item)]
            for layerName in displayLayers:
                if cmds.objExists(layerName):
                    cmds.delete(layerName)
            ctrl_containers = [item for item in cmds.ls(type='container') if re.match('^MRT_character[a-zA-Z0-9]*__\w+_Container$', item)]
            if ctrl_containers:
                cmds.delete(ctrl_containers)
            autoFile = self.autoCollections_path + '/' + status[1] + '.mrtmc'
            self.installSelectedModuleCollectionToScene(True, autoFile)

    def checkMRTcharacter(self):
        namespace = cmds.namespaceInfo(currentNamespace=True)
        cmds.namespace(setNamespace=':')
        transforms = cmds.ls(type='transform')
        characterGrp = []
        for transform in transforms:
            if re.match('MRT_character[a-zA-Z0-9]*__mainGrp', transform):
                characterGrp.append(transform)
        if len(characterGrp) > 1:
            cmds.warning('MRT Error: More than one character exists in the scene. Aborting.')
            return
        elif len(characterGrp) == 0:
            characterGrp = None
        elif len(characterGrp) == 1:
            characterGrp = characterGrp[0]
        characterCollectionFile = ''
        if characterGrp:
            fileId = cmds.getAttr(characterGrp+'.collectionFileID')
            characterCollectionFile = 'character__%s'%(fileId)
            characterCollectionFiles = os.listdir(self.autoCollections_path)
            characterCollectionFiles = [item for item in characterCollectionFiles if re.match('^.*mrtmc$', item)]
            if len(characterCollectionFiles):
                for item in characterCollectionFiles:
                    if item.partition('.')[0] == characterCollectionFile:
                        break
                else:
                    characterCollectionFile = ''
            else:
                characterCollectionFile = ''
        cmds.namespace(setNamespace=namespace)
        return characterGrp, characterCollectionFile

    def saveCharacterTemplate(self, *args):
        def saveCharTemplateFromDescriptionProcessInputUI(*args):
            status = self.checkMRTcharacter()
            if not status[0]:
                cmds.warning('MRT Error: No character in the scene. Aborting.')
                cmds.deleteUI('mrt_charTemplateDescription_UI_window')
                return
            templateDescription = cmds.scrollField(self.uiVars['charTemplateDescrpWindowScrollField'], query=True, text=True)
            if templateDescription == '':
                try:
                    cmds.deleteUI('mrt_charTemplate_noDescpError_UI_window')
                except:
                    pass
                self.uiVars['charTemplateDescrpErrorWindow'] = cmds.window('mrt_charTemplate_noDescpError_UI_window', title='Character template warning', maximizeButton=False, sizeable=False)
                try:
                    cmds.windowPref('mrt_charTemplate_noDescpError_UI_window', remove=True)
                except:
                    pass
                cmds.frameLayout(visible=True, borderVisible=False, collapsable=False, labelVisible=False, height=90, width=220, marginWidth=20, marginHeight=15)
                cmds.text(label='Are you sure you want to continue saving a character template with an empty description?')
                cmds.rowLayout(numberOfColumns=2, columnAttach=([1, 'left', 128], [2, 'left', 30]), rowAttach=([1, 'top', 8], [2, 'top', 8]))
                cmds.button(label='Continue', width=90, command=partial(saveCharTemplateFromDescription, templateDescription))
                ##cmds.button(label='Revert', width=90, command=('cmds.deleteUI(\"'+self.uiVars['charTemplateDescrpErrorWindow']+'\")'))
                cmds.button(label='Revert', width=90, command=partial(self.closeWindow, self.uiVars['charTemplateDescrpErrorWindow']))
                cmds.showWindow(self.uiVars['charTemplateDescrpErrorWindow'])
            else:
                saveCharTemplateFromDescription(True, templateDescription)

        def saveCharTemplateFromDescription(args, templateDescription):
            try:
                cmds.deleteUI('mrt_charTemplate_noDescpError_UI_window')
            except:
                pass
            try:
                cmds.deleteUI('mrt_charTemplateDescription_UI_window')
            except:
                pass
            status = self.checkMRTcharacter()
            if not status[0]:
                cmds.warning('MRT Error: No character in the scene. Aborting.')
                return
            ui_preferences_file = open(self.ui_preferences_path, 'rb')
            ui_preferences = cPickle.load(ui_preferences_file)
            ui_preferences_file.close()
            startDirectory = ui_preferences['directoryForSavingCharacterTemplates']
            if not os.path.exists(startDirectory):
                startDirectory = ui_preferences['defaultDirectoryForSavingCharacterTemplates']
            fileFilter = 'MRT Character Template Files (*.mrtct)'
            fileReturn = cmds.fileDialog2(caption='Save character template', fileFilter=fileFilter, startingDirectory=startDirectory, dialogStyle=2)
            if fileReturn == None:
                return
            ui_preferences['directoryForSavingCharacterTemplates'] = fileReturn[0].rpartition('/')[0]
            ui_preferences_file = open(self.ui_preferences_path, 'wb')
            cPickle.dump(ui_preferences, ui_preferences_file, cPickle.HIGHEST_PROTOCOL)
            ui_preferences_file.close()

            if os.path.exists(fileReturn[0]):
                os.remove(fileReturn[0])

            mrtct_fObject = {}
            mrtct_fObject['templateDescription'] = templateDescription

            templateObjects = [status[0]]
            characterName = status[0].partition('MRT_character')[2].rpartition('__')[0]
            layerName = 'MRT_character'+characterName+'_proxy_geometry'
            if cmds.objExists(layerName):
                templateObjects.append(layerName)
            skinJointSet = 'MRT_character'+characterName+'__skinJointSet'
            templateObjects.append(skinJointSet)

            selection = cmds.ls(selection=True)
            cmds.select(templateObjects, replace=True, noExpand=True)
            tempFilePath = fileReturn[0].rpartition('.mrtct')[0]+'_temp.ma'
            cmds.file(tempFilePath, force=True, options='v=1', type='mayaAscii', exportSelected=True, pr=True)

            tempFile_fObject = open(tempFilePath)
            i = 1
            for line in tempFile_fObject:
                mrtct_fObject['templateData_line_'+str(i)] = line
                i +=1
            tempFile_fObject.close()
            os.remove(tempFilePath)
            mrtct_fObject_file = open(fileReturn[0], 'wb')
            cPickle.dump(mrtct_fObject, mrtct_fObject_file, cPickle.HIGHEST_PROTOCOL)
            mrtct_fObject_file.close()
            del mrtct_fObject

            ui_preferences_file = open(self.ui_preferences_path, 'rb')
            ui_preferences = cPickle.load(ui_preferences_file)
            ui_preferences_file.close()
            if ui_preferences['loadNewCharTemplatesToCurrentList']:
                self.loadCharTemplatesForUI(fileReturn)

            cmds.namespace(setNamespace=namespace)
            if not selection:
                cmds.select(clear=True)
            else:
                cmds.select(selection)
        namespace = cmds.namespaceInfo(currentNamespace=True)
        cmds.namespace(setNamespace=':')
        status = self.checkMRTcharacter()
        if not status[0]:
            cmds.warning('MRT Error: No character in the scene. Aborting.')
            return

        allAttrs = cmds.listAttr(status[0].partition('mainGrp')[0]+'root_transform', visible=True, keyable=True)
        controlAttrs = set.symmetric_difference(set(['translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ', 'globalScale', 'CONTROL_RIGS']), set(allAttrs))
        if len(controlAttrs):
            cmds.warning('MRT Error: One or more control rigs are currently applied to the character. Detach them before saving a character template.')
            return
        try:
            cmds.deleteUI('mrt_charTemplateDescription_UI_window')
        except:
            pass
        self.uiVars['charTemplateDescrpWindow'] = cmds.window('mrt_charTemplateDescription_UI_window', title='Character template description', height=150, maximizeButton=False, sizeable=False)
        try:
            cmds.windowPref('mrt_charTemplateDescription_UI_window', remove=True)
        except:
            pass
        self.uiVars['charTemplateDescrpWindowColumn'] = cmds.columnLayout(adjustableColumn=True)
        cmds.text(label='')
        cmds.text('Enter description for character template', align='center', font='boldLabelFont')
        cmds.frameLayout(visible=True, borderVisible=False, collapsable=False, labelVisible=False, height=75, width=300, marginWidth=5, marginHeight=10)
        self.uiVars['charTemplateDescrpWindowScrollField'] = cmds.scrollField(preventOverride=True, wordWrap=True)
        cmds.setParent(self.uiVars['charTemplateDescrpWindowColumn'])
        cmds.rowLayout(numberOfColumns=2, columnAttach=([1, 'left', 28], [2, 'left', 20]))
        cmds.button(label='Save template', width=130, command=saveCharTemplateFromDescriptionProcessInputUI)
        ##cmds.button(label='Cancel', width=90, command=('cmds.deleteUI(\"'+self.uiVars['charTemplateDescrpWindow']+'\")'))
        cmds.button(label='Cancel', width=90, command=partial(self.closeWindow, self.uiVars['charTemplateDescrpWindow']))
        cmds.setParent(self.uiVars['charTemplateDescrpWindowColumn'])
        cmds.text(label='')
        cmds.showWindow(self.uiVars['charTemplateDescrpWindow'])

    def displayControlRiggingOptionsAllWindow(self, *args):
        '''
        control_types = []
        for attribute in dir(mrt_controlRig):
        try:
        # If the control type class is derived from ControlRig class, collect it.
        if eval('mrt_controlRig.%s.__bases__'%attribute)[0] == mrt_controlRig.BaseJointControl:
        control_types.append(attribute)
        except Exception:
        pass
        '''
        control_types = [cls for cls in getattr(mrt_controlRig, 'BaseJointControl').__subclasses__()]

        if control_types:
            scrollTextString = '\n\t\t\t\t  < Available control rigging options for character hierarchy types >'.upper()
            for cls in control_types:
                klassName = cls.__name__
                klassName = mfunc.findLastSubClassForSuperClass(klassName, 'mrt_controlRig')
                klass_p_name = klassName[0].upper()
                for char in klassName[1:]:
                    if char.isupper():
                        klass_p_name += ' ' + char
                    else:
                        klass_p_name += char
                scrollTextString += '\n\n\n' + klass_p_name

                scrollTextString += '\n' + '-' * len(klass_p_name) + '\n'

                cls_string = cls.__doc__

                c_docString = ''

                if cls_string:

                    cls_string_list = str.split(' '.join(cls_string.split('\n')))

                    docline_temp = ''

                    for item in cls_string_list:
                        c_docString += item + ' '
                        docline_temp += item + ' '
                        if len(docline_temp) > 98:
                            docline_temp = ''
                            c_docString += '\n'

                scrollTextString += c_docString + '\n\n| Control rigging options |\n'

                funcList = [item.partition('apply')[2].replace('_', ' ') for item in dir(cls) if re.match('^apply[A-Z]\D+$', item)]
                i = 1
                for func in funcList:
                    scrollTextString += '\n%s. '%i
                    scrollTextString += func
                    i += 1

            try:
                cmds.deleteUI('mrt_displayCtrlRigOptions_UI_window')
            except:
                pass
            self.uiVars['displayCtrlRigOptionsWindow'] = cmds.window('mrt_displayCtrlRigOptions_UI_window', title='Control rigging options for character hierarchies', maximizeButton=False, sizeable=False)
            try:
                cmds.windowPref(self.uiVars['displayCtrlRigOptionsWindow'], remove=True)
            except:
                pass
            self.uiVars['displayCtrlRigOptions_columnLayout'] = cmds.columnLayout()
            self.uiVars['displayCtrlRigOptions_scrollField'] = cmds.scrollField(text=scrollTextString, editable=False, width=760, enableBackground=True, height=300, wordWrap=False)
            cmds.showWindow(self.uiVars['displayCtrlRigOptionsWindow'])

    def displayControlRiggingOptions(self, rootJoint, customHierarchyTreeListString=None):
        self.controlRiggingOptionsList = {}
        cmds.textScrollList(self.uiVars['c_rig_txScList'], edit=True, height=32, removeAll=True)
        if rootJoint:
            mp_klasses = []
            if customHierarchyTreeListString:
                customClasses = [klass.__name__ for klass in getattr(mrt_controlRig, 'BaseJointControl').__subclasses__() if eval('mrt_controlRig.%s.customHierarchy'%klass.__name__) != None]
                customClasses.sort()
                for klass in customClasses:
                    klass = mfunc.findLastSubClassForSuperClass(klass, 'mrt_controlRig')
                    h_string = eval('mrt_controlRig.%s.customHierarchy'%klass)
                    if h_string == customHierarchyTreeListString:
                        mp_klasses.append(klass)
                if len(mp_klasses):
                    mp_klasses.sort()
                    className = mp_klasses[0]
                    if len(mp_klasses) > 1:
                        print '## MRT message: Multiple user control rigging classes (%s) found for selected custom joint hierarchy. ##\n## Using \"%s\" control class for rigging options. ##'%(', '.join(mp_klasses), (className))
                    else:
                        print '## MRT message: Using \"%s\" control class for rigging custom hierarchy. ##'%(className)
                else:
                    className = 'JointControl'
                    print '## MRT message: No custom control rigging class found for selected custom hierarchy. Using JointControl class. ##'
            else:
                moduleType = cmds.getAttr(rootJoint+'.inheritedNodeType')
                numNodes = cmds.getAttr(rootJoint+'.numNodes')
                if moduleType != 'JointNode':
                    className = '%sControl'%(moduleType.partition('Node')[0])
                if moduleType == 'JointNode' and numNodes < 4:
                    className = 'JointControl'
                if moduleType == 'JointNode' and numNodes > 3:
                    className = 'JointChainControl'
                subClasses = [klass.__name__ for klass in eval('mrt_controlRig.%s'%(className)).__subclasses__()]

                if subClasses:
                    for klass in subClasses:
                        klass = mfunc.findLastSubClassForSuperClass(klass, 'mrt_controlRig')
                        mp_klasses.append(klass)
                        #subs = [sklass.__name__ for sklass in getattr(mrt_controlRig, klass).__subclasses__()]
                        #if not len(subs):
                            #mp_klasses.append(klass)
                    if len(mp_klasses):
                        mp_klasses.sort()
                        className = mp_klasses[0]
                        if len(mp_klasses) > 1:
                            print '## MRT message: Multiple user control rigging classes (%s) found for selected joint hierarchy. ##\n## Using \"%s\" control class for rigging options. ##'%(', '.join(mp_klasses), (className))
                        else:
                            print '## MRT message: Custom user control rigging class found for selected joint hierarchy. ##\n## Using \"%s\" control class for rigging options. ##'%(className)
            self.controlRiggingOptionsList['__klass__'] = '%s'%(className)
            funcList = eval('[item for item in dir(mrt_controlRig.%s) if not re.search(\'__\', item)]'%(className))
            funcNameList = eval('[item.partition(\'apply\')[2].replace(\'_\', \' \') for item in dir(mrt_controlRig.%s) if re.search(\'^apply[A-Z]\', item)]'%(className))
            for (funcName, func) in zip(funcNameList, funcList):
                self.controlRiggingOptionsList[funcName] = func

        if self.controlRiggingOptionsList:
            self.controlRiggingOptionsList['__rootJoint__'] = rootJoint
            appendFuncList = [item for item in self.controlRiggingOptionsList if item.find('__') == -1]
            atRigList = cmds.getAttr(rootJoint+'.rigLayers')
            if atRigList != 'None':
                atRigList = atRigList.split(',')
                atRigList = [item.replace('_', ' ') for item in atRigList]
                appendFuncList = [item for item in appendFuncList if not item in atRigList]
            if appendFuncList:
                scrollHeight = len(appendFuncList) * 20
                if scrollHeight > 100:
                    scrollHeight = 100
                if scrollHeight == 20:
                    scrollHeight = 40
                for funcName in sorted(appendFuncList):
                    cmds.textScrollList(self.uiVars['c_rig_txScList'], edit=True, enable=True, 
                    											 height=scrollHeight, append=funcName, font='plainLabelFont')
                cmds.textScrollList(self.uiVars['c_rig_txScList'], edit=True, selectIndexedItem=1)
                cmds.button(self.uiVars['c_rig_attachRigButton'], edit=True, enable=True)
            else:
                cmds.textScrollList(self.uiVars['c_rig_txScList'], edit=True, enable=True, height=32, 
                						 append=['         < No unattached rig(s) found for selected character hierarchy >'], 
                																					 font='obliqueLabelFont')
                cmds.button(self.uiVars['c_rig_attachRigButton'], edit=True, enable=False)
        else:
            cmds.textScrollList(self.uiVars['c_rig_txScList'], edit=True, enable=False, height=32, 
            			  						append=['        < select a character hierarchy to attach control rig(s) >'], 
            			  																				font='boldLabelFont')
            cmds.button(self.uiVars['c_rig_attachRigButton'], edit=True, enable=False)


    def attachSelectedControlRigToHierarchy(self, *args):
        selection = cmds.ls(selection=True)[-1]
        if cmds.ls(selection, referencedNodes=True):
            cmds.warning('MRT Error: Referenced object selected. Aborting.')
            return
        selectFunc = cmds.textScrollList(self.uiVars['c_rig_txScList'], query=True, selectItem=True)[-1]
        hierarchyRoot = self.controlRiggingOptionsList['__rootJoint__']
        rigLayers = cmds.getAttr(hierarchyRoot+'.rigLayers')
        if rigLayers != 'None':
            rigLayers = rigLayers.split(',')
            for layer in rigLayers:
                if selectFunc == layer:
                    cmds.warning('MRT Error: The control rig is already attached. Skipping.')
                    return
        controlClass = self.controlRiggingOptionsList['__klass__']
        characterName = selection.partition('__')[0].partition('MRT_character')[2]
        controlRigInst = eval('mrt_controlRig.%s(characterName, hierarchyRoot)'%controlClass)
        controlRigApplyFunc = self.controlRiggingOptionsList[selectFunc]
        eval('controlRigInst.%s()'%controlRigApplyFunc)
        del controlRigInst
        if isinstance(rigLayers, list):
            rigLayers.append(controlRigApplyFunc.split('apply')[1])
            rigLayers = ','.join(rigLayers)
            cmds.setAttr(hierarchyRoot+'.rigLayers', lock=False)
            cmds.setAttr(hierarchyRoot+'.rigLayers', rigLayers, type='string', lock=True)
        else:
            cmds.setAttr(hierarchyRoot+'.rigLayers', lock=False)
            cmds.setAttr(hierarchyRoot+'.rigLayers', controlRigApplyFunc.split('apply')[1], type='string', lock=True)
        self.displayAttachedControlRigs(hierarchyRoot)
        cmds.select(selection)


    def removeSelectedControlRigFromHierarchy(self, *args):
        cy_check = cmds.cycleCheck(query=True, evaluation=True)
        if cy_check:
            cmds.cycleCheck(evaluation=False)
        selection = cmds.ls(selection=True)[-1]
        if cmds.ls(selection, referencedNodes=True):
            cmds.warning('MRT Error: Referenced object selected. Aborting.')
            return
        ctrlRigLayerName = cmds.textScrollList(self.uiVars['c_rig_attachedRigs_txScList'], query=True, 
        																								selectItem=True)[-1]
        ctrlRigLayer = self.controlRiggingOptionsList[ctrlRigLayerName].partition('apply')[2]
        hierarchyRoot = self.controlRiggingOptionsList['__rootJoint__']
        characterName = hierarchyRoot.partition('__')[0].partition('MRT_character')[2]
        userSpecName = re.split('_root_node_transform', hierarchyRoot)[0].partition('__')[2]
        # Change the rig layer attribute on root joint for the character hierarchy
        rigLayers = cmds.getAttr(hierarchyRoot+'.rigLayers')
        rigLayers = rigLayers.split(',')
        index = rigLayers.index(ctrlRigLayer)
        rigLayers.pop(index)
        if len(rigLayers):
            cmds.setAttr(hierarchyRoot+'.rigLayers', lock=False)
            cmds.setAttr(hierarchyRoot+'.rigLayers', ','.join(rigLayers), type='string', lock=True)
        else:
            cmds.setAttr(hierarchyRoot+'.rigLayers', lock=False)
            cmds.setAttr(hierarchyRoot+'.rigLayers', 'None', type='string', lock=True)
        cmds.currentTime(0)
        # Reset all controls.
        nodes = []
        cmds.currentTime(0)
        rootCtrls = [item for item in cmds.ls(type='transform') 
        			 if re.match('^MRT_character%s__(world|root){1}_transform$' % (characterName), item)]
        if rootCtrls:
            nodes.extend(rootCtrls)
        ctrl_containers = [item for item in cmds.ls(type='container') 
        				   if re.match('^MRT_character%s__\w+_Container$'%(characterName), item)]
        if ctrl_containers:
            nodes.extend(ctrl_containers)
        if nodes:
            for node in nodes:
                mel.eval('cutKey -t ":" '+node+';')
                ctrlAttrs = cmds.listAttr(node, keyable=True, visible=True, unlocked=True)
                if ctrlAttrs:
                    for attr in ctrlAttrs:
                        if re.search('(translate|rotate){1}', attr):
                            cmds.setAttr(node+'.'+attr, 0)
                        if re.search('scale', attr):
                            cmds.setAttr(node+'.'+attr, 1)
        allJoints = cmds.getAttr('MRT_character'+characterName+'__mainGrp.skinJointList')
        allJoints = allJoints.split(',')

        # Force update on character joint attributes.
        for joint in allJoints:
            cmds.getAttr(joint+'.translate')
            cmds.getAttr(joint+'.rotate')
            cmds.getAttr(joint+'.scale')

        # Remove the control rig container
        ctrl_container = 'MRT_character{0}__{1}_{2}_Container'.format(characterName, userSpecName, ctrlRigLayer)

        allControlRigHandles = [item for item in cmds.ls(type='transform') 
        						if re.match('^MRT_character%s__%s_%s\w+handle$' % (characterName, userSpecName, ctrlRigLayer), item)]

        for handle in allControlRigHandles:
            childTargetHandles = set([item.rpartition('_parentSwitch_grp_parentConstraint')[0] 
            		  				  for item in cmds.listConnections(handle, destination=True) 
            		  				  if re.match('^MRT_character%s__\w+handle_parentSwitch_grp_parentConstraint$' % (characterName), item)])
            if childTargetHandles:
                for child in childTargetHandles:
                    parentSwitchCondition = child+'_'+handle+'_parentSwitch_condition'
                    cmds.delete(parentSwitchCondition)
                    attrs = cmds.addAttr(child+'.targetParents', query=True, enumName=True)
                    attrs = attrs.split(':')
                    index = attrs.index(handle)
                    attrs.pop(index)
                    cmds.addAttr(child+'.targetParents', edit=True, enumName=':'.join(attrs))
                    if cmds.objectType(child, isType='joint'):
                        cmds.orientConstraint(handle, child+'_parentSwitch_grp', edit=True, remove=True)
                    else:
                        cmds.parentConstraint(handle, child+'_parentSwitch_grp', edit=True, remove=True)
                    currentTargets = cmds.getAttr(child+'_parentSwitch_grp.parentTargetList')
                    currentTargets = currentTargets.split(',')
                    index = currentTargets.index(handle)
                    currentTargets.pop(index)
                    if isinstance(currentTargets, list):
                        currentTargets = ','.join(currentTargets)
                    cmds.setAttr(child+'_parentSwitch_grp.parentTargetList', lock=False)
                    cmds.setAttr(child+'_parentSwitch_grp.parentTargetList', currentTargets, type='string', lock=True)

                    allAttrs = cmds.addAttr(child+'.targetParents', query=True, enumName=True)
                    allAttrs = allAttrs.split(':')
                    for attr in allAttrs[1:]:
                        index = allAttrs.index(attr)
                        parentSwitchCondition = child+'_'+attr+'_parentSwitch_condition'
                        cmds.setAttr(parentSwitchCondition+'.firstTerm', index)
                    if len(allAttrs) > 0:
                        cmds.setAttr(child+'.targetParents', 1)
                    else:
                        cmds.setAttr(child+'.targetParents', 0)

        allParentSwitchConditions = [item for item in cmds.ls(type='condition') if \
        							 re.match('^MRT_character%s__%s_%s_\w+_parentSwitch_condition$' 
        							 		  % (characterName, userSpecName, ctrlRigLayer), item)]
        if allParentSwitchConditions:
            cmds.delete(allParentSwitchConditions)

        if cmds.objExists(ctrl_container):
            cmds.delete(ctrl_container)
        else:
            cmds.warning('MRT Error: No container found for the control rig to be removed. Please check the source ' \
            			 'definition for the control rig.')

        # Remove the rig layer attribute from world transform
        attrName = '{0}_{1}'.format(userSpecName, ctrlRigLayer)
        check = False
        if cmds.attributeQuery(attrName, node='MRT_character'+characterName+'__root_transform', exists=True):
            cmds.deleteAttr('MRT_character'+characterName+'__root_transform', attribute=attrName)
            check = True
        if cmds.attributeQuery(attrName+'_visibility', node='MRT_character'+characterName+'__root_transform', exists=True):
            cmds.deleteAttr('MRT_character'+characterName+'__root_transform', attribute=attrName+'_visibility')
            check = True
        if not check:
            cmds.warning('MRT Error: No attribute found on the character root transform for the control rig to be removed. ' \
            			 'Please check the source definition for the control rig.')
        cmds.select(clear=True)
        cmds.select(selection)
        self.displayAttachedControlRigs(hierarchyRoot)
        if cy_check:
            cmds.cycleCheck(evaluation=True)
        self.clearParentSwitchControlField()


    def displayAttachedControlRigs(self, rootJoint):
        cmds.textScrollList(self.uiVars['c_rig_attachedRigs_txScList'], edit=True, height=32, removeAll=True)
        if rootJoint:
            atRigList = cmds.getAttr(rootJoint+'.rigLayers')
            if atRigList != 'None':
                atRigList = atRigList.split(',')
                scrollHeight = len(atRigList) * 20
                if scrollHeight > 100:
                    scrollHeight = 100
                if scrollHeight == 20:
                    scrollHeight = 40
                for layer in sorted(atRigList):
                    layer = layer.replace('_', ' ')
                    cmds.textScrollList(self.uiVars['c_rig_attachedRigs_txScList'], edit=True, enable=True, 
                    												append=layer, height=scrollHeight, font='plainLabelFont')
                cmds.textScrollList(self.uiVars['c_rig_attachedRigs_txScList'], edit=True, selectIndexedItem=1)
                cmds.button(self.uiVars['c_rig_removeRigButton'], edit=True, enable=True)
            if atRigList == 'None':
                cmds.textScrollList(self.uiVars['c_rig_attachedRigs_txScList'], edit=True, enable=True, 
                		 height=32, append=['              < No rig(s) attached to the selected character hierarchy >'], 
                		 																		font='obliqueLabelFont')
                cmds.button(self.uiVars['c_rig_removeRigButton'], edit=True, enable=False)
        else:
            cmds.textScrollList(self.uiVars['c_rig_attachedRigs_txScList'], edit=True, enable=False, 
                              height=32, append=['      < select a character hierarchy to remove attached rig(s) >'], 
                              																	font='boldLabelFont')
            cmds.button(self.uiVars['c_rig_removeRigButton'], edit=True, enable=False)


    def returnValidSelectionFlagForCharacterHierarchy(self, selection):
        matchObjects = [re.compile('^MRT_character[a-zA-Z0-9]*__\w+_node_\d+_transform$'),
                        re.compile('^MRT_character[a-zA-Z0-9]*__\w+_root_node_transform$'),
                        re.compile('^MRT_character[a-zA-Z0-9]*__\w+_end_node_transform$')]
        i = 1
        for matchObject in matchObjects:
            matchResult = matchObject.match(selection)
            if matchResult:
                characterName = selection.partition('__')[0].partition('MRT_character')[2]
                skinJointSet = 'MRT_character%s__skinJointSet'%(characterName)
                status = cmds.sets(selection, isMember=skinJointSet)
                if status:
                    return True, i
                else:
                    return False, 0
            i += 1
        return False, 0


    def viewControlRigOptionsOnHierarchySelection(self):
        selection = mel.eval('ls -sl -type joint')
        if selection:
            selection = selection[-1]
            if re.match('^MRT_character\w+', selection):
                status = mfunc.checkForJointDuplication()
                if not status:
                    self.displayControlRiggingOptions(None)
                    self.displayAttachedControlRigs(None)
                    return
            status = self.returnValidSelectionFlagForCharacterHierarchy(selection)
            if status[0]:
                characterName = selection.partition('__')[0].partition('MRT_character')[2]
                rootJoint = mfunc.returnRootForCharacterHierarchy(selection)
                rootJointAllChildren = cmds.listRelatives(rootJoint, allDescendents=True, type='joint') or []
                children_roots = [item for item in rootJointAllChildren if \
                				  re.match('^MRT_character\w+_root_node_transform$', item)]
                if children_roots:
                    hierarchyTreeString = mfunc.returnHierarchyTreeListStringForCustomControlRigging(rootJoint)
                    self.displayControlRiggingOptions(rootJoint, hierarchyTreeString)
                else:
                    self.displayControlRiggingOptions(rootJoint)
                self.displayAttachedControlRigs(rootJoint)
            else:
                self.displayControlRiggingOptions(None)
                self.displayAttachedControlRigs(None)
        else:
            self.displayControlRiggingOptions(None)
            self.displayAttachedControlRigs(None)


    def clearParentSwitchControlField(self, *args):
        cmds.textField(self.uiVars['c_rig_prntSwitch_textField'], edit=True, text='< insert control >', 
        																						font='obliqueLabelFont')
        cmds.button(self.uiVars['c_rig_prntSwitch_addButton'], edit=True, enable=False)
        cmds.button(self.uiVars['c_rig_prntSwitch_RemoveAll'], edit=True, enable=False)
        cmds.button(self.uiVars['c_rig_prntSwitch_RemoveSelected'], edit=True, enable=False)
        cmds.button(self.uiVars['c_rig_prntSwitch_createButton'], edit=True, enable=False)
        cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], edit=True, removeAll=True)
        cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], edit=True, enable=False, 
        								 height=32, append=['\t           < no control inserted >'], font='boldLabelFont')
        self.controlParentSwitchGrp = None
        self.existingParentSwitchTargets = []



    def insertValidSelectionForParentSwitching(self, *args):
    
        selection = cmds.ls(selection=True)
        if selection:
            selection = selection[-1]
        else:
            return
        
        self.clearParentSwitchControlField()
        parent = cmds.listRelatives(selection, parent=True)[0]
        
        if re.match('^MRT_character[A-Za-z0-9]*__\w+_handle$', selection):
        
            if re.match('^MRT_character[A-Za-z0-9]*__\w+_(node_\d+_transform|end_node_transform){1}_handle$', selection):
                cmds.warning('MRT Error: Invalid control/object for assigning target parent controls. You can only select '\
                																			  'the root FK control handle.')
                return
            
            if re.match(selection+'_grp', parent):
            
                self.controlParentSwitchGrp = selection + '_parentSwitch_grp'
                cmds.textField(self.uiVars['c_rig_prntSwitch_textField'], edit=True, text=selection, font='plainLabelFont')
                self.updateListForExistingParentSwitchTargets()
                cmds.button(self.uiVars['c_rig_prntSwitch_addButton'], edit=True, enable=True)
            else:
                cmds.warning('MRT Error: Invalid control/object for parent switching. '
                			 'The control transform has no parent switch group.')
                self.clearParentSwitchControlField()
        else:
            cmds.warning('MRT Error: Invalid control/object for assigning target parent controls. '
            			 'You can only select a control transform (with suffix \'handle\').')
            self.clearParentSwitchControlField()



    def updateListForExistingParentSwitchTargets(self):
        cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], edit=True, height=32, removeAll=True)
        targetInfo = cmds.getAttr(self.controlParentSwitchGrp+'.parentTargetList')
        if targetInfo != 'None':
            targetInfoList = targetInfo.split(',')
            scrollHeight = len(targetInfoList) * 20
            if scrollHeight > 100:
                scrollHeight = 100
            if scrollHeight == 20:
                scrollHeight = 40
            if len(targetInfoList) > 0:
                for layer in sorted(targetInfoList):
                    if re.match('^MRT_character[A-Za-z0-9]*__root_transform$', layer):
                        #layer = layer + ' (default)'
                        cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], edit=True, 
                        				 enable=True, appendPosition=[1, layer], height=scrollHeight, font='plainLabelFont')
                    else:
                        cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], edit=True, 
                        							  enable=True, append=layer, height=scrollHeight, font='plainLabelFont')
                    self.existingParentSwitchTargets.append(layer)
                cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], edit=True, selectIndexedItem=1)
                self.postSelectionParentSwitchListItem()
                cmds.button(self.uiVars['c_rig_prntSwitch_RemoveAll'], edit=True, enable=True)
        else:
            cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], edit=True, enable=False,
                                            height=32, append='\t           < no current target(s) >', font='boldLabelFont')
        
        self.updateRemoveAllButtonStatForParentSwitching()



    def postSelectionParentSwitchListItem(self, *args):
        selectedItem = cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], query=True, selectItem=True)
        if selectedItem:
            cmds.button(self.uiVars['c_rig_prntSwitch_RemoveSelected'], edit=True, enable=True)
        else:
            cmds.button(self.uiVars['c_rig_prntSwitch_RemoveSelected'], edit=True, enable=False)



    def addSelectedControlToTargetList(self, *args):
    
        selection = cmds.ls(selection=True)
        
        if selection:
            selection = selection[-1]
        else:
            return
        
        if re.match('^MRT_character[A-Za-z0-9]*__\w+_handle$', selection) or
                                                    re.match('^MRT_character[A-Za-z0-9]*__root_transform$', selection):
                                                    
            ins_control = cmds.textField(self.uiVars['c_rig_prntSwitch_textField'], query=True, text=True)
            characterName = selection.partition('__')[0].partition('MRT_character')[2]
            ins_control = ins_control.partition('__')[2]
            ins_control_h_name = re.split('_[A-Z]', ins_control)[0]
            ins_control_rootJoint = 'MRT_character%s__%s_root_node_transform'%(characterName, ins_control_h_name)
            
            if not re.match('^MRT_character[A-Za-z0-9]*__root_transform$', selection):
            
                selectionName = selection.partition('__')[2]
                selectionUserSpecName = re.split('_[A-Z]', selectionName)[0]
                rootJoint = 'MRT_character%s__%s_root_node_transform'%(characterName, selectionUserSpecName)
                
                if rootJoint != ins_control_rootJoint:
                
                    result = mfunc.traverseConstrainedParentHierarchiesForSkeleton(rootJoint)
                    
                    if ins_control_rootJoint in result:
                    
                        cmds.warning('MRT Error: Cannot add target parent control from a child hierarchy, which ' \
                                     'will cause cyclic DG evaluation. Select and add another control handle.')
                        return
                else:
                    cmds.warning('MRT Error: Cannot add a target parent control within the same hierarchy. ' \
                                 'Select and add another control handle.')
                    return
            else:
                result = mfunc.traverseConstrainedParentHierarchiesForSkeleton(ins_control_rootJoint)
                
                if not result:
                    cmds.warning('MRT Warning: The joint hierarchy for the selected control rig has no parent hierarchy. '\
                                 'If you\'re adding the character root transform as a target parent for a root FK control '\
                                 'assigned to this hierarchy, it\'d have no effect.')

            #self.controlParentSwitchAddList.append(selection)
            if not cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], query=True, enable=True):
                cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], edit=True,
                                                                                            height=32, removeAll=True)

            allItems = cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], query=True, allItems=True) or []
            scrollHeight = (len(allItems) + 1)* 25
            if scrollHeight > 100:
                scrollHeight = 100
            if scrollHeight < 40:
                scrollHeight = 60
            selection = selection+' (new)'
            cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], edit=True, enable=True,
                                            append=selection, width=300, height=scrollHeight, font='plainLabelFont')
                                            
            cmds.button(self.uiVars['c_rig_prntSwitch_createButton'], edit=True, enable=True)

        else:
            cmds.warning('MRT Error: Invalid control/object as a parent target. You can only select a control ' \
                         'transform (with suffix \'handle\') or the character root transform.')
        
        self.updateRemoveAllButtonStatForParentSwitching()



    def removeSelectedTargetFromParentSwitchList(self, *args):
        selectedItem = cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], query=True, selectItem=True)[0]
        cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], edit=True, removeItem=selectedItem)
                                                                                    
        allItems = cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], query=True, allItems=True) or []
        if not allItems:
            cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], edit=True, enable=False,
                                        height=32, append='\t           < no current target(s) >', font='boldLabelFont')
        
        targetDiff = set.symmetric_difference(set(self.existingParentSwitchTargets), set(allItems))
        
        if len(targetDiff) > 0:
            cmds.button(self.uiVars['c_rig_prntSwitch_createButton'], edit=True, enable=True)
        else:
            cmds.button(self.uiVars['c_rig_prntSwitch_createButton'], edit=True, enable=False)
        
        cmds.button(self.uiVars['c_rig_prntSwitch_RemoveSelected'], edit=True, enable=False)

        if len(allItems):
            scrollHeight = len(allItems)* 25
            if scrollHeight > 100:
                scrollHeight = 100
            if scrollHeight == 50:
                scrollHeight = 60
            if scrollHeight == 25:
                scrollHeight = 40
            cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], edit=True, height=scrollHeight)
            self.postSelectionParentSwitchListItem()

        self.updateRemoveAllButtonStatForParentSwitching()



    def removeAllTargetsFromParentSwitchList(self, *args):
        allItems = cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], query=True, allItems=True)
        for item in allItems:
            cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], edit=True,
                                                                                                removeItem=item)
        
        remItems = cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], query=True, allItems=True) or []
        if not remItems:
            cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], edit=True,
                              enable=False, append='\t           < no current target(s) >', font='boldLabelFont')
        
        cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], edit=True, height=32)
        
        targetDiff = set.symmetric_difference(set(self.existingParentSwitchTargets), set(remItems))
        
        if len(targetDiff) > 0:
            cmds.button(self.uiVars['c_rig_prntSwitch_createButton'], edit=True, enable=True)
        else:
            cmds.button(self.uiVars['c_rig_prntSwitch_createButton'], edit=True, enable=False)
        
        cmds.button(self.uiVars['c_rig_prntSwitch_RemoveAll'], edit=True, enable=False)



    def updateRemoveAllButtonStatForParentSwitching(self):
        allItems = cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], query=True, allItems=True)
        if allItems:
            if len(allItems) == 1 and re.findall('< no current target\(s\) >', allItems[0]):
                cmds.button(self.uiVars['c_rig_prntSwitch_RemoveAll'], edit=True, enable=False)
            else:
                cmds.button(self.uiVars['c_rig_prntSwitch_RemoveAll'], edit=True, enable=True)
        else:
            cmds.button(self.uiVars['c_rig_prntSwitch_RemoveAll'], edit=True, enable=False)



    def create_update_parentSwitchTargetsForControl(self, *args):
    	"""
    	This method applies the changes to parent switch space options in the UI. It adds or removes the parent
    	targets for a selected / inserted control object.
    	"""
    	# Get all the current parent targets
        allItems = cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], query=True, allItems=True)
    	# Get the control to apply changes to parent switching                                                             
        ss_control = cmds.textField(self.uiVars['c_rig_prntSwitch_textField'], query=True, text=True)
        
        updatedTargets = []
        existingTargets = []
        
        # Collect the parent targets
        for item in allItems:
            if not '< no current target(s) >' in item:
                item = item.partition('(')[0].strip()
                updatedTargets.append(item)
        
        # Get the current parent targets
        for item in self.existingParentSwitchTargets:
            existingTargets.append(item)
            
        # Now get the parent targets to be updated
        targetsToBeRemoved = set.difference(set(existingTargets), set(updatedTargets))
        targetsToBeAdded = set.difference(set(updatedTargets), set(existingTargets))

        cmds.currentTime(0)
        
        # Collect the character root and world transform controls, and all the control rig
        # containers currently in the scene.
        nodes = []
        nodes.extend([item for item in cmds.ls(type='transform') if
                                                re.match('^MRT_character[0-9a-zA-Z]*__(world|root){1}_transform$', item)])
        nodes.extend([item for item in cmds.ls(type='container') if
                                                            re.match('^MRT_character[0-9a-zA-Z]*__\w+_Container$', item)])
                                                            
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

        if targetsToBeRemoved:
            for target in targetsToBeRemoved:
            
            	# Delete the switch condition node 
                parentSwitchCondition = '%s_%s_parentSwitch_condition' % (ss_control, target)
                cmds.delete(parentSwitchCondition)
                
                # Remove the target (to be removed) from the enum parent options list
                attrs = cmds.addAttr(ss_control+'.targetParents', query=True, enumName=True)
                attrs = attrs.split(':')
                index = attrs.index(target)
                attrs.pop(index)
                cmds.addAttr(ss_control+'.targetParents', edit=True, enumName=':'.join(attrs))
                
                # Remove the target constraint
                if cmds.objectType(ss_control, isType='joint'):
                    cmds.orientConstraint(target, self.controlParentSwitchGrp, edit=True, remove=True)
                else:
                    cmds.parentConstraint(target, self.controlParentSwitchGrp, edit=True, remove=True)
                
                # Update the parent target transform list
                currentTargets = cmds.getAttr(self.controlParentSwitchGrp+'.parentTargetList')
                currentTargets = currentTargets.split(',')
                index = currentTargets.index(target)
                currentTargets.pop(index)
                if isinstance(currentTargets, list):
                    currentTargets = ','.join(currentTargets)
                cmds.setAttr(self.controlParentSwitchGrp+'.parentTargetList', lock=False)
                cmds.setAttr(self.controlParentSwitchGrp+'.parentTargetList', currentTargets, type='string', lock=True)

        if targetsToBeAdded:
            for target in targetsToBeAdded:
            	
            	# Apply the constraint from the parent target
                if cmds.objectType(ss_control, isType='joint'):
                    constraint = cmds.orientConstraint(target, self.controlParentSwitchGrp, maintainOffset=True,
                                                            name=self.controlParentSwitchGrp+'_orientConstraint')[0]
                else:
                    constraint = cmds.parentConstraint(target, self.controlParentSwitchGrp, maintainOffset=True,
                                                            name=self.controlParentSwitchGrp+'_parentConstraint')[0]
                
                # Update the parent target options enum list on the control
                attrs = cmds.addAttr(ss_control+'.targetParents', query=True, enumName=True)
                attrs = attrs + ':' + target
                cmds.addAttr(ss_control+'.targetParents', edit=True, enumName=attrs)
                
                parentSwitchCondition = cmds.createNode('condition', name=ss_control+'_'+target+'_parentSwitch_condition',
                                                                                                          skipSelect=True)
                attrs = attrs.split(':')
                index = attrs.index(target)
                cmds.setAttr(parentSwitchCondition+'.firstTerm', index)
                cmds.connectAttr(ss_control+'.targetParents', parentSwitchCondition+'.secondTerm')
                cmds.setAttr(parentSwitchCondition+'.colorIfTrueR', 1)
                cmds.setAttr(parentSwitchCondition+'.colorIfFalseR', 0)
                weightIndex, ctrlAttr = mfunc.returnConstraintWeightIndexForTransform(target, constraint)
                cmds.connectAttr(parentSwitchCondition+'.outColorR', constraint+'.'+ctrlAttr)
                currentTargets = cmds.getAttr(self.controlParentSwitchGrp+'.parentTargetList')
                if currentTargets != 'None':
                    currentTargets = currentTargets+','+target
                    cmds.setAttr(self.controlParentSwitchGrp+'.parentTargetList', lock=False)
                    cmds.setAttr(self.controlParentSwitchGrp+'.parentTargetList', currentTargets, type='string', lock=True)
                else:
                    cmds.setAttr(self.controlParentSwitchGrp+'.parentTargetList', lock=False)
                    cmds.setAttr(self.controlParentSwitchGrp+'.parentTargetList', target, type='string', lock=True)

        targetInfo = cmds.getAttr(self.controlParentSwitchGrp+'.parentTargetList')
        if not targetInfo:
            cmds.setAttr(self.controlParentSwitchGrp+'.parentTargetList', lock=False)
            cmds.setAttr(self.controlParentSwitchGrp+'.parentTargetList', 'None', type='string', lock=True)

        allAttrs = cmds.addAttr(ss_control+'.targetParents', query=True, enumName=True)
        allAttrs = allAttrs.split(':')
        for attr in allAttrs[1:]:
            index = allAttrs.index(attr)
            parentSwitchCondition = ss_control+'_'+attr+'_parentSwitch_condition'
            cmds.setAttr(parentSwitchCondition+'.firstTerm', index)

        if len(allAttrs) == 1:
            cmds.setAttr(ss_control+'.targetParents', 0)
        if len(allAttrs) > 1:
            cmds.setAttr(ss_control+'.targetParents', 1)

        self.clearParentSwitchControlField()
        cmds.select(ss_control, replace=True)
        self.insertValidSelectionForParentSwitching()



    def makeCreateTabControls(self):
        """
        Create the tab layout contents for creating scene modules. Contains options for specifying module type,
        module length, module node attributes and components, module proxy geometry, module mirroring and module naming.
        """
        # Create the main column for the 'Create' tab.
        self.uiVars['modules_Column'] = cmds.columnLayout(adjustableColumn=True, rowSpacing=3)
        
        # Create a frame layout for 'Module Creation'.
        self.uiVars['modules_fLayout'] = cmds.frameLayout(label='Module creation', font='boldLabelFont', collapsable=True,
                                                              borderVisible=True, borderStyle='etchedIn', marginHeight=1,
                                                              marginWidth=2, collapse=True)
        
        # Create a row layout to hold a text label and two radio buttons.
        self.uiVars['moduleType_row'] = cmds.rowLayout(numberOfColumns=4, columnWidth=[(1, 100), (2, 85), (3, 100), (4, 100)],
                                              columnAttach=[(1, 'right', 15), (2, 'left', 0), (3, 'left', 5), (4, 'left', 0)])
                                              
        cmds.text(label='Module Type', font='boldLabelFont')
        
        self.uiVars['moduleType_radioColl'] = cmds.radioCollection()
        cmds.radioButton('JointNode', label='Joint Node', select=True, onCommand=self.modifyModuleCreationOptions)
        cmds.radioButton('SplineNode', label='Spline Node', select=False, onCommand=self.modifyModuleCreationOptions)
        cmds.radioButton('HingeNode', label='Hinge Node', select=False, onCommand=self.modifyModuleCreationOptions)
        
        # Set parent to the 'Module Creation' frame layout, and then create two field input sliders
        # and then two buttons for creating and undoing module creation.
        cmds.setParent(self.uiVars['modules_fLayout'])

        self.uiVars['numNodes_sliderGrp'] = cmds.intSliderGrp(field=True, label='Number of nodes',
                                                              columnWidth=[(1, 100), (2, 70), (3, 100)],
                                                              columnAttach=[(1, 'both', 5), (2, 'both', 5), (3, 'right', 5)],
                                                              minValue=1, maxValue=20, fieldMinValue=1, fieldMaxValue=100,
                                                              value=1, dragCommand=self.updateModuleLengthValue,
                                                              changeCommand=self.updateModuleLengthValue)
                                                              
        self.uiVars['lenNodes_sliderGrp'] = cmds.floatSliderGrp(field=True, label='Length of module',
                                                                columnWidth=[(1, 100), (2, 70), (3, 100)],
                                                                columnAttach=[(1, 'both', 5), (2, 'both', 5), (3, 'right', 5)],
                                                                minValue=0, maxValue=50, fieldMinValue=0, fieldMaxValue=100,
                                                                value=0, dragCommand=self.updateNumNodesValue,
                                                                changeCommand=self.updateNumNodesValue)
        
        # Put the module creation and undo buttons under a row layout.
        self.uiVars['moduleCreateButtons_row'] = cmds.rowLayout(numberOfColumns=2, rowAttach=[(1, 'top', 0), (2, 'top', 0)],
                                                                                           columnWidth=[(1, 190), (2, 190)],
                                                                              columnAttach=[(1, 'both', 3), (2, 'both', 3)])
                                                                
        self.uiVars['moduleCreate_button'] = cmds.button(label='Create', command=self.createModuleFromUI)
        
        self.uiVars['moduleUndoCreate_button'] = cmds.button(label='Undo last create', enable=False,
                                                                   command=self.undoCreateModuleTool)
        
        # Set parent to the main column for the tab to create the 'Create Options' frame layout.
        cmds.setParent(self.uiVars['modules_Column'])
        
        # Create a frame layout for 'Create Options'.
        self.uiVars['creationOpt_fLayout'] = cmds.frameLayout(label='Creation options', font='boldLabelFont',
                                                                  collapsable=True, borderVisible=True,
                                                                  borderStyle='etchedIn', marginHeight=1,
                                                                  marginWidth=2, collapse=True)
        
        # Create a row layout to hold four elements, a text label and radio buttons in a row.
        self.uiVars['creationPlane_row'] = cmds.rowLayout(numberOfColumns=4,
                                                          columnWidth=[(1, 146), (2, 81), (3, 81), (4, 81)],
                                                          columnAttach=[(1, 'right', 20)])
                                                          
        cmds.text(label='Creation Plane', font='boldLabelFont')
        
        self.uiVars['creationPlane_radioColl'] = cmds.radioCollection()
        cmds.radioButton('XY', label='XY', select=True)
        cmds.radioButton('YZ', label='YZ', select=False)
        cmds.radioButton('XZ', label='XZ', select=False)
        
        # Set parent to the 'Creation Options' frame layout.
        cmds.setParent(self.uiVars['creationOpt_fLayout'])
        self.uiVars['modOriginOffset_slider'] = cmds.floatSliderGrp(field=True, label='Offset from creation plane',
                                                                    columnWidth=[(1, 140), (2, 70), (3, 100)],
                                               columnAttach=[(1, 'both', 5), (2, 'both', 5), (3, 'right', 5)],
                                               minValue=0, maxValue=20, fieldMinValue=0, fieldMaxValue=100, value=1)
        # Create a separator.
        cmds.separator()
        
        # Create a row layout to hold four elements, a text label and three option menu controls in a row.
        self.uiVars['nodeAxes_row'] = cmds.rowLayout(numberOfColumns=4, columnWidth=[(1, 70), (2, 100), (3, 110), (4, 130)],
                                        columnAttach=[(1, 'right', 3), (2, 'right', 0), (3, 'left', 15), (4, 'left', 0)])
                                           
        cmds.text(label='Node Axes', font='boldLabelFont')
        self.uiVars['aimAxis_menu'] = cmds.optionMenu(label='Aim axis')
        cmds.menuItem(label='X')
        cmds.menuItem(label='Y')
        cmds.menuItem(label='Z')
        self.uiVars['upAxis_menu'] = cmds.optionMenu(label='Up axis')
        cmds.menuItem(label='Y')
        cmds.menuItem(label='X')
        cmds.menuItem(label='Z')
        self.uiVars['planeAxis_menu'] = cmds.optionMenu(label='Plane axis')
        cmds.menuItem(label='Z')
        cmds.menuItem(label='Y')
        cmds.menuItem(label='X')
        
        cmds.setParent(self.uiVars['modules_Column'])

        # Set parent to the main column for the tab to create the 'Node Components' frame layout.
        cmds.setParent(self.uiVars['modules_Column'])
        
        # Create a frame layout for 'Node Components'.
        self.uiVars['nodeCompnt_fLayout'] = cmds.frameLayout(label='Node components', font='boldLabelFont',
                                                                 collapsable=True, borderVisible=True, borderStyle='etchedIn',
                                                                 collapse=True, marginWidth=4)
        
        # Create a row layout to hold two check box elements in a row.
        self.uiVars['nodeCompnts_row'] = cmds.rowLayout(numberOfColumns=3, columnWidth=[(1, 100), (2, 140), (3, 160)],
                                                   columnAttach=[(1, 'right', 0), (2, 'right', 15), (3, 'right', 40)])
                                                   
        self.uiVars['node_hierarchy_check'] = cmds.checkBox(label='Hierarchy', enable=False, value=False)
        self.uiVars['node_orientation_check'] = cmds.checkBox(label='Orientation', enable=True, value=True)
        self.uiVars['proxyGeo_check'] = cmds.checkBox(label='Proxy Geometry', enable=True, value=False)
        
        # Set parent to 'Node Components' frame layout to create a child frame layout 'Proxy Geometry'.
        cmds.setParent(self.uiVars['nodeCompnt_fLayout'])
        
        # Create a frame layout for 'Proxy Geometry'.
        self.uiVars['proxyGeo_fLayout'] = cmds.frameLayout(label='Proxy geometry', font='boldLabelFont',
                                                                                     borderStyle='etchedIn',
                                                                                     collapsable=True,
                                                                                     collapse=True,
                                                                                     enable=False)
        # Create a row layout to hold two check box elements.
        self.uiVars['proxyGeoFrame_firstRow'] = cmds.rowLayout(numberOfColumns=2, columnWidth=[(1, 167), (2, 167)],
                                                               columnAttach=[(1, 'left', 60), (2, 'right', 0)])
                                                               
        self.uiVars['proxyGeoBones_check'] = cmds.checkBox(label='Create Bones', enable=False, value=False)
        self.uiVars['proxyGeoElbow_check'] = cmds.checkBox(label='Create Elbow / joint', enable=True, value=True,
                                                                    changeCommand=self.toggleElbowProxyTypeRadio)
        
        # Set parent to the 'Proxy Geometry' frame layout.
        cmds.setParent(self.uiVars['proxyGeo_fLayout'])
        self.uiVars['proxyElbowType_row'] = cmds.rowLayout(numberOfColumns=3, columnWidth=[(1, 145), (2, 125), (3, 125)],
                                                                        columnAttach=[(1, 'right', 0), (2, 'right', 30)])
        cmds.text(label='Elbow proxy type', font='plainLabelFont')
        
        self.uiVars['elbowproxyType_radioColl'] = cmds.radioCollection()
        
        cmds.radioButton('sphere', label='Sphere', select=True)
        cmds.radioButton('cube', label='Cube', select=False)
        cmds.setParent(self.uiVars['proxyGeo_fLayout'])
        
        # Create a separator.
        cmds.separator()
        
        # Create a row layout to hold a text label, and two radio buttons.
        self.uiVars['proxyGeoFrame_secondRow'] = cmds.rowLayout(numberOfColumns=3, columnWidth=[(1, 150), (2, 125), (3, 125)],
                                                                    columnAttach=[(1, 'right', 0), (2, 'right', 30)],
                                                                                                        enable=False)
        cmds.text(label='Mirror Instancing')
        
        self.uiVars['proxyGeo_mirrorInstn_radioColl'] = cmds.radioCollection()
        self.uiVars['proxyGeo_mirrorInstn_radioButton_on'] = cmds.radioButton('On', label='On', enable=True, select=False)
        self.uiVars['proxyGeo_mirrorInstn_radioButton_off'] = cmds.radioButton('Off', label='Off', enable=True, select=True)
        
        # Add options to the 'Proxy Geometry' checkbox. This is done here because the callback functions uses keys from
        # self.UI_Elements that are created after the checkBox is initialized.
        cmds.checkBox(self.uiVars['proxyGeo_check'], edit=True, onCommand=self.enableProxyGeoOptions,
                                                                offCommand=self.disableProxyGeoOptions)
        
        # Set parent to the main column for the tab to create the 'Mirroring' frame layout.
        cmds.setParent(self.uiVars['modules_Column'])
        
        # Create a frame layout for 'Mirroring'.
        self.uiVars['mirroring_fLayout'] = cmds.frameLayout(label='Mirroring & Transform Function', font='boldLabelFont',
                                                                    borderStyle='etchedIn', collapsable=True, collapse=True)
        
        # Create a row layout to hold a text label and two check box elements in a row.
        self.uiVars['mirrorSwitch_row'] = cmds.rowLayout(numberOfColumns=3, columnWidth=[(1, 130), (2, 130), (3, 130)],
                                                    columnAttach=[(1, 'right', 0), (2, 'right', 30), (3, 'right', 65)])
                                                    
        cmds.text(label='Mirror module', font='boldLabelFont')
        
        self.uiVars['mirrorSwitch_radioColl'] = cmds.radioCollection()
        cmds.radioButton('On', label='On', select=False, onCommand=self.enableMirrorFunctions)
        cmds.radioButton('Off', label='Off', select=True, onCommand=self.disableMirrorFunctions)
        
        # Set parent to the 'Mirroring' frame layout.
        cmds.setParent(self.uiVars['mirroring_fLayout'])
        
        # Create a separator.
        cmds.separator()
        
        # Create a text label.
        cmds.text(label='Transform Function', font='boldLabelFont')
        
        # Create a row column layout to hold a text label and two radio buttons in two subsequent rows.
        self.uiVars['transformFunc_rowColumn'] = cmds.rowColumnLayout(numberOfColumns=3,
                                                                      rowOffset=[(1, 'both', 2), (2, 'both', 2)],
                                                                columnWidth=[(1, 130), (2, 130), (3, 130)], enable=True)
                                                                
        cmds.text(label='Translation', font='obliqueLabelFont')
        
        self.uiVars['transFunc_radioColl'] = cmds.radioCollection()
        cmds.radioButton('World', label='World', select=False)
        cmds.radioButton('Local_Orientation', label='Local Orientation', select=True)
        
        cmds.text(label='Rotation (Mirror only)', font='obliqueLabelFont')
        
        self.uiVars['mirrorRot_radioColl'] = cmds.radioCollection()
        
        self.uiVars['mirrorRot_radioButton_behaviour'] = cmds.radioButton('Behaviour', label='Behaviour', select=True,
                                                                                                         enable=False)
        self.uiVars['mirrorRot_radioButton_ori'] = cmds.radioButton('Orientation', label='Orientation', select=False,
                                                                                                         enable=False)
        
        # Set parent to the main column for the tab to create the 'Module Naming / Handle Colour' frame layout.
        cmds.setParent(self.uiVars['modules_Column'])
        
        # Create the frame layout.
        self.uiVars['moduleNaming_fLayout'] = cmds.frameLayout(label='Module naming / Handle colour', font='boldLabelFont',
                                                                borderStyle='etchedIn', collapsable=True, collapse=True)
        
        # Create a row column layout to hold a text label with a text field in one row and then a text label with a color
        # index slider in the next row.
        self.uiVars['moduleNaming_rowColumn'] = cmds.rowColumnLayout(numberOfColumns=2,
                                                                     rowOffset=[(1, 'both', 2), (2, 'both', 2)],
                                                                     columnWidth=[(1, 140), (2, 245)])
        cmds.text(label='User specified name')
        
        self.uiVars['userSpecName_textField'] = cmds.textField(text='module', enable=True)
        
        cmds.text(label='Handle Colour')
        
        self.uiVars['handleColour_slider'] = cmds.colorIndexSliderGrp('__MRT_moduleHandleColour_IndexSliderGrp', minValue=1,
                                                                            maxValue=32, value=23, enable=True)

        # Save frames for create tab.
        self.createTabFrames.extend([self.uiVars['modules_fLayout'], self.uiVars['creationOpt_fLayout'],
                                     self.uiVars['nodeCompnt_fLayout'], self.uiVars['proxyGeo_fLayout'],
                                     self.uiVars['mirroring_fLayout'], self.uiVars['moduleNaming_fLayout']])



    def makeEditTabControls(self):
        """
        Create the tab layout contents for editing or working with scene modules. These include selecting and loading
        module collections, viewing scene module list (sorted or by hierarchy), saving module(s) as module collections,
        module renaming, deletion, duplication and module parenting operations.
        """
    
        scrollWidth = self.width_Height[0] - 20
        
        self.uiVars['edit_Column'] = cmds.columnLayout(adjustableColumn=True, rowSpacing=3)
        
        
        # List for module collections for loading, editing and deletion ---

        self.uiVars['loadedCollections_fLayout'] = cmds.frameLayout(label='Module collections', font='boldLabelFont',
                                                                        collapsable=True, borderVisible=True,
                                                                        borderStyle='etchedIn', marginHeight=1,
                                                                        marginWidth=2, collapse=True)
                                                                        
        self.uiVars['moduleCollection_txScList'] = cmds.textScrollList(enable=False, height=32,
                                                                             allowMultiSelection=False,
                                                                 append=['              < no module collection(s) loaded >'],
                                                                             font='boldLabelFont')

        cmds.setParent(self.uiVars['loadedCollections_fLayout'])
        
        self.uiVars['collectionDescrp_scrollField'] = cmds.scrollField(text='< no collection info >', font='obliqueLabelFont',
                                                                       editable=False, width=scrollWidth-10,
                                                                       enableBackground=True,
                                                                       backgroundColor=[0.7, 0.7, 0.7], height=32,
                                                                        wordWrap=True)
                                                                        
        self.uiVars['loadedCollections_button_install'] = cmds.button(label='Install selected module collection into the scene',
                                                            enable=False, command=self.installSelectedModuleCollectionToScene)
                                                            
        self.uiVars['loadedCollections_button_edit'] = cmds.button(label='Edit description for selected module collection',
                                                                   enable=False,
                                                                   command=self.editSelectedModuleCollectionDescriptionFromUI)
                                                                   
        self.uiVars['loadedCollections_button_delete'] = cmds.button(label='Delete selected module collection', enable=False,
                                                                                 command=self.deleteSelectedModuleCollection)

        cmds.setParent(self.uiVars['edit_Column'])
        
        
        # List of scene modules, module opertions ---
        
        self.uiVars['sceneModules_fLayout'] = cmds.frameLayout(label='Scene modules', font='boldLabelFont',
                                                                   collapsable=True, borderVisible=True, borderStyle='etchedIn',
                                                                   marginHeight=1, marginWidth=2, collapse=True)
                                                                   
        self.uiVars['moduleList_Scroll'] = cmds.scrollLayout(visible=True, childResizable=True, horizontalScrollBarThickness=0,
                                                             verticalScrollBarThickness=0, height=40)
                                                             
        self.uiVars['moduleList_fLayout'] = cmds.frameLayout(visible=True, borderVisible=False, collapsable=False,
                                                                                        labelVisible=False, height=32)
                                                                                        
        self.uiVars['sceneModuleList_treeVie(w'] = cmds.treeView('__MRT_treeView_SceneModulesUI', numberOfButtons=1,
                                                                allowReparenting=False, preventOverride=True, enable=False)

        cmds.setParent(self.uiVars['sceneModules_fLayout'])
        
        self.uiVars['sortModuleList_row'] = cmds.rowLayout(numberOfColumns=7, columnWidth=[(1, 50), (2, 120), (3, 120)],
                                           columnAttach=[(1, 'left', 10), (2, 'left', 20), (3, 'left', 10), (4, 'left', 20)],
                                           rowAttach=[(1, 'top', 2), (2, 'top', 0), (3, 'top', 0)], enable=False)
                                           
        cmds.text(label='Sort:', font='boldLabelFont')
        
        self.uiVars['sortModuleList_radioColl'] = cmds.radioCollection()
        
        cmds.radioButton('Alphabetically', label='Alphabetically', select=True, onCommand=self.toggleSceneModuleListSortTypeFromUI)
        cmds.radioButton('By_hierarchy', label='By hierarchy', select=False, onCommand=self.toggleSceneModuleListSortTypeFromUI)
        
        cmds.button(label='+', recomputeSize=False, width=20, height=20, command=self.increaseModuleListHeight)
        cmds.button(label='-', recomputeSize=False, width=20, height=20, command=self.decreaseModuleListHeight)
        cmds.button(label='R', recomputeSize=False, width=20, height=20, command=self.resetListHeightForSceneModulesUI)
        cmds.setParent(self.uiVars['sceneModules_fLayout'])
        
        
        # Saving module collections --
        
        self.uiVars['moduleSaveColl_button'] = cmds.button(label='Save selected module(s) as a collection', enable=False,
                                                                    command=self.makeCollectionFromSceneTreeViewModulesUI)
        
        self.uiVars['moduleSaveCollOptions_row1'] = cmds.rowLayout(enable=False, numberOfColumns=5, columnWidth=[(1, 70),
                                                                                      (2, 67), (3, 70), (4, 70), (5, 70)],
                                                      columnAttach=[(1, 'left', 10), (2, 'right', 10), (3, 'right', 20)])
        
        cmds.text(label='Include:', font='boldLabelFont')
        cmds.text(label='Parent', font='boldLabelFont')
        self.uiVars['moduleSaveColl_options_parentsCheckRadioCollection'] = cmds.radioCollection()
        
        cmds.radioButton('All_Parents', label='All', select=False)
        
        cmds.radioButton('Direct_Parent', label='Direct', select=True)
        
        cmds.radioButton('None', label='None', select=False)
        
        cmds.setParent(self.uiVars['sceneModules_fLayout'])
        
        self.uiVars['moduleSaveCollOptions_row2'] = cmds.rowLayout(enable=False, numberOfColumns=4, columnWidth=[(1, 140),
                                                                                                (2, 70), (3, 70), (4, 70)],
                                                                        columnAttach=[(1, 'right', 10), (2, 'right', 20)])
        
        cmds.text(label='Children', font='boldLabelFont')
        self.uiVars['moduleSaveColl_options_childrenCheckRadioCollection'] = cmds.radioCollection()
        self.uiVars['moduleSaveColl_options_childrenCheckRadioButtonAll'] = cmds.radioButton('All_Children', label='All',
                                                                                                        select=False)
                                                                                                            
        cmds.radioButton('Direct_Children', label='Direct', select=True)
                                                                                                
        cmds.radioButton('None', label='None', select=False)
        
        cmds.setParent(self.uiVars['sceneModules_fLayout'])
        cmds.separator()
        
        
        # Module renaming, deletion and duplication --
        
        self.uiVars['moduleEditFunc3_row'] = cmds.rowLayout(numberOfColumns=2, rowAttach=[(1, 'top', 0), (2, 'top', 0)],
                                                            columnWidth=[(1, 220), (2, 160)],
                                                            columnAttach=[(1, 'both', 3), (2, 'both', 3)])
        
        self.uiVars['moduleRename_textField'] = cmds.textField(enable=True, enterCommand=self.performModuleRename)
        
        self.uiVars['moduleRename_button'] = cmds.button(label='Rename selected module', enable=False,
                                                         command=self.performModuleRename)
        
        cmds.setParent(self.uiVars['sceneModules_fLayout'])
        
        self.uiVars['moduleEditFunc4_row'] = cmds.rowLayout(numberOfColumns=2, rowAttach=[(1, 'top', 0), (2, 'top', 0)],
                                                            columnWidth=[(1, 190), (2, 190)],
                                                            columnAttach=[(1, 'both', 3), (2, 'both', 3)])
        
        self.uiVars['moduleDelete_button'] = cmds.button(label='Delete selected module', enable=False,
                                                         command=self.performModuleDeletion)
        
        self.uiVars['moduleDuplicate_button'] = cmds.button(label='Duplicate selected module', enable=False,
                                                            command=self.performModuleDuplicate_UI_wrapper)

        cmds.setParent(self.uiVars['edit_Column'])
        
        
        # Module parenting --
        
        self.uiVars['moduleParenting_fLayout'] = cmds.frameLayout(label='Module parenting', font='boldLabelFont',
                                                                      collapsable=True, borderVisible=True,
                                                                      borderStyle='etchedIn', marginHeight=1, marginWidth=2,
                                                                      collapse=True)
        
        self.uiVars['moduleParent1_row'] = cmds.rowLayout(numberOfColumns=3, columnWidth=[(1, 130), (2, 130), (3, 130)],
                                                          columnAttach=[(1, 'right', 5), (2, 'right', 23), (3, 'both', 0)],
                                                          rowAttach=[(1, 'top', 4), (2, 'top', 2), (3, 'top', 2)])
        
        cmds.text(label='Parent type:', font='boldLabelFont')
        self.uiVars['moduleParent_radioColl'] = cmds.radioCollection()
        cmds.radioButton('Constrained', label='Constrained', select=True)
        cmds.radioButton('Hierarchical', label='Hierarchical', select=False)
        cmds.setParent(self.uiVars['moduleParenting_fLayout'])

        self.uiVars['moduleParent3_row'] = cmds.rowLayout(numberOfColumns=4, rowAttach=[(1, 'both', 0), (2, 'both', 0),
                                                                                        (3, 'both', 0), (4, 'both', 0)],
                                                                        columnWidth=[(1, 110), (2, 220), (3, 25), (4, 20)],
                                                                        columnAttach=[(1, 'both', 3), (2, 'both', 3),
                                                                                      (3, 'both', 0), (4, 'both', 0)])
        
        self.uiVars['moduleParent_button'] = cmds.button(label='Parent', enable=False, command=self.performParentForModule)
        
        self.uiVars['selectedParent_textField'] = cmds.textField(enable=True, editable=False,
                                                                 text='< insert parent module node >', font='obliqueLabelFont',
                                                                 enableBackground=True, backgroundColor=[0.7, 1.0, 0.4])
        
        cmds.button(label='<<', command=self.insertParentModuleNodeIntoField)
        cmds.button(label='C', command=self.clearParentModuleField)
        cmds.setParent(self.uiVars['moduleParenting_fLayout'])

        self.uiVars['moduleParent2_row'] = cmds.rowLayout(numberOfColumns=4, rowAttach=[(1, 'both', 0), (2, 'both', 0),
                                                                                        (3, 'both', 0), (4, 'both', 0)],
                                                                        columnWidth=[(1, 110), (2, 220), (3, 25), (4, 20)],
                                                                        columnAttach=[(1, 'both', 3), (2, 'both', 3),
                                                                                      (3, 'both', 0), (4, 'both', 0)])
                                                  
        self.uiVars['moduleUnparent_button'] = cmds.button(label='Unparent', enable=False, command=self.performUnparentForModule)
        
        self.uiVars['selectedChildModule_textField'] = cmds.textField(enable=True, editable=False,
                                                                      text='< insert child module >', font='obliqueLabelFont',
                                                                      enableBackground=True, backgroundColor=[1.0, 0.4, 0.9])
        
        cmds.button(label='<<', command=self.insertChildModuleIntoField)
        cmds.button(label='C', command=self.clearChildModuleField)
        cmds.setParent(self.uiVars['moduleParenting_fLayout'])

        self.uiVars['moduleParent_l_row'] = cmds.rowLayout(numberOfColumns=2, rowAttach=[(1, 'top', 0), (2, 'top', 0)],
                                                           columnWidth=[(1, 190), (2, 190)],
                                                           columnAttach=[(1, 'both', 3), (2, 'both', 3)])
        
        cmds.text(label='Parent module node', enableBackground=True, backgroundColor=[0.7, 1.0, 0.4])
        cmds.text(label='Child module', enableBackground=True, backgroundColor=[1.0, 0.4, 0.9])
        cmds.setParent(self.uiVars['moduleParenting_fLayout'])

        self.uiVars['moduleParent4_row'] = cmds.rowLayout(numberOfColumns=2, rowAttach=[(1, 'top', 0), (2, 'top', 0)],
                                                          columnWidth=[(1, 190), (2, 190)],
                                                          columnAttach=[(1, 'both', 3), (2, 'both', 3)])
                                                          
        self.uiVars['parentSnap_button'] = cmds.button(label='Snap parent to child', enable=False,
                                                            command=self.performSnapParentToChild)
        
        self.uiVars['childSnap_button'] = cmds.button(label='Snap child root to parent', enable=False,
                                                                command=self.performSnapChildToParent)
        
        # Save frames under edit tab ---
        
        self.editTabFrames.extend([self.uiVars['loadedCollections_fLayout'], self.uiVars['sceneModules_fLayout'],
                                                                             self.uiVars['moduleParenting_fLayout']])



    def makeRigTabControls(self):
        """
        Create the tab layout contents for rig controls. These functions will create character from scene module(s)
        and then modify it by applying control rigging and space switching.
        """
        scrollWidth = self.width_Height[0] - 20
        
        self.uiVars['rig_Column'] = cmds.columnLayout(adjustableColumn=True, rowSpacing=3)
        
        
        # Creating character from scene modules ---
        
        self.uiVars['characterCreation_fLayout'] = cmds.frameLayout(label='Character creation', font='boldLabelFont',
                                    		collapsable=True, borderVisible=True, borderStyle='etchedIn', marginHeight=5,
                                                                        					marginWidth=4, collapse=True)
                                                                        
        cmds.button(label='Create character from scene modules', command=self.processCharacterFromScene)
        
        cmds.button(label='Revert current character to modules', command=self.revertModulesFromCharacter)
        
        cmds.rowLayout(numberOfColumns=2, rowAttach=[(1, 'top', 2), (2, 'top', 0)], columnWidth=[(1, 180), (2, 190)],
                                          							   columnAttach=[(1, 'both', 3), (2, 'both', 3)])
                                          
        cmds.text(label='Character name (no underscore):')
        
        self.uiVars['characterName_textField'] = cmds.textField(text='')

        cmds.setParent(self.uiVars['rig_Column'])
        
        
        # Working with character templates ---
        
        self.uiVars['charTemplates_fLayout'] = cmds.frameLayout(label='Character templates and Control rigging',
                                    font='boldLabelFont', collapsable=True, borderVisible=True, borderStyle='etchedIn',
                                                                    	marginHeight=7, marginWidth=4, collapse=True)
                                                                    
        cmds.text(label='Note: You can only save a character template before adding a control rig', font='smallBoldLabelFont')
        
        cmds.button(label='Save character template from scene', command=self.saveCharacterTemplate)
        
        self.uiVars['charTemplatesList_fLayout'] = cmds.frameLayout(label='Templates', font='boldLabelFont',
                                    collapsable=True, borderVisible=True, borderStyle='etchedIn', marginHeight=1,
                                                                        			marginWidth=2, collapse=True)
                                                                        
        self.uiVars['charTemplates_txScList'] = cmds.textScrollList(enable=False, height=32, allowMultiSelection=False,
                                    append=['              < no character template(s) loaded >'], font='boldLabelFont')
                                        
        scrollWidth = self.width_Height[0] - 20
        
        self.uiVars['charTemplateDescrp_scrollField'] = cmds.scrollField(text='< no template info >', font='obliqueLabelFont',
                    			editable=False, width=scrollWidth-10, enableBackground=True, backgroundColor=[0.7, 0.7, 0.7], 
                                                                                                height=32, wordWrap=True)
                                                                         
        self.uiVars['charTemplate_button_import'] = cmds.button(label='Install selected character template', enable=False,
                                                                command=self.importSelectedCharTemplate)
                                                                
        self.uiVars['charTemplate_button_edit'] = cmds.button(label='Edit description for selected character template',
                                                    enable=False, command=self.editSelectedCharTemplateDescriptionFromUI)
                                                              
        self.uiVars['charTemplate_button_delete'] = cmds.button(label='Delete selected character template',
                                            		enable=False, command=self.deleteSelectedCharTemplate)
                                                                
        cmds.setParent(self.uiVars['charTemplates_fLayout'])
        
        
        # Working with control rigging ---
        
        self.uiVars['c_rig_fLayout'] = cmds.frameLayout(label='Control rigging', font='boldLabelFont',
                        				collapsable=True, borderVisible=True, borderStyle='etchedIn', marginHeight=3,
                                                                       					marginWidth=2, collapse=True)

        cmds.button(label='Click to view available control rigs for character hierarchies', height=20,
                    													  command=self.displayControlRiggingOptionsAllWindow)
                    
        self.uiVars['c_rig_txScList'] = cmds.textScrollList(enable=False, height=32,
                    allowMultiSelection=False, append=['        < select a character hierarchy to attach control rig(s) >'],
                                                                                                    font='boldLabelFont')
                                                                             
        cmds.rowColumnLayout(numberOfColumns=2, rowOffset=[(1, 'both', 2), (2, 'both', 2)], columnWidth=[(1, 105), (2, 260)])
        
        cmds.text(label='Control rig colour', font='smallBoldLabelFont')
        
        self.uiVars['controlLayerColour_slider'] = cmds.colorIndexSliderGrp('__MRT_controlLayerColour_IndexSliderGrp',
                                                                            minValue=1, maxValue=32, value=23, enable=True)
                                                                            
        cmds.setParent(self.uiVars['c_rig_fLayout'])
        
        self.uiVars['c_rig_attachRigButton'] = cmds.button(label='Attach rig', enable=False,
                                                           command=self.attachSelectedControlRigToHierarchy)
                                                                      
        cmds.setParent(self.uiVars['c_rig_fLayout'])
        
        self.uiVars['c_rig_attachedRigs_txScList'] = cmds.textScrollList(enable=False, height=32,
                    allowMultiSelection=False, append=['      < select a character hierarchy to remove attached rig(s) >'],
                                               font='boldLabelFont')
                                                                                          
        self.uiVars['c_rig_removeRigButton'] = cmds.button(label='Detach Rig', enable=False,
                                                           command=self.removeSelectedControlRigFromHierarchy)
                                                                      
        cmds.setParent(self.uiVars['charTemplates_fLayout'])
        
        
        # Working with space or parent switching ---
        
        self.uiVars['c_rig_prntSwitch_fLayout'] = cmds.frameLayout(label='Parent switching',
                        font='boldLabelFont', collapsable=True, borderVisible=True, borderStyle='etchedIn', marginHeight=3,
                                                                                marginWidth=2, collapse=True)
                                                                                       
        cmds.rowLayout(numberOfColumns=1, rowAttach=(1, 'both', 2), columnAttach=(1, 'left', 12))
        
        cmds.text(label='Note: Parent switching works only on control names with "handle" suffix.', font='smallBoldLabelFont')
        
        cmds.setParent(self.uiVars['c_rig_prntSwitch_fLayout'])
        
        self.uiVars['c_rig_prntSwitch_row1'] = cmds.rowLayout(numberOfColumns=3,
                                				 rowAttach=[(1, 'both', 0), (2, 'top', 0)], columnWidth=[(1, 299), (2, 33)],
                                                        columnAttach=[(1, 'both', 3), (2, 'both', 3)])
                                                                              
        self.uiVars['c_rig_prntSwitch_textField'] = cmds.textField(enable=True, editable=False,
                                                                   text='< insert control >', font='obliqueLabelFont')
                                                                                   
        cmds.button(label='<<', command=self.insertValidSelectionForParentSwitching)
        
        cmds.button(label='Clear', command=self.clearParentSwitchControlField)
        
        cmds.setParent(self.uiVars['c_rig_prntSwitch_fLayout'])
        
        cmds.text(label='Parent switch target(s)')
        
        self.uiVars['c_rig_prntSwitch_target_txScList'] = cmds.textScrollList(enable=False, height=32,
        					allowMultiSelection=False, append=['\t           < no control inserted >'], font='boldLabelFont',
                                                    selectCommand=self.postSelectionParentSwitchListItem)
                                                                        
        cmds.setParent(self.uiVars['c_rig_prntSwitch_fLayout'])
        
        self.uiVars['c_rig_prntSwitch_addButton'] = cmds.button(label='Add selected control to target list',
                                                                enable=False, command=self.addSelectedControlToTargetList)
                                                                                
        self.uiVars['c_rig_prntSwitch_row2'] = cmds.rowLayout(numberOfColumns=2,
                    							rowAttach=[(1, 'top', 0), (2, 'top', 0)], columnWidth=[(1, 188), (2, 188)],
                                                columnAttach=[(1, 'both', 3), (2, 'both', 3)])
                                                                              
        self.uiVars['c_rig_prntSwitch_RemoveAll'] = cmds.button(label='Remove All', enable=False,
                                                                command=self.removeAllTargetsFromParentSwitchList)
                                                                
        self.uiVars['c_rig_prntSwitch_RemoveSelected'] = cmds.button(label='Remove selected', enable=False,
                                                                     command=self.removeSelectedTargetFromParentSwitchList)
                                                                     
        cmds.setParent(self.uiVars['c_rig_prntSwitch_fLayout'])
        
        self.uiVars['c_rig_prntSwitch_createButton'] = cmds.button(label='Create / Update parent switch for' \
                                                                         'inserted control', enable=False,
                                                                    command=self.create_update_parentSwitchTargetsForControl)
        # Save frames under rig tab ---
        
        self.editTabFrames.extend([self.uiVars['characterCreation_fLayout'], self.uiVars['charTemplates_fLayout'],
                                   self.uiVars['charTemplatesList_fLayout'], self.uiVars['c_rig_fLayout'],
                                   self.uiVars['c_rig_prntSwitch_fLayout']])



    def increaseModuleListHeight(self, *args):
        """
        UI callback method to increment the height of scroll list for scene modules.
        """
        height = cmds.frameLayout(self.uiVars['moduleList_fLayout'], query=True, height=True)
        cmds.frameLayout(self.uiVars['moduleList_fLayout'], edit=True, height=height+40)
        cmds.scrollLayout(self.uiVars['moduleList_Scroll'], edit=True, height=height+48)



    def decreaseModuleListHeight(self, *args):
        """
        UI callback method to decrement the height of scroll list for scene modules.
        """
        # Get the module namespaces ion the scene.
        sceneNamespaces = cmds.namespaceInfo(listOnlyNamespaces=True)
        MRT_namespaces = mfunc.returnMRT_Namespaces(sceneNamespaces)
        
        # Set the size of the scroll list based on the number of modules, minus a decrement value.
        if MRT_namespaces != None:
            treeLayoutHeight = len(MRT_namespaces) * 29
            if treeLayoutHeight > 200:
                treeLayoutHeight = 200
            c_height = cmds.frameLayout(self.uiVars['moduleList_fLayout'], query=True, height=True)
            if (c_height - 40) >= treeLayoutHeight:
                cmds.scrollLayout(self.uiVars['moduleList_Scroll'], edit=True, height=(c_height - 40)+8)
                cmds.frameLayout(self.uiVars['moduleList_fLayout'], edit=True, height=c_height - 40)
            if (c_height - 40) < treeLayoutHeight:
                cmds.scrollLayout(self.uiVars['moduleList_Scroll'], edit=True, height=treeLayoutHeight+8)
                cmds.frameLayout(self.uiVars['moduleList_fLayout'], edit=True, height=treeLayoutHeight)


    '''
    # ---- FOR FUTURE USE - TO BE IMPLEMENTED ---- #
    
    def makeAnimateTabControls(self):
    
        self.uiVars['animate_Column'] = cmds.columnLayout(adjustableColumn=True, rowSpacing=3)

        self.uiVars['refCharacterList_fLayout'] = cmds.frameLayout(label='Referenced characters', font='boldLabelFont',
                                                                       collapsable=True, borderVisible=True,
                                                                       borderStyle='etchedIn', marginHeight=5,
                                                                       marginWidth=4, collapse=True)
                                                                       
        self.uiVars['refCharacterList_txScList'] = cmds.textScrollList(enable=False, height=32,
                                                                             allowMultiSelection=False,
                                                 append=['              < no character references(s) loaded in the scene >'],
                                                                             font='boldLabelFont')
                           
        self.uiVars['refCharacterList_button_load'] = cmds.button(label='Load a new character into the scene',
                                                                  enable=False,
                                                                  command=self.loadCharAsReference)
                                                                  
        self.uiVars['refCharacterList_button_unload'] = cmds.button(label='Unload the selected character from scene',
                                                                    enable=False,
                                                                    command=self.unloadRefCharFromScene)
                                                                    
        self.uiVars['refCharacterList_button_reload'] = cmds.button(label='Reload the selected character',
                                                                    enable=False, command=self.reloadRefCharInScene)
                                                                    
        cmds.setParent(self.uiVars['animate_Column'])

        # self.uiVars['characterAttributes_fLayout'] = cmds.frameLayout(label='Character attributes',
        #                                                                   font='boldLabelFont', collapsable=True,
        #                                                                   borderVisible=True, borderStyle='etchedIn',
        #                                                                   marginHeight=5, marginWidth=4, collapse=True)
        
        # cmds.text(label='Select a referenced character to display attributes', font='boldLabelFont')
        
        # cmds.setParent(self.uiVars['animate_Column'])

        self.uiVars['characterLayout_fLayout'] = cmds.frameLayout(label='Character control rigs', font='boldLabelFont',
                                                                      collapsable=True, borderVisible=True,
                                                                      borderStyle='etchedIn', marginHeight=5,
                                                                      marginWidth=4, collapse=True)
                                                                      
        cmds.text(label='Select a character in the scene from list to display its\nhierarchies and the controls on them',
                  font='boldLabelFont')
                  
        self.uiVars['refChar_selectListMenu'] = cmds.optionMenu(label='Character', enable=False)
        
        cmds.menuItem(label='No character found in the scene')
        
        cmds.text(label='Select a character hierarchy')
        
        self.uiVars['characterHierarchyList_txScList'] = cmds.textScrollList(enable=False, height=32,
                                                                                   allowMultiSelection=False,
                                               append=['                           < no character selected from the list >'],
                                                                                   font='boldLabelFont')
                                                                                   
        cmds.text(label='Select a control rig from the selected hierarchy to adjust its weight')
        
        self.uiVars['hierarchyControlRigList_txScList'] = cmds.textScrollList(enable=False, height=32,
                                                                                    allowMultiSelection=False,
                                               append=['                           < no character selected from the list >'],
                                                                                    font='boldLabelFont')
        cmds.setParent(self.uiVars['animate_Column'])

        # self.uiVars['animateConstraints_fLayout'] = cmds.frameLayout(label='Constraints', font='boldLabelFont',
        #                                                                  collapsable=True, borderVisible=True,
        #                                                                  borderStyle='etchedIn', marginHeight=5,
        #                                                                  marginWidth=4, collapse=True)
        
        # cmds.setParent(self.uiVars['animate_Column'])

        # self.uiVars['bakeAnim_fLayout'] = cmds.frameLayout(label='Bake animation to FK', font='boldLabelFont',
        #                                                        collapsable=True, borderVisible=True, borderStyle='etchedIn',
        #                                                              marginHeight=5, marginWidth=4, collapse=True)
        
        # cmds.text(label='Select a referenced character to bake animation', font='boldLabelFont')

        # self.animateTabFrames.extend([self.uiVars['refCharacterTemplates_fLayout'],
        #                               self.uiVars['characterAttributes_fLayout'],
        #                               self.uiVars['characterLayout_fLayout'],
        #                               self.uiVars['animateConstraints_fLayout'],
        #                               self.uiVars['bakeAnim_fLayout']])
        
        self.animateTabFrames.extend([self.uiVars['refCharacterList_fLayout'],
                                      self.uiVars['characterLayout_fLayout']])


    def loadCharAsReference(self, *args):
        pass
        

    def unloadRefCharFromScene(self, *args):
        pass
        

    def reloadRefCharInScene(self, *args):
        pass
    '''



    def createModuleFromUI(self, *args):
        """
        This method collects all the information from the 'Create' UI tab, and uses the "createModuleFromAttributes"
        from 'mrt_functions' to create a module.
        """
        # Check if a character exists in the scene. A module can't be created with a character in the scene.
        characterStatus = self.checkMRTcharacter()
        
        # If a character exists in the scene, skip creating a module.
        if characterStatus[0]:
            cmds.warning('MRT Error: Cannot create a module with a character in the scene.\n')
            return
        
        cmds.select(clear=True)
        
        # Update the user specified name field with a suffix if the module user spcified name exists in the scene.
        self.updateDefaultUserSpecifiedNameField()
        
        # Check if the length of the module specified in the create UI works with the number of nodes in the module.
        if not self.checkNodeNumWithLength():
            return

        # Collect module info from the create UI tab.
        self.moduleInfo = {}
        self.moduleInfo['node_type'] = nodeType = cmds.radioCollection(self.uiVars['moduleType_radioColl'],
                                                                       query=True,
                                                                       select=True)
        self.moduleInfo['module_length'] = cmds.floatSliderGrp(self.uiVars['lenNodes_sliderGrp'],
                                                               query=True,
                                                               value=True)
        self.moduleInfo['num_nodes'] = cmds.intSliderGrp(self.uiVars['numNodes_sliderGrp'],
                                                         query=True,
                                                         value=True)
        self.moduleInfo['creation_plane'] = cmds.radioCollection(self.uiVars['creationPlane_radioColl'],
                                                                  query=True,
                                                                  select=True)
        self.moduleInfo['module_offset'] = cmds.floatSliderGrp(self.uiVars['modOriginOffset_slider'],
                                                               query=True,
                                                               value=True)
        # Check the node axes for the module to be created.
        self.moduleInfo['node_axes'] = self.checkAndReturnNodeAxes()
        if self.moduleInfo['node_axes'] == None:
            return


        # Module components

        # Hierarchy representation.
        hierarchy = cmds.checkBox(self.uiVars['node_hierarchy_check'], query=True, value=True)

        # Orientaton representation control.
        orientation = cmds.checkBox(self.uiVars['node_orientation_check'], query=True, value=True)

        # Module proxy creation.
        proxy_geo_switch = cmds.checkBox(self.uiVars['proxyGeo_check'], query=True, value=True)
        self.moduleInfo['node_compnts'] = hierarchy, orientation, proxy_geo_switch

        # Proxy geo components.
        proxy_bones = cmds.checkBox(self.uiVars['proxyGeoBones_check'], query=True, value=True)
        proxy_elbows = cmds.checkBox(self.uiVars['proxyGeoElbow_check'], query=True, value=True)
        proxy_elbow_type = cmds.radioCollection(self.uiVars['elbowproxyType_radioColl'], query=True, select=True)

        # Mirror instancing for mirror module.
        proxy_mirror = cmds.radioCollection(self.uiVars['proxyGeo_mirrorInstn_radioColl'],
                                            query=True, select=True)
        # Save proxy geo options.
        self.moduleInfo['proxy_geo_options'] = proxy_bones, proxy_elbows, proxy_elbow_type, proxy_mirror

        # Mirroring for the module.
        mirror_switch = cmds.radioCollection(self.uiVars['mirrorSwitch_radioColl'], query=True, select=True)
        # Translate / Rotate mirror function.
        mirror_trans_func = cmds.radioCollection(self.uiVars['transFunc_radioColl'], query=True, select=True)
        mirror_rot_func = cmds.radioCollection(self.uiVars['mirrorRot_radioColl'], query=True, select=True)
        self.moduleInfo['mirror_options'] = mirror_switch, mirror_trans_func, mirror_rot_func

        # Get the handle colour for module.
        self.moduleInfo['handle_colour'] = cmds.colorIndexSliderGrp(self.uiVars['handleColour_slider'],
                                                                    query=True, value=True)
        # Get the user specified name.
        userSpecifiedName = cmds.textField(self.uiVars['userSpecName_textField'], query=True, text=True)
        userSpecifiedName = userSpecifiedName.lower()
        self.moduleInfo['userSpecName'] = userSpecifiedName

        # Construct the module namespace.
        self.moduleInfo['module_Namespace'] = 'MRT_%s__%s' % (nodeType, userSpecifiedName)
        # Construct the mirror module namespace. Used as a placeholder here.
        self.moduleInfo['mirror_module_Namespace'] = 'MRT_%s__%s_mirror' % (nodeType, userSpecifiedName)

        # Set the current module to be on the + side of the creation plane. If a mirror module is
        # to be created, this value is set to True. This is set by "createModuleFromAttributes".
        self.moduleInfo['mirrorModule'] = False

        # Create the module from attributes. Get the current time, this is used for undoing module creation.
        self.modules[time.time()] = mfunc.createModuleFromAttributes(self.moduleInfo, createFromUI=True)

        # Set the 'undo create' module button to True.
        cmds.button(self.uiVars['moduleUndoCreate_button'], edit=True, enable=True)

        # Update UI for the edit module tab.
        self.updateListForSceneModulesInUI()
        self.clearParentModuleField()
        self.clearChildModuleField()



    def undoCreateModuleTool(self, *args):
        """
        Undo a module creation, if the module is stored in self.modules.
        """
        # Module namespaces to be removed. There's two namespaces if the module is a mirror module.
        namespacesToBeRemoved = []
        
        # Delete mirror move nodes with its connections.
        mfunc.deleteMirrorMoveConnections()
        
        # Get the current namespace, set the namespace to root.
        currentNamespace = cmds.namespaceInfo(currentNamespace=True)
        cmds.namespace(setNamespace=':')

        # Get all module namespaces in the scene.
        moduleNamespaces = mfunc.returnMRT_Namespaces(cmds.namespaceInfo(listOnlyNamespaces=True))
        
        # Skip module undo if no module namespace exists in the scene.
        if moduleNamespaces == None:
            cmds.button(self.uiVars['moduleUndoCreate_button'], edit=True, enable=False)
            self.modules = {}
            return

        # If modules are created in the current UI session (without refreshing the MRT UI),
        # undo the last module creation.
        if len(self.modules):
            
            # Get the last created module namespace (or mirror module namespaces).
            lastCreatedModuleNamespaces = self.modules.pop(sorted(self.modules, reverse=True)[0])
            
            # Remove the module or the mirror module pair.
            for namespace in lastCreatedModuleNamespaces:
            
                if cmds.namespace(exists=namespace):
                    
                    # Remove children module relationship(s), if any.
                    self.removeChildrenModules(namespace)
                    
                    # Delete the module container and its nodes.
                    moduleContainer = namespace+':module_container'
                    cmds.lockNode(moduleContainer, lock=False, lockUnpublished=False)
                    dgNodes = cmds.container(moduleContainer, query=True, nodeList=True)
                    
                    for node in dgNodes:
                        if node.endswith('_curveInfo'):
                            cmds.delete(node)
                    
                    # Delete the proxy geometry for the module if it exists.
                    try:
                        proxyGeoGrp = namespace+':proxyGeometryGrp'
                        cmds.select(proxyGeoGrp, replace=True)
                        cmds.delete()
                    except:
                        pass
                    
                    cmds.select(moduleContainer, replace=True)
                    cmds.delete()
                    
                    # Get the module namespaces to be removed.
                    namespacesToBeRemoved.append(namespace)

            # Remove the module namespaces.
            if len(namespacesToBeRemoved) > 0:
                for namespace in namespacesToBeRemoved:
                    cmds.namespace(removeNamespace=namespace)

            mfunc.cleanSceneState()
        
        # If self.modules is empty, disable undo module button.
        else:
            cmds.button(self.uiVars['moduleUndoCreate_button'], edit=True, enable=False)

        # If all modules are removed from the scene, set the undo module to False.
        if len(self.modules) == 0:
            cmds.button(self.uiVars['moduleUndoCreate_button'], edit=True, enable=False)

        if cmds.namespace(exists=currentNamespace):
            cmds.namespace(setNamespace=currentNamespace)

        # Update UI for the edit module tab.
        self.clearParentModuleField()
        self.clearChildModuleField()
        self.updateListForSceneModulesInUI()



    def updateDefaultUserSpecifiedNameField(self):
        """
        Update the user specified module name field. This checks if the current module name exists in the scene
        and update the value with a numerical suffix.
        """
    
        # Get the current user specified name.
        userSpecifiedName = cmds.textField(self.uiVars['userSpecName_textField'], query=True, text=True)
        userSpecifiedName = re.split('_+\d+', userSpecifiedName)[0].lower()
        
        # Get a list of module namespaces in the scene.
        currentNamespace = cmds.namespaceInfo(currentNamespace=True)
        cmds.namespace(setNamespace=':')
        moduleNamespaces = mfunc.returnMRT_Namespaces(cmds.namespaceInfo(listOnlyNamespaces=True))
        cmds.namespace(setNamespace=currentNamespace)
        
        # If module namespaces exist, get their respective user specified names.
        if moduleNamespaces:
            userSpecifiedNames = mfunc.returnModuleUserSpecNames(moduleNamespaces)[1]
            
            # Get the highest trailing number suffix for the namespaces with default 'module' name.
            if userSpecifiedName in userSpecifiedNames:
                underscore_search = '_'
                
                if re.match('^\w+_[0-9]*$', userSpecifiedName):
                    underscore_search = re.findall('_*', userSpecifiedName)
                    underscore_search.reverse()
                    for item in underscore_search:
                        if '_' in item:
                            underscore_search = item
                            break
                    
                    userSpecNameBase = userSpecifiedName.rpartition(underscore_search)[0]
            
                else:
                    userSpecNameBase = userSpecifiedName
                
                suffix = mfunc.findHighestNumSuffix(userSpecNameBase, userSpecifiedNames)
                text = '{0}{1}{2}'.format(userSpecifiedName, underscore_search, suffix+1)
        
            else:
                text = userSpecifiedName
            
            # Update the text field.
            cmds.textField(self.uiVars['userSpecName_textField'], edit=True, text=text)
    
        if not moduleNamespaces:
            cmds.textField(self.uiVars['userSpecName_textField'], edit=True, text=userSpecifiedName)



    def checkAndReturnNodeAxes(self):
        """
        Checks the "node axes" field values in the create UI tab.
        """
        # Get the field values.
        node_aim_axis = cmds.optionMenu(self.uiVars['aimAxis_menu'], query=True, value=True)
        node_up_axis = cmds.optionMenu(self.uiVars['upAxis_menu'], query=True, value=True)
        node_front_axis = cmds.optionMenu(self.uiVars['planeAxis_menu'], query=True, value=True)
        node_axes = node_aim_axis + node_up_axis + node_front_axis
        
        for axis in ['X', 'Y', 'Z']:
            if node_axes.count(axis) > 1:
                cmds.warning('MRT Error: Node axes error. More than one axis have been assigned the same value.')
                return None
        
        return node_axes



    def checkNodeNumWithLength(self):
        """
        Checks the module length with its number of nodes for creation.
        """
        # Get the field values.
        module_length = cmds.floatSliderGrp(self.uiVars['lenNodes_sliderGrp'], query=True, value=True)
        num_nodes = cmds.intSliderGrp(self.uiVars['numNodes_sliderGrp'], query=True, value=True)
        
        # Check if the module length is 0 and number of nodes > 1 and vice versa.
        
        if num_nodes != 1 and module_length == 0:
        
            cmds.warning('MRT Error: Module Length Error. \
                          A module with %s nodes cannot be created with the specified length.'%(num_nodes))
            return False
        
        if num_nodes == 1 and module_length > 0.0:
            cmds.warning('MRT Error: Module Length Error. \
                          A module with single node cannot be created with the specified length.')
            return False
        
        return True



    def modifyModuleCreationOptions(self, *args):
        """
        Sets the UI attributes for module creation, based on the selected module type for creation.
        This is a UI callback method when the module type radio button is selected.
        """
        # Get the module node type
        node_type = cmds.radioCollection(self.uiVars['moduleType_radioColl'], query=True, select=True)
        
        if node_type == 'JointNode':
        
            cmds.intSliderGrp(self.uiVars['numNodes_sliderGrp'], edit=True, minValue=1, maxValue=20,
                              fieldMinValue=1, fieldMaxValue=100, value=1, enable=True)
                              
            cmds.floatSliderGrp(self.uiVars['lenNodes_sliderGrp'], edit=True, minValue=0, maxValue=50,
                                fieldMinValue=0, fieldMaxValue=100, value=0)
                                
            self.updateNumNodesValue([])

        if node_type == 'SplineNode':
        
            cmds.intSliderGrp(self.uiVars['numNodes_sliderGrp'], edit=True, minValue=4, maxValue=20,
                              fieldMinValue=4, fieldMaxValue=100, value=4, enable=True)
                              
            cmds.floatSliderGrp(self.uiVars['lenNodes_sliderGrp'], edit=True, minValue=1, maxValue=50,
                                fieldMinValue=1, fieldMaxValue=100, value=4)
                                
            self.updateNumNodesValue([])

        if node_type == 'HingeNode':
        
            cmds.intSliderGrp(self.uiVars['numNodes_sliderGrp'], edit=True, minValue=1, maxValue=20,
                              fieldMinValue=3, fieldMaxValue=100, value=3, enable=False)
                              
            cmds.floatSliderGrp(self.uiVars['lenNodes_sliderGrp'], edit=True, minValue=1, maxValue=50,
                                fieldMinValue=1, fieldMaxValue=100, value=3)
                                
            self.updateNumNodesValue([])


    def enableProxyGeoOptions(self, *args):
        """
        Enables the Proxy Geo UI options. UI callback method.
        """
        cmds.frameLayout(self.uiVars['proxyGeo_fLayout'], edit=True, enable=True)


    def disableProxyGeoOptions(self, *args):
        """
        Disables the Proxy Geo UI options. UI callback method.
        """
        cmds.frameLayout(self.uiVars['proxyGeo_fLayout'], edit=True, enable=False, collapse=True)


    def enableMirrorFunctions(self, *args):
        """
        Enable the module mirroring options in the create UI tab. UI callback method.
        """
        cmds.radioButton(self.uiVars['mirrorRot_radioButton_behaviour'], edit=True, enable=True)
        cmds.radioButton(self.uiVars['mirrorRot_radioButton_ori'], edit=True, enable=True)
        cmds.rowLayout(self.uiVars['proxyGeoFrame_secondRow'], edit=True, enable=True)


    def disableMirrorFunctions(self, *args):
        """
        Disables the module mirroring options in the create UI tab. UI callback method.
        """
        cmds.radioButton(self.uiVars['mirrorRot_radioButton_behaviour'], edit=True, enable=False)
        cmds.radioButton(self.uiVars['mirrorRot_radioButton_ori'], edit=True, enable=False)
        cmds.rowLayout(self.uiVars['proxyGeoFrame_secondRow'], edit=True, enable=False)
        cmds.radioButton(self.uiVars['proxyGeo_mirrorInstn_radioButton_on'], edit=True, select=False)
        cmds.radioButton(self.uiVars['proxyGeo_mirrorInstn_radioButton_off'], edit=True, select=True)


    def updateModuleLengthValue(self, *args):
        """
        Updates the module length value in the UI based on the number of module nodes and the type of
        module node type set in the create UI tab. UI callback method.
        """
        num_nodes = cmds.intSliderGrp(self.uiVars['numNodes_sliderGrp'], query=True, value=True)
        length_module = cmds.floatSliderGrp(self.uiVars['lenNodes_sliderGrp'], query=True, value=True)
        node_type = cmds.radioCollection(self.uiVars['moduleType_radioColl'], query=True, select=True)
        
        if num_nodes > 1 and length_module == 0:
            cmds.floatSliderGrp(self.uiVars['lenNodes_sliderGrp'], edit=True, value=0.1)
            cmds.checkBox(self.uiVars['node_orientation_check'], edit=True, value=False)
            cmds.checkBox(self.uiVars['node_hierarchy_check'], edit=True, enable=True, value=True)
            cmds.checkBox(self.uiVars['proxyGeoBones_check'], edit=True, enable=True, value=True)
        
        if num_nodes == 1 and length_module > 0:
            cmds.floatSliderGrp(self.uiVars['lenNodes_sliderGrp'], edit=True, value=0)
            cmds.checkBox(self.uiVars['node_orientation_check'], edit=True, value=True)
            cmds.checkBox(self.uiVars['node_hierarchy_check'], edit=True, enable=False, value=False)
            cmds.checkBox(self.uiVars['proxyGeoBones_check'], edit=True, enable=False, value=False)
        
        if node_type == 'JointNode':
            if num_nodes > 1:
                cmds.checkBox(self.uiVars['proxyGeoBones_check'], edit=True, enable=True)
        
        if node_type == 'SplineNode':
            cmds.checkBox(self.uiVars['node_orientation_check'], edit=True, value=True)
            cmds.checkBox(self.uiVars['node_hierarchy_check'], edit=True, enable=True, value=True)
            cmds.checkBox(self.uiVars['proxyGeoBones_check'], edit=True, enable=False, value=False)

        if node_type == 'HingeNode':
            cmds.checkBox(self.uiVars['proxyGeoBones_check'], edit=True, enable=True)
            cmds.checkBox(self.uiVars['node_orientation_check'], edit=True, enable=True, value=True)
            cmds.checkBox(self.uiVars['node_hierarchy_check'], edit=True, enable=True)


    def updateNumNodesValue(self, *args):
        """
        Updates the number of module nodes in the UI based on the number of module nodes and the type of
        module node type set in the create UI tab. UI callback method.
        """
        length_module = cmds.floatSliderGrp(self.uiVars['lenNodes_sliderGrp'], query=True, value=True)
        num_nodes = cmds.intSliderGrp(self.uiVars['numNodes_sliderGrp'], query=True, value=True)
        node_type = cmds.radioCollection(self.uiVars['moduleType_radioColl'], query=True, select=True)
        
        if length_module == 0:
            cmds.intSliderGrp(self.uiVars['numNodes_sliderGrp'], edit=True, value=1)
            cmds.checkBox(self.uiVars['node_orientation_check'], edit=True, value=True)
            cmds.checkBox(self.uiVars['node_hierarchy_check'], edit=True, enable=False, value=False)
            cmds.checkBox(self.uiVars['proxyGeoBones_check'], edit=True, enable=False, value=False)
        
        if length_module > 0 and num_nodes == 1:
            cmds.intSliderGrp(self.uiVars['numNodes_sliderGrp'], edit=True, value=2)
            cmds.checkBox(self.uiVars['node_orientation_check'], edit=True, value=False)
            cmds.checkBox(self.uiVars['node_hierarchy_check'], edit=True, enable=True)
            cmds.checkBox(self.uiVars['proxyGeoBones_check'], edit=True, enable=True, value=True)
        
        if length_module > 0 and num_nodes > 1:
            cmds.checkBox(self.uiVars['node_hierarchy_check'], edit=True, enable=True, value=True)
        
        if node_type == 'JointNode':
            if length_module == 0:
                cmds.checkBox(self.uiVars['proxyGeoBones_check'], edit=True, enable=False, value=False)
        
        if node_type == 'SplineNode':
            cmds.checkBox(self.uiVars['node_orientation_check'], edit=True, value=True)
            cmds.checkBox(self.uiVars['node_hierarchy_check'], edit=True, enable=True, value=True)
            cmds.checkBox(self.uiVars['proxyGeoBones_check'], edit=True, enable=False, value=False)

        if node_type == 'HingeNode':
            cmds.checkBox(self.uiVars['proxyGeoBones_check'], edit=True, enable=True)
            cmds.checkBox(self.uiVars['node_orientation_check'], edit=True, enable=True, value=True)
            cmds.checkBox(self.uiVars['node_hierarchy_check'], edit=True, enable=True)


    def collapseAllUIframes(self, *args):
        """
        Called as a menu item under windows to collapse all frames under UI tabs.
        """
        for element in self.uiVars:
        
            try:
                if cmds.objectTypeUI(self.uiVars[element], isType='frameLayout'):
                    if cmds.frameLayout(self.uiVars[element], query=True, enable=True):
                        cmds.frameLayout(self.uiVars[element], edit=True, collapse=True)
            
            except RuntimeError:
                pass


    def expandAllUIframes(self, *args):
        """
        Called as a menu item under windows to expand frames under the current UI tab.
        """
        currentTabIndex = cmds.tabLayout(self.uiVars['tabs'], query=True, selectTabIndex=True)
        
        if currentTabIndex == 1:
            for frame in self.createTabFrames:
                if cmds.frameLayout(frame, query=True, enable=True):
                    cmds.frameLayout(frame, edit=True, collapse=False)
        
        if currentTabIndex == 2:
            for frame in self.editTabFrames:
                if cmds.frameLayout(frame, query=True, enable=True):
                    cmds.frameLayout(frame, edit=True, collapse=False)
                    
        if currentTabIndex == 3:
            for frame in self.animateTabFrames:
                if cmds.frameLayout(frame, query=True, enable=True):
                    cmds.frameLayout(frame, edit=True, collapse=False)
                    

    def toggleElbowProxyTypeRadio(self, *args):
        stat = cmds.checkBox(self.uiVars['proxyGeoElbow_check'], query=True, value=True)
        if stat:
            cmds.rowLayout(self.uiVars['proxyElbowType_row'], edit=True, enable=True)
        else:
            cmds.rowLayout(self.uiVars['proxyElbowType_row'], edit=True, enable=False)



