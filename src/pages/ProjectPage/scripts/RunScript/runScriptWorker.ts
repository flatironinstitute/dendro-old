import {
  RunScriptResult,
  RunScriptAddJobInputFile,
  RunScriptAddJobOutputFile,
  RunScriptAddJobParameter,
  RunScriptAddJobRequiredResources,
} from "./RunScriptWorkerTypes";

const runScript = (_script: string, _files: any[]) => {
  const result: RunScriptResult = { jobs: [], addedFiles: []};
  const _addJob = (a: {
    processorName: string;
    inputs: RunScriptAddJobInputFile[];
    outputs: RunScriptAddJobOutputFile[];
    parameters: RunScriptAddJobParameter[];
    requiredResources: RunScriptAddJobRequiredResources;
    runMethod: "local" | "aws_batch" | "slurm";
  }) => {
    // validate parameters - this is being called by the user's javascript code which doesn't enforce types
    if (!a.processorName)
      throw new Error("In addJob, processorName is required");
    if (typeof a.processorName !== "string")
      throw new Error("In addJob, processorName must be a string");
    if (!a.inputs) throw new Error("In addJob, inputs is required");
    if (!Array.isArray(a.inputs))
      throw new Error("In addJob, inputs must be an array");
    for (const input of a.inputs) {
      if (!input.name) throw new Error("In addJob, input.name is required");
      if (typeof input.name !== "string")
        throw new Error("In addJob, input.name must be a string");
      if (!input.fileName)
        throw new Error("In addJob, input.fileName is required");
      if (typeof input.fileName !== "string")
        throw new Error("In addJob, input.fileName must be a string");
    }
    if (!a.outputs) throw new Error("In addJob, outputs is required");
    if (!Array.isArray(a.outputs))
      throw new Error("In addJob, outputs must be an array");
    for (const output of a.outputs) {
      if (!output.name) throw new Error("In addJob, output.name is required");
      if (typeof output.name !== "string")
        throw new Error("In addJob, output.name must be a string");
      if (!output.fileName)
        throw new Error("In addJob, output.fileName is required");
      if (typeof output.fileName !== "string")
        throw new Error("In addJob, output.fileName must be a string");
    }
    if (!a.parameters) throw new Error("In addJob, parameters is required");
    if (!Array.isArray(a.parameters))
      throw new Error("In addJob, parameters must be an array");
    for (const parameter of a.parameters) {
      if (!parameter.name)
        throw new Error("In addJob, parameter.name is required");
      if (typeof parameter.name !== "string")
        throw new Error("In addJob, parameter.name must be a string");
      if (!('value' in parameter))
        throw new Error("In addJob, parameter.value is required");
    }
    if (!a.requiredResources)
      throw new Error("In addJob, requiredResources is required");
    if (typeof a.requiredResources !== "object")
      throw new Error("In addJob, requiredResources must be an object");
    if (!("numCpus" in a.requiredResources))
      throw new Error("In addJob, requiredResources.numCpus is required");
    if (!("numGpus" in a.requiredResources))
      throw new Error("In addJob, requiredResources.numGpus is required");
    if (!("memoryGb" in a.requiredResources))
      throw new Error("In addJob, requiredResources.memoryGb is required");
    if (!("timeSec" in a.requiredResources))
      throw new Error("In addJob, requiredResources.timeSec is required");
    if (!a.runMethod) throw new Error("In addJob, runMethod is required");
    if (typeof a.runMethod !== "string")
      throw new Error("In addJob, runMethod must be a string");
    if (!["local", "aws_batch", "slurm"].includes(a.runMethod))
      throw new Error(
        "In addJob, runMethod must be one of 'local', 'aws_batch', 'slurm'"
      );
    ///////////////////////////////////////////////////////////////////////////
    const {
      processorName,
      inputs,
      outputs,
      parameters,
      requiredResources,
      runMethod,
    } = a;
    context.print(`Adding job. Processor ${processorName}`);
    result.jobs.push({
      processorName: processorName,
      inputFiles: inputs,
      outputFiles: outputs,
      inputParameters: parameters,
      requiredResources: requiredResources,
      runMethod: runMethod,
    });
  };

  const _addFile = (fileName: string, a: {url: string}) => {
    result.addedFiles.push({fileName, url: a.url});
  }

  const log: string[] = [];
  const context = {
    print: function (message: string) {
      // make sure it is a string
      if (typeof message !== "string") {
        message = JSON.stringify(message);
      }
      log.push(message);
    },
    files: _files,
    addJob: _addJob,
    addFile: _addFile
  };
  const scriptFunction = new Function("context", _script);
  try {
    scriptFunction(context); // Execute the code received from the main thread, passing context explicitly
    postMessage({ type: "result", result: result, log: log });
  } catch (error: any) {
    postMessage({ type: "error", error: error.message, log: log });
  }
};

self.onmessage = function (e) {
  if (e.data.type === "run") {
    runScript(e.data.script, e.data.files);
  }
};
