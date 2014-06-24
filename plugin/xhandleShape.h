/*

    PLUGIN: xhandleShape v1.0
    
    xhandleShape.h
    
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

// Maya libs

# include <maya/MTypeId.h>
# include <maya/MPxLocatorNode.h>
# include <maya/M3dView.h>
# include <maya/MMatrix.h>
# include <maya/MTransformationMatrix.h>
# include <maya/MQuaternion.h>
# include <maya/MDagPath.h>
# include <maya/MFnDagNode.h>
# include <maya/MFnNumericAttribute.h>
# include <maya/MFnEnumAttribute.h>
# include <maya/MDistance.h>
# include <maya/MIOStream.h>
# include <maya/MHardwareRenderer.h>
# include <maya/MGLFunctionTable.h>
# include <maya/MGlobal.h>

# define RAD_TO_DEG(rad) (rad * 57.2957795130f)

// Vertex points for draw

static GLfloat handle_low[][3] = { {0.41f, 1.0f, 0.0f},
                                   {1.0f, 0.41f, 0.0f},
                                   {1.0f, -0.41f, 0.0f},
                                   {0.41f, -1.0f, 0.0f},
                                   {-0.41f, -1.0f, 0.0f},
                                   {-1.0f, -0.41f, 0.0f},
                                   {-1.0f, 0.41f, 0.0f},
                                   {-0.41f, 1.0f, 0.0f} };
                                    
static GLfloat handle_high[][3] = { {0.15f, 0.0f, 0.0f},
                                    {0.139f, 0.057f, 0.0f},
                                    {0.106f, 0.106f, 0.0f},
                                    {0.058f, 0.138f, 0.0f},
                                    {0.001f, 0.15f, 0.0f},
                                    {-0.057f, 0.139f, 0.0f},
                                    {-0.105f, 0.107f, 0.0f},
                                    {-0.138f, 0.058f, 0.0f},
                                    {-0.15f, 0.001f, 0.0f},
                                    {-0.139f, -0.056f, 0.0f},
                                    {-0.107f, -0.105f, 0.0f},
                                    {-0.059f, -0.138f, 0.0f},
                                    {-0.002f, -0.15f, 0.0f},
                                    {0.055f, -0.139f, 0.0f},
                                    {0.104f, -0.108f, 0.0f},
                                    {0.138f, -0.06f, 0.0f} };


// Node class declaration

class xhandleShape : public MPxLocatorNode
{
    public:
        
        // Member functions
        
        xhandleShape();
        
        virtual ~xhandleShape();
        
        static void* creator();
        
        static MStatus initialize();
        
        virtual MStatus compute(const MPlug& plug, MDataBlock& data);
    
        virtual void setInternalAttrs() const;
    
        virtual void drawShapes(bool selection);
    
        virtual void draw(M3dView &view, const MDagPath &path,
                          M3dView::DisplayStyle style, M3dView::DisplayStatus status);
    
        virtual bool isBounded() const;
        
        virtual MBoundingBox boundingBox() const;
    
    
        // Data
        
        static MTypeId id;
    
        static double l_positionX;
        static double l_positionY;
        static double l_positionZ;
        
        static double add_scaleX;
        static double add_scaleY;
        static double add_scaleZ;
        
        static double l_scaleX;
        static double l_scaleY;
        static double l_scaleZ;
        
        static bool dDrawOrtho;
        
        static int dDrawStyle;
        
        static GLfloat dThickness;
        
        static bool dTransformScaling;
        
        static bool dBlendHColour;
        
        static bool dDrawAxColour;
        
        static GLfloat uMult;
    
        static bool colorOverride;
    
        static int colorId;
    
        static int i_color;
    
    
        // Attributes
        
        static MObject aAddScale;
        
        static MObject aAddScaleX;
        
        static MObject aAddScaleY;
        
        static MObject aAddScaleZ;
        
        static MObject aDrawOrtho;
        
        static MObject aDrawStyle;
        
        static MObject aThickness;
        
        static MObject aTransformScaling;
        
        static MObject aBlendHColour;      
        
        static MObject aDrawAxColour;
    
    protected:
    
        MGLFunctionTable *glft;
    
    
};
