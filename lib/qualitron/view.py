import revitron
from revitron import _
from System.Collections.Generic import List
import sys

class ElementOverrides:
    """
    Class for handling graphical element overrides.
    """
    def __init__(self, view, element):
        """
        Inits a new ElementOverrids instance.

        Args:
            view (object): A Revit view element
            element (object): A Revit element or ElementId
        """
        self.overrides = revitron.DB.OverrideGraphicSettings()
        self.element = element
        self.view = view
        try:
            self.id = element.Id
        except:
            self.id = element
            

    def set(self, color, patternId, transparency=0, overrideCutPattern=True):
        """
        Sets graphical element overrides in the active view.

        Args:
            color (int): A list or tuple (r, g, b)
            pattern (object): An element id of a Revit fill pattern
            overrideCutPattern (bool, optional): Override cut pattern. Defaults to True.
        """
        patternColor = revitron.DB.Color(color[0], color[1], color[2])
        x = 0.7
        lineColor =  revitron.DB.Color(color[0] * x, color[1] * x, color[2] * x)
        self.overrides.SetSurfaceForegroundPatternColor(patternColor)
        self.overrides.SetSurfaceForegroundPatternId(patternId)
        self.overrides.SetProjectionLineColor(lineColor)
        self.overrides.SetSurfaceTransparency(transparency)
        if overrideCutPattern:
            self.overrides.SetCutForegroundPatternColor(patternColor)
            self.overrides.SetCutForegroundPatternId(patternId)
        self.view.SetElementOverrides(self.id, self.overrides)
        return self.element

    def clear(self):
        """
        Clears a graphical element overrides in view.
        """
        self.view.SetElementOverrides((self.id), self.overrides)
        return self.element


class Isolate:
    """
    Class for handling temporary isolations.
    """
    @staticmethod    
    def byCategory(categoryIds):
        """
        Isolates given categories

        Args:
            categoryIds (object): A list of category ids or a single category id
        """
        if not type(categoryIds) == list:
            categoryIds = [categoryIds]
        categoryIds = List[revitron.DB.ElementId](categoryIds)
        revitron.ACTIVE_VIEW.IsolateCategoriesTemporary(categoryIds)
    
    @staticmethod
    def byElementIds(elementIds):
        """
        Isolates given elements

        Args:
            elementIds (object): A list of element ids or a single element id
        """
        elementIds = List[revitron.DB.ElementId](elementIds)
        revitron.ACTIVE_VIEW.IsolateElementsTemporary(elementIds)

        
class View3dCreator:
    """
    Functions for 3D view creating.
    """

    @staticmethod
    def create(prefix='' ,categoryIds=[], setActive=True):
        """
        create 3D view, isolate category at the same tiem

        Args:
            prefix (str, optional): view name prefix
            categoryIds (list): categories to isolate
            setActive (bool, optional): if 3D view set active

        Returns:
            obj: new 3D view
        """
        username = revitron.DOC.Application.Username
        newViewName = prefix + username
        viewType3D = revitron.DB.ViewType.ThreeD
        fltr = revitron.Filter().byClass('View')
        fltr = fltr.noTypes().getElements()
        newView = [v for v in fltr 
                                if v.ViewType == viewType3D
                                    and v.Name == newViewName]
        if newView:
            newView = newView[0]
        else:
            view3DFamily = revitron.DB.ViewFamily.ThreeDimensional
            viewFamilyType = [vt for vt in revitron.Filter()
                                                    .byClass('ViewFamilyType').getElements()
                                                    if vt.ViewFamily == view3DFamily][0]                   
            with revitron.Transaction():
                view3D = revitron.DB.View3D         
                newView = view3D.CreateIsometric(revitron.DOC,viewFamilyType.Id)
                newView.Name = newViewName
        if setActive:
            revitron.UIDOC.ActiveView = newView

            with revitron.Transaction():
                ids = List[revitron.DB.ElementId](categoryIds)
                newView.IsolateCategoriesTemporary(ids)
        return newView
    

