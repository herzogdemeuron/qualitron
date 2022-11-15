import clr
import os.path as op
import revitron
from pyrevit import forms
from pyrevit import framework
from pyrevit.forms import WPFWindow
clr.AddReference('System')
from System.Windows.Media import BrushConverter


class ColorSwitchWindow(forms.CommandSwitchWindow):
    '''
    Extended form to select from a list of command options.

    Args:
        context (list[str]): list of command options to choose from
        switches (list[str]): list of on/off switches
        message (str): window title message
        config (dict): dictionary of config dicts for options or switches
        recognize_access_key (bool): recognize '_' as mark of access key
    '''

    def __init__(self,
                context,
                xamlFilesDir,
                xamlSource,
                title,
                width,
                height,
                **kwargs):
        '''
        Initialize user input window.
        '''
        WPFWindow.__init__(self,
                           op.join(xamlFilesDir, xamlSource),
                           handle_esc=True)
        self.Title = title or 'pyRevit'
        self.Width = width
        self.Height = height

        self._context = context
        self.response = None

        # parent window?
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
        """Handle click on command option button."""
        self.Close()
        if sender:
            selectionIds = [revitron.DB.ElementId(int(x)) for x in self.paramValuesDict['values'][sender.Content]]
            revitron.Selection.set(selectionIds)
