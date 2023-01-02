# -*- coding: utf-8 -*-

import revitron
import pyrevit
from qualitron import AreaHelperManager,AreaHelperWindow
import Autodesk.Revit.UI as ui
 
if __name__ == "__main__":

    xamlfile = pyrevit.script.get_bundle_file("ui.xaml")
    selection = revitron.Selection.get()
    runWindow = True

    # Select areas function
    if selection:
        areaIds = AreaHelperManager.selectAreas(selection)
        if areaIds:
            count = str(len(areaIds))
            decide = ui.TaskDialog.Show("AreaHelper","Select " + count + " area(s)?",
                                        ui.TaskDialogCommonButtons.Yes|
                                        ui.TaskDialogCommonButtons.No
                                        )
            if decide == ui.TaskDialogResult.Yes:
                runWindow = False
                revitron.Selection.set(areaIds)
                
    # If no selection, show window
    if runWindow:
        revitron.DOC.MassDisplayTemporaryOverride = revitron.DB\
                                        .MassDisplayTemporaryOverrideType\
                                        .ShowMassFormAndFloors
        main = AreaHelperWindow(xamlfile,
                                AreaHelperManager())
        main.Show()

