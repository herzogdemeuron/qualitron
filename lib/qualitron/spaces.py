from System.Collections.Generic import List
import revitron
import Autodesk.Revit.UI as ui
from revitron import _
from revitron import DB
from revitron import DOC
from qualitron import View3dCreator, SharedParamUtils

MIN_GAP = 0.3 # The minimum gap to decide if the last curve should be trimmed
MIN_CRV = 0.3 # The minimum length of a curve to be treated as a curve, otherwise it will be treated as a gap
TRIM = 0.1 # The amount of trimming to be done on the last curve (raw parameter)

class SpaceHelperManager(object):

    def __init__(self, categoryStr, helperClass):
        self.Target = []    # List of selected areas/rooms
        self.MainDict = {}  # Dict for all areas/rooms
        self.ParamDict = {} # Dict for instance params

        self.HelperClass = helperClass
        self.CategoryStr = categoryStr
        self.Prefix = self.CategoryStr + 'Helper_'

        
        self.ParamUtils = SharedParamUtils(self.Prefix)

        self.Dishapes = []
        self.DishapeTypeIdsToPurge = []

        self.updateParamDict()
        self._removeUnused()
    

    def _removeUnused(self):
        """
        Remove unused direct shapes on script startup.
        """
        allDishapes =  self._getAllDishapes()
        usedDishapeTypeIds = [x.GetTypeId() for x in allDishapes]
        flr = revitron.Filter().byClass('DirectShapeType')
        allDishapeTypeIds = flr.byCategory('Mass').getElementIds()
        unusedDishapeTypeIds = list(set(allDishapeTypeIds) - set(usedDishapeTypeIds))
        if unusedDishapeTypeIds:
            with revitron.Transaction():
                dishapeTypeIds_icol = List[DB.ElementId](unusedDishapeTypeIds)
                DOC.Delete(dishapeTypeIds_icol)

    def _getAllDishapes(self):
        """
        Get all existing direct shapes.
        """
        return revitron.Filter().byClass('DirectShape').byCategory('Mass').getElements()
    
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

    def updateParamDict(self):
        """
        Update parameter dict.
        {areaParamName:dishapeParamName}
        """
        spaces = revitron.Filter().byCategory(self.CategoryStr).getElements()
        if spaces:
            space = spaces[0]
            for param in space.Parameters:
                name = param.Definition.Name
                self.ParamDict[name] = self.Prefix + name

    def set3DView(self):
        """
        Create 3D view and set active.
        """
        mass = revitron.DB.BuiltInCategory.OST_Mass
        massId = revitron.DB.ElementId(mass)
        View3dCreator.create(self.Prefix, [massId])

    def toggle(self):
        """
        Switch direct shapes.
        """
        status = self.checkStatus()

        if status:
            self.removeDishapes()
            #self.purgeSharedParams()--WIP
        else:
            self.set3DView()
            with revitron.Transaction():
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
    
    def showWarning(self, count):
        decide = ui.TaskDialog.Show('DT',
                                    'Visualize ' + str(count) 
                                    + ' elements?\nThis may take a long time.',
                                    ui.TaskDialogCommonButtons.Yes|
                                    ui.TaskDialogCommonButtons.No)
        if decide == ui.TaskDialogResult.No:
            return False
        else:
            return True

    def createDishapes(self):
        """
        Create all selected direct shapes.
        """
        count = len(self.Target)
        run = True
        if count > 300:
            run = self.showWarning(count)
        if run:
            for elem in self.Target:
                helper = self.HelperClass(elem)
                shape = helper.createDishape()
                if shape:
                    self.ParamUtils.writeParamstoDishape(elem,
                                                        shape,
                                                        self.ParamDict)

    def createSharedParams(self):
        """
        Create shared parameters to direct shape category.
        """
        massCategory = revitron.DOC.Settings.Categories.get_Item('Mass')
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
    def selectTargets(selected,prefix):
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
                if typeName.startswith(prefix):
                    id = int(typeName.strip(prefix))
                    id = DB.ElementId(id)
                    result.append(id)
        return result


