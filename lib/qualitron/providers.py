import revitron

class ElementListProvider(revitron.AbstractDataProvider):
    """
	This data provider returns the ElementIds of filtered elements after applying all
	filters that are defined in the provider configuration.
	"""

    def run(self):
        """
        Run the data provider and return the number of filtered elements.

        Returns:
            object: A list of element ids of filtered elements
        """
        return [x.Id for x in self._filterElements()]

    @property
    def valueType(self):
        """
        The value type for the counter is ``count``.

        Returns:
            string: The value type
        """
        return 'ElementId'
