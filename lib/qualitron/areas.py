from System.Collections.Generic import List
import revitron
import Autodesk.Revit.UI as ui
from revitron import _
from revitron import DB
from revitron import DOC
from qualitron import View3dCreator, SharedParamUtils


class AreaHelperManager:
    """
    Manage Area Helper instances, including create, purge and
    write parameter values.
    """

    def __init__(self):
        """
        Initialize instance of the class.
        """
        self.Areas = []
        self.AreaDict = {}
        self.ParamDict = {}
        self.updateAreaDict()
        self.updateParamDict()
        self._removeUnused()
        paramGroup = revitron.DB.BuiltInParameterGroup\
                                .PG_ADSK_MODEL_PROPERTIES
        self.ParamUtils = SharedParamUtils('Area Helper', paramGroup)
        self.UnusedDishapeTypeIds = []
        self.Dishapes = []
        self.DishapeTypeIdsToPurge = []

    def _removeUnused(self):
        """
        Remove unused direct shapes on script startup.
        """
        allDishapes =  self._getAllDishapes()
        usedDishapeIds = [x.GetTypeId() for x in allDishapes]
        allDishapeTypeIds = revitron.Filter().byClass('DirectShapeType').getElementIds()
        unusedDishapeTypeIds = list(set(allDishapeTypeIds) - set(usedDishapeIds))
        with revitron.Transaction():
            dishapeTypeIds_icol = List[DB.ElementId](unusedDishapeTypeIds)
            DOC.Delete(dishapeTypeIds_icol)

    def _getAllDishapes(self):
        """
        Get all existing direct shapes.
        """
        return revitron.Filter().byClass('DirectShape').getElements()
    
    def checkStatus(self):
        """
        check if any areaHelper instances exist
        string rules of revitron filter sometimes dont work
        so using lookup parameter.
        """
        allDishapes =  self._getAllDishapes()
        self.Dishapes = [x for x in allDishapes
                        if _(x).get('Comments') != 'Baked']
        self.DishapeTypeIdsToPurge = [x.GetTypeId() for x in self.Dishapes]
        if self.DishapeTypeIdsToPurge:
            return True
        else:
            return False

    def updateAreaDict(self):
        """
        Update area dict.
        {area scheme name : {levelName : [areas]}
        """
        areaSchemes = revitron.Filter().byCategory('AreaSchemes').getElements()
        for arsch in areaSchemes:
            flr = revitron.Filter().byCategory('Areas')
            flr = flr.noTypes().getElements()
            areas = [x for x in flr 
                    if x.Area > 0
                    and x.AreaScheme.Id == arsch.Id]
            dict = {}
            if areas:
                """Conclude areas to level ALL"""
                dict['- ALL -'] = areas
            for area in areas:
                levelName = area.Level.Name
                if not levelName in dict:
                    dict[levelName] = []
                list = dict.get(levelName)
                if levelName not in list:
                    list.append(area)
            self.AreaDict[arsch.Name] = dict 

    def updateParamDict(self):
        """
        Update parameter dict.
        {areaParamName:dishapeParamName}
        """
        areas = revitron.Filter().byCategory('Areas').getElements()
        if areas:
            area = areas[0]
            for param in area.Parameters:
                name = param.Definition.Name
                readOnly = param.IsReadOnly
                self.ParamDict[name] = 'AreaHelper - ' + name

    def updateAreas(self, schemeName, levelName):
        """
        Refresh selected areas.
        """
        self.Areas = self.AreaDict.get(schemeName).get(levelName)
    
    def set3DView(self):
        """
        Create 3D view and set active.
        """
        mass = revitron.DB.BuiltInCategory.OST_Mass
        massId = revitron.DB.ElementId(mass)
        View3dCreator.create('AreaHelper_', [massId])

    def toggle(self):
        """
        Switch direct shapes.
        """
        status = self.checkStatus()
        if status:
            self.removeDishapes()
            #self.purgeSharedParams()
        else:
            self.set3DView()
            self.createSharedParams()
            self.createDishapes()
            
    def removeDishapes(self):
        """
        Purge dishapes.
        """
        with revitron.Transaction():
            dishapeTypeIds_icol = List[DB.ElementId](self.DishapeTypeIdsToPurge)
            DOC.Delete(dishapeTypeIds_icol)
       
    def bakeDishapes(self):
        """
        Set comment parameter to mark a direct shape baked.
        """
        with revitron.Transaction():
            for ds in self.Dishapes:
                _(ds).set('Comments', 'Baked')

    def createDishapes(self):
        """
        Create all selected direct shapes.
        """
        count = len(self.Areas)
        run = True
        if count > 300:
            decide = ui.TaskDialog.Show('AreaHelper', 'Visualize ' + str(count) 
                                        + ' areas?\nThis may take a long time.',
                                        ui.TaskDialogCommonButtons.Yes|
                                        ui.TaskDialogCommonButtons.No)
            if decide == ui.TaskDialogResult.No:
                run = False
        if run:
            with revitron.Transaction():
                for area in self.Areas:
                    if area.Area > 0: 
                        areaHelper = _AreaHelper(area)
                        shape = areaHelper.createDishape()
                        if shape:
                            self.ParamUtils.writeParamstoDishape(area, shape, self.ParamDict)

    def createSharedParams(self):
        """
        Create shared parameters to direct shape category.
        """
        massCategory = revitron.DOC.Settings.Categories.get_Item('Mass')
        with revitron.Transaction():
            self.ParamUtils.createParams(massCategory, 
                                        self.ParamDict.values())

    def purgeSharedParams(self):
        """
        purge shared parameters
        WIP
        """
        with revitron.Transaction():
            self.ParamUtils.purgeParams()

    @staticmethod
    def selectAreas(selected):
        """
        Select areas according to heighlited direct shgapes.

        Args:
            selected (obj): Heighlited direct shapes

        Returns:
            obj: Areas
        """
        result = []
        for sel in selected:
            if sel.GetType().Name == 'DirectShape':
                type = DOC.GetElement(sel.GetTypeId())
                typeName = _(type).get('Type Name')
                if typeName.startswith('AreaHelper_'):
                    id = int(typeName.strip('AreaHelper_'))
                    id = DB.ElementId(id)
                    result.append(id)
        return result

    
