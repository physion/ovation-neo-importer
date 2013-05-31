import itertools
import logging
import numpy as np

from nose.tools import istest, assert_equals, assert_sequence_equal, assert_true
from ovation_neo.importer import import_file

from neo.io import AxonIO

from ovation import DateTime
from ovation.core import *
from ovation.testing import TestBase
from ovation.conversion import to_map
from ovation.data import as_data_frame

from ovation_neo.__main__ import main

class TestAxonImport(TestBase):
    @classmethod
    def setup_class(cls):

        TestBase.setup_class()

        ctx = cls.local_stack.getAuthenticatedDataStoreCoordinator().getContext()

        proj = ctx.insertProject('ABF import', 'ABF import', DateTime())

        exp = proj.insertExperiment('ABF experiment', DateTime())
        device_info = {'amplifier.mode': 'I-clamp',
                       'amplifier.channels.0.gain': 2.5,
                       'amplifier.channels.1.gain': 3.5}

        exp.setEquipmentSetup(to_map(device_info))

        cls.src = ctx.insertSource("recording source", "source-id")

        abf_file = 'fixtures/example1.abf'

        logging.info("Importing file...")
        cls.epoch_group = import_file(abf_file,
                                      exp,
                                      exp.getEquipmentSetup(),
                                      "amplifier",
                                      [cls.src])

        reader = AxonIO(filename=abf_file)
        cls.block = reader.read()


    def setup(self):
        self.src = self.__class__.src
        self.block = self.__class__.block
        self.epoch_group = self.__class__.epoch_group
        self.ctx = self.get_dsc().getContext()

    @istest
    def should_import_one_epoch_per_block(self):
        assert_equals(len(self.block.segments), len(set(self.epoch_group.getEpochs())), "should import one epoch per segment")


    @istest
    def should_import_segment_annotations(self):
        block, epoch_group = self.block, self.epoch_group

        for segment, epoch in zip(block.segments, epoch_group.getEpochs()):
            # Check protocol parameters
            for k, v in segment.annotations.iteritems():
                assert_equals(v, epoch.getProtocolParameter(k))


    @istest
    def test_should_import_analog_segments_as_measurements(self):
        block, epoch_group = self.block, self.epoch_group

        for segment, epoch in zip(block.segments, epoch_group.getEpochs()):
            check_measurements(segment, epoch)

    @istest
    def should_import_events(self):
        assert_true(False, "Not implemented")

    def get_dsc(self):
        return self.__class__.local_stack.getAuthenticatedDataStoreCoordinator()

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



def check_numeric_measurement(signal, m):
    data_frame = as_data_frame(m)
    for (name, data) in data_frame.iteritems():
        assert_equals(signal.units, data.units)
        assert_sequence_equal(signal.shape, data.shape)
        assert_true(np.all(np.asarray(signal) == np.asarray(data)))
        assert_equals(signal.sampling_rate, data.sampling_rates[0])


def check_measurements(segment, epoch):
    assert_equals(len(segment.analogsignals), len(list(epoch.getMeasurements())))

    measurements = dict(((m.getName(), m) for m in epoch.getMeasurements()))

    for signal in segment.analogsignals:
        print measurements
        m = measurements[signal.name]
        check_numeric_measurement(signal, m)



