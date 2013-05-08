"""
This module provides a mapping from the Neo core data model to Ovation's data model
"""

__copyright__ = 'Copyright (c) 2013. Physion Consulting. All rights reserved.'

"""
MAPPING
=======

Data Objects
------------

AnalogSignal => Measurement
    Name?
Spike => spike_times + spike_waveforms (see SpikeTrain)
Event => TimelineAnnotation
Epoch => TimelineAnnotation


Container Objects
-----------------

Segment => Epoch
Block => EpochGroup


Grouping Objects
----------------

RecordingChannel => DeviceInfo (level k+1) (+ Measurement reference)
RecordingChannelGroup => DeviceInfo (level k)

Unit => AnalysisRecord (derived measurement)
SpikeTrain => AnalysisRecord (derived measurement) spike_times + spike_waveforms

Unit => ? Source per Unit, as child of input Source (protocol?)
        ? AnalysisRecord (?)


Annotations
-----------

Segment annotations => Protocol parameters



Notes
-----

- Empty protocols, unless defined
- DeviceInfo names must be .channels.{i} for individual channels or .arrays.{i}.channels{j} for AnalogSignalArrays from provided root
-
"""

import neo.io as nio


def import_file(file_path, epoch_group_container, equipment_setup, equipment_setup_root, source):
    """Import a Neo IO readable file

    Parameters
    ----------

    file_path : str
        Path to file to import
    epoch_group_container : ovation.EpochGroup or ovation.Experiment
        Container for the inserted `ovation.EpochGroup`
    equipment_setup : ovation.EquipmentSetup
        Experiment `EquipmentSetup` for the data contained in the file to be imported
    equipment_setup_root : str
        Root path for equipment setup describing equipment that recorded the data to be imported
    source : ovation.Source
        Experimental `Subject` for data contained in file to be imported


    Returns
    -------

    The inserted `ovation.EpochGroup`

    """

    reader = nio.PlexonIO(filename=file_path)
    block = reader.read()

    return import_block(block,
                        epoch_group_container,
                        equipment_setup,
                        equipment_setup_root,
                        source)


def import_block(epoch_group_container, block, equipment_setup, equipment_setup_root, source):
    """Import a `Neo <http://neuralensemble.org/neo/>`_ `Block` as a single Ovation `EpochGroup`


    Parameters
    ----------

    block : neo.Block
        `neo.Block` to import
    epoch_group_container : ovation.EpochGroup or ovation.Experiment
        Container for the inserted `ovation.EpochGroup`
    equipment_setup : ovation.EquipmentSetup
        Experiment `EquipmentSetup` for the data contained in the file to be imported
    equipment_setup_root : str
        Root path for equipment setup describing equipment that recorded the data to be imported
    source : ovation.Source
        Experimental `Subject` for data contained in `block`


    Returns
    -------

    The inserted `ovation.EpochGroup`

    """

    return None
