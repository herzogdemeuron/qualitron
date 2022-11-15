import revitron
import json
import os
import sys
from revitron import Log

class ModelAnalyzer:
    """
    The ``ModelAnalyzer`` class loads and applies configured data providers on a model.
    """
    def __init__(self):
        """
        Inits a new `ModelAnalyzer` instance. Loads a configuration file
        that specifies the various checks configured for the current Revit model.
        """
        configPath = revitron.DocumentConfigStorage().get('qualitron.configpath')

        if configPath:
            if os.path.exists(configPath):
                with open(configPath, 'r') as f:
                    config = json.load(f)
                try:
                    self.providers = config['providers']
                except:
                    Log().error('Invalid analyzer configuration JSON file')
                    sys.exit(1)
            else:
                Log().error('Qualitron config file does not exist.')
                sys.exit(1)
        else:
            Log().error('Set path to Qualitron configuration file.')
            sys.exit(1)

    def run(self, provider):
        """
        Runs an ``ElementListProvider`` with the given 
        provider configuration on the model. 

        Args:
            provider (dict): The provider configuration

        Returns:
            object: Lists of tested, passed and failed elements
        """
        from qualitron.providers import ElementListProvider
        providerConfig = provider.get('config')
        testElements = ElementListProvider(providerConfig).run()

        filters = providerConfig['filters']
        for rule in providerConfig['rules']:
            filters.append(rule)

        providerConfig['filters'] = filters
        passedElements = ElementListProvider(providerConfig).run()

        failedElements = list(set(testElements) - set(passedElements))
        return testElements, passedElements, failedElements
