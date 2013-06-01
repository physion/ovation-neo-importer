# -*- coding: utf-8 -*-
"""
This module provides a mapping from the Neo core data model to Ovation's data model
"""
from xmlrpclib import DateTime

__copyright__ = 'Copyright (c) 2013. Physion Consulting. All rights reserved.'

"""
MAPPING
=======

Data Objects
------------

√ AnalogSignal => Measurement
- Spike => spike_times + spike_waveforms (see SpikeTrain)
[ ] Event => TimelineAnnotation
[ ] Epoch => TimelineAnnotation


Container Objects
-----------------

√ Segment => Epoch
√ Block => EpochGroup


Grouping Objects
----------------

Not supported in current NIO instances, so we'll hold off on this for now...
RecordingChannel => DeviceInfo (level k+1) (+ Measurement reference)
RecordingChannelGroup => DeviceInfo (level k)

[ ] Unit => AnalysisRecord (derived measurement)
[ ] SpikeTrain => AnalysisRecord (derived measurement) spike_times + spike_waveforms

[ ] Unit => ? Source per Unit, as child of input Source (protocol?)
        ? AnalysisRecord (?)


Annotations
-----------

√ Segment annotations => Protocol parameters



Notes
-----

- Empty protocols, unless defined
- DeviceInfo names must be .channels.{i} for individual analog signals from provided root
-
"""

import os.path
import neo
import neo.io as nio
import logging

try:
    from itertools import chain
except ImportError:
    # chain is builtin in Python3
    pass


from ovation import *
from ovation.core import *
from ovation.conversion import to_map, to_java_set
from ovation.data import insert_numeric_measurement
from ovation.wrapper import property_annotatable

# Map from file extension to importer
__IMPORTERS = {
    '.plx' : nio.PlexonIO,
    '.abf' : nio.AxonIO
}


def import_file(file_path,
                epoch_group_container,
                equipment_setup_root,
                sources,
                group_label=None,
                protocol=None):
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
    sources : iterable of us.physion.ovation.domain.Source
        Experimental `Subjects` for data contained in file to be imported
    group_label : string, optional
    protocol : protocol

    Returns
    -------
    The inserted `ovation.EpochGroup`

    """

    ext = os.path.splitext(file_path)[-1]

    reader = __IMPORTERS[ext](filename=file_path)
    block = reader.read()

    return import_block(epoch_group_container,
                        block,
                        equipment_setup_root,
                        sources,
                        group_label=group_label,
                        protocol=protocol)


def import_block(epoch_group_container,
                 block,
                 equipment_setup_root,
                 sources,
                 protocol=None,
                 protocol_parameters={},
                 device_parameters={},
                 group_label=None):
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
    source : iterable of us.physion.ovation.domain.Source
        Experimental `Subjects` for data contained in `block`
    protocol : ovation.Protocol, optional
        Ovation `Protocol` for the EpochGroup (if present)
    protocol_parameters : Mapping, optional
    device_parameters : Mapping, optional
    group_label : string, optional
        EpochGroup label. If `None`, and `block.name` is not `None`, `block.name` will be used
        for the EpochGroup label.


    Returns
    -------
    The inserted `ovation.EpochGroup`

    """

    if group_label is None:
        if not (block.name is None):
            group_label = block.name
        else:
            group_label = "Neo importer"


    merged_protocol_parameters = protocol_parameters.copy()
    merged_protocol_parameters.update(block.annotations)

    #Convert a datetime.datetime to a DateTime
    start_time = DateTime(*(block.rec_datetime.timetuple()[:7]))

    epochGroup = EpochGroupContainer.cast_(epoch_group_container).insertEpochGroup(group_label,
                                                                                    start_time,
                                                                                    protocol,
                                                                                    to_map(merged_protocol_parameters),
                                                                                    to_map(device_parameters)
                                                                                )

    if len(block.recordingchannelgroups) > 0:
        logging.warning("Block contains RecordingChannelGroups. Import of RecordingChannelGroups is currently not supported.")

    logging.info("Importing segments from {}".format(block.file_origin))
    for seg in block.segments:
        logging.info("Importing segment {} from {}".format(str(seg.index), block.file_origin))
        import_segment(epochGroup, seg, sources,
                       protocol=protocol,
                       equipment_setup_root=equipment_setup_root)

    return epochGroup

NEO_PROTOCOL = "neo.io empty protocol"
NEO_PROTOCOL_TEXT = """Data imported via neo.io with no additional protocol provided."""

def import_segment(epoch_group,
                   segment,
                   sources,
                   protocol=None,
                   equipment_setup_root=None):


    ctx = epoch_group.getDataContext()
    if protocol is None:
        protocol = ctx.getProtocol(NEO_PROTOCOL)
        if protocol is None:
            protocol = ctx.insertProtocol(NEO_PROTOCOL, NEO_PROTOCOL_TEXT)

    segment_duration = max(arr.t_stop for arr in segment.analogsignals)
    segment_duration.units = 'ms' #milliseconds
    start_time = DateTime(TimelineElement.cast_(epoch_group).getStart())

    inputSources = Maps.newHashMap()
    outputSources = Maps.newHashMap()

    for s in sources:
        inputSources.put(s.getLabel(), s)

    device_parameters = dict(("{}.{}".format(equipment_setup_root, k), v) for (k,v) in segment.annotations.items())
    epoch = EpochContainer.cast_(epoch_group).insertEpoch(inputSources,
                                                          outputSources,
                                                          start_time,
                                                          start_time.plusMillis(int(segment_duration)),
                                                          protocol,
                                                          to_map(segment.annotations),
                                                          to_map(device_parameters)
                                                          )
    property_annotatable(epoch).addProperty('index', segment.index)

    if len(segment.analogsignalarrays) > 0:
        logging.warning("Segment contains AnalogSignalArrays. Import of AnalogSignalArrays is currently not supported")


    for analog_signal in segment.analogsignals:
        import_analog_signal(epoch, analog_signal, equipment_setup_root)


def import_analog_signal_array(epoch, signal_array, equipment_setup_root):
    signal_array.labels = [u'time', u'channel']
    signal_array.sampling_rates = [signal_array.sampling_rate] * signal_array.shape[1]

    #TODO should use channel, etc. for equipment setup
    insert_numeric_measurement(epoch,
                               set(),
                               {equipment_setup_root},
                               signal_array.name,
                               { signal_array.name : signal_array })


def import_analog_signal(epoch, analog_signal, equipment_setup_root):

    analog_signal.labels = [u'time']
    analog_signal.sampling_rates = [analog_signal.sampling_rate]
    insert_numeric_measurement(epoch,
                               set(),
                               {"{}.channels.{}".format(equipment_setup_root, analog_signal.annotations['channel_index'])},
                               analog_signal.name,
                               { analog_signal.name : analog_signal})





