import { FunctionComponent, useCallback } from "react"
import Hyperlink from "../../../components/Hyperlink"
import { ProtocaasJob } from "../../../types/protocaas-types"
import useRoute from "../../../useRoute"
import { useProject } from "../ProjectPageContext"

type OutputsTableProps = {
    job: ProtocaasJob
}

const OutputsTable: FunctionComponent<OutputsTableProps> = ({ job }) => {
    const {openTab} = useProject()
    const {setRoute} = useRoute()
    const handleOpenFile = useCallback((fileName: string) => {
        openTab(`file:${fileName}`)
        setRoute({
            page: 'project',
            projectId: job.projectId,
            tab: `project-files`
        })
    }, [openTab, setRoute, job.projectId])
    return (
        <table className="table1">
            <tbody>
                {
                    job.processorSpec.outputs.map((output, ii) => {
                        const x = job.outputFiles.find(x => (x.name === output.name))
                        return (
                            <tr key={ii}>
                                <td>{output.name}</td>
                                <td>
                                    <Hyperlink
                                        onClick={() => {
                                            x && handleOpenFile(x?.fileName)
                                        }}
                                    >
                                        {x?.fileName || 'unknown'}
                                    </Hyperlink>
                                </td>
                                <td>{output.help}</td>
                            </tr>
                        )
                    })
                }
            </tbody>
        </table>
    )
}

export default OutputsTable