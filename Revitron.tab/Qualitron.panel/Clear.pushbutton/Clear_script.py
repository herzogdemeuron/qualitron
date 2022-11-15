import revitron
import qualitron

with revitron.Transaction():
    view = revitron.DOC.ActiveView
    viewElements = revitron.Filter(view.Id).getElements()
    for element in viewElements:
        qualitron.ElementOverrides(view, element).clear()