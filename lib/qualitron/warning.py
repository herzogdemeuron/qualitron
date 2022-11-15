import revitron
import qualitron


class Warnings:
    """
    Class for visualizing Revit warnings.
    """
    def __init__(self):
        """
        Inits a new instance of the Warnings class.
        """
        self.colorWarning = (243,220,86)
        self.colorNone = (200,200,200)
        self.patternId = revitron.Filter().byClass('FillPatternElement').noTypes().getElementIds()[0]
        self.warningElements = []
        warnings = revitron.DB.Document.GetWarnings(revitron.DOC)
        for warning in warnings:
            for elementId in warning.GetFailingElements():
                self.warningElements.append(elementId)


    def colorElements(self, view=revitron.DOC.ActiveView):
        """
        Colors element that have warnings in a view.

        Args:
            view (object, optional): A Revit view. Defaults to the active view.
        """
        viewElements = revitron.Filter(view.Id).getElementIds()
        viewWarningElements = set(viewElements).intersection(set(self.warningElements))

        for elementId in viewWarningElements:
            element = revitron.DOC.GetElement(elementId)
            qualitron.ElementOverrides(view, element).set(self.colorWarning,
                                                            self.patternId,
                                                            )
                                                            
        for elementId in list(set(viewElements) - set(viewWarningElements)):
            element = revitron.DOC.GetElement(elementId)
            qualitron.ElementOverrides(view, element).set(self.colorNone,
                                                            self.patternId,
                                                            transparency=40
                                                            )
