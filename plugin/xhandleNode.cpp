/*
    
    PLUGIN: xhandleNodePlugin v1.0
 
    xhandleNode.cpp
    
    ////////////////////////////////////////////////////////////////////////////

    Source for xhandleShape node plugin/command, for use as control locators in 
    modules and control rigging for modular rigging tools for maya.
 
    Current limitations:
    Negative scaling while using "draw ortho" might draw incorrectly.
    
    ////////////////////////////////////////////////////////////////////////////
    
    Feel free to modify, extend or copy for your own purpose.
    
    Written by Himanish Bhattacharya

*/

# include "xhandleNode.h"


// Data

MTypeId xhandleShape::id(0x80090);

double xhandleShape::l_positionX;
double xhandleShape::l_positionY;
double xhandleShape::l_positionZ;
double xhandleShape::add_scaleX;
double xhandleShape::add_scaleY;
double xhandleShape::add_scaleZ;
double xhandleShape::l_scaleX;
double xhandleShape::l_scaleY;
double xhandleShape::l_scaleZ;
bool xhandleShape::dDrawOrtho;
int xhandleShape::dDrawStyle;
GLfloat xhandleShape::dThickness;
bool xhandleShape::dTransformScaling;
bool xhandleShape::dBlendHColour;
bool xhandleShape::dDrawAxColour;
GLfloat xhandleShape::uMult;
bool xhandleShape::colorOverride;
int xhandleShape::colorId;


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


xhandleShape::xhandleShape() {
    
    // Get a pointer to a GL function table
    MHardwareRenderer *rend = MHardwareRenderer::theRenderer();
	glft = rend->glFunctionTable();
}

xhandleShape::~xhandleShape() { }

void* xhandleShape::creator() {

    return new xhandleShape();
}

