import revitron
import qualitron

with revitron.Transaction():
    qualitron.Warnings().colorElements()