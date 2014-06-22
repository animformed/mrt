/*

    xhandleShapeNode.cpp
    
    ////////////////////////////////////////////////////////////////////////////

    Source for xhandleShape node plugin, for use as control locators in modules
    and control rigging for modular rigging tools for maya.

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

# include "xhandleShape.h"


// Data

MTypeId xhandleShape::id(0x80090);
float xhandleShape::l_positionX;
float xhandleShape::l_positionY;
float xhandleShape::l_positionZ;
float xhandleShape::add_scaleX;
float xhandleShape::add_scaleY;
float xhandleShape::add_scaleZ;
float xhandleShape::l_scaleX;
float xhandleShape::l_scaleY;
float xhandleShape::l_scaleZ;
bool xhandleShape::dDrawOrtho;
int xhandleShape::dDrawStyle;
GLfloat xhandleShape::dThickness;
bool xhandleShape::dTransformScaling;
bool xhandleShape::dBlendHColour;
bool xhandleShape::dDrawAxColour;
GLfloat xhandleShape::uMult;


// Attributes

MObject xhandleShape::aAddScale;
MObject xhandleShape::aAddScaleX;
MObject xhandleShape::aAddScaleY;
MObject xhandleShape::aAddScaleZ;
MObject xhandleShape::aDrawOrtho;
MObject xhandleShape::aDrawStyle;
MObject xhandleShape::aThickness;
MObject xhandleShape::aTransformScaling;
MObject xhandleShape::aBlendHColour;
MObject xhandleShape::aDrawAxColour;


xhandleShape::xhandleShape() { }

xhandleShape::~xhandleShape() { }

void* xhandleShape::creator() { return new xhandleShape(); }

MStatus xhandleShape::initialize() {

    MFnNumericAttribute dsAttr;
    aDrawStyle = dsAttr.create("drawStyle", "ds", MFnNumericData::kShort);
    CHECK_MSTATUS (dsAttr.setMax(8));
    CHECK_MSTATUS (dsAttr.setMin(1));
    CHECK_MSTATUS (dsAttr.setDefault(1));
    CHECK_MSTATUS (dsAttr.setStorable(true));
    CHECK_MSTATUS (dsAttr.setReadable(true));
    CHECK_MSTATUS (dsAttr.setWritable(true));
    CHECK_MSTATUS (dsAttr.setKeyable(true));
    
    MFnEnumAttribute droAttr;
    aDrawOrtho = droAttr.create("drawOrtho", "dro");
    CHECK_MSTATUS (droAttr.addField("Off", 0));
    CHECK_MSTATUS (droAttr.addField("On", 1));
    CHECK_MSTATUS (droAttr.setDefault(1));
    CHECK_MSTATUS (droAttr.setReadable(true));
    CHECK_MSTATUS (droAttr.setStorable(true));
    CHECK_MSTATUS (droAttr.setWritable(true));
    CHECK_MSTATUS (droAttr.setKeyable(true));
    
    MFnNumericAttribute wtAttr;
    aThickness = wtAttr.create("wireframeThickness", "wt", MFnNumericData::kFloat);
    CHECK_MSTATUS (wtAttr.setMin(1.0f));
    CHECK_MSTATUS (wtAttr.setDefault(5.0f));
    CHECK_MSTATUS (wtAttr.setStorable(true));
    CHECK_MSTATUS (wtAttr.setReadable(true));
    CHECK_MSTATUS (wtAttr.setWritable(true));
    CHECK_MSTATUS (wtAttr.setKeyable(true));
    
    MFnEnumAttribute tscAttr;
    aTransformScaling = tscAttr.create("transformScaling", "tsc");
    CHECK_MSTATUS (tscAttr.addField("Off", 0));
    CHECK_MSTATUS (tscAttr.addField("On", 1));
    CHECK_MSTATUS (tscAttr.setDefault(1));
    CHECK_MSTATUS (tscAttr.setReadable(true));
    CHECK_MSTATUS (tscAttr.setStorable(true));
    CHECK_MSTATUS (tscAttr.setWritable(true));
    CHECK_MSTATUS (tscAttr.setKeyable(true));
    
    MFnNumericAttribute asxAttr;
    aAddScaleX = asxAttr.create("addScaleX", "asx", MFnNumericData::kFloat);
    CHECK_MSTATUS (asxAttr.setDefault(1.0));
    CHECK_MSTATUS (asxAttr.setStorable(true));
    CHECK_MSTATUS (asxAttr.setReadable(true));
    CHECK_MSTATUS (asxAttr.setWritable(true));
    CHECK_MSTATUS (asxAttr.setKeyable(true));
    
    MFnNumericAttribute asyAttr;
    aAddScaleY = asyAttr.create("addScaleY", "asy", MFnNumericData::kFloat);
    CHECK_MSTATUS (asyAttr.setDefault(1.0));
    CHECK_MSTATUS (asyAttr.setStorable(true));
    CHECK_MSTATUS (asyAttr.setReadable(true));
    CHECK_MSTATUS (asyAttr.setWritable(true));
    CHECK_MSTATUS (asyAttr.setKeyable(true));
    
    MFnNumericAttribute aszAttr;
    aAddScaleZ = aszAttr.create("addScaleZ", "asz", MFnNumericData::kFloat);
    CHECK_MSTATUS (aszAttr.setDefault(1.0));
    CHECK_MSTATUS (aszAttr.setStorable(true));
    CHECK_MSTATUS (aszAttr.setReadable(true));
    CHECK_MSTATUS (aszAttr.setWritable(true));
    CHECK_MSTATUS (aszAttr.setKeyable(true));

    MFnNumericAttribute asAttr;
    aAddScale = asAttr.create("addScale", "as", aAddScaleX, aAddScaleY, aAddScaleZ);
    CHECK_MSTATUS (asAttr.setDefault(1.0));
    CHECK_MSTATUS (asAttr.setStorable(true));
    CHECK_MSTATUS (asAttr.setReadable(true));
    CHECK_MSTATUS (asAttr.setWritable(true));
    CHECK_MSTATUS (asAttr.setKeyable(true));
    
    MFnEnumAttribute bhcAttr;
    aBlendHColour = bhcAttr.create("blendColour", "bhc");
    CHECK_MSTATUS (bhcAttr.addField("Off", 0));
    CHECK_MSTATUS (bhcAttr.addField("On", 1));
    CHECK_MSTATUS (bhcAttr.setDefault(0));
    CHECK_MSTATUS (bhcAttr.setReadable(true));
    CHECK_MSTATUS (bhcAttr.setStorable(true));
    CHECK_MSTATUS (bhcAttr.setWritable(true));
    CHECK_MSTATUS (bhcAttr.setKeyable(true));
    
    MFnEnumAttribute daxcAttr;
    aDrawAxColour = daxcAttr.create("drawAxisColour", "daxc");
    CHECK_MSTATUS (daxcAttr.addField("Off", 0));
    CHECK_MSTATUS (daxcAttr.addField("On", 1));
    CHECK_MSTATUS (daxcAttr.setDefault(0));
    CHECK_MSTATUS (daxcAttr.setReadable(true));
    CHECK_MSTATUS (daxcAttr.setStorable(true));
    CHECK_MSTATUS (daxcAttr.setWritable(true));
    CHECK_MSTATUS (daxcAttr.setKeyable(true));
    
    // Add the attributes
    CHECK_MSTATUS (addAttribute(aAddScale));
    CHECK_MSTATUS (addAttribute(aDrawStyle));
    CHECK_MSTATUS (addAttribute(aDrawOrtho));
    CHECK_MSTATUS (addAttribute(aThickness));
    CHECK_MSTATUS (addAttribute(aTransformScaling));
    CHECK_MSTATUS (addAttribute(aBlendHColour));
    CHECK_MSTATUS (addAttribute(aDrawAxColour));

    return MS::kSuccess;
}


MStatus xhandleShape::compute(const MPlug& /*plug*/, MDataBlock& dataBlock)
{		
		MStatus status;
    
        // Get the internal unit multiplier from maya for GL draw.
        MDistance distanceObject;
        uMult = (float) distanceObject.uiToInternal(1.0);
    
        // Get the local position attributes
        MDataHandle localPositionXHandle = dataBlock.inputValue(localPositionX, &status);
        CHECK_MSTATUS (status);
        l_positionX = localPositionXHandle.asFloat();
    
        MDataHandle localPositionYHandle = dataBlock.inputValue(localPositionY, &status);
        CHECK_MSTATUS (status);
        l_positionY = localPositionYHandle.asFloat();
    
        MDataHandle localPositionZHandle = dataBlock.inputValue(localPositionZ, &status);
        CHECK_MSTATUS (status);
        l_positionZ = localPositionZHandle.asFloat();
    
		// Get the local scale attributes
        MDataHandle localScaleXHandle = dataBlock.inputValue(localScaleX, &status);
        CHECK_MSTATUS (status);
        l_scaleX = localScaleXHandle.asFloat();
    
        MDataHandle localScaleYHandle = dataBlock.inputValue(localScaleY, &status);
        CHECK_MSTATUS (status);
        l_scaleY = localScaleYHandle.asFloat();
    
        MDataHandle localScaleZHandle = dataBlock.inputValue(localScaleZ, &status);
        CHECK_MSTATUS (status);
        l_scaleZ = localScaleZHandle.asFloat();

        // Get the add scale attributes
        MDataHandle addScaleXHandle = dataBlock.inputValue(aAddScaleX, &status);
        CHECK_MSTATUS (status);
        add_scaleX = addScaleXHandle.asFloat();
    
        MDataHandle addScaleYHandle = dataBlock.inputValue(aAddScaleY, &status);
        CHECK_MSTATUS (status);
        add_scaleY = addScaleYHandle.asFloat();
    
        MDataHandle addScaleZHandle = dataBlock.inputValue(aAddScaleZ, &status);
        CHECK_MSTATUS (status);
        add_scaleZ = addScaleZHandle.asFloat();

        // Get the draw ortho attribute
		MDataHandle drawOrthoHandle = dataBlock.inputValue(aDrawOrtho, &status);
		CHECK_MSTATUS (status);
		dDrawOrtho = drawOrthoHandle.asBool();

		// Get the draw style attribute
        MDataHandle drawStyleHandle = dataBlock.inputValue(aDrawStyle, &status);
        CHECK_MSTATUS (status);
		dDrawStyle = drawStyleHandle.asInt();
        
		// Get the draw thickness attribute
		MDataHandle wThicknessHandle = dataBlock.inputValue(aThickness, &status);
        CHECK_MSTATUS (status);
		dThickness = wThicknessHandle.asFloat();

		// Get the transform scaling attribute
		MDataHandle trnsScalingHandle = dataBlock.inputValue(aTransformScaling, &status);
        CHECK_MSTATUS (status);
		dTransformScaling = trnsScalingHandle.asBool();
        
        // Get the draw blend colour attribute
		MDataHandle blendHClrHandle = dataBlock.inputValue(aBlendHColour, &status);
        CHECK_MSTATUS (status);
		dBlendHColour = blendHClrHandle.asBool();
        
        // Get the draw axes colour attribute
		MDataHandle drawAxClrHandle = dataBlock.inputValue(aDrawAxColour, &status);
        CHECK_MSTATUS (status);
		dDrawAxColour = drawAxClrHandle.asBool();
        
    return MS::kSuccess;
}

