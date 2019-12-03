modelmanager
===============================

Version number: 0.6

Author: Michel Wortmann, Potsdam Institute of Climate Impact Research, Germany

Overview
--------

A python package to create flexible APIs for (scientific) models.


Dependencies
------------
Modelmanager itself has no dependencies, but some of its plugins do. They will
direct you two install them through `pip`.
Python development dependencies are listed in `requirements_dev.txt`. Before
installing the any package (see below) consider setting up a virtual python
environment (`virtualenv mydevenv`).

Installation
--------------------

To install use pip:

    $ pip install modelmanager


Or clone the repo:

    $ git clone https://github.com/mwort/modelmanager.git
    $ python setup.py install


Concept
-------
The model
The modelmanager links with your model like illustrated in this file structure:
```
modeldir/               # your main model directory
    mm/                 # the modelmanager resource directory
        settings.py     # define or import here all variables, functions and plugins
	      browser/        # this is a plugin directory, e.g. for the browser app

    modelexec           # all your model resources
    input/
    output/
```
With this setup you can either use your model interface through the commandline
or through the python API (see Usage below).


Usage
-----

Initialise project where in your model root directory:
```
cd home/mymodel
modelmanager init
```
Add some variables, functions or plugins for your model in mm/settings.py and
call them on the commandline like this:
```
modelmanager example_function --example_argument=2
```
Or use your new model api in a Python script like this:
```
import modelmanager as mm

project = mm.Project()
result = project.example_function()
```

Use the browser app by adding this line to your settings:
```
from modelmanager.plugins.browser import *
```
Then start the application on the commandline:
```
modelmanager startbrowser
```
Navigate to localhost/admin in your browser.


Contributing
------------
Bug reports, ideas and feature requests welcome on Github.

## Testing
Run test in tests/ like this:
```
make                                # runs all tests
python test_project.py              # just runs test_projects with call stats
python -m unittest test_project.Settings  # just run Settings tests
make clean                          # clean any leftover test output
```
`make` should pass before submitting a pull/merge request.


Releasing
---------
- add entry in `CHANGELOG.md`
- change version number in `__init__.py` and `README.md`, tag and commit (`make version`)
- build sdist and push to git and pypi (`make release`)
