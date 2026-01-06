# Namespaces and Imports

Namespaces provide a hierarchal mechanism for identifying what lives where.  Anytime a "." is used, it can be read as "from the namespace to the left of the dot, give me the item named on the right of the dot".

Namespace organization is pervasive, but there are three basic levels:

- package: A directory containing a set of modules (Python files) and subpackages (nested directories).
    - module: A Python file containing classes, functions, variables...
        - class: A class definition containing methods and variables.

In the file system, you will find a structure like:

```
package/
    __init__.py
    module1.py
    module2.py
    subpackage1/
        __init__.py
        module3.py
        module4.py
    subpackage2/
        __init__.py
        module5.py
        module6.py
```

One thing to note in that structure is \_\_init\_\_.py.  First and foremost this is a file that identifies the directory as a Python package, and the contents can be imported by other Python modules.  However, upon importing a package, the contents of \_\_init\_\_.py will be executed, so the file also serves as a "constructor" for the package.  Most commonly it simply contains a set of import statements that let users know which modules are considered "public" and meant to be used by modules outside the package and which are "internal" and not intended to be used externally.

Import statements pull functionality from an outside source into a Python module.  There are two forms of the import statement.

- Import statements that start with "import" bring the imported namespace into the module's namespace.  Accessing items from the imported namespace will require the whole path to access items.
- Import statements that start with "from" bring specific parts of the imported namespace into the module's namespace.[^1]

[^1]:
    Python also supports "from package import *", which means bring in everything package has.  Don't use that kind of import.  Though it still exists for reverse-compatability reasons, it was long ago found to be a Bad Idea.

"import" example:

```python
import package.subpackage1

module3_class = package.subpackage1.Module3Class()
```

"from" example:

```python
from package.subpackage1 import Module3Class

module3_class = Module3Class()
```

In general, "from" style imports are preferable to "import" style.

Python also supports what are known as "relative" imports.  Say module3.py needed something from module1.py in the package tree.  The usage of prefixed "." can indicate where in the tree the import is coming from.  One "." means "from this directory".  Two ".." means "from the directory above".  So in module3.py, we may find something like:

```python
from ..module1 import some_function
```

The import statements should always appear at the top of the module file.  Additionally, the imports are organized into sections:

- standard library imports: Functionality brought in from Python's standard library.
- third party imports: Functionality brought in from the Python package ecosystem.
- application imports: Functionality brought in from other parts of the code base.
- local imports: Relative imports bringing in functionality from nearby parts of the package tree.

```python linenums="1"
# standard library imports
from datetime import datetime, UTC

# third party imports
from joblib import delayed, Parallel

# application imports
from long_term_storage.constant.path import Path
from long_term_storage.model import MasterConfigModel
from state_machine.config import Config
from state_machine.decorator import (
    handle_exceptions,
    machine,
    no_exceptions,
    node,
)
from state_machine import AbstractMachine, Failure, Transition

# local imports
from ..eom_delete import MachineEomDelete, StateEomDelete
from .dependency_eom_deletion_candidates import DependencyEomDeletionCandidates
from .state_eom_deletion_candidates import StateEomDeletionCandidates
```

Lines 1 and 2 are imports from the Python's standard library.

Lines 4 and 5 are imports third party package imports.

Lines 7 through 17 are the application imports.

Lines 19 through 22 are the package's local level imports.