void xhandleShape::drawShapes(bool selection)
{
    // Draw according to drawStyle attribute value passed to enumType.
    switch(dDrawStyle) {
    
    case 1: glRotatef(-90.0f, 1.0f, 0.0f, 0.0f);
            glEnable(GL_POINT_SMOOTH);
            glLineWidth(dThickness);
            glPointSize(dThickness);
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
            glBegin(GL_POINTS);
            glVertex3f(0.0f, 1.0f * uMult, 0.0f);
            glVertex3f(1.0f * uMult, -1.0f * uMult, 0.0f);
            glVertex3f(-1.0f * uMult, -1.0f * uMult, 0.0f);
            glEnd();
            glBegin(GL_LINE_LOOP);
            glVertex3f(0.0f, 1.0f * uMult, 0.0f);
            glVertex3f(1.0f * uMult, -1.0f * uMult, 0.0f);
            glVertex3f(-1.0f * uMult, -1.0f * uMult, 0.0f);
            glEnd();
            break;
            
    case 2: glRotatef(-90.0f, 1.0f, 0.0f, 0.0f);
            glRotatef(180.0f, 0.0f, 0.0f, 1.0f);
            glEnable(GL_POINT_SMOOTH);
            glLineWidth(dThickness);
            glPointSize(dThickness);
            glBegin(GL_POINTS);
            glVertex3f(0.0f, 1.0f * uMult, 0.0f);
            glVertex3f(1.0f * uMult, -1.0f * uMult, 0.0f);
            glVertex3f(-1.0f * uMult, -1.0f * uMult, 0.0f);
            glEnd();
            glBegin(GL_LINE_LOOP);
            glVertex3f(0.0f, 1.0f * uMult, 0.0f);
            glVertex3f(1.0f * uMult, -1.0f * uMult, 0.0f);
            glVertex3f(-1.0f * uMult, -1.0f * uMult, 0.0f);
            glEnd();
            break;
    
    case 3: glRotatef(-90.0f, 1.0f, 0.0f, 0.0f);
            glEnable(GL_POINT_SMOOTH);
            glLineWidth(dThickness);
            glPointSize(dThickness);
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
            glBegin(GL_POINTS);
            glVertex3f(-1.0f * uMult, 1.0f * uMult, 0.0f);
            glVertex3f(1.0f * uMult, 1.0f * uMult, 0.0f);
            glVertex3f(1.0f * uMult, -1.0f * uMult, 0.0f);
            glVertex3f(-1.0f * uMult, -1.0f * uMult, 0.0f);
            glEnd();
            glBegin(GL_LINE_LOOP);
            glVertex3f(-1.0f * uMult, 1.0f * uMult, 0.0f);
            glVertex3f(1.0f * uMult, 1.0f * uMult, 0.0f);
            glVertex3f(1.0f * uMult, -1.0f * uMult, 0.0f);
            glVertex3f(-1.0f * uMult, -1.0f * uMult, 0.0f);
            glEnd();
            break;
    
    case 4: glRotatef(-90.0f, 1.0f, 0.0f, 0.0f);
            glEnable(GL_POINT_SMOOTH);
            glLineWidth(dThickness);
            glPointSize(dThickness);
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
            glBegin(GL_POINTS);
            for (int i=0; i<8; i++)
                glVertex3f(handle_low[i][0] * uMult, handle_low[i][1] * uMult, 0.0f);
            glEnd();
            glBegin(GL_LINE_LOOP);
            for (int i=0; i<8; i++)
                glVertex3f(handle_low[i][0] * uMult, handle_low[i][1] * uMult, 0.0f);
            glEnd();
            break;
    
    case 5: glRotatef(-90.0f, 1.0f, 0.0f, 0.0f);
            glEnable(GL_POINT_SMOOTH);
            glLineWidth(dThickness);
            glPointSize(dThickness);
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
            glBegin(GL_POINTS);
            for (int i=0; i<16; i++)
                glVertex3f(handle_high[i][0] * 6.66f * uMult, handle_high[i][1] * 6.66f * uMult, 0.0f);
            glEnd();
            glBegin(GL_LINE_LOOP);
            for (int i=0; i<16; i++)
                glVertex3f(handle_high[i][0] * 6.66f * uMult, handle_high[i][1] * 6.66f * uMult, 0.0f);
            glEnd();
            break;
    
    case 6: glRotatef(-90.0f, 1.0f, 0.0f, 0.0f);
            glBegin(GL_LINE_LOOP);
            glVertex3f(-1.0f * uMult, 1.0f * uMult, 0.0f);
            glVertex3f(1.0f * uMult, 1.0f * uMult, 0.0f);
            glVertex3f(1.0f * uMult, -1.0f * uMult, 0.0f);
            glVertex3f(-1.0f * uMult, -1.0f * uMult, 0.0f);
            glEnd();
            glBegin(GL_POINTS);
            glVertex3f(-1.0f * uMult, 1.0f * uMult, 0.0f);
            glVertex3f(1.0f * uMult, 1.0f * uMult, 0.0f);
            glVertex3f(1.0f * uMult, -1.0f * uMult, 0.0f);
            glVertex3f(-1.0f * uMult, -1.0f * uMult, 0.0f);
            glEnd();
            glEnable(GL_POINT_SMOOTH);
            glLineWidth(dThickness);
            glPointSize(dThickness);
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
            glBegin(GL_POINTS);
            for (int i=0; i<8; i++)
                glVertex3f(handle_low[i][0] * 0.525f * uMult, handle_low[i][1] * 0.525f * uMult, 0.0f);
            glEnd();
            glBegin(GL_LINE_LOOP);
            for (int i=0; i<8; i++)
                glVertex3f(handle_low[i][0] * 0.525f * uMult, handle_low[i][1] * 0.525f * uMult, 0.0f);
            glEnd();
            break;
    
    case 7: glRotatef(-90.0f, 1.0f, 0.0f, 0.0f);
            glBegin(GL_LINE_LOOP);
            glVertex3f(-1.0f * uMult, 1.0f * uMult, 0.0f);
            glVertex3f(1.0f * uMult, 1.0f * uMult, 0.0f);
            glVertex3f(1.0f * uMult, -1.0f * uMult, 0.0f);
            glVertex3f(-1.0f * uMult, -1.0f * uMult, 0.0f);
            glEnd();
            glBegin(GL_POINTS);
            glVertex3f(-1.0f * uMult, 1.0f * uMult, 0.0f);
            glVertex3f(1.0f * uMult, 1.0f * uMult, 0.0f);
            glVertex3f(1.0f * uMult, -1.0f * uMult, 0.0f);
            glVertex3f(-1.0f * uMult, -1.0f * uMult, 0.0f);
            glEnd();
            glEnable(GL_POINT_SMOOTH);
            glLineWidth(dThickness);
            glPointSize(dThickness);
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
            glBegin(GL_POINTS);
            for (int i=0; i<16; i++)
                glVertex3f(handle_high[i][0] * 3.5f * uMult, handle_high[i][1] * 3.5f * uMult, 0.0f);
            glEnd();
            glBegin(GL_LINE_LOOP);
            for (int i=0; i<16; i++)
                glVertex3f(handle_high[i][0] * 3.5f * uMult, handle_high[i][1] * 3.5f * uMult, 0.0f);
            glEnd();
            break;
    
    case 8: glRotatef(-90.0f, 1.0f, 0.0f, 0.0f);
            glLineWidth(dDrawOrtho);
            if ((dDrawAxColour == 1) && (dDrawOrtho == 0) && (selection == false))
                glColor3f(1.0f, 0.0f, 0.0f);
            glBegin(GL_LINES);
            glVertex3f(1.0f * uMult, 0.0f, 0.0f);
            glVertex3f(-1.0f * uMult, 0.0f, 0.0f);
            glEnd();
            if ((dDrawAxColour == 1) && (dDrawOrtho == 0) && (selection == false))
                glColor3f(0.0f, 0.0f, 1.0f);
            glBegin(GL_LINES);
            glVertex3f(0.0f, 1.0f * uMult, 0.0f);
            glVertex3f(0.0f, -1.0f * uMult, 0.0f);
            glEnd();
            if (!dDrawOrtho) {
                if ((dDrawAxColour == 1) && (dDrawOrtho == 0) && (selection == false))
                    glColor3f(0.0f, 1.0f, 0.0f);
            }
            glBegin(GL_LINES);
            glVertex3f(0.0f, 0.0f, 1.0f * uMult);
            glVertex3f(0.0f, 0.0f, -1.0f * uMult);
            glEnd();
            break;
        }

}

