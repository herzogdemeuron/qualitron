import revitron
import sys
import qualitron
from revitron import _
from pyrevit import forms

class Parameter:
    """
    The ``Parameter`` class simplifies interactions with Revit parameters.
    """
    @staticmethod
    def ProcessOptions(elements, staticParams=None):
        """
        Generates a list of parameters that are shared across a given set of elements.
        The output of this function is intended to be used with the CommandSwitchWindow from pyRevit forms.

        Args:
            elements (object): A list of Revit elements

        Returns:
            dict: A list of strings 
        """
        from collections import namedtuple
        ParamDef = namedtuple('ParamDef', ['name', 'type', 'isInstance'])

        paramSets = []

        for el in elements:
            typeId = el.GetTypeId()
                
            sharedParams = set()
            for param in el.ParametersMap:
                pdef = param.Definition
                sharedParams.add(ParamDef(pdef.Name, pdef.ParameterType, True))

            elType = revitron.DOC.GetElement(typeId)
            if elType:
                for param in elType.ParametersMap:
                    pdef = param.Definition
                    sharedParams.add(ParamDef(pdef.Name, pdef.ParameterType, False))

            paramSets.append(sharedParams)

        if paramSets:
            allSharedParams = paramSets[0]
            for paramSet in paramSets[1:]:
                allSharedParams = allSharedParams.intersection(paramSet)

            if staticParams:
                allStaticParams = set()
                for paramSet in paramSets:
                    for param in paramSet:
                        if param.name in staticParams:
                            allStaticParams.add(param)
                allSharedParams = allSharedParams | allStaticParams
            
            return {'{}'.format(x.name): x for x in allSharedParams}

    @staticmethod
    def GetValue(element, parameter, isInstance):
        """
        Get a parameter value from an element regardless if it is a
        type or instance parameter.

        Args:
            element (object): A Revit element
            parameter (string): The parameter name
            isInstance (bool): Specifies if type or instance parameter

        Returns:
            string: The Revit 'ValueString' for given parameter
        """
        if isInstance:
            elementParameter = _(element).getParameter(parameter)
        elif not isInstance:
            elementType = revitron.DOC.GetElement(element.GetTypeId())
            elementParameter = _(elementType).getParameter(parameter)

        valueString = elementParameter.getValueString()
        if valueString:
            return valueString
        else:
            return None

    @staticmethod
    def Exists(element, parameterName, isInstance):
        """
        Checks if a parameter exists as a type or instance parameter.

        Args:
            element (object): A Revit element
            parameterName (string): The name of the parameter
            isInstance (bool): Specifies if type or instance parameter

        Returns:
            bool: True if parameter exists, otherwise False
        """
        if isInstance:
            return revitron.Parameter(element, parameterName).exists()
        elif not isInstance:
            typeId = element.GetTypeId()
            if str(typeId) == '-1':
                return False
            elementType = revitron.DOC.GetElement(typeId)
            return revitron.Parameter(elementType, parameterName).exists()
        
