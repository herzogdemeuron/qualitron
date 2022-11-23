from System.Collections.Generic import List
import revitron
db = revitron.DB
_ = revitron._
doc = revitron.DOC
import Autodesk.Revit.UI as ui
from qualitron import View3dCreator

class AreaHelperManager:
    """creates and removes areaHelper instances"""
    def __init__(self):
        self.Areas = []
        self.AreaDict = {}
        self.ParamDict = {}
        self.update_area_dict()
        self.update_param_dict()
        self.remove_unused()
        self.ParamUtils = SharedParamUtils("Area Helper",self.ParamDict)

        self.UnusedDishapeTypeIds = []
        self.Dishapes = []
        self.DishapeTypeIdsToPurge = []
    
    def remove_unused(self):
        allDishapes =  self.get_all_dishapes()
        usedDishapeIds = [x.GetTypeId() for x in allDishapes]
        allDishapeTypeIds = revitron.Filter().byClass('DirectShapeType').getElementIds()
        unusedDishapeTypeIds = list(set(allDishapeTypeIds) - set(usedDishapeIds))
        with revitron.Transaction():
            dishapeTypeIds_icol = List[db.ElementId](unusedDishapeTypeIds)
            doc.Delete(dishapeTypeIds_icol)

    def get_all_dishapes(self):
        return revitron.Filter().byClass('DirectShape').getElements()
    
    def check_status(self):
        """
        check if any areaHelper instances exist
        string rules of revitron filter sometimes dont work
        so using lookup parameter
        """
        allDishapes =  self.get_all_dishapes()
        self.Dishapes = [x for x in allDishapes if _(x).get("Comments") != "Baked"]
        self.DishapeTypeIdsToPurge = [x.GetTypeId() for x in self.Dishapes]

        if self.DishapeTypeIdsToPurge:
            return True
        else:
            return False

    def update_area_dict(self):
        """{area scheme name : {levelName : [areas]}"""
        areaSchemes = revitron.Filter().byCategory('AreaSchemes').getElements()
        for arsch in areaSchemes:
            areas = revitron.Filter().byCategory('Areas')
            areas = areas.noTypes().getElements()
            areas = [x for x in areas if x.Area > 0]
            areas = [x for x in areas if x.AreaScheme.Id == arsch.Id]
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

    def update_param_dict(self):
        """parameter list of area"""
        areas = revitron.Filter().byCategory('Areas').getElements()
        if areas:
            area = areas[0]
            for param in area.Parameters:
                name = param.Definition.Name
                readOnly = param.IsReadOnly
                self.ParamDict[name] = "AreaHelper - " + name

    def update_areas(self,schemeName,levelName):
        """refreshes area dict"""
        self.Areas = self.AreaDict.get(schemeName).get(levelName)
    
    def set3DView(self):
        mass = revitron.DB.BuiltInCategory.OST_Mass
        massId = revitron.DB.ElementId(mass)
        View3dCreator.create('AreaHelper_',[massId])

    def toggle(self):
        status = self.check_status()
        self.set3DView()
        if status:
            self.remove_dishapes()
            #self.purge_sharedParams()
        else:
            self.create_sharedParams()
            self.create_dishapes()
            
    def remove_dishapes(self):
        with revitron.Transaction():
            dishapeTypeIds_icol = List[db.ElementId](self.DishapeTypeIdsToPurge)
            doc.Delete(dishapeTypeIds_icol)
       
    def bake_dishapes(self):
        with revitron.Transaction():
            for ds in self.Dishapes:
                _(ds).set("Comments","Baked")

    def create_dishapes(self):
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
                        shape = areaHelper.create_dishape()
                        if shape:
                            self.ParamUtils.write_params(area,shape)

    def create_sharedParams(self):
        with revitron.Transaction():
            self.ParamUtils.create_params()

    def purge_sharedParams(self):
        with revitron.Transaction():
            self.ParamUtils.purge_params()

    @staticmethod
    def select_areas(selected):
        result = []
        for sel in selected:
            if sel.GetType().Name == "DirectShape":
                type = doc.GetElement(sel.GetTypeId())
                typeName = _(type).get("Type Name")
                if typeName.startswith("AreaHelper_"):
                    id = int(typeName.strip("AreaHelper_"))
                    id = db.ElementId(id)
                    result.append(id)
        return result

