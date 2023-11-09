import { FunctionComponent, useCallback, useMemo } from "react";
import Hyperlink from "../../../../components/Hyperlink";
import { createJob, DendroProcessingJobDefinition } from "../../../../dbInterface/dbInterface";
import { useGithubAuth } from "../../../../GithubAuth/useGithubAuth";
import { DendroJob } from "../../../../types/dendro-types";
import { useProject } from "../../ProjectPageContext";
import { isElectricalSeriesPathParameter } from "../../EditJobDefinitionWindow/EditJobDefinitionWindow";

type SpikeSortingOutputSectionProps = {
    spikeSortingJob: DendroJob
    fileName: string
}

const SpikeSortingOutputSection: FunctionComponent<SpikeSortingOutputSectionProps> = ({spikeSortingJob, fileName}) => {
    const {jobs, files, projectId, computeResource} = useProject()

    const recordingFileName = useMemo(() => {
        const output = spikeSortingJob.inputFiles.find(f => f.name === 'input')
        if (!output) return undefined
        return output.fileName
    }, [spikeSortingJob])

    const electricalSeriesPath = useMemo(() => {
        const pp = spikeSortingJob.inputParameters.find(p => (isElectricalSeriesPathParameter(p.name)))
        if (!pp) return undefined
        return pp.value
    }, [spikeSortingJob])

    const recordingFile = useMemo(() => {
        if (!recordingFileName) return undefined
        if (!files) return undefined
        return files.find(f => (f.fileName === recordingFileName))
    }, [recordingFileName, files])

    const sortingFile = useMemo(() => {
        if (!files) return undefined
        return files.find(f => (f.fileName === fileName))
    }, [fileName, files])

    const spikeSortingFigurlJob = useMemo(() => {
        if (!jobs) return undefined
        return jobs.find(j => {
            if (j.processorName !== 'spike_sorting_figurl') return false
            const rr = j.inputFiles.find(f => (f.name === 'recording'))
            const ss = j.inputFiles.find(f => (f.name === 'sorting'))
            if ((!rr) || (!ss)) return false
            if (rr.fileName !== recordingFileName) return false
            if (ss.fileName !== fileName) return false
            return true
        })
    }, [jobs, recordingFileName, fileName])

    const spikeSortingFigurlFile = useMemo(() => {
        if (!spikeSortingFigurlJob) return undefined
        if (!files) return undefined
        const ff1 = spikeSortingFigurlJob.outputFiles.find(f => (f.name === 'output'))
        const ff2 = files.find(f => (f.fileName === ff1?.fileName))
        return ff2
    }, [spikeSortingFigurlJob, files])

    const spikeSortingFigurlProcessor = useMemo(() => {
        if (!computeResource) return undefined
        if (!computeResource.spec) return undefined
        for (const app of computeResource.spec.apps) {
            for (const pp of app.processors) {
                if (pp.name === 'spike_sorting_figurl') {
                    return pp
                }
            }
        }
        return undefined
    }, [computeResource])

    const auth = useGithubAuth()

    const handlePrepareSpikeSortingView = useCallback(async () => {
        if (!spikeSortingFigurlProcessor) return
        if (!recordingFileName) return
        if (!electricalSeriesPath) return
        if (!files) return
        const jobDefinition: DendroProcessingJobDefinition = {
            processorName: spikeSortingFigurlProcessor.name,
            inputFiles: [
                {
                    name: 'recording',
                    fileName: recordingFileName
                },
                {
                    name: 'sorting',
                    fileName
                }
            ],
            outputFiles: [
                {
                    name: 'output',
                    fileName: `.spike_sorting_figurl/${fileName}.figurl`
                }
            ],
            inputParameters: [
                {
                    name: 'electrical_series_path',
                    value: electricalSeriesPath
                }
            ]
        }
        await createJob({
            projectId,
            jobDefinition,
            processorSpec: spikeSortingFigurlProcessor,
            files,
            batchId: undefined
        }, auth)
    }, [spikeSortingFigurlProcessor, projectId, recordingFileName, auth, fileName, electricalSeriesPath, files])

    const handleOpenSpikeSortingView = useCallback(async () => {
        if (!spikeSortingFigurlFile) return
        const c = spikeSortingFigurlFile.content
        if (!c) return
        if (!c.startsWith('url:')) return
        const url = c.slice('url:'.length)
        const x = await loadRemoteData(url)
        if (!x) return
        if (!x.startsWith('https:')) return
        window.open(x, '_blank')
    }, [spikeSortingFigurlFile])

    const status = spikeSortingFigurlJob ? spikeSortingFigurlJob.status : undefined

    if (!recordingFile) return <div>Recording file not found</div>
    if (!sortingFile) return <div>Sorting file not found</div>

    if (status === 'completed') {
        return (
            <div>
                <Hyperlink onClick={handleOpenSpikeSortingView}>Open spike sorting view</Hyperlink>
            </div>
        )
    }

    if (['pending', 'queued', 'starting', 'running'].includes(status || '')) {
        return <div>Spike sorting view: {status}</div>
    }

    if (status === 'failed') {
        return <div>Error creating spike sorting view</div>
    }

    if (!spikeSortingFigurlProcessor) return <div>No spike_sorting_figurl processor found</div>

    return (
        <Hyperlink
            onClick={handlePrepareSpikeSortingView}
        >
            Prepare spike sorting view
        </Hyperlink>
    )
}

const loadRemoteData = async (url: string) => {
    const response = await fetch(url)
    if (!response.ok) {
        console.warn(`Unable to load remote data: ${url}`)
        return undefined
    }
    const text = await response.text()
    return text
}

export default SpikeSortingOutputSection