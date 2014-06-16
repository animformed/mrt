/*

    mrt_xhandleShapePlu.h
    
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

# include <maya/MTypeId.h>
# include <maya/MPxLocatorNode.h> 
# include <maya/M3dView.h>
# include <maya/MMatrix.h>
# include <maya/MTransformationMatrix.h>
# include <maya/MQuaternion.h>
# include <maya/MDagPath.h>
# include <maya/MFnTransform.h>
# include <maya/MFnDependencyNode.h>
# include <maya/MFnNumericAttribute.h>
# include <maya/MFnEnumAttribute.h>
# include <maya/MFnPlugin.h>
# include <maya/MDistance.h>
# include <maya/MPlug.h>
# include <maya/MHardwareRenderer.h>

// Vertex points
static GLfloat handle_low[][3] = { {0.41f, 1.0f, 0.0f},
                                   {1.0f, 0.41f, 0.0f},
                                   {1.0f, -0.41f, 0.0f},
                                   {0.41f, -1.0f, 0.0f},
                                   {-0.41f, -1.0f, 0.0f},
                                   {-1.0f, -0.41f, 0.0f},
                                   {-1.0f, 0.41f, 0.0f},
                                   {-0.41f, 1.0f, 0.0f} };

static GLfloat handle_high[][3] = { {0.15f, 0.0f, 0.0f},
                                    {0.138644463844f, 0.0572513112978f, 0.0f},
                                    {0.106297164729f, 0.10583436479f, 0.0f},
                                    {0.0578557149829f, 0.138393338871f, 0.0f},
                                    {0.000654496392712f, 0.149998572108f, 0.0f},
                                    {-0.0566458176302f, 0.138892949227f, 0.0f},
                                    {-0.105369549918f, 0.106757940923f, 0.0f},
                                    {-0.138139579088f, 0.0584590171787f, 0.0f},
                                    {-0.14999428846f, 0.00130898032476f, 0.0f},
                                    {-0.139138790288f, -0.0560392455079f, 0.0f},
                                    {-0.1072166846f, -0.104902728961f, 0.0f},
                                    {-0.059061206399f, -0.137883189326f, 0.0f},
                                    {-0.0019634393357f, -0.149987149136f, 0.0f},
                                    {0.0554316064791f, -0.139381982348f, 0.0f},
                                    {0.104433910807f, -0.107673387026f, 0.0f},
                                    {0.137624174467f, -0.0596622711791f, 0.0f} };

class xhandleShape : public MPxLocatorNode
{
	public:
		xhandleShape();
		virtual	~xhandleShape();
    
		virtual void postConstructor();
    
		virtual MStatus compute(const MPlug& plug, MDataBlock& data);
    
		virtual void draw(M3dView &view, const MDagPath &path,
                          M3dView::DisplayStyle style, M3dView::DisplayStatus status);
    
		virtual void drawShapes(short enumType, bool drawWire, float unit_multiplier,
                                     GLfloat w_size, short drawOrtho, bool selection);
    
		virtual bool            isBounded() const;
		virtual MBoundingBox    boundingBox() const;
    
		static  void *          creator();
		static  MStatus         initialize();
		static  MTypeId     	id;

		static  MObject		aAddScaleX;
		static  MObject		aAddScaleY;
		static  MObject		aAddScaleZ;
		
		static  MObject		aDrawOrtho;
		static  MObject		aDrawStyle;
		static  MObject		aThickness;
		static  MObject		aTransformScaling;
		static  MObject		aBlendHColour;		
		static  MObject		aDrawAxColour;
		
	protected:
		MGLFunctionTable *gGLFT;
};

MTypeId xhandleShape::id(0x80090);
MObject xhandleShape::aAddScaleX;
MObject xhandleShape::aAddScaleY;
MObject xhandleShape::aAddScaleZ;
MObject xhandleShape::aDrawOrtho;
MObject xhandleShape::aDrawStyle;
MObject xhandleShape::aThickness;
MObject xhandleShape::aTransformScaling;
MObject xhandleShape::aBlendHColour;
MObject xhandleShape::aDrawAxColour;

xhandleShape::xhandleShape()
{
	// Get a pointer to a GL function table
    MHardwareRenderer *rend = MHardwareRenderer::theRenderer();
	gGLFT = rend->glFunctionTable();
}

xhandleShape::~xhandleShape(){}

void xhandleShape::postConstructor(){}

MStatus xhandleShape::compute(const MPlug& /*plug*/, MDataBlock& /*data*/)
{
	return MS::kUnknownParameter;
}

