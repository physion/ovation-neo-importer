# -*- coding: utf-8 -*-
"""
This module provides a mapping from the Neo core data model to Ovation's data model
"""
from xmlrpclib import DateTime
import sys

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
import quantities as pq
import neo.io as nio
import logging
from datetime import datetime

try:
    from itertools import chain
except ImportError:
    # chain is builtin in Python3
    pass


from ovation import Maps, TimeUnit, DateTime
from ovation.conversion import to_map, box_number, iterable, asclass
from ovation.data import insert_numeric_measurement, insert_numeric_analysis_artifact

# Map from file extension to importer
__IMPORTERS = {
    '.plx' : nio.PlexonIO,
    '.abf' : nio.AxonIO
}


def log_info(msg):
    logging.info(msg)
    sys.stderr.write("{}\n".format(msg))
    sys.stderr.flush()

def log_warning(msg):
    logging.warning(msg)
    sys.stderr.write("Warning: {}\n".format(msg))
    sys.stderr.flush()

def log_error(msg):
    logging.error(msg)
    sys.stderr.write("Error: {}\n".format(msg))
    sys.stderr.flush()


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
                        protocol=protocol,
                        group_label=group_label,
                        file_mtime=os.path.getmtime(file_path))


def import_block(epoch_group_container,
                 block,
                 equipment_setup_root,
                 sources,
                 protocol=None,
                 protocol_parameters={},
                 device_parameters={},
                 group_label=None,
                 file_mtime=None):
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
    if block.rec_datetime is not None:
        start_time = DateTime(*(block.rec_datetime.timetuple()[:7]))
    else:
        log_warning("Block does not contain a recording date/time. Using file modification time instead.")
        start_time = DateTime(*(datetime.fromtimestamp(file_mtime).timetuple()[:7]))

    epochGroup = asclass("us.physion.ovation.domain.mixin.EpochGroupContainer", epoch_group_container).insertEpochGroup(group_label,
                                                        start_time,
                                                        protocol,
                                                        to_map(merged_protocol_parameters),
                                                        to_map(device_parameters)
    )

    if len(block.recordingchannelgroups) > 0:
        log_warning("Block contains RecordingChannelGroups. Import of RecordingChannelGroups is currently not supported.")

    log_info("Importing segments from {}".format(block.file_origin))
    for seg in block.segments:
        log_info("Importing segment {} from {}".format(str(seg.index), block.file_origin))
        import_segment(epochGroup, seg, sources,
                       protocol=protocol,
                       equipment_setup_root=equipment_setup_root)

    log_info("Waiting for uploads to complete...")
    fs = epoch_group_container.getDataContext().getFileService()
    while(fs.hasPendingUploads()):
        fs.waitForPendingUploads(10, TimeUnit.SECONDS)

    return epochGroup

NEO_PROTOCOL = "neo.io empty protocol"
NEO_PROTOCOL_TEXT = """Data imported via neo.io with no additional protocol provided."""


def import_timeline_annotations(epoch, segment, start_time):
    for event in segment.events:
        event_time = event.time
        event_time.units = pq.ms
        if event.description:
                description = event.description
        else:
            description = ""
        epoch.addTimelineAnnotation(event.name,
                                    description,
                                    start_time.plusMillis(int(event_time.item())))
    for event_array in segment.eventarrays:
        for (event_time, label) in zip(event_array.times, event_array.labels):
            if event_array.name:
                name = "{} - {}".format(event_array.name, label)
            else:
                name = label

            event_time.units = pq.ms
            if event_array.description:
                description = event_array.description
            else:
                description = ""

            epoch.addTimelineAnnotation(name,
                                        description,
                                        start_time.plusMillis(int(event_time.item())))
    for neoepoch in segment.epochs:
        event_time = neoepoch.time
        event_time.units = pq.ms
        duration = neoepoch.duration
        duration.units = pq.ms

        epoch_start = start_time.plusMillis(int(event_time.item()))
        epoch_end = epoch_start.plusMillis(int(duration.item()))
        if neoepoch.description:
            description = neoepoch.description
        else:
            description = ""


        epoch.addTimelineAnnotation(neoepoch.label,
                                    description,
                                    epoch_start,
                                    epoch_end)
    for epoch_array in segment.epocharrays:
        for (event_time, duration, label) in zip(epoch_array.times, epoch_array.durations, epoch_array.labels):
            if epoch_array.name:
                name = "{} - {}".format(epoch_array.name, label)
            else:
                name = label

            event_time.units = pq.ms
            duration.units = pq.ms
            epoch_start = start_time.plusMillis(int(event_time.item()))
            epoch_end = epoch_start.plusMillis(int(duration.item()))

            epoch.addTimelineAnnotation(event.name,
                                        event.description,
                                        epoch_start,
                                        epoch_end)


