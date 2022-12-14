import revitron
from System.Collections.Generic import List


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