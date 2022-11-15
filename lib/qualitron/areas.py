from System.Collections.Generic import List
import revitron
db = revitron.DB
_ = revitron._
#doc = revitron.DOC
#import Autodesk.Revit.UI as ui

class AreaHelperManager:
    """creates and removes areaHelper instances"""
    def __init__(self):
        self.Doc = revitron.DOC
        self.Areas = None
        self.ParamName = None
        self.AreaDict = {}
        self.ParamList = []
        self.update_scheme_dict()
        self.update_param_list()
    
    def check_status(self):
        """check if any areaHelper instances exist"""
        dishapeTypeIds = revitron.Filter().byClass('DirectShapeType')
        dishapeTypeIds = dishapeTypeIds.byStringBeginsWith('Type Name', 'Area').getElementIds()
        if dishapeTypeIds:
            return True
        else:
            return False

    def update_scheme_dict(self):
        """{area scheme name : [areas]}"""
        areaSchemes = revitron.Filter().byCategory('AreaSchemes').getElements()
        for arsch in areaSchemes:
            areas = revitron.Filter().byCategory('Areas')
            areas = areas.noTypes().byNumberIsGreater('Area', 0).getElements()
            areas = [x for x in areas if x.AreaScheme.Id == arsch.Id]
            self.AreaDict[arsch.Name] = areas

    def update_param_list(self):
        """parameter list of area"""
        areas = revitron.Filter().byCategory('Areas').getElements()
        if areas:
            area = areas[0]
            self.ParamList = [p.Definition.Name for p in area.Parameters]
            #if not p.IsReadOnly and (p.Definition.ParameterType == db.ParameterType.Text)]

    def update_areas(self,areaSchemeName):
        """refreshes area dict"""
        self.Areas = self.AreaDict.get(areaSchemeName)
    def update_param(self,areaParamName):
        self.ParamName = areaParamName

    def toggle_dishapes(self):
        status = self.check_status()
        if status:
            self.remove_dishapes()
        else:
            self.create_dishapes()

    def remove_dishapes(self):
        t = revitron.DB.Transaction(self.Doc,"remove area helper instances")
        t.Start()
        dishapeTypeIds = revitron.Filter().byClass('DirectShapeType')
        dishapeTypeIds = dishapeTypeIds.byStringBeginsWith('Type Name', 'Area').getElementIds()
        dishapeTypeIds_icol = List[db.ElementId](dishapeTypeIds)
        self.Doc.Delete(dishapeTypeIds_icol)
        t.Commit()

    def create_dishapes(self):
        t = revitron.DB.Transaction(self.Doc,"create area helper instances")
        t.Start()
        for area in self.Areas:
            if area.Area > 0: 
                areaHelper = AreaHelper(area,self.ParamName)
                shape = areaHelper.modify_dishape()
        t.Commit()


