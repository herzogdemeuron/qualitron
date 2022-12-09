import Autodesk.Revit.UI as ui


class EventManager:
    """
    Setup functions in ui script, only for non modal ui.
    """
    def __init__(self):
        """
        Initialize functions to an event handler.
        """
        self.Functions = None
        self.EventInstance = None

    def raiseEvent(self):
        """
        Raise event.

        Returns:
            obj: Trigger raise function in event instance.
        """
        return self.EventInstance.Raise()
    
    def setFunctions(self, *functions):
        """
        Create external event and add functions.
        """
        self.Functions = functions
        eventHandler = _EventHandler(functions)
        self.EventInstance = ui.ExternalEvent.Create(eventHandler)

        
class _EventHandler(ui.IExternalEventHandler):
    """
    External event handler class.
    """

    def __init__(self, funcs):
        """
        Initialize an event handler.

        Args:
            funcs (obj): Functions to excute.
        """
        self.funcs = funcs

    def Execute(self, uiapp):
        """
        Execute functions when event raised.

        Returns:
            bool: If execute successfully.
        """
        for func in self.funcs:
            try:
                func()
            except:
                import traceback
                print(traceback.format_exc())
        return True
    
    def GetName(self):
        """
        Name of the event handler.

        Returns:
            str: Name.
        """
        return 'External Event Handler - DT'