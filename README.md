modelmanager
===============================

Version number: 0.0.1
Author: Michel Wortmann, Potsdam Institute of Climate Impact Research, Germany

Overview
--------

A python package to manage (scientific) model runs, input and output.


Dependencies
------------
All python dependencies are listed in `requirements.txt`. Before installing the
package (see below) consider setting up a virtual python environment (`virtualenv mydevenv`).

Installation
--------------------

To install use pip:

    $ pip install modelmanager


Or clone the repo:

    $ git clone https://github.com/mwort/modelmanager.git
    $ python setup.py install



Usage
-----

Initialise project where in your model root directory:
```
cd home/mymodel
python -m modelmanager init
```
Add some interface functions for your model in .mm/interface.py and register them:
```
python -m modelmanager update
```
Start the browser app:
python -m modelmanager browser
```
Navigate to localhost/admin in your browser.


Example
-------


Contributing
------------
Ideas and feature requests are collected in IDEAS.md.
