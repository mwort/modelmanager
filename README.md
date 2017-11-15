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


Concept
-------
The model interface approach used in the modelmanager is best explained in a little file structure:
```
modeldir/                  # main model directory (our model for example has its executable here and an input
                             and output dir, but its really up to you what you do in here, the only
                             specific stuff is the resourcedir)
    resourcedir/
        settings.json      # any project settings that you need for the interface but are not model
                             parameters, e.g. paths to input files. Can also be changed/saved through the package
        interface.py       # here I define all the interface functions, reading/writing input files,
                             interpreting results etc. Can also just import functions from packages as
                             long as the function takes a project instance as first argument
        jobs/              # place to store cluster jobfiles
        clones/	           # default place to store clones of the model, i.e. copies to play around with 
                             or slaves for parallel runs
	    browser/           # this is a django app that tracks and saves my model runs, I used to just have a
                             couple of txt files here but I want to get this into a little browser app
                             where you can see what you have done etc., but mainly work in progress
```
Thats the basic structure. I then have a project class that loads the settings and the interface from the modeldir and there you have a little python API for your model, including commandline interface. In the interface.py you expose your model interface functions to work with the input/ and output/ or overwrite them for specific model cases, a bit like a plugin approach. The "browser" package stores your runs in a database and lets see them with the little browser app.


Usage
-----

Initialise project where in your model root directory:
```
cd home/mymodel
modelmanager init
```
Add some interface functions for your model in .mm/interface.py and register them:
```
modelmanager update
```
Start the browser app:
```
modelmanager browser
```
Navigate to localhost/admin in your browser.


Example
-------


Contributing
------------
Ideas and feature requests are collected in IDEAS.md.
