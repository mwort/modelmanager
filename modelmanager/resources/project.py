"""Custom project functions.

The functions in this file will be available with the project instance as
class methods. Thus, all functions must take the project object 'self' as first
arguement. With this argument all project attributes and methods can be used.
See test function as example.
"""


def test(self, morearguments=1, **evenmore):
    print(self.projectdir)
    res = self.test()
    return res