class AreasHelperManager(SpaceHelperManager):
    """
    Manage Area Helper instances, including create, purge and
    write parameter values.
    """
    def __init__(self):
        """
        Initialize instance of the class.
        """
        super(AreasHelperManager, self).__init__('Areas', AreaHelper)
        self.updateMainDict()

    def updateMainDict(self):
        """
        Update dict for all areas.
        {area scheme name : {levelName : [areas]}
        """
        flr = revitron.Filter()
        flr = flr.byCategory('AreaSchemes')
        areaSchemes = flr.getElements()
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
                list.append(area)
            self.MainDict[arsch.Name] = dict 

    def updateTarget(self, schemeName, levelName):
        """
        Refresh selected areas.
        """
        self.Target = self.MainDict.get(schemeName).get(levelName)


class RoomsHelperManager(SpaceHelperManager):
    def __init__(self):
        """
        Initialize instance of the class.
        """
        super(RoomsHelperManager, self).__init__('Rooms', RoomHelper)
        self.updateMainDict()

    def updateMainDict(self):
        """
        Update dict for all rooms.
        {levelName : [rooms]}
        """
        flr = revitron.Filter().byCategory('Rooms')
        flr = flr.noTypes().getElements()
        rooms = [x for x in flr if x.Perimeter > 0]
        self.MainDict = {}
        if rooms:
            self.MainDict['- ALL -'] = rooms
        for room in rooms:
            levelName = room.Level.Name
            if not levelName in self.MainDict:
                self.MainDict[levelName] = []
            self.MainDict[levelName].append(room)

    def updateTarget(self, levelName):
        """
        Refresh selected rooms.
        """
        self.Target = self.MainDict.get(levelName)


