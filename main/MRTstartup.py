# *************************************************************************************************************
#
#    MRTstartup.py - Init functions for Modular rigging tools for Maya. 
#                    Runs startup checks to see MRT is correctly installed and supported.
#
#    This file should be placed under the maya scripts directory.
#
#    Can be modified or copied for your own purpose.
#
#    Written by Himanish Bhattacharya 
#
# *************************************************************************************************************

__moduleName__ = 'mrt_startup'

import os, sys
import maya.cmds as cmds

def runMRTstartup(__debug = 0):
    """
    Runs with the MRT mel call. This function is executed from this file separate from MRT package import files.
    Does startup checks, to see MRT is supported for the current maya version.
    Set the __debug to 1 to refresh all /MRT .pyc files.
    """
    # IN-SCOPE DEF
    def postInstallDialog():
        '''
        Displays a dialog window to confirm the installation for MRT.
        '''

        dialogWin = cmds.window(title='MRT Start Up', resizeToFitChildren=True, 
                                        maximizeButton=False, minimizeButton=False, sizeable=False)
        
        mainCol = cmds.columnLayout(width=500, rowSpacing=15)
        
        cmds.separator(style='none')
        cmds.text(label='Modular rigging tools has been installed.', align='center', width=400)
        cmds.text(label='Please restart maya.', font='boldLabelFont', align='center', width=400)
        
        cmds.rowLayout(numberOfColumns=2, columnWidth=[(1, 150), (2, 100)])
        
        cmds.separator(style='none')
        cmds.button(label='OK', command=('import maya.cmds; maya.cmds.deleteUI(\"'+dialogWin+'\")'), width=100, align='center')
        
        cmds.setParent(mainCol)
        cmds.separator(style='none')
        cmds.showWindow(dialogWin)
        
        try: cmds.windowPref(dialogWin, remove=True) 
        except: pass


    # MAIN DEF BEGINS
    
    # Working MRT scripts directory.
    workingDir = cmds.internalVar(userScriptDir=True) + 'mrt/'
    
    # Check if this directory exists in sys.path and add it. 
    # Initialize an instance of the UI class and run startup functions.
    if os.path.exists(workingDir):
        if not workingDir in sys.path:
            sys.path.append(workingDir)
        
        # Run the MRT error handler.
        import mrt_errorHandle
        
        # Get the startup functions
        import mrt_functions

        # Prep the mrt_controlRig.py source
        mrt_functions.prep_MRTcontrolRig_source()
        
        if __debug:
            reload(mrt_functions)
            import mrt_module; reload(mrt_module)
            import mrt_objects; reload(mrt_objects)
            import mrt_UI; reload(mrt_UI)
        
        # See if the xHandleShape plugin can be loaded. Print warning if otherwise.
        stat = mrt_functions.loadXhandleShapePlugin()
        if not stat:
            return

        # Check if MRT is being loaded for the first time. If true, configure it.
        firstLoadStatus = mrt_functions.prep_MRTMayaStartupActions()

        # If MRT is configured to run, load the UI.
        if firstLoadStatus[0] == False and firstLoadStatus[1] == False:
            
            import mrt_UI
            mrt_UI.MRT_UI()
        else:
            postInstallDialog()
    
    # If scripts/MRT directory not found, warn if it doesn't exist. 
    else:
        sys.stderr.write('Please copy the files for MRT to their appropriate directories. Aborting.')