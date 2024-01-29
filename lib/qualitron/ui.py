import clr
import wpf
import os.path as op
import revitron
from System import Windows
from pyrevit import forms
from pyrevit import framework
from pyrevit.forms import WPFWindow
from qualitron.event import EventManager
clr.AddReference('System')
from System.Windows.Media import BrushConverter


class ColorSwitchWindow(forms.CommandSwitchWindow):
    """
    Extended form to select from a list of command options.
    """

    def __init__(self,
                context,
                xamlFilesDir,
                xamlSource,
                title,
                width,
                height,
                **kwargs):
        """
        Initialize user input window.
        """
        WPFWindow.__init__(self,
                           op.join(xamlFilesDir, xamlSource),
                           handle_esc=True)
        self.Title = title or 'pyRevit'
        self.Width = width
        self.Height = height

        self._context = context
        self.response = None

        owner = kwargs.get('owner', None)
        if owner:
            # set wpf windows directly
            self.Owner = owner
            self.WindowStartupLocation = \
                framework.Windows.WindowStartupLocation.CenterOwner

        self._setup(**kwargs)

    def colorButtons(self):
        """
        Sets the background color for all buttons according to the corresponding
        hex value in buttonColors. 
        """
        for button in self.button_list.Children:
            key = button.Content
            if key:
                try:
                    brush = BrushConverter().ConvertFrom(self.buttonColors[key])
                    button.Background = brush
                except:
                    pass

    @classmethod
    def show(cls, 
            buttonColors,  #pylint: disable=W0221
            context,
            xamlFilesDir,
            xamlSource,
            title='User Input',
            width=forms.DEFAULT_INPUTWINDOW_WIDTH,
            height=forms.DEFAULT_INPUTWINDOW_HEIGHT,
            **kwargs):
        """
        Show user input window.

        Args:
            context (any): window context element(s)
            title (str): window title
            **kwargs (any): other arguments to be passed to window
        """
        context = sorted(buttonColors.keys())
        dlg = cls(context,
                xamlFilesDir,
                xamlSource,
                title,
                width,
                height,
                **kwargs)
        dlg.buttonColors = buttonColors
        dlg.context = context
        dlg.colorButtons()
        dlg.ShowDialog()

        return dlg.response


class CompareParameterWindow(ColorSwitchWindow):
    """
    Extended form to select from a list of command options.
    Selects elements at button click.
    """

    def __init__(self,
                context,
                xamlFilesDir,
                xamlSource,
                title,
                width,
                height,
                **kwargs):
        super(CompareParameterWindow, self).__init__(context,
                                                xamlFilesDir,
                                                xamlSource,
                                                title,
                                                width,
                                                height,
                                                **kwargs)

    @classmethod
    def show(cls, 
            buttonColors,  #pylint: disable=W0221
            paramValuesDict,
            xamlFilesDir,
            xamlSource,
            title='User Input',
            width=forms.DEFAULT_INPUTWINDOW_WIDTH,
            height=forms.DEFAULT_INPUTWINDOW_HEIGHT,
            **kwargs):
        """
        Show user input window.

        Args:
            context (any): window context element(s)
            title (str): window title
            width (int): window width
            height (int): window height
            **kwargs (any): other arguments to be passed to window
        """
        context = sorted(buttonColors.keys())
        dlg = cls(context,
                xamlFilesDir,
                xamlSource,
                title,
                width,
                height,
                **kwargs)
        dlg.buttonColors = buttonColors
        dlg.paramValuesDict = paramValuesDict
        dlg.colorButtons()
        dlg.Show()

    def process_option(self, sender, args):    #pylint: disable=W0613
        """
        Handle click on command option button. 
        Closes the window and selects all elements with the value of the selected button.
        """
        self.Close()
        if sender:
            selectionIds = [revitron.DB.ElementId(int(x)) for x in self.paramValuesDict['values'][sender.Content]]
            revitron.Selection.set(selectionIds)

    def dragWindow(self, sender, arg):
        self.DragMove()

