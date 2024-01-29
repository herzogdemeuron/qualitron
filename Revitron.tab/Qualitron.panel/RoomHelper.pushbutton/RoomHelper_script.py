# -*- coding: utf-8 -*-

import revitron
import pyrevit
from qualitron import RoomsHelperManager, RoomsHelperWindow
import Autodesk.Revit.UI as ui
 
if __name__ == "__main__":

    xamlfile = pyrevit.script.get_bundle_file("ui.xaml")
    selection = revitron.Selection.get()
    runWindow = True

    if selection:
        areaIds = RoomsHelperManager.selectTargets(selection,'RoomsHelper_')
        if areaIds:
            count = str(len(areaIds))
            decide = ui.TaskDialog.Show("RoomsHelper","Select " + count + " room(s)?",
                                        ui.TaskDialogCommonButtons.Yes|
                                        ui.TaskDialogCommonButtons.No
                                        )
            if decide == ui.TaskDialogResult.Yes:
                runWindow = False
                revitron.Selection.set(areaIds)
                
    if runWindow:
        revitron.DOC.MassDisplayTemporaryOverride = revitron.DB\
                                        .MassDisplayTemporaryOverrideType\
                                        .ShowMassFormAndFloors
        main = RoomsHelperWindow(xamlfile,
                                RoomsHelperManager())
        main.Show()

