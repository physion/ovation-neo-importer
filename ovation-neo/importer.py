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
Spike => spike_times + spike_waveforms (see SpikeTrain)
Event => TimelineAnnotation
Epoch => TimelineAnnotation


Container Objects
-----------------

Segment => Epoch3
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


def import_block(block, device_info, device_info_root, epoch_group_container, source):
    """Import a `Neo <http://neuralensemble.org/neo/>`_ `Block` as a single Ovation `EpochGroup`


    Parameters
    ----------

    block : neo.Block
        `neo.Block` to import
    device_info : ovation.DeviceInfo
        `ovation.DeviceInfo` providing equipment description for the `Block`. The device info must contain
        `.channels.{i}` for individual channels or `.arrays.{i}.channels{j}` for `AnalogSignalArrays` from the
        `device_info_root` provided root
    device_info_root : str
        Root name for device info for data contained in `block`
    epoch_group : ovation.EpochGroug or ovation.Experiment
        Data is inserted into this container as a new `ovation.EpochGroup`
    source : ovation.Subject
        Root `Subject` for data contained in `block`


    Returns
    -------

    The inserted `ovation.EpochGroup`

    """

    pass
