# CHANGE LOG

## development


## v0.8 (2025-01-22)
* Support GRASS version 8
* settings.FunctionInfo: support project functions of builtin type.
* Stability fixes.


## v0.7 (2021-03-19)
* Allow project loading without resource dir (`resourcedir=False`).
* Allow non-default address:port settings to browser start.
* Bug and stability fixes.


## v0.6 (2019-12-03)
* Enable standalone use of `GrassAttributeTable, ReadWriteDataFrame, ProjectOrRunData`
* Bug and stability fixes


## v0.5 (2018-12-14)
* Allow parsing of --projectdir/-p as first argument of commandline
* Various fixes, especially in clone plugin
* Added GroupPlugin for simple grouper plugins
* Boolean CLI arguments are set to False via --not-<arg>


## v0.4 (2018-11-10)
* Allow capitalised plugins and dont change plugins to lowercase. Existing
  plugins are all changed to lowercase and the browser plugin needs to be
  imported via `from modelmanager.plugins.browser import browser`.
* Rename ResultFile and ResultIndicator to File and Indicator in browser plugin.
* Allow clones with a linked resources load the same browser app.
* GrassAttributeTable now works without grass and doesnt support the
  `add_attributes` attribute anymore.
* Read `GrassModule` arguments from specified settings dict rather than any
  setting.
* New defaults argument to `SettingsManager.load`.
* Implement optional `argcomplete` support for the commandline interface.


## v0.3 (2018-08-01)
* first release on PyPI (PyPI name changed to model-manager)
* added *grass* plugin
* added *pandas* plugin
* *browser API* debugged and improved
* many smaller improvements


## v0.2 (2018-02-09)
* implement call function (and view settings) API for the browser plugin
* all browser tables/models are defined in the browser resources models.py, all
  modelmanager tables are abstract models


## v0.1 (2018-02-07)
* implementation of core settings file and project class with commandline interface
* browser plugin: Django app that allows saving and viewing of tables in the browser
* templates plugin: easy read and write of templated model input files
* clones plugin: project cloning with optional linking or ignoring
