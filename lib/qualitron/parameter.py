import revitron
from revitron import _
import sys

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
                paramType = _(el).getParameter(pdef.Name).definitionType
                sharedParams.add(ParamDef(pdef.Name, paramType, True))

            elType = revitron.DOC.GetElement(typeId)
            if elType:
                for param in elType.ParametersMap:
                    pdef = param.Definition
                    paramType = _(elType).getParameter(pdef.Name).definitionType
                    sharedParams.add(ParamDef(pdef.Name, paramType, False))

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
    """
    A utility class of functions related to shared parameter. 
    """

    def __init__(self, groupname):
        """
        Initialize class instance with necassary infos related to shared parameters.

        Args:
            groupname (str): Shared parameter group name in the text file
            paramGroup (obj): BuiltInParameterGroup of the instance for creating/writing
        """
        self.File = revitron.DOC.Application.OpenSharedParameterFile()
        self.Group = self._getGroup(groupname)
        groupDefinitions = self.Group.Definitions
        self.DefiDict = {x.Name:x for x in groupDefinitions}
        self.ParamGroup = self._getParamGroup()

    def _getGroup(self, groupName):
        """
        Get or create wanted parameter group
        in the shared parameter file.
        """
        if not self.File:
            print('Please check shared parameter file setting.')
            sys.exit()
        group = self.File.Groups.get_Item(groupName)
        if not group:
            group = self.File.Groups.Create(groupName)
        if not group:
            print('Please check shared parameter file setting.')
        return group

    def _getDefinition(self, name, readOnly):
        """
        Get or create parameter definition
        in the shared parameter file
        """
        try:
            paramType = revitron.DB.SpecTypeId.String.Text
        except:
            paramType = revitron.DB.ParameterType.Text
            
        if name in self.DefiDict:
            return self.DefiDict[name]
        else:
            opt = revitron.DB.ExternalDefinitionCreationOptions(name, paramType)
            opt.UserModifiable = not(readOnly)
            sharedParamDefi = self.Group.Definitions.Create(opt)
            self.DefiDict[name] = sharedParamDefi
            return sharedParamDefi

    def createParams(self, category, paramNames, readOnly=True):
        """
        Create shared parameter to category instances.

        Args:
            category (obj): Target category
            paramNames (list): List of parameter names to create
            readOnly (bool, optional): If the paramer should be user modifible
        """
        for name in paramNames:
            sharedParamDefi = self._getDefinition(name, readOnly)
            cateSet = revitron.DOC.Application.Create.NewCategorySet()
            cateSet.Insert(category)
            instanceBinding = revitron.DOC.Application.Create.NewInstanceBinding(cateSet)
            revitron.DOC.ParameterBindings.Insert(sharedParamDefi,
                                                instanceBinding,
                                                self.ParamGroup)
    
    def _getParamGroup(self):
        """
        Get the parameter group from the shared parameter file.
        """
        try:
            return revitron.DB.BuiltInParameterGroup.PG_ADSK_MODEL_PROPERTIES
        except:
            # for Revit 2024+
            return revitron.DB.GroupTypeId.AdskModelProperties

    
    def _getParamFromGroup(self, instance, paramName):
        """""
        Get the first parameter of an instance
        in a specific parameter group with parameter name.

        Args:
            instance (obj): Instance
            paramName (str): Name of target parameter

        Returns:
            object: Parameter object
        """""
        for p in instance.Parameters:
            try:
                pGroup = p.Definition.ParameterGroup
            except:
                pGroup = p.Definition.GetGroupTypeId()
            if pGroup == self.ParamGroup and p.Definition.Name == paramName:
                return p
        return None

    def writeParamstoDishape(self, area, dishape, paramDict):
        """
        Copy parameter values from area to direct shape instance.

        Args:
            area (obj): Source area instance
            dishape (obj):Target direct shape instance
            paramDict (dict): Dictionary {parameter name in area: parameter name in direct shape}
        """
        for paramName,targetName in paramDict.items():
            value = Parameter.GetValue(area, paramName, True)
            target_param = self._getParamFromGroup(
                                dishape,targetName)
            if value:
             target_param.Set(str(value))
    