class View3DChecker:
    @staticmethod
    def create():
        XYZ = revitron.DB.XYZ  
        def makeCounterClockweise(curveloop):
            if not curveloop.IsCounterclockwise(
                        revitron.DB.XYZ(0,0,1)):
                curveloop.Flip()

        def getCropPoints(crop,plane):
            result = None
            if crop.IsRectangular(plane) and (not crsm.ShapeSet):
                makeCounterClockweise(crop)
                result = [c.GetEndPoint(0) for c in crop]
            return result

        def getVector(p1,p2):
            return p2.Add(p1.Negate()).Normalize()
        
        def getRangeHeight(level,offset,replace):
            if level:
                return level.ProjectElevation + offset
            else:
                return replace

        def createBoundingBox(in_min,in_max,angle):
            origin = XYZ(0,0,0)
            axis = XYZ(0,0,1)
            rotate = revitron.DB.Transform.\
                    CreateRotationAtPoint(axis,
                                        angle,
                                        origin)

            rotate_back = revitron.DB.Transform.\
                    CreateRotationAtPoint(axis,
                                        -angle,
                                        origin)	
            min = rotate.OfPoint(in_min)
            max = rotate.OfPoint(in_max)
            bb = revitron.DB.BoundingBoxXYZ()
            bb.Max = max
            bb.Min = min
            bb.Transform = bb.Transform.Multiply(rotate_back)
            return bb

        def setView3d(bb):
            view3d = View3dCreator.create('Qualitron_')
            with revitron.Transaction():
                view3d.SetSectionBox(bb)
                view3d.IsSectionBoxActive = True
            revitron.ACTIVE_VIEW = view3d
            return view3d

        def createPlanBbox(view2d, points):
            cutPlane = revitron.DB.PlanViewPlane.CutPlane
            topClipPlane = revitron.DB.PlanViewPlane.TopClipPlane
            bottomClipPlane = revitron.DB.PlanViewPlane.BottomClipPlane

            viewrange = view2d.GetViewRange()	
            cut_level =  revitron.DOC.GetElement(viewrange.GetLevelId(cutPlane))
            cut_offset = viewrange.GetOffset(cutPlane)
            cut_replace = cut_level.ProjectElevation + cut_offset
            
            top_level =  revitron.DOC.GetElement(viewrange.GetLevelId(topClipPlane))
            top_offset = viewrange.GetOffset(topClipPlane)
            top_height = getRangeHeight(top_level, top_offset, cut_replace + 6.561679)	
            
            bottom_level =  revitron.DOC.GetElement(viewrange.GetLevelId(bottomClipPlane))
            bottom_offset = viewrange.GetOffset(bottomClipPlane)	
            bottom_height = getRangeHeight(
                                        bottom_level,
                                        bottom_offset,
                                        cut_replace - 6.561679)
            v = getVector(points[0],points[1])
            angle = v.AngleOnPlaneTo(XYZ(1,0,0),XYZ(0,0,1))	
            p_min = XYZ(points[0].X,points[0].Y,bottom_height)
            p_max = XYZ(points[2].X,points[2].Y,top_height)

            return createBoundingBox(p_min,p_max,angle)

        def createSectionBbox(view2d, points, plane):
            points_top = []
            points_bottom = []
            zList = [p.Z for p in points]
            center = sum(zList)/len(zList)
            for p in points:
                if p.Z > center:
                    points_top.append(p)
                else:
                    points_bottom.append(p)
            bb_height = points_top[0].Z - points_bottom[0].Z
            bb_depth = _(view2d).get('Far Clip Offset')
            bb_depth = 100 if bb_depth > 100 else bb_depth
            bb_depth = 10 if bb_depth < 10 else bb_depth
            v_bottom = getVector(points_bottom[0],points_bottom[1])
            angle = v_bottom.AngleOnPlaneTo(XYZ(1,0,0),XYZ(0,0,1))
            p_min = points_bottom[0]
            p_max = points_bottom[1].Add(plane.Normal.Multiply(bb_depth))
            p_max = p_max.Add(XYZ(0,0,bb_height))
            return createBoundingBox(p_min,p_max,angle)

        
        vt = revitron.DB.ViewType           
        planViewTypes = [vt.FloorPlan,vt.AreaPlan,vt.CeilingPlan]
        sectionViewTypes = [vt.Section]
        view2d = revitron.ACTIVE_VIEW
        crsm = view2d.GetCropRegionShapeManager()
        crop = crsm.GetCropShape()

        recCheck = False
        if crop:    
            crop = crop[0]
            plane = crop.GetPlane()
            rec = crop.IsRectangular(plane) and (not crsm.ShapeSet)
            if rec:
                recCheck = True
            else:
                print('View Crop is not rectangular.')
        else:
            print('Please turn on view crop.')
        if not recCheck:
            sys.exit()

        cropPts = getCropPoints(crop, plane)
        if view2d.ViewType in planViewTypes:
            bbox = createPlanBbox(view2d, cropPts)
        elif view2d.ViewType in sectionViewTypes:
            bbox = createSectionBbox(view2d, cropPts, plane)
        else:
            bbox = None
        if bbox:    
            view3d = setView3d(bbox)
            view3d.OrientTo(plane.Normal)