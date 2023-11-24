from typing import Union, List, Any, Optional

from .. import BaseModel

class DendroProjectUser(BaseModel):
    userId: str
    role: str # 'admin' | 'editor' | 'viewer'

class DendroProject(BaseModel):
    projectId: str
    name: str
    description: str
    ownerId: str
    users: List[DendroProjectUser]
    publiclyReadable: bool
    tags: List[str]
    timestampCreated: float
    timestampModified: float
    computeResourceId: Union[str, None] = None # it seems this needs to go at the end, otherwise it will be required by pydantic - not sure why

class DendroJobInputFile(BaseModel):
    name: str
    fileId: str
    fileName: str

class DendroJobInputParameter(BaseModel):
    name: str
    value: Union[Any, None] = None
    secret: Union[bool, None] = None

class DendroJobOutputFile(BaseModel):
    name: str
    fileName: str
    fileId: Union[str, None] = None

class ComputeResourceSpecProcessorParameter(BaseModel):
    name: str
    description: str
    type: str
    default: Union[Any, None] = None
    options: Union[List[str], List[int], None] = None
    secret: bool = False

class ComputeResourceSpecProcessorInput(BaseModel):
    name: str
    description: str
    list: bool = False

class ComputeResourceSpecProcessorOutput(BaseModel):
    name: str
    description: str

class ComputeResourceSpecProcessorAttribute(BaseModel):
    name: str
    value: Any

class ComputeResourceSpecProcessorTag(BaseModel):
    tag: str

class ComputeResourceSpecProcessor(BaseModel):
    name: str
    description: str
    inputs: List[ComputeResourceSpecProcessorInput]
    outputs: List[ComputeResourceSpecProcessorOutput]
    parameters: List[ComputeResourceSpecProcessorParameter]
    attributes: List[ComputeResourceSpecProcessorAttribute]
    tags: List[ComputeResourceSpecProcessorTag]

class DendroJob(BaseModel):
    projectId: str
    jobId: str
    jobPrivateKey: str
    userId: str
    processorName: str
    inputFiles: List[DendroJobInputFile]
    inputFileIds: List[str]
    inputParameters: List[DendroJobInputParameter]
    outputFiles: List[DendroJobOutputFile]
    timestampCreated: float
    computeResourceId: str
    status: str # 'pending' | 'queued' | 'starting' | 'running' | 'completed' | 'failed'
    batchId: Union[str, None] = None
    error: Union[str, None] = None
    processorVersion: Union[str, None] = None
    computeResourceNodeId: Union[str, None] = None # obsolete
    computeResourceNodeName: Union[str, None] = None # obsolete
    consoleOutputUrl: Union[str, None] = None
    timestampQueued: Union[float, None] = None
    timestampStarting: Union[float, None] = None
    timestampStarted: Union[float, None] = None
    timestampFinished: Union[float, None] = None
    outputFileIds: Union[List[str], None] = None
    processorSpec: ComputeResourceSpecProcessor
    dandiApiKey: Union[str, None] = None

class DendroFile(BaseModel):
    projectId: str
    fileId: str
    userId: str
    fileName: str
    size: int
    timestampCreated: float
    content: str # e.g., 'url:https://...'
    metadata: dict
    jobId: Union[str, None] = None # the job that produced this file

class ComputeResourceAwsBatchOpts(BaseModel):
    jobQueue: Optional[str] = None # obsolete
    jobDefinition: Optional[str] = None # obsolete
    useAwsBatch: Optional[bool] = None

class ComputeResourceSlurmOpts(BaseModel):
    partition: Union[str, None] = None
    time: Union[str, None] = None
    cpusPerTask: Union[int, None] = None
    otherOpts: Union[str, None] = None

class DendroComputeResourceApp(BaseModel):
    name: str
    specUri: str
    executablePath: Union[str, None] = None # to be removed (once database has been cleared)
    container: Union[str, None] = None # to be removed (once database has been cleared)
    awsBatch: Union[ComputeResourceAwsBatchOpts, None] = None
    slurm: Union[ComputeResourceSlurmOpts, None] = None

class ComputeResourceSpecApp(BaseModel):
    name: str
    description: str
    processors: List[ComputeResourceSpecProcessor]
    appImage: Union[str, None] = None
    appExecutable: Union[str, None] = None
    requiresGpu: Union[bool, None] = None

class ComputeResourceSpec(BaseModel):
    apps: List[ComputeResourceSpecApp]

class DendroComputeResource(BaseModel):
    computeResourceId: str
    ownerId: str
    name: str
    timestampCreated: float
    apps: List[DendroComputeResourceApp]
    spec: Union[ComputeResourceSpec, None] = None

class PubsubSubscription(BaseModel):
    pubnubSubscribeKey: str
    pubnubChannel: str
    pubnubUser: str

class ProcessorGetJobResponseInput(BaseModel):
    name: str
    url: str

class ProcessorGetJobResponseOutput(BaseModel):
    name: str

class ProcessorGetJobResponseParameter(BaseModel):
    name: str
    value: Any

class ProcessorGetJobResponse(BaseModel):
    jobId: str
    status: str
    processorName: str
    inputs: List[ProcessorGetJobResponseInput]
    outputs: List[ProcessorGetJobResponseOutput]
    parameters: List[ProcessorGetJobResponseParameter]

class DendroUser(BaseModel):
    userId: str
    dendroApiKey: Union[str, None] = None

class CreateJobRequestInputFile(BaseModel):
    name: str
    fileName: str

class CreateJobRequestOutputFile(BaseModel):
    name: str
    fileName: str

class CreateJobRequestInputParameter(BaseModel):
    name: str
    value: Union[Any, None]

class CreateJobRequest(BaseModel):
    projectId: str
    processorName: str
    inputFiles: List[CreateJobRequestInputFile]
    outputFiles: List[CreateJobRequestOutputFile]
    inputParameters: List[CreateJobRequestInputParameter]
    processorSpec: ComputeResourceSpecProcessor
    batchId: Union[str, None] = None
    dandiApiKey: Union[str, None] = None

class CreateJobResponse(BaseModel):
    jobId: str
    success: bool
