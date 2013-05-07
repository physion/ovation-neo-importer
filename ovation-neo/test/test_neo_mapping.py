from nose.tools import istest
from ovation import initVM, DateTime
from ovation.testing import local_stack


def setup_module():
    print "initializing VM"
    initVM()


@istest
def should_import_example_abf():
    with local_stack() as dsc:
        ctx = dsc.getContext()

        proj = ctx.insertProject('ABF import', 'ABF import', DateTime())
        exp = proj.insertExperiment('ABF experiment', DateTime())
        device_info = None
