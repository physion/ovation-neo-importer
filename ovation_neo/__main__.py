# Copyright 2011, Physion Consulting LLC
# -*- coding: utf-8 -*-

import sys
from ovation import *
from ovation.core import *
from ovation.importer import import_main
from ovation_neo.importer import import_file

DESCRIPTION="""Import physiology data into an existing Ovation Experiment"""

def import_wrapper(data_context,
                  container_id=None,
                  protocol_id=None,
                  files=None,
                  timezone=None,
                  **args):

    experiment = Experiment.cast_(data_context.objectWithUuid(UUID.fromString(container_id)))
    protocol = Protocol.cast_(data_context.objectWithUuid(UUID.fromString(protocol_id)))

    for file in files:
        import_file(file,
                    experiment,
                    experiment.getEquipmentSetup(),
                    args.equipment_setup_root,
                    protocol=protocol)

    return 0


def parser_wrapper(parser):
    # Add equipment setup root
    pass

if __name__ == '__main__':
    sys.exit(import_main(name='neo_import',
                         description=DESCRIPTION,
                         file_ext='plx|abf',
                         import_fn=import_wrapper))
