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


def import_block(block, device_info, epoch_group, source):
    """
    Imports a Neo Block as a single Ovation EpochGroup

    """

    pass
