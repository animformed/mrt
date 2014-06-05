# *************************************************************************************************************
#
#    mrt_UI.py - Main UI source for modular rigging tools for maya. Contains the UI class, and its methods
#                called during runtime events and user commands.
#
#    Can be modified or copied for your own purpose. Please keep updating it for use with future versions
#    of Maya. This was originally written for Maya 2011, and updated for 2013 and then for 2014.
#
#    Written by Himanish Bhattacharya.
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

# Now declare MEL and Python UI callbacks calling the defined functions above,
# depending on the maya's version.

if _maya_version >= 2013:
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

        # Save the current selection
        selection = cmds.ls(selection=True)

        # Turn off undo
        cmds.undoInfo(stateWithoutFlush=False)

        # Dictionary to hold UI elements by key.
        self.uiVars = {}

        # To store main UI tab frameLayouts
        self.createTabFrames = []
        self.editTabFrames = []
        self.animateTabFrames = []

        # For storing the module collections and character template paths by key.
        self.module_collectionList = {}
        self.charTemplateList = {}

        # To store the selected module items in the scene modules treeView list.
        self.treeViewSelection_list = {}

        # To store the control rigging properties / attributes for a character joint hierarchy.
        self.controlRiggingAttributes = {}

        # To store the parent transform for control for parent switching (which is constrained).
        self.controlParentSwitchGrp = None
        # To store the current parent targets.
        self.existingParentSwitchTargets = []

        # To store the id for the scriptJob which runs when MRT UI is closed (for cleanup).
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
        self.uiVars['window'] = cmds.window('mrt_UI_window', title='Modular Rigging Tools',
                                            widthHeight=self.width_Height, resizeToFitChildren=True, maximizeButton=False)

        # Remove the main window from preferences.
        try:
            cmds.windowPref('mrt_UI_window', remove=True)
        except:
            # For some reason, maya occasionally prompts the window element doesn't exist under windowPref. Not sure why.
            pass

        # Create a menu bar under main window, with two menu elements, 'File' and 'Help'.
        cmds.menuBarLayout()

        # The 'File' menu will have saving and loading file operations.
        self.uiVars['fileMenu_windowBar'] = cmds.menu(label='File')
        self.uiVars['autoLoad_moduleCollection_check'] = cmds.menuItem(label='Auto-load settings for module collection(s)',
                                                                           command=self.autoLoadSettingsUIforCollections)
        cmds.menuItem(divider=True)
        self.uiVars['autoLoad_moduleCollection_selectDir'] = \
            cmds.menuItem(label='Select directory for loading saved collection(s)',
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
        # cmds.menuItem(label='Exit', command=('cmds.deleteUI(\"'+self.uiVars['window']+'\")')) # OR
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
        cmds.menuItem(label='Create parent switch group for selected control handle',
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

        # Show the main window.
        cmds.showWindow(self.uiVars['window'])

        # DEPRECATED #
        # I didn't like the dock control on this. You want it? Enable and test it.
        # self.uiVars['dockWindow'] = cmds.dockControl('mrt_UI_dockWindow', label='Modular Rigging Tools',
        #                                                    area='left', content=self.uiVars['window'],
        #                                                    allowedArea=['left', 'right'])

        # Reset UI prefernces
        self.resetListHeightForSceneModulesUI()
        self.updateListForSceneModulesInUI()
        self.selectModuleInTreeViewUIfromViewport()
        self.createUIutilityScriptJobs()

        # Get the default paths for saving / loading UI preferences
        self.autoCollections_path = \
                           cmds.internalVar(userScriptDir=True)+'MRT/module_collections/auto-generated_character_collections'
        self.ui_preferences_path = cmds.internalVar(userScriptDir=True)+'MRT/mrt_uiPrefs'
        self.module_collectionList_path = cmds.internalVar(userScriptDir=True)+'MRT/mrt_collectionList'
        self.charTemplateList_path = cmds.internalVar(userScriptDir=True)+'MRT/mrt_charTemplateList'

        # Load the preferences for loading module collections and character templates
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

        # Load the module collections using the preferences
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

        # Load the character templates using the preferences
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

        # Re-select
        if selection:
            cmds.select(selection)

        # Turn on undo
        cmds.undoInfo(stateWithoutFlush=True)

    # -------------------------------------------------------------------------------------------------------------
    #
    #   TOP MENU ITEM METHODS
    #
    # -------------------------------------------------------------------------------------------------------------

    def autoLoadSettingsUIforCollections(self, *args):
        '''
        Shows the auto load settings for module collections. It has two preferences,
        "Preserve and load current list at next startup" and "Load new saved collection(s) to current list".
        The first option loads the current module collection(s) next time MRT UI is restarted. The second option
        adds any new module collection saved to disk to the list.
        '''
        def setAutoLoadSettingsValues(*args):
            # I'm defining a local function here since it'll be used only within
            # the scope of "autoLoadSettingsUIforCollections".
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

        # Close the preferences window if open
        try:
            cmds.deleteUI('mrt_autoLoadSettingsUI_window')
        except:
            pass

        # Create the preferences window
        self.uiVars['autoLoadSettingsUIwindow'] = cmds.window('mrt_autoLoadSettingsUI_window',
                                                               title='Auto-load settings for module collections',
                                                               width=90, maximizeButton=False, sizeable=False)
        try:
            cmds.windowPref('mrt_autoLoadSettingsUI_window', remove=True)
        except:
            pass

        # Main window column
        self.uiVars['autoLoadSettingsWindowColumn'] = cmds.columnLayout(adjustableColumn=True)

        cmds.text(label='')

        # Get the default preferences
        ui_preferences_file = open(self.ui_preferences_path, 'rb')
        ui_preferences = cPickle.load(ui_preferences_file)
        ui_preferences_file.close()
        loadAtStartup = ui_preferences['autoLoadPreviousCollectionListAtStartupStatus']
        loadNewCollections = ui_preferences['autoLoadNewSavedModuleCollectionToListStatus']

        # Create the checkboxes for setting the preferences. Load the previous preferred values.
        cmds.rowLayout(numberOfColumns=1, columnAttach=([1, 'left', 57]))
        self.uiVars['autoLoadPreviousCollectionListAtStartup_checkBox'] = \
            cmds.checkBox(label='Preserve and load current list at next startup', value=loadAtStartup,
                                                                                changeCommand=setAutoLoadSettingsValues)
        cmds.setParent(self.uiVars['autoLoadSettingsWindowColumn'])
        cmds.rowLayout(numberOfColumns=1, columnAttach=([1, 'both', 60]), rowAttach=([1, 'top', 5]))
        self.uiVars['autoLoadNewSavedModuleCollectionToList_checkBox'] = \
            cmds.checkBox(label='Load new saved collection(s) to current list', value=loadNewCollections, \
                                                                                changeCommand=setAutoLoadSettingsValues)
        cmds.setParent(self.uiVars['autoLoadSettingsWindowColumn'])

        cmds.text(label='')

        # Create button to close window
        cmds.rowLayout(numberOfColumns=1, columnAttach=([1, 'left', 120]))
        cmds.button(label='Close', width=120, command=partial(self.closeWindow, self.uiVars['autoLoadSettingsUIwindow']))
        cmds.setParent(self.uiVars['autoLoadSettingsWindowColumn'])
        cmds.text(label='')

        # Show the window
        cmds.showWindow(self.uiVars['autoLoadSettingsUIwindow'])


    def selectDirectoryForLoadingCollections(self, *args):
        '''
        Called when the menu item under the "File" menu, "Select directory for loading saved collection(s)"
        is selected. This loads module collection(s) from a directory on the disk.
        '''
        # Get the previous directory path which was used to load module collections
        ui_preferences_file = open(self.ui_preferences_path, 'rb')
        ui_preferences = cPickle.load(ui_preferences_file)
        ui_preferences_file.close()
        startDir = ui_preferences['directoryForAutoLoadingCollections']

        # If the previous directory path doesn't exist, use the default "user_collections" path under MRT
        if not os.path.exists(startDir):
            startDir = ui_preferences['defaultDirectoryForAutoLoadingCollections']

        # Load the module collection files under the directory
        fileFilter = 'MRT Module Collection Files (*.mrtmc)'
        directoryPath = cmds.fileDialog2(caption='Select directory for loading module collections', okCaption='Select',
                                                fileFilter=fileFilter, startingDirectory=startDir, fileMode=2, dialogStyle=2)

        # If a valid directory path is selected, load collections from it
        if directoryPath:

            # Save the directory path as a preference
            ui_preferences['directoryForAutoLoadingCollections'] = directoryPath[0]

            # Get the preference to clear current module collection list
            value = ui_preferences['loadCollectionDirectoryClearModeStatus']
            mrtmc_files = []
            for file in os.listdir(directoryPath[0]):
                if fnmatch.fnmatch(file, '*mrtmc'):
                    mrtmc_files.append('%s/%s'%(directoryPath[0], file))
            self.loadModuleCollectionsForUI(mrtmc_files, value)

        # Save the directory preference
        ui_preferences_file = open(self.ui_preferences_path, 'wb')
        cPickle.dump(ui_preferences, ui_preferences_file, cPickle.HIGHEST_PROTOCOL)
        ui_preferences_file.close()


    def loadSavedModuleCollections(self, *args):
        '''
        Called when the menu item under the "File" menu, "Select and load saved module collection(s)"
        is selected. This loads selected module collection file(s) from the disk.
        '''
        # Get the last directory accessed for selecting module collection files(s)
        ui_preferences_file = open(self.ui_preferences_path, 'rb')
        ui_preferences = cPickle.load(ui_preferences_file)
        ui_preferences_file.close()
        startDir = ui_preferences['lastDirectoryForLoadingCollections']

        # If the previous directory path doesn't exist, use the default "user_collections" path under MRT
        if not os.path.exists(startDir):
            startDir = ui_preferences['defaultLastDirectoryForLoadingCollections']
        fileFilter = 'MRT Module Collection Files (*.mrtmc)'
        mrtmc_files = cmds.fileDialog2(caption='Select module collection files(s) for loading', okCaption='Load',
                                                fileFilter=fileFilter, startingDirectory=startDir, fileMode=4, dialogStyle=2)
        if not mrtmc_files:
            return

        # Load the selected module collection files, with the preference to clear the current module collection list
        value = ui_preferences['loadCollectionClearModeStatus']
        self.loadModuleCollectionsForUI(mrtmc_files, value)

        # Save the current directory used to access module collection files(s)
        directory = mrtmc_files[0].rpartition('/')[0]
        ui_preferences['lastDirectoryForLoadingCollections'] = directory
        ui_preferences_file = open(self.ui_preferences_path, 'wb')
        cPickle.dump(ui_preferences, ui_preferences_file, cPickle.HIGHEST_PROTOCOL)
        ui_preferences_file.close()


    def changeLoadCollectionListClearMode(self, *args):
        '''
        This function is called when a user selects the option box for "Select and load saved module collection(s)"
        from the "File" menu. It sets the preference, "Clear current collection list before loading" for
        module collections(s).
        '''
        def loadCollectionsFromSettingsWindow(*args):
            # Called to load module collection(s) into the UI
            try:
                cmds.deleteUI('mrt_loadCollectionClearMode_setting_UI_window')
            except:
                pass
            self.loadSavedModuleCollections()

        def setLoadCollectionClearModeValue(*args):
            # Saves the current preference set for clearing the current module collection(s) before loading.
            value = cmds.checkBox(self.uiVars['loadCollectionClearMode_checkBox'], query=True, value=True)
            ui_preferences_file = open(self.ui_preferences_path, 'rb')
            ui_preferences = cPickle.load(ui_preferences_file)
            ui_preferences_file.close()
            ui_preferences['loadCollectionClearModeStatus'] = value
            ui_preferences_file = open(self.ui_preferences_path, 'wb')
            cPickle.dump(ui_preferences, ui_preferences_file, cPickle.HIGHEST_PROTOCOL)
            ui_preferences_file.close()

        # Close the preferences window if open
        try:
            cmds.deleteUI('mrt_loadCollectionClearMode_setting_UI_window')
        except:
            pass

        # Create the preferences window
        self.uiVars['loadCollectionClearModeWindow'] = cmds.window('mrt_loadCollectionClearMode_setting_UI_window',
                                                                    title='Load module collections selectively',
                                                                    height=50, maximizeButton=False, sizeable=False)
        try:
            cmds.windowPref('mrt_loadCollectionClearMode_setting_UI_window', remove=True)
        except:
            pass

        # Main window column
        self.uiVars['loadCollectionClearModeWindowColumn'] = cmds.columnLayout(adjustableColumn=True)

        cmds.text(label='')

        cmds.frameLayout(visible=True, borderVisible=False, collapsable=False, labelVisible=False, height=40, width=330,
                                                                                             marginWidth=5, marginHeight=5)

        cmds.rowLayout(numberOfColumns=1, columnAttach=([1, 'left', 55]), rowAttach=([1, 'top', 0]))

        # Get the default preferences
        ui_preferences_file = open(self.ui_preferences_path, 'rb')
        ui_preferences = cPickle.load(ui_preferences_file)
        ui_preferences_file.close()
        value = ui_preferences['loadCollectionClearModeStatus']

        # Create the checkbox for setting the preference for clearing current module collection list before loading
        # new module collection(s) to the list.
        self.uiVars['loadCollectionClearMode_checkBox'] = \
            cmds.checkBox(label='Clear current collection list before loading', value=value,
                                                                            changeCommand=setLoadCollectionClearModeValue)
        cmds.setParent(self.uiVars['loadCollectionClearModeWindowColumn'])
        cmds.rowLayout(numberOfColumns=2, columnAttach=([1, 'left', 38], [2, 'left', 30]))
        cmds.button(label='Load collection(s)', width=130, command=loadCollectionsFromSettingsWindow)

        # Create button to close window
        cmds.button(label='Close', width=90, command=partial(self.closeWindow, self.uiVars['loadCollectionClearModeWindow']))
        cmds.setParent(self.uiVars['loadCollectionClearModeWindowColumn'])

        cmds.text(label='')

        # Show the window
        cmds.showWindow(self.uiVars['loadCollectionClearModeWindow'])


    def changeLoadCollectionDirectoryClearMode(self, *args):
        '''
        This function is called when a user selects the option box for "Select directory for loading saved collection(s)"
        from the "File" menu. It sets the preference, "Clear current collection list before loading" for
        module collections(s).
        '''
        def loadCollectionsFromSettingsWindow(*args):
            # Called to load module collection(s) from a directory
            try:
                cmds.deleteUI('mrt_loadCollectionDirectoryClearMode_setting_UI_window')
            except:
                pass
            self.selectDirectoryForLoadingCollections()

        def setLoadCollectionDirectoryClearModeValue(*args):
            # Saves the current preference set for clearing the current module collection(s) before loading
            # module collections(s) from a directory.
            value = cmds.checkBox(self.uiVars['loadCollectionDirectoryClearMode_checkBox'], query=True, value=True)
            ui_preferences_file = open(self.ui_preferences_path, 'rb')
            ui_preferences = cPickle.load(ui_preferences_file)
            ui_preferences['loadCollectionDirectoryClearModeStatus'] = value
            ui_preferences_file.close()
            ui_preferences_file = open(self.ui_preferences_path, 'wb')
            cPickle.dump(ui_preferences, ui_preferences_file, cPickle.HIGHEST_PROTOCOL)
            ui_preferences_file.close()

        # Close the preferences window if open
        try:
            cmds.deleteUI('mrt_loadCollectionDirectoryClearMode_setting_UI_window')
        except:
            pass

        # Create the preferences window
        self.uiVars['loadCollectionDirectoryClearModeWindow'] = \
            cmds.window('mrt_loadCollectionDirectoryClearMode_setting_UI_window', \
                         title='Load module collections from directory', height=50, maximizeButton=False, sizeable=False)
        try:
            cmds.windowPref('mrt_loadCollectionDirectoryClearMode_setting_UI_window', remove=True)
        except:
            pass

        # Main window column
        self.uiVars['loadCollectionDirectoryClearModeWindowColumn'] = cmds.columnLayout(adjustableColumn=True)

        cmds.text(label='')

        cmds.frameLayout(visible=True, borderVisible=False, collapsable=False, labelVisible=False, height=40, width=350,
                                                                                            marginWidth=5, marginHeight=5)

        cmds.rowLayout(numberOfColumns=1, columnAttach=([1, 'left', 62]), rowAttach=([1, 'top', 0]))

        # Get the default preferences
        ui_preferences_file = open(self.ui_preferences_path, 'rb')
        ui_preferences = cPickle.load(ui_preferences_file)
        value = ui_preferences['loadCollectionDirectoryClearModeStatus']
        ui_preferences_file.close()

        # Create the checkbox for setting the preference for clearing current module collection list before loading
        # new module collection(s) from a directory to the list.
        self.uiVars['loadCollectionDirectoryClearMode_checkBox'] = \
            cmds.checkBox(label='Clear current collection list before loading', value=value, \
                                                                    changeCommand=setLoadCollectionDirectoryClearModeValue)

        cmds.setParent(self.uiVars['loadCollectionDirectoryClearModeWindowColumn'])
        cmds.rowLayout(numberOfColumns=2, columnAttach=([1, 'left', 22], [2, 'left', 14]))
        cmds.button(label='Load collection(s) from directory', width=200, command=loadCollectionsFromSettingsWindow)

        # Create button to close window
        cmds.button(label='Close', width=90, command=partial(self.closeWindow, \
                                                                self.uiVars['loadCollectionDirectoryClearModeWindow']))
        cmds.setParent(self.uiVars['loadCollectionDirectoryClearModeWindowColumn'])
        cmds.text(label='')

        # Show the window
        cmds.showWindow(self.uiVars['loadCollectionDirectoryClearModeWindow'])


    def loadSavedCharTemplates(self, *args):
        '''
        Performs selective loading of character template files on disk into the MRT UI.
        '''
        # Get the previous directory accessed, saved as a preference
        ui_preferences_file = open(self.ui_preferences_path, 'rb')
        ui_preferences = cPickle.load(ui_preferences_file)
        ui_preferences_file.close()
        startDir = ui_preferences['directoryForCharacterTemplates']

        # If the saved directory doesn't exist on the disk, use the default directory under MRT/character_templates
        if not os.path.exists(startDir):
            startDir = ui_preferences['defaultDirectoryForCharacterTemplates']

        # Get the selected character template files from the user
        fileFilter = 'MRT Character Template Files (*.mrtct)'
        mrtct_files = cmds.fileDialog2(caption='Load character template(s)', fileFilter=fileFilter, okCaption='Load',
                                                                      startingDirectory=startDir, fileMode=4, dialogStyle=2)
        if mrtct_files == None:
            return

        # Get the preference if the currently loaded character template files in the UI needs to be cleared.
        clearStatus = ui_preferences['loadCharTemplateClearModeStatus']

        # Load the new character template files into the UI
        self.loadCharTemplatesForUI(mrtct_files, clearStatus)

        # Get the directory used for selecting character template files, save it as a preference
        ui_preferences['directoryForCharacterTemplates'] = mrtct_files[0].rpartition('/')[0]
        ui_preferences_file = open(self.ui_preferences_path, 'wb')
        cPickle.dump(ui_preferences, ui_preferences_file, cPickle.HIGHEST_PROTOCOL)
        ui_preferences_file.close()


    def changeLoadSettingsForCharTemplates(self, *args):
        '''
        Modifies the load settings for character templates into MRT UI.
        '''
        def setCharTemplateLoadSettingsValues(*args):
            # Load the preferences
            ui_preferences_file = open(self.ui_preferences_path, 'rb')
            ui_preferences = cPickle.load(ui_preferences_file)
            ui_preferences_file.close()

            # Get the current preferences
            clearListStatus = cmds.checkBox(self.uiVars['clearCharTemplateListOnLoad_checkBox'], query=True, value=True)
            loadPreviousListAtStartup = cmds.checkBox(self.uiVars['charTemplateLoadAtStartup_checkBox'], query=True,
                                                                                                            value=True)
            loadNewTemplatesToList = cmds.checkBox(self.uiVars['newCharTemplateLoadToList_checkBox'], query=True,
                                                                                                            value=True)
            # Set the current preference for clearing the current template list
            ui_preferences['loadCharTemplateClearModeStatus'] = clearListStatus
            # Set the current preference for loading the current template list at next MRT startup
            ui_preferences['autoLoadPreviousCharTemplateListAtStartupStatus'] = loadPreviousListAtStartup
            # Set the current preference for loading new templates to list
            ui_preferences['loadNewCharTemplatesToCurrentList'] = loadNewTemplatesToList

            # Save these preferences
            ui_preferences_file = open(self.ui_preferences_path, 'wb')
            cPickle.dump(ui_preferences, ui_preferences_file, cPickle.HIGHEST_PROTOCOL)
            ui_preferences_file.close()

        def loadTemplatesFromSettingsWindow(*args):
            # Load the templates
            try:
                cmds.deleteUI('mrt_charTemplateLoadSettingsUI_window')
            except:
                pass
            self.loadSavedCharTemplates()

        # Close the preferences window
        try:
            cmds.deleteUI('mrt_charTemplateLoadSettingsUI_window')
        except:
            pass

        # Create the preference window
        self.uiVars['charTemplateLoadSettingsUIwindow'] = cmds.window('mrt_charTemplateLoadSettingsUI_window',
                         title='Settings for loading character templates(s)', width=90, maximizeButton=False, sizeable=False)
        try:
            cmds.windowPref('mrt_charTemplateLoadSettingsUI_window', remove=True)
        except:
            pass

        # Main column
        self.uiVars['charTemplateLoadSettingsWindowColumn'] = cmds.columnLayout(adjustableColumn=True)

        cmds.text(label='')

        # Get the saved preferences
        ui_preferences_file = open(self.ui_preferences_path, 'rb')
        ui_preferences = cPickle.load(ui_preferences_file)
        ui_preferences_file.close()

        # Preference to clear current template list for loading new character templates
        clearListStatus = ui_preferences['loadCharTemplateClearModeStatus']

        # Load current character template list at next MRT startup
        loadPreviousListAtStartup = ui_preferences['autoLoadPreviousCharTemplateListAtStartupStatus']

        # Add new character templates to the current list
        loadNewTemplatesToList = ui_preferences['loadNewCharTemplatesToCurrentList']

        # Create a layout and buttons to set the preferences
        cmds.rowLayout(numberOfColumns=1, columnAttach=([1, 'left', 57]))
        self.uiVars['charTemplateLoadAtStartup_checkBox'] = \
            cmds.checkBox(label='Preserve and load current list at next startup', value=loadPreviousListAtStartup,
                                                                    changeCommand=setCharTemplateLoadSettingsValues)
        cmds.setParent(self.uiVars['charTemplateLoadSettingsWindowColumn'])

        cmds.rowLayout(numberOfColumns=1, columnAttach=([1, 'both', 60]), rowAttach=([1, 'top', 5]))
        self.uiVars['newCharTemplateLoadToList_checkBox'] = \
            cmds.checkBox(label='Load new saved templates(s) to current list', value=loadNewTemplatesToList,
                                                                    changeCommand=setCharTemplateLoadSettingsValues)
        cmds.setParent(self.uiVars['charTemplateLoadSettingsWindowColumn'])

        cmds.rowLayout(numberOfColumns=1, columnAttach=([1, 'left', 65]), rowAttach=([1, 'top', 5]))
        self.uiVars['clearCharTemplateListOnLoad_checkBox'] = \
            cmds.checkBox(label='Clear current template list before loading', value=clearListStatus,
                                                                    changeCommand=setCharTemplateLoadSettingsValues)
        cmds.setParent(self.uiVars['charTemplateLoadSettingsWindowColumn'])


        cmds.text(label='')

        # Load Templates
        cmds.rowLayout(numberOfColumns=2, columnAttach=([1, 'left', 58], [2, 'left', 30]))
        cmds.button(label='Load templates(s)', width=130, command=loadTemplatesFromSettingsWindow)
        cmds.button(label='Close', width=90, command=partial(self.closeWindow,
                                                  self.uiVars['charTemplateLoadSettingsUIwindow']))
        # Set to the main columns
        cmds.setParent(self.uiVars['charTemplateLoadSettingsWindowColumn'])
        cmds.text(label='')
        cmds.showWindow(self.uiVars['charTemplateLoadSettingsUIwindow'])


    def closeWindow(self, windowName, *args):
        '''
        I know, but this way it's just a one word callback.
        '''
        cmds.deleteUI(windowName)


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


    def putShelfButtonForUI(self, *args):
        '''
        Puts a shelf button for MRT on the current maya shelf
        '''
        # Get the current tab under maya shelf
        currentTab = cmds.tabLayout('ShelfLayout', query=True, selectTab=True)

        # Get its shelf buttons
        shelfTabButtons = cmds.shelfLayout(currentTab, query=True, childArray=True)

        # Check if the MRT button exists, return if true.
        if shelfTabButtons:
            for button in shelfTabButtons:
                annotation = cmds.shelfButton(button, query=True, annotation=True)
                if annotation == 'Modular Rigging Tools':
                    return

        # Else, put the shelf button on the current shelf tab
        imagePath = cmds.internalVar(userScriptDir=True)+'MRT/mrt_shelfLogo.png'
        cmds.shelfButton(annotation='Modular Rigging Tools', commandRepeatable=True,
                         image1=imagePath, parent=currentTab, sourceType='mel', command='MRT')


    def swapHingeNodeRootEndHandlePos(self, *args):
        '''
        Used to swap the positions of the start and end handles for a hinge module. This
        can be used to quickly reverse the hierarchy of the node chain for the module.
        '''
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
                    cmds.evalDeferred(partial(cmds.select, item), lowestPriority=True)
            else:
                sys.stderr.write('Please select a hinge node module.\n')
                return


    def deleteSelectedProxyGeo(self, *args):
        '''
        Deletes selected module proxy geometry, if it's valid. This doesn't delete
        all proxy geometry, only the ones that are selected. A module may have multiple
        proxy geo transfroms.
        '''
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
        '''
        Deletes all proxy geometry for selected module(s).
        '''
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
        '''
        Deletes construction history on all module proxy geometry in the scene. The
        history may be a result of a user modification of module proxy geometry.
        '''
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


    def purgeAutoCollections(self, *args):
        '''
        Removes all auto module collection files auto generated by MRT. An auto collection file
        is used by MRT to revert a character back to scene modules.
        '''
        # Get all files
        autoCollectionFiles = filter(lambda fileName:re.match('^character__[0-9]*\.mrtmc$', fileName),
                                                                os.listdir(self.autoCollections_path))
        # Remove them.
        if len(autoCollectionFiles):
            for item in autoCollectionFiles:
                itemPath = self.autoCollections_path + '/' + item
                os.remove(itemPath)
            sys.stderr.write('%s file(s) were removed.\n'%(len(autoCollectionFiles)))
        else:
            sys.stderr.write('No auto-collection file(s) found.\n')


    def openWebPage(self, urlString, *args):
        '''
        Just like it says.
        '''
        webbrowser.open(urlString)


    def display_mrt_issues(self, *args):
        '''
        First things first. Keep a record of current issues with MRT, displayable to the user.
        Not sure why I didn't use a txt source :)
        '''
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
        '''
        Display MRT dev stats
        '''
        printString1 = '\n\t\t\tModular Rigging Tools v1.0\n\t\t\tfor Maya 2011 - 2013'
        printString2 = '\n\n\tWritten by Himanish Bhattacharya' \
            '\n\thimanish@animformed.net' \
            '\n\n\t________________________________________________' \
            '\n\n\tFor annoyances or bugs, contact me at, bugs@animformed.net\n'
        try:
            cmds.deleteUI('mrt_about_UI_window')
        except:
            # It's time they put an end to this.
            pass
        self.uiVars['displayMrtAboutWindow'] = cmds.window('mrt_about_UI_window', title='About', maximizeButton=False, \
                                                                                                            sizeable=False)
        try:
            cmds.windowPref(self.uiVars['displayMrtAboutWindow'], remove=True)
        except:
            # I agrreee.
            pass

        self.uiVars['displayMrtAbout_columnLayout'] = cmds.columnLayout()
        cmds.text(label=printString1, font='boldLabelFont')
        cmds.text(label=printString2)
        cmds.showWindow(self.uiVars['displayMrtAboutWindow'])


    # -------------------------------------------------------------------------------------------------------------
    #
    #   UI INITIALIZATION METHODS
    #
    # -------------------------------------------------------------------------------------------------------------

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

        self.uiVars['sceneModuleList_treeView'] = cmds.treeView('__MRT_treeView_SceneModulesUI', numberOfButtons=1,
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

    '''


    # -------------------------------------------------------------------------------------------------------------
    #
    #   UI UTILITY METHODS
    #
    # -------------------------------------------------------------------------------------------------------------

    def createUIutilityScriptJobs(self):
        '''
        Run helper scriptJobs for MRT UI events.
        '''
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


    def toggleEditMenuButtonsOnModuleSelection(self):
        '''
        Set UI states for controls with buttons for performing module edits (under Edit tab), based on
        valid scene module selection. Used by a scriptJob under "createUIutilityScriptJobs".
        '''
        # Get selection, and get the selection module namespace, if valid.
        selection = mel.eval("ls -sl -type dagNode")
        if selection:
            lastSelection = selection[-1]
            namespaceInfo = mfunc.stripMRTNamespace(lastSelection)

            # If valid scene module.
            if namespaceInfo != None:

                cmds.button(self.uiVars['moduleSaveColl_button'], edit=True, enable=True)
                cmds.rowLayout(self.uiVars['moduleSaveCollOptions_row1'], edit=True, enable=True)
                cmds.rowLayout(self.uiVars['moduleSaveCollOptions_row2'], edit=True, enable=True)
                cmds.button(self.uiVars['moduleRename_button'], edit=True, enable=True)
                cmds.button(self.uiVars['moduleDelete_button'], edit=True, enable=True)
                cmds.button(self.uiVars['moduleDuplicate_button'], edit=True, enable=True)
                text = namespaceInfo[0].rpartition('__')[2]
                cmds.textField(self.uiVars['moduleRename_textField'], edit=True, text=text)

                return

        cmds.button(self.uiVars['moduleSaveColl_button'], edit=True, enable=False)
        cmds.rowLayout(self.uiVars['moduleSaveCollOptions_row1'], edit=True, enable=False)
        cmds.rowLayout(self.uiVars['moduleSaveCollOptions_row2'], edit=True, enable=False)
        cmds.button(self.uiVars['moduleRename_button'], edit=True, enable=False)
        cmds.button(self.uiVars['moduleDelete_button'], edit=True, enable=False)
        cmds.button(self.uiVars['moduleDuplicate_button'], edit=True, enable=False)
        cmds.textField(self.uiVars['moduleRename_textField'], edit=True, text=None)


    def checkMRTcharacter(self):
        '''
        Checks for a character in the current scene. If found, it returns the name
        of main character group and the auto module collection file generated while creating the character.
        '''
        # Get the cuurent namespace, set to root.
        namespace = cmds.namespaceInfo(currentNamespace=True)
        cmds.namespace(setNamespace=':')

        # Look for character main groups. Normally, there should only be one.
        transforms = cmds.ls(type='transform')
        characterGrp = []
        for transform in transforms:
            if re.match('MRT_character[a-zA-Z0-9]*__mainGrp', transform):
                characterGrp.append(transform)

        # If found more than one character main group.
        if len(characterGrp) > 1:
            cmds.warning('MRT Error: More than one character exists in the scene. Aborting.')
            return

        # If a character group is found in the scene.
        if len(characterGrp) == 1:
            characterGrp = characterGrp[0]

        # If no character main group is found in the scene.
        if len(characterGrp) == 0:
            characterGrp = None

        autoCollectionFile = ''

        if characterGrp:

            # Get the stored auto-module collection file id
            fileId = cmds.getAttr(characterGrp+'.collectionFileID')

            # Look for the target auto module collection file under "MRT/module_collections/auto-generated_character_collections"
            collectionFile = 'character__%s' % (fileId)
            autoCollectionFiles = [item for item in os.listdir(self.autoCollections_path) if re.match('^.*mrtmc$', item)]
            if len(autoCollectionFiles):
                for item in autoCollectionFiles:
                    if item.partition('.')[0] == collectionFile:
                        autoCollectionFile = collectionFile
                        break

        # Reset namespace.
        cmds.namespace(setNamespace=namespace)

        return characterGrp, autoCollectionFile


    # -------------------------------------------------------------------------------------------------------------
    #
    #   "CREATE" TAB ITEM METHODS
    #
    # -------------------------------------------------------------------------------------------------------------

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


    def toggleElbowProxyTypeRadio(self, *args):
        '''
        Called to change the UI option for proxy elbow type for module proxy geometry creation.
        '''
        stat = cmds.checkBox(self.uiVars['proxyGeoElbow_check'], query=True, value=True)
        if stat:
            cmds.rowLayout(self.uiVars['proxyElbowType_row'], edit=True, enable=True)
        else:
            cmds.rowLayout(self.uiVars['proxyElbowType_row'], edit=True, enable=False)


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


    # -------------------------------------------------------------------------------------------------------------
    #
    #   "EDIT" TAB ITEM METHODS
    #
    # -------------------------------------------------------------------------------------------------------------

    # ............................................. MODULE COLLECTIONS ............................................

    def loadModuleCollectionsForUI(self, moduleCollectionFileList, clearCurrentList=False):
        '''
        Loads the passed-in module collection list into the MRT UI. It also clears the current module
        collection list if needed.
        '''
        # Remove all contents of the module collection scroll list.
        cmds.textScrollList(self.uiVars['moduleCollection_txScList'], edit=True, height=32, removeAll=True)

        # Clear old module collection list record, conditionally.
        if clearCurrentList:
            self.module_collectionList = {}

        # If module collection list is passed-in, re-build the module collection scroll list.
        if len(moduleCollectionFileList):
            for collection in moduleCollectionFileList:

                # Get the collection name suitable for the list from the collection file name.
                collectionName = re.split(r'\/|\\', collection)[-1].rpartition('.')[0]

                # Skip if a collection file exists.
                if collection in self.module_collectionList.values():
                    continue

                # If the collection name exist in the list, add a numerical suffix to it
                # Example:
                # collectionName
                # collectionName (2)
                if collectionName in self.module_collectionList:
                    suffix = mfunc.findHighestCommonTextScrollListNameSuffix(collectionName, self.module_collectionList.keys())
                    suffix = suffix + 1
                    collectionName = '%s (%s)'%(collectionName, suffix)

                # Save the collection name as a key with its collection file as value
                self.module_collectionList[collectionName] = collection

            # Get the height for the module collection scroll list
            scrollHeight = len(self.module_collectionList) * 20
            if scrollHeight > 200:
                scrollHeight = 200
            if scrollHeight == 20:
                scrollHeight = 40

            # Add the module collection names to the module collection scroll list
            for collectionName in sorted(self.module_collectionList):
                cmds.textScrollList(self.uiVars['moduleCollection_txScList'], edit=True, enable=True,
                                                    height=scrollHeight, append=collectionName, font='plainLabelFont',
                                                                                selectCommand=self.printCollectionInfoForUI)
            # Select the first item
            cmds.textScrollList(self.uiVars['moduleCollection_txScList'], edit=True, selectIndexedItem=1)
            self.printCollectionInfoForUI()

        # If module collection list is valid, save it, and enable UI buttons for installing, editing,
        # and deletion of module collection(s) from the UI scroll list.
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
            # Enable buttons
            cmds.button(self.uiVars['loadedCollections_button_install'], edit=True, enable=True)
            cmds.button(self.uiVars['loadedCollections_button_edit'], edit=True, enable=True)
            cmds.button(self.uiVars['loadedCollections_button_delete'], edit=True, enable=True)

        # If no module collection is to be loaded
        if not len(self.module_collectionList):

            # Clear the saved module collection data
            module_collectionList_file = open(self.module_collectionList_path, 'wb')
            cPickle.dump({}, module_collectionList_file, cPickle.HIGHEST_PROTOCOL)
            module_collectionList_file.close()

            # Clear the module collection scroll list
            cmds.textScrollList(self.uiVars['moduleCollection_txScList'], edit=True, enable=False, height=32,
                                                    append=['              < no module collection(s) loaded >'],
                                                                                                font='boldLabelFont')
            # Clear module collection info field
            cmds.scrollField(self.uiVars['collectionDescrp_scrollField'], edit=True, text='< no collection info >',
                                                                           font='obliqueLabelFont', editable=False,
                                                                                                        height=32)
            # Disable buttons for installing, editing and deletion of module collection(s)
            cmds.button(self.uiVars['loadedCollections_button_install'], edit=True, enable=False)
            cmds.button(self.uiVars['loadedCollections_button_edit'], edit=True, enable=False)
            cmds.button(self.uiVars['loadedCollections_button_delete'], edit=True, enable=False)


    def printCollectionInfoForUI(self):
        '''
        Prints the module collection info for a selected item in the module collection scroll list
        in the module collection description field in the UI.
        '''
        # Get the current selected module collection name
        selectedItem = cmds.textScrollList(self.uiVars['moduleCollection_txScList'], query=True, selectItem=True)[0]

        # Get its module collection file
        collectionFile = self.module_collectionList[selectedItem]

        # Get the module collection description from the module collection file
        if os.path.exists(collectionFile):
            # Get the module collection data
            collectionFileObj_file = open(collectionFile, 'rb')
            collectionFileObj = cPickle.load(collectionFileObj_file)
            collectionFileObj_file.close()
            collectionDescrp = collectionFileObj['collectionDescrp']    # Module collection description

            # If description is valid, print it in the module collection description field
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

                # Print it
                cmds.scrollField(self.uiVars['collectionDescrp_scrollField'], edit=True, text=collectionDescrp,
                                                                          font='smallPlainLabelFont', height=infoScrollheight)
            else:
                # Invalid module collection description
                cmds.scrollField(self.uiVars['collectionDescrp_scrollField'], edit=True,
                                      text='< no valid collection info >', font='obliqueLabelFont', editable=False, height=32)
            return True

        else:
            # If the module collection file for the selected module collection name is not found, remove it from
            # the module collection scroll list
            cmds.warning('MRT Error: Module collection error. \
                                    The selected module collection file, "%s" cannot be found on disk.' % (collectionFile))

            # Remove it from module collection scroll list
            cmds.textScrollList(self.uiVars['moduleCollection_txScList'], edit=True, removeItem=selectedItem)

            # Remove it from module collection records
            self.module_collectionList.pop(selectedItem)

            # Remove it from saved module collection list data
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

            # Reset the module collection description field
            cmds.scrollField(self.uiVars['collectionDescrp_scrollField'], edit=True, text='< no collection info >',
                                                                        font='obliqueLabelFont', editable=False, height=32)

            # Check and update the module collection list, if it contains any item(s) after removal
            allItems = cmds.textScrollList(self.uiVars['moduleCollection_txScList'], query=True, allItems=True)
            if not allItems:
                cmds.textScrollList(self.uiVars['moduleCollection_txScList'], edit=True, enable=False, height=32,
                                                            append=['              < no module collection(s) loaded >'],
                                                                                                    font='boldLabelFont')
            # Disable buttons for installing, editing and deletion of module collection(s)
            cmds.button(self.uiVars['loadedCollections_button_install'], edit=True, enable=False)
            cmds.button(self.uiVars['loadedCollections_button_edit'], edit=True, enable=False)
            cmds.button(self.uiVars['loadedCollections_button_delete'], edit=True, enable=False)

            return False


    def deleteSelectedModuleCollection(self, *args):
        '''
        Deletes a selected module collection from the module collection list in the MRT UI.
        '''
        def deleteModuleCollection(deleteFromDisk=False, *args):
            # This definition will be used only within the scope of deleteSelectedModuleCollection

            # If the module collection is to be deleted, close the window
            cmds.deleteUI('mrt_deleteCollection_UI_window')

            # Remove the module collection name from the UI scroll list
            selectedItem = cmds.textScrollList(self.uiVars['moduleCollection_txScList'], query=True, selectItem=True)[0]
            cmds.textScrollList(self.uiVars['moduleCollection_txScList'], edit=True, removeItem=selectedItem)

            # Get its collection file
            collectionFile = self.module_collectionList[selectedItem]

            # Remove it from module collection records
            self.module_collectionList.pop(selectedItem)

            # Remove it from saved module collection list data, save the new list
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

            # Remove the module collection from disk if specified
            if deleteFromDisk:
                os.remove(collectionFile)

            # After removing the module collection name from the UI, check for item(s) in the module
            # collection scroll list
            allItems = cmds.textScrollList(self.uiVars['moduleCollection_txScList'], query=True, allItems=True) or []

            # If item(s) are found, re-build the scroll list
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
                # If no item is found, reset and disable the module collection scroll list with its buttons
                cmds.textScrollList(self.uiVars['moduleCollection_txScList'], edit=True, enable=False, height=32,
                                                        append=['              < no module collection(s) loaded >'],
                                                                                                font='boldLabelFont')

                cmds.scrollField(self.uiVars['collectionDescrp_scrollField'], edit=True, text='< no collection info >',
                                                                                font='obliqueLabelFont', editable=False,
                                                                                                                height=32)
                cmds.button(self.uiVars['loadedCollections_button_install'], edit=True, enable=False)
                cmds.button(self.uiVars['loadedCollections_button_edit'], edit=True, enable=False)
                cmds.button(self.uiVars['loadedCollections_button_delete'], edit=True, enable=False)

        # Check if the selected module collection is valid, meaning if it exists on disk.
        validItem = self.printCollectionInfoForUI()
        if not validItem:
            return

        # Delete the remove module collection window, if it exists.
        try:
            cmds.deleteUI('mrt_deleteCollection_UI_window')
        except:
            pass

        # Create the delete module collection window.
        self.uiVars['deleteCollectionWindow'] = cmds.window('mrt_deleteCollection_UI_window',
                                                                    title='Delete module collection',
                                                                            maximizeButton=False, sizeable=False)
        try:
            cmds.windowPref('mrt_deleteCollection_UI_window', remove=True)
        except:
            pass

        # Create the main layout
        cmds.frameLayout(visible=True, borderVisible=False, collapsable=False, labelVisible=False, height=90,
                                                                            width=220, marginWidth=20, marginHeight=15)

        # Create two buttons under a row, to delete the selected module collection from disk or to
        # remove the module collection frpm the UI scroll list only.
        cmds.rowLayout(numberOfColumns=2, columnAttach=([1, 'left', 0], [2, 'left', 20]))
        cmds.button(label='From disk', width=90, command=partial(deleteModuleCollection, True))
        cmds.button(label='Remove from list', width=120, command=deleteModuleCollection)
        cmds.showWindow(self.uiVars['deleteCollectionWindow'])


    def installSelectedModuleCollectionToScene(self, **kwargs):
        '''
        Performs installation of a selected module collection from the module collection scroll list
        into the maya scene. It also accepts an auto-collection file, which is auto generated by MRT
        while creating a character from scene modules (It's used by MRT to revert a character back
        to its scene modules).
        '''
        # If an auto-install module collection file is passed, use it.
        if 'autoInstallFile' in kwargs:
            collectionFile = kwargs['autoInstallFile']
        else:
            # Get the selected module collection name from the UI scroll list and its
            # associated file.
            validItem = self.printCollectionInfoForUI()
            if not validItem:
                return
            selectedItem = cmds.textScrollList(self.uiVars['moduleCollection_txScList'], query=True, selectItem=True)[0]
            collectionFile = self.module_collectionList[selectedItem]

        # Create and set a temporary namespace to work with module installations from collection file.
        currentNamespace = cmds.namespaceInfo(currentNamespace=True)    # Save current namespace
        cmds.namespace(setNamespace=':')
        cmds.namespace(addNamespace='MRT_tempNamespaceForImport')
        cmds.namespace(setNamespace='MRT_tempNamespaceForImport')

        # Read the module collection file data.
        mrtmc_fObject_file = open(collectionFile, 'rb')
        mrtmc_fObject = cPickle.load(mrtmc_fObject_file)
        mrtmc_fObject_file.close()

        # Write a temporary maya scene file which will be used to import scene modules.
        tempFilePath = collectionFile.rpartition('.mrtmc')[0]+'_temp.ma'
        tempFile_fObject = open(tempFilePath, 'w')

        # Write content to the maya scene file with the data from the module collection file.
        for i in range(1, len(mrtmc_fObject)):
            tempFile_fObject.write(mrtmc_fObject['collectionData_line_'+str(i)])
        tempFile_fObject.close()

        # Remove reference to the module collection file object (for garbage collection)
        del mrtmc_fObject

        # Import the scene module from the temporary maya scene file
        cmds.file(tempFilePath, i=True, type="mayaAscii", prompt=False, ignoreVersion=True)
        os.remove(tempFilePath) # Delete the maya scene file after import

        # Get the MRT module names in the current temporary namespace.
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

            # Get the user specified names of the modules in the temporary namespace.
            userSpecNamesInTemp = mfunc.returnModuleUserSpecNames(namespacesInTemp)
            cmds.namespace(setNamespace='MRT_tempNamespaceForImport')
            allUserSpecNames = set(userSpecNamesInTemp[1] + userSpecNamesForSceneModules)

            # If there're existing modules in the scene, check and rename module(s) in the temporary namespace
            # to resolve name conflicts.
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

                    # Rename the module with the temporary namespace, and remove the old namespace.
                    cmds.namespace(moveNamespace=[':MRT_tempNamespaceForImport:'+namespace,
                                                                            ':MRT_tempNamespaceForImport:'+newNamespace])
                    cmds.namespace(removeNamespace=namespace)
                    allUserSpecNames.add(newUserSpecName)

                    # If its mirror module exists, rename it as well.
                    if cmds.attributeQuery('mirrorModuleNamespace',
                                            node=':MRT_tempNamespaceForImport:'+newNamespace+':moduleGrp', exists=True):

                        mirrorModuleNamespace = \
                            cmds.getAttr(':MRT_tempNamespaceForImport:'+newNamespace+':moduleGrp.mirrorModuleNamespace')

                        cmds.lockNode(':MRT_tempNamespaceForImport:'+mirrorModuleNamespace+':module_container',
                                                                                        lock=False, lockUnpublished=False)

                        cmds.setAttr(':MRT_tempNamespaceForImport:'+mirrorModuleNamespace+':moduleGrp.mirrorModuleNamespace',
                                                                                            newNamespace, type='string')
                        cmds.lockNode(':MRT_tempNamespaceForImport:'+mirrorModuleNamespace+':module_container', lock=True,
                                                                                                    lockUnpublished=True)
        # After renaming the new module for the current scene, move them from the
        # temporary namespace into the root namespace.
        cmds.namespace(setNamespace=':')
        cmds.namespace(moveNamespace=['MRT_tempNamespaceForImport', ':'], force=True)

        # Remove the temporary namespace
        cmds.namespace(removeNamespace='MRT_tempNamespaceForImport')

        # Set the saved namespace
        cmds.namespace(setNamespace=currentNamespace)

        # Update UI fields
        self.clearParentModuleField()
        self.clearChildModuleField()


    def editSelectedModuleCollectionDescriptionFromUI(self, *args):
        '''
        Edits the module collection description for a selected module collection from the
        UI module collection scroll list.
        '''
        def editDescriptionForSelectedModuleCollection(collectionDescription, *args):
            # Performs / updates the changes to the module collection description
            # from the UI field to the module collection file.

            # Close the edit module collection descrption window
            cancelEditCollectionNoDescpErrorWindow()

            # Get the current selected module collection name from UI scroll list
            selectedItem = cmds.textScrollList(self.uiVars['moduleCollection_txScList'], query=True, selectItem=True)[0]

            # Get the corresponding module collection file
            collectionFile = self.module_collectionList[selectedItem]

            # Get module collection data from the file
            collectionFileObj_file = open(collectionFile, 'rb')
            collectionFileObj = cPickle.load(collectionFileObj_file)
            collectionFileObj_file.close()

            # Update the module collection description for the data wnd write it
            collectionFileObj['collectionDescrp'] = collectionDescription
            collectionFileObj_file = open(collectionFile, 'wb')
            cPickle.dump(collectionFileObj, collectionFileObj_file, cPickle.HIGHEST_PROTOCOL)
            collectionFileObj_file.close()

            # Update the UI
            self.printCollectionInfoForUI()

        def cancelEditCollectionNoDescpErrorWindow(*args):
            # Closes the edit module collection description window
            cmds.deleteUI(self.uiVars['editCollectionDescpWindow'])
            try:
                cmds.deleteUI(self.uiVars['editCollectionNoDescpErrorWindow'])
            except:
                pass

        def checkEditDescriptionForSelectedModuleCollection(*args):
            # Checks the new module collection description for saving / updating
            # Get the description
            collectionDescription = cmds.scrollField(self.uiVars['editCollectionDescpWindowScrollField'],
                                                                                        query=True, text=True)
            if collectionDescription == '':
                # If no description is entered, create a warning window before proceeding
                self.uiVars['editCollectionNoDescpErrorWindow'] = \
                    cmds.window('mrt_editCollection_noDescpError_UI_window', title='Module collection warning',
                                                                                maximizeButton=False, sizeable=False)
                # Remove the window from UI preferences
                try:
                    cmds.windowPref('mrt_editCollection_noDescpError_UI_window', remove=True)
                except:
                    pass

                # Main layout
                cmds.frameLayout(visible=True, borderVisible=False, collapsable=False, labelVisible=False, height=90,
                                                                                width=220, marginWidth=20, marginHeight=15)

                # Give the user a choice to save the module collection description with
                # an empty value (Please don't be lazy like this haha)
                cmds.text(label='Are you sure you want to continue with an empty description?')
                cmds.rowLayout(numberOfColumns=2, columnAttach=([1, 'left', 55], [2, 'left', 20]),
                                                                        rowAttach=([1, 'top', 8], [2, 'top', 8]))
                cmds.button(label='Continue', width=90,
                                        command=partial(editDescriptionForSelectedModuleCollection, collectionDescription))
                cmds.button(label='Cancel', width=90, command=cancelEditCollectionNoDescpErrorWindow)

                # Show the window for warning
                cmds.showWindow(self.uiVars['editCollectionNoDescpErrorWindow'])
            else:
                # Proceed saving with the new module collection description
                editDescriptionForSelectedModuleCollection(collectionDescription)

        # Check if the selected module collection is valid.
        validItem = self.printCollectionInfoForUI()
        if not validItem:
            return

        # Close the edit module collection description window if open
        try:
            cmds.deleteUI('mrt_collectionDescription_edit_UI_window')
        except:
            pass

        # Create the module collection description window
        self.uiVars['editCollectionDescpWindow'] = cmds.window('mrt_collectionDescription_edit_UI_window', \
                                     title='Module collection description', height=150, maximizeButton=False, sizeable=False)

        # Remove the window from UI preference
        try:
            cmds.windowPref('mrt_collectionDescription_edit_UI_window', remove=True)
        except:
            pass

        # Main column
        self.uiVars['editCollectionDescpWindowColumn'] = cmds.columnLayout(adjustableColumn=True)

        # Create the layout for the module collection description field
        cmds.text(label='')
        cmds.text('Enter new description for module collection', align='center', font='boldLabelFont')

        cmds.frameLayout(visible=True, borderVisible=False, collapsable=False, labelVisible=False, height=75,
                                                                            width=320, marginWidth=5, marginHeight=10)
        # Get the current module collection description from its file
        selectedItem = cmds.textScrollList(self.uiVars['moduleCollection_txScList'], query=True, selectItem=True)[0]
        collectionFile = self.module_collectionList[selectedItem]
        collectionFileObj_file = open(collectionFile, 'rb')
        collectionFileObj = cPickle.load(collectionFileObj_file)
        currentDescriptionText = collectionFileObj['collectionDescrp']
        collectionFileObj_file.close()

        # Create the field for module collection description and set its value with the current description
        self.uiVars['editCollectionDescpWindowScrollField'] = cmds.scrollField(preventOverride=True, wordWrap=True,
                                                                                            text=currentDescriptionText)

        # Create the layout and its button for updating the module collection description from the field
        cmds.setParent(self.uiVars['editCollectionDescpWindowColumn'])
        cmds.rowLayout(numberOfColumns=2, columnAttach=([1, 'left', 34], [2, 'left', 26]))
        cmds.button(label='Save description', width=130, command=checkEditDescriptionForSelectedModuleCollection)
        cmds.button(label='Cancel', width=90, command=partial(self.closeWindow, self.uiVars['editCollectionDescpWindow']))

        # Set to the main UI column
        cmds.setParent(self.uiVars['editCollectionDescpWindowColumn'])
        cmds.text(label='')

        # Show the edit module collection description window
        cmds.showWindow(self.uiVars['editCollectionDescpWindow'])


    # ................................................ SCENE MODULES ...............................................

    def selectModuleInTreeViewUIfromViewport(self):
        '''
        Highlights an item in the scene module list in the MRT UI, if a valid module is selected
        in the maya viewport.
        '''
        cmds.undoInfo(stateWithoutFlush=False)

        # Update the treeView module selection record, remove any modules(s) that are not actively selected
        active_UI_selection = {}
        selection = mel.eval("ls -sl -type dagNode")
        if selection == None:
            self.treeViewSelection_list = {}
        else:
            for item in copy.copy(self.treeViewSelection_list):
                if not item in selection:
                    self.treeViewSelection_list.pop(item)

        # Filter selection for module(s) and add to record
        if selection != None:
            for select in selection:
                namespaceInfo = mfunc.stripMRTNamespace(select)
                if namespaceInfo != None:
                    moduleNamespace = namespaceInfo[0]
                    self.treeViewSelection_list[select] = moduleNamespace

        # Clear all highlight selection
        cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True, clearSelection=True)

        # Highlight selected module(s) in the scene module list treeView
        if len(self.treeViewSelection_list):
            for item in self.treeViewSelection_list:
                if item in selection:
                    active_UI_selection[item] = self.treeViewSelection_list[item]
            for item in active_UI_selection:
                cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True, selectItem=[active_UI_selection[item], 1])
        #else:
            # This clears the selection highlight(s)
            #self.updateListForSceneModulesInUI()
        cmds.undoInfo(stateWithoutFlush=True)


    def updateListForSceneModulesInUI_runIdle(self, *args):
        '''
        Delays the update for scene module list re-build at CPU idle time.
        (Useful for testing purposes, you may need it. I'm not calling this right now).
        '''
        cmds.evalDeferred(self.updateListForSceneModulesInUI, lowestPriority=True)


    def toggleSceneModuleListSortTypeFromUI(self, *args):
        '''
        Triggers sorting / updating for scene module list in the MRT UI, based on the preference
        set by user scene module(s) to sort by 'Hierarchy' or 'Alphabetically'.
        '''
        # Save the current selection, updating changes it.
        selection = cmds.ls(selection=True)

        # Update scene module list.
        self.updateListForSceneModulesInUI()

        # Re-select
        if selection:
            cmds.select(selection, replace=True)


    def resetListHeightForSceneModulesUI(self, *args):
        '''
        Resets the height of the scene module list treeView based on the number of modules.
        '''
        # Get the scene modules
        sceneNamespaces = cmds.namespaceInfo(listOnlyNamespaces=True)
        MRT_namespaces = mfunc.returnMRT_Namespaces(sceneNamespaces)

        # Set the height for the treeeView and its parent layout
        if MRT_namespaces != None:
            treeLayoutHeight = len(MRT_namespaces) * 22
            if treeLayoutHeight > 200:
                treeLayoutHeight = 200
            cmds.scrollLayout(self.uiVars['moduleList_Scroll'], edit=True, height=treeLayoutHeight+8)
            cmds.frameLayout(self.uiVars['moduleList_fLayout'], edit=True, height=treeLayoutHeight)


    def updateListForSceneModulesInUI(self, *args):
        '''
        Main procedure for performing all updates to the scene module list in the MRT UI.
        '''
        cmds.undoInfo(stateWithoutFlush=False)

        # Get the selection, if none, clear the record for module(s)
        selection = mel.eval("ls -sl -type dagNode")

        if selection == None:
            self.treeViewSelection_list = {}

        # Get the module(s) in the current scene
        currentNamespace = cmds.namespaceInfo(currentNamespace=True)
        cmds.namespace(setNamespace=':')
        sceneNamespaces = cmds.namespaceInfo(listOnlyNamespaces=True)
        MRT_namespaces = mfunc.returnMRT_Namespaces(sceneNamespaces)

        # Clear the scene module treeView list
        cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True, removeAll=True)

        # To collect the module name attributes per module (to be displayed in the module list)
        listNames = {}

        # If scene module(s) are found,
        if MRT_namespaces != None:

            # Enable treeView and its parent layout (disabled at MRT startup)
            cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True, enable=True)
            cmds.rowLayout(self.uiVars['sortModuleList_row'], edit=True, enable=True)

            # For every scene module
            for name in MRT_namespaces:

                # Get the user specified name
                userSpecifiedName = name.partition('__')[2]

                # Get the module type from its name
                moduleType = name.partition('__')[0].partition('_')[2].partition('Node')[0]

                # Get the mirrored module (if it's a mirrored module pair)
                if cmds.attributeQuery('mirrorModuleNamespace', node=name+':moduleGrp', exists=True):
                    mirrorModuleNamespace = cmds.getAttr(name+':moduleGrp.mirrorModuleNamespace')
                else:
                    mirrorModuleNamespace = None

                # Collect the module name attributes
                listNames[userSpecifiedName] = [name, moduleType, mirrorModuleNamespace]

            # Get the height for the scene module scroll list (with treeView)
            defTreeLayoutHeight = cmds.frameLayout(self.uiVars['moduleList_fLayout'], query=True, height=True)
            treeLayoutHeight = len(MRT_namespaces) * 22
            if defTreeLayoutHeight > treeLayoutHeight:
                treeLayoutHeight = defTreeLayoutHeight

            # Set the heights for module list layouts (containing treeView)
            cmds.scrollLayout(self.uiVars['moduleList_Scroll'], edit=True, height=treeLayoutHeight+8)
            cmds.frameLayout(self.uiVars['moduleList_fLayout'], edit=True, height=treeLayoutHeight)

            # Get the current module list sort type
            listStatus = cmds.radioCollection(self.uiVars['sortModuleList_radioColl'], query=True, select=True)

            # Create / update the module list based on sort type
            if listStatus == 'Alphabetically':

                for name in sorted(listNames):

                    # Segregate treeView callback setup based on maya version.
                    # If you don't want to support older maya versions, remove the checks and additional lines
                    # below as necessary.

                    # For maya > 2012, the treeView now accepts python UI callbacks.
                    if _maya_version >=2013:

                        # Add the module name to the treeView, set callbacks
                        cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True, numberOfButtons=3,
                                      addItem=(listNames[name][0], ''),
                                      selectionChangedCommand=moduleSelectionFromTreeViewCallback,
                                      editLabelCommand=processItemRenameForTreeViewListCallback)

                        # If proxy geometry for the module is found, enable/set the proxy geo buttons
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
                            # If no proxy geometry, only enable/set button for module visibility.
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
                        # For maya < 2013, use MEL UI callbacks
                        cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True, numberOfButtons=3,
                                      addItem=(listNames[name][0], ''),
                                      selectionChangedCommand='moduleSelectionFromTreeViewCallback',
                                      editLabelCommand='processItemRenameForTreeViewListCallback')

                        # If proxy geometry for the module is found, enable/set the proxy geo buttons
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
                            # If no proxy geometry, only enable/set button for module visibility.
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


            if listStatus == 'By_hierarchy':    # To sort/show module list by hierarchy

                # To collect modules with their number of traversed parent modules as keys
                parentTraverseForModules = {}

                # Go through each module and collect their parent modules (all).
                for namespace in MRT_namespaces:
                    parentTraverseLength = mfunc.traverseParentModules(namespace)
                    parentTraverseLength = parentTraverseLength[1]

                    # Collect module(s) with their hierarchy levels (number of parent modules).
                    # Store the hierarchy level as key with the module's user specified name as value.
                    if not parentTraverseLength in parentTraverseForModules:
                        parentTraverseForModules[parentTraverseLength] = [namespace.partition('__')[2]]
                    else:
                        # Append module with other modules with the same hierarchy level.
                        parentTraverseForModules[parentTraverseLength].append(namespace.partition('__')[2])

                # Start adding modules to the tree module list starting with module with the
                # least number of parent modules.
                for value in sorted(parentTraverseForModules):

                    # Go through modules at same hierarchy level
                    for name in sorted(parentTraverseForModules[value]):

                        # Get the parent module node (which is attached to module's root node)
                        parentModuleNode = cmds.getAttr(listNames[name][0]+':moduleGrp.moduleParent')

                        # Set python callbacks for maya > 2012
                        if _maya_version >=2013:

                            # Add the module name to the treeView with its parent module, if it exists
                            if parentModuleNode == 'None':
                                # No parent added
                                cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True, numberOfButtons=3,
                                              addItem=(listNames[name][0], ''),
                                              selectionChangedCommand=moduleSelectionFromTreeViewCallback,
                                              editLabelCommand=processItemRenameForTreeViewListCallback)
                            else:
                                # Get the parent module node from attribute info (stripped from parent type text info)
                                parentModuleNode = parentModuleNode.split(',')[0]
                                # Get its namespace
                                parentModule = mfunc.stripMRTNamespace(parentModuleNode)[0]
                                # Add the module name with its parent
                                cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True, numberOfButtons=3,
                                              addItem=(listNames[name][0], parentModule),
                                              selectionChangedCommand=moduleSelectionFromTreeViewCallback,
                                              editLabelCommand=processItemRenameForTreeViewListCallback)

                            # If proxy geometry for the module is found, enable/set the proxy geo buttons
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
                                # If no proxy geometry, only enable/set button for module visibility.
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
                            # For maya < 2013, set MEL UI callbacks

                            # Add the module name to the treeView with its parent module, if it exists
                            if parentModuleNode == 'None':
                                # No parent added
                                cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True, numberOfButtons=3,
                                              addItem=(listNames[name][0], ''),
                                              selectionChangedCommand='moduleSelectionFromTreeViewCallback',
                                              editLabelCommand='processItemRenameForTreeViewListCallback')
                            else:
                                # Get the parent module node from attribute info (stripped from parent type text info)
                                parentModuleNode = parentModuleNode.split(',')[0]
                                # Get its namespace
                                parentModule = mfunc.stripMRTNamespace(parentModuleNode)[0]
                                # Add the module name with its parent
                                cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True, numberOfButtons=3,
                                              addItem=(listNames[name][0], parentModule),
                                              selectionChangedCommand='moduleSelectionFromTreeViewCallback',
                                              editLabelCommand='processItemRenameForTreeViewListCallback')

                            # If proxy geometry for the module is found, enable/set the proxy geo buttons
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
                                # If no proxy geometry, only enable/set button for module visibility.
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

            # After creating the treeView items for scene modules,
            # set their button states / attributes, based on
            for name in sorted(listNames):

                # Set the colour for proxy geo visibility / selection toggle buttons
                if cmds.objExists(listNames[name][0]+':proxyGeometryGrp'):
                    # If proxy geo exist for the module, set the default button colours
                    cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True,
                                  buttonTransparencyColor=([listNames[name][0], 1, 0.85, 0.66, 0.27],
                                                           [listNames[name][0], 2, 0.57, 0.66, 1.0],
                                                           [listNames[name][0], 3, 0.42, 0.87, 1.0]))

                    # If the proxy geometry is visible, set its button colour / state
                    p_state = cmds.getAttr(listNames[name][0]+':proxyGeometryGrp.visibility')
                    if p_state == 0:
                        cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True,
                                      buttonTransparencyColor=[listNames[name][0], 2, 0.65, 0.71, 0.90],
                                      buttonState=[listNames[name][0], 2, 'buttonUp'])

                    # If the proxy geometry is non-selectable, set its button colour / state
                    r_state = cmds.getAttr(listNames[name][0]+':proxyGeometryGrp.overrideDisplayType')
                    if r_state == 0:
                        cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True,
                                      buttonTransparencyColor=[listNames[name][0], 3, 0.68, 0.85, 0.90],
                                      buttonState=[listNames[name][0], 3, 'buttonUp'])
                else:
                    # If no proxy geo exists for the module, set the default button colours
                    cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True,
                                  buttonTransparencyColor=([listNames[name][0], 1, 0.85, 0.66, 0.27],
                                                           [listNames[name][0], 2, 0.39, 0.39, 0.39],
                                                           [listNames[name][0], 3, 0.39, 0.39, 0.39]))
                # Get if the module is visible
                v_state = cmds.getAttr(listNames[name][0]+':moduleGrp.visibility')

                if v_state == 0:
                    # Set the button colour/state if associated module is hidden
                    cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True,
                                  buttonTransparencyColor=[listNames[name][0], 1, 0.71, 0.66, 0.56],
                                  buttonState=[listNames[name][0], 1, 'buttonUp'])

        # If no scene module is found, clear the scene module treeView list, its associated layouts.
        else:
            cmds.scrollLayout(self.uiVars['moduleList_Scroll'], edit=True, height=40)
            cmds.frameLayout(self.uiVars['moduleList_fLayout'], edit=True, height=32)
            cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True, numberOfButtons=1,
                                        addItem=('< no current module in scene >', ''), hideButtons=True)
            cmds.rowLayout(self.uiVars['sortModuleList_row'], edit=True, enable=False)

            if _maya_version >=2013:
                cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True,
                                        font=['< no current module in scene >', 'boldLabelFont'],
                                        editLabelCommand=processItemRenameForTreeViewListCallback, enable=False)
            else:
                cmds.treeView(self.uiVars['sceneModuleList_treeView'], edit=True,
                                        font=['< no current module in scene >', 'boldLabelFont'],
                                        editLabelCommand='processItemRenameForTreeViewListCallback', enable=False)

        # Restore current namespace
        cmds.namespace(setNamespace=currentNamespace)
        cmds.undoInfo(stateWithoutFlush=True)


    def makeCollectionFromSceneTreeViewModulesUI(self, **kwargs):
        '''
        Called to make a module collection by selecting scene module(s) from the MRT UI
        scene module treeView list. This method is also called internally by MRT for creating an
        "auto" module collection while creating a character from scene module(s). The argument
        "allModule" specifies that all modules in the scene will be used to save a module collection.
        '''
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

            # If the module collection is being created by the user.
            # Get the file path for saving the collection.
            # Save it as the new preferred location for saving module collections.
            if not auto:
                fileReturn = cmds.fileDialog2(caption='Save module collection', fileFilter=fileFilter,
                                                                        startingDirectory=startDir, dialogStyle=2)
                if fileReturn == None:
                    return
                ui_preferences['startDirectoryForCollectionSave'] = fileReturn[0].rpartition('/')[0]
                ui_preferences_file = open(self.ui_preferences_path, 'wb')
                cPickle.dump(ui_preferences, ui_preferences_file, cPickle.HIGHEST_PROTOCOL)
                ui_preferences_file.close()

            # If an auto module collection is being by created internally by MRT.
            if auto:
                fileReturn = [auto]

            # If mirror module(s) exist for the selected modules for making a collection
            for module in treeViewSelection[:]: # treeViewSelection to be modified
                if cmds.attributeQuery('mirrorModuleNamespace', node=module+':moduleGrp', exists=True):
                    mirrorModule = cmds.getAttr(module+':moduleGrp.mirrorModuleNamespace')
                    treeViewSelection.append(mirrorModule)

            # Get the first pass of modules to be collected for saving a collection
            modulesToBeCollected = treeViewSelection[:]

            # Get the status for collecting parent modules for current selected modules (and their mirror modules)
            parentCollectStatus = cmds.radioCollection(self.uiVars['moduleSaveColl_options_parentsCheckRadioCollection'],
                                                                                                    query=True, select=True)
            # If direct parent modules are to be collected for current modules, find and add them.
            if parentCollectStatus == 'Direct_Parent':
                # Go through each module.
                for module in treeViewSelection:
                    # Get the parent module node, if it exists.
                    parentModuleNode = cmds.getAttr(module+':moduleGrp.moduleParent')
                    if parentModuleNode != 'None':
                        # Get the parent module namespace and add it.
                        parentModuleNode = parentModuleNode.split(',')[0]
                        parentModule = mfunc.stripMRTNamespace(parentModuleNode)[0]
                        modulesToBeCollected.append(parentModule)

            # If all parents are to be collected for current modules, find and add them.
            if parentCollectStatus == 'All_Parents':
                # Go through each module.
                for module in treeViewSelection:
                    # Find all parent modules for the module.
                    allParentsModuleList = mfunc.traverseParentModules(module)[0]
                    # Collect all the parent module names in a linear list. The 'modulesToBeCollected' is mutable
                    # and is used by the following method as a storage. The existing content for
                    # 'modulesToBeCollected' is not affected.
                    if len(allParentsModuleList):
                        modulesToBeCollected = \
                                mfunc.concatenateCommonNamesFromHierarchyData(allParentsModuleList, modulesToBeCollected)

            # Get the status for collecting child modules for current selected modules (and their mirror modules)
            childrenCollectStatus = cmds.radioCollection(self.uiVars['moduleSaveColl_options_childrenCheckRadioCollection'],
                                                                                                    query=True, select=True)
            # If direct child modules are to be collected for current modules, find and add them.
            if childrenCollectStatus == 'Direct_Children':
                # Go through each module.
                for module in treeViewSelection:
                    # Get the children module(s), if they exist.
                    childrenModuleDict = mfunc.traverseChildrenModules(module)
                    if childrenModuleDict:
                        # Collect the child module(s) by their namespaces
                        modulesToBeCollected += [module for module in childrenModuleDict]

            # If all descendent modules are to be collected for current modules, find and add them.
            if childrenCollectStatus == 'All_Children':
                # Go through each module.
                for module in treeViewSelection:
                    # Find all descendent module(s) for the module.
                    allChildrenModuleDict = mfunc.traverseChildrenModules(module, allChildren=True)
                    if allChildrenModuleDict:
                        # Collect all children module(s) in a linear list and add it to 'modulesToBeCollected'.
                        modulesToBeCollected = mfunc.concatenateCommonNamesFromHierarchyData(allChildrenModuleDict,
                                                                                                    modulesToBeCollected)
            # Collect the mirror module(s) for the new module(s) that are added.
            for module in copy.copy(modulesToBeCollected):
                if cmds.attributeQuery('mirrorModuleNamespace', node=module+':moduleGrp', exists=True):
                    mirrorModule = cmds.getAttr(module+':moduleGrp.mirrorModuleNamespace')
                    modulesToBeCollected.append(mirrorModule)

            modulesToBeUnparented = {}
            # Collect all parent module(s) (non-included in 'modulesToBeCollected') for modules to be collected.
            # These modules to be collected will be temporarily "unparented".
            # This is done to select and export the collected module(s) without exporting unnecessary DG items.
            allModuleNamespaces = mfunc.returnMRT_Namespaces(cmds.namespaceInfo(listOnlyNamespaces=True))
            for module in modulesToBeCollected:
                moduleParentNode = cmds.getAttr(module+':moduleGrp.moduleParent')
                if moduleParentNode != 'None':
                    parentModuleNodeAttr = moduleParentNode.split(',')
                    moduleParent = mfunc.stripMRTNamespace(parentModuleNodeAttr[0])[0]
                    if not moduleParent in modulesToBeCollected:

                        # Collect the parent module node not included in the modules to be saved as collection
                        modulesToBeUnparented[module] = parentModuleNodeAttr[0]

            if modulesToBeUnparented:
                # Go through each module.
                for module in modulesToBeUnparented:
                    # Remove the module parenting constraint connection.
                    cmds.lockNode(module+':module_container', lock=False, lockUnpublished=False)
                    constraint = cmds.listRelatives(module+':moduleParentReprSegment_segmentCurve_endLocator',
                                                                            children=True, fullPath=True, type='constraint')
                    cmds.delete(constraint)

            # Finally, for the modules to be saved as collection, save their corresponding module containers,
            # and their proxy geometry group, if it exists.
            moduleObjectsToBeCollected = []
            for module in modulesToBeCollected:
                moduleObjectsToBeCollected.append(module+':module_container')
                if cmds.objExists(module+':proxyGeometryGrp'):
                    moduleObjectsToBeCollected.append(module+':proxyGeometryGrp')

            # Check if the file path exists for the module collection, previously returned by the user (using fileDialog).
            # Remove the module collection file. It'll be overwritten.
            if os.path.exists(fileReturn[0]):
                os.remove(fileReturn[0])

            # Create a dict object, to contain the module collection data (by key) to be saved.
            mrtmc_fObject = {}

            # Save the module collection description.
            mrtmc_fObject['collectionDescrp'] = collectionDescription

            # Select the module containers and module proxy geometry (see above) to be included in the collection.
            cmds.select(moduleObjectsToBeCollected, replace=True)

            # Disable / remove module mirror move connections
            mfunc.deleteMirrorMoveConnections()

            # Create a temporary maya scene to export module collection data.
            tempFilePath = fileReturn[0].rpartition('.mrtmc')[0]+'_temp.ma'
            cmds.file(tempFilePath, force=True, options='v=1', type='mayaAscii', exportSelected=True, pr=True)

            # Read the contents of the maya scene and use it to construct module collection file.
            tempFile_fObject = open(tempFilePath)
            for i, line in enumerate(tempFile_fObject):
                mrtmc_fObject['collectionData_line_'+str(i+1)] = line
            tempFile_fObject.close()

            # Remove the temporary maya scene file.
            os.remove(tempFilePath)

            # Now, write/save the module collection file.
            mrtmc_fObject_file = open(fileReturn[0], 'wb')
            cPickle.dump(mrtmc_fObject, mrtmc_fObject_file, cPickle.HIGHEST_PROTOCOL)
            mrtmc_fObject_file.close()

            # Remove the reference to module collection file object (for garbage collection).
            del mrtmc_fObject

            # If module collection is being saved by the user, get the UI preference to load the
            # new module collection into the UI module collection list.
            if not auto:
                ui_preferences_file = open(self.ui_preferences_path, 'rb')
                ui_preferences = cPickle.load(ui_preferences_file)
                ui_preferences_file.close()
                loadNewCollections = ui_preferences['autoLoadNewSavedModuleCollectionToListStatus']
                # If preference set to load new collections, load/add the new saved collection to the list.
                if loadNewCollections:
                    self.loadModuleCollectionsForUI([fileReturn[0]])

            # Re-create the module parenting constraints, which were temporarily removed (see above).
            if modulesToBeUnparented:
                for module in modulesToBeUnparented:
                    pointConstraint = cmds.pointConstraint(modulesToBeUnparented[module],
                        module+':moduleParentReprSegment_segmentCurve_endLocator', maintainOffset=False,
                                    name=module+':moduleParentReprSegment_endLocator_pointConstraint')[0]
                    mfunc.addNodesToContainer(module+':module_container', [pointConstraint])
                    cmds.setAttr(module+':moduleGrp.moduleParent', modulesToBeUnparented[module], type='string')
                    cmds.lockNode(module+':module_container', lock=True, lockUnpublished=True)


        # NESTED_DEF_2 #
        def saveModuleCollectionFromDescriptionProcessInputUI(*args):
            # Process the module collection description input before proceeding with creating a module collection.

            # If all modules are to be saved as a collection,
            if allModules:
                treeViewSelection = mrt_namespaces
            else:
                # Get the module(s) that are selected in the treeView list.
                # During the proces of entering a description, if the selection changes.
                treeViewSelection = cmds.treeView(self.uiVars['sceneModuleList_treeView'], query=True, selectItem=True)
                if treeViewSelection == None:
                    cmds.warning('MRT Error: Module collection error. No module(s) selected for making a collection.')
                    return

            # Check the description. If empty, notify the user, or proceed.
            if not auto:
                collectionDescription = cmds.scrollField(self.uiVars['collectionDescpWindowScrollField'], query=True, text=True)

                if collectionDescription == '':

                    # Close the window if it exists.
                    try:
                        cmds.deleteUI('mrt_collection_noDescpError_UI_window')
                    except:
                        pass

                    # Create the "no description error window".
                    self.uiVars['collectionNoDescpErrorWindow'] = cmds.window('mrt_collection_noDescpError_UI_window',
                                                title='Module collection warning', maximizeButton=False, sizeable=False)

                    # Remove it from preference.
                    try:
                        cmds.windowPref('mrt_collection_noDescpError_UI_window', remove=True)
                    except:
                        pass

                    # Create the parent layouts and elements.
                    cmds.frameLayout(visible=True, borderVisible=False, collapsable=False, labelVisible=False, height=90,
                                                                                width=220, marginWidth=20, marginHeight=15)
                    cmds.text(label='Are you sure you want to continue saving a collection with an empty description?')
                    cmds.rowLayout(numberOfColumns=2, columnAttach=([1, 'left', 90], [2, 'left', 30]),
                                                                rowAttach=([1, 'top', 8], [2, 'top', 8]))

                    cmds.button(label='Continue', width=90, command=partial(saveModuleCollectionFromDescription,
                                                                            collectionDescription,
                                                                            treeViewSelection))
                    # cmds.button(label='Revert', width=90,
                    #                   command=('cmds.deleteUI(\"'+self.uiVars['collectionNoDescpErrorWindow']+'\")'))

                    cmds.button(label='Revert', width=90, command=partial(self.closeWindow,
                                                                        self.uiVars['collectionNoDescpErrorWindow']))
                    # Display the "no description error window".
                    cmds.showWindow(self.uiVars['collectionNoDescpErrorWindow'])
                else:
                    saveModuleCollectionFromDescription(collectionDescription, treeViewSelection)
            if auto:
                # If an auto module collection is to be saved.
                saveModuleCollectionFromDescription('Auto generated collection', treeViewSelection)

        # MAIN DEF_BEGINS #

        # Save current namespace, set to root
        currentNamespace = cmds.namespaceInfo(currentNamespace=True)
        cmds.namespace(setNamespace=':')

        # Get the current selection.
        selection = cmds.ls(selection=True) or None

        # Get the method arguments
        allModules = kwargs['allModules'] if 'allModules' in kwargs else False
        auto = kwargs['auto'] if 'auto' in kwargs else None

        if allModules:
            # If all modules in the scene are to be included in the collection,
            namespaces = cmds.namespaceInfo(listOnlyNamespaces=True)
            # Include all module namespaces
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

        # If a module collection is being save by a user.
        if not auto:
            # Close the window for entering module collection description, if it exists.
            try:
                cmds.deleteUI('mrt_collectionDescription_input_UI_window')
            except:
                pass

            # Create a window UI for entering the module collection description.
            self.uiVars['collectionDescpWindow'] = cmds.window('mrt_collectionDescription_input_UI_window',
                                title='Module collection description', height=150, maximizeButton=False, sizeable=False)

            # Remove the window from preference
            try:
                cmds.windowPref('mrt_collectionDescription_input_UI_window', remove=True)
            except:
                pass

            # Main column
            self.uiVars['collectionDescpWindowColumn'] = cmds.columnLayout(adjustableColumn=True)

            cmds.text(label='')
            cmds.text('Enter description for module collection', align='center', font='boldLabelFont')

            # Parent layout for description text field.
            cmds.frameLayout(visible=True, borderVisible=False, collapsable=False, labelVisible=False, height=75,
                                                                            width=300, marginWidth=5, marginHeight=10)
            self.uiVars['collectionDescpWindowScrollField'] = cmds.scrollField(preventOverride=True, wordWrap=True)

            # Set to main column
            cmds.setParent(self.uiVars['collectionDescpWindowColumn'])
            # Parent layout for buttons
            cmds.rowLayout(numberOfColumns=2, columnAttach=([1, 'left', 28], [2, 'left', 20]))
            cmds.button(label='Save collection', width=130, command=saveModuleCollectionFromDescriptionProcessInputUI)
            # cmds.button(label='Cancel', width=90, command=('cmds.deleteUI(\"'+self.uiVars['collectionDescpWindow']+'\")'))
            cmds.button(label='Cancel', width=90, command=partial(self.closeWindow, self.uiVars['collectionDescpWindow']))

            cmds.setParent(self.uiVars['collectionDescpWindowColumn'])
            cmds.text(label='')

            cmds.showWindow(self.uiVars['collectionDescpWindow'])

        # If an auto module collection is to be saved (used internally by MRT).
        if auto:
            saveModuleCollectionFromDescriptionProcessInputUI()

        # Restore previous namespace
        cmds.namespace(setNamespace=currentNamespace)

        # Restore previous selection
        cmds.select(selection, replace=True)


    def performModuleRename(self, *args):
        '''
        Renames a selected module. Modifies the user specified name.
        '''
        # Save the current namespace, set to root.
        currentNamespace = cmds.namespaceInfo(currentNamespace=True)
        cmds.namespace(setNamespace=':')

        # Disable / delete all mirror move nodes and connections for mirror module nodes.
        mfunc.deleteMirrorMoveConnections()

        # Get the new user specified name for renaming the module.
        newUserSpecifiedName = cmds.textField(self.uiVars['moduleRename_textField'], query=True, text=True)
        newUserSpecifiedName = newUserSpecifiedName.lower()

        # Get the last selected module.
        selectedModule = cmds.ls(selection=True)
        selectedModule = selectedModule[-1]

        # Get the current namespace name for the selected module.
        currentNamespaceForSelectedModule = mfunc.stripMRTNamespace(selectedModule)[0]

        # Set the new namespace using the new user specified name for the module.
        newNamespace = currentNamespaceForSelectedModule.rpartition('__')[0] + '__' + newUserSpecifiedName

        # If the new namespace matches existing, return.
        if newNamespace == currentNamespaceForSelectedModule:
            return

        # Get all module namespaces in the scene.
        sceneNamespaces = mfunc.returnMRT_Namespaces(cmds.namespaceInfo(listOnlyNamespaces=True))

        currentModuleUserNames = []

        # Check if the new module namespace exists in the scene, return if true.
        if sceneNamespaces:
            for namespace in sceneNamespaces:
                userSpecifiedName = namespace.partition('__')[2]
                if newUserSpecifiedName == userSpecifiedName:
                    cmds.warning('MRT Error: Namespace conflict. The module name "%s" already ' \
                                                                    'exists in the scene.' % newUserSpecifiedName)
                    return

        # Now, that there are no namespace conflicts with existing modules, module re-naming can proceed.

        # Modify the module's namespace stored in module creation queue with the new namespace.
        if len(self.modules):
            for (key, value) in self.modules.items():
                for i, item in enumerate(value):
                    if item == currentNamespaceForSelectedModule:
                        self.modules[key][i] = newNamespace
                        break

        # If the module has children (modules), modify their "moduleParent" attribute, to
        # match the new parent module namespace.
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

        # Finally, re-name the namespace for the module itself.
        # Add the new module namespace.
        cmds.namespace(addNamespace=newNamespace)

        # Unclock the module container to perform changes.
        cmds.lockNode(currentNamespaceForSelectedModule+':module_container', lock=False, lockUnpublished=False)

        # Move the contents of module from old namespace to the new namespace.
        cmds.namespace(moveNamespace=[currentNamespaceForSelectedModule, newNamespace])

        # Remove the old module namespace.
        cmds.namespace(removeNamespace=currentNamespaceForSelectedModule)

        # If a mirror module exists (if the module is part of a mirror module pair),
        # change the "mirrorModuleNamespace" attribute on the mirror module to match the new namespace.
        # This attribute is used to find a module's mirror.
        if cmds.attributeQuery('mirrorModuleNamespace', node=newNamespace+':moduleGrp', exists=True):
            mirrorModuleNamespace = cmds.getAttr(newNamespace+':moduleGrp.mirrorModuleNamespace')
            cmds.lockNode(mirrorModuleNamespace+':module_container', lock=False, lockUnpublished=False)
            cmds.setAttr(mirrorModuleNamespace+':moduleGrp.mirrorModuleNamespace', newNamespace, type='string')
            cmds.lockNode(mirrorModuleNamespace+':module_container', lock=True, lockUnpublished=True)

        # Lock the module container after re-naming.
        cmds.lockNode(newNamespace+':module_container', lock=True, lockUnpublished=True)

        # Select the re-named module.
        selection = newNamespace+':'+mfunc.stripMRTNamespace(selectedModule)[1]
        cmds.select(selection, replace=True)

        # Update the scene module list
        self.updateListForSceneModulesInUI()

        # Clear module parenting fields.
        self.clearParentModuleField()
        self.clearChildModuleField()

        # Reset the current namespace.
        if cmds.namespace(exists=currentNamespace):
            cmds.namespace(setNamespace=currentNamespace)


    def performModuleDuplicate_UI_wrapper(self, *args):
        '''
        Duplicates a selected module, when initiated using the "Duplicate selected module" from MRT UI.
        Calls performModuleDuplicate() to perform the duplication.
        '''
        # Close the duplicate action window if open.
        try:
            cmds.deleteUI('mrt_duplicateModuleAction_UI_window')
        except:
            pass

        # Create the module duplication window
        self.uiVars['duplicateActionWindow'] = cmds.window('mrt_duplicateModuleAction_UI_window', title='Duplicate Module',
                                                                widthHeight=(300, 150), maximizeButton=False, sizeable=False)
        # Remove it from preferences
        try:
            cmds.windowPref('mrt_duplicateModuleAction_UI_window', remove=True)
        except:
            pass

        # Main column
        self.uiVars['duplicateActionWindowColumn'] = cmds.columnLayout(adjustableColumn=True)

        cmds.text(label='')

        # Float 3 field for module duplication offset
        cmds.text('Enter relative offset for duplication (translation)', align='center', font='boldLabelFont')
        self.uiVars['duplicateActionWindowFloatfieldGrp'] = cmds.floatFieldGrp(numberOfFields=3,
                                                                               label='Offset (world units)',
                                                                               value1=1.0, value2=1.0, value3=1.0,
                                                                               columnAttach=([1, 'left', 15],
                                                                                             [2, 'left', 1],
                                                                                             [3, 'left', 1],
                                                                                             [4, 'right', 12]),
                                                                               columnWidth4=[120, 80, 80, 90],
                                                                               rowAttach=([1, 'top', 14],
                                                                                          [2, 'top', 10],
                                                                                          [3, 'top', 10],
                                                                                          [4, 'top', 10]))
        # Maintain module parenting after duplication
        cmds.rowLayout(numberOfColumns=1, columnAttach=[1, 'left', 110], rowAttach=[1, 'top', 2])
        self.uiVars['duplicateAction_maintainParentCheckbox'] = cmds.checkBox(label='Maintain parent connections',
                                                                                            enable=True, value=True)
        cmds.setParent(self.uiVars['duplicateActionWindowColumn'])

        # Button for module duplicate command
        cmds.rowLayout(numberOfColumns=1, columnAttach=[1, 'left', 115], rowAttach=[1, 'top', 5])
        cmds.button(label='OK', width=150, command=self.performModuleDuplicate)
        cmds.setParent(self.uiVars['duplicateActionWindowColumn'])

        cmds.text(label='')
        cmds.showWindow(self.uiVars['duplicateActionWindow'])


    def performModuleDuplicate(self, *args):
        '''
        Called by "performModuleDuplicate_UI_wrapper" to duplicate a scene module.
        '''
        # Check selection.
        selection = cmds.ls(selection=True)
        if not selection:
            cmds.warning('MRT Error: Duplicate Module Error. Nothing is selected. ' \
                                                    'Please select a module to perform duplication.')
            return

        # Get last item in selection.
        selection = selection[-1]

        # Check selection for module.
        if mfunc.stripMRTNamespace(selection) == None:
            cmds.warning('MRT Error: Duplicate Module Error. Invalid selection. Please select a module.')
            return

        # Get module namespace and its current attributes.
        moduleNamespace = mfunc.stripMRTNamespace(selection)[0]
        moduleAttrsDict = mfunc.returnModuleAttrsFromScene(moduleNamespace)

        # Create a new copy of the module using the attributes.
        mfunc.createModuleFromAttributes(moduleAttrsDict)

        cmds.select(clear=True)

        # If "Maintain parent connections" is turned on, connect the new module to the parent of the original module.
        if cmds.checkBox(self.uiVars['duplicateAction_maintainParentCheckbox'], query=True, value=True):

            # Get the module parenting info from the collected attributes.
            # "createModuleFromAttributes" modifies the "moduleParentInfo" key's first item
            # with the new created module namespace.
            for (module, parentModuleNode) in moduleAttrsDict['moduleParentInfo']:

                # If the original module has parent.
                if module != None and parentModuleNode != 'None':

                    # Get the parent module node.
                    parentModuleNodeAttr = parentModuleNode.split(',')

                    # Unlock the new module container.
                    cmds.lockNode(module+':module_container', lock=False, lockUnpublished=False)

                    # Connect the module parent representation to the parent module node.
                    pointConstraint = \
                    cmds.pointConstraint(parentModuleNodeAttr[0],
                                         module+':moduleParentReprSegment_segmentCurve_endLocator',
                                         maintainOffset=False,
                                         name=module+':moduleParentReprSegment_endLocator_pointConstraint')[0]

                    # Update the "moduleParent" attribute on the new module with the parent module node.
                    cmds.setAttr(module+':moduleGrp.moduleParent', parentModuleNode, type='string')

                    # Set the module parent representation colour to "white" if module parent type
                    # is set to "Hierarchical".
                    if parentModuleNodeAttr[1] == 'Hierarchical':
                        cmds.setAttr(module+':moduleParentReprSegment_hierarchy_reprShape.overrideColor', 16)

                    # Add the new nodes to the new module container.
                    mfunc.addNodesToContainer(module+':module_container', [pointConstraint])

                    # Turn on the visibility for module parent representation.
                    cmds.setAttr(module+':moduleParentReprGrp.visibility', 1)

                    # Lock the container for the new module.
                    cmds.lockNode(module+':module_container', lock=True, lockUnpublished=True)

        cmds.select(clear=True)

        # If the original module has proxy geometry, duplicate them as well.
        # To do this, delete the proxy geometry on the duplicated module first.
        if moduleAttrsDict['node_compnts'][2] == True:

            # If elbow proxy geometry.
            if moduleAttrsDict['proxy_geo_options'][1] == True:

                for i in range(moduleAttrsDict['num_nodes']):

                    if i == 0:

                        # Get the name of the original proxy geometry transform.
                        orig_proxy_elbow_transform = moduleAttrsDict['orig_module_Namespace']+':root_node_transform_proxy_elbow_geo'

                        # Get the name of the duplicated module proxy geometry transform.
                        proxy_elbow_transform = moduleAttrsDict['module_Namespace']+':root_node_transform_proxy_elbow_geo'

                        if cmds.objExists(orig_proxy_elbow_transform+'_preTransform'):

                            # Delete the new proxy geometry transform on the duplicated module.
                            cmds.delete(proxy_elbow_transform)

                            # Duplicate the original proxy geometry transform, rename it.
                            duplicatedTransform = cmds.duplicate(orig_proxy_elbow_transform,
                                        name=moduleAttrsDict['module_Namespace']+':root_node_transform_proxy_elbow_geo')[0]

                            # Assign it to the new duplicate module.
                            cmds.parent(duplicatedTransform, proxy_elbow_transform+'_scaleTransform', relative=True)

                        else:
                            cmds.delete(proxy_elbow_transform+'_preTransform')

                    elif i == moduleAttrsDict['num_nodes']-1:
                        orig_proxy_elbow_transform = moduleAttrsDict['orig_module_Namespace']+':end_node_transform_proxy_elbow_geo'
                        proxy_elbow_transform = moduleAttrsDict['module_Namespace']+':end_node_transform_proxy_elbow_geo'

                        if cmds.objExists(orig_proxy_elbow_transform+'_preTransform'):
                            cmds.delete(proxy_elbow_transform)
                            duplicatedTransform = cmds.duplicate(orig_proxy_elbow_transform,
                                        name=moduleAttrsDict['module_Namespace']+':end_node_transform_proxy_elbow_geo')[0]

                            cmds.parent(duplicatedTransform, proxy_elbow_transform+'_scaleTransform', relative=True)

                        else:
                            cmds.delete(proxy_elbow_transform+'_preTransform')

                    else:
                        proxy_elbow_transform = moduleAttrsDict['module_Namespace']+':node_'+str(i)+'_transform_proxy_elbow_geo'
                        orig_proxy_elbow_transform = moduleAttrsDict['orig_module_Namespace']+':node_'+str(i)+'_transform_proxy_elbow_geo'

                        if cmds.objExists(orig_proxy_elbow_transform+'_preTransform'):
                            cmds.delete(proxy_elbow_transform)
                            duplicatedTransform = cmds.duplicate(orig_proxy_elbow_transform,
                                        name=moduleAttrsDict['module_Namespace']+':node_'+str(i)+'_transform_proxy_elbow_geo')[0]

                            cmds.parent(duplicatedTransform, proxy_elbow_transform+'_scaleTransform', relative=True)

                        else:
                            cmds.delete(proxy_elbow_transform+'_preTransform')


            # If bone proxy geometry.
            if moduleAttrsDict['proxy_geo_options'][0] == True:

                for i in range(moduleAttrsDict['num_nodes']-1):

                    if i == 0:

                        orig_proxy_bone_transform = moduleAttrsDict['orig_module_Namespace']+':root_node_transform_proxy_bone_geo'
                        proxy_bone_transform = moduleAttrsDict['module_Namespace']+':root_node_transform_proxy_bone_geo'

                        if cmds.objExists(orig_proxy_bone_transform+'_preTransform'):
                            cmds.delete(proxy_bone_transform)
                            duplicatedTransform = cmds.duplicate(orig_proxy_bone_transform,
                                        name=moduleAttrsDict['module_Namespace']+':root_node_transform_proxy_bone_geo')[0]

                            cmds.parent(duplicatedTransform, proxy_bone_transform+'_scaleTransform', relative=True)

                        else:
                            cmds.delete(proxy_bone_transform+'_preTransform')

                    else:
                        proxy_bone_transform = moduleAttrsDict['module_Namespace']+':node_'+str(i)+'_transform_proxy_bone_geo'
                        orig_proxy_bone_transform = moduleAttrsDict['orig_module_Namespace']+':node_'+str(i)+'_transform_proxy_bone_geo'

                        if cmds.objExists(orig_proxy_bone_transform+'_preTransform'):
                            cmds.delete(proxy_bone_transform)
                            duplicatedTransform = cmds.duplicate(orig_proxy_bone_transform,
                                        name=moduleAttrsDict['module_Namespace']+':node_'+str(i)+'_transform_proxy_bone_geo')[0]

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
                                    duplicatedTransform = cmds.duplicate(orig_proxy_elbow_transform,
                                        name=moduleAttrsDict['mirror_module_Namespace']+':root_node_transform_proxy_elbow_geo')[0]

                                    cmds.parent(duplicatedTransform, proxy_elbow_transform+'_scaleTransform', relative=True)

                                else:
                                    cmds.delete(proxy_elbow_transform+'_preTransform')

                            if moduleAttrsDict['proxy_geo_options'][3] == 'On':

                                mirror_proxy_elbow_transform = moduleAttrsDict['module_Namespace']+':root_node_transform_proxy_elbow_geo'

                                if cmds.objExists(mirror_proxy_elbow_transform+'_preTransform'):
                                    cmds.delete(proxy_elbow_transform)
                                    duplicatedTransform = cmds.duplicate(mirror_proxy_elbow_transform, instanceLeaf=True,
                                        name=moduleAttrsDict['mirror_module_Namespace']+':root_node_transform_proxy_elbow_geo')[0]

                                    cmds.parent(duplicatedTransform, proxy_elbow_transform+'_scaleTransform', relative=True)

                                else:
                                    cmds.delete(proxy_elbow_transform+'_preTransform')

                        elif i == moduleAttrsDict['num_nodes']-1:

                            orig_proxy_elbow_transform = moduleAttrsDict['orig_mirror_module_Namespace']+':end_node_transform_proxy_elbow_geo'
                            proxy_elbow_transform = moduleAttrsDict['mirror_module_Namespace']+':end_node_transform_proxy_elbow_geo'

                            if moduleAttrsDict['proxy_geo_options'][3] == 'Off':

                                if cmds.objExists(orig_proxy_elbow_transform+'_preTransform'):
                                    cmds.delete(proxy_elbow_transform)
                                    duplicatedTransform = cmds.duplicate(orig_proxy_elbow_transform,
                                        name=moduleAttrsDict['mirror_module_Namespace']+':end_node_transform_proxy_elbow_geo')[0]

                                    cmds.parent(duplicatedTransform, proxy_elbow_transform+'_scaleTransform', relative=True)

                                else:
                                    cmds.delete(proxy_elbow_transform+'_preTransform')

                            if moduleAttrsDict['proxy_geo_options'][3] == 'On':

                                mirror_proxy_elbow_transform = moduleAttrsDict['module_Namespace']+':end_node_transform_proxy_elbow_geo'

                                if cmds.objExists(mirror_proxy_elbow_transform+'_preTransform'):
                                    cmds.delete(proxy_elbow_transform)
                                    duplicatedTransform = cmds.duplicate(mirror_proxy_elbow_transform, instanceLeaf=True,
                                        name=moduleAttrsDict['mirror_module_Namespace']+':end_node_transform_proxy_elbow_geo')[0]

                                    cmds.parent(duplicatedTransform, proxy_elbow_transform+'_scaleTransform', relative=True)

                                else:
                                    cmds.delete(proxy_elbow_transform+'_preTransform')

                        else:
                            orig_proxy_elbow_transform = moduleAttrsDict['orig_mirror_module_Namespace']+':node_'+str(i)+'_transform_proxy_elbow_geo'
                            proxy_elbow_transform = moduleAttrsDict['mirror_module_Namespace']+':node_'+str(i)+'_transform_proxy_elbow_geo'

                            if moduleAttrsDict['proxy_geo_options'][3] == 'Off':

                                if cmds.objExists(orig_proxy_elbow_transform+'_preTransform'):
                                    cmds.delete(proxy_elbow_transform)
                                    duplicatedTransform = cmds.duplicate(orig_proxy_elbow_transform,
                                        name=moduleAttrsDict['mirror_module_Namespace']+':node_'+str(i)+'_transform_proxy_elbow_geo')[0]

                                    cmds.parent(duplicatedTransform, proxy_elbow_transform+'_scaleTransform', relative=True)

                                else:
                                    cmds.delete(proxy_elbow_transform+'_preTransform')

                            if moduleAttrsDict['proxy_geo_options'][3] == 'On':

                                mirror_proxy_elbow_transform = moduleAttrsDict['module_Namespace']+':node_'+str(i)+'_transform_proxy_elbow_geo'

                                if cmds.objExists(mirror_proxy_elbow_transform+'_preTransform'):
                                    cmds.delete(proxy_elbow_transform)
                                    duplicatedTransform = cmds.duplicate(mirror_proxy_elbow_transform, instanceLeaf=True,
                                        name=moduleAttrsDict['mirror_module_Namespace']+':node_'+str(i)+'_transform_proxy_elbow_geo')[0]

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
                                    duplicatedTransform = cmds.duplicate(orig_proxy_bone_transform,
                                        name=moduleAttrsDict['mirror_module_Namespace']+':root_node_transform_proxy_bone_geo')[0]

                                    cmds.parent(duplicatedTransform, proxy_bone_transform+'_scaleTransform', relative=True)

                                else:
                                    cmds.delete(proxy_bone_transform+'_preTransform')

                            if moduleAttrsDict['proxy_geo_options'][3] == 'On':

                                mirror_proxy_bone_transform = moduleAttrsDict['module_Namespace']+':root_node_transform_proxy_bone_geo'

                                if cmds.objExists(mirror_proxy_bone_transform+'_preTransform'):
                                    cmds.delete(proxy_bone_transform)
                                    duplicatedTransform = cmds.duplicate(mirror_proxy_bone_transform, instanceLeaf=True,
                                        name=moduleAttrsDict['mirror_module_Namespace']+':root_node_transform_proxy_bone_geo')[0]

                                    cmds.parent(duplicatedTransform, proxy_bone_transform+'_scaleTransform', relative=True)

                                else:
                                    cmds.delete(proxy_bone_transform+'_preTransform')
                        else:
                            orig_proxy_bone_transform = moduleAttrsDict['orig_mirror_module_Namespace']+':node_'+str(i)+'_transform_proxy_bone_geo'
                            proxy_bone_transform = moduleAttrsDict['mirror_module_Namespace']+':node_'+str(i)+'_transform_proxy_bone_geo'

                            if moduleAttrsDict['proxy_geo_options'][3] == 'Off':

                                if cmds.objExists(orig_proxy_bone_transform+'_preTransform'):
                                    cmds.delete(proxy_bone_transform)
                                    duplicatedTransform = cmds.duplicate(orig_proxy_bone_transform,
                                        name=moduleAttrsDict['mirror_module_Namespace']+':node_'+str(i)+'_transform_proxy_bone_geo')[0]

                                    cmds.parent(duplicatedTransform, proxy_bone_transform+'_scaleTransform', relative=True)

                                else:
                                    cmds.delete(proxy_bone_transform+'_preTransform')

                            if moduleAttrsDict['proxy_geo_options'][3] == 'On':
                                mirror_proxy_bone_transform = moduleAttrsDict['module_Namespace']+':node_'+str(i)+'_transform_proxy_bone_geo'

                                if cmds.objExists(mirror_proxy_bone_transform+'_preTransform'):
                                    cmds.delete(proxy_bone_transform)
                                    duplicatedTransform = cmds.duplicate(mirror_proxy_bone_transform, instanceLeaf=True,
                                        name=moduleAttrsDict['mirror_module_Namespace']+':node_'+str(i)+'_transform_proxy_bone_geo')[0]

                                    cmds.parent(duplicatedTransform, proxy_bone_transform+'_scaleTransform', relative=True)

                                else:
                                    cmds.delete(proxy_bone_transform+'_preTransform')

        # Update the scene module treeView list with the new duplicated module.
        self.updateListForSceneModulesInUI()

        # Get the translation offset to be applied to the new duplicated module.
        offset = cmds.floatFieldGrp(self.uiVars['duplicateActionWindowFloatfieldGrp'], query=True, value=True)

        # Apply the offset to new module's module transform.
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

        # Clear selection when idle.
        cmds.evalDeferred(partial(mfunc.performOnIdle), lowestPriority=True)


    def performModuleDeletion(self, *args):
        '''
        Deletes a selected module from scene.
        '''
        # Store the current namespace.
        currentNamespace = cmds.namespaceInfo(currentNamespace=True)
        cmds.namespace(setNamespace=':')

        # Get the selected module.
        selection = mel.eval("ls -sl -type dagNode")
        moduleSelection = selection[0]

        # Get the module namespace.
        moduleSelectionNamespace = mfunc.stripMRTNamespace(moduleSelection)[0]

        # Collect the module to be removed (if its mirrored module exists, it will be added later).
        modulesToBeRemoved = [moduleSelectionNamespace]

        # Now add the mirror for the current module if it exists.
        if cmds.attributeQuery('mirrorModuleNamespace', node=moduleSelectionNamespace+':moduleGrp', exists=True):
            modulesToBeRemoved.append(cmds.getAttr(moduleSelectionNamespace+':moduleGrp.mirrorModuleNamespace'))

        # Remove the module(s) to be deleted from module creation queue.
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

        # If the module creation queue becomes empty, disable the "Undo last create" button for modules.
        if not len(self.modules):
            cmds.button(self.uiVars['moduleUndoCreate_button'], edit=True, enable=False)

        # Delete the connections/nodes for moving mirror modules.
        mfunc.deleteMirrorMoveConnections()

        # Perform deletions.
        for namespace in modulesToBeRemoved:

            # Remove connection(s) to children module(s) (if they exist).
            self.removeChildrenModules(namespace)

            # Get the module container, unlock it.
            moduleContainer = namespace+':module_container'
            cmds.lockNode(moduleContainer, lock=False, lockUnpublished=False)

            # Remove curveInfo from module container (maya issues warnings if connections are deleted
            # to curveInfos, before deleting the curveInfo nodes).
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

            # Now delete the module container.
            cmds.select(moduleContainer, replace=True)
            cmds.delete()

        # Remove the module namespaces.
        for namespace in modulesToBeRemoved:
            cmds.namespace(removeNamespace=namespace)

        # Reset current namespace.
        if cmds.namespace(exists=currentNamespace):
            cmds.namespace(setNamespace=currentNamespace)

        # Perform cleanup.
        mfunc.cleanSceneState()
        self.clearParentModuleField()
        self.clearChildModuleField()
        self.resetListHeightForSceneModulesUI()


    def deleteAllSceneModules(self):
        '''
        Removes all module from scene. Called in "processCharacterFromScene".
        '''
        namespacesToBeRemoved = []

        # Store the current namespace.
        currentNamespace = cmds.namespaceInfo(currentNamespace=True)
        cmds.namespace(setNamespace=':')

        # Get all module namespaces.
        allModules = mfunc.returnMRT_Namespaces(cmds.namespaceInfo(listOnlyNamespaces=True))

        # Disconnect module parenting connections for all modules.
        for namespace in allModules:
            self.removeChildrenModules(namespace)

        # Remove curveInfos from module containers (maya issues warnings if connections are deleted
        # to curveInfos, before deleting the curveInfo nodes).
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

            # Delete the module container.
            cmds.select(moduleContainer, replace=True)
            cmds.delete()

            namespacesToBeRemoved.append(namespace)

        # Remove module namespaces from scene.
        if namespacesToBeRemoved:
            for namespace in namespacesToBeRemoved:
                cmds.namespace(removeNamespace=namespace)

        # Reset current namespace.
        if cmds.namespace(exists=currentNamespace):
            cmds.namespace(setNamespace=currentNamespace)

        # Perform cleanup.
        mfunc.cleanSceneState()
        cmds.button(self.uiVars['moduleUndoCreate_button'], edit=True, enable=False)
        self.modules = {}
        self.clearParentModuleField()
        self.clearChildModuleField()


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


    # ................................................ MODULE PARENTING ............................................

    def removeChildrenModules(self, moduleNamespace):
        '''
        Removes connections from children module(s) from a given module, if they exist.
        '''
        # Get children module namespaces.
        childrenModules = mfunc.traverseChildrenModules(moduleNamespace)

        if childrenModules:

            for childModule in childrenModules:

                # Unlock child module container.
                cmds.lockNode(childModule+':module_container', lock=False, lockUnpublished=False)

                # Get module parenting constraint, and delete it.
                constraint = cmds.listRelatives(childModule+':moduleParentReprSegment_segmentCurve_endLocator',
                                                                    children=True, fullPath=True, type='constraint')
                cmds.delete(constraint)

                # Reset module parenting attributes.
                cmds.setAttr(childModule+':moduleGrp.moduleParent', 'None', type='string')
                cmds.setAttr(childModule+':moduleParentReprGrp.visibility', 0)

                # Lock child module container.
                cmds.lockNode(childModule+':module_container', lock=True, lockUnpublished=True)


    def insertChildModuleIntoField(self, *args):
        '''
        Inserts a selected scene module into the child module textfield for module parenting.
        '''
        # Get selection, and get the selection module namespace, if valid.
        selection = cmds.ls(selection=True)
        if selection:
            lastSelection = selection[-1]
            namespaceInfo = mfunc.stripMRTNamespace(lastSelection)

            # If valid scene module, insert its namespace into the child module textfield.
            if namespaceInfo != None:
                cmds.textField(self.uiVars['selectedChildModule_textField'], edit=True, text=namespaceInfo[0],
                                                                                                font='plainLabelFont')
                parentInfo = cmds.getAttr(namespaceInfo[0]+':moduleGrp.moduleParent')

                # If the module has a parent, enable associated button states.
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

                return

        # If no valid module is selected.
        cmds.textField(self.uiVars['selectedChildModule_textField'], edit=True, text='< insert child module >',
                                                                                                font='obliqueLabelFont')
        cmds.button(self.uiVars['moduleUnparent_button'], edit=True, enable=False)
        cmds.button(self.uiVars['parentSnap_button'], edit=True, enable=False)
        cmds.button(self.uiVars['childSnap_button'], edit=True, enable=False)
        cmds.warning('MRT Error: Please select and insert a module as child.')


    def insertParentModuleNodeIntoField(self, *args):
        '''
        Inserts a selected scene module node nto the parent module textfield for module parenting.
        '''
        # Get selection, and get the selection module namespace, if valid.
        selection = cmds.ls(selection=True)
        if selection:
            lastSelection = selection[-1]
            namespaceInfo = mfunc.stripMRTNamespace(lastSelection)

            # If valid scene module, insert the parent module node into the textfield.
            if namespaceInfo != None:

                # Check the module node based on its type, before inserting it.
                moduleType = namespaceInfo[0].partition('__')[0]

                if moduleType == 'MRT_JointNode' or moduleType == 'MRT_SplineNode':
                    if cmds.nodeType(lastSelection) == 'joint':
                        cmds.textField(self.uiVars['selectedParent_textField'], edit=True, text=lastSelection, font='plainLabelFont')
                        cmds.button(self.uiVars['moduleParent_button'], edit=True, enable=True)
                        return
                    else:
                        cmds.warning('MRT Error: Please select and insert a module node as parent.')

                if moduleType == 'MRT_HingeNode':
                    if lastSelection.endswith('_control'):
                        cmds.textField(self.uiVars['selectedParent_textField'], edit=True, text=lastSelection, font='plainLabelFont')
                        cmds.button(self.uiVars['moduleParent_button'], edit=True, enable=True)
                        return
                    else:
                        cmds.warning('MRT Error: Please select and insert a module node as parent.')

        cmds.textField(self.uiVars['selectedParent_textField'], edit=True, text='< insert parent module node >', font='obliqueLabelFont')
        cmds.button(self.uiVars['moduleParent_button'], edit=True, enable=False)
        cmds.warning('MRT Error: Please select and insert a module node as parent.')


    def clearParentModuleField(self, *args):
        '''
        Clears parent module node textfield for module parenting.
        '''
        cmds.textField(self.uiVars['selectedParent_textField'], edit=True, text='< insert parent module node >', font='obliqueLabelFont')
        cmds.button(self.uiVars['moduleParent_button'], edit=True, enable=False)


    def clearChildModuleField(self, *args):
        '''
        Clears child module namespace textfield for module parenting.
        '''
        cmds.textField(self.uiVars['selectedChildModule_textField'], edit=True, text='< insert child module >', font='obliqueLabelFont')
        cmds.button(self.uiVars['moduleUnparent_button'], edit=True, enable=False)
        cmds.button(self.uiVars['parentSnap_button'], edit=True, enable=False)
        cmds.button(self.uiVars['childSnap_button'], edit=True, enable=False)


    def performUnparentForModule(self, *args):
        '''
        Remove parent module connections from a valid child module.
        '''
        # Store the current namespace, set to root.
        currentNamespace = cmds.namespaceInfo(currentNamespace=True)
        cmds.namespace(setNamespace=':')

        # Get the child module namespace.
        fieldInfo = cmds.textField(self.uiVars['selectedChildModule_textField'], query=True, text=True)

        # Get the current scene module namespaces.
        moduleNamespaces = mfunc.returnMRT_Namespaces(cmds.namespaceInfo(listOnlyNamespaces=True))

        # Check for scene and child module namespaces.
        if moduleNamespaces == None:
            cmds.warning('MRT Error: Module parenting conflict. No modules in the scene.')
            self.clearChildModuleField()
            return
        else:
            if not fieldInfo in moduleNamespaces:
                cmds.warning('MRT Error: Module parenting conflict. The child module doesn\'t exist.')
                self.clearChildModuleField()
                return

        # Remove the child module connections from parent module.
        cmds.lockNode(fieldInfo+':module_container', lock=False, lockUnpublished=False)
        constraint = cmds.listRelatives(fieldInfo+':moduleParentReprSegment_segmentCurve_endLocator', children=True,
                                                                                        fullPath=True, type='constraint')
        cmds.delete(constraint)

        # Hide representation for module parenting.
        cmds.setAttr(fieldInfo+':moduleGrp.moduleParent', 'None', type='string')
        cmds.setAttr(fieldInfo+':moduleParentReprGrp.visibility', 0)
        cmds.setAttr(fieldInfo+':moduleParentReprSegment_hierarchy_reprShape.overrideColor', 2)
        cmds.lockNode(fieldInfo+':module_container', lock=True, lockUnpublished=True)

        # Disable associated button states for working with parent module.
        cmds.button(self.uiVars['moduleUnparent_button'], edit=True, enable=False)
        cmds.button(self.uiVars['parentSnap_button'], edit=True, enable=False)
        cmds.button(self.uiVars['childSnap_button'], edit=True, enable=False)

        # Update scene module list.
        self.updateListForSceneModulesInUI()

        # Reset current namespace.
        cmds.namespace(setNamespace=currentNamespace)


    def performParentForModule(self, *args):
        '''
        Perform module parenting connections/settings for a child module from parent module node.
        '''
        # Save the current namespace.
        currentNamespace = cmds.namespaceInfo(currentNamespace=True)
        cmds.namespace(setNamespace=':')

        # Get the parent module node from the parent field for module parenting.
        parentFieldInfo = cmds.textField(self.uiVars['selectedParent_textField'], query=True, text=True)

        # If the parent module is a HingeNode module, get the appropriate node.
        if 'MRT_HingeNode' in parentFieldInfo:
            parentFieldInfo = parentFieldInfo.rpartition('_control')[0]

        # Get the parent module namespace.
        parentModuleNamespace = mfunc.stripMRTNamespace(parentFieldInfo)[0]

        # Get the child module namespace.
        childFieldInfo = cmds.textField(self.uiVars['selectedChildModule_textField'], query=True, text=True)
        if childFieldInfo == '< insert child module >':
            cmds.warning('MRT Error: Module parenting conflict. Insert a child module for parenting.')
            return

        # Get all module namespace.
        moduleNamespaces = mfunc.returnMRT_Namespaces(cmds.namespaceInfo(listOnlyNamespaces=True))

        # If no module(s) in the scene.
        if moduleNamespaces == None:
            cmds.warning('MRT Error: Module parenting conflict. No modules in the scene.')
            self.clearChildModuleField()
            return

        # Check if the parent and child module namespaces exist in the current scene.
        # This is not necessary, but a user can delete the modules after inserting them
        # into the module parenting fields. You never know haha.
        if not childFieldInfo in moduleNamespaces:
            cmds.warning('MRT Error: Module parenting conflict. The child module doesn\'t exist.')
            self.clearChildModuleField()
            return
        if not parentModuleNamespace in moduleNamespaces:
            cmds.warning('MRT Error: Module parenting conflict. The parent module doesn\'t exist.')
            self.clearParentModuleField()
            return

        # Check if the child module namespace equals parent module namespace.
        if mfunc.stripMRTNamespace(parentFieldInfo)[0] == childFieldInfo:
            cmds.warning('MRT Error: Module parenting conflict. Cannot parent a module on itself.')
            return

        # Check if the parent module node is already assigned.
        child_moduleParentInfo = cmds.getAttr(childFieldInfo+':moduleGrp.moduleParent')

        if child_moduleParentInfo != 'None':
            child_moduleParentInfo = child_moduleParentInfo.split(',')[0]
            child_moduleParentInfo = mfunc.stripMRTNamespace(child_moduleParentInfo)[0]

            if child_moduleParentInfo == parentModuleNamespace:
                cmds.warning('MRT Error: Module parenting conflict. The parent module node is already assigned as a parent.')
                return

        # Check if the parent module is already a child.
        parentModule_moduleParentInfo = cmds.getAttr(parentModuleNamespace+':moduleGrp.moduleParent')
        if parentModule_moduleParentInfo != 'None':

            parentModule_moduleParentInfo = parentModule_moduleParentInfo.split(',')[0]
            parentModule_moduleParentInfo = mfunc.stripMRTNamespace(parentModule_moduleParentInfo)[0]

            if parentModule_moduleParentInfo == childFieldInfo:
                cmds.warning('MRT Error: Module parenting conflict. The module to be parented is already a child.')
                return

        # Check if the parent module is a mirrored module for the child module.
        if cmds.attributeQuery('mirrorModuleNamespace', node=childFieldInfo+':moduleGrp', exists=True):

            if parentModuleNamespace == cmds.getAttr(childFieldInfo+':moduleGrp.mirrorModuleNamespace'):
                cmds.warning('MRT Error: Module parenting conflict. Cannot set up parenting inside mirror modules.')
                return

        # If the child module has an existing valid parent module node, unparent it before proceeding.
        if cmds.getAttr(childFieldInfo+':moduleGrp.moduleParent') != 'None':
            self.performUnparentForModule([])

        # Unlock and update the child module container.
        cmds.lockNode(childFieldInfo+':module_container', lock=False, lockUnpublished=False)
        mfunc.updateContainerNodes(childFieldInfo+':module_container')
        mfunc.updateContainerNodes(parentModuleNamespace+':module_container')

        # Set-up module parenting connections.
        moduleParentingConstraint = \
        cmds.pointConstraint(parentFieldInfo, childFieldInfo+':moduleParentReprSegment_segmentCurve_endLocator',
                             maintainOffset=False, name=childFieldInfo+':moduleParentReprSegment_endLocator_pointConstraint')[0]

        mfunc.addNodesToContainer(childFieldInfo+':module_container', [moduleParentingConstraint])

        # Set module parenting representation colour.
        parentType = cmds.radioCollection(self.uiVars['moduleParent_radioColl'], query=True, select=True)
        if parentType == 'Hierarchical':
            cmds.setAttr(childFieldInfo+':moduleParentReprSegment_hierarchy_reprShape.overrideColor', 16)
        cmds.setAttr(childFieldInfo+':moduleParentReprGrp.visibility', 1)

        # Update the "moduleParent" attribute on the child module.
        parentInfo = parentFieldInfo + ',' + parentType
        cmds.setAttr(childFieldInfo+':moduleGrp.moduleParent', parentInfo, type='string')

        # Lock the child module container.
        cmds.lockNode(childFieldInfo+':module_container', lock=True, lockUnpublished=True)

        # Set button states for post module parenting operations.
        cmds.button(self.uiVars['moduleUnparent_button'], edit=True, enable=True)
        cmds.button(self.uiVars['childSnap_button'], edit=True, enable=True)
        if not 'MRT_SplineNode' in parentFieldInfo:
            # The spline module nodes cannot be translated directly, unlike other module nodes.
            cmds.button(self.uiVars['parentSnap_button'], edit=True, enable=True)

        # Restore namespace
        cmds.namespace(setNamespace=currentNamespace)


    def performSnapParentToChild(self, *args):
        '''
        Transform the parent module node for a child module to the root child module node position.
        The child module is connected from its root to its parent module node.
        '''
        # Get the child module namespace.
        childFieldInfo = cmds.textField(self.uiVars['selectedChildModule_textField'], query=True, text=True)

        # Get the child module root node name.
        childRootNode = childFieldInfo+':root_node_transform'

        # Get the parent module node name.
        parentModuleNode = cmds.getAttr(childFieldInfo+':moduleGrp.moduleParent')
        parentModuleNode = parentModuleNode.split(',')[0]
        if 'MRT_HingeNode' in parentModuleNode:
            parentModuleNode = parentModuleNode + '_control'

        # Transform the parent module node.
        cmds.xform(parentModuleNode, worldSpace=True, absolute=True,
                   translation=cmds.xform(childRootNode, query=True, worldSpace=True, translation=True))


    def performSnapChildToParent(self, *args):
        '''
        Transform the child module root node to the parent module node position.
        '''
        # Get the child module namespace.
        childFieldInfo = cmds.textField(self.uiVars['selectedChildModule_textField'], query=True, text=True)

        # Get the child module root node name.
        if 'MRT_HingeNode' in childFieldInfo:
            childRootNode = childFieldInfo+':root_node_transform_control'
        elif 'MRT_SplineNode' in childFieldInfo:
            childRootNode = childFieldInfo+ ':spline_1_adjustCurve_transform'
        else:
            childRootNode = childFieldInfo+':root_node_transform'

        # Get the parent module node name.
        parentModuleNode = cmds.getAttr(childFieldInfo+':moduleGrp.moduleParent')
        parentModuleNode = parentModuleNode.split(',')[0]

        # Transform the child module root node.
        cmds.xform(childRootNode, worldSpace=True, absolute=True,
                   translation=cmds.xform(parentModuleNode, query=True, worldSpace=True, translation=True))


    # -------------------------------------------------------------------------------------------------------------
    #
    #   "RIG" TAB ITEM METHODS
    #
    # -------------------------------------------------------------------------------------------------------------

    # ............................................. CHARACTER CREATION .............................................

    def processCharacterFromScene(self, *args):
        '''
        Main procedure for creating character from scene module(s).
        '''
        # Check if a character exists in the scene.
        characterStatus = self.checkMRTcharacter()
        if characterStatus[0]:
            characterName = re.findall('^MRT_character(\D+)__mainGrp$', characterStatus[0])
            cmds.warning('MRT Error: Character "%s" exists in the scene, aborting.'%(characterName[0]))
            return

        # Check for valid character name entered by the user.
        characterName = cmds.textField(self.uiVars['characterName_textField'], query=True, text=True)
        if not str(characterName).isalnum():
            cmds.warning('MRT Error: Please enter a valid name for creating a character.')
            return
        # Or
        characterName = characterName.title()

        # Save current namespace, set to root.
        currentNamespace = cmds.namespaceInfo(currentNamespace=True)
        cmds.namespace(setNamespace=':')

        # Get the current scene modules.
        scene_modules = mfunc.returnMRT_Namespaces(cmds.namespaceInfo(listOnlyNamespaces=True))
        if not scene_modules:
            cmds.warning('MRT Error: No modules found in the scene to create a character.')
            return

        # Sort modules by their mirror namespaces (Mirrored namespaces are appended at the end).
        mrt_modules = []
        for module in scene_modules[:]:
            if cmds.getAttr(module+':moduleGrp.onPlane')[0] != '-':
                mrt_modules.append(module)
                index = scene_modules.index(module)
                scene_modules.pop(index)
        mrt_modules.extend(scene_modules)

        # Create the main character group.
        mainGrp = cmds.group(empty=True, name='MRT_character'+characterName+'__mainGrp')

        # Add an attribute to store the module collection file name for the scene modules used to
        # create the character (for auto module collection file).
        cmds.addAttr(mainGrp, dataType='string', longName='collectionFileID')

        # Add an attribute to store a string list of skin joints for the character.
        cmds.addAttr(mainGrp, dataType='string', longName='skinJointList')

        # Create the groups under the main character groups.
        jointsGrp = cmds.group(empty=True, name='MRT_character'+characterName+'__jointsMainGrp', parent=mainGrp)
        geoMainGrp = cmds.group(empty=True, name='MRT_character'+characterName+'__geometryMainGrp', parent=mainGrp)
        skinGeoGrp = cmds.group(empty=True, name='MRT_character'+characterName+'__skinGeometryGrp', parent=geoMainGrp)
        cntlGrp = cmds.group(empty=True, name='MRT_character'+characterName+'__controlGrp', parent=mainGrp)
        miscGrp = cmds.group(empty=True, name='MRT_character'+characterName+'__MiscGrp', parent=mainGrp)
        defGrp = cmds.group(empty=True, name='MRT_character'+characterName+'__DeformersGrp', parent=miscGrp)
        cmds.setAttr(defGrp+'.visibility', 0)

        # Create a group for character proxy geometry under the "geometry" main group.
        proxyMainGrp = cmds.group(empty=True, name='MRT_character'+characterName+'__proxyAllGeometryGrp', parent=geoMainGrp)

        # Create the display layers for the character.
        skinGeoLayerName = cmds.createDisplayLayer(empty=True, name='MRT_character'+characterName+'_skin_geometry', noRecurse=False)
        skinJointsLayerName = cmds.createDisplayLayer(empty=True, name='MRT_character'+characterName+'_all_joints', noRecurse=True)
        controlRigLayerName = cmds.createDisplayLayer(empty=True, name='MRT_character'+characterName+'_control_rig', noRecurse=False)

        cmds.select(clear=True)

        # Get a random name for the auto module collection file to be saved. This file is used by MRT to revert
        # back to scene modules from a character.
        fileId = reduce(lambda x,y:x+y, (random.random(), random.random(), random.random()))
        fileId = str(fileId).partition('.')[2]

        # Set the collection file id for the auto module collection file.
        cmds.setAttr(mainGrp+'.collectionFileID', fileId, type='string', lock=True)

        # Get the path for the auto module collection file.
        autoCharacterFile = self.autoCollections_path + '/character__%s.mrtmc'%(fileId)

        # Now, save an auto module collection file from scene modules.
        self.makeCollectionFromSceneTreeViewModulesUI(allModules=True, auto=autoCharacterFile)

        characterJointSet = []

        # Go through each scene module,
        for module in mrt_modules:

            # Get the module attributes/properties.
            moduleAttrsDict = mfunc.returnModuleAttrsFromScene(module)

            # Create the joint hierarchy from module.
            joints = mfunc.createSkeletonFromModule(moduleAttrsDict, characterName)

            # Collect and append the joint names for the joint hierarchy generated from module by:
            # ("<parent module node>,<parent type>", ["<child hierarchy root joint>", ..., "<child hierarchy end joint>"])
            # As an example:
            # ("MRT_JointNode__r_clavicle:root_node_transform,Constrained", ["MRT_characterNew__r_arm_root_node_transform",
            #                                                                "MRT_characterNew__r_arm_node_1_transform",
            #                                                                "MRT_characterNew__r_arm_end_node_transform"])
            # Also, the moduleAttrsDict['moduleParentInfo'] has the following data:
            # [[current module namespace, module parent info,
            #             [mirror module namespace, mirror module parent info (if this module has a mirrored module pair)]]
            characterJointSet.append( ( moduleAttrsDict['moduleParentInfo'][0][1], joints[:] ) )

            # If the module has proxy geometry, generate the proxy geometry for the joint hierarchy as well.
            #
            # The moduleAttrsDict['proxy_geo_options'] has a list with the following:
            # [ True if it contains bone proxy geo,
            #       True if it contains elbow proxy geo,
            #           elbow proxy type, 'sphere' or 'cube',
            #                  mirror instancing status for all module proxy geo ]
            #
            # The moduleAttrsDict['node_compnts'] has a list with the following:
            # [True for visibility of module hierarchy representation (set to True as  default),
            #       True for visibility of module node orientation representation (set to False as default),
            #               True for creation of proxy geometry (set as False as default)]
            #
            if moduleAttrsDict['node_compnts'][2] == True:
                # Create and return the proxy geo group for the joint hierarchy, if proxy geo exists for the module.
                proxyGrp = mfunc.createProxyForSkeletonFromModule(characterJointSet, moduleAttrsDict, characterName)
                if proxyGrp:
                    # Parent the proxy geo for the joint hierarchy under the main proxy geo group.
                    cmds.parent(proxyGrp, proxyMainGrp, absolute=True)

        # Delete all scene modules (not needed further).
        self.deleteAllSceneModules()

        # Set up parenting among discrete joint hierarchies generated from scene modules. This parenting
        # is either constrained or DAG type. This depends on the module parenting relationships set-up
        # earlier among scene modules ("Constrained" or "Hierarchical" module parenting).
        all_root_joints = mfunc.setupParentingForRawCharacterParts(characterJointSet, jointsGrp, characterName)

        # Find the root joints for all character joint hierarchies, parent them into the character joint group.
        characterJoints = []
        allJoints = cmds.ls(type='joint')
        for joint in allJoints:
            validJoint = self.returnValidFlagForCharacterJoint(joint)[0]
            if validJoint:
                characterJoints.append(joint)
                parent = cmds.listRelatives(joint, parent=True)
                if parent == None:
                    cmds.parent(joint, jointsGrp)

        # Set the string list attribute for storing character joints
        characterJointsAttr = ','.join(characterJoints)
        cmds.setAttr(mainGrp+'.skinJointList', characterJointsAttr, type='string', lock=True)

        # If the character has no proxy geometry, delete the proxy geo main group.
        proxyGrpChildren = cmds.listRelatives(proxyMainGrp, allDescendents=True)
        if proxyGrpChildren == None:
            cmds.delete(proxyMainGrp)

        # Create the character world and root transform controls.
        # "createRawCharacterTransformControl" returns [<root transform>, <world transform>]
        transforms = objects.createRawCharacterTransformControl()

        # Calculate and set the position and size for the character world transform,
        # based on the number and position of all character joints.
        avgBound = 6.0
        sumPos = [0.0, 0.0, 0.0]
        for joint in characterJoints:
            worldPos = cmds.xform(joint, query=True, worldSpace=True, translation=True)
            magWorldPos = math.sqrt(reduce(lambda x,y: x+y, [cmpnt**2 for cmpnt in worldPos]))
            if magWorldPos > avgBound:
                avgBound = magWorldPos
            sumPos = map(lambda x,y:x+y, worldPos, sumPos)
        sumPos = [item/len(characterJoints) for item in sumPos]
        sumPos[1] = 0.0
        scaleAdd = [x*avgBound*320 for x in [1.0, 1.0, 1.0]]

        # Set the default position and size of the character world transform.
        cmds.setAttr(transforms[1]+'.translate', *sumPos, type='double3')
        cmds.setAttr(transforms[1]+'.scale', *scaleAdd, type='double3')
        cmds.makeIdentity(transforms[1], scale=True, translate=True, apply=True)

        # Put the "globalScale" on the character root transform control.
        cmds.connectAttr(transforms[0]+'.scaleY', transforms[0]+'.scaleX')
        cmds.connectAttr(transforms[0]+'.scaleY', transforms[0]+'.scaleZ')
        cmds.aliasAttr('globalScale', transforms[0]+'.scaleY')
        cmds.setAttr(transforms[0]+'.scaleX', lock=True, keyable=False, channelBox=False)
        cmds.setAttr(transforms[0]+'.scaleZ', lock=True, keyable=False, channelBox=False)

        # Hide the scale attributes on the character world transform control.
        cmds.setAttr(transforms[1]+'.scaleX', keyable=False, lock=True)
        cmds.setAttr(transforms[1]+'.scaleY', keyable=False, lock=True)
        cmds.setAttr(transforms[1]+'.scaleZ', keyable=False, lock=True)
        cmds.parent(transforms[1], mainGrp, absolute=True)

        # Name the character root transform control.
        transforms[0] = cmds.rename(transforms[0], 'MRT_character'+characterName+transforms[0])

        # Name the character world transform control.
        transforms[1] = cmds.rename(transforms[1], 'MRT_character'+characterName+transforms[1])

        # Constrain all root joint hierarchies in a character to the character root transform.
        # Usually, there's only one root joint hierarchy (like spine in a biped). But there can be multiple.
        for joint in all_root_joints:
            cmds.parentConstraint(transforms[0], joint, maintainOffset=True, name=transforms[0]+'_'+joint+'__parentConstraint')

        # Connect the character "globalScale" to main joints group.
        cmds.connectAttr(transforms[0]+'.globalScale', 'MRT_character'+characterName+'__jointsMainGrp.scaleX')
        cmds.connectAttr(transforms[0]+'.globalScale', 'MRT_character'+characterName+'__jointsMainGrp.scaleY')
        cmds.connectAttr(transforms[0]+'.globalScale', 'MRT_character'+characterName+'__jointsMainGrp.scaleZ')

        cmds.select(clear=True)

        # Add the "rigLayers" attribute to all root joints for all character joint hierachies.
        # This attribute is used for parent/space switching operations.
        for joint in characterJoints:
            if re.search('_root_node_transform', joint):
                cmds.addAttr(joint, dataType='string', longName='rigLayers', keyable=False)
                cmds.setAttr(joint+'.rigLayers', 'None', type='string', lock=True)

        # Add the "skinGeometryGrp" to the "skin_geometry" display layer.
        cmds.editDisplayLayerMembers(skinGeoLayerName, skinGeoGrp)

        # Add all character joints to the all_joints display layer.
        cmds.editDisplayLayerMembers(skinJointsLayerName, *characterJoints)

        # Create an "FK bake" driver joint layer.
        result = mfunc.createFKlayerDriverOnJointHierarchy(characterJoints, 'FK_bake', characterName, False, 'None', True)

        # Add the "FK bake control layer" switch attribute on the character root control.
        # This attribute is for internal use only.
        cmds.addAttr(transforms[0], attributeType='float', longName='FK_Bake_Layer', hasMinValue=True, hasMaxValue=True,
                                                                    minValue=0, maxValue=1, defaultValue=0, keyable=False)
        # Go through the joints in the FK bake driver layer.
        for joint in result[0]:
            # Connect all the weights on the driver constraints for the "FK bake control layer" to
            # its attribute on the character root control.
            for constraint in result[1]:
                constrainResult = mfunc.returnConstraintWeightIndexForTransform(joint, constraint)
                if constrainResult:
                    cmds.connectAttr(transforms[0]+'.FK_Bake_Layer', constraint+'.'+constrainResult[1])

        # New control rig layer switch attribute(s) will be user keyable.
        cmds.addAttr(transforms[0], attributeType='enum', longName='CONTROL_RIGS', enumName=' ', keyable=True)
        cmds.setAttr(transforms[0]+'.CONTROL_RIGS', lock=True)

        # Add the character world transform and controlGrp to the "control_rig" display layer.
        cmds.select([transforms[1], cntlGrp])
        mel.eval('editDisplayLayerMembers -noRecurse MRT_character'+characterName+'_control_rig `ls -selection`;')

        cmds.select(clear=True)

        # Create a set for all character joints.
        cmds.select(characterJoints, replace=True)
        cmds.sets(name='MRT_character'+characterName+'__skinJointSet')

        # Reset namespace.
        if cmds.namespace(exists=currentNamespace):
            cmds.namespace(setNamespace=currentNamespace)

        # Post clean up.
        self.clearParentModuleField()
        self.clearChildModuleField()

        cmds.select(clear=True)


    def revertModulesFromCharacter(self, *args):
        '''
        Restores a character back to its scene modules. It uses the auto module collection file generated
        internally during character creation for this purpose
        '''
        # Check if a character exists in the scene.
        status = self.checkMRTcharacter()
        if not status[0]:
            cmds.warning('MRT Error: No character in the scene. Aborting.')
            return

        # If no auto module collection is found for the character, warn.
        if status[0] and status[1] == '':
            cmds.warning('MRT Error: Cannot find the auto-collection file containing the modules for ' \
                         'the current character. Unable to revert. Aborting')
            return

        # If the main character group and auto module collection file is found for the character.
        if status[0] and status[1] != '':

            characterName = status[0].partition('MRT_character')[2].rpartition('__')[0]
            charGeoGrp = 'MRT_character'+characterName + '__geometryMainGrp'
            charSkinGeoGrp = 'MRT_character'+characterName + '__deformersGrp'
            charDefGrp = 'MRT_character'+characterName + '__skinGeometryGrp'
            charMiscGrp = 'MRT_character'+characterName + '__miscGrp'
            proxyGeoGep = 'MRT_character'+characterName + '__proxyAllGeometryGrp'

            # Unparent the groups under the character main group to world.
            for obj in [charDefGrp, charSkinGeoGrp, charMiscGrp, charGeoGrp, proxyGeoGep]:
                if cmds.objExists(obj):
                    allChildren = cmds.listRelatives(obj, children=True) or []
                    if allChildren:
                        for child in allChildren:
                            if not re.match('^MRT_character\w+(DeformersGrp|skinGeometryGrp|proxyAllGeometryGrp|proxyGeoGrp)$', child):
                                cmds.parent(child, world=True)

            # Delete the main character group.
            cmds.delete(status[0])

            # Remove all display layers created for character.
            displayLayers = [item for item in cmds.ls(type='displayLayer') if re.match('^MRT_character[a-zA-Z0-9]*_\w+', item)]
            for layerName in displayLayers:
                if cmds.objExists(layerName):
                    cmds.delete(layerName)

            # Remove all control rig containers, if any, for the character.
            ctrl_containers = [item for item in cmds.ls(type='container') if re.match('^MRT_character[a-zA-Z0-9]*__\w+_Container$', item)]
            if ctrl_containers:
                cmds.delete(ctrl_containers)

            # Get the auto module collection file path for the character.
            autoFile = self.autoCollections_path + '/' + status[1] + '.mrtmc'

            # Install scene module(s) from the module collection file.
            self.installSelectedModuleCollectionToScene(autoInstallFile=autoFile)


    # ............................................. CHARACTER TEMPLATES ............................................

    def loadCharTemplatesForUI(self, charTemplatesFileList, clearCurrentList=False):
        '''
        Loads passed-in character templaes into the MRT UI. It also takes an argument if the current
        character template list is to be cleared.
        '''
        # Remove the items from the current template scroll list
        cmds.textScrollList(self.uiVars['charTemplates_txScList'], edit=True, height=32, removeAll=True)

        # Clear the current character template record list
        if clearCurrentList:
            self.charTemplateList = {}

        # If character template list is passed-in, re-build the character template scroll list.
        if len(charTemplatesFileList):
            for template in charTemplatesFileList:

                # Get the character template name suitable for the list from the template file name.
                templateName = re.split(r'\/|\\', template)[-1].rpartition('.')[0]

                # Skip if a template file exists in the list values.
                if template in self.charTemplateList.values():
                    continue

                # If the template name exist in the list, add a numerical suffix to it
                # Example:
                # templateName
                # templateName (2)
                if templateName in self.charTemplateList:
                    suffix = mfunc.findHighestCommonTextScrollListNameSuffix(templateName, self.charTemplateList.keys())
                    suffix = suffix + 1
                    templateName = '%s (%s)'%(templateName, suffix)

                # Save the template name as a key with its template file as value
                self.charTemplateList[templateName] = template

            # Get the height for the character template scroll list
            scrollHeight = len(self.charTemplateList) * 20
            if scrollHeight > 200:
                scrollHeight = 200
            if scrollHeight == 20:
                scrollHeight = 40

            # Add the character template names to the module collection scroll list
            for templateName in sorted(self.charTemplateList):
                cmds.textScrollList(self.uiVars['charTemplates_txScList'], edit=True, enable=True,
                                    height=scrollHeight, append=templateName, font='plainLabelFont',
                                    selectCommand=self.printCharTemplateInfoForUI)

            # Select the first item
            cmds.textScrollList(self.uiVars['charTemplates_txScList'], edit=True, selectIndexedItem=1)
            self.printCharTemplateInfoForUI()

        # If character template list is valid, save it, and enable UI buttons for importing, editing,
        # and deletion of character template(s) from the UI scroll list.
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
            # Enable buttons
            cmds.button(self.uiVars['charTemplate_button_import'], edit=True, enable=True)
            cmds.button(self.uiVars['charTemplate_button_edit'], edit=True, enable=True)
            cmds.button(self.uiVars['charTemplate_button_delete'], edit=True, enable=True)

        # If no character template is to be loaded
        if not len(self.charTemplateList):

            # Clear the saved character template data
            charTemplateList_file = open(self.charTemplateList_path, 'wb')
            cPickle.dump({}, charTemplateList_file, cPickle.HIGHEST_PROTOCOL)
            charTemplateList_file.close()

            # Clear the character template scroll list
            cmds.textScrollList(self.uiVars['charTemplates_txScList'], edit=True, enable=False,
                                    height=32, append=['              < no character template(s) loaded >'],
                                                                                        font='boldLabelFont')
            # Clear character template info field
            cmds.scrollField(self.uiVars['charTemplateDescrp_scrollField'], edit=True,
                                            text='< no collection info >', font='obliqueLabelFont',
                                                                            editable=False, height=32)

            # Disable buttons for importing, editing and deletion of character template(s)
            cmds.button(self.uiVars['charTemplate_button_import'], edit=True, enable=False)
            cmds.button(self.uiVars['charTemplate_button_edit'], edit=True, enable=False)
            cmds.button(self.uiVars['charTemplate_button_delete'], edit=True, enable=False)


    def printCharTemplateInfoForUI(self, *args):
        '''
        Prints the character template info for a selected item in the character template scroll list
        in the character template description field in the UI.
        '''
        # Get the current selected character template name
        selectedItem = cmds.textScrollList(self.uiVars['charTemplates_txScList'], query=True, selectItem=True)[0]

        # Get its template file
        templateFile = self.charTemplateList[selectedItem]

        # Get the character template description from its template file
        if os.path.exists(templateFile):
            # Get the character template data
            templateFileObj = open(templateFile, 'rb')
            templateFileData = cPickle.load(templateFileObj)
            templateFileObj.close()
            templateDescrp = templateFileData['templateDescription']    # Character template description

            # If description is valid, print it in the character template description field
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

                # Print it
                cmds.scrollField(self.uiVars['charTemplateDescrp_scrollField'], edit=True, text=templateDescrp,
                                                                        font='smallPlainLabelFont', height=infoScrollheight)
            else:
                # Invalid character template description
                cmds.scrollField(self.uiVars['charTemplateDescrp_scrollField'], edit=True, text='< no template info >',
                                                                        font='obliqueLabelFont', editable=False, height=32)
            return True
        else:
            # If the character template file for the selected character template name is not found, remove it from
            # the character template scroll list
            cmds.warning('MRT Error: Character template error. The selected character template file, "%s" cannot be found' \
                                                                                                'on disk.' % (templateFile))

            # Remove it from character template scroll list
            cmds.textScrollList(self.uiVars['charTemplateDescrp_scrollField'], edit=True, removeItem=selectedItem)

            # Remove it from character template records
            self.charTemplateList.pop(selectedItem)

            # Remove it from saved character template list data
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

            # Reset the character template description field
            cmds.scrollField(self.uiVars['charTemplateDescrp_scrollField'], edit=True, text='< no template info >',
                                                                        font='obliqueLabelFont', editable=False, height=32)

            # Check and update the character template list, if it contains any item(s) after removal
            allItems = cmds.textScrollList(self.uiVars['charTemplates_txScList'], query=True, allItems=True)
            if not allItems:
                cmds.textScrollList(self.uiVars['charTemplates_txScList'], edit=True, enable=False, height=32,
                                                append=['              < no character template(s) loaded >'],
                                                                                        font='boldLabelFont')

            # Disable buttons for importing, editing and deletion of character template(s)
            cmds.button(self.uiVars['charTemplate_button_import'], edit=True, enable=False)
            cmds.button(self.uiVars['charTemplate_button_edit'], edit=True, enable=False)
            cmds.button(self.uiVars['charTemplate_button_delete'], edit=True, enable=False)

            return False


    def importSelectedCharTemplate(self, *args):
        '''
        Imports a selected character template from the character template scroll list
        into the maya scene.
        '''
        # Save the current namespace, set to root.
        namespace = cmds.namespaceInfo(currentNamespace=True)
        cmds.namespace(setNamespace=':')

        # Check if a character exists in the current scene, skip importing if true.
        transforms = cmds.ls(type='transform')
        for transform in transforms:
            characterName = re.findall('^MRT_character(\D+)__mainGrp$', transform)
            if characterName:
                cmds.warning('MRT Error: The character "%s" exists in the scene. '  \
                                                                    'Unable to import a template.' % (characterName[0]))
                return

        # Skip importing if module(s) exist in the scene.
        moduleContainers = [item for item in cmds.ls(type='container') if mfunc.stripMRTNamespace(item)]
        if moduleContainers:
            cmds.warning('MRT Error: Module(s) were found in the scene; cannot import a character template. '   \
                                                                                'Try importing it in a new scene.')
            return

        # Get the selected character template
        selectedItem = cmds.textScrollList(self.uiVars['charTemplates_txScList'], query=True, selectItem=True)[0]

        # Get the associated character template, read its data.
        templateFile = self.charTemplateList[selectedItem]
        templateFileObj = open(templateFile, 'rb')
        templateFileData = cPickle.load(templateFileObj)
        templateFileObj.close()

        # Write a temporary maya scene file which will be used to import the character template.
        tempFilePath = templateFile.rpartition('.mrtct')[0]+'_temp.ma'
        tempFileObj = open(tempFilePath, 'w')

        # Write content to the maya scene file with the data from the character template file.
        for i in range(1, len(templateFileData)):
            tempFileObj.write(templateFileData['templateData_line_'+str(i)])
        tempFileObj.close()

        # Remove reference to the character template file object (for garbage collection)
        del templateFileData

        # Import the character template from the temporary maya scene file
        cmds.file(tempFilePath, i=True, type='mayaAscii', prompt=False, ignoreVersion=True)

        # Delete the maya scene file after import
        os.remove(tempFilePath)


    def editSelectedCharTemplateDescriptionFromUI(self, *args):
        '''
        Edits the character template description for a selected character template from the
        UI character template scroll list.
        '''
        def editDescriptionForSelectedCharTemplate(templateDescription, *args):
            # Performs / updates the changes to the character template description
            # from the UI field to the character template file.

            # Close the edit character template descrption window
            cancelEditCharTemplateNoDescrpErrorWindow()

            # Get the current selected character template name from UI scroll list
            selectedItem = cmds.textScrollList(self.uiVars['charTemplates_txScList'], query=True, selectItem=True)[0]

            # Get the corresponding character template file
            templateFile = self.charTemplateList[selectedItem]

            # Get character template data from the file
            templateFileObj = open(templateFile, 'rb')
            templateFileData = cPickle.load(templateFileObj)
            templateFileObj.close()

            # Update the character template description for the data wnd write it
            templateFileData['templateDescription'] = templateDescription
            templateFileObj = open(templateFile, 'wb')
            cPickle.dump(templateFileData, templateFileObj, cPickle.HIGHEST_PROTOCOL)
            templateFileObj.close()

            # Update the UI
            self.printCharTemplateInfoForUI()

        def cancelEditCharTemplateNoDescrpErrorWindow(*args):
            # Closes the edit character template description window
            cmds.deleteUI(self.uiVars['editCharTemplateDescrpWindow'])
            try:
                cmds.deleteUI(self.uiVars['editCharTemplateNoDescrpErrorWindow'])
            except:
                pass

        def checkEditDescriptionForSelectedCharTemplate(*args):
            # Checks the new character template description for saving / updating
            # Get the description
            templateDescription = cmds.scrollField(self.uiVars['editCharTemplateDescrpWindowScrollField'],
                                                                                                query=True, text=True)
            if templateDescription == '':
                # If no description is entered, create a warning window before proceeding
                self.uiVars['editCharTemplateNoDescrpErrorWindow'] = \
                    cmds.window('mrt_editCharTemplate_noDescrpError_UI_window', title='Character template warning',
                                                                                    maximizeButton=False, sizeable=False)
                # Remove the window from UI preferences
                try:
                    cmds.windowPref('mrt_editCharTemplate_noDescrpError_UI_window', remove=True)
                except:
                    pass

                # Main layout
                cmds.frameLayout(visible=True, borderVisible=False, collapsable=False, labelVisible=False, height=90,
                                                                            width=220, marginWidth=20, marginHeight=15)

                # Give the user a choice to save the character template description with
                # an empty value
                cmds.text(label='Are you sure you want to continue with an empty description?')
                cmds.rowLayout(numberOfColumns=2, columnAttach=([1, 'left', 55], [2, 'left', 20]),
                                                                            rowAttach=([1, 'top', 8], [2, 'top', 8]))
                cmds.button(label='Continue', width=90,
                                        command=partial(editDescriptionForSelectedCharTemplate, templateDescription))
                cmds.button(label='Cancel', width=90, command=cancelEditCharTemplateNoDescrpErrorWindow)

                # Show the window for warning
                cmds.showWindow(self.uiVars['editCharTemplateNoDescrpErrorWindow'])
            else:
                # Proceed saving with the new character template description
                editDescriptionForSelectedCharTemplate(templateDescription)

        # Check if the selected character template is valid.
        validItem = self.printCharTemplateInfoForUI()
        if not validItem:
            return

        # Close the edit character template description window if open
        try:
            cmds.deleteUI('mrt_charTemplateDescription_edit_UI_window')
        except:
            pass

        # Create the character template description window
        self.uiVars['editCharTemplateDescrpWindow'] = cmds.window('mrt_charTemplateDescription_edit_UI_window',
                                title='Character template description', height=150, maximizeButton=False, sizeable=False)

        # Remove the window from UI preference
        try:
            cmds.windowPref('mrt_charTemplateDescription_edit_UI_window', remove=True)
        except:
            pass

        # Main column
        self.uiVars['editCharTemplateDescrpWindowColumn'] = cmds.columnLayout(adjustableColumn=True)

        # Create the layout for the character template description field
        cmds.text(label='')
        cmds.text('Enter new description for character template', align='center', font='boldLabelFont')
        cmds.frameLayout(visible=True, borderVisible=False, collapsable=False, labelVisible=False, height=75, width=320,
                                                                                              marginWidth=5, marginHeight=10)

        # Get the current character template description from its file
        selectedItem = cmds.textScrollList(self.uiVars['charTemplates_txScList'], query=True, selectItem=True)[0]
        templateFile = self.charTemplateList[selectedItem]
        templateFileObj = open(templateFile, 'rb')
        templateFileData = cPickle.load(templateFileObj)
        currentDescriptionText = templateFileData['templateDescription']
        templateFileObj.close()

        # Create the field for character template description and set its value with the current description
        self.uiVars['editCharTemplateDescrpWindowScrollField'] = cmds.scrollField(preventOverride=True, wordWrap=True,
                                                                                              text=currentDescriptionText)

        # Create the layout and its button for updating the character template description from the field
        cmds.setParent(self.uiVars['editCharTemplateDescrpWindowColumn'])
        cmds.rowLayout(numberOfColumns=2, columnAttach=([1, 'left', 34], [2, 'left', 26]))
        cmds.button(label='Save description', width=130, command=checkEditDescriptionForSelectedCharTemplate)
        cmds.button(label='Cancel', width=90, command=partial(self.closeWindow, self.uiVars['editCharTemplateDescrpWindow']))

        # Set to the main UI column
        cmds.setParent(self.uiVars['editCharTemplateDescrpWindowColumn'])
        cmds.text(label='')

        # Show the edit character template description window
        cmds.showWindow(self.uiVars['editCharTemplateDescrpWindow'])


    def deleteSelectedCharTemplate(self, *args):
        '''
        Deletes a selected character template from the character template list in the MRT UI.
        '''
        def deleteCharTemplate(deleteFromDisk=False, *args):
            # This definition will be used only within the scope of deleteSelectedCharTemplate

            # If the character template is to be deleted, close the window
            cmds.deleteUI('mrt_deleteCharTemplate_UI_window')

            # Remove the character template name from the UI scroll list
            selectedItem = cmds.textScrollList(self.uiVars['charTemplates_txScList'], query=True, selectItem=True)[0]
            cmds.textScrollList(self.uiVars['charTemplates_txScList'], edit=True, removeItem=selectedItem)

            # Get its collection file
            templateFile = self.charTemplateList[selectedItem]

            # Remove it from character template records
            self.charTemplateList.pop(selectedItem)

            # Remove it from saved character template list data, save the new list
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

            # Remove the character template from disk if specified
            if deleteFromDisk:
                os.remove(templateFile)

            # After removing the character template name from the UI, check for item(s) in the module
            # collection scroll list
            allItems = cmds.textScrollList(self.uiVars['charTemplates_txScList'], query=True, allItems=True) or []

            # If item(s) are found, re-build the scroll list
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
                # If no item is found, reset and disable the character template scroll list with its buttons
                cmds.textScrollList(self.uiVars['charTemplates_txScList'], edit=True, enable=False,
                                height=32, append=['              < no character template(s) loaded >'], font='boldLabelFont')
                cmds.scrollField(self.uiVars['charTemplateDescrp_scrollField'], edit=True, text='< no template info >',
                                                                           font='obliqueLabelFont', editable=False, height=32)
                cmds.button(self.uiVars['charTemplate_button_import'], edit=True, enable=False)
                cmds.button(self.uiVars['charTemplate_button_edit'], edit=True, enable=False)
                cmds.button(self.uiVars['charTemplate_button_delete'], edit=True, enable=False)

        # Check if the selected character template is valid, meaning if it exists on disk.
        validItem = self.printCharTemplateInfoForUI()
        if not validItem:
            return

        # Delete the remove character template window, if it exists.
        try:
            cmds.deleteUI('mrt_deleteCharTemplate_UI_window')
        except:
            pass
        self.uiVars['deleteCharTemplateWindow'] = cmds.window('mrt_deleteCharTemplate_UI_window',
                                                     title='Delete character template', maximizeButton=False, sizeable=False)

        # Create the delete character template window.
        try:
            cmds.windowPref('mrt_deleteCharTemplate_UI_window', remove=True)
        except:
            pass

        # Create the main layout
        cmds.frameLayout(visible=True, borderVisible=False, collapsable=False, labelVisible=False, height=90, width=220,
                                                                                              marginWidth=20, marginHeight=15)

        # Create two buttons under a row, to delete the selected character template from disk or to
        # remove the character template frpm the UI scroll list only.
        cmds.rowLayout(numberOfColumns=2, columnAttach=([1, 'left', 0], [2, 'left', 20]))
        cmds.button(label='From disk', width=90, command=partial(deleteCharTemplate, True))
        cmds.button(label='Remove from list', width=120, command=deleteCharTemplate)
        cmds.showWindow(self.uiVars['deleteCharTemplateWindow'])


    def saveCharacterTemplate(self, *args):
        '''
        Saves a character template for an existing character in a scene. The character template must be saved
        before applying any control rigging.
        '''
        # NESTED DEF 1
        def saveCharTemplateFromDescriptionProcessInputUI(*args):
            '''
            Processes the character template description from UI to check if it's valid 
            for saving with a character template.
            '''
            # Check if a character exists in the scene.
            status = self.checkMRTcharacter()
            
            if not status[0]:
                cmds.warning('MRT Error: No character in the scene. Aborting.')
                
                # Close the character template description window
                cmds.deleteUI('mrt_charTemplateDescription_UI_window')
                return
                
            # Get the character template description entered by the user.
            templateDescription = cmds.scrollField(self.uiVars['charTemplateDescrpWindowScrollField'], query=True, text=True)
            
            # If the character template description string is empty,
            if templateDescription == '':
                try:
                    cmds.deleteUI('mrt_charTemplate_noDescpError_UI_window')
                except:
                    pass
                    
                # Create the check template description window
                self.uiVars['charTemplateDescrpErrorWindow'] = cmds.window('mrt_charTemplate_noDescpError_UI_window',
                                                title='Character template warning', maximizeButton=False, sizeable=False)
                try:
                    cmds.windowPref('mrt_charTemplate_noDescpError_UI_window', remove=True)
                except:
                    pass
                    
                cmds.frameLayout(visible=True, borderVisible=False, collapsable=False, labelVisible=False, height=90,
                                                                            width=220, marginWidth=20, marginHeight=15)
                         
                cmds.text(label='Are you sure you want to continue saving a character template with an empty description?')
                
                cmds.rowLayout(numberOfColumns=2, columnAttach=([1, 'left', 128], [2, 'left', 30]),
                                                                    rowAttach=([1, 'top', 8], [2, 'top', 8]))
                
                # If accepted, save the character template with an empty description.
                cmds.button(label='Continue', width=90,
                                    command=partial(saveCharTemplateFromDescription, templateDescription))
                
                # Else, close the window without saving character template.
                cmds.button(label='Revert', width=90,
                                    command=partial(self.closeWindow, self.uiVars['charTemplateDescrpErrorWindow']))
                
                cmds.showWindow(self.uiVars['charTemplateDescrpErrorWindow'])
                
            # If the character template description string is valid, save the character template with the description.
            else:
                saveCharTemplateFromDescription(True, templateDescription)
        
        # NESTED DEF 2
        def saveCharTemplateFromDescription(args, templateDescription):
            '''
            Saves a character template with the description entered by the user.
            '''
            # Close the check character template description window
            try:
                cmds.deleteUI('mrt_charTemplate_noDescpError_UI_window')
            except:
                pass
                
            # Close the character template description window
            try:
                cmds.deleteUI('mrt_charTemplateDescription_UI_window')
            except:
                pass
                
            # Check the current scene for character, if not, return.
            status = self.checkMRTcharacter()
            if not status[0]:
                cmds.warning('MRT Error: No character in the scene. Aborting.')
                return
                
            # Get the last directory accessed to save character template (saved as a preference)
            ui_preferences_file = open(self.ui_preferences_path, 'rb')
            ui_preferences = cPickle.load(ui_preferences_file)
            ui_preferences_file.close()
            startDirectory = ui_preferences['directoryForSavingCharacterTemplates']
            
            # If the directory doesn't exist, get the default directory
            if not os.path.exists(startDirectory):
                startDirectory = ui_preferences['defaultDirectoryForSavingCharacterTemplates']
            
            # Get the character template file name to be saved.
            fileFilter = 'MRT Character Template Files (*.mrtct)'
            fileReturn = cmds.fileDialog2(caption='Save character template', fileFilter=fileFilter,
                                                            startingDirectory=startDirectory, dialogStyle=2)
            # If no valid file name specified by the user.
            if fileReturn == None:
                return
                
            # Save the directory for saving character template file as a preference.
            ui_preferences['directoryForSavingCharacterTemplates'] = fileReturn[0].rpartition('/')[0]
            ui_preferences_file = open(self.ui_preferences_path, 'wb')
            cPickle.dump(ui_preferences, ui_preferences_file, cPickle.HIGHEST_PROTOCOL)
            ui_preferences_file.close()
            
            # If the character template file exists, remove it (for overwriting).
            if os.path.exists(fileReturn[0]):
                os.remove(fileReturn[0])

            # Get the description for the template file object.
            mrtct_fObject = {}
            mrtct_fObject['templateDescription'] = templateDescription
            
            # Now collect objects from the scene for the character template file.
            
            # Collect the character main group (returned by checkMRTcharacter)
            templateObjects = [status[0]]
            
            # Collect the proxy geometry display layer.
            characterName = status[0].partition('MRT_character')[2].rpartition('__')[0]
            layerName = 'MRT_character'+characterName+'_proxy_geometry'
            if cmds.objExists(layerName):
                templateObjects.append(layerName)
                
            # Collect the skinJointSet set.
            skinJointSet = 'MRT_character'+characterName+'__skinJointSet'
            templateObjects.append(skinJointSet)
            
            # Select the collected objects.
            cmds.select(templateObjects, replace=True, noExpand=True)
            
            # Save them temporarily in a maya scene.
            tempFilePath = fileReturn[0].rpartition('.mrtct')[0]+'_temp.ma'
            cmds.file(tempFilePath, force=True, options='v=1', type='mayaAscii', exportSelected=True, pr=True)
            
            # Add the maya scene contents to the template file object.
            tempFile_fObject = open(tempFilePath)
            for i, line in enumerate(tempFile_fObject):
                mrtct_fObject['templateData_line_'+str(i+1)] = line
            tempFile_fObject.close()
            
            # Remove the temporary maya scene file.
            os.remove(tempFilePath)
            
            # Now save the character template file.
            mrtct_fObject_file = open(fileReturn[0], 'wb')
            cPickle.dump(mrtct_fObject, mrtct_fObject_file, cPickle.HIGHEST_PROTOCOL)
            mrtct_fObject_file.close()
            del mrtct_fObject   # Remove the reference to file object.
            
            # Load the new saved character template into the UI scroll list, if preferred.
            ui_preferences_file = open(self.ui_preferences_path, 'rb')
            ui_preferences = cPickle.load(ui_preferences_file)
            ui_preferences_file.close()
            if ui_preferences['loadNewCharTemplatesToCurrentList']:
                self.loadCharTemplatesForUI(fileReturn)


        # MAIN DEF BEGINS
        
        # Save current selection.
        selection = cmds.ls(selection=True)
        
        # Save current namespace, set to root.
        namespace = cmds.namespaceInfo(currentNamespace=True)
        cmds.namespace(setNamespace=':')
        
        # Check if a character exists in the scene.
        status = self.checkMRTcharacter()
        if not status[0]:
            cmds.warning('MRT Error: No character in the scene. Aborting.')
            return
        
        # Check if any control rig is applied to the character before saving a template.
        # This can be done by finding any control rig attribute on the character root transform.
        allAttrs = cmds.listAttr(status[0].partition('mainGrp')[0]+'root_transform', visible=True, keyable=True)
        
        # Get the control rig attribute(s), if any.
        controlAttrs = set.symmetric_difference(set(['translateX', 'translateY', 'translateZ',
                                                     'rotateX', 'rotateY', 'rotateZ',
                                                     'globalScale', 'CONTROL_RIGS']), set(allAttrs))
        # If found,
        if len(controlAttrs):
            cmds.warning('MRT Error: One or more control rigs are currently applied to the character. ' \
                         'Detach them before saving a character template.')
            return
        
        # Bring up the window for entering the character template description.
        try:
            cmds.deleteUI('mrt_charTemplateDescription_UI_window')
        except:
            pass
        self.uiVars['charTemplateDescrpWindow'] = cmds.window('mrt_charTemplateDescription_UI_window',
                                                                title='Character template description',
                                                                    height=150, maximizeButton=False, sizeable=False)
        try:
            cmds.windowPref('mrt_charTemplateDescription_UI_window', remove=True)
        except:
            pass
            
        self.uiVars['charTemplateDescrpWindowColumn'] = cmds.columnLayout(adjustableColumn=True)
        
        cmds.text(label='')
        cmds.text('Enter description for character template', align='center', font='boldLabelFont')
        
        cmds.frameLayout(visible=True, borderVisible=False, collapsable=False, labelVisible=False, height=75,
                                                                            width=300, marginWidth=5, marginHeight=10)
                         
        self.uiVars['charTemplateDescrpWindowScrollField'] = cmds.scrollField(preventOverride=True, wordWrap=True)
        
        cmds.setParent(self.uiVars['charTemplateDescrpWindowColumn'])
        
        cmds.rowLayout(numberOfColumns=2, columnAttach=([1, 'left', 28], [2, 'left', 20]))
        
        # To process the character template description and save the character template (calls nested def).
        cmds.button(label='Save template', width=130, command=saveCharTemplateFromDescriptionProcessInputUI)
        
        cmds.button(label='Cancel', width=90, command=partial(self.closeWindow, self.uiVars['charTemplateDescrpWindow']))
        
        cmds.setParent(self.uiVars['charTemplateDescrpWindowColumn'])
        cmds.text(label='')
        
        cmds.showWindow(self.uiVars['charTemplateDescrpWindow'])
        
        # Restore namespace and selection.
        cmds.namespace(setNamespace=namespace)
        if not selection:
            cmds.select(clear=True)
        else:
            cmds.select(selection)


    # ............................................... CONTROL RIGGING ..............................................

    def displayControlRiggingOptionsAllWindow(self, *args):
        '''
        Brings up a window to display a list for currently available control rig type(s) that can be applied to
        character joint hierarchies.
        '''
        
        # Find derived control rig type classes from the "BaseJointControl" class (direct inheritance).
        control_types = [cls for cls in getattr(mrt_controlRig, 'BaseJointControl').__subclasses__()]

        if control_types:
        
            scrollTextString = '\n\t\t\t\t  < Available control rigging options for character hierarchy types >'.upper()
            
            for cls in control_types:
            
                # For each drived control rig type class, find the last subclass for it, if any.
                # This class will override the rig definitions, and will contain the latest updates
                # to the control rig type defined in the class directly inherited from the base "BaseJointControl" class.
                klass = mfunc.findLastSubClassForSuperClass(cls)

                # Make the title for the control rig type (from class name) for display.
                klassName = klass.__name__
                klass_p_name = klassName.capitalize()
                for char in klassName[1:]:
                    if char.isupper():
                        klass_p_name += ' ' + char
                    else:
                        klass_p_name += char
                        
                # Now add the title.
                scrollTextString += '\n\n\n' + klass_p_name
                scrollTextString += '\n' + '-' * len(klass_p_name) + '\n'
                
                # Get the class docstring for control rig type description.
                cls_string = cls.__doc__ or ''
                c_type_descrp = ''

                if cls_string:

                    cls_string_list = str.split(' '.join(cls_string.split('\n')))

                    docline_temp = ''

                    for item in cls_string_list:
                        c_type_descrp += item + ' '
                        docline_temp += item + ' '
                        if len(docline_temp) > 98:
                            docline_temp = ''
                            c_type_descrp += '\n'
                
                # Add the description for display.
                scrollTextString += c_type_descrp + '\n\n| Control rigging options |\n'
                
                # Get a list of rig definition names that can be applied under the control rig type.
                funcList = [item.partition('apply')[2].replace('_', ' ') for item in dir(cls)
                                                                            if re.match('^apply[A-Z]\D+$', item)]
                # Add the rig definition names for display.
                for i, func in enumerate(funcList):
                    scrollTextString += '\n%s. '% (i+1)
                    scrollTextString += func
            
            # Bring up the window to display the current rigging options.
            try:
                cmds.deleteUI('mrt_displayCtrlRigOptions_UI_window')
            except:
                pass
                
            self.uiVars['displayCtrlRigOptionsWindow'] = cmds.window('mrt_displayCtrlRigOptions_UI_window',
                            title='Control rigging options for character hierarchies', maximizeButton=False, width=760, height=300)
            try:
                cmds.windowPref(self.uiVars['displayCtrlRigOptionsWindow'], remove=True)
            except:
                pass
                
            self.uiVars['displayCtrlRigOptions_formLayout'] = cmds.formLayout()
            
            # Now display the string under "scrollTextString".
            self.uiVars['displayCtrlRigOptions_scrollField'] = cmds.scrollField(text=scrollTextString, editable=False,
                                                                                enableBackground=True, wordWrap=False)

            cmds.formLayout(self.uiVars['displayCtrlRigOptions_formLayout'], edit=True,
                                            attachForm=[(self.uiVars['displayCtrlRigOptions_scrollField'], 'top', 0),
                                                        (self.uiVars['displayCtrlRigOptions_scrollField'], 'left', 0),
                                                        (self.uiVars['displayCtrlRigOptions_scrollField'], 'right', 0),
                                                        (self.uiVars['displayCtrlRigOptions_scrollField'], 'bottom', 0)])
                         
            cmds.showWindow(self.uiVars['displayCtrlRigOptionsWindow'])


    def displayControlRiggingOptions(self, rootJoint='', customHierarchyTreeListString=None):
        '''
        Displays/updates the available control rig(s) under UI that can be applied or attached to a
        selected character joint hierarchy.
        
        Takes in the name of the root joint of the selected character hierarchy and
        "customHierarchyTreeListString" string value, if needed. This is used to match or identify 
        control rig(s) that can be applied to the selected joint hierarchy, if it's a custom 
        joint hierarchy created from modules with hierarchical module parenting.
        
        If it's not a custom joint hierarchy, then the control rig(s) are searched based
        on the type of module it was created from.
        
        Called from "viewControlRigOptionsOnHierarchySelection".
        '''
        # To store the control rig attributes for the selected joint hierarchy.
        self.controlRiggingAttributes = {}
        
        # Clear the current control rig list.
        cmds.textScrollList(self.uiVars['c_rig_txScList'], edit=True, height=32, removeAll=True)
        
        # If root joint name is passed-in
        if rootJoint:
            
            # To collect valid control rig classes identified for the joint hierarchy.
            control_klasses = []
            
            if customHierarchyTreeListString:
                # Get all control rig classes under the base class with class attribute
                # "customHierarchy" set to string value (default base value is set to None).
                customClasses = [cls for cls in getattr(mrt_controlRig, 'BaseJointControl').__subclasses__()
                                                    if eval('mrt_controlRig.%s.customHierarchy' % cls.__name__) != None]
                customClasses.sort()
                
                # Now find the class(es) that matches the input "customHierarchyTreeListString" string value.
                for cls in customClasses:

                    klass = mfunc.findLastSubClassForSuperClass(cls)

                    klassName = klass.__name__

                    h_string = eval('mrt_controlRig.%s.customHierarchy' % klassName)
                    if h_string == customHierarchyTreeListString:
                        control_klasses.append(klassName)
                
                # If multiple control rig classes are found for the custom joint hierarchy,
                if len(control_klasses):
                    control_klasses.sort()
                    
                    # Use the first control rig class from the list.
                    className = control_klasses[0]
                    
                    if len(control_klasses) > 1:
                        print '## MRT message: ' \
                              'Multiple user control rigging classes (%s) found for selected custom joint hierarchy. ' \
                              '##\n## Using \"%s\" control class for rigging options. ##' \
                                              % (', '.join(control_klasses), (className))
                    else:
                        print '## MRT message: Using \"%s\" control class for rigging custom hierarchy. ##' % (className)
                
                # If no control rig class is found.
                else:
                    className = 'JointControl'
                    print '## MRT message: No custom control rigging class found for selected custom hierarchy. ' \
                          'Using JointControl class. ##'
            
            # If the select joint hierarchy was created from a single module.
            else:
                # Get the module type for the selected joint hierarchy (It was created from).
                moduleType = cmds.getAttr(rootJoint+'.inheritedNodeType')
                numNodes = cmds.getAttr(rootJoint+'.numNodes')
                
                if moduleType != 'JointNode':
                    className = '%sControl'%(moduleType.partition('Node')[0])
                if moduleType == 'JointNode' and numNodes < 4:
                    className = 'JointControl'
                if moduleType == 'JointNode' and numNodes > 3:
                    className = 'JointChainControl'
                
                # If class name has subclass(es) that overrides it.
                subClasses = [cls for cls in eval('mrt_controlRig.%s' % (className)).__subclasses__()]

                if subClasses:
                    for cls in subClasses:
                        klass = mfunc.findLastSubClassForSuperClass(cls)
                        control_klasses.append(klass.__name__)
                    
                    # If multiple control rig classes are found for the joint hierarchy,
                    if len(control_klasses):
                        control_klasses.sort()
                        
                        # Use the first control rig class from the list.
                        className = control_klasses[0]
                        
                        if len(control_klasses) > 1:
                            print '## MRT message: ' \
                                  'Multiple user control rigging classes (%s) found for selected joint hierarchy. ' \
                                  '##\n## Using \"%s\" control class for rigging options. ##' \
                                                  % (', '.join(control_klasses), (className))
                        else:
                            print '## MRT message: Custom user control rigging class found for selected joint hierarchy. ' \
                                  '##\n## Using \"%s\" control class for rigging options. ##' % (className)
            
            # Now store the attributes for control rigging for the selected joint hierarchy.
            # Store the control rig class name
            self.controlRiggingAttributes['__klass__'] = '%s' % (className)
            
            # Get the control rig definitions that can be applied to the selected joint hierarchy.
            funcList = eval('[item for item in dir(mrt_controlRig.%s) if not re.search(\'__\', item)]'%(className))
            funcNameList = eval('[item.partition(\'apply\')[2].replace(\'_\', \' \') for item in dir(mrt_controlRig.%s) \
                                                                        if re.search(\'^apply[A-Z]\', item)]' % (className))
            # Store the control rig definitions under the attributes.
            for (funcName, func) in zip(funcNameList, funcList):
                self.controlRiggingAttributes[funcName] = func
            
            # Store the root joint for the selected joint hierarchy.
            self.controlRiggingAttributes['__rootJoint__'] = rootJoint

        if self.controlRiggingAttributes:
            # Get the control rig definitions stored previously under "self.controlRiggingAttributes".
            # They're stored as key names without '__' prefix/suffix.
            appendFuncList = [item for item in self.controlRiggingAttributes if item.find('__') == -1]
            
            # Get the list of control rig defitions currently applied to the selected joint hierarchy.
            atRigList = cmds.getAttr(rootJoint+'.rigLayers')
            if atRigList != 'None':
                atRigList = atRigList.split(',')
                atRigList = [item.replace('_', ' ') for item in atRigList]
                
                # Filter the control rig definitions not currently applied.
                appendFuncList = [item for item in appendFuncList if not item in atRigList]
            
            # Now update the control rig scroll list in the UI.
            # Get the height of the scroll list.
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
                
            # If no control rig defitions are found for the selected joint hierarchy.
            else:
                cmds.textScrollList(self.uiVars['c_rig_txScList'], edit=True, enable=True, height=32, 
                                    append=['         < No unattached rig(s) found for selected character hierarchy >'],
                                                                                                font='obliqueLabelFont')
                cmds.button(self.uiVars['c_rig_attachRigButton'], edit=True, enable=False)
                
        # If no control rig attributes are stored or generated (means bad inputs).
        else:
            cmds.textScrollList(self.uiVars['c_rig_txScList'], edit=True, enable=False, height=32, 
                                append=['        < select a character hierarchy to attach control rig(s) >'],
                                                                                                font='boldLabelFont')
            cmds.button(self.uiVars['c_rig_attachRigButton'], edit=True, enable=False)


    def attachSelectedControlRigToHierarchy(self, *args):
        '''
        Applies or attaches a control rig definition to a selected character joint hierarchy.
        '''
        # Get the selected joint hierarchy.
        selection = cmds.ls(selection=True)[-1]
        
        # Make sure the selection is not referenced.
        if cmds.ls(selection, referencedNodes=True):
            cmds.warning('MRT Error: Referenced object selected. Aborting.')
            return
            
        # Get the control rig definition to be applied from UI.
        selectFunc = cmds.textScrollList(self.uiVars['c_rig_txScList'], query=True, selectItem=True)[-1]
        
        # Use the data from "self.controlRiggingAttributes", which was generated previously.
        # Get the root joint name for the joint hierarchy.
        hierarchyRoot = self.controlRiggingAttributes['__rootJoint__']
        
        # Get the control rig(s) currently applied to the joint hierarchy.
        rigLayers = cmds.getAttr(hierarchyRoot+'.rigLayers')
        if rigLayers != 'None':
            rigLayers = rigLayers.split(',')
            for layer in rigLayers:
            
                # If the control rig definition is already applied.
                if selectFunc == layer:
                    cmds.warning('MRT Error: The control rig is already attached. Skipping.')
                    return
        
        # Get the control rig class for the joint hierarchy.
        controlClass = self.controlRiggingAttributes['__klass__']
        
        # Get the character name.
        characterName = selection.partition('__')[0].partition('MRT_character')[2]
        
        # Get the instance for the control rig class.
        controlRigInst = eval('mrt_controlRig.%s(characterName, hierarchyRoot)' % controlClass)
        
        # Get the control rig definition to be applied.
        controlRigApplyFunc = self.controlRiggingAttributes[selectFunc]
        
        # Apply the control rig definition to the selected joint hierarchy.
        eval('controlRigInst.%s()' % controlRigApplyFunc)
        del controlRigInst
        
        # Add the new control rig definition to the "rigLayers" attribute
        # on the root joint for the selected joint hierarchy.
        if isinstance(rigLayers, list):
            rigLayers.append(controlRigApplyFunc.split('apply')[1])
            rigLayers = ','.join(rigLayers)
            cmds.setAttr(hierarchyRoot+'.rigLayers', lock=False)
            cmds.setAttr(hierarchyRoot+'.rigLayers', rigLayers, type='string', lock=True)
        else:
            cmds.setAttr(hierarchyRoot+'.rigLayers', lock=False)
            cmds.setAttr(hierarchyRoot+'.rigLayers', controlRigApplyFunc.split('apply')[1], type='string', lock=True)
        
        # Update the UI.
        self.displayAttachedControlRigs(hierarchyRoot)
        cmds.select(selection)


    def removeSelectedControlRigFromHierarchy(self, *args):
        '''
        Detaches a control rig currently applied to a character joint hierarchy.
        '''
        # Temporarily disable DG cycle check.
        cy_check = cmds.cycleCheck(query=True, evaluation=True)
        if cy_check:
            cmds.cycleCheck(evaluation=False)

        # Check if the selection is referenced.
        selection = cmds.ls(selection=True)[-1]
        if cmds.ls(selection, referencedNodes=True):
            cmds.warning('MRT Error: Referenced object selected. Aborting.')
            return

        # Get the selected control rig to be detached.
        ctrlRigLayerName = cmds.textScrollList(self.uiVars['c_rig_attachedRigs_txScList'], query=True, selectItem=True)[-1]
        ctrlRigLayer = self.controlRiggingAttributes[ctrlRigLayerName].partition('apply')[2]
        hierarchyRoot = self.controlRiggingAttributes['__rootJoint__']
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

        # Get character root and world transform controls.
        rootCtrls = [item for item in cmds.ls(type='transform') 
                     if re.match('^MRT_character%s__(world|root){1}_transform$' % (characterName), item)]
        if rootCtrls:
            nodes.extend(rootCtrls)

        # Get all module containers.
        ctrl_containers = [item for item in cmds.ls(type='container') 
                           if re.match('^MRT_character%s__\w+_Container$'%(characterName), item)]
        if ctrl_containers:
            nodes.extend(ctrl_containers)

        # Remove anim on collected nodes.
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

        # Get all character joints.
        allJoints = cmds.getAttr('MRT_character'+characterName+'__mainGrp.skinJointList')
        allJoints = allJoints.split(',')

        # Force update on character joint attributes.
        for joint in allJoints:
            cmds.getAttr(joint+'.translate')
            cmds.getAttr(joint+'.rotate')
            cmds.getAttr(joint+'.scale')

        # Remove the control rig container
        ctrl_container = 'MRT_character{0}__{1}_{2}_Container'.format(characterName, userSpecName, ctrlRigLayer)

        # Get all character controls.
        allControlRigHandles = [item for item in cmds.ls(type='transform') 
                    if re.match('^MRT_character%s__%s_%s\w+handle$' % (characterName, userSpecName, ctrlRigLayer), item)]

        # Go through each character control.
        for handle in allControlRigHandles:

            # Get all child target character control(s) for current control, if they exist.
            # The current control may be a parent target for space switching for the child control.
            childTargetHandles = \
                set([item.rpartition('_parentSwitch_grp_parentConstraint')[0]
                    for item in cmds.listConnections(handle, destination=True)
                    if re.match('^MRT_character%s__\w+handle_parentSwitch_grp_parentConstraint$' % (characterName), item)])

            if childTargetHandles:

                for child in childTargetHandles:

                    # Remove the parent switch condition for the current parent character control.
                    parentSwitchCondition = child+'_'+handle+'_parentSwitch_condition'
                    cmds.delete(parentSwitchCondition)

                    # Get the parent name enum targets on child character control.
                    targets = cmds.addAttr(child+'.targetParents', query=True, enumName=True)
                    targets = targets.split(':')

                    # Remove current character control from enum parent switch list.
                    targets.remove(handle)

                    # Re-set the parent switch condition nodes for the child control.
                    for target in targets[1:]:  # Go through all enum target names, except the first, which is "None".
                        index = targets.index(target)
                        parentSwitchCondition = child+'_'+target+'_parentSwitch_condition'
                        cmds.setAttr(parentSwitchCondition+'.firstTerm', index)
                    if len(targets) > 0:
                        cmds.setAttr(child+'.targetParents', 1)
                    else:
                        cmds.setAttr(child+'.targetParents', 0)

                    # Update the parent target enum list.
                    cmds.addAttr(child+'.targetParents', edit=True, enumName=':'.join(targets))

                    # Remove constraint for space switching.
                    if cmds.objectType(child, isType='joint'):
                        cmds.orientConstraint(handle, child+'_parentSwitch_grp', edit=True, remove=True)
                    else:
                        cmds.parentConstraint(handle, child+'_parentSwitch_grp', edit=True, remove=True)

                    # Update the parent target transform list on the parent switch group for the child control.
                    currentTargets = cmds.getAttr(child+'_parentSwitch_grp.parentTargetList')
                    currentTargets = currentTargets.split(',')
                    currentTargets.remove(handle)
                    currentTargets = ','.join(currentTargets)
                    cmds.setAttr(child+'_parentSwitch_grp.parentTargetList', lock=False)
                    cmds.setAttr(child+'_parentSwitch_grp.parentTargetList', currentTargets, type='string', lock=True)

        # Remove all parent switch condition nodes for the control rig layer (which is to be deleted).
        allParentSwitchConditions = [item for item in cmds.ls(type='condition') if \
                                     re.match('^MRT_character%s__%s_%s_\w+_parentSwitch_condition$'
                                              % (characterName, userSpecName, ctrlRigLayer), item)]
        if allParentSwitchConditions:
            cmds.delete(allParentSwitchConditions)

        # Remove the control rig container.
        if cmds.objExists(ctrl_container):
            cmds.delete(ctrl_container)
        else:
            cmds.warning('MRT Error: No container found for the control rig to be removed. Please check the source ' \
                         'definition for the control rig.')

        # Remove the control rig layer attribute from charcater world transform control.
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

        # Reset selection.
        cmds.select(selection)

        # Reset display for current control rig(s) attached to the hierarchy.
        self.displayAttachedControlRigs(hierarchyRoot)

        # Enable DG cycle check.
        if cy_check:
            cmds.cycleCheck(evaluation=True)

        # Clear control textfield for Parent switching.
        self.clearParentSwitchControlField()


    def displayAttachedControlRigs(self, rootJoint):
        '''
        Displays the attached/applied control rig(s) on a character joint hierarchy under "Control rigging".
        Uses the "rigLayers" attribute on the root joint of the character hierarchy.
        '''
        # Clear current attached control rig list.
        cmds.textScrollList(self.uiVars['c_rig_attachedRigs_txScList'], edit=True, height=32, removeAll=True)

        # Get the "rigLayers" attribute from the root joint of the character hierarchy. This contains a string
        # list of control rigs(s) currently applied to the character hierarchy.
        if rootJoint:
            atRigList = cmds.getAttr(rootJoint+'.rigLayers')

            # If attached control rig(s) are found.
            if atRigList != 'None':

                # Set the height of the attached control rig scroll list based on the number of items.
                atRigList = atRigList.split(',')
                scrollHeight = len(atRigList) * 20
                if scrollHeight > 100:
                    scrollHeight = 100
                if scrollHeight == 20:
                    scrollHeight = 40

                # Append control rig entry to the scroll list.
                for layer in sorted(atRigList):
                    layer = layer.replace('_', ' ')
                    cmds.textScrollList(self.uiVars['c_rig_attachedRigs_txScList'], edit=True, enable=True, 
                                                                    append=layer, height=scrollHeight, font='plainLabelFont')
                cmds.textScrollList(self.uiVars['c_rig_attachedRigs_txScList'], edit=True, selectIndexedItem=1)
                cmds.button(self.uiVars['c_rig_removeRigButton'], edit=True, enable=True)

            # If no attached control rig is found.
            if atRigList == 'None':
                cmds.textScrollList(self.uiVars['c_rig_attachedRigs_txScList'], edit=True, enable=True, 
                         height=32, append=['              < No rig(s) attached to the selected character hierarchy >'],
                                                                                                font='obliqueLabelFont')
                cmds.button(self.uiVars['c_rig_removeRigButton'], edit=True, enable=False)

        # If no root joint is specified.
        else:
            cmds.textScrollList(self.uiVars['c_rig_attachedRigs_txScList'], edit=True, enable=False, 
                              height=32, append=['      < select a character hierarchy to remove attached rig(s) >'], 
                                                                                                font='boldLabelFont')
            cmds.button(self.uiVars['c_rig_removeRigButton'], edit=True, enable=False)


    def returnValidFlagForCharacterJoint(self, selection):
        '''
        Checks if a selected object (passed-in) is an MRT character joint.
        '''
        matchObjects = [re.compile('^MRT_character[a-zA-Z0-9]*__\w+_node_\d+_transform$'),
                        re.compile('^MRT_character[a-zA-Z0-9]*__\w+_root_node_transform$'),
                        re.compile('^MRT_character[a-zA-Z0-9]*__\w+_end_node_transform$')]

        for i, matchObject in enumerate(matchObjects):

            # Check if the object matches an MRT character joint name.
            matchResult = matchObject.match(selection)

            if matchResult:

                # If valid, return true with the index+1 of the matchObjects index.
                # This can be used to identify the joint name type.
                return True, i+1

        # Invalid MRT character joint.
        return False, 0


    def viewControlRigOptionsOnHierarchySelection(self):
        '''
        Called during selection to check if a character hierarchy is selected, to show available
        control rig(s) and attached control rig(s) on the character hierarchy.
        '''
        # Check for joint selection.
        selection = mel.eval('ls -sl -type joint')  # cmds module had issues with "ls" when executed via scriptJob
        if selection:
            selection = selection[-1]

            # Check if the selected joint belongs to an MRT character.
            status = self.returnValidFlagForCharacterJoint(selection)[0]

            if status:

                # Check for duplicated character joint(s) in the scene.
                char_joint_state = mfunc.checkForJointDuplication()

                # If there are no duplicated character joint(s) in the scene, proceed.
                if char_joint_state:

                    characterName = selection.partition('__')[0].partition('MRT_character')[2]
                    rootJoint = mfunc.returnRootForCharacterHierarchy(selection)
                    rootJointAllChildren = cmds.listRelatives(rootJoint, allDescendents=True, type='joint') or []

                    # Check for additional "root_node_transform" joint children. This might exist
                    # in a custom character joint hierarchy, created from module with hierarchical child module(s).
                    children_roots = [item for item in rootJointAllChildren if \
                                      re.match('^MRT_character\w+_root_node_transform$', item)]
                    if children_roots:

                        # Get the joint hierarchy data from the main root joint for the selected character hierarchy.
                        hierarchyTreeString = mfunc.returnHierarchyTreeListStringForCustomControlRigging(rootJoint)

                        # Get the control rigging options that can be applied to the custom joint hierarchy.
                        self.displayControlRiggingOptions(rootJoint, hierarchyTreeString)
                    else:
                        # If the character joint hierarchy is created from a module with no hierarchical child module(s).
                        self.displayControlRiggingOptions(rootJoint)

                    # Show attached control rig(s) on the selected character joint hierarchy.
                    self.displayAttachedControlRigs(rootJoint)

                # If duplicated character joint(s) in the scene.
                else:
                    self.displayControlRiggingOptions(None)
                    self.displayAttachedControlRigs(None)

            # If non-MRT character joint is selected.
            else:
                self.displayControlRiggingOptions(None)
                self.displayAttachedControlRigs(None)

        # No selection.
        else:
            self.displayControlRiggingOptions(None)
            self.displayAttachedControlRigs(None)


    # ............................................... PARENT SWITCHING ..............................................


    def insertValidSelectionForParentSwitching(self, *args):
        '''
        Checks for a valid character control to be inserted into the control field.
        '''
        selection = cmds.ls(selection=True)
        if selection:
            selection = selection[-1]
        else:
            return

        # Clear the text field for storing the character control for parent switching.
        self.clearParentSwitchControlField()

        # Check if a character control is selected.
        if re.match('^MRT_character[A-Za-z0-9]*__\w+_handle$', selection):

            # While selecting FK based control for assigning parent target(s), you can only select the root FK control.
            # Match for root: MRT_character[A-Za-z0-9]*__\w+_root_node_transform_handle
            if re.match('^MRT_character[A-Za-z0-9]*__\w+_(node_\d+_transform|end_node_transform){1}_handle$', selection):
                cmds.warning('MRT Error: Invalid control/object for assigning target parent controls. You can only select '\
                                                                                              'the root FK control handle.')
                return

            # If the character control has a valid pre-transform below the parent switch group.
            parent = cmds.listRelatives(selection, parent=True)[0]
            if re.match(selection+'_grp', parent):

                # Get the parent switch group
                self.controlParentSwitchGrp = selection + '_parentSwitch_grp'

                # Update the text field for character control (for parent switching)
                cmds.textField(self.uiVars['c_rig_prntSwitch_textField'], edit=True, text=selection, font='plainLabelFont')

                # Update the parent target list for existing parent target(s) on the character control
                self.updateListForExistingParentSwitchTargets()

                # Enable button state for adding parent targets.
                cmds.button(self.uiVars['c_rig_prntSwitch_addButton'], edit=True, enable=True)

            else:
                cmds.warning('MRT Error: Invalid control/object for parent switching. '
                             'The control transform has no parent switch group.')

                self.clearParentSwitchControlField()
        else:
            cmds.warning('MRT Error: Invalid control/object for assigning target parent controls. '
                         'You can only select a control transform (with suffix \'handle\').')

            self.clearParentSwitchControlField()


    def clearParentSwitchControlField(self, *args):
        '''
        Called to reset the UI states under "Parent Switching".
        '''
        # Reset the character control field to perform parent switching.
        cmds.textField(self.uiVars['c_rig_prntSwitch_textField'], edit=True, text='< insert control >',
                                                                                                font='obliqueLabelFont')
        # Disable associated button states
        cmds.button(self.uiVars['c_rig_prntSwitch_addButton'], edit=True, enable=False)
        cmds.button(self.uiVars['c_rig_prntSwitch_RemoveAll'], edit=True, enable=False)
        cmds.button(self.uiVars['c_rig_prntSwitch_RemoveSelected'], edit=True, enable=False)
        cmds.button(self.uiVars['c_rig_prntSwitch_createButton'], edit=True, enable=False)

        # Remove all items from parent target scroll list
        cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], edit=True, removeAll=True)
        cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], edit=True, enable=False,
                                         height=32, append=['\t           < no control inserted >'], font='boldLabelFont')

        # Empty records for current parent switch group and parent target list.
        self.controlParentSwitchGrp = None
        self.existingParentSwitchTargets = []


    def updateListForExistingParentSwitchTargets(self):
        '''
        Updates / populates the parent target scroll list for Parent switching. Uses existing parent switch
        targets for a character control.
        '''
        # Remove all existing items from the list.
        cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], edit=True, height=32, removeAll=True)

        # Get the parent target list ("parentTargetList" on parent switch group node for the character control).
        targetInfo = cmds.getAttr(self.controlParentSwitchGrp+'.parentTargetList')

        # Add parent target items to the scroll list. Adjust the scroll height based on the number of items.
        if targetInfo != 'None':

            targetInfoList = targetInfo.split(',')
            scrollHeight = len(targetInfoList) * 20
            if scrollHeight > 100:
                scrollHeight = 100
            if scrollHeight == 20:
                scrollHeight = 40

            if len(targetInfoList) > 0:
                for layer in sorted(targetInfoList):

                    # Character root control to be added as the first item in the parent target list
                    if re.match('^MRT_character[A-Za-z0-9]*__root_transform$', layer):
                        cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], edit=True, 
                                         enable=True, appendPosition=[1, layer], height=scrollHeight, font='plainLabelFont')
                    else:
                        # Add other parent targets
                        cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], edit=True, 
                                                      enable=True, append=layer, height=scrollHeight, font='plainLabelFont')

                    # Store/append existing parent targets
                    self.existingParentSwitchTargets.append(layer)

                # Select first item
                cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], edit=True, selectIndexedItem=1)

                # Update the "Remove selected" button status.
                self.postSelectionParentSwitchListItem()

                # Enable the "Remove All" button for clearing parent targets.
                cmds.button(self.uiVars['c_rig_prntSwitch_RemoveAll'], edit=True, enable=True)

        # If no existing parent target(s)
        else:
            cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], edit=True, enable=False,
                                            height=32, append='\t           < no current target(s) >', font='boldLabelFont')

        self.updateRemoveAllButtonStatForParentSwitching()


    def postSelectionParentSwitchListItem(self, *args):
        '''
        Updates the button state for "Remove selected" for Parent switching.
        '''
        # If a parent target is selected in the scroll list, set the button state to true, else false.
        selectedItem = cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], query=True, selectItem=True)
        if selectedItem:
            cmds.button(self.uiVars['c_rig_prntSwitch_RemoveSelected'], edit=True, enable=True)
        else:
            cmds.button(self.uiVars['c_rig_prntSwitch_RemoveSelected'], edit=True, enable=False)


    def addSelectedControlToTargetList(self, *args):
        '''
        Callback for "Add selected control to target list" button in Parent switching. Adds a selected character 
        control to the parent target list.
        '''
        # Check selection.
        selection = cmds.ls(selection=True)

        if selection:
            selection = selection[-1]
        else:
            return

        # If a character control or character root transform is selected (to be added as valid parent target).
        if re.match('^MRT_character[A-Za-z0-9]*__\w+_handle$', selection) or \
                                                    re.match('^MRT_character[A-Za-z0-9]*__root_transform$', selection):

            # Get the control to which parent target(s) are to be added.
            ins_control = cmds.textField(self.uiVars['c_rig_prntSwitch_textField'], query=True, text=True)

            characterName = selection.partition('__')[0].partition('MRT_character')[2]
            ins_control = ins_control.partition('__')[2]
            ins_control_h_name = re.split('_[A-Z]', ins_control)[0]
            
            # Get the root joint in its joint hierarchy.
            ins_control_rootJoint = 'MRT_character%s__%s_root_node_transform'%(characterName, ins_control_h_name)
            
            # If the selected control is not the character root transform
            if not re.match('^MRT_character[A-Za-z0-9]*__root_transform$', selection):

                selectionName = selection.partition('__')[2]
                selectionUserSpecName = re.split('_[A-Z]', selectionName)[0]
                rootJoint = 'MRT_character%s__%s_root_node_transform'%(characterName, selectionUserSpecName)
                
                # If the root joint for the joint hierarchy belonging to the selected control doesn't match.
                if rootJoint != ins_control_rootJoint:
                    
                    # Check if the joint hierarchy is not a descendent.
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
                                 'assigned to this hierarchy, it will have no effect.')

            # Now add the selection to the parent target list in the UI.
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
        '''
        Callback for "Remove selected" button under "Parent switching". Removes a selected parent target from parent
        target scroll list.
        '''
        # Remove the selected item from scroll list.
        selectedItem = cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], query=True, selectItem=True)[0]
        cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], edit=True, removeItem=selectedItem)

        # If there are no items left in the list, append the default item.
        allItems = cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], query=True, allItems=True) or []
        if not allItems:
            cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], edit=True, enable=False,
                                        height=32, append='\t           < no current target(s) >', font='boldLabelFont')

        # If there are item(s) in the parent target list that needs to be updated, get them.
        # (self.existingParentSwitchTargets) is a list of existing parent target(s).
        targetDiff = set.symmetric_difference(set(self.existingParentSwitchTargets), set(allItems))
        if len(targetDiff) > 0:
            cmds.button(self.uiVars['c_rig_prntSwitch_createButton'], edit=True, enable=True)
        else:
            cmds.button(self.uiVars['c_rig_prntSwitch_createButton'], edit=True, enable=False)

        # Disable the button state for removing selected parent target.
        cmds.button(self.uiVars['c_rig_prntSwitch_RemoveSelected'], edit=True, enable=False)

        # Update the target parent scroll list height based on the number of items.
        if len(allItems):
            scrollHeight = len(allItems)* 25
            if scrollHeight > 100:
                scrollHeight = 100
            if scrollHeight == 50:
                scrollHeight = 60
            if scrollHeight == 25:
                scrollHeight = 40
            cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], edit=True, height=scrollHeight)

            #self.postSelectionParentSwitchListItem()

        # Update state for "Remove All" parent targets button.
        self.updateRemoveAllButtonStatForParentSwitching()


    def removeAllTargetsFromParentSwitchList(self, *args):
        '''
        Callback for "Remove All" button for clearing all items in parent target scroll list under "Parent switching".
        '''
        # Clear the target parent list items.
        cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], edit=True, removeAll=True)

        # Add the default item, and set the height.
        cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], edit=True, enable=False,
                                                append='\t           < no current target(s) >', font='boldLabelFont')
        cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], edit=True, height=32)

        # Disable the associate button states.
        cmds.button(self.uiVars['c_rig_prntSwitch_createButton'], edit=True, enable=False)
        cmds.button(self.uiVars['c_rig_prntSwitch_RemoveAll'], edit=True, enable=False)


    def updateRemoveAllButtonStatForParentSwitching(self):
        '''
        Updates the button enable state for "Remove All" button in Parent switching under Rig tab.
        '''
        # If there are items in the parent switch target scroll list, proceed, or disable button state.
        allItems = cmds.textScrollList(self.uiVars['c_rig_prntSwitch_target_txScList'], query=True, allItems=True)
        if allItems:
            # If the list contains just the default item, disable button state
            if len(allItems) == 1 and re.findall('< no current target\(s\) >', allItems[0]):
                cmds.button(self.uiVars['c_rig_prntSwitch_RemoveAll'], edit=True, enable=False)
            else:
                cmds.button(self.uiVars['c_rig_prntSwitch_RemoveAll'], edit=True, enable=True)
        else:
            cmds.button(self.uiVars['c_rig_prntSwitch_RemoveAll'], edit=True, enable=False)


    def createParentSwitchGroupforControlHandle(self, *args):
        '''
        Creates the transform for a character control for constraining in space switching use. It 
        receives constraints from parent controls added as parent switches.
        '''
        # Check selection
        selection = cmds.ls(selection=True) or ' '
        if selection:
            selection = selection[-1]

        # Check if the selected object is a character control
        if re.match('^MRT_character[A-Za-z0-9]*__\w+_handle$', selection):

            # Check if the character control has a parent switch group
            transformParent = cmds.listRelatives(selection, parent=True)
            if transformParent:
                if re.match(selection+'_grp', transformParent[0]):
                    cmds.warning('MRT Error: The selected control handle already has parent switch group. Skipping')
                    return
        else:
            cmds.warning('MRT Error: Invalid selection. Please select a valid character control.')
            return

        characterName = selection.partition('__')[0].partition('MRT_character')[2]
        selectionName = selection.partition('__')[2]
        selectionUserSpecName = re.split('_[A-Z]', selectionName)[0]
        rootJoint = 'MRT_character%s__%s_root_node_transform'%(characterName, selectionUserSpecName)

        # Create the parent switch group node which will receive the constraints from parent transforms.
        parentSwitch_grp = cmds.group(empty=True, name=selection + '_parentSwitch_grp')
        tempConstraint = cmds.parentConstraint(selection, parentSwitch_grp, maintainOffset=False)[0]
        cmds.delete(tempConstraint)

        # Add custom attributes to the group node, and create a child transform to contain the main transform
        # (for which the parent switch group is being created).

        # Create an enum attribute on the character control (to be updated later to add parent names for user switching)
        cmds.addAttr(selection, attributeType='enum', longName='targetParents', enumName=' ', keyable=True)
        cmds.setAttr(selection+'.targetParents', lock=True)

        # Create string attribute on parent switch group node to store parent node list
        cmds.addAttr(parentSwitch_grp, dataType='string', longName='parentTargetList', keyable=False)
        cmds.setAttr(parentSwitch_grp+'.parentTargetList', 'None', type='string', lock=True)

        # Create a pre-transform for the character control, to be placed below the parent switch group.
        transform_grp = cmds.duplicate(parentSwitch_grp, parentOnly=True, name=selection+'_grp')[0]

        # If the character control has a parent, get it.
        transformParent = cmds.listRelatives(selection, parent=True)
        if transformParent:
            cmds.parent(parentSwitch_grp, transformParent[0], absolute=True)

        # Parent the control pre-transform below the parent switch group.
        cmds.parent(transform_grp, parentSwitch_grp, absolute=True)

        # Parent the control below its pre-transform
        cmds.parent(selection, transform_grp, absolute=True)

        # Add the control pre-transform and the parent switch group to the control's container.
        controlContainer = cmds.container(selection, query=True, findContainer=True)
        mfunc.addNodesToContainer(controlContainer, [parentSwitch_grp, transform_grp])


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
                
                # Create the parent switch condition
                parentSwitchCondition = cmds.createNode('condition', name=ss_control+'_'+target+'_parentSwitch_condition',
                                                                                                          skipSelect=True)
                # Connect the condition to drive the constraint weight for the new parent target.
                index = attrs.count(':')
                cmds.setAttr(parentSwitchCondition+'.firstTerm', index)
                cmds.connectAttr(ss_control+'.targetParents', parentSwitchCondition+'.secondTerm')
                cmds.setAttr(parentSwitchCondition+'.colorIfTrueR', 1)
                cmds.setAttr(parentSwitchCondition+'.colorIfFalseR', 0)
                weightIndex, ctrlAttr = mfunc.returnConstraintWeightIndexForTransform(target, constraint)
                cmds.connectAttr(parentSwitchCondition+'.outColorR', constraint+'.'+ctrlAttr)
                
                # Update the parent target string list on the control parent switch group.
                currentTargets = cmds.getAttr(self.controlParentSwitchGrp+'.parentTargetList')
                if currentTargets != 'None':
                    currentTargets = currentTargets+','+target
                    cmds.setAttr(self.controlParentSwitchGrp+'.parentTargetList', lock=False)
                    cmds.setAttr(self.controlParentSwitchGrp+'.parentTargetList', currentTargets, type='string', lock=True)
                else:
                    cmds.setAttr(self.controlParentSwitchGrp+'.parentTargetList', lock=False)
                    cmds.setAttr(self.controlParentSwitchGrp+'.parentTargetList', target, type='string', lock=True)
        
        # Check if the parent target string list is valid after updates
        targetInfo = cmds.getAttr(self.controlParentSwitchGrp+'.parentTargetList')
        if not targetInfo:
            cmds.setAttr(self.controlParentSwitchGrp+'.parentTargetList', lock=False)
            cmds.setAttr(self.controlParentSwitchGrp+'.parentTargetList', 'None', type='string', lock=True)
        
        # Refresh the parent target indices in all parent switch conditions for the control
        allAttrs = cmds.addAttr(ss_control+'.targetParents', query=True, enumName=True)
        allAttrs = allAttrs.split(':')
        for attr in allAttrs[1:]:
            index = allAttrs.index(attr)
            parentSwitchCondition = ss_control+'_'+attr+'_parentSwitch_condition'
            cmds.setAttr(parentSwitchCondition+'.firstTerm', index)
        
        # Set the default parent target
        if len(allAttrs) == 1:
            cmds.setAttr(ss_control+'.targetParents', 0)
        if len(allAttrs) > 1:
            cmds.setAttr(ss_control+'.targetParents', 1)
        
        # Cleanup
        self.clearParentSwitchControlField()
        cmds.select(ss_control, replace=True)
        self.insertValidSelectionForParentSwitching()