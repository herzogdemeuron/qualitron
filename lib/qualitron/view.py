import revitron
from System.Collections.Generic import List
from pyrevit import DB, UI, forms

uidoc = __revit__.ActiveUIDocument
active_doc = __revit__.ActiveUIDocument.Document
active_view = uidoc.ActiveView

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
        self.overrides = DB.OverrideGraphicSettings()
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
        patternColor = DB.Color(color[0], color[1], color[2])
        x = 0.7
        lineColor =  DB.Color(color[0] * x, color[1] * x, color[2] * x)
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
        categoryIds = List[DB.ElementId](categoryIds)
        active_view.IsolateCategoriesTemporary(categoryIds)
    
    @staticmethod
    def byElementIds(elementIds):
        """
        Isolates given elements

        Args:
            elementIds (object): A list of element ids or a single element id
        """
        elementIds = List[DB.ElementId](elementIds)
        active_view.IsolateElementsTemporary(elementIds)

        
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
        username = active_doc.Application.Username
        newViewName = prefix + username
        viewType3D = DB.ViewType.ThreeD
        views = DB.FilteredElementCollector(active_doc).OfClass(DB.View).WhereElementIsNotElementType().ToElements()
        newView = [v for v in views 
                                if v.ViewType == viewType3D
                                    and v.Name == newViewName]
        transaction = DB.Transaction(active_doc, 'Create 3D view')
        if newView:
            newView = newView[0]
        else:
            view3DFamily = DB.ViewFamily.ThreeDimensional
            view_types = DB.FilteredElementCollector(active_doc).OfClass(DB.ViewFamilyType).ToElements()
            viewFamilyType = [vt for vt in view_types if vt.ViewFamily == view3DFamily][0]

            transaction.Start()
            view3D = DB.View3D         
            newView = view3D.CreateIsometric(active_doc,viewFamilyType.Id)
            newView.Name = newViewName
            transaction.Commit()

        if setActive:
            uidoc.ActiveView = newView

            transaction.Start()
            ids = List[DB.ElementId](categoryIds)
            newView.IsolateCategoriesTemporary(ids)
            transaction.Commit()

        return newView
    