void xhandleShape::drawShapes(short enumType, bool drawWire, float unit_multiplier,
                                            GLfloat w_size, short drawOrtho, bool selection)
{
	MObject thisNode = thisMObject();
    
    // Get the current draw color for this node
	MPlug drawAxColourPlug(thisNode, aDrawAxColour);
	short drawAxColourValue;
	drawAxColourPlug.getValue(drawAxColourValue);
    
    // Check if draw ortho is turned on.
	MPlug drawOrthoPlug(thisNode, aDrawOrtho);
	short drawOrthoValue;
	drawOrthoPlug.getValue(drawOrthoValue);

    // Draw according to drawStyle attribute value passed to enumType.
	switch(enumType) {
    
	case 1: gGLFT->glRotatef(-90.0f, 1.0f, 0.0f, 0.0f);
		gGLFT->glEnable(GL_POINT_SMOOTH);
		gGLFT->glLineWidth(w_size);
		gGLFT->glPointSize(w_size);
		gGLFT->glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
		gGLFT->glBegin(GL_POINTS);
		gGLFT->glVertex3f(0.0f, 1.0f * unit_multiplier, 0.0f);
		gGLFT->glVertex3f(1.0f * unit_multiplier, -1.0f * unit_multiplier, 0.0f);
		gGLFT->glVertex3f(-1.0f * unit_multiplier, -1.0f * unit_multiplier, 0.0f);
		gGLFT->glEnd();
		gGLFT->glBegin(GL_LINE_LOOP);
		gGLFT->glVertex3f(0.0f, 1.0f * unit_multiplier, 0.0f);
		gGLFT->glVertex3f(1.0f * unit_multiplier, -1.0f * unit_multiplier, 0.0f);
		gGLFT->glVertex3f(-1.0f * unit_multiplier, -1.0f * unit_multiplier, 0.0f);
		gGLFT->glEnd();
		break;
			
	case 2: gGLFT->glRotatef(-90.0f, 1.0f, 0.0f, 0.0f);
		gGLFT->glRotatef(180.0f, 0.0f, 0.0f, 1.0f);
		gGLFT->glEnable(GL_POINT_SMOOTH);
		gGLFT->glLineWidth(w_size);
		gGLFT->glPointSize(w_size);
		gGLFT->glBegin(GL_POINTS);
		gGLFT->glVertex3f(0.0f, 1.0f * unit_multiplier, 0.0f);
		gGLFT->glVertex3f(1.0f * unit_multiplier, -1.0f * unit_multiplier, 0.0f);
		gGLFT->glVertex3f(-1.0f * unit_multiplier, -1.0f * unit_multiplier, 0.0f);
		gGLFT->glEnd();
		gGLFT->glBegin(GL_LINE_LOOP);
		gGLFT->glVertex3f(0.0f, 1.0f * unit_multiplier, 0.0f);
		gGLFT->glVertex3f(1.0f * unit_multiplier, -1.0f * unit_multiplier, 0.0f);
		gGLFT->glVertex3f(-1.0f * unit_multiplier, -1.0f * unit_multiplier, 0.0f);
		gGLFT->glEnd();
		break;
	
	case 3: gGLFT->glRotatef(-90.0f, 1.0f, 0.0f, 0.0f);
		gGLFT->glEnable(GL_POINT_SMOOTH);
		gGLFT->glLineWidth(w_size);
		gGLFT->glPointSize(w_size);
		gGLFT->glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
		gGLFT->glBegin(GL_POINTS);
		gGLFT->glVertex3f(-1.0f * unit_multiplier, 1.0f * unit_multiplier, 0.0f);
		gGLFT->glVertex3f(1.0f * unit_multiplier, 1.0f * unit_multiplier, 0.0f);
		gGLFT->glVertex3f(1.0f * unit_multiplier, -1.0f * unit_multiplier, 0.0f);
		gGLFT->glVertex3f(-1.0f * unit_multiplier, -1.0f * unit_multiplier, 0.0f);
		gGLFT->glEnd();	
		gGLFT->glBegin(GL_LINE_LOOP);
		gGLFT->glVertex3f(-1.0f * unit_multiplier, 1.0f * unit_multiplier, 0.0f);
		gGLFT->glVertex3f(1.0f * unit_multiplier, 1.0f * unit_multiplier, 0.0f);
		gGLFT->glVertex3f(1.0f * unit_multiplier, -1.0f * unit_multiplier, 0.0f);
		gGLFT->glVertex3f(-1.0f * unit_multiplier, -1.0f * unit_multiplier, 0.0f);
		gGLFT->glEnd();
		break;
	
	case 4: gGLFT->glRotatef(-90.0f, 1.0f, 0.0f, 0.0f);
		gGLFT->glEnable(GL_POINT_SMOOTH);
		gGLFT->glLineWidth(w_size);
		gGLFT->glPointSize(w_size);
		gGLFT->glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
		gGLFT->glBegin(GL_POINTS);
		for (int i=0; i<8; i++)
			gGLFT->glVertex3f(handle_low[i][0] * unit_multiplier, handle_low[i][1] * unit_multiplier, 0.0f);
		gGLFT->glEnd();
		gGLFT->glBegin(GL_LINE_LOOP);
		for (int i=0; i<8; i++)
			gGLFT->glVertex3f(handle_low[i][0] * unit_multiplier, handle_low[i][1] * unit_multiplier, 0.0f);
		gGLFT->glEnd();
		break;
	
	case 5: gGLFT->glRotatef(-90.0f, 1.0f, 0.0f, 0.0f);
		gGLFT->glEnable(GL_POINT_SMOOTH);
		gGLFT->glLineWidth(w_size);
		gGLFT->glPointSize(w_size);
		gGLFT->glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
		gGLFT->glBegin(GL_POINTS);
		for (int i=0; i<16; i++)
			gGLFT->glVertex3f(handle_high[i][0] * 6.66f * unit_multiplier, handle_high[i][1] * 6.66f * unit_multiplier, 0.0f);
		gGLFT->glEnd();
		gGLFT->glBegin(GL_LINE_LOOP);
		for (int i=0; i<16; i++)
			gGLFT->glVertex3f(handle_high[i][0] * 6.66f * unit_multiplier, handle_high[i][1] * 6.66f * unit_multiplier, 0.0f);
		gGLFT->glEnd();
		break;
	
	case 6: gGLFT->glRotatef(-90.0f, 1.0f, 0.0f, 0.0f);
		gGLFT->glBegin(GL_LINE_LOOP);
		gGLFT->glVertex3f(-1.0f * unit_multiplier, 1.0f * unit_multiplier, 0.0f);
		gGLFT->glVertex3f(1.0f * unit_multiplier, 1.0f * unit_multiplier, 0.0f);
		gGLFT->glVertex3f(1.0f * unit_multiplier, -1.0f * unit_multiplier, 0.0f);
		gGLFT->glVertex3f(-1.0f * unit_multiplier, -1.0f * unit_multiplier, 0.0f);
		gGLFT->glEnd();
		gGLFT->glBegin(GL_POINTS);
		gGLFT->glVertex3f(-1.0f * unit_multiplier, 1.0f * unit_multiplier, 0.0f);
		gGLFT->glVertex3f(1.0f * unit_multiplier, 1.0f * unit_multiplier, 0.0f);
		gGLFT->glVertex3f(1.0f * unit_multiplier, -1.0f * unit_multiplier, 0.0f);
		gGLFT->glVertex3f(-1.0f * unit_multiplier, -1.0f * unit_multiplier, 0.0f);
		gGLFT->glEnd();
		gGLFT->glEnable(GL_POINT_SMOOTH);
		gGLFT->glLineWidth(w_size);
		gGLFT->glPointSize(w_size);
		gGLFT->glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
		gGLFT->glBegin(GL_POINTS);
		for (int i=0; i<8; i++)
			gGLFT->glVertex3f(handle_low[i][0] * 0.525f * unit_multiplier, handle_low[i][1] * 0.525f * unit_multiplier, 0.0f);
		gGLFT->glEnd();
		gGLFT->glBegin(GL_LINE_LOOP);
		for (int i=0; i<8; i++)
			gGLFT->glVertex3f(handle_low[i][0] * 0.525f * unit_multiplier, handle_low[i][1] * 0.525f * unit_multiplier, 0.0f);
		gGLFT->glEnd();
		break;
	
	case 7: gGLFT->glRotatef(-90.0f, 1.0f, 0.0f, 0.0f);
		gGLFT->glBegin(GL_LINE_LOOP);
		gGLFT->glVertex3f(-1.0f * unit_multiplier, 1.0f * unit_multiplier, 0.0f);
		gGLFT->glVertex3f(1.0f * unit_multiplier, 1.0f * unit_multiplier, 0.0f);
		gGLFT->glVertex3f(1.0f * unit_multiplier, -1.0f * unit_multiplier, 0.0f);
		gGLFT->glVertex3f(-1.0f * unit_multiplier, -1.0f * unit_multiplier, 0.0f);
		gGLFT->glEnd();
		gGLFT->glBegin(GL_POINTS);
		gGLFT->glVertex3f(-1.0f * unit_multiplier, 1.0f * unit_multiplier, 0.0f);
		gGLFT->glVertex3f(1.0f * unit_multiplier, 1.0f * unit_multiplier, 0.0f);
		gGLFT->glVertex3f(1.0f * unit_multiplier, -1.0f * unit_multiplier, 0.0f);
		gGLFT->glVertex3f(-1.0f * unit_multiplier, -1.0f * unit_multiplier, 0.0f);
		gGLFT->glEnd();	
		gGLFT->glEnable(GL_POINT_SMOOTH);
		gGLFT->glLineWidth(w_size);
		gGLFT->glPointSize(w_size);
		gGLFT->glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
		gGLFT->glBegin(GL_POINTS);
		for (int i=0; i<16; i++)
			gGLFT->glVertex3f(handle_high[i][0] * 3.5f * unit_multiplier, handle_high[i][1] * 3.5f * unit_multiplier, 0.0f);
		gGLFT->glEnd();
		gGLFT->glBegin(GL_LINE_LOOP);
		for (int i=0; i<16; i++)
			gGLFT->glVertex3f(handle_high[i][0] * 3.5f * unit_multiplier, handle_high[i][1] * 3.5f * unit_multiplier, 0.0f);
		gGLFT->glEnd();
		break;
	
	case 8: gGLFT->glRotatef(-90.0f, 1.0f, 0.0f, 0.0f);
		gGLFT->glLineWidth(w_size);
		if ((drawAxColourValue == 1) && (drawOrthoValue == 0) && (selection == false)){
			gGLFT->glColor3f(1.0f, 0.0f, 0.0f);
		}
		gGLFT->glBegin(GL_LINES);
		gGLFT->glVertex3f(1.0f * unit_multiplier, 0.0f, 0.0f);
		gGLFT->glVertex3f(-1.0f * unit_multiplier, 0.0f, 0.0f);
		gGLFT->glEnd();
		if ((drawAxColourValue == 1) && (drawOrthoValue == 0) && (selection == false)){
			gGLFT->glColor3f(0.0f, 0.0f, 1.0f);
		}
		gGLFT->glBegin(GL_LINES);
		gGLFT->glVertex3f(0.0f, 1.0f * unit_multiplier, 0.0f);
		gGLFT->glVertex3f(0.0f, -1.0f * unit_multiplier, 0.0f);
		gGLFT->glEnd();
		if (drawOrtho != 1) {
			if ((drawAxColourValue == 1) && (drawOrthoValue == 0) && (selection == false)){
				gGLFT->glColor3f(0.0f, 1.0f, 0.0f);
			}
		gGLFT->glBegin(GL_LINES);
		gGLFT->glVertex3f(0.0f, 0.0f, 1.0f * unit_multiplier);
		gGLFT->glVertex3f(0.0f, 0.0f, -1.0f * unit_multiplier);
		gGLFT->glEnd();
		break;
		}
	}
}

