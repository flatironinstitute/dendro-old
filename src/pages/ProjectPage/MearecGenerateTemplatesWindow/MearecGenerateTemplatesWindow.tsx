import { FunctionComponent, useCallback, useMemo } from "react"
import { useProject } from "../ProjectPageContext"
import { DendroProcessingJobDefinition, createJob } from "../../../dbInterface/dbInterface"
import { DendroJobRequiredResources } from "../../../types/dendro-types"
import { useGithubAuth } from "../../../GithubAuth/useGithubAuth"
import Splitter from "../../../components/Splitter"

type MearecGenerateTemplatesWindowProps = {
    width: number
    height: number
    onClose: () => void
}

const MearecGenerateTemplatesWindow: FunctionComponent<MearecGenerateTemplatesWindowProps> = ({ onClose, width, height }) => {
    const {projectId, computeResource, files} = useProject()
    const mearecGenerateTemplatesProcessor = useMemo(() => {
        if (!computeResource) return undefined
        for (const app of computeResource.spec?.apps || []) {
            for (const p of app.processors || []) {
                if (p.name === 'mearec_generate_templates') {
                    return p
                }
            }
        }
        return undefined
    }, [computeResource])
    const auth = useGithubAuth()
    const handleMearecGenerateTemplates = useCallback(() => {
        (async () => {
            if (!projectId) return
            if (!mearecGenerateTemplatesProcessor) return
            if (!files) return
            const processorName = 'mearec_generate_templates'
            const jobDef: DendroProcessingJobDefinition = {
                processorName,
                inputFiles: [],
                inputParameters: [],
                outputFiles: [{
                    name: 'output',
                    fileName: 'generated/mearec/default.templates.h5'
                }]
            }
            const requiredResources: DendroJobRequiredResources = {
                numCpus: 8,
                numGpus: 0,
                memoryGb: 8,
                timeSec: 3600 * 1
            }
            const defaultRunMethod = computeResource?.spec?.defaultJobRunMethod
            if (!defaultRunMethod) {
                throw new Error(`defaultRunMethod not found for compute resource: ${computeResource?.computeResourceId}`)
            }
            const job = {
                projectId,
                jobDefinition: jobDef,
                processorSpec: mearecGenerateTemplatesProcessor,
                files,
                batchId: undefined,
                requiredResources,
                runMethod: 'aws_batch' as any // hard-code during testing
            }
            console.log('CREATING JOB', job)
            await createJob(job, auth)
            console.log('JOB CREATED')
            onClose()
        })()
    }, [projectId, mearecGenerateTemplatesProcessor, computeResource, files, auth, onClose])
    const W1 = Math.min(500, width / 2)
    return (
        <Splitter
            width={width}
            height={height}
            initialPosition={W1}
        >
            <div>
                <button onClick={handleMearecGenerateTemplates}>Generate Templates</button>
            </div>
            <div>

            </div>
        </Splitter>
    )
}

export default MearecGenerateTemplatesWindow
