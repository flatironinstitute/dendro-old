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
    processorName: string,
    inputs: { [key: string]: string },
    outputs: { [key: string]: string },
    parameters: { [key: string]: any },
    requiredResources: RunScriptAddJobRequiredResources
  }) => {
    const { processorName, inputs, outputs, parameters, requiredResources } = a;
    context.print(`Adding job. Processor ${processorName}`);
    result.jobs.push({
      processorName: processorName,
      inputFiles: Object.entries(inputs).sort().map(
        ([name, fileName]) =>
          ({
            name: name,
            fileName: fileName,
          } as RunScriptAddJobInputFile)
      ),
      outputFiles: Object.entries(outputs).sort().map(
        ([name, fileName]) =>
          ({
            name: name,
            fileName: fileName,
          } as RunScriptAddJobOutputFile)
      ),
      inputParameters: Object.entries(parameters).sort().map(
        ([name, value]) =>
          ({
            name: name,
            value: value,
          } as RunScriptAddJobParameter)
      ),
      requiredResources: requiredResources,
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
  try {
    eval(_script); // Execute the code received from the main thread
    postMessage({ type: "result", result: result, log: log });
  } catch (error: any) {
    postMessage({ type: "error", error: error.message, log: log });
  }
};

self.onmessage = function (e) {
  console.log("--- msg", e, e.data);
  if (e.data.type === "run") {
    runScript(e.data.script, e.data.files);
  }
};
