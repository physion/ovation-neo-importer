__author__ = 'barry'
__copyright__ = 'Copyright (c) 2013. Physion Consulting. All rights reserved.'

from nose.tools import istest

@istest
def should_fail():
    assert False
