import { FunctionComponent, useMemo } from "react"
import Markdown from "../../../Markdown/Markdown"
import { ProtocaasProject } from "../../../types/protocaas-types"

type LoadNwbInPythonWindowProps = {
    onClose: () => void
    project: ProtocaasProject
    fileName: string
}

const getMdSource = (project: ProtocaasProject, fileName: string) => {
    const source = `
\`\`\`python
import h5py
import pynwb
import protocaas.client as prc
import remfile


# Load project ${project.name}
project = prc.load_project('${project.projectId}')

# Lazy load ${fileName}
nwb_file = project.get_file('${fileName}')
nwb_url = nwb_file.get_url()
nwb_remf = remfile.File(nwb_url)
io = pynwb.NWBHDF5IO(file=h5py.File(nwb_remf, 'r'), mode='r')
nwb = io.read()

# Explore the NWB file
print(nwb)
\`\`\`
`
    return source
}

const LoadNwbInPythonWindow: FunctionComponent<LoadNwbInPythonWindowProps> = ({project, fileName}) => {
    const source = useMemo(() => (getMdSource(project, fileName)), [project, fileName])
    return (
        <Markdown source={source} />
    )
}

export default LoadNwbInPythonWindow