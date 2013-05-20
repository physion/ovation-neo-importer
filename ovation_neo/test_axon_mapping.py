import itertools
import logging
import numpy as np

from nose.tools import istest, assert_equals, assert_sequence_equal, assert_true
from ovation_neo.importer import import_file

from neo.io import AxonIO

from ovation import DateTime
from ovation.core import NumericMeasurementUtils, DataElement
from ovation.testing import make_local_stack
from ovation.conversion import to_map, asarray

class TestAxonImport(object):
    @classmethod
    def setup_class(cls):

        logging.info("Creating local database stack...")
        (cls.local_stack, cls.dsc) = make_local_stack()

        ctx = cls.dsc.getContext()

        proj = ctx.insertProject('ABF import', 'ABF import', DateTime())

        exp = proj.insertExperiment('ABF experiment', DateTime())
        device_info = {"amplifier": {"mode": "I-clamp",
                                     "channels": {0: {"gain": 2.5},
                                                  1: {"gain": 3.5}}}}
        
        exp.setEquipmentSetup(to_map(device_info))

        src = ctx.insertSource("recording source", "source-id")

        abf_file = 'fixtures/example1.abf'

        logging.info("Importing file...")
        cls.epoch_group = import_file(abf_file,
                                      exp,
                                      exp.getEquipmentSetup(),
                                      "amplifier",
                                      src)

        reader = AxonIO(filename=abf_file)
        cls.block = reader.read()

    @classmethod
    def teardown_class(cls):
        logging.info("Removing local database stack...")
        cls.local_stack.cleanUp()

    def get_block_and_group(self):
        block = self.__class__.block
        epoch_group = self.__class__.epoch_group
        return block, epoch_group

    @istest
    def should_import_one_epoch_per_block(self):
        block, epoch_group = self.get_block_and_group()
        assert_equals(len(block.segments), len(set(epoch_group.getEpochs())), "should import one epoch per segment")


    @istest
    def should_import_segment_annotations(self):
        block, epoch_group = self.get_block_and_group()

        for segment, epoch in zip(block.segments, epoch_group.getEpochs()):
            # Check protocol parameters
            for k, v in segment.annotations.iteritems():
                yield assert_equals(v, epoch.getProtocolParameter(k))


    @istest
    def should_import_analog_segments_as_measurements(self):
        block, epoch_group = self.get_block_and_group()

        for segment, epoch in zip(block.segments, epoch_group.getEpochs()):
            yield check_measurements(segment, epoch)

    @istest
    def should_import_events(self):
        assert_true(False, "Not implemented")




def check_numeric_measurement(signal, m):
    nd = NumericMeasurementUtils.getNumericData(DataElement.cast_(m).getData()).get()
    data = asarray(nd.getData())
    assert_equals(signal.units, data.units)
    assert_sequence_equal(signal.shape, data.shape)
    assert_true(np.all(np.asarray(signal) == np.asarray(data)))
    assert_equals(signal.sampling_rate, data.sampling_rate)


def check_measurements(segment, epoch):
    assert_equals(len(segment.analogsignals), len(list(epoch.getMeasurements())))

    measurements = dict(((m.getName(), m) for m in epoch.getMeasurements()))
    
    for signal in segment.analogsignals:
        print measurements
        m = measurements[signal.name]
        check_numeric_measurement(signal, m)



