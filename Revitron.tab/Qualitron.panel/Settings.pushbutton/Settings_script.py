import revitron
from pyrevit import forms

path = forms.save_file(file_ext='json', default_name='qualitronConfig')

if path:
    with revitron.Transaction():
        revitron.DocumentConfigStorage().set('qualitron.configpath', path)
