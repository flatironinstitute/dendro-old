[![codecov](https://codecov.io/gh/scratchrealm/protocaas/graph/badge.svg?token=B2DUYR34RZ)](https://codecov.io/gh/scratchrealm/protocaas)

# Protocaas (prototype v3) - Neuroscience Analysis Web App

Protocaas is a **prototype** web application designed for scientists in research labs who want to efficiently manage and conduct neurophysiology data analysis. The current focus is spike sorting of electrophysiology data. Whether you are working with your own data or utilizing public resources from the [DANDI Archive](https://dandiarchive.org/), Protocaas provides a user-friendly platform for organizing, running, and sharing neuroscientific processing jobs.

:warning: **Please note:** This software is currently in the prototype phase and is not recommended for production use.

If you're a lab working with electrophysiology data and looking for a solution to spike sort your data, consider trying this software as a beta tester. You can use it in the cloud *or* with your local resources. Reach out to one of the authors if interested.

* [Access the live site](https://protocaas.vercel.app) (it's a prototype!)
* [Learn how to host a compute resource](./doc/host_compute_resource.md)

## System Requirements

To use Protocaas, you only need a web browser. No additional software installation is required. Simply open your preferred web browser and navigate to the [live site](https://protocaas.vercel.app) to get started.

If you want to [host your own compute resource](./doc/host_compute_resource.md) for processing, you will need a Linux machine with optional access to a Slurm cluster or AWS resources.

## Getting started

### Upload raw ephys data to DANDI

The first step in uploading your raw electrophysiology data to DANDI is to convert it to the NWB format. You can use [NeuroConv](https://neuroconv.readthedocs.io/en/main/user_guide/user_guide.html) and/or [nwb-guide](https://github.com/NeurodataWithoutBorders/nwb-guide).

Once your data is in NWB format, create a new dandiset on [DANDI Archive](https://dandiarchive.org/) and then [follow these instructions to upload your data](https://www.dandiarchive.org/handbook/13_upload). If you are not ready to make your data public, you can choose to create an embargoed (private) dandiset and share it with collaborators. If you are only testing the system, you can use the [staging site](https://gui-staging.dandiarchive.org/).

### Create a Protocaas project

Note: If you are working with an embargoed dandiset, then you will need to first provide your DANDI API key (see below).

Each Protocaas project is associated with a dandiset. To create a new project, go to the [protocaas web interface](https://protocaas.vercel.app) and log in using your GitHub account. You can then navigate to the desired dandiset and click "Create a new protocaas project for this dandiset". Provide a project name. You are now ready to import data from the dandiset and start spike sorting.

### Import files from DANDI into a Protocaas project

Once you have created a Protocaas project associated with a dandiset (see above) you can import NWB files (aka DANDI assets) by clicking on the "DANDI import" tab on the left. Use the checkboxes to select the desired files and then click "Import selected assets". The import process can take a minute or two depending on the number of files you are importing. Once the import is complete, you can click on the "Files" tab to see the imported files.

### Run spike sorting

Once you have imported NWB files from DANDI into your Protocaas project, you can begin processing your data. At this point you will need to select a compute resource. By default a very limited default compute resource will be used, which is okay for quick tests. For more serious processing, you will need to [set up your own compute resource](./doc/host_compute_resource.md). You can select the compute resource by clicking the "Settings" button on the "Project home" tab.

Once you have selected the compute resource for your project, you can select files for spike sorting using the checkboxes and then click "Run spike sorting". Choose the desired spike sorter, set the desired sorting parameters, and click "Submit". Note that in order to run spike sorting, your NWB files will need to have the appropriate ElectricalSeries data objects in the acquisition section.

You can then monitor the sorting jobs using the "Jobs" tab, or by viewing the greyed-out files inside the "generated" folder.

Once a job is complete, you can click the NWB output files and view them in Neurosift, which includes a "raster plot" view.

### Upload sorting outputs to DANDI?

For now, you can only upload spike sorting results to the same dandiset from which the raw data was imported. In the future you will also be able to upload them to a new dandiset.

You will first need to provide your DANDI API key (see below).

To upload the sorting results to DANDI, select the generated files and click "Upload to DANDI" and then the "Upload" button. A new processing job will be created that will complete the upload. You can monitor that job using the "Jobs" tab. Once the upload is complete you should be able to see the NWB files in the DANDI web interface.

### Providing a DANDI API key

You can obtain your DANDI API key from [https://dandiarchive.org/](https://dandiarchive.org/) or, for the staging site, [https://gui-staging.dandiarchive.org/](https://gui-staging.dandiarchive.org/). Click the button in the upper-right corner.

Then, in the [Protocaas web interface](https://protocaas.vercel.app/), click the key icon in the upper-right and paste in the API key.

### Hosting a compute resource

See [hosting a compute resource](./doc/host_compute_resource.md).

### Contribute a custom processing app for spike sorting

More detailed instructions will be forthcoming. For now you can take a look at the [source code for the currently-available processing apps](https://github.com/scratchrealm/pc-spike-sorting).

### Projects, Files and Jobs

Protocaas organizes datasets into projects, files and jobs, streamlining your data management process. Each project is associated a dandiset and a compute resource and comprises files and processing jobs. You can choose to make your projects public or private.

Project files serve as either pointers to external data sources (e.g., DANDI assets) or as the output of specific processing jobs. These files are typically formatted in NWB (Neurodata Without Borders) format. To get started, you can use the DANDI import tool to seamlessly import data from DANDI repositories. Once imported, you can define processing jobs, such as spike sorting, that take these raw data files as input and generate new project files as output. Project files are immutable.

### Files and Jobs are Tightly Linked

The full provenance history of each file is stored within a Protocaas project. Each generated file is associated with a unique job that generated it, and each job has links to its input and output files. If a file is deleted, then all jobs that link to that job (either as an input or an output) are also deleted. Similarly, if a job is deleted, then the linked files are also deleted. Thus, in a pipeline, deleting a single file can have a cascading effect in deleting files and jobs throughout the project. In this way, Protocaas files always have a full provenance record.

Files and jobs can also be automatically deleted if a new job is queued that would overwrite existing files. Note that existing files (and jobs) are deleted when the new job is *queued* (not *run*).

### Processing Apps

Protocaas processing tools are organized into plugin apps which are containerized executable programs. At this point, there are only [a few processing apps available](https://github.com/scratchrealm/pc-spike-sorting), including:

- Spike sorting using Kilosort 2.5
- Spike sorting using Kilosort 3
- Spike sorting using MountainSort 5

As the project matures, we will add more apps to this list. Users can also contribute their own processing apps.

### LICENSE

Apache 2.0

## Authors

Jeremy Magland (Flatiron Institute) in collaboration with Ben Dichter and Luiz Tauffer (CatalystNeuro)