void xhandleShape::draw(M3dView &view, const MDagPath &path, M3dView::DisplayStyle style, M3dView::DisplayStatus status)
{   
    glPushAttrib(GL_ALL_ATTRIB_BITS);
    
    view.beginGL();
    
    // The draw operation happens in the local matrix space.
    // Apply any position offsets before the draw operations.
    glMatrixMode(GL_MODELVIEW);

    glTranslatef(l_positionX, l_positionY, l_positionZ);
    
    // If the draw "ortho" only is enabled for draw operations,
    // then we want to negate all transformations applied to GL draw operations
    // as a result of locator transformations in maya's scene space.
    if (dDrawOrtho == 1) {
        
        // Based on the maya viewport, get the camera inverse matr
        MDagPath cameraPath;
        view.getCamera(cameraPath);
        MMatrix camInvMMatrix = cameraPath.inclusiveMatrix().inverse();
        glMultMatrixd(&(camInvMMatrix.matrix[0][0]));
        
        // Apply world translation only to the current draw space.
        MMatrix path_t_Matrix = path.inclusiveMatrix();
        MTransformationMatrix trans_matrix(path_t_Matrix);
        MVector trans_vec = trans_matrix.getTranslation(MSpace::kTransform);
        glTranslated(trans_vec[0], trans_vec[1], trans_vec[2]);
        
        glRotatef(90.0f, 1.0f, 0.0f, 0.0f);
    }
    
    // Apply scaling to draw space
    MMatrix pathMatrix;
    if ((dTransformScaling == 0) && (dDrawOrtho == 0))
        pathMatrix = path.inclusiveMatrixInverse();
    if ((dTransformScaling == 1) && (dDrawOrtho == 1))
        pathMatrix = path.inclusiveMatrix();
    MTransformationMatrix pathTransMatrix(pathMatrix);
    double scale[3];
    pathTransMatrix.getScale(scale, MSpace::kTransform);
    glScaled(scale[0], scale[1], scale[2]);
    
    if (dDrawOrtho == 1) {      
        glScalef((l_scaleX * add_scaleX), (l_scaleZ * add_scaleZ), (l_scaleY * add_scaleY));
    }
    if (dDrawOrtho == 0) {      
        glScalef((l_scaleX * add_scaleX), (l_scaleY * add_scaleY), (l_scaleZ * add_scaleZ));
    }

    // Set the draw color based on the current display status.
    view.setDrawColor(colorRGB(status));

    // Set the blend colour state.
    if (dBlendHColour == 0)
        glDisable(GL_BLEND);
    
    if (dBlendHColour == 1) {
        glEnable(GL_BLEND);
        glBlendFunc(GL_DST_COLOR, GL_SRC_COLOR);
    }
    
    if ((style == M3dView::kWireFrame) || (style == M3dView::kPoints)) {
        glEnable(GL_LINE_SMOOTH);
        drawShapes(status == M3dView::kActive);
    }   
    if ((style == M3dView::kFlatShaded) || (style == M3dView::kGouraudShaded)) {
        glClearDepth(0.0);
        glDepthFunc(GL_ALWAYS);
        glEnable(GL_LINE_SMOOTH);
        drawShapes(status == M3dView::kActive);
    }
    
    view.endGL();
    
    glPopAttrib();
}