void xhandleShape::draw(M3dView &view, const MDagPath &path, M3dView::DisplayStyle style, M3dView::DisplayStatus status)
{	
	gGLFT->glPushAttrib(GL_ALL_ATTRIB_BITS);
	view.beginGL();
	
	MDistance distanceObject;
	GLfloat unit_multiplier = (float) distanceObject.uiToInternal(1.0);
	
	MObject thisNode = thisMObject();
	
	MPlug localPositionX_plug(thisNode, localPositionX);
	MPlug localPositionY_plug(thisNode, localPositionY);
	MPlug localPositionZ_plug(thisNode, localPositionZ);
	GLfloat localPositionX_value = localPositionX_plug.asFloat();
	GLfloat localPositionY_value = localPositionY_plug.asFloat();
	GLfloat localPositionZ_value = localPositionZ_plug.asFloat();
	gGLFT->glMatrixMode(GL_MODELVIEW);
	gGLFT->glTranslatef(localPositionX_value, localPositionY_value, localPositionZ_value);
	
	MPlug drawOrthoPlug(thisNode, aDrawOrtho);
	short drawOrthoValue;
	drawOrthoPlug.getValue(drawOrthoValue);
	
	if (drawOrthoValue == 1) {
		MMatrix path_r_Matrix = path.inclusiveMatrixInverse();
		gGLFT->glMultMatrixd(&(path_r_Matrix.matrix[0][0]));
		MMatrix path_t_Matrix = path.inclusiveMatrix();
		MTransformationMatrix trans_matrix(path_t_Matrix);
		MVector trans_vec = trans_matrix.getTranslation(MSpace::kTransform);
		gGLFT->glTranslated(trans_vec[0], trans_vec[1], trans_vec[2]);
	
		MDagPath cameraPath;
		view.getCamera(cameraPath);
		MMatrix camMatrix = cameraPath.inclusiveMatrix();
		MTransformationMatrix camTransMatrix(camMatrix);
		MQuaternion camRotation = camTransMatrix.rotation();
		MVector camRotAxis;
		double camRotTheta;
		camRotation.getAxisAngle(camRotAxis, camRotTheta);
		camRotTheta *= 57.2957795130f;
		gGLFT->glRotated(camRotTheta, camRotAxis[0], camRotAxis[1], camRotAxis[2]);
	}
	
	MPlug transformScalingPlug(thisNode, aTransformScaling);
	short transformScaling;
	transformScalingPlug.getValue(transformScaling);
	
	if ((transformScaling == 0) && (drawOrthoValue == 0)){
		MMatrix pathInvMatrix = path.inclusiveMatrixInverse();
		MTransformationMatrix pathInvTransMatrix(pathInvMatrix);
		double invScale[3];
		pathInvTransMatrix.getScale(invScale, MSpace::kTransform);
		gGLFT->glScaled(invScale[0], invScale[1], invScale[2]);
	}
	if ((transformScaling == 1) && (drawOrthoValue == 1)) {
		MMatrix pathMatrix = path.inclusiveMatrix();
		MTransformationMatrix pathTransMatrix(pathMatrix);
		double scale[3];
		pathTransMatrix.getScale(scale, MSpace::kTransform);
		gGLFT->glScaled(scale[0], scale[2], scale[1]);
	}
	
	MPlug localScaleX_plug(thisNode, localScaleX);
	MPlug localScaleY_plug(thisNode, localScaleY);
	MPlug localScaleZ_plug(thisNode, localScaleZ);
	GLfloat l_scaleX = localScaleX_plug.asFloat();
	GLfloat l_scaleY = localScaleY_plug.asFloat();
	GLfloat l_scaleZ = localScaleZ_plug.asFloat();
	
	MPlug addScaleX_plug(thisNode, aAddScaleX);
	MPlug addScaleY_plug(thisNode, aAddScaleY);
	MPlug addScaleZ_plug(thisNode, aAddScaleZ);
	GLfloat a_scaleX = addScaleX_plug.asFloat();
	GLfloat a_scaleY = addScaleY_plug.asFloat();
	GLfloat a_scaleZ = addScaleZ_plug.asFloat();
	
	if (drawOrthoValue == 1) {		
		gGLFT->glScalef((l_scaleX * a_scaleX), (l_scaleZ * a_scaleZ), (l_scaleY * a_scaleY));
	}
	if (drawOrthoValue == 0) {		
		gGLFT->glScalef((l_scaleX * a_scaleX), (l_scaleY * a_scaleY), (l_scaleZ * a_scaleZ));
	}
	if (drawOrthoValue == 1) {
		gGLFT->glRotatef(90.0f, 1.0f, 0.0f, 0.0f);
	}
	
	MFnDependencyNode shapeNodeFn(thisNode);
	MObject ovEnabled = shapeNodeFn.attribute("overrideEnabled");
	MObject ovColor = shapeNodeFn.attribute("overrideColor");
	MPlug ovEnabledPlug(thisNode, ovEnabled);
	MPlug ovColorPlug(thisNode, ovColor);
	bool ovEnabledValue = ovEnabledPlug.asBool();
	short ovColorValue = ovColorPlug.asShort();
	MPlug drawStylePlug(thisNode, aDrawStyle);
	short drawStyleValue = drawStylePlug.asShort();
	MPlug w_thicknessPlug(thisNode, aThickness);
	GLfloat w_size = w_thicknessPlug.asFloat();
	
	MPlug blendHColourPlug(thisNode, aBlendHColour);
	short blendHColourValue;
	blendHColourPlug.getValue(blendHColourValue);
	
	bool sel = true;
	
	if (status == M3dView::kLead)
		view.setDrawColor(18, M3dView::kActiveColors);
	if (status == M3dView::kActive)
	view.setDrawColor(15, M3dView::kActiveColors);
	if (status == M3dView::kDormant)
	{
		sel = false;
	view.setDrawColor(4, M3dView::kDormantColors);
		if (ovEnabledValue == true)
			view.setDrawColor(ovColorValue-1, M3dView::kDormantColors);
	}
	
	if (blendHColourValue == 1) {
	gGLFT->glEnable(GL_BLEND);
	gGLFT->glBlendFunc(GL_DST_COLOR, GL_SRC_COLOR);
	}
	if (blendHColourValue == 0) {
			gGLFT->glDisable(GL_BLEND);
	}

	
	if ((style == M3dView::kWireFrame) || (style == M3dView::kPoints)) 
	{   
		    gGLFT->glEnable(GL_LINE_SMOOTH);
		    drawShapes(drawStyleValue, true, unit_multiplier, w_size, drawOrthoValue, sel); 
	}	
	if ((style == M3dView::kFlatShaded) || (style == M3dView::kGouraudShaded)) 
	{
		    gGLFT->glClearDepth(0.0);
	    gGLFT->glDepthFunc(GL_ALWAYS);
		    gGLFT->glEnable(GL_LINE_SMOOTH);
		    drawShapes(drawStyleValue, true, unit_multiplier, w_size, drawOrthoValue, sel); 
		    
	}	
	view.endGL();
	gGLFT->glPopAttrib();
}

