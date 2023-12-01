# Hosting a Dendro compute resource

Each Dendro project comes equipped with a dedicated compute resource for executing analysis jobs. The default setting uses a compute resource provided by the authors with limitations on CPU, memory, and concurrent jobs, shared among all users. This public resource should only be used for testing with small jobs. Contact one of the authors if you would like to run more intensive processing or configure your own compute resources.

Prerequisites

* Python >= 3.9
* Docker or (Singularity >= 3.11)

Clone this repo, then

```bash
# install
cd dendro/python
pip install -e .[compute_resource]
```

```bash
# Initialize (one time)
export COMPUTE_RESOURCE_DIR=/some/path
export CONTAINER_METHOD=singularity # or docker
cd $COMPUTE_RESOURCE_DIR
dendro register-compute-resource
# Open the provided link in a browser and log in using GitHub
```

```bash
# Start the compute resource
cd $COMPUTE_RESOURCE_DIR
dendro start-compute-resource
# Leave this open in a terminal. It is recommended that you use a terminal multiplexer like tmux or screen.
```

In the web interface, go to settings for your project, and select your compute resource. New jobs submitted within your project will now use your compute resource for analysis jobs.

## Configuring apps for your compute resource

In order to run jobs with your compute resource, you will need to configure apps to use it.

In the web interface, click on the appropriate link to manage your compute resource. You will then be able to add apps to your compute resource by entering the information (see below for available apps).

:warning: After you make changes to your compute resource on the web interface, reload the page so that your changes will take effect.

The following are available apps that you can configure

| App name | Spec URI |
| -------- | --------------- |
| mountainsort5 | https://github.com/scratchrealm/pc-spike-sorting/blob/main/mountainsort5/spec.json |
| kilosort3 | https://github.com/scratchrealm/pc-spike-sorting/blob/main/kilosort3/spec.json |
| kilosort2_5 | https://github.com/scratchrealm/pc-spike-sorting/blob/main/kilosort2_5/spec.json |
| spike-sorting_utils | https://github.com/scratchrealm/pc-spike-sorting/blob/main/spike_sorting_utils/spec.json |
| dandi-upload | https://github.com/scratchrealm/pc-spike-sorting/blob/main/dandi_upload/spec.json |

## Submitting jobs to AWS Batch

[See iaac_aws_batch](./iaac_aws_batch.md)