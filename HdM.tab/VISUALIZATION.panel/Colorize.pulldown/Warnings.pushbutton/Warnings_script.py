import revitron
import qualitron
import sys
from revitron import _
from pyrevit import forms

if _(revitron.ACTIVE_VIEW).get('Sheet Name'):
    forms.alert('Current view is placed on sheet, choose a different view.', ok=True)
    sys.exit()

with revitron.Transaction():
    qualitron.Warnings().colorElements()