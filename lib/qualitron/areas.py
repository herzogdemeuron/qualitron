from System.Collections.Generic import List
import revitron
import Autodesk.Revit.UI as ui
from revitron import _
from revitron import DB
from revitron import DOC
from qualitron import View3dCreator

class AreaHelperManager:
    """creates and removes areaHelper instances"""
    def __init__(self):
        self.Areas = []
        self.AreaDict = {}
        self.ParamDict = {}
        self.updateAreaDict()
        self.updateParamDict()
        self.removeUnused()
        self.ParamUtils = SharedParamUtils("Area Helper",self.ParamDict)
        self.UnusedDishapeTypeIds = []
        self.Dishapes = []
        self.DishapeTypeIdsToPurge = []

    def removeUnused(self):
        allDishapes =  self.getAllDishapes()
        usedDishapeIds = [x.GetTypeId() for x in allDishapes]
        allDishapeTypeIds = revitron.Filter().byClass('DirectShapeType').getElementIds()
        unusedDishapeTypeIds = list(set(allDishapeTypeIds) - set(usedDishapeIds))
        with revitron.Transaction():
            dishapeTypeIds_icol = List[DB.ElementId](unusedDishapeTypeIds)
            DOC.Delete(dishapeTypeIds_icol)

    def getAllDishapes(self):
        return revitron.Filter().byClass('DirectShape').getElements()
    
    def checkStatus(self):
        """
        check if any areaHelper instances exist
        string rules of revitron filter sometimes dont work
        so using lookup parameter
        """
        allDishapes =  self.getAllDishapes()
        self.Dishapes = [x for x in allDishapes
                        if _(x).get("Comments") != "Baked"]
        self.DishapeTypeIdsToPurge = [x.GetTypeId() for x in self.Dishapes]
        if self.DishapeTypeIdsToPurge:
            return True
        else:
            return False

    def updateAreaDict(self):
        """{area scheme name : {levelName : [areas]}"""
        areaSchemes = revitron.Filter().byCategory('AreaSchemes').getElements()
        for arsch in areaSchemes:
            flr = revitron.Filter().byCategory('Areas')
            flr = flr.noTypes().getElements()
            areas = [x for x in flr 
                    if x.Area > 0
                    and x.AreaScheme.Id == arsch.Id]
            dict = {}
            if areas:
                """conclude areas to level ALL"""
                dict["- ALL -"] = areas
            for area in areas:
                levelName = area.Level.Name
                if not levelName in dict:
                    dict[levelName] = []
                list = dict.get(levelName)
                if levelName not in list:
                    list.append(area)
            self.AreaDict[arsch.Name] = dict 

    def updateParamDict(self):
        """parameter list of area"""
        areas = revitron.Filter().byCategory('Areas').getElements()
        if areas:
            area = areas[0]
            for param in area.Parameters:
                name = param.Definition.Name
                readOnly = param.IsReadOnly
                self.ParamDict[name] = "AreaHelper - " + name

    def updateAreas(self,schemeName,levelName):
        """refreshes area dict"""
        self.Areas = self.AreaDict.get(schemeName).get(levelName)
    
    def set3DView(self):
        mass = revitron.DB.BuiltInCategory.OST_Mass
        massId = revitron.DB.ElementId(mass)
        View3dCreator.create('AreaHelper_',[massId])

    def toggle(self):
        status = self.checkStatus()
        self.set3DView()
        if status:
            self.removeDishapes()
            #self.purgeSharedParams()
        else:
            self.createSharedParams()
            self.createDishapes()
            
    def removeDishapes(self):
        with revitron.Transaction():
            dishapeTypeIds_icol = List[DB.ElementId](self.DishapeTypeIdsToPurge)
            DOC.Delete(dishapeTypeIds_icol)
       
    def bakeDishapes(self):
        with revitron.Transaction():
            for ds in self.Dishapes:
                _(ds).set("Comments","Baked")

    def createDishapes(self):
        count = len(self.Areas)
        run = True
        if count > 300:
            decide = ui.TaskDialog.Show("AreaHelper","Visualize " + str(count) 
                                        + " areas?\nThis may take a long time.",
                                        ui.TaskDialogCommonButtons.Yes|
                                        ui.TaskDialogCommonButtons.No)
            if decide == ui.TaskDialogResult.No:
                run = False
        if run:
            with revitron.Transaction():
                for area in self.Areas:
                    if area.Area > 0: 
                        areaHelper = AreaHelper(area)
                        shape = areaHelper.createDishape()
                        if shape:
                            self.ParamUtils.writeParams(area,shape)

    def createSharedParams(self):
        with revitron.Transaction():
            self.ParamUtils.createParams()

    def purgeSharedParams(self):
        with revitron.Transaction():
            self.ParamUtils.purgeParams()

    @staticmethod
    def selectAreas(selected):
        result = []
        for sel in selected:
            if sel.GetType().Name == "DirectShape":
                type = DOC.GetElement(sel.GetTypeId())
                typeName = _(type).get("Type Name")
                if typeName.startswith("AreaHelper_"):
                    id = int(typeName.strip("AreaHelper_"))
                    id = DB.ElementId(id)
                    result.append(id)
        return result

class SharedParamUtils():
    def __init__(self, groupname, paramDict):
        self.File = DOC.Application.OpenSharedParameterFile()
        self.GroupName = groupname
        self.ParamDict = paramDict
        self.ParamSort = DB.BuiltInParameterGroup.PG_ADSK_MODEL_PROPERTIES
        self.Group = self.getGroup(groupname)
        massCategory = DOC.Settings.Categories.get_Item("Mass")
        self.CateSet = DOC.Application.Create.NewCategorySet()
        self.CateSet.Insert(massCategory)

        groupDefinitions = self.Group.Definitions
        self.DefiDict = {x.Name:x for x in groupDefinitions}

    def getGroup(self,groupName):
        """
        get or create wanted parameter 
        group in the shared parameter file
        """
        group = self.File.Groups.get_Item(groupName)
        if not group:
            group = self.File.Groups.Create(groupName)
        return group

    def getDefinition(self,name,readOnly):
        """
        get or create parameter definition
        in the shared parameter file
        """
        if name in self.DefiDict:
            return self.DefiDict[name]
        else:
            opt = DB.ExternalDefinitionCreationOptions(
                        name, DB.SpecTypeId.String.Text)
            opt.UserModifiable = not(readOnly)
            sharedParamDefi = self.Group.Definitions.Create(opt)
            self.DefiDict[name] = sharedParamDefi
            return sharedParamDefi

    def createParams(self):
        for name in self.ParamDict:
            #readOnly = self.ParamDict[name]
            readOnly = True
            sharedParamDefi = self.getDefinition(self.ParamDict[name],readOnly)
            instanceBinding = DOC.Application.Create.NewInstanceBinding(self.CateSet)
            DOC.ParameterBindings.Insert(sharedParamDefi,
                                        instanceBinding,
                                        self.ParamSort)
    
    def getParamFromGroup(self,diShape,paramName):
        param = [p for p in diShape.Parameters 
                if p.Definition.ParameterGroup == self.ParamSort
                and p.Definition.Name == paramName] 
        return param[0]

    def writeParams(self,area,dishape):
        for paramName in self.ParamDict:
            value = area.LookupParameter(paramName).AsValueString()
            target_param = self.getParamFromGroup(
                                dishape,self.ParamDict[paramName])
            if value:
             target_param.Set(str(value))
    
    def purgeParams(self):
        #WIP
        defiIds = [x.Id for x in self.DefiDict.values()]
        defiIds_icol = List[DB.ElementId](defiIds)
        DOC.Delete(defiIds_icol)

