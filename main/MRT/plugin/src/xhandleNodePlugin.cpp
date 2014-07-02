/*

    PLUGIN: xhandleNodePlugin v1.0
 
    xhandleNodePlugin.cpp
 
    ////////////////////////////////////////////////////////////////////////////

    Plugin and command registration/de-registration for xhandleShape node.
    
    ////////////////////////////////////////////////////////////////////////////
    
    Feel free to modify, extend or copy for your own purpose.
    
    Written by Himanish Bhattacharya

*/


# include "xhandleNode.h"
# include <maya/MFnPlugin.h>

MStatus initializePlugin(MObject obj)   // Register the plugin
{
    MStatus status;
    MFnPlugin plugin(obj, "hb", "1.0", "2014");

    status = plugin.registerNode("xhandleShape",
                                 xhandleShape::id,
                                 xhandleShape::creator,
                                 xhandleShape::initialize,
                                 MPxNode::kLocatorNode);   
    if (!status) {
        
        status.perror("Failed to register node \"xhandleShape\"");
        return status; 
    }
    
    status = plugin.registerCommand("xhandle", xhandle::creator);
    
    if (!status) {
        
        status.perror("Failed to register command \"xhandle\"");
        return status;
    }
    
    return status;
}


MStatus uninitializePlugin(MObject obj)     // De-register the plugin
{
    MStatus status;
    MFnPlugin plugin(obj);

    status = plugin.deregisterNode(xhandleShape::id);

    if (!status) {
        
        status.perror("Failed to de-register node \"xhandleShape\"");
        return status;
    }
    
    status = plugin.deregisterCommand("xhandle");
    
    if (!status) {
        
        status.perror("Failed to de-register command \"xhandle\"");
        return status;
    }

    return status;
}