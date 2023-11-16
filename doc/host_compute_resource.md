# Hosting a Dendro compute resource

Each Dendro project comes equipped with a dedicated compute resource for executing analysis jobs. The default setting uses a compute resource provided by the author with limitations on CPU, memory, and concurrent jobs, shared among all users. This public resource should only be used for testing with small jobs. Contact one of the authors if you would like to run more intensive processing or configure your own compute resources.

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

In the web interface, go to settings for your project, and select your compute resource. New analyses within your project will now use your compute resource for analysis jobs.

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

## Configuring apps to use a Slurm cluster

If you have access to a Slurm cluster, you can configure apps to use it. This is done by providing the following fields when configuring the app in the web interface

* CPUs per task: e.g., `4`
* Partition: the name of the Slurm partition to use
* Time: the maximum time to allow for a single job (impacts job scheduling) (e.g., `5:00:00` for 5 hours)
* Other options: any other options to pass to the `srun` command (e.g., `--gpus=1`)

Don't forget to reload the page after making changes to the web interface.

## Configuring apps to use AWS Batch

To use AWS Batch, you will need to set up an AWS Batch compute environment and job queue. You will also need to set up an AWS Batch job definition for each app you want to use. The job definition should be configured to use the appropriate docker image for the app. If you are a beta tester, you can reach out to the authors for help configuring this.

You will need to provide the following fields when configuring the app in the web interface.

* Job queue: the name of the AWS Batch job queue to use
* Job definition: the name of the AWS Batch job definition to use

You will also need to provide your AWS credentials in the `.dendro-compute-resource-node.yaml` in the directory where your compute resource node daemon is running.

Don't forget to reload the page after making changes to the web interface.

## Configuring apps to use a local machine

By default, if you do not configure your app to use AWS Batch or a Slurm cluster, it will use your local machine to run jobs, or the machine where the compute resource node daemon is running.