class _AreaHelper:
    """
    Used to create direct shape for one area.
    """
    def __init__(self, area):
        """
        Initialize an area helper instance related to an area.
        Args:
            area (_type_): Revit area instance.
        """
        self.Area = area
        self.Name = 'AreaHelper_' + str(area.Id.IntegerValue)
        self.doc = revitron.DOC
        self.LevelHandler = LevelHandler()
        self.Height = self.LevelHandler.getHeight(area)
    
    def createDishape(self):
        """
        Loops -> solid -> direct shape.
        """
        def _getCrvToAppend(basept, crv):
            """
            When connecting the start point of a curve with the
            end point of the last curve:
            If distance between two connecting points is too small,
            then try the end point.

            Args:
                basept (obj): Base point
                crv (obj): Curve after the base point

            Returns:
                obj: List of lines to be append to loop
            """
            added_line = None
            start = crv.GetEndPoint(0)
            end = crv.GetEndPoint(1)
            if basept.DistanceTo(end) > 0.0025:
                dist = start.DistanceTo(basept)
                if dist == 0:
                    added_line = [crv]
                elif crv.Length > 0.0025 and dist > 0.0025:
                    added_line = [DB.Line.CreateBound(basept, start)]
                    added_line.append(crv)
                else:
                    added_line = [DB.Line.CreateBound(basept, end)]
            return added_line

        def _makeDishape(solid):
            """
            Create a direct shape using solid.
            """
            cateId = DB.ElementId(DB.BuiltInCategory.OST_Mass)
            lib = DB.DirectShapeLibrary.GetDirectShapeLibrary(self.doc) 
            shapeType = DB.DirectShapeType.Create(self.doc, self.Name , cateId)
            shapeType.SetShape(List[DB.GeometryObject ]([solid]))
            lib.AddDefinitionType(self.Name, shapeType.Id)
            element = DB.DirectShape.CreateElementInstance(
                                                        self.doc, shapeType.Id, 
                                                        cateId, 
                                                        self.Name,
                                                        DB.Transform.Identity)
            element.SetTypeId(shapeType.Id)
            return element  

        try:
            if self.Area.Area > 0:
                seopt = DB.SpatialElementBoundaryOptions()
                segments = self.Area.GetBoundarySegments(seopt)
                loops_col = List[DB.CurveLoop]([])
                for segmentList in segments:
                    loop = DB.CurveLoop()
                    for seg in segmentList:
                        segCrv = seg.GetCurve()
                        if loop.NumberOfCurves() == 0:
                            basePt = segCrv.GetEndPoint(0)
                        crvs_to_append = _getCrvToAppend(basePt, segCrv)
            
                        if crvs_to_append:
                            if loop.NumberOfCurves() == 0:
                                finalPt = segCrv.GetEndPoint(0)
                            for c in crvs_to_append:
                                loop.Append(c)
                            backPt = segCrv.GetEndPoint(0)
                            basePt = segCrv.GetEndPoint(1)

                    if loop.IsOpen():
                        if finalPt.DistanceTo(basePt) > 0.0025:
                            line = DB.Line.CreateBound(basePt, finalPt)
                        else:
                            line = DB.Line.CreateBound(basePt, backPt)
                        loop.Append(line)

                    loops_col.Add(loop)
                solid = DB.GeometryCreationUtilities.CreateExtrusionGeometry(
                                        loops_col, DB.XYZ.BasisZ, self.Height)
                dishape = _makeDishape(solid)
                return dishape
            
        except:
            import traceback
            print traceback.format_exc()
            print self.Area.Id

            
