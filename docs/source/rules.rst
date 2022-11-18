Model Rules
===========

Setting model rules is a key feature of Qualitron. It allows you to define dependencies between categories, types and parameter values that should be kept clean for a particular Revit model.
Once the configured, anyone opening the model can get visual feedback on the observance of those rules by using the *Check Parameter Values button*.
Think of it as Revit filters, but more flexible, more powerful and temporary.

To get started, you need a `configuration.json file <https://github.com/qualitron/qualitron/blob/master/docs/examples/model-analyzer-config.json>`_ 
and load the path to that file into Revit using the *Settings button*.
Once that is done you can start using the *Check Parameter Values button*.

A typical `JSON file <https://github.com/qualitron/qualitron/blob/master/docs/examples/model-analyzer-config.json>`_ that can be used to define a rule that checks if floor have an area between 500 and 5000 looks as follows:

.. code-block:: json

    {
        "providers": [
            {
                "name": "Floors With Area Between 500 and 5000",
                "config": {
                    "filters": [
                    {
                        "rule": "byCategory",
                        "args": [
                        "Floors"
                        ]
                    }
                    ],
                    "rules": [
                    {
                        "rule": "byNumberIsLess",
                        "args": [
                        "Area",
                        5000
                        ]
                    },
                    {
                        "rule": "byNumberIsGreater",
                        "args": [
                        "Area",
                        500
                        ]
                    }
                    ]
                }
            }
        ]
    }
