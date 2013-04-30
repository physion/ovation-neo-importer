"""
Testing utilities for ovation-neo.importer
"""

__copyright__ = 'Copyright (c) 2013. Physion Consulting. All rights reserved.'

from ovation import Guice, OvationApiModule, LocalDatabaseStack


def setup_local_database_stack():
    local_database_stack = _create_local_database_stack()

    local_database_stack.createLocalCloudDatabase(cloudDatabaseName,
                                                  userIdentity,
                                                  PASSWORD,
                                                  localCouchUserName,
                                                  host,
                                                  port,
                                                  userId)


def delete_local_database_stack():
    pass

def _create_local_database_stack():
    injector = Guice.createInjector(OvationApiModule())

    return injector.getInstance(LocalDatabaseStack)