class AreaHelper:
    """used to create direct shape for one area"""
    def __init__(self, area, paramName = None):
        self.Area = area
        self.ParamName = paramName
        self.Name = "AreaHelper_" + str(area.Id.IntegerValue)
        self.doc = revitron.DOC
        self.LevelHandler = LevelHandler()
        self.AreaLevelName = area.Level.Name
        self.AreaLevelItem = self.LevelHandler.Dict[self.AreaLevelName]
        """get dishape bottom and top height"""
        self.VolBottomLevelItem = self.get_area_vol_bo()
        if self.VolBottomLevelItem:
            self.VolBottom = self.VolBottomLevelItem.Elevation
        else:
            self.VolBottom = 0

        self.VolTopLevelItem = self.get_area_vol_to()
        if self.VolTopLevelItem:
            self.VolTop = self.VolTopLevelItem.Elevation
        else:
            self.VolTop = self.VolBottom + 3.28084
        
    def get_area_vol_bo(self):
        """
        get area volume bottom level item
        if no level returns None
        """
        if self.AreaLevelItem.Story:
            result = self.AreaLevelItem
        else:
            under = self.LevelHandler.get_under(self.AreaLevelItem)
            if under:
                result = under
            else:
                above = self.LevelHandler.get_above(self.AreaLevelItem)
                if above:
                    result = above
                else:
                    result = None
        return result

    def get_area_vol_to(self):
        """
        get area volume top level item
        if no level returns None
        """
        story = self.AreaLevelItem.Story
        storyAbove = self.AreaLevelItem.StoryAbove
        if story and storyAbove:
            result = self.LevelHandler.Dict[storyAbove]
        else:
            if self.VolBottomLevelItem:
                above = self.LevelHandler.get_above(self.VolBottomLevelItem)
                if above:
                    result = above
                else:
                    result = None
            else:
                result = None
        return result
    
    def set_centroid(self,xyz):
        x = str(xyz.X)
        y = str(xyz.Y)
        return x + "*" + y
    def get_centroid(self,str):
        xy = str.split("*")
        return xy

    def get_dishape_type(self):
        try:
            dishapeType = revitron.Filter().byClass('DirectShapeType')
            dishapeType = dishapeType.byStringEquals('Type Name',self.Name)
            return dishapeType
        except:
            return None

    def delete_dishape(self):
        type = self.get_dishape_type().getElementIds()
        dishapeTypeIds_icol = List[db.ElementId](type)
        self.doc.Delete(dishapeTypeIds_icol)

    def modify_dishape(self):
        try:
            ext_dishape = self.get_dishape_type().getElements()
            if self.Area.Area > 0:
            
                """ui.TaskDialog.Show("Fehler", str(self.Area.Id.IntegerValue))"""
                seopt = db.SpatialElementBoundaryOptions()
                segments = self.Area.GetBoundarySegments(seopt)
                loops_col = List[db.CurveLoop]([])
                for segmentList in segments:
                    loop = db.CurveLoop()
                    #print "loop number init"
                    #print loop.NumberOfCurves()

                    #print "seg count"
                    #print len(segmentList)

                    for seg in segmentList:
                        #print "---------"
                        segCrv = seg.GetCurve()
                        #print "start point"
                        #print [segCrv.GetEndPoint(0).X/3.28084,segCrv.GetEndPoint(0).Y/3.28084]
                        #print "end point"
                        #print [segCrv.GetEndPoint(1).X/3.28084,segCrv.GetEndPoint(1).Y/3.28084]
                        #print "seg curve length"
                        #print segCrv.Length/3.28084
                        if segCrv.Length > 0.0025:
                            ept = segCrv.GetEndPoint(0)
                            #print "now number of crvs in loop"
                            #print loop.NumberOfCurves()
                            if loop.NumberOfCurves()>0:
                                #print "distance"
                                #print spt.DistanceTo(ept)         
                                if spt.DistanceTo(ept) > 0.0025: 

                                    line = db.Line.CreateBound(spt,ept)
                                    loop.Append(line)
                                    #print "added line to loop"
                                    #print "loop number"
                                    #print loop.NumberOfCurves()
                            else:
                                final_ept = ept
                            loop.Append(segCrv)
                            #print "added crv to loop"
                            #print "loop number"
                            #print loop.NumberOfCurves()
                            spt = segCrv.GetEndPoint(1)
                    if loop.IsOpen():
                        #print "loop is open"
                        line = db.Line.CreateBound(spt,final_ept)
                        #print "added final line to loop"
                        #print "loop number"
                        #print loop.NumberOfCurves()
                        loop.Append(line)
                    
                    #print "final loop curve number"
                    #print loop.NumberOfCurves()
                    #print "--------"



                    loops_col.Add(loop)
                thickness = self.VolTop - self.VolBottom
            
                simple_solid = db.GeometryCreationUtilities.CreateExtrusionGeometry(loops_col,db.XYZ.BasisZ,thickness)


                new_centriod = simple_solid.ComputeCentroid()
                if ext_dishape:
                    description = _(ext_dishape[0]).get("Description")
                    ext_centroid = self.get_centroid(description)
                    ext_point = db.XYZ(float(ext_centroid[0]),float(ext_centroid[1]),0)
                    new_point = db.XYZ(new_centriod.X,new_centriod.Y,0)
                    distance = ext_point.DistanceTo(new_point)
                    if distance>= 0.1:
                        self.delete_dishape()
                        self.make_dishape(simple_solid,loop)
                else:
                    self.make_dishape(simple_solid,loop)


        
            else:
                self.delete_dishape()

        except:
            import traceback
            print traceback.format_exc()
            print self.Area.Id
            #print "--------------------END--------------------"

    def make_dishape(self,solid,loop):
        """move a simple extruded solid to the right Z, uses it to create a direct shape"""
        cateId = db.ElementId(db.BuiltInCategory.OST_Mass)
        lib = db.DirectShapeLibrary.GetDirectShapeLibrary(self.doc) 
        loopElevation =  loop.GetPlane().Origin.Z
        offset_Z = self.VolBottom - loopElevation
        transform = db.Transform.CreateTranslation(db.XYZ(0,0,offset_Z))
        solid1 = db.SolidUtils.CreateTransformed(solid,transform)
        shapeType = db.DirectShapeType.Create(self.doc,self.Name ,cateId)
        shapeType.SetShape(List[db.GeometryObject ]([solid1]))
        centroid = solid1.ComputeCentroid()
        _(shapeType).set("Description",self.set_centroid(centroid))
        lib.AddDefinitionType(self.Name,shapeType.Id)

        element = db.DirectShape.CreateElementInstance(
                                                        self.doc,shapeType.Id,
                                                        cateId,
                                                        self.Name,
                                                        db.Transform.Identity)
        element.SetTypeId(shapeType.Id)
        if self.ParamName:
            param = _(self.Area).getParameter(self.ParamName).getValueString()
            _(element).set("Comment",param)
        return element    


class LevelHandler:
    """get level above and underneath if level items"""
    def __init__(self):
        allLevels = revitron.Filter().byCategory('Levels').noTypes().getElements()
        self.LevelItems = [LevelItem(level) for level in allLevels]
        self.Dict = {li.Name : li for li in self.LevelItems} 

    def get_under(self,levelItem):
        """
        get the name of the first story level beneath a given level
        if not found, return None
        """
        resultItem = None
        for l in self.LevelItems:
            if l.Story and l.Elevation < levelItem.Elevation:
                if resultItem:
                    if l.Elevation > resultItem.Elevation:
                        resultItem = l
                else:
                    resultItem = l
        return resultItem
    
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
     


