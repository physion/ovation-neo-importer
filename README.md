# Ovation Neo IO importer

[Ovation](http://ovation.io "ovation.io") is the revolutionary data management service that empowers researchers through the seamless organization of multiple data formats and sources, preservation of the link between raw data and analyses and the ability to securely share of all of this with colleagues and collaborators.

This project provides a Python package for importing electrophysiology data into Ovation. The importer leverages the [Neo](http://neuralensemble.org/neo/ "Neo") package for reading electrophysiology data from a variety of supported formats.

From the [Neo](http://neuralensemble.org/neo/ "Neo") website:

> Neo is a package for representing electrophysiology data in Python, together with support for reading a wide range of neurophysiology file formats, including Spike2, NeuroExplorer, AlphaOmega, Axon, Blackrock, Plexon, Tdt, and support for writing to a subset of these formats plus non-proprietary formats including HDF5.


## Supported formats
The Ovation Neo IO importer can load data from any format supported by the  [neo.io](http://neo.readthedocs.org/en/0.2.1/io.html#module-neo.io) package, including:

* Spike2
* NeuroExplorer
* Axon/pClamp
* AlphaOmega
* Blackrock
* Plexon
* Tdt
* Neo HDF5

If you have data in a format that isn't currently supported by the Neo IO package, please help the Neo project add support for your format rather than writing a custom Ovation importer. By contributing to the Neo project, the entire community benefits, whether they use Ovation or not. You can learn more about writing a Neo IO implementation by reading the [IO developers' guide](http://neo.readthedocs.org/en/0.2.1/io_developers_guide.html "Neo IO developers guide")

## Installation

To use the the physiology data importer, install it into your Python interpreter from the terminal command line:

	easy_install ovation_neo

This will install the `ovation_neo` module and all of its dependencies.

## Usage

The physiology data importer is run from the terminal command line:

	python -m ovation_neo --timezone <time zone ID> --container <experiment ID> --protocol <protocol ID> file1.abf file2.plx...

You can get more information about the available arguments by running:

	python -m ovation_neo -h

To find the `Experiment` and `Protocol` IDs, you can copy-and-paste the relevant object(s) from the Ovation application or call the `getUuid()` method on either object within Python.

## License

The Ovation Neo IO importer is Copyright (c) 2013 Physion Consulting LLC and is licensed under the [GPL v3.0 license](http://www.gnu.org/licenses/gpl.html "GPLv3") license.
