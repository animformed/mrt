/*

    PLUGIN: xhandleShape v1.0
 
    xhandleShapePlugin.cpp
 
    ////////////////////////////////////////////////////////////////////////////

    Plugin registration/de-registration for xhandleShape node.
    
    ////////////////////////////////////////////////////////////////////////////
    
    Feel free to modify, extend or copy for your own purpose.
    
    Written by Himanish Bhattacharya

*/


# include "xhandleShape.h"
# include <maya/MFnPlugin.h>

MStatus initializePlugin(MObject obj)   // Register the plugin
{
    MStatus status;
    MFnPlugin plugin(obj, "hb", "1.0", "2014");

    status = plugin.registerNode("xhandleShape",
                                 xhandleShape::id,
                                 &xhandleShape::creator,
                                 &xhandleShape::initialize,
                                 MPxNode::kLocatorNode);   
    if (!status) {
        status.perror("Failed to register node \"xhandleShape\"");
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

    return status;
}