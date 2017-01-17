*Components*

- input (read and write) / output (read) functions in separate module that are attached to Pro class
    + get functions out of modules: funct=[v for v in swim.__dict__.values() if hasattr(v,'__call__')]
    + attach to instance: self.funct = types.MethodType(method, self)
    + check if all attributes are set for attached function:
        attr = re.findall(r"self\.(\w*)",inspect.getsource(funct))
    + call signiture: (self is Project instance)
        dict = input(self, **writekwargs)
        (pandas object or similar) = ouput(self, **options)
        columtype = output(self, **options) for performance tables
    + how to link file paths to functions? in parameter file, in function defaults?
    + can be extended by user-defined file in addition to standard input/output files

- postprocessing.py: functions to attach to Run class
    + call signiture:
        anything = funct(self,**kwargs) whereas self is the Run instance
    + maybe extended by postprocessing.py in resource dir

- json parameter file
    + on read check
        + valid paths
        + read paths with .pa at the end
    + attach all variables to Pro class

- save results as pandas pickles by listing output functions that return pandas Series/DF
    + storefunctions = ['subbasinQ']
    + add folders in resource dir to save .pa files subbasinQ/0001.pa

- sqlite database interface
    + through pandas.DataFrame.to_sql()
    + run, parameter tables as standard
    + variable performance tables to be specified in parameter file
        + e.g. tables={'hydrology':['NSE','bias']}
        + functions either return float/int or dict with str:float/int
        + all have ID, runID at beginning

- optional GRASS linking
    + smart grass session/mapset management
    + keep track of maps used in project
        + e.g. check names in parameter file exist
    + force mapset for run/evaluation output

- get some inspiration from https://github.com/dtavan/PyBPS 

*Classes*

- Pro: base class
    + methods:
        + load parameters
        + save parameters
        + _attach methods
        + __call__/run for model run
        + storeRun
        + storeResults
        + storeStats

- Run: line in runs table with some useful methods and attributes from other tables
- Parameterset: line in parameter table, simple attribute class

