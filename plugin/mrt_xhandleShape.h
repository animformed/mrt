/*

    PLUGIN: mrt_xhandleShape v1.0
 
    mrt_xhandleShape.h
    
    ////////////////////////////////////////////////////////////////////////////
 
    Source for xhandleShape node plugin class declaration.

    This is derived from an MPxLocatorNode, with the following
    added attributes :

    addScaleX
    addScaleY
    addScaleZ
    drawStyle
    drawAxisColour
    drawOrtho
    transformScaling
    wireframeThickness
    blendColour
    
    ////////////////////////////////////////////////////////////////////////////
    
    Feel free to modify, extend or copy for your own purpose.
    
    Written by Himanish Bhattacharya

*/

// Maya Libs

# include <maya/MTypeId.h>
# include <maya/MPxLocatorNode.h> 
//# include <maya/M3dView.h>
//# include <maya/MMatrix.h>
//# include <maya/MTransformationMatrix.h>
//# include <maya/MQuaternion.h>
//# include <maya/MDagPath.h>
//# include <maya/MFnTransform.h>
//# include <maya/MFnDependencyNode.h>
//# include <maya/MFnNumericAttribute.h>
//# include <maya/MFnEnumAttribute.h>
//# include <maya/MFnPlugin.h>
//# include <maya/MDistance.h>
//# include <maya/MPlug.h>
//# include <maya/MHardwareRenderer.h>


class xhandleShape : public MPxLocatorNode
{
	public:
    
        // Member functions
    
		xhandleShape();
    
		virtual	~xhandleShape();
    
		virtual void postConstructor();
    
        static void* creator();
    
        static MStatus initialize();
    
		virtual MStatus compute(const MPlug& plug, MDataBlock& data);
    
		virtual void draw(M3dView &view, const MDagPath &path,
                          M3dView::DisplayStyle style, M3dView::DisplayStatus status);
    
		virtual void drawShapes(short enumType, bool drawWire, float unit_multiplier,
                                     GLfloat w_size, short drawOrtho, bool selection);
    
		virtual bool isBounded() const;
    
		virtual MBoundingBox boundingBox() const;
    
    
        // Data
    
		static MTypeId id;

		static MObject aAddScaleX;
    
		static MObject aAddScaleY;
    
		static MObject aAddScaleZ;
		
		static MObject aDrawOrtho;
    
		static MObject aDrawStyle;
    
		static MObject aThickness;
    
		static MObject aTransformScaling;
    
		static MObject aBlendHColour;
    
		static MObject aDrawAxColour;
		
        static MDataBlock& block;
    
	protected:
    
		MGLFunctionTable *gGLFT;
};