bool xhandleShape::isBounded() const
{ 
    return true;
}

MBoundingBox xhandleShape::boundingBox() const
{   
	MObject thisNode = thisMObject();
	MDistance distanceObject;
	float unit_multiplier = (float) distanceObject.uiToInternal(1.0);

	MPlug localPositionX_plug(thisNode, localPositionX);
	MPlug localPositionY_plug(thisNode, localPositionY);
	MPlug localPositionZ_plug(thisNode, localPositionZ);
	float localPositionX_value = localPositionX_plug.asFloat();
	float localPositionY_value = localPositionY_plug.asFloat();
	float localPositionZ_value = localPositionZ_plug.asFloat();
	
	MVector translation_vec(localPositionX_value, localPositionY_value, localPositionZ_value);
	MTransformationMatrix t_matrix;
	t_matrix.setTranslation(translation_vec, MSpace::kTransform);
	MMatrix localPos_matrix = t_matrix.asMatrix();
	
	MPlug localScaleX_plug(thisNode, localScaleX);
	MPlug localScaleY_plug(thisNode, localScaleY);
	MPlug localScaleZ_plug(thisNode, localScaleZ);
	float l_scaleX = localScaleX_plug.asFloat();
	float l_scaleY = localScaleY_plug.asFloat();
	float l_scaleZ = localScaleZ_plug.asFloat();
	
	MPlug addScaleX_plug(thisNode, aAddScaleX);
	MPlug addScaleY_plug(thisNode, aAddScaleY);
	MPlug addScaleZ_plug(thisNode, aAddScaleZ);
	float a_scaleX = addScaleX_plug.asFloat();
	float a_scaleY = addScaleY_plug.asFloat();
	float a_scaleZ = addScaleZ_plug.asFloat();

	MPlug drawStylePlug(thisNode, aDrawStyle);
	short drawStyleValue = drawStylePlug.asShort();

	MPlug drawOrthoPlug(thisNode, aDrawOrtho);
	short drawOrthoValue;
	drawOrthoPlug.getValue(drawOrthoValue);

	float c1[3] = {-1.0, 0.0, 1.0};
	float c2[3] = {1.0, 0.0, -1.0};

	if ((drawOrthoValue == 0) && (drawStyleValue == 8)) {
		c1[1] = 1.0;
		c2[1] = -1.0;
	}
	if (drawOrthoValue == 1) {
		c1[1] = 1.0;
		c2[1] = -1.0;
	}

	c1[0] = c1[0] * (l_scaleX * a_scaleX);
	c2[0] = c2[0] * (l_scaleX * a_scaleX);
	c1[1] = c1[1] * (l_scaleY * a_scaleY);
	c2[1] = c2[1] * (l_scaleY * a_scaleY);
	c1[2] = c1[2] * (l_scaleZ * a_scaleZ);
	c2[2] = c2[2] * (l_scaleZ * a_scaleZ);

	MPoint corner1(c1[0], c1[1], c1[2]);
	MPoint corner2(c2[0], c2[1], c2[2]);

	corner1 = corner1 * unit_multiplier;
	corner2 = corner2 * unit_multiplier;

	MBoundingBox b_box(corner1, corner2);
	b_box.transformUsing(localPos_matrix);

	MPlug transformScalingPlug(thisNode, aTransformScaling);
	short transformScaling;
	transformScalingPlug.getValue(transformScaling);

	if (transformScaling == 0) {
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

void* xhandleShape::creator()
{
    return new xhandleShape();
}

MStatus xhandleShape::initialize()
{	
	MFnNumericAttribute numAttr;
	MFnEnumAttribute enumAttr;
	
	aDrawStyle = numAttr.create("drawStyle", "ds", MFnNumericData::kShort);
	numAttr.setMax(8);
	numAttr.setMin(1);
	numAttr.setDefault(1);
	numAttr.setStorable(true);
	numAttr.setReadable(true);
	numAttr.setWritable(true);
	numAttr.setKeyable(true);
	
	aDrawOrtho = enumAttr.create("drawOrtho", "dro");
	enumAttr.addField("Off", 0);
	enumAttr.addField("On", 1);
	enumAttr.setDefault(1);
	enumAttr.setReadable(true);
	enumAttr.setStorable(true);
	enumAttr.setWritable(true);
	enumAttr.setKeyable(true);

	aThickness = numAttr.create("wireframeThickness", "wt", MFnNumericData::kFloat);
	numAttr.setMin(1.0f);
	numAttr.setDefault(5.0f);
	numAttr.setStorable(true);
	numAttr.setReadable(true);
	numAttr.setWritable(true);
	numAttr.setKeyable(true);

	aTransformScaling = enumAttr.create("transformScaling", "tsc");
	enumAttr.addField("Off", 0);
	enumAttr.addField("On", 1);
	enumAttr.setDefault(1);
	enumAttr.setReadable(true);
	enumAttr.setStorable(true);
	enumAttr.setWritable(true);
	enumAttr.setKeyable(true);

	aAddScaleX = numAttr.create("addScaleX", "asx", MFnNumericData::kFloat);
	numAttr.setDefault(1.0);
	numAttr.setStorable(true);
	numAttr.setReadable(true);
	numAttr.setWritable(true);
	numAttr.setKeyable(true);
	
	aAddScaleY = numAttr.create("addScaleY", "asy", MFnNumericData::kFloat);
	numAttr.setDefault(1.0);
	numAttr.setStorable(true);
	numAttr.setReadable(true);
	numAttr.setWritable(true);
	numAttr.setKeyable(true);

	aAddScaleZ = numAttr.create("addScaleZ", "asz", MFnNumericData::kFloat);
	numAttr.setDefault(1.0);
	numAttr.setStorable(true);
	numAttr.setReadable(true);
	numAttr.setWritable(true);
	numAttr.setKeyable(true);

	aBlendHColour = enumAttr.create("blendColour", "bhc");
	enumAttr.addField("Off", 0);
	enumAttr.addField("On", 1);
	enumAttr.setDefault(0);
	enumAttr.setReadable(true);
	enumAttr.setStorable(true);
	enumAttr.setWritable(true);
	enumAttr.setKeyable(true);


	aDrawAxColour = enumAttr.create("drawAxisColour", "daxc");
	enumAttr.addField("Off", 0);
	enumAttr.addField("On", 1);
	enumAttr.setDefault(0);
	enumAttr.setReadable(true);
	enumAttr.setStorable(true);
	enumAttr.setWritable(true);
	enumAttr.setKeyable(true);
	
	MStatus stat1, stat2, stat3, stat4, stat5, stat6, stat7, stat8, stat9, stat10, stat11;
	stat1 = addAttribute(aAddScaleX);
	stat2 = addAttribute(aAddScaleY);
	stat3 = addAttribute(aAddScaleZ);
	stat4 = addAttribute(aDrawStyle);
	stat5 = addAttribute(aDrawOrtho);
	stat6 = addAttribute(aThickness);
	stat7 = addAttribute(aTransformScaling);
	stat8 = addAttribute(aBlendHColour);
	stat9 = addAttribute(aDrawAxColour);


	if ( !stat1 || !stat2 || !stat3 || !stat4 || !stat5 || !stat6 || !stat7 || !stat8 || !stat9 ) 
	{
        stat1.perror("Error in adding attribute");
        stat2.perror("Error in adding attribute");
        stat3.perror("Error in adding attribute");
	stat4.perror("Error in adding attribute");
        stat5.perror("Error in adding attribute");
        stat6.perror("Error in adding attribute");
	stat7.perror("Error in adding attribute");
	stat8.perror("Error in adding attribute");
	stat9.perror("Error in adding attribute");
	return MS::kFailure;
    }
    return MS::kSuccess;
}

MStatus initializePlugin(MObject obj)
{ 
    MStatus status;
    MFnPlugin plugin(obj, "Unknown", "1.0", "2011x64");
    status = plugin.registerNode("xhandleShape", xhandleShape::id, &xhandleShape::creator, &xhandleShape::initialize, MPxNode::kLocatorNode);
    if (!status) 
	{	
        status.perror("Node falied to register.");
        return status;
    }
    return status;
}

MStatus uninitializePlugin(MObject obj)
{
    MStatus status;
    MFnPlugin plugin(obj);
    status = plugin.deregisterNode(xhandleShape::id);
    if (!status) 
	{
        status.perror("Node failed to de-register.");
        return status;
    }
    return status;
}