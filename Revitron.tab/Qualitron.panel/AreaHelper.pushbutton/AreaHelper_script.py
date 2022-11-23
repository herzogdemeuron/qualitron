# -*- coding: utf-8 -*-

import sys
from System import Windows
import revitron
import pyrevit
from qualitron import AreaHelperManager, EventManager, View3dCreator
import wpf
import Autodesk.Revit.UI as ui
from System.Collections.Generic import List
 
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
        self.update_status()
        self.refresh_ui()
        self.combo_scheme.ItemsSource = self.areaHelperManager.AreaDict
        self.refresh_event.set_functions(self.areaHelperManager.toggle,
                                        self.update_status,
                                        self.refresh_ui)
        self.bake_event.set_functions(self.areaHelperManager.bake_dishapes,
                                        self.update_status,
                                        self.refresh_ui)                                
        self.close_event.set_functions(self.areaHelperManager.remove_dishapes)

    
    def update_selected_areas(self):
        self.areaHelperManager.update_areas(self.combo_scheme.SelectedValue,
                                            self.combo_level.SelectedValue)
    
    def combo_changed_scheme(self,sender,args):
        level_list =  self.areaHelperManager.AreaDict[
                        self.combo_scheme.SelectedValue]
        level_list = self.change_order(level_list.keys())
        self.combo_level.ItemsSource = level_list
        self.update_selected_areas()
        self.refresh_ui()
        self.combo_level.SelectedValue = "- ALL -"

    def combo_changed_level(self,sender,args):
        self.update_selected_areas()
        self.refresh_ui()

    def update_status(self):
        self.areaHelperCheck = self.areaHelperManager.check_status()

    def refresh_ui(self):
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

    def change_order(self,list):
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

    def refresh_click(self,sender,e):
        try:
            self.areaHelperManager.update_area_dict()
            self.update_selected_areas()
            self.refresh_event.raise_event() 
        except:
            import traceback
            print traceback.format_exc()
    
    def bake_click(self,sender,e):
        try:
            self.areaHelperManager.update_area_dict()
            self.update_selected_areas()
            self.bake_event.raise_event() 
        except:
            import traceback
            print traceback.format_exc()
  
    def Window_Closing(self,sender,e):
        try:

            self.close_event.raise_event()
        except:
            import traceback
            print traceback.format_exc()


selection = revitron.Selection.get()
runWindow = True
if selection:
    areaIds = AreaHelperManager.select_areas(selection)
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
    doc.MassDisplayTemporaryOverride = db.MassDisplayTemporaryOverrideType.ShowMassFormAndFloors
    main = MainWindow()
    main.Show()