class SharedParamUtils():
    def __init__(self, groupname, paramDict):
        self.File = doc.Application.OpenSharedParameterFile()
        self.GroupName = groupname
        self.ParamDict = paramDict
        self.ParamSort = db.BuiltInParameterGroup.PG_ADSK_MODEL_PROPERTIES
        self.Group = self.get_group(groupname)

        massCategory = doc.Settings.Categories.get_Item("Mass")
        self.CateSet = doc.Application.Create.NewCategorySet()
        self.CateSet.Insert(massCategory)

        groupDefinitions = self.Group.Definitions
        self.DefiDict = {x.Name:x for x in groupDefinitions}

    def get_group(self,groupName):
        """
        get or create wanted parameter 
        group in the shared parameter file
        """
        group = self.File.Groups.get_Item(groupName)
        if not group:
            group = self.File.Groups.Create(groupName)
        return group

    def get_definition(self,name,readOnly):
        """
        get or create parameter definition
        in the shared parameter file
        """
        if name in self.DefiDict:
            return self.DefiDict[name]
        else:
            opt = db.ExternalDefinitionCreationOptions(
                        name, db.SpecTypeId.String.Text)
            opt.UserModifiable = not(readOnly)
            sharedParamDefi = self.Group.Definitions.Create(opt)
            self.DefiDict[name] = sharedParamDefi
            return sharedParamDefi

    def create_params(self):
        for name in self.ParamDict:
            #readOnly = self.ParamDict[name]
            readOnly = True
            sharedParamDefi = self.get_definition(self.ParamDict[name],readOnly)
            instanceBinding = doc.Application.Create.NewInstanceBinding(self.CateSet)
            doc.ParameterBindings.Insert(sharedParamDefi,
                                        instanceBinding,
                                        self.ParamSort)
    
    def get_param_from_group(self,diShape,paramName):
        param = [p for p in diShape.Parameters 
                if p.Definition.ParameterGroup == self.ParamSort
                and p.Definition.Name == paramName] 
        return param[0]

    def write_params(self,area,dishape):
        for paramName in self.ParamDict:
            value = area.LookupParameter(paramName).AsValueString()
            target_param = self.get_param_from_group(
                                dishape,self.ParamDict[paramName])
            if value:
             target_param.Set(str(value))
    
    def purge_params(self):
        #WIP
        defiIds = [x.Id for x in self.DefiDict.values()]
        defiIds_icol = List[db.ElementId](defiIds)
        doc.Delete(defiIds_icol)

