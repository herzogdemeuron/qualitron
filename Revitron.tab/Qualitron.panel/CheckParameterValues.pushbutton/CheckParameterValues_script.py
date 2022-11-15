import revitron
import qualitron
import sys
from qualitron import Color
from pyrevit import forms


analyzer = qualitron.ModelAnalyzer()
buttons = [x['name'] for x in analyzer.providers]
selectedOption, switches = forms.CommandSwitchWindow.show(buttons, 
                                        switches={'Isolate Elements': False})
if not selectedOption:
    sys.exit()
provider = [x for x in analyzer.providers if x['name'] == selectedOption][0]
testElements, passedElements, failedElements = analyzer.run(provider)
# print(testElements, 'test')
# print(passedElements, 'pass')
# print(failedElements, 'fail')

view = revitron.ACTIVE_VIEW
pattern = revitron.Filter().byClass('FillPatternElement').noTypes().getElementIds()[0]
colorPassed = Color.HEXtoRGB('#4AAB79')
colorFailed = Color.HEXtoRGB('#FFA316')

with revitron.Transaction():
    if switches['Isolate Elements']:
        qualitron.Isolate.byElementIds(testElements)

    for passedElement in passedElements:
        qualitron.ElementOverrides(view, passedElement).set(colorPassed, pattern)

    for failedElement in failedElements:
        qualitron.ElementOverrides(view, failedElement).set(colorFailed, pattern)