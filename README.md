# Protocaas (prototype v3) - Neuroscience Analysis Web App

Protocaas is a **prototype** web application designed for scientists in research labs who want to efficiently manage and conduct neurophysiology data analysis. The current focus is spike sorting of electrophysiology data. Whether you are working with your own data or utilizing public resources from the [DANDI Archive](https://dandiarchive.org/), Protocaas provides a user-friendly platform for organizing, running, and sharing neuroscientific processing jobs.

:warning: **Please note:** This software is currently in the prototype phase and is not recommended for production use.

If you're a lab working with electrophysiology data and looking for a solution to spike sort your data, consider trying this software as a beta tester. You can use it in the cloud *or* with your local resources. Reach out to one of the authors if interested.

* [Access the live site](https://protocaas3.vercel.app) (it's a prototype!)
* [Learn how to host a compute resource](./doc/host_compute_resource.md)

## System Requirements

To use Protocaas, you only need a web browser. No additional software installation is required. Simply open your preferred web browser and navigate to the [live site](https://protocaas3.vercel.app) to get started.

If you want to [host your own compute resource](./doc/host_compute_resource.md) for processing, you will need a Linux machine with optional access to a Slurm cluster or AWS resources.

## Projects, Files and Jobs

Protocaas organizes datasets into projects, files and jobs, streamlining your data management process. Each project is associated with an owner and a compute resource and can include optional collaborators. You can choose to make your projects public or private. Each project consists of files and processing jobs.

Project files serve as either pointers to external data sources (e.g., DANDI assets) or as the output of specific processing jobs. These files are typically formatted in NWB (Neurodata Without Borders) format. To get started, you can use the DANDI import tool to seamlessly import data from DANDI repositories. Once imported, you can define processing jobs, such as spike sorting, that take these raw data files as input and generate new project files as output. Project files are immutable.

## Files and Jobs are Tightly Linked

The full provenance history of each file is stored within a Protocaas project. Each generated file is associated with a unique job that generated it, and each job has links to its input and output files. If a file is deleted, then all jobs that link to that job (either as an input or an output) are also deleted. Similarly, if a job is deleted, then the linked files are also deleted. Thus, in a pipeline, deleting a single file can have a cascading effect in deleting files and jobs throughout the project. In this way, Protocaas files always have a full provenance record.

Files and jobs can also be automatically deleted if a new job is queued that would overwrite existing files. Note that existing files (and jobs) are deleted when the new job is *queued* (not *run*).

## Processing Apps

Protocaas processing tools are organized into plugin apps which are containerized executable programs. At this point, there are only [a few processing apps available](https://github.com/scratchrealm/pc-spike-sorting), including:

- Spike sorting using Kilosort 2.5
- Spike sorting using Kilosort 3
- Spike sorting using MountainSort 5

As the project matures, we will add more apps to this list. Users can also contribute their own processing apps.

## Frequently Asked Questions

### How do I import data from DANDI?

TODO

### How do I run spike sorting?

TODO

### How do I upload sorting results to DANDI?

TODO

### How do I host my own compute resource?

See [this document](./doc/host_compute_resource.md).

### How do I contribute my own processing app?

TODO

### LICENSE

Apache 2.0

## Authors

Jeremy Magland (Flatiron Institute) in collaboration with Ben Dichter and Luiz Tauffer (CatalystNeuro)