class SpaceHelperWindow(Windows.Window):
    """
    Area Helper Window UI.

    Args:
        Windows (obj): Inherits Window
    """

    def __init__(self, xamlfile, helperManager):
        """
        Shows Area Helper window.
        As a non-modal window, 
        transactions are in event manager integrated,
        which is used to trigger external commands.

        Args:
            xamlfile (str): xaml file path
            areaHelperManager (obj): Area Helper Manager instance
        """
        wpf.LoadComponent(self, xamlfile)
        self.HelperManager = helperManager
        self.setupEvents()
        self.Status = False
        # Status: if any spaceHleper instances exist
        self.updateStatus()
        self.refreshUi()
    
    def setupEvents(self):
        self.refresh_event = EventManager()
        self.bake_event = EventManager()
        self.close_event = EventManager()
        self.refresh_event.setFunctions(self.HelperManager.toggle,
                                        self.updateStatus,
                                        self.refreshUi)
        self.bake_event.setFunctions(self.HelperManager.bakeDishapes,
                                        self.updateStatus,
                                        self.refreshUi)                                
        self.close_event.setFunctions(self.HelperManager.removeDishapes)

    def updateStatus(self):
        """
        Call check status function from area helper manager,
        for UI reaction.        """
        self.Status = self.HelperManager.checkStatus()

    def refreshUi(self):
        """
        Updates ui according to area helper check result
        """
        if self.Status:
            self.button_refresh.Content = 'Purge'
            self.button_bake.Content = 'Bake'
            self.button_refresh.Tag = ''
            refreshEnable = True
            bakeEnable = True
            comboEnable = False
        elif self.HelperManager.Target:
            # If there are selected spaces as Target.
            self.button_refresh.Content = 'Visualize'
            self.button_bake.Content = ''
            self.button_refresh.Tag = len(self.HelperManager.Target)
            refreshEnable = True
            bakeEnable = False
            comboEnable = True
        else:
            self.button_refresh.Content = ''
            self.button_bake.Content = ''
            self.button_refresh.Tag = ''
            refreshEnable = False
            bakeEnable = False
            comboEnable = True

        self.button_refresh.IsEnabled = refreshEnable
        self.button_bake.IsEnabled - bakeEnable
        self.comboPanel.IsEnabled = comboEnable

    def changeOrder(self, list):
        """
        Sort list,
        add '- ALL -' to top
        """
        if list:
            x = '- ALL -'
            if x in list:
                list.remove(x)
                list.sort()
                list.insert(0, x)
            return list
        else:
            return []

    def refreshClicked(self, sender, e):
        """
        On visualize/purge clicked,
        raises refresh event.
        Tracebacks must be catched to avoid application crash.
        """
        try:
            self.HelperManager.updateMainDict()
            self.updateSelected()
            self.refresh_event.raiseEvent() 
        except:
            import traceback
            print(traceback.format_exc())
    
    def bakeClicked(self, sender, e):
        """
        On bake clicked,
        raises bake event.
        Tracebacks must be catched to avoid application crash.
        """
        try:
            self.HelperManager.updateMainDict()
            self.updateSelected()
            self.bake_event.raiseEvent() 
        except:
            import traceback
            print(traceback.format_exc())
  
    def windowClosing(self, sender, e):
        """
        On windowing closing,
        raises event to purge not baked.
        Tracebacks must be catched to avoid application crash.
        """
        try:

            self.close_event.raiseEvent()
        except:
            import traceback
            print(traceback.format_exc())

    def closeClicked(self, sender, e):
        self.Close()

    def dragWindow(self, sender, e):
        self.DragMove()



class AreasHelperWindow(SpaceHelperWindow):
    """
    Area Helper Window UI.

    Args:
        Windows (obj): Inherits Window
    """

    def __init__(self, xamlfile, helperManager):
        """
        Shows Area Helper window.
        As a non-modal window, 
        transactions are in event manager integrated,
        which is used to trigger external commands.

        Args:
            xamlfile (str): xaml file path
            areaHelperManager (obj): Area Helper Manager instance
        """
        super(AreasHelperWindow, self).__init__(xamlfile, helperManager)
        self.combo_scheme.ItemsSource = self.HelperManager.MainDict

    def updateSelected(self):
        """
        Fetch selected areas according to combo box.
        """
        self.HelperManager.updateTarget(self.combo_scheme.SelectedValue,
                                            self.combo_level.SelectedValue)

    def comboSchemeChanged(self, sender, args):
        """
        On scheme combobox changed,
        updates level combobox and refreshed buttons.
        """
        level_list = self.HelperManager.MainDict[
                        self.combo_scheme.SelectedValue]
        level_list = self.changeOrder(level_list.keys())
        self.combo_level.ItemsSource = level_list
        self.updateSelected()
        self.refreshUi()
        self.combo_level.SelectedValue = '- ALL -'

    def comboLevelChanged(self, sender, args):
        """
        On level combobox changed,
        updates area list from that level
        """
        self.updateSelected()
        self.refreshUi()


class RoomsHelperWindow(SpaceHelperWindow):
    """
    Area Helper Window UI.

    Args:
        Windows (obj): Inherits Window
    """

    def __init__(self, xamlfile, helperManager):
        """
        Shows Area Helper window.
        As a non-modal window, 
        transactions are in event manager integrated,
        which is used to trigger external commands.

        Args:
            xamlfile (str): xaml file path
            areaHelperManager (obj): Area Helper Manager instance
        """
        super(RoomsHelperWindow, self).__init__(xamlfile, helperManager)
        self.setupLevelCombo()

    def updateSelected(self):
        """
        Fetch selected areas according to combo box.
        """
        self.HelperManager.updateTarget(self.combo_level.SelectedValue)

    def setupLevelCombo(self):
        """
        On scheme combobox changed,
        updates level combobox and refreshed buttons.
        """
        level_list = self.HelperManager.MainDict.keys()
        level_list = self.changeOrder(level_list)
        self.combo_level.ItemsSource = level_list
        self.combo_level.SelectedValue = '- ALL -'
        self.updateSelected()
        self.refreshUi()

    def comboLevelChanged(self, sender, args):
        """
        On level combobox changed,
        updates area list from that level
        """
        self.updateSelected()
        self.refreshUi()