def import_spiketrains(epoch, protocol, segment):
    for (i, spike_train) in enumerate(segment.spiketrains):
        params = {'t_start_ms': spike_train.t_start.rescale(pq.ms).item(),
                  't_stop_ms': spike_train.t_stop.rescale(pq.ms).item(),
                  'sampling_rate_hz': spike_train.sampling_rate.rescale(pq.Hz).item(),
                  'description': spike_train.description,
                  'file_origin': spike_train.file_origin}

        if spike_train.name:
            name = spike_train.name
        else:
            name = "spike train {}".format(i + 1)

        inputs = Maps.newHashMap()
        for m in iterable(epoch.getMeasurements()):
            inputs.put(m.getName(), m)

        ar = epoch.addAnalysisRecord(name,
                                     inputs,
                                     protocol,
                                     to_map(params))

        #
        spike_train.labels = ['spike time' for i in spike_train.shape]
        spike_train.sampling_rates = [spike_train.sampling_rate for i in spike_train.shape]

        spike_train.waveforms.labels = ['channel index', 'time', 'spike']
        spike_train.waveforms.sampling_rates = [0, spike_train.sampling_rate, 0] * pq.Hz

        insert_numeric_analysis_artifact(ar,
                                         name,
                                         {'spike times': spike_train,
                                          'spike waveforms': spike_train.waveforms})


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
    start_time = DateTime(epoch_group.getStart())

    inputSources = Maps.newHashMap()
    outputSources = Maps.newHashMap()

    for s in sources:
        inputSources.put(s.getLabel(), s)

    device_parameters = dict(("{}.{}".format(equipment_setup_root, k), v) for (k,v) in segment.annotations.items())
    epoch = epoch_group.insertEpoch(inputSources,
                                    outputSources,
                                    start_time,
                                    start_time.plusMillis(int(segment_duration)),
                                    protocol,
                                    to_map(segment.annotations),
                                    to_map(device_parameters)
    )
    if segment.index is not None:
        epoch.addProperty('index', box_number(segment.index))

    if len(segment.analogsignalarrays) > 0:
        log_warning("Segment contains AnalogSignalArrays. Import of AnalogSignalArrays is currently not supported")


    for analog_signal in segment.analogsignals:
        import_analog_signal(epoch, analog_signal, equipment_setup_root)

    import_timeline_annotations(epoch, segment, start_time)

    if len(segment.spikes) > 0:
        logging.warning("Segment contains Spikes. Import of individual Spike data is not yet implemented (but SpikeTrains are).")

    import_spiketrains(epoch, protocol, segment)





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
    if 'channel_index' in analog_signal.annotations:
        channel_index = analog_signal.annotations['channel_index']
    else:
        channel_index = 'unknown'
        log_warning("Analog signal does not have a channel index. Using '{}.channels.{}' as measurement device.".format(equipment_setup_root, channel_index))


    if analog_signal.name is not None:
        name = analog_signal.name
    else:
        name = 'analog signal'
        log_warning("Analog signal does not have a name. Using '{}' as measurement and data name.".format(name))

    device = '{}.channels.{}'.format(equipment_setup_root, channel_index)
    insert_numeric_measurement(epoch,
                               set(iterable(epoch.getInputSources().keySet())),
                               {device},
                               name,
                               {name : analog_signal})