MStatus xhandleShape::initialize() {
    
    // Add node attributes
    
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
    CHECK_MSTATUS (wtAttr.setMax(10.0f));
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



MStatus xhandleShape::compute(const MPlug& /*plug*/, MDataBlock& /*block*/) {
    
    return MS::kUnknownParameter;
}


double xhandleShape::RAD_TO_DEG(double rad) {
    
    return rad * 57.2957795130f;
}


void xhandleShape::setInternalAttrs() const {
    
     // Store and update the node attributes values //
     // for internal use. //
    
    MObject thisNode = thisMObject();
    
    MPlug plug(thisNode, localPositionX);
    plug.getValue(l_positionX);
    
    plug.setAttribute(localPositionY);
    plug.getValue(l_positionY);
    
    plug.setAttribute(localPositionZ);
    plug.getValue(l_positionZ);
    
    plug.setAttribute(aAddScaleX);
    plug.getValue(add_scaleX);
    
    plug.setAttribute(aAddScaleY);
    plug.getValue(add_scaleY);
    
    plug.setAttribute(aAddScaleZ);
    plug.getValue(add_scaleZ);
    
    plug.setAttribute(localScaleX);
    plug.getValue(l_scaleX);
    
    plug.setAttribute(localScaleY);
    plug.getValue(l_scaleY);
    
    plug.setAttribute(localScaleZ);
    plug.getValue(l_scaleZ);
 
    plug.setAttribute(aDrawOrtho);
    plug.getValue(dDrawOrtho);
    
    plug.setAttribute(aDrawStyle);
    plug.getValue(dDrawStyle);
    
    plug.setAttribute(aThickness);
    plug.getValue(dThickness);
    
    plug.setAttribute(aTransformScaling);
    plug.getValue(dTransformScaling);
    
    plug.setAttribute(aBlendHColour);
    plug.getValue(dBlendHColour);
    
    plug.setAttribute(aDrawAxColour);
    plug.getValue(dDrawAxColour);
    
    // Get the internal unit multiplier from maya for GL draw.
    MDistance distanceObject;
    uMult = (float) distanceObject.uiToInternal(1.0);
    
    // Get the override colour value for the locator shape.
    MFnDependencyNode shapeNodeFn(thisNode);
    MObject ovEnabled = shapeNodeFn.attribute("overrideEnabled");
	MObject ovColor = shapeNodeFn.attribute("overrideColor");
    
    plug.setAttribute(ovEnabled);
    plug.getValue(colorOverride);
    
    plug.setAttribute(ovColor);
    plug.getValue(colorId);

}

void xhandleShape::drawShapes(bool selection)
{
    // Draw according to drawStyle attribute value (stored in dDrawStyle).
    
    // 1 - Triangle
    // 2 - Inverted triangle
    // 3 - Square
    // 4 - Octagon
    // 5 - Circle
    // 6 - Octagon within a square
    // 7 - Circle within a square
    // 8 - Three axes
    
    switch(dDrawStyle) {
    
    case 1: glft->glRotatef(-90.0f, 1.0f, 0.0f, 0.0f);
            glft->glEnable(GL_POINT_SMOOTH);
            glft->glLineWidth(dThickness);
            glft->glPointSize(dThickness);
            glft->glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
            glft->glBegin(GL_POINTS);
            glft->glVertex3f(0.0f, 1.0f * uMult, 0.0f);
            glft->glVertex3f(1.0f * uMult, -1.0f * uMult, 0.0f);
            glft->glVertex3f(-1.0f * uMult, -1.0f * uMult, 0.0f);
            glft->glEnd();
            glft->glBegin(GL_LINE_LOOP);
            glft->glVertex3f(0.0f, 1.0f * uMult, 0.0f);
            glft->glVertex3f(1.0f * uMult, -1.0f * uMult, 0.0f);
            glft->glVertex3f(-1.0f * uMult, -1.0f * uMult, 0.0f);
            glft->glEnd();
            break;
            
    case 2: glft->glRotatef(-90.0f, 1.0f, 0.0f, 0.0f);
            glft->glRotatef(180.0f, 0.0f, 0.0f, 1.0f);
            glft->glEnable(GL_POINT_SMOOTH);
            glft->glLineWidth(dThickness);
            glft->glPointSize(dThickness);
            glft->glBegin(GL_POINTS);
            glft->glVertex3f(0.0f, 1.0f * uMult, 0.0f);
            glft->glVertex3f(1.0f * uMult, -1.0f * uMult, 0.0f);
            glft->glVertex3f(-1.0f * uMult, -1.0f * uMult, 0.0f);
            glft->glEnd();
            glft->glBegin(GL_LINE_LOOP);
            glft->glVertex3f(0.0f, 1.0f * uMult, 0.0f);
            glft->glVertex3f(1.0f * uMult, -1.0f * uMult, 0.0f);
            glft->glVertex3f(-1.0f * uMult, -1.0f * uMult, 0.0f);
            glft->glEnd();
            break;
    
    case 3: glft->glRotatef(-90.0f, 1.0f, 0.0f, 0.0f);
            glft->glEnable(GL_POINT_SMOOTH);
            glft->glLineWidth(dThickness);
            glft->glPointSize(dThickness);
            glft->glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
            glft->glBegin(GL_POINTS);
            glft->glVertex3f(-1.0f * uMult, 1.0f * uMult, 0.0f);
            glft->glVertex3f(1.0f * uMult, 1.0f * uMult, 0.0f);
            glft->glVertex3f(1.0f * uMult, -1.0f * uMult, 0.0f);
            glft->glVertex3f(-1.0f * uMult, -1.0f * uMult, 0.0f);
            glft->glEnd();
            glft->glBegin(GL_LINE_LOOP);
            glft->glVertex3f(-1.0f * uMult, 1.0f * uMult, 0.0f);
            glft->glVertex3f(1.0f * uMult, 1.0f * uMult, 0.0f);
            glft->glVertex3f(1.0f * uMult, -1.0f * uMult, 0.0f);
            glft->glVertex3f(-1.0f * uMult, -1.0f * uMult, 0.0f);
            glft->glEnd();
            break;
    
    case 4: glft->glRotatef(-90.0f, 1.0f, 0.0f, 0.0f);
            glft->glEnable(GL_POINT_SMOOTH);
            glft->glLineWidth(dThickness);
            glft->glPointSize(dThickness);
            glft->glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
            glft->glBegin(GL_POINTS);
            for (int i=0; i<8; i++)
                glft->glVertex3f(handle_low[i][0] * uMult, handle_low[i][1] * uMult, 0.0f);
            glft->glEnd();
            glft->glBegin(GL_LINE_LOOP);
            for (int i=0; i<8; i++)
                glft->glVertex3f(handle_low[i][0] * uMult, handle_low[i][1] * uMult, 0.0f);
            glft->glEnd();
            break;
    
    case 5: glft->glRotatef(-90.0f, 1.0f, 0.0f, 0.0f);
            glft->glEnable(GL_POINT_SMOOTH);
            glft->glLineWidth(dThickness);
            glft->glPointSize(dThickness);
            glft->glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
            glft->glBegin(GL_POINTS);
            for (int i=0; i<16; i++)
                glft->glVertex3f(handle_high[i][0] * 6.66f * uMult, handle_high[i][1] * 6.66f * uMult, 0.0f);
            glft->glEnd();
            glft->glBegin(GL_LINE_LOOP);
            for (int i=0; i<16; i++)
                glft->glVertex3f(handle_high[i][0] * 6.66f * uMult, handle_high[i][1] * 6.66f * uMult, 0.0f);
            glft->glEnd();
            break;
    
    case 6: glft->glRotatef(-90.0f, 1.0f, 0.0f, 0.0f);
            glft->glBegin(GL_LINE_LOOP);
            glft->glVertex3f(-1.0f * uMult, 1.0f * uMult, 0.0f);
            glft->glVertex3f(1.0f * uMult, 1.0f * uMult, 0.0f);
            glft->glVertex3f(1.0f * uMult, -1.0f * uMult, 0.0f);
            glft->glVertex3f(-1.0f * uMult, -1.0f * uMult, 0.0f);
            glft->glEnd();
            glft->glBegin(GL_POINTS);
            glft->glVertex3f(-1.0f * uMult, 1.0f * uMult, 0.0f);
            glft->glVertex3f(1.0f * uMult, 1.0f * uMult, 0.0f);
            glft->glVertex3f(1.0f * uMult, -1.0f * uMult, 0.0f);
            glft->glVertex3f(-1.0f * uMult, -1.0f * uMult, 0.0f);
            glft->glEnd();
            glft->glEnable(GL_POINT_SMOOTH);
            glft->glLineWidth(dThickness);
            glft->glPointSize(dThickness);
            glft->glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
            glft->glBegin(GL_POINTS);
            for (int i=0; i<8; i++)
                glft->glVertex3f(handle_low[i][0] * 0.525f * uMult, handle_low[i][1] * 0.525f * uMult, 0.0f);
            glft->glEnd();
            glft->glBegin(GL_LINE_LOOP);
            for (int i=0; i<8; i++)
                glft->glVertex3f(handle_low[i][0] * 0.525f * uMult, handle_low[i][1] * 0.525f * uMult, 0.0f);
            glft->glEnd();
            break;
    
    case 7: glft->glRotatef(-90.0f, 1.0f, 0.0f, 0.0f);
            glft->glBegin(GL_LINE_LOOP);
            glft->glVertex3f(-1.0f * uMult, 1.0f * uMult, 0.0f);
            glft->glVertex3f(1.0f * uMult, 1.0f * uMult, 0.0f);
            glft->glVertex3f(1.0f * uMult, -1.0f * uMult, 0.0f);
            glft->glVertex3f(-1.0f * uMult, -1.0f * uMult, 0.0f);
            glft->glEnd();
            glft->glBegin(GL_POINTS);
            glft->glVertex3f(-1.0f * uMult, 1.0f * uMult, 0.0f);
            glft->glVertex3f(1.0f * uMult, 1.0f * uMult, 0.0f);
            glft->glVertex3f(1.0f * uMult, -1.0f * uMult, 0.0f);
            glft->glVertex3f(-1.0f * uMult, -1.0f * uMult, 0.0f);
            glft->glEnd();
            glft->glEnable(GL_POINT_SMOOTH);
            glft->glLineWidth(dThickness);
            glft->glPointSize(dThickness);
            glft->glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
            glft->glBegin(GL_POINTS);
            for (int i=0; i<16; i++)
                glft->glVertex3f(handle_high[i][0] * 3.5f * uMult, handle_high[i][1] * 3.5f * uMult, 0.0f);
            glft->glEnd();
            glft->glBegin(GL_LINE_LOOP);
            for (int i=0; i<16; i++)
                glft->glVertex3f(handle_high[i][0] * 3.5f * uMult, handle_high[i][1] * 3.5f * uMult, 0.0f);
            glft->glEnd();
            break;
    
    case 8: glft->glRotatef(-90.0f, 1.0f, 0.0f, 0.0f);
            glft->glLineWidth(dDrawOrtho);
            if ((dDrawAxColour == 1) && (dDrawOrtho == 0) && (selection == false))
                glft->glColor3f(1.0f, 0.0f, 0.0f);
            glft->glBegin(GL_LINES);
            glft->glVertex3f(1.0f * uMult, 0.0f, 0.0f);
            glft->glVertex3f(-1.0f * uMult, 0.0f, 0.0f);
            glft->glEnd();
            if ((dDrawAxColour == 1) && (dDrawOrtho == 0) && (selection == false))
                glft->glColor3f(0.0f, 0.0f, 1.0f);
            glft->glBegin(GL_LINES);
            glft->glVertex3f(0.0f, 1.0f * uMult, 0.0f);
            glft->glVertex3f(0.0f, -1.0f * uMult, 0.0f);
            glft->glEnd();
            if (!dDrawOrtho) {
                if ((dDrawAxColour == 1) && (dDrawOrtho == 0) && (selection == false))
                    glft->glColor3f(0.0f, 1.0f, 0.0f);
            }
            glft->glBegin(GL_LINES);
            glft->glVertex3f(0.0f, 0.0f, 1.0f * uMult);
            glft->glVertex3f(0.0f, 0.0f, -1.0f * uMult);
            glft->glEnd();
            break;
        }

}

void xhandleShape::draw(M3dView &view, const MDagPath &path, M3dView::DisplayStyle style, M3dView::DisplayStatus status)
{
    // Update/Get the node attribute values.
    setInternalAttrs();
    
    glft->glPushAttrib(GL_ALL_ATTRIB_BITS);
    
    // Set the current matrix type.
    glft->glMatrixMode(GL_MODELVIEW);
    
    view.beginGL();
    
    // Get the path world matrix and inv matrix.
    MMatrix pathMatrix = path.inclusiveMatrix();
    MMatrix pathInvMatrix = path.inclusiveMatrixInverse();
    MTransformationMatrix pathTransMatrix(pathMatrix);
    MTransformationMatrix pathTransInvMatrix(pathInvMatrix);
    
    // Get the inverse/real scaling values (inclusive).
    double scale[3];
    double inv_scale[3];
    pathTransMatrix.getScale(scale, MSpace::kTransform);
    pathTransInvMatrix.getScale(inv_scale, MSpace::kTransform);
    
    // If the draw "ortho" only is enabled for draw operations,
    if (dDrawOrtho) {
        
        // Negate all transformations applied to GL draw operations
        // as a result of locator transformations in maya's scene space.
		glft->glMultMatrixd(&(pathInvMatrix.matrix[0][0]));
        
        // Apply scaling if enabled. To be applied before any translations.
        if (dTransformScaling)
            glft->glScaled(scale[0], scale[1], scale[2]);
        
        // Apply local translation (localPosition).
        glft->glTranslated(l_positionX, l_positionY, l_positionZ);
        
        // Apply translations only to the draw space (from the parent transforms).
		MVector trans_vec = pathTransMatrix.getTranslation(MSpace::kTransform);
		glft->glTranslated(trans_vec[0], trans_vec[1], trans_vec[2]);
        
        // Rotate the draw space based on the viewport camera.
		MDagPath cameraPath;
		view.getCamera(cameraPath);
		MMatrix camMatrix = cameraPath.inclusiveMatrix();
		MTransformationMatrix camTransMatrix(camMatrix);
		MQuaternion camRotation = camTransMatrix.rotation();
		MVector camRotAxis;
		double camRotTheta;
		camRotation.getAxisAngle(camRotAxis, camRotTheta);
		glft->glRotated(RAD_TO_DEG(camRotTheta), camRotAxis[0], camRotAxis[1], camRotAxis[2]);
        
        // Apply local scaling (localScale and addScale).
        glft->glScaled((l_scaleX * add_scaleX), (l_scaleY * add_scaleY), (l_scaleZ * add_scaleZ));
        
        // Now rotate 90 deg to face the viewport camera.
        glft->glRotatef(90.0f, 1.0f, 0.0f, 0.0f);
        
    } else {    // If "draw ortho" is disabled.
        
        // Negate scaling if applicable (tansform scaling is disabled).
        if (! dTransformScaling)
            glft->glScaled(inv_scale[0], inv_scale[1], inv_scale[2]);
        
        // Apply local translation (localPosition).
        glft->glTranslated(l_positionX, l_positionY, l_positionZ);
        
        // Apply local scaling (localScale and addScale).
        glft->glScaled((l_scaleX * add_scaleX), (l_scaleY * add_scaleY), (l_scaleZ * add_scaleZ));
    }

    // Set the draw color based on the current display status.
    if (status == M3dView::kLead)
		view.setDrawColor(18, M3dView::kActiveColors);
	if (status == M3dView::kActive)
        view.setDrawColor(15, M3dView::kActiveColors);
	if (status == M3dView::kDormant)
	{
        view.setDrawColor(color(M3dView::kDormant), M3dView::kDormantColors);
		if (colorOverride == true)
			view.setDrawColor(color(M3dView::kDormant), M3dView::kDormantColors);
	}
    
    // Set the blend colour state.
    if (dBlendHColour == 0)
        glft->glDisable(GL_BLEND);
    
    if (dBlendHColour == 1) {
        glft->glEnable(GL_BLEND);
        glft->glBlendFunc(GL_DST_COLOR, GL_SRC_COLOR);
    }
    // Now draw the shapes.
    if ((style == M3dView::kWireFrame) || (style == M3dView::kPoints)) {
        glft->glEnable(GL_LINE_SMOOTH);
        drawShapes(status == M3dView::kActive);
    }   
    if ((style == M3dView::kFlatShaded) || (style == M3dView::kGouraudShaded)) {
        glft->glClearDepth(0.0);
        glft->glDepthFunc(GL_ALWAYS);
        glft->glEnable(GL_LINE_SMOOTH);
        drawShapes(status == M3dView::kActive);
    }
    
    view.endGL();
    
    glft->glPopAttrib();
}


bool xhandleShape::isBounded() const { return true; }


MBoundingBox xhandleShape::boundingBox() const
{
    // This method is called for drawing bounding box only.
    
    setInternalAttrs(); // Update/Get the node attribute values.
    
    MObject thisNode = thisMObject();
    
    // Define and calculate the two corner points for the bounding box.
    // By default, set the corner points to be coplanar.
    double c1[3] = {-1.0, 0.0, 1.0};
    double c2[3] = {1.0, 0.0, -1.0};
    
    // If drawOrtho is disabled, or if drawStyle is set to three axes,
    // Separate the corners in -/+ 1 unit in Y.
    if ((dDrawOrtho == 0) && (dDrawStyle == 8)) {
        c1[1] = 1.0;
        c2[1] = -1.0;
    }
    if (dDrawOrtho == 1) {
        c1[1] = 1.0;
        c2[1] = -1.0;
    }
    
    // Apply scaling from localScale and addScale to corners points if any.
    
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
    
    // Now define the bounding box.
    MBoundingBox b_box(corner1, corner2);
    
    // Translate the position of the bounding box as per "localPosition" values.
    MVector translation_vec(l_positionX, l_positionY, l_positionZ);
    MTransformationMatrix t_matrix;
    t_matrix.setTranslation(translation_vec, MSpace::kTransform);
    MMatrix localPos_matrix = t_matrix.asMatrix();
    b_box.transformUsing(localPos_matrix);
    
    // If "transformScaling" is disabled, negate any scaling from parent transforms.
    if (dTransformScaling == 0) {
        
        // Get the inverse worldMatrix for transformation.
        MDagPath path;
        MFnDagNode pathNode(thisNode);
        pathNode.getPath(path);
        MMatrix pathMatrix = path.inclusiveMatrixInverse();
        MTransformationMatrix pathTransMatrix(pathMatrix);
        
        // Get the scaling from transformation matrix.
        double scale[3];
        pathTransMatrix.getScale(scale, MSpace::kTransform);
        
        // Create the inverse scaling matrix.
        MTransformationMatrix s_matrix;
        s_matrix.setScale(scale, MSpace::kTransform);
        MMatrix scale_matrix = s_matrix.asMatrix();
        
        // Apply it to the bounding box.
        b_box.transformUsing(scale_matrix);
        
    }
    
    return b_box;
}

// "xhandle" command implementation //

xhandle::xhandle() { }


xhandle::~xhandle() { }


void* xhandle::creator() { return new xhandle(); }


bool xhandle::isUndoable() const { return true; }


MString xhandle::commandString() const { return "xhandle"; }


MStatus xhandle::doIt(const MArgList& args) {
    
    MStatus status;
    positionSpecified = nodeCreated = false;
    
    for (unsigned i = 0; i < args.length(); i++) {
        
        if ((MString("-name")==args.asString(i)) || (MString("-n")==args.asString(i)))

            xhandleName = args.asString(++i);   // Store the node name provided.
        
        else if ((MString("-position")==args.asString(i)) || (MString("-p")==args.asString(i))) {
            
            positionSpecified = true;
            position = args.asPoint(++i, 3, &status);   // Store the xhandleShape local position provided.
            
            if (!status) {
                status.perror("(xhandle) Incorrect position specified.");
                return MS::kFailure;
            }
        }
        
        else {  // If a flag specified is invalid.
            
            displayError("(xhandle) Invalid flag: " + args.asString(i));
            return MS::kFailure;
        }
    }

    return redoIt();
    
}

// This method is executed by doIt() if the command returns no errors.
MStatus xhandle::redoIt() {
    
    nodeCreated = true;     // This method if executed, creates the xhandle.
    
    MFnDependencyNode nodeFn;   // To create the dependency node.
    
    // "node" may store the parent transform node, and not the xhandleShape shape node.
    MObject node = nodeFn.create("xhandleShape");
    
    // Get the transform for the xhandleShape.
    
    // To get the path.
    MDagPath xhandlePath;
    
    // To operate on dag path.
    MFnDagNode xhandleDagNode(node);
    
    // Set the dag path.
    xhandleDagNode.getPath(xhandlePath);
    
    // Get the transform.
    xhandleNode = xhandlePath.transform();
    
    // Get the fn for the transform.
    MFnDependencyNode xhandleNodeFn(xhandleNode);
    
    // Set the name (for the transform) given using the command.
    if (xhandleName != "")
        xhandleNodeFn.setName(xhandleName);
    
    // Get the new name set for the node.
    xhandleName = xhandleNodeFn.name();

    // Set the local position (for xhandleShape) given using the command.
    if (positionSpecified) {
        
        xhandlePath.extendToShape();
        MFnDependencyNode xhandleShapeNodeFn(xhandlePath.node());
        
        MPlug localPositionX = xhandleShapeNodeFn.findPlug("localPositionX");
        localPositionX.setValue(position.x);

        MPlug localPositionY = xhandleShapeNodeFn.findPlug("localPositionY");
        localPositionY.setValue(position.y);
        
        MPlug localPositionZ = xhandleShapeNodeFn.findPlug("localPositionZ");
        localPositionZ.setValue(position.z);
    }
    
    // To return the name of the created node after the command is executed.
    setResult(xhandleName);
    
    return MStatus::kSuccess;
}


MStatus xhandle::undoIt() {
    
    // To delete the xhandle if successfully created by the command.
    
    MStatus status;
    
    if (nodeCreated)
        status = MGlobal::deleteNode(xhandleNode);
    else
        status = MS::kInvalidParameter;
    
    // Return status for maya if the node is successfully deleted after creation in the undo queue.
    // If a correct status is not returned, maya may crash while parsing through the undo queue.
    return status;

}