class SpaceHelper(object):
    """
    Used to create direct shape for one area or room.
    """
    def __init__(self, elem, prefix):
        """
        Initialize an area helper instance related to an area.
        Args:
            area (_type_): Revit area instance.
        """
        self.Elem = elem
        self.Name = prefix + str(elem.Id.IntegerValue)
    
    
    def _makeSolid(self):
        """
        Create a direct shape instance from a spatial element.
        Args: elem (obj): Spatial element
        Returns: obj: Direct shape instance

        It takes boundary segment lists from the spatial element,
        each segment list contains a array of boundary segments.
        Retrieve the curve from each boundary segment and append them to a curve loop.
        Problem 1: between each boundary segment, there is sometimes tiny gap.
        Problem 2: sometimes one segment is too small to be used to create direct shape.
        And those 2 problems may happen in the same time.

        Solution:
        assum curve1 is the last curve in the curve loop and curve2 to be appended,
        for curve2, firstly check if its start point has a gap with the end point of curve1,
        if there is, try to fill the with a function _fillGap(). After that, check if the length
        of curve2 is too small, if it is, treat it as a gap and fill the gap using the same function _fillGap().
        If the length of curve2 is ok, then append it to the curve loop. 
        After the last boundary segment is appended, check if the curve loop is open, if so fix it.   
        At last, create a direct shape using the curve loop via function _makeDishape().
        """
        seopt = DB.SpatialElementBoundaryOptions()
        segmentLists = self.Elem.GetBoundarySegments(seopt)
        loopList = List[DB.CurveLoop]([])
        for segs in segmentLists:
            crvList = []
            for seg in segs:
                crv = seg.GetCurve()
                if crv.Length < MIN_CRV:
                    continue  
                start = crv.GetEndPoint(0)
                end = crv.GetEndPoint(1)
                lastCrv = crvList[-1] if len(crvList) > 0 else None
                if lastCrv:
                    lastEnd = lastCrv.GetEndPoint(1)
                    if start.DistanceTo(lastEnd) != 0:
                        self._fillGap(crvList, start)
                    if crv.Length < MIN_GAP:
                        self._fillGap(crvList, end)
                    else:
                        crvList.append(crv)
                else:
                    crvList.append(crv)
            self._fixOpenCurveLoop(crvList)
            crvList = List[DB.Curve](crvList)
            crvLoop = DB.CurveLoop.Create(crvList)
            loopList.Add(crvLoop)
        solid = DB.GeometryCreationUtilities.CreateExtrusionGeometry(
                                            loopList, DB.XYZ.BasisZ, self.Height)
        return solid
        

    def _fixOpenCurveLoop(self, crvList):
        """
        Fix the open curve loop.
        Args:
            crvList (obj): Curve loop list
        """
        
        firstCrv = crvList[0]
        lastCrv = crvList[-1]
        firstStart = firstCrv.GetEndPoint(0)
        lastEnd = lastCrv.GetEndPoint(1)
        if firstStart.DistanceTo(lastEnd) != 0:
            self._fillGap(crvList, firstStart)

    def _fillGap(self, crvList, pt):
        """
        Fill the gap between the last curve in crvList and the next pt.

        If the gap doesn't meet the minimum length requirement MIN_GAP,
        the last curve in the list would be trimmed (using _trimCurve()) to ensure the gap to be filled
        with a line of an enough length, then fill the gap with a line.
        If the gap meets the minimum length requirement MIN_GAP, fill the gap with a line.
        Args:
            crvList (obj): Curve loop list
            pt (obj): next point
        """
        lastCrv = crvList[-1]
        lastEnd = lastCrv.GetEndPoint(1)
        gap = pt.DistanceTo(lastEnd)
        if gap < MIN_GAP:
            self._trimCurve(lastCrv)
            crvList.remove(lastCrv)
            crvList.append(lastCrv)
            lastEnd = lastCrv.GetEndPoint(1)
        line = DB.Line.CreateBound(lastEnd, pt)
        crvList.append(line)

    def _trimCurve(self, curve):
        """reduce the length of a curve"""
        param0 = curve.GetEndParameter(0)
        param1 = curve.GetEndParameter(1)
        len = curve.Length
        radio = 1- TRIM/len
        paramEnd = (param1 - param0)*radio + param0
        curve.MakeBound(param0, paramEnd)

    def createDishape(self):
        """
        Create a direct shape using solid.
        """
        try:
            solid = self._makeSolid()
            cateId = DB.ElementId(DB.BuiltInCategory.OST_Mass)
            lib = DB.DirectShapeLibrary.GetDirectShapeLibrary(DOC) 
            shapeType = DB.DirectShapeType.Create(DOC, self.Name , cateId)
            shapeType.SetShape(List[DB.GeometryObject ]([solid]))
            lib.AddDefinitionType(self.Name, shapeType.Id)
            element = DB.DirectShape.CreateElementInstance(
                                                        DOC, shapeType.Id, 
                                                        cateId, 
                                                        self.Name,
                                                        DB.Transform.Identity)
            element.SetTypeId(shapeType.Id)
            return element 
        except:
            print('Error in creating direct shape for element Id: {}'.format(self.Elem.Id))
   
class AreaHelper(SpaceHelper):
    """
    Used to create direct shape for one area.
    """
    def __init__(self, area):
        """
        Initialize an area helper instance related to an area.
        Args:
            area (_type_): Revit area instance.
        """
        super(AreaHelper, self).__init__(area, 'AreasHelper_')
        self.LevelHandler = LevelHandler()
        self.Height = self.LevelHandler.getHeight(area)
        

class RoomHelper(SpaceHelper):
    """
    Used to create direct shape for one area.
    """
    def __init__(self, room):
        """
        Initialize an area helper instance related to an area.
        Args:
            area (_type_): Revit area instance.
        """
        super(RoomHelper, self).__init__(room, 'RoomsHelper_')
        self.Height = self.Elem.get_Parameter(
                                DB.BuiltInParameter.ROOM_HEIGHT).AsDouble()
        
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