# Copyright 2011, Physion Consulting LLC
# -*- coding: utf-8 -*-

import sys
from ovation.conversion import asclass
from ovation.importer import import_main
from ovation_neo.importer import import_file

DESCRIPTION="""Import physiology data into an existing Ovation Experiment"""

def main(argv=sys.argv, dsc=None):
    def import_wrapper(data_context,
                  container=None,
                  protocol=None,
                  files=None,
                  sources=None,
                  equipment_setup_root=None,
                  **args):

        container = data_context.getObjectWithURI(container)
        protocol_entity = data_context.getObjectWithURI(protocol)
        if protocol_entity:
            protocol = asclass("Protocol", protocol_entity)
        else:
            protocol = None

        sources = [data_context.getObjectWithURI(source) for source in sources]

        for file in files:
            import_file(file,
                        container,
                        equipment_setup_root,
                        sources,
                        protocol=protocol)

        return 0


    def parser_wrapper(parser):
        # Add equipment setup root
        equipment_group = parser.add_argument_group('hardware')
        equipment_group.add_argument('--equipment-setup-root',
                                     help='Physiology hardware root in Equipment setup')

        return parser


    return import_main(argv=argv,
                       name='neo_import',
                       description=DESCRIPTION,
                       file_ext='plx|abf',
                       import_fn=import_wrapper,
                       parser_callback=parser_wrapper,
                       dsc=dsc)

if __name__ == '__main__':
    sys.exit(main())
