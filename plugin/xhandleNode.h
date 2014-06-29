/*

    PLUGIN: xhandleNodePlugin v1.0
    
    xhandleNode.h
    
    ////////////////////////////////////////////////////////////////////////////

    Source for xhandleShape node plugin class declaration.

    This is derived from an MPxLocatorNode, with the following
    added attributes :

    addScaleX - Additional local scaling attribute multiplied with localScale.
    addScaleY
    addScaleZ
 
    drawStyle - Draw shape type with values from 1 to 8.
                1 - Triangle
                2 - Inverted triangle
                3 - Square
                4 - Octagon
                5 - Circle
                6 - Octagon within a square
                7 - Circle within a square
                8 - Three axes
 
    drawAxisColour - Draw shape type 8 with coloured axes, red, green and blue.
 
    drawOrtho - Draw the current draw shape orthogonally facing the viewport camera.
 
    transformScaling - Enable / Disable scaling for the draw shape from parent transform.
 
    wireframeThickness - Draw thickness for the shape, with values from 1 to 10.
 
    blendColour - Blend the shape draw colour with viewport background.
    
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
# include <maya/MArgList.h>
# include <maya/MPxCommand.h>
# include <maya/MDGModifier.h>

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


// xhandleShape node class declaration

class xhandleShape : public MPxLocatorNode
{
    public:
        
        // Member functions
        
        xhandleShape();
        
        virtual ~xhandleShape();
        
        static void* creator();
        
        static MStatus initialize();
        
        virtual MStatus compute(const MPlug& plug, MDataBlock& data);
    
        inline double RAD_TO_DEG(double);
    
        void setInternalAttrs() const;
    
        void drawShapes(bool selection);
    
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


// xhandle command class declaration

class xhandle : public MPxCommand
{
    public:
        
        xhandle();
        
        virtual ~xhandle();
    
        static void* creator();
    
        MStatus doIt(const MArgList&);
    
        MStatus redoIt();
    
        MStatus undoIt();
        
        inline bool isUndoable() const;
    
        MString commandString() const;
    
    private:
    
        MString xhandleName;    // Name passed in with the -name or -n flag.
    
        MPoint position;    // Local position passed in with the -position or -p flag.
    
        bool nodeCreated;   // To record if node is successfully created for a command
    
        bool positionSpecified;     // If a position is specified during a command.
    
        MObject xhandleNode;    // To store the node object, if successfully created.

};

