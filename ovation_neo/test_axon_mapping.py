import logging

from neo import Event, EventArray, SpikeTrain
import numpy as np
import quantities as pq
from nose.tools import istest, assert_equals, assert_sequence_equal, assert_true
import neo.core.epoch
from neo.io import AxonIO

from ovation import DateTime, Maps
from ovation.conversion import iterable
from ovation.testing import TestBase
from ovation.conversion import to_map, to_dict, asclass
from ovation.data import as_data_frame

from ovation_neo.importer import import_file, import_timeline_annotations, import_spiketrains
from ovation_neo.__main__ import main


class TestAxonImport(TestBase):
    @classmethod
    def setup_class(cls):

        TestBase.setup_class()

        ctx = cls.local_stack.getAuthenticatedDataStoreCoordinator().getContext()

        proj = ctx.insertProject('ABF import', 'ABF import', DateTime())

        exp = proj.insertExperiment('ABF experiment', DateTime())
        cls.device_info = {u'amplifier.mode': u'I-clamp',
                       u'amplifier.channels.0.gain': 2.5,
                       u'amplifier.channels.1.gain': 3.5}

        # TODO when we move to beta3
        #exp.setEquipmentSetupFromMap(to_map(cls.device_info))

        cls.src = ctx.insertSource("recording source", "source-id")

        abf_file = 'fixtures/example1.abf'

        logging.info("Importing file...")
        cls.epoch_group = import_file(abf_file,
                                      exp,
                                      "amplifier",
                                      [cls.src])

        reader = AxonIO(filename=abf_file)
        cls.block = reader.read()


    def setup(self):
        self.src = self.__class__.src
        self.block = self.__class__.block
        self.epoch_group = self.__class__.epoch_group
        self.ctx = self.get_dsc().getContext()
        self.device_info = self.__class__.device_info


    def get_dsc(self):
        """Overridden to make sure we get an authenticated DSC"""

        return self.__class__.local_stack.getAuthenticatedDataStoreCoordinator()

    @istest
    def should_import_one_epoch_per_block(self):
        assert_equals(len(self.block.segments), len(set(iterable(self.epoch_group.getEpochs()))), "should import one epoch per segment")


    @istest
    def should_import_segment_annotations(self):
        for segment, epoch in zip(self.block.segments, iterable(self.epoch_group.getEpochs())):
            # Check protocol parameters
            for k, v in segment.annotations.iteritems():
                assert_equals(v, epoch.getProtocolParameter(k))

    @istest
    def should_store_segment_index(self):
        for segment, epoch in zip(self.block.segments, iterable(self.epoch_group.getEpochs())):
            assert_equals(segment.index,
                          (epoch.getUserProperty(epoch.getDataContext().getAuthenticatedUser(), 'index')))

    @istest
    def should_import_analog_segments_as_measurements(self):
        for segment, epoch in zip(self.block.segments, iterable(self.epoch_group.getEpochs())):
            check_measurements(segment, epoch)

    @istest
    def should_import_events(self):
        assert_true(False, "Not implemented")

    @istest
    def should_call_via_main(self):
        expt2 = self.ctx.insertProject("project2","project2",DateTime()).insertExperiment("purpose", DateTime())
        protocol2 = self.ctx.insertProtocol("protocol", "description")

        args = ['executable-name',
                '--source={}'.format(self.src.getURI().toString()),
                '--timezone=America/New_York',
                '--container={}'.format(expt2.getURI().toString()),
                '--protocol={}'.format(protocol2.getURI().toString()),
                'fixtures/example1.abf',
                ]

        main(argv=args, dsc=self.get_dsc())

        epoch_group = list(iterable(expt2.getEpochGroups()))[0]
        assert_equals(len(self.block.segments), len(set(iterable(epoch_group.getEpochs()))), "should import one epoch per segment")

    @istest
    def should_set_device_parameters(self):
        assert_equals(self.device_info.keys(),
                      to_dict(asclass("Experiment", self.epoch_group.getParent()).getEquipmentSetup().getDeviceDetails()).keys())

    @istest
    def should_set_device_for_analog_signals(self):
        for segment, epoch in zip(self.block.segments, iterable(self.epoch_group.getEpochs())):
            measurements = dict(((m.getName(), m) for m in iterable(epoch.getMeasurements())))

            for signal in segment.analogsignals:
                m = measurements[signal.name]
                assert_equals({"amplifier.channels.{}".format(signal.annotations['channel_index'])},
                              set(iterable(m.getDevices())))

    @istest
    def should_import_events(self):
        expt2 = self.ctx.insertProject("project2","project2",DateTime()).insertExperiment("purpose", DateTime())
        protocol2 = self.ctx.insertProtocol("protocol", "description")
        epoch_start = DateTime()
        epoch = expt2.insertEpoch(Maps.newHashMap(),
                                  Maps.newHashMap(),
                                  epoch_start,
                                  DateTime(),
                                  protocol2,
                                  to_map(dict()),
                                  to_map(dict()))

        segment = self.block.segments[0]
        event_ms = 10
        event1 = Event(event_ms * pq.ms, "event1", name = "event1")

        segment.events.append(event1)

        try:
            import_timeline_annotations(epoch, segment, epoch_start)

            annotations = list(iterable(epoch.getUserTimelineAnnotations(self.ctx.getAuthenticatedUser())))

            assert(epoch_start.plusMillis(event_ms).equals(annotations[0].getStart()))
            assert_equals(1, len(annotations))
        finally:
            segment.events.remove(event1)

    @istest
    def should_import_event_arrays(self):
        expt2 = self.ctx.insertProject("project2","project2",DateTime()).insertExperiment("purpose", DateTime())
        protocol2 = self.ctx.insertProtocol("protocol", "description")
        epoch_start = DateTime()
        
        epoch = expt2.insertEpoch(Maps.newHashMap(),
                                  Maps.newHashMap(),
                                  epoch_start,
                                  DateTime(),
                                  protocol2,
                                  to_map({}),
                                  to_map({}))

        segment = self.block.segments[0]

        event_ms = [10, 12]
        event_array = EventArray(times=np.array(event_ms) * pq.ms, labels=['event1', 'event2'])
        segment.eventarrays.append(event_array)

        try:
            import_timeline_annotations(epoch, segment, epoch_start)

            annotations = list(iterable(epoch.getUserTimelineAnnotations(self.ctx.getAuthenticatedUser())))

            assert_equals(2, len(annotations))

            event_starts = [a.getStart() for a in annotations]
            for ms in event_ms:
                found = False
                for s in event_starts:
                    if epoch_start.plusMillis(ms).equals(s):
                        found = True

                if not found:
                    assert_true(False, "event start time doesn't match")
        finally:
            segment.eventarrays.remove(event_array)



    @istest
    def should_import_epochs(self):
        expt2 = self.ctx.insertProject("project2","project2",DateTime()).insertExperiment("purpose", DateTime())
        protocol2 = self.ctx.insertProtocol("protocol", "description")
        epoch_start = DateTime()

        epoch = expt2.insertEpoch(Maps.newHashMap(),
                                  Maps.newHashMap(),
                                  epoch_start,
                                  DateTime(),
                                  protocol2,
                                  to_map({}),
                                  to_map({}))

        segment = self.block.segments[0]

        neoepoch = neo.core.epoch.Epoch(10 * pq.ms, 100 * pq.ms, "epoch1")
        segment.epochs.append(neoepoch)

        try:
            import_timeline_annotations(epoch, segment, epoch_start)

            annotations = list(iterable(epoch.getUserTimelineAnnotations(self.ctx.getAuthenticatedUser())))

            assert_equals(1, len(annotations))
            assert_equals(epoch_start.plusMillis(10).getMillis(), annotations[0].getStart().getMillis())
            assert_equals(epoch_start.plusMillis(10).plusMillis(100).getMillis(), annotations[0].getEnd().get().getMillis())
        finally:
            segment.epochs.remove(neoepoch)



    @istest
    def should_import_spike_trains(self):
        expt2 = self.ctx.insertProject("project2","project2",DateTime()).insertExperiment("purpose", DateTime())
        protocol2 = self.ctx.insertProtocol("protocol", "description")
        epoch_start = DateTime()

        epoch = expt2.insertEpoch(Maps.newHashMap(),
                                  Maps.newHashMap(),
                                  epoch_start,
                                  DateTime(),
                                  protocol2,
                                  to_map({}),
                                  to_map({}))

        segment = self.block.segments[0]

        times = [.1, .2, .3, .4]
        waveforms = np.random.rand(2,3,4) * pq.mV

        train_name = 'spike train 1'
        spike_train = SpikeTrain(times, name=train_name, t_stop=2.0 * pq.s, units="s", waveforms=waveforms)

        segment.spiketrains.append(spike_train)
        try:
            import_spiketrains(epoch, protocol2, segment)

            records = list(iterable(epoch.getAnalysisRecords()))

            assert_equals(1, len(records))

            ar = records[0]

            assert_equals(train_name, ar.getName())

            expected_params = {'t_start_ms': spike_train.t_start.rescale(pq.ms).item(),
                  't_stop_ms': spike_train.t_stop.rescale(pq.ms).item(),
                  'sampling_rate_hz': spike_train.sampling_rate.rescale(pq.Hz).item(),
                  'description': spike_train.description,
                  'file_origin': spike_train.file_origin}

            for (k,v) in expected_params.iteritems():
                actual = ar.getProtocolParameters().get(k)
                if actual:
                    assert_equals(v, actual)

            assert_equals(len(expected_params), ar.getProtocolParameters().size())

            data_map = ar.getDataElements()
            df = as_data_frame(data_map.get(spike_train.name))

            check_signal(spike_train, df['spike times'])
            check_signal(spike_train.waveforms, df['spike waveforms'])
        finally:
            segment.spiketrains.remove(spike_train)


def check_signal(data, signal):
    assert_equals(signal.units, data.units)
    assert_sequence_equal(signal.shape, data.shape)
    assert_true(np.all(np.asarray(signal) == np.asarray(data)))
    try:
        assert_equals(signal.sampling_rate, data.sampling_rates[0])
    except AttributeError:
        pass


def check_numeric_measurement(signal, m):
    data_frame = as_data_frame(m)
    for (name, data) in data_frame.iteritems():
        check_signal(data, signal)


def check_measurements(segment, epoch):
    assert_equals(len(segment.analogsignals), len(list(iterable(epoch.getMeasurements()))))

    measurements = dict(((m.getName(), m) for m in iterable(epoch.getMeasurements())))

    for signal in segment.analogsignals:
        m = measurements[signal.name]
        check_numeric_measurement(signal, m)





