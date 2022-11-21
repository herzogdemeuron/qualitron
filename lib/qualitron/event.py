import Autodesk.Revit.UI as ui


class EventManager:
    """setup functions in ui script, only for non modal ui"""
    def __init__(self):
        self.Functions = None
        self.EventInstance = None
    def raise_event(self):
        return self.EventInstance.Raise()
    def set_functions(self,*functions):
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
        return "TEST"