import revitron
import math

from Autodesk.Revit.DB import FilteredElementCollector, Line, ViewType, XYZ, BuiltInParameter, Transform, BoundingBoxXYZ, View, ViewFamilyType, ViewFamily, Transaction, View3D, PlanViewPlane

pi = math.pi
uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document
app = __revit__.Application
from qualitron import View3dCreator

def makeCounterclockweise(curveloop):
	if not curveloop.IsCounterclockwise(XYZ(0,0,1)):
		curveloop.Flip()

def findCenter(points):
	n = len(points)
	x = y = z = 0
	for point in points:
		x += point.X
		y += point.Y
		z += point.Z
	return XYZ(x/n,y/n,z/n)	

def getVector(p1,p2):
	return p2.Add(p1.Negate()).Normalize()
	
def getRangeHeight(level,offset,replace):
	if level:
		return level.ProjectElevation + offset
	else: return replace

def createBoundingBox(in_min,in_max,angle):
	origin = XYZ(0,0,0)
	axis = XYZ(0,0,1)
	#rotate the max and min points as a line
	if angle != 0:
		line = Line.CreateBound(in_min,in_max)
		rotate = Transform.CreateRotationAtPoint(axis, angle, origin)
		line_rotated = line.CreateTransformed(rotate)
		min = line_rotated.GetEndPoint(0)
		max = line_rotated.GetEndPoint(1)
	else:
		min = p_min
		max = p_max
	#create bb and set max, min	
	bb = BoundingBoxXYZ()
	bb.Max = max
	bb.Min = min
	#bb from rotated points should be set back
	if angle != 0:
		rotate_back = Transform.CreateRotationAtPoint(axis, -angle, origin)
		bb.Transform = bb.Transform.Multiply(rotate_back)
	return bb

def setView3d(bb):

	view3d = View3dCreator.create()

	t=Transaction(doc,"3D from current view")
	t.Start()
	view3d.SetSectionBox(bb)
	view3d.IsSectionBoxActive = True
	t.Commit()
	uidoc.ActiveView = view3d
	return view3d

#pick the active view to generate 3d section
view2d = uidoc.ActiveView
#get the crop shape of view
crsm = view2d.GetCropRegionShapeManager()
crop = crsm.GetCropShape()
#the active view should be either view plan or section

#---------for a FloorPlan
viewTypes = [ViewType.FloorPlan,ViewType.AreaPlan]
if view2d.ViewType in viewTypes and crop:
	crop = crop[0]
	plane = crop.GetPlane()
	#ensure the crop shape is rechtangle	
	if crop.IsRectangular(plane) and (not crsm.ShapeSet):
		#make sure crop is counter clockweise
		makeCounterclockweise(crop)
		points = []
		for c in crop:
			points.append(c.GetEndPoint(0))
			
		v = getVector(points[0],points[1])
		angle = v.AngleOnPlaneTo(XYZ(1,0,0),XYZ(0,0,1))
		
		viewrange = view2d.GetViewRange()	
		cut_level =  doc.GetElement(viewrange.GetLevelId(PlanViewPlane.CutPlane))
		cut_offset = viewrange.GetOffset(PlanViewPlane.CutPlane)
		cut_replace = cut_level.ProjectElevation + cut_offset
		
		top_level =  doc.GetElement(viewrange.GetLevelId(PlanViewPlane.TopClipPlane))
		top_offset = viewrange.GetOffset(PlanViewPlane.TopClipPlane)
		# if the top level sret to unlimited, the height should be cut level height with 2 meter offset	
		top_height = getRangeHeight(top_level,top_offset,cut_replace + 6.561679)	
		
		bottom_level =  doc.GetElement(viewrange.GetLevelId(PlanViewPlane.BottomClipPlane))
		bottom_offset = viewrange.GetOffset(PlanViewPlane.BottomClipPlane)	
		bottom_height = getRangeHeight(bottom_level,bottom_offset,cut_replace - 6.561679)		
	
		#create bb from the rotated crop
		p_min = XYZ(points[0].X,points[0].Y,bottom_height)
		p_max = XYZ(points[2].X,points[2].Y,top_height)
		
		bb = createBoundingBox(p_min,p_max,angle)
		view3d = setView3d(bb)
		view3d.OrientTo(plane.Normal)
		
	
#---------for a Section
if view2d.ViewType == ViewType.Section and crop:
	crop = crop[0]
	plane = crop.GetPlane()
	#ensure the crop shape is rechtangle	
	if crop.IsRectangular(plane) and (not crsm.ShapeSet):
		#make sure crop is counter clockweise
		makeCounterclockweise(crop)
		points = []
		for c in crop:
			points.append(c.GetEndPoint(0))

		#sort points to top and bottom
		points_top = []
		points_bottom = []
		center = findCenter(points)
		for p in points:
			if p.Z > center.Z: points_top.append(p)
			else: points_bottom.append(p)
		#height of bb
		bb_height = points_top[0].Z - points_bottom[0].Z
		#depth of bb
		bb_depth = view2d.get_Parameter(BuiltInParameter.VIEWER_BOUND_OFFSET_FAR).AsDouble()
		#set max depth
		bb_depth = 100 if bb_depth > 100 else bb_depth
		#set min depth
		bb_depth = 10 if bb_depth < 10 else bb_depth
		
		v_bottom = getVector(points_bottom[0],points_bottom[1])
		angle = v_bottom.AngleOnPlaneTo(XYZ(1,0,0),XYZ(0,0,1))
		p_min = points_bottom[0]
		p_max = points_bottom[1].Add(plane.Normal.Multiply(bb_depth)).Add(XYZ(0,0,bb_height))

		bb = createBoundingBox(p_min,p_max,angle)	
		view3d = setView3d(bb)
		view3d.OrientTo(plane.Normal)
		