class LevelHandler:
    """
    Functions for handling level infos.
    """

    def __init__(self):
        """
        Initialize a level handler instance by creating level items for all levels.
        """
        self.LevelItems = [LevelItem(l) for l in
                                        revitron.Filter().byCategory('Levels')
                                        .noTypes().getElements()]
        self.Dict = {li.Name : li for li in self.LevelItems}

    def getHeight(self,area):
        """
        Get height of area based on this level,
        by default 3 meters.
        """
        levelItem = self.Dict[area.Level.Name]
        aboveLevelItem = None
        if levelItem.StoryAbove:
            aboveLevelItem = self.Dict[levelItem.StoryAbove]
        else:
            aboveLevelItem = self.getAbove(levelItem)
        if aboveLevelItem:
            height = aboveLevelItem.Elevation - levelItem.Elevation
        else:
            height = 3.28084*3
        return height

    def getAbove(self, levelItem):
        """
        Get the name of the first story level above the given level,
        if not found, return None.
        """
        resultItem = None
        for l in self.LevelItems:
            if l.Story and l.Elevation > levelItem.Elevation:
                if resultItem:
                    if l.Elevation < resultItem.Elevation:
                        resultItem = l
                else:
                    resultItem = l
        return resultItem

    
class LevelItem:
    """
    Contains infos of a level.
    """

    def __init__(self, level):
        """
        Initialize a level item instance.

        Args:
            level (obj): Revit level instance.
        """
        self.Level = level
        self.Name = self.Level.Name
        story = _(level).getParameter('Building Story').getInteger()
        self.Story = True if story == 1 else False
        self.Elevation = level.Elevation
        above = _(level).getParameter('Story Above').getValueString()
        self.StoryAbove = None if above == "Default" else above