# About the Dendro API

The Dendro API is implemented using Python with [FastAPI](https://fastapi.tiangolo.com/), deployed as serverless functions on [Vercel](https://vercel.com/about). It is divided into four sections: GUI, Compute Resource, Processor, and Client.

Here is the [ReDoc-generated documentation](https://dendro.vercel.app/redoc) and the [Swagger UI-generated documentation](https://dendro.vercel.app/docs).

Here is the source code: [index.py](../api/index.py) and [api_helpers](../python/dendro/api_helpers).


## GUI

The GUI API receives requests from the [web interface](https://dendro.vercel.app). Operations include

* Getting and creating projects
* Getting and creating project files
* Getting and creating project jobs
* Registering and managing compute resources, including configuring apps.
* Getting pub/sub information
* Authenticating via GitHub

All write operations and some read operations require authentication via GitHub.

## Compute Resource

The compute resource API receives requests from compute resources. Operations include

* Getting the list of apps configured on the web interface
* Getting pub/sub information
* Getting a list of unfinished jobs for the compute resource, including their private keys
* Setting the compute resource spec (on startup of the compute resource)

All operations require authentication via signatures created using the secret compute resource private key, which is associated with the public compute resource ID.

## Processor

The processor API receives requests from processing jobs. Operations include

* Getting detailed information about a processing job
* Getting the status of a processing job (to see if it has been canceled)
* Setting the status of a processing job (running, completed, failed, ...)
* Getting presigned upload URLs for uploading outputs and console logs

All operations are authenticated using the job private key

## Client

The client API receives requests from Python clients. Operations include

* Getting the files and jobs associated with a project

At this time, no authentication is required.
