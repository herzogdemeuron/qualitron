import Autodesk.Revit.UI as ui

class EventManager:
    """setup functions in ui script, only for non modal ui"""
    def __init__(self):
        self.Functions = None
        self.EventInstance = None
    def raiseEvent(self):
        return self.EventInstance.Raise()
    def setFunctions(self,*functions):
        self.Functions = functions
        eventHandler = _EventHandler(functions)
        self.EventInstance = ui.ExternalEvent.Create(eventHandler)

class _EventHandler(ui.IExternalEventHandler):
    def __init__(self,funcs):
        self.funcs = funcs
    def Execute(self,uiapp):
        for func in self.funcs:
            try:
                func()
            except:
                import traceback
                print traceback.format_exc()
        return True
    def GetName(self):
        return "External Event Handler - DT"