class AreaHelper:
    """used to create direct shape for one area"""
    def __init__(self, area):
        self.Area = area
        self.Name = "AreaHelper_" + str(area.Id.IntegerValue)
        self.doc = revitron.DOC
        self.LevelHandler = LevelHandler()
        self.Height = self.LevelHandler.getHeight(area)

    def getDishapeType(self):
        fltr = revitron.Filter().byClass('DirectShapeType')
        fltr = fltr.byStringEquals('Type Name',self.Name).getElements()
        dishapeType = [x.Id for x in fltr 
                       if x.LookupParameter('Type Name')
                       .AsValueString() == self.Name]
        if dishapeType:
            return dishapeType[0]
        else:
            return None

    def deleteDishape(self):
        type.Id = self.getDishapeType().Id
        self.doc.Delete(type.Id)

    def createDishape(self):
        def _getCrvToAppend(basept,crv):
            added_line = None
            start = crv.GetEndPoint(0)
            end = crv.GetEndPoint(1)
            if basept.DistanceTo(end) > 0.0025:
                dist = start.DistanceTo(basept)
                if dist == 0:
                    added_line = [crv]
                elif crv.Length > 0.0025 and dist > 0.0025:
                    added_line = [DB.Line.CreateBound(basept,start)]
                    added_line.append(crv)
                else:
                    added_line = [DB.Line.CreateBound(basept,end)]
            return added_line

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
                        crvs_to_append = _getCrvToAppend(basePt,segCrv)
            
                        if crvs_to_append:
                            if loop.NumberOfCurves() == 0:
                                finalPt = segCrv.GetEndPoint(0)
                            for c in crvs_to_append:
                                loop.Append(c)
                            backPt = segCrv.GetEndPoint(0)
                            basePt = segCrv.GetEndPoint(1)

                    if loop.IsOpen():
                        if finalPt.DistanceTo(basePt) > 0.0025:
                            line = DB.Line.CreateBound(basePt,finalPt)
                        else:
                            line = DB.Line.CreateBound(basePt,backPt)
                        loop.Append(line)

                    loops_col.Add(loop)
                solid = DB.GeometryCreationUtilities.CreateExtrusionGeometry(
                                        loops_col,DB.XYZ.BasisZ,self.Height)
                dishape = self.makeDishape(solid)
                return dishape
            
        except:
            import traceback
            print traceback.format_exc()
            print self.Area.Id

    def makeDishape(self,solid):
        """creates direct shape using solid"""
        cateId = DB.ElementId(DB.BuiltInCategory.OST_Mass)
        lib = DB.DirectShapeLibrary.GetDirectShapeLibrary(self.doc) 
        shapeType = DB.DirectShapeType.Create(self.doc,self.Name ,cateId)
        shapeType.SetShape(List[DB.GeometryObject ]([solid]))
        lib.AddDefinitionType(self.Name,shapeType.Id)
        element = DB.DirectShape.CreateElementInstance(
                                                    self.doc,shapeType.Id,
                                                    cateId,
                                                    self.Name,
                                                    DB.Transform.Identity)
        element.SetTypeId(shapeType.Id)
        return element    

class LevelHandler:
    """get level above and underneath if level items"""
    def __init__(self):
        self.LevelItems = [LevelItem(l) for l in
                                        revitron.Filter().byCategory('Levels')
                                        .noTypes().getElements()]
        self.Dict = {li.Name : li for li in self.LevelItems}

    def getHeight(self,area):
        """
        get height of area based on this level
        by default 3 meters
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

    def getAbove(self,levelItem):
        """
        get the name of the first story level above the given level
        if not found, return None
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
    def __init__(self,level):
        self.Level = level
        self.Name = self.Level.Name
        story = _(level).getParameter('Building Story').getInteger()
        self.Story = True if story == 1 else False
        self.Elevation = level.Elevation
        above = _(level).getParameter('Story Above').getValueString()
        self.StoryAbove = None if above == "Default" else above
     


