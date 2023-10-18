# Protocaas compute resource prerequisites

Suppose you have a Linux machine and would like to use it as a protocaas compute resource. Here are the recommended steps to prepare it with the necessary software.

## Use Linux

Any distribution should do.

## Conda / Miniconda

I recommend using Miniconda, but you can use other conda solutions, virtualenv, etc.

Follow these instructions: https://docs.conda.io/projects/miniconda/en/latest/miniconda-install.html

This will involve downloading the Linux installation script file (usually the "Miniconda3 Linux 64-bit" option) and running it using bash.

Create a new conda environment. I'd recommend using Python 3.9, but you can more recent versions as well.

```bash
conda create -n processing python=3.9
```

You can replace "processing" with any name you like. To use this environment run the following each time you open your terminal

```bash
conda activate processing
```

or add this command to your ~/.bashrc file to automatically start in this environment each time you open a new terminal.

## Install docker or singularity

To use your computer as a protocaas compute resource, you'll most likely need to install either docker or singularity. Docker is simpler to install, whereas singularity is better for shared environments or compute clusters.

To install docker server (or docker engine): https://docs.docker.com/engine/install/
