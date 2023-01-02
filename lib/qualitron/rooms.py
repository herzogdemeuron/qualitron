from System.Collections.Generic import List
import revitron
import Autodesk.Revit.UI as ui
from revitron import _
from revitron import DB
from revitron import DOC
from qualitron import View3dCreator, SharedParamUtils, AreaHelperManager, AreaHelper


class RoomHelperManager(AreaHelperManager):
    def __init__(self):
        """
        Initialize instance of the class.
        """
        self.Rooms = []
        self.RoomDict = {}
        self.ParamDict = {}
        self.updateRoomDict()
        self.updateParamDict('Rooms', 'RoomHelper - ')
        self._removeUnused()
        paramGroup = revitron.DB.BuiltInParameterGroup\
                                .PG_ADSK_MODEL_PROPERTIES
        self.ParamUtils = SharedParamUtils('Room Helper', paramGroup)
        self.Dishapes = []
        self.DishapeTypeIdsToPurge = []

    def updateRoomDict(self):
        """
        Update room dict.
        {levelName : [rooms]}
        """
        flr = revitron.Filter().byCategory('Rooms')
        flr = flr.noTypes().getElements()
        rooms = [x for x in flr if x.Area > 0]
        self.RoomDict = {}
        if rooms:
            self.RoomDict['- ALL -'] = rooms
        for room in rooms:
            levelName = room.Level.Name
            if not levelName in self.RoomDict:
                self.RoomDict[levelName] = []
            self.RoomDict[levelName].append(room)

    def updateRooms(self, levelName):
        """
        Refresh selected rooms.
        """
        self.Areas = self.RoomDict.get(levelName)

class RoomHelper(AreaHelper):
    """
    Used to create direct shape for one area.
    """
    def __init__(self, room):
        """
        Initialize an area helper instance related to an area.
        Args:
            area (_type_): Revit area instance.
        """
        self.Room = room
        self.Name = 'RoomHelper_' + str(room.Id.IntegerValue)
        self.doc = revitron.DOC
        self._opt = revitron.DB.Options()

    def getSolid(self):
        result = None
        geomobjs = self.Room.get_Geometry(self._opt)
        for item in geomobjs:
            type =  item.ToString()
            if "Solid" in type and item.Volume > 0: 
                result = item
                break
            """elif "GeometryInstance" in type:
                solids = item.GetInstanceGeometry()
                for solid in solids:
                    if solid.Volume > 0:
                        result = solid
                        break"""	
        return result

    def createDishape(self):
        """
        geometry -> solid -> direct shape.
        """
        solid = self.getSolid()
        dishape = self.makeDishape(solid)
        return dishape