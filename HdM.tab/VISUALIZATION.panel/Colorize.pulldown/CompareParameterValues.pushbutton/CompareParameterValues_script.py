import revitron
import qualitron
import os.path as op
import sys
from math import floor
from revitron import _
from qualitron import Parameter, Color
from pyrevit import forms

if _(revitron.ACTIVE_VIEW).get('Sheet Name'):
    forms.alert('Current view is placed on sheet, choose a different view.', ok=True)
    sys.exit()

xamlFilesDir = op.dirname(__file__)
xamlSource = 'ColorSwitchWindow.xaml'
colorEqual = '#bfef45'

def compareParameterValues(element, colorEqual):
    falseColors = [
            '#e6194b',
            '#ffe119',
            '#4363d8',
            '#f58231',
            '#911eb4',
            '#46f0f0',
            '#f032e6',
            '#fabebe',
            '#008080',
            '#e6beff',
            '#9a6324',
            '#fffac8',
            '#800000',
            '#808000',
            '#ffd8b1',
            '#000075',
            '#808080',
            '#dcbeff'
            ]

    options = Parameter.ProcessOptions([element])
    if options:
        selectedSwitch, switches = forms.CommandSwitchWindow.show(sorted(options),
            switches={'Isolate Elements': True},
            message='Visualize parameter:')

    if not selectedSwitch:
        sys.exit()

    selectedOption = options[selectedSwitch]
    paramName = selectedOption.name
    isInstance = selectedOption.isInstance
    value = Parameter.GetValue(element, paramName, isInstance)

    view = revitron.ACTIVE_VIEW
    viewElements = revitron.Filter(view.Id).noTypes().getElements()
    patternId = revitron.Filter().byClass('FillPatternElement').noTypes().getElementIds()[0]
    colorEqualRGB = qualitron.Color.HEXtoRGB(colorEqual)

    paramValuesDict = {}
    paramValuesDict['values'] = {}
    paramValuesDict['colors'] = {}
    paramValuesDict['colors'][str(value)] = colorEqual
    isolateElementIds = []
    index = 0

    for element in viewElements:
        if not Parameter.Exists(element, paramName, isInstance):
            continue

        isolateElementIds.append(element.Id)
        if _(element).getCategoryName() in ['Curtain Panels', 'Curtain Wall Mullions']:
            try:
                hostId = element.Host.Id
                if not hostId in isolateElementIds:
                    isolateElementIds.append(hostId)
            except:
                pass

        paramValue = str(Parameter.GetValue(element,
                                            paramName,
                                            isInstance))

        if paramValue not in paramValuesDict['values']:
            paramValuesDict['values'][paramValue] = []

        paramValuesDict['values'][paramValue].append(str(element.Id))

        if paramValue == value:
            qualitron.ElementOverrides(view, element).set(colorEqualRGB, patternId)
        else:
            if paramValue not in paramValuesDict['colors']:
                usedColorCount = len(paramValuesDict['colors'].keys())
                defaultColorCount = len(falseColors)
                factor = 1 - (1 / (floor(usedColorCount / defaultColorCount) + 1))
                color = falseColors[index % len(falseColors)]
                rgb = Color.HEXtoRGB(color)
                rgb = tint(rgb, factor)
                colorDifferent = Color.RGBtoHEX(rgb)
                paramValuesDict['colors'][paramValue] = colorDifferent
                index += 1

            qualitron.ElementOverrides(view, element).set(
                Color.HEXtoRGB(paramValuesDict['colors'][paramValue]),
                patternId)

    if switches['Isolate Elements']:
        qualitron.Isolate.byElementIds(isolateElementIds)

    return paramValuesDict

def tint(rgb, factor):
    """
    Lightes an rgb color by adding the remainder to white multiplied by a factor.

    Args:
        rgb (list[float]): The rgb color
        factor (float): Multiplication factor

    Returns:
        _type_: _description_
    """
    newR = rgb[0] + ((255 - rgb[0]) * factor)
    newG = rgb[1] + ((255 - rgb[1]) * factor)
    newB = rgb[2] + ((255 - rgb[2]) * factor)
    return [newR, newG, newB]


with revitron.Transaction():
    paramValuesDict = compareParameterValues(
                                            revitron.Selection.first(),
                                            colorEqual
                                            )
    buttonColors = {}
    for key in paramValuesDict['values'].keys():
        buttonColors[str(key)] = paramValuesDict['colors'][key]

    revitron.Selection.set([])

qualitron.CompareParameterWindow.show(
                                buttonColors,
                                paramValuesDict,
                                xamlFilesDir,
                                xamlSource,
                                title='Result',
                                message='Select by Value')
