# Submodules for each backend

In order to open the output files from a given simulation code, an ozzy submodule for that code is required (in `src/ozzy/backends`). This submodule should contain instructions for parsing the data and the definition of format-specific methods (see [Backend-specific methods](../../data-objects/backend-methods.md)).

Each file format submodule must contain the following minimal quantities.

::: ozzy.backends.template_backend
    options:
        separate_signature: false