class AreaHelper:
    """used to create direct shape for one area"""
    def __init__(self, area):
        self.Area = area
        self.Name = "AreaHelper_" + str(area.Id.IntegerValue)
        self.doc = revitron.DOC
        self.LevelHandler = LevelHandler()
        self.Height = self.LevelHandler.get_height(area)

    def get_dishape_type(self):
        dishapeType = revitron.Filter().byClass('DirectShapeType')
        dishapeType = dishapeType.byStringEquals('Type Name',self.Name).getElements()
        dishapeType = [x.Id for x in dishapeType 
                       if x.LookupParameter('Type Name')
                       .AsValueString() == self.Name]
        if dishapeType:
            return dishapeType[0]
        else:
            return None

    def delete_dishape(self):
        type.Id = self.get_dishape_type().Id
        self.doc.Delete(type.Id)

    def create_dishape(self):

        def get_crv_to_append(basept,crv):
            added_line = None
            start = crv.GetEndPoint(0)
            end = crv.GetEndPoint(1)
            #print "evaluating crvs to append"
            if basept.DistanceTo(end) > 0.0025:
                #print "total distance enough"
                dist = start.DistanceTo(basept)
                if dist == 0:
                    added_line = [crv]
                    #print "start point at base point"
                elif crv.Length > 0.0025 and dist > 0.0025:
                    #print "start point dosent match basepoint, but both crv and line enough"
                    added_line = [db.Line.CreateBound(basept,start)]
                    added_line.append(crv)
                else:
                    #print "one of start distance of crv is too short, so created one line for total"
                    added_line = [db.Line.CreateBound(basept,end)]
            """if added_line: 
                print "got crvs to append:"
                print added_line
            else:
                print "no crvs to append, skipping" """         
            return added_line
          
        try:
            if self.Area.Area > 0:
                seopt = db.SpatialElementBoundaryOptions()
                segments = self.Area.GetBoundarySegments(seopt)
                loops_col = List[db.CurveLoop]([])
                for segmentList in segments:
                    loop = db.CurveLoop()

                    #print "loop number of crvs:"
                    #print loop.NumberOfCurves()
                    #print "seg count:"
                    #print len(segmentList)

                    for seg in segmentList:

                        segCrv = seg.GetCurve()

                        #print "start point:"
                        #print [segCrv.GetEndPoint(0).X/3.28084,segCrv.GetEndPoint(0).Y/3.28084]
                        #print "end point:"
                        #print [segCrv.GetEndPoint(1).X/3.28084,segCrv.GetEndPoint(1).Y/3.28084]
                        #print "seg curve length:"
                        #print segCrv.Length/3.28084

                        if loop.NumberOfCurves() == 0:
                            #print "start point set as base point"
                            basePt = segCrv.GetEndPoint(0)
                        crvs_to_append = get_crv_to_append(basePt,segCrv)
                        
                        if crvs_to_append:
                            if loop.NumberOfCurves() == 0:
                                #print "set finalPt from start point of the crv"
                                finalPt = segCrv.GetEndPoint(0)
                            for c in crvs_to_append:
                                loop.Append(c)
                            backPt = segCrv.GetEndPoint(0)
                            #print "set basePt to crv end"
                            basePt = segCrv.GetEndPoint(1)

                        #print "now loop curve number:"
                        #print loop.NumberOfCurves()
                        #print "----segment done----"

                    if loop.IsOpen():
                        
                        #print "loop is open"

                        if finalPt.DistanceTo(basePt) > 0.0025:
                            #print "finalPt connected to basePt"
                            line = db.Line.CreateBound(basePt,finalPt)
                        else:
                            #print "final line too short, backPt connected to basePt"
                            line = db.Line.CreateBound(basePt,backPt)

                        loop.Append(line)
                        #print "added final line to loop"
                        #print loop.NumberOfCurves()

                        

                    #print "final loop curve number"
                    #print loop.NumberOfCurves()
                    
                    
                    loops_col.Add(loop)
                solid = db.GeometryCreationUtilities.CreateExtrusionGeometry(
                                        loops_col,db.XYZ.BasisZ,self.Height)
                dishape = self.make_dishape(solid)
                return dishape
        except:
            import traceback
            print traceback.format_exc()
            print self.Area.Id

    def make_dishape(self,solid):
        """creates direct shape using solid"""
        cateId = db.ElementId(db.BuiltInCategory.OST_Mass)
        lib = db.DirectShapeLibrary.GetDirectShapeLibrary(self.doc) 
        shapeType = db.DirectShapeType.Create(self.doc,self.Name ,cateId)
        shapeType.SetShape(List[db.GeometryObject ]([solid]))
        lib.AddDefinitionType(self.Name,shapeType.Id)

        element = db.DirectShape.CreateElementInstance(
                                                    self.doc,shapeType.Id,
                                                    cateId,
                                                    self.Name,
                                                    db.Transform.Identity)
        element.SetTypeId(shapeType.Id)
        return element    

class LevelHandler:
    """get level above and underneath if level items"""
    def __init__(self):
        allLevels = revitron.Filter().byCategory('Levels').noTypes().getElements()
        self.LevelItems = [LevelItem(level) for level in allLevels]
        self.Dict = {li.Name : li for li in self.LevelItems}

    def get_height(self,area):
        """
        get height of area based on this level
        by default 3 meter
        """
        levelItem = self.Dict[area.Level.Name]
        aboveLevelItem = None
        if levelItem.StoryAbove:
            aboveLevelItem = self.Dict[levelItem.StoryAbove]
        else:
            aboveLevelItem = self.get_above(levelItem)
        if aboveLevelItem:
            height = aboveLevelItem.Elevation - levelItem.Elevation
        else:
            height = 3.28084*3
        return height

    def get_above(self,levelItem):
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
     