bool xhandleShape::isBounded() const { return true; }


MBoundingBox xhandleShape::boundingBox() const
{   
    MObject thisNode = thisMObject();
    
    MVector translation_vec(l_positionX, l_positionY, l_positionZ);
    MTransformationMatrix t_matrix;
    t_matrix.setTranslation(translation_vec, MSpace::kTransform);
    MMatrix localPos_matrix = t_matrix.asMatrix();

    float c1[3] = {-1.0, 0.0, 1.0};
    float c2[3] = {1.0, 0.0, -1.0};

    if ((dDrawOrtho == 0) && (dDrawStyle == 8)) {
        c1[1] = 1.0;
        c2[1] = -1.0;
    }
    if (dDrawOrtho == 1) {
        c1[1] = 1.0;
        c2[1] = -1.0;
    }

    c1[0] = c1[0] * (l_scaleX * add_scaleX);
    c2[0] = c2[0] * (l_scaleX * add_scaleX);
    c1[1] = c1[1] * (l_scaleY * add_scaleY);
    c2[1] = c2[1] * (l_scaleY * add_scaleY);
    c1[2] = c1[2] * (l_scaleZ * add_scaleZ);
    c2[2] = c2[2] * (l_scaleZ * add_scaleZ);

    MPoint corner1(c1[0], c1[1], c1[2]);
    MPoint corner2(c2[0], c2[1], c2[2]);

    corner1 = corner1 * uMult;
    corner2 = corner2 * uMult;

    MBoundingBox b_box(corner1, corner2);
    b_box.transformUsing(localPos_matrix);

    //MPlug transformScalingPlug(thisNode, aTransformScaling);
    //short transformScaling;
    //transformScalingPlug.getValue(transformScaling);

    if (dTransformScaling == 0) {
        MDagPath path;
        MFnDagNode pathNode(thisNode);
        pathNode.getPath(path);
        MMatrix pathMatrix = path.inclusiveMatrixInverse();
        MTransformationMatrix pathTransMatrix(pathMatrix);
        double scale[3];
        pathTransMatrix.getScale(scale, MSpace::kTransform);
        MTransformationMatrix s_matrix;
        s_matrix.setScale(scale, MSpace::kTransform);
        MMatrix scale_matrix = s_matrix.asMatrix();
        b_box.transformUsing(scale_matrix);
    }
    
    return b_box;
}



