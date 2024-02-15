import {
  RunScriptResult,
  RunScriptAddJobInputFile,
  RunScriptAddJobOutputFile,
  RunScriptAddJobParameter,
  RunScriptAddJobRequiredResources,
} from "./RunScriptWorkerTypes";

const runScript = (_script: string, _files: any[]) => {
  const result: RunScriptResult = { jobs: [] };
  const _addJob = (a: {
    processorName: string;
    inputs: { [key: string]: string };
    outputs: { [key: string]: string };
    parameters: { [key: string]: any };
    requiredResources: RunScriptAddJobRequiredResources;
    runMethod: "local" | "aws_batch" | "slurm";
  }) => {
    // validate parameters - this is being called by the user's javascript code which doesn't enforce types
    if (!a.processorName)
      throw new Error("In addJob, processorName is required");
    if (typeof a.processorName !== "string")
      throw new Error("In addJob, processorName must be a string");
    if (!a.inputs) throw new Error("In addJob, inputs is required");
    if (typeof a.inputs !== "object")
      throw new Error("In addJob, inputs must be an object");
    if (!a.outputs) throw new Error("In addJob, outputs is required");
    if (typeof a.outputs !== "object")
      throw new Error("In addJob, outputs must be an object");
    if (!a.parameters) throw new Error("In addJob, parameters is required");
    if (typeof a.parameters !== "object")
      throw new Error("In addJob, parameters must be an object");
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
      inputFiles: Object.entries(inputs)
        .sort()
        .map(
          ([name, fileName]) =>
            ({
              name: name,
              fileName: fileName,
            } as RunScriptAddJobInputFile)
        ),
      outputFiles: Object.entries(outputs)
        .sort()
        .map(
          ([name, fileName]) =>
            ({
              name: name,
              fileName: fileName,
            } as RunScriptAddJobOutputFile)
        ),
      inputParameters: Object.entries(parameters)
        .sort()
        .map(
          ([name, value]) =>
            ({
              name: name,
              value: value,
            } as RunScriptAddJobParameter)
        ),
      requiredResources: requiredResources,
      runMethod: runMethod,
    });
  };

  const log: string[] = [];
  const context = {
    print: function (message: string) {
      log.push(message);
    },
    files: _files,
    addJob: _addJob,
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
