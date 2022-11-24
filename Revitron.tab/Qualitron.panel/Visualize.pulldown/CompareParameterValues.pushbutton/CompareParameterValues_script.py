import revitron
import qualitron
import os.path as op

xamlFilesDir = op.dirname(__file__)
xamlSource = 'ColorSwitchWindow.xaml'
colorEqual = '#bfef45'

def compareParameterValues(element, colorEqual):
    import sys
    from revitron import _
    from qualitron import Parameter
    from pyrevit import forms

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
    parameterName = selectedOption.name
    isInstance = selectedOption.isInstance
    value = Parameter.GetValue(element, parameterName, isInstance)

    view = revitron.ACTIVE_VIEW
    viewElements = revitron.Filter(view.Id).noTypes().getElements()
    patternId = revitron.Filter().byClass('FillPatternElement').noTypes().getElementIds()[0]
    colorEqualRGB = qualitron.Color.HEXtoRGB(colorEqual)

    paramValuesDict = {}
    paramValuesDict['values'] = {}
    paramValuesDict['colors'] = {}
    paramValuesDict['colors'][str(value)] = colorEqual
    isolateElementIds = []
    falseColorCount = 0

    for element in viewElements:
        hasParameter = Parameter.Exists(element, parameterName, isInstance)
        if hasParameter:
            isolateElementIds.append(element.Id)
            if _(element).getCategoryName() in ['Curtain Panels', 'Curtain Wall Mullions']:
                try:
                    hostId = element.Host.Id
                    if not hostId in isolateElementIds:
                        isolateElementIds.append(hostId)
                except:
                    pass

            elementParameterValue = Parameter.GetValue(element,
                                            parameterName,
                                            isInstance
                                            )
            elementParameterValue = str(elementParameterValue)

            if elementParameterValue not in paramValuesDict['values']:
                paramValuesDict['values'][elementParameterValue] = []

            paramValuesDict['values'][elementParameterValue].append(str(element.Id))

            if elementParameterValue == value:
                qualitron.ElementOverrides(view, element).set(colorEqualRGB, patternId)
            else:
                if elementParameterValue not in paramValuesDict['colors']:
                    if falseColorCount < len(falseColors):
                        colorDifferent = falseColors[falseColorCount]
                    else:
                        colorDifferent = '#000000'

                    paramValuesDict['colors'][elementParameterValue] = colorDifferent
                    falseColorCount += 1
                else:
                    colorDifferent = paramValuesDict['colors'][elementParameterValue]

                colorDifferentRGB = qualitron.Color.HEXtoRGB(colorDifferent)
                qualitron.ElementOverrides(view, element).set(colorDifferentRGB, patternId)
            
    if switches['Isolate Elements']:
        qualitron.Isolate.byElementIds(isolateElementIds)

    return paramValuesDict


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
