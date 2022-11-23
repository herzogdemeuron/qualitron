# -*- coding: utf-8 -*-

from System import Windows
import revitron
import pyrevit
from qualitron import AreaHelperManager, EventManager
import wpf
import Autodesk.Revit.UI as ui
 
doc = revitron.DOC
db =  revitron.DB
uiapp = pyrevit._HostApplication().uiapp
addinId = uiapp.Application.ActiveAddInId
xamlfile = pyrevit.script.get_bundle_file("ui.xaml")

class MainWindow(Windows.Window):
    def __init__(self):
        wpf.LoadComponent(self, xamlfile)
        self.areaHelperManager = AreaHelperManager()
        self.refresh_event = EventManager()
        self.bake_event = EventManager()
        self.close_event = EventManager()
        self.areaHelperCheck = False
        self.updateStatus()
        self.refreshUi()
        self.combo_scheme.ItemsSource = self.areaHelperManager.AreaDict
        self.refresh_event.setFunctions(self.areaHelperManager.toggle,
                                        self.updateStatus,
                                        self.refreshUi)
        self.bake_event.setFunctions(self.areaHelperManager.bakeDishapes,
                                        self.updateStatus,
                                        self.refreshUi)                                
        self.close_event.setFunctions(self.areaHelperManager.removeDishapes)

    
    def updateSelectedAreas(self):
        self.areaHelperManager.updateAreas(self.combo_scheme.SelectedValue,
                                            self.combo_level.SelectedValue)
    
    def comboSchemeChanged(self,sender,args):
        level_list =  self.areaHelperManager.AreaDict[
                        self.combo_scheme.SelectedValue]
        level_list = self.changeOrder(level_list.keys())
        self.combo_level.ItemsSource = level_list
        self.updateSelectedAreas()
        self.refreshUi()
        self.combo_level.SelectedValue = "- ALL -"

    def comboLevelChanged(self,sender,args):
        self.updateSelectedAreas()
        self.refreshUi()

    def updateStatus(self):
        self.areaHelperCheck = self.areaHelperManager.checkStatus()

    def refreshUi(self):
        if self.areaHelperCheck:
            self.button_refresh.Content = "Purge"
            self.button_bake.Content = "Bake"
            self.button_refresh.Tag = ""
            refreshEnable = True
            bakeEnable = True
            comboEnable = False
        elif self.areaHelperManager.Areas:
            self.button_refresh.Content = "Visualize"
            self.button_bake.Content = ""
            self.button_refresh.Tag = len(self.areaHelperManager.Areas)
            refreshEnable = True
            bakeEnable = False
            comboEnable = True
        else:
            self.button_refresh.Content = ""
            self.button_bake.Content = ""
            self.button_refresh.Tag = ""
            refreshEnable = False
            bakeEnable = False
            comboEnable = True

        self.button_refresh.IsEnabled = refreshEnable
        self.button_bake.IsEnabled - bakeEnable
        self.combo_scheme.IsEnabled = comboEnable
        self.combo_level.IsEnabled = comboEnable

    def changeOrder(self,list):
        """change - ALL - to first"""
        if list:
            x = "- ALL -"
            l = list[:]
            if x in l:
                l.remove(x)
                l.sort()
                l.insert(0,x)
            return l
        else:
            return []

    def refreshClicked(self,sender,e):
        try:
            self.areaHelperManager.updateAreaDict()
            self.updateSelectedAreas()
            self.refresh_event.raiseEvent() 
        except:
            import traceback
            print traceback.format_exc()
    
    def bakeClicked(self,sender,e):
        try:
            self.areaHelperManager.updateAreaDict()
            self.updateSelectedAreas()
            self.bake_event.raiseEvent() 
        except:
            import traceback
            print traceback.format_exc()
  
    def windowClosing(self,sender,e):
        try:

            self.close_event.raiseEvent()
        except:
            import traceback
            print traceback.format_exc()


selection = revitron.Selection.get()
runWindow = True
if selection:
    areaIds = AreaHelperManager.selectAreas(selection)
else:
    areaIds = []
if areaIds:
    count = str(len(areaIds))
    decide = ui.TaskDialog.Show("AreaHelper","Select " + count + " area(s)?",
                                ui.TaskDialogCommonButtons.Yes|
                                ui.TaskDialogCommonButtons.No
                                )
    if decide == ui.TaskDialogResult.Yes:
        runWindow = False
        revitron.Selection.set(areaIds)
if runWindow:
    doc.MassDisplayTemporaryOverride = db\
                                    .MassDisplayTemporaryOverrideType\
                                    .ShowMassFormAndFloors
    main = MainWindow()
    main.Show()

