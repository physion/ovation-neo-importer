import itertools
import logging
import numpy as np

from nose.tools import istest, assert_equals, assert_sequence_equal, assert_true
from ovation.wrapper import property_annotatable
from ovation_neo.importer import import_file

from neo.io import AxonIO

from ovation import DateTime, Integer
from ovation.core import *
from ovation.testing import TestBase
from ovation.conversion import to_map, to_dict
from ovation.data import as_data_frame

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

        exp.setEquipmentSetup(to_map(cls.device_info))

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
        assert_equals(len(self.block.segments), len(set(self.epoch_group.getEpochs())), "should import one epoch per segment")


    @istest
    def should_import_segment_annotations(self):
        for segment, epoch in zip(self.block.segments, self.epoch_group.getEpochs()):
            # Check protocol parameters
            for k, v in segment.annotations.iteritems():
                assert_equals(v, epoch.getProtocolParameter(k))

    @istest
    def should_store_segment_index(self):
        for segment, epoch in zip(self.block.segments, self.epoch_group.getEpochs()):
            assert_equals(segment.index,
                          Integer.cast_((property_annotatable(epoch).getUserProperty(epoch.getDataContext().getAuthenticatedUser(), 'index'))).intValue())

    @istest
    def test_should_import_analog_segments_as_measurements(self):
        for segment, epoch in zip(self.block.segments, self.epoch_group.getEpochs()):
            check_measurements(segment, epoch)

    @istest
    def should_import_events(self):
        assert_true(False, "Not implemented")

    @istest
    def should_call_via_main(self):
        expt2 = self.ctx.insertProject("project2","project2",DateTime()).insertExperiment("purpose", DateTime())
        protocol2 = self.ctx.insertProtocol("protocol", "description")

        args = ['--source={}'.format(str(self.src.getUuid())),
                '--timezone=America/New_York',
                '--container={}'.format(str(expt2.getUuid())),
                '--protocol={}'.format(str(protocol2.getUuid())),
                'fixtures/example1.abf',
                ]

        main(argv=args, dsc=self.get_dsc())

        epoch_group = list(EpochGroupContainer.cast_(expt2).getEpochGroups())[0]
        assert_equals(len(self.block.segments), len(set(epoch_group.getEpochs())), "should import one epoch per segment")

    @istest
    def should_set_device_parameters(self):
        assert_equals(self.device_info.keys(),
                      to_dict(Experiment.cast_(self.epoch_group.getParent()).getEquipmentSetup().getDeviceDetails()).keys())

    @istest
    def should_set_device_for_analog_signals(self):
        for segment, epoch in zip(self.block.segments, self.epoch_group.getEpochs()):
            measurements = dict(((DataElement.cast_(m).getName(), m) for m in epoch.getMeasurements()))

            for signal in segment.analogsignals:
                m = measurements[signal.name]
                assert_equals({"amplifier.channels.{}".format(signal.annotations['channel_index'])},
                              set(m.getDevices()))

    @istest
    def should_import_events(self):
        assert_true(False, "No fixure")

    @istest
    def should_import_epochs(self):
        assert_true(False, "No fixture")


    @istest
    def should_import_spike_trains(self):
        assert_true(False, "Not implemented")

    @istest
    def should_import_units(self):
        assert_true(False, "Not implemented")






def check_numeric_measurement(signal, m):
    data_frame = as_data_frame(m)
    for (name, data) in data_frame.iteritems():
        assert_equals(signal.units, data.units)
        assert_sequence_equal(signal.shape, data.shape)
        assert_true(np.all(np.asarray(signal) == np.asarray(data)))
        assert_equals(signal.sampling_rate, data.sampling_rates[0])


def check_measurements(segment, epoch):
    assert_equals(len(segment.analogsignals), len(list(epoch.getMeasurements())))

    measurements = dict(((DataElement.cast_(m).getName(), m) for m in epoch.getMeasurements()))

    for signal in segment.analogsignals:
        m = measurements[signal.name]
        check_numeric_measurement(signal, m)