class View3DChecker:
    """
    Functions to create 3D view generated from a 2D view.
    """
    @staticmethod
    def create():
        """
        Function to be called in order to create.
        """
        XYZ = DB.XYZ  
        def makeCounterClockweise(curveloop):
            """
            Make sure that a curve loop is counter clockweise
            to ensure rotation direction.

            Args:
                curveloop (obj): A revit curve loop element.
            """
            if not curveloop.IsCounterclockwise(DB.XYZ(0, 0, 1)):
                curveloop.Flip()

        def getCropPoints(crop, plane):
            """
            Get crop corner points as a list.
            Only when the crop has a rectangular form
            and not reshaped, otherweise return None. 

            Args:
                crop (obj): revit view crop element.
                plane (obj): the crop plane.
            """
            result = None
            if crop.IsRectangular(plane) and (not crsm.ShapeSet):
                makeCounterClockweise(crop)
                result = [c.GetEndPoint(0) for c in crop]
            return result

        def getVector(p1,p2):
            """
            Get normalized vector from two end points.

            Args:
                p1 (obj): starting point of the vector.
                p2 (obj): end point of the vector.

            Returns:
                obj: normalized vector.
            """
            return p2.Add(p1.Negate()).Normalize()
        
        def getLevelHeight(level, offset, default):
            """
            Get elevetion of a level,
            return default if level dosen't exist.

            Args:
                level (obj): revit level element.
                offset (float): offset to the level elevation.
                default (float): default elevation.
            """

            if level:
                return level.ProjectElevation + offset
            else:
                return default

        def createBoundingBox(in_min, in_max, angle):
            """
            Create a boundingbox with min and max point.
            Rotation of the boundingbox would be calculated
            with an angle.

            Args:
                in_min (obj): min point of the boundingbox.
                in_max (obj): max point of the boundingbox.
                angle (obj): rotation.
            """
            origin = XYZ(0, 0, 0)
            axis = XYZ(0, 0, 1)
            rotate = DB.Transform.\
                    CreateRotationAtPoint(axis,
                                        angle,
                                        origin)

            rotate_back = DB.Transform.\
                    CreateRotationAtPoint(axis,
                                        -angle,
                                        origin)	
            r_min = rotate.OfPoint(in_min)
            r_max = rotate.OfPoint(in_max)
            bb = DB.BoundingBoxXYZ()
            bb.Max = r_max
            bb.Min = r_min
            bb.Transform = bb.Transform.Multiply(rotate_back)
            return bb

        def setView3d(bb):
            """
            Create a 3D view, set boundingbox
            to its scope box and set it as active.

            Args:
                bb (obj): A revit BoundingboxXYZ element.

            Returns:
                obj: created 3D view.
            """
            view3d = View3dCreator.create('HdM_3D_')

            transaction = DB.Transaction(active_doc, 'Set 3D view section box')
            transaction.Start()
            view3d.SetSectionBox(bb)
            view3d.IsSectionBoxActive = True
            transaction.Commit()

            uidoc.ActiveView = view3d
            return view3d

        def createPlanBbox(view2d, points):
            """
            Create a boundingbox according to a plan view
            and 


            Args:
                view2d (_type_): _description_
                points (_type_): _description_

            Returns:
                _type_: _description_
            """
            cutPlane = DB.PlanViewPlane.CutPlane
            topClipPlane = DB.PlanViewPlane.TopClipPlane
            bottomClipPlane = DB.PlanViewPlane.BottomClipPlane

            viewrange = view2d.GetViewRange()	
            cut_level = active_doc.GetElement(viewrange.GetLevelId(cutPlane))
            cut_offset = viewrange.GetOffset(cutPlane)
            cut_replace = cut_level.ProjectElevation + cut_offset
            
            top_level = active_doc.GetElement(viewrange.GetLevelId(topClipPlane))
            top_offset = viewrange.GetOffset(topClipPlane)
            top_height = getLevelHeight(top_level,
                                        top_offset,
                                        cut_replace + 6.561679)	
            
            bottom_level = active_doc.GetElement(viewrange.GetLevelId(bottomClipPlane))
            bottom_offset = viewrange.GetOffset(bottomClipPlane)	
            bottom_height = getLevelHeight(bottom_level,
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
            bb_depth = min(bb_depth, 100)
            bb_depth = max(10, bb_depth)
            v_bottom = getVector(points_bottom[0],points_bottom[1])
            angle = v_bottom.AngleOnPlaneTo(XYZ(1,0,0),XYZ(0,0,1))
            p_min = points_bottom[0]
            p_max = points_bottom[1].Add(plane.Normal.Multiply(bb_depth))
            p_max = p_max.Add(XYZ(0,0,bb_height))
            return createBoundingBox(p_min,p_max,angle)

        
        vt = DB.ViewType           
        planViewTypes = [vt.FloorPlan,vt.AreaPlan,vt.CeilingPlan]
        sectionViewTypes = [vt.Section]
        crsm = active_view.GetCropRegionShapeManager()
        crop = crsm.GetCropShape()
        print(active_view.ViewType)
        # check if active view is a sheet
        if active_view.ViewType not in (planViewTypes + sectionViewTypes):
            forms.alert('Can only create 3D view from plan or section view.', ok=True)
            return

        recCheck = False
        if crop:    
            crop = crop[0]
            plane = crop.GetPlane()
            rec = crop.IsRectangular(plane) and (not crsm.ShapeSet)
            if rec:
                recCheck = True
            else:
                forms.alert('View Crop is not rectangular.', ok=True)
        else:
            forms.alert('Please activate view crop.', ok=True)
        if not recCheck:
            return

        cropPts = getCropPoints(crop, plane)
        if active_view.ViewType in planViewTypes:
            bbox = createPlanBbox(active_view, cropPts)
        elif active_view.ViewType in sectionViewTypes:
            bbox = createSectionBbox(active_view, cropPts, plane)
        else:
            bbox = None
        if bbox:    
            view3d = setView3d(bbox)
            view3d.OrientTo(plane.Normal)