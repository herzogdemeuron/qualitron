import revitron
import sys
import qualitron
from revitron import _
from pyrevit import forms
from System.Collections.Generic import List

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
            try:
                string = elementParameter.getString()
                if string:
                    return string
                else:
                    return None
            except:
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
        
class SharedParamUtils():
    def __init__(self, groupname,paramGroup):
        """
        creates/writes shared parameters

        Args:
            groupname (str): shared parameter group name in the text file
            paramGroup (obj): BuiltInParameterGroup of the instance for creating/writing
        """

        self.File = revitron.DOC.Application.OpenSharedParameterFile()
        self.ParamGroup = paramGroup
        self.Group = self._getGroup(groupname)
        groupDefinitions = self.Group.Definitions
        self.DefiDict = {x.Name:x for x in groupDefinitions}

    def _getGroup(self,groupName):
        """
        get or create wanted parameter group
        in the shared parameter file
        """
        group = self.File.Groups.get_Item(groupName)
        if not group:
            group = self.File.Groups.Create(groupName)
        return group

    def _getDefinition(self,name,readOnly,
                    paramType=revitron.DB.SpecTypeId.String.Text):
        """
        get or create parameter definition
        in the shared parameter file
        """
        if name in self.DefiDict:
            return self.DefiDict[name]
        else:
            opt = revitron.DB.ExternalDefinitionCreationOptions(name,paramType)
            opt.UserModifiable = not(readOnly)
            sharedParamDefi = self.Group.Definitions.Create(opt)
            self.DefiDict[name] = sharedParamDefi
            return sharedParamDefi

    def createParams(self,category,paramNames,readOnly=True):
        """creates shared parameter to category instances

        Args:
            category (obj): target category
            paramGroup (obj): parameter group of instance property
            paramNames (list): list of parameter names to create
            readOnly (bool, optional): if the paramer should be user modifible
        """
        for name in paramNames:
            sharedParamDefi = self._getDefinition(name,readOnly)
            cateSet = revitron.DOC.Application.Create.NewCategorySet()
            cateSet.Insert(category)
            instanceBinding = revitron.DOC.Application.Create.NewInstanceBinding(cateSet)
            revitron.DOC.ParameterBindings.Insert(sharedParamDefi,
                                                instanceBinding,
                                                self.ParamGroup)
    
    def _getParamFromGroup(self,instance,paramName):
        """
        gets the first parameter of an instance
        in a specific parameter group with parameter name

        Args:
            instance (obj): instance
            paramGroup (obj): parameter group of instance property
            paramName (_type_): name of target parameter

        Returns:
            parameter object
        """
        param = [p for p in instance.Parameters 
                if p.Definition.ParameterGroup == self.ParamGroup
                and p.Definition.Name == paramName] 
        return param[0]

    def writeParamstoDishape(self,area,dishape,paramDict):
        """
        copies parameter values from area to direct shape instance

        Args:
            area (obj): source area instance
            dishape (obj): target direct shape instance
            paramDict (dict): dictionary {parameter name in area: parameter name in direct shape}
        """
        for paramName,targetName in paramDict.items():
            value = area.LookupParameter(paramName).AsValueString()
            target_param = self._getParamFromGroup(
                                dishape,targetName)
            if value:
             target_param.Set(str(value))
    