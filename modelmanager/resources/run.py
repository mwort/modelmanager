"""Custom run functions.

The functions in this file will be available with any run instance as
class methods. Thus, all functions must take the run object 'self' as first
arguement. With this argument all run attributes and methods can be used.
See test function as example.
"""

def test(self, morearguments=1, **evenmore):
    print(self.projectdir)
    res = self.test()
    return res
