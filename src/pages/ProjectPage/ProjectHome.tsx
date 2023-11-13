import { Settings } from "@mui/icons-material";
import { FunctionComponent } from "react";
import { useModalDialog } from "../../ApplicationBar";
import Hyperlink from "../../components/Hyperlink";
import ModalWindow from "../../components/ModalWindow/ModalWindow";
import SmallIconButton from "../../components/SmallIconButton";
import { timeAgoString } from "../../timeStrings";
import useRoute from "../../useRoute";
import { useProject } from "./ProjectPageContext";
import ProjectSettingsWindow from "./ProjectSettingsWindow";
import ComputeResourceNameDisplay from "../../ComputeResourceNameDisplay";
import ComputeResourceSection from "./ComputeResourceSection";

type Props = {
    width: number
    height: number
}

const headingStyle: React.CSSProperties = {
    fontSize: 20,
    fontWeight: 'bold',
}

const ProjectHome: FunctionComponent<Props> = ({width, height}) => {
    const {setRoute} = useRoute()
    const {project, files, jobs, projectId} = useProject()

    const {visible: settingsWindowVisible, handleOpen: openSettingsWindow, handleClose: closeSettingsWindow} = useModalDialog()

    return (
        <div className="ProjectHome" style={{position: 'absolute', width, height, overflowY: 'auto', padding: 10, background: 'white'}}>
            <div style={headingStyle}>Project: {project?.name}</div>
            &nbsp;
            <table className="table1" style={{maxWidth: 500}}>
                <tbody>
                    <tr>
                        <td>Project name:</td>
                        <td>{project?.name}</td>
                    </tr>
                    <tr>
                        <td>Project ID:</td>
                        <td>{project?.projectId}</td>
                    </tr>
                    <tr>
                        <td>Compute resource:</td>
                        <td>{project ? <ComputeResourceNameDisplay computeResourceId={project.computeResourceId || undefined} link={true} /> : ''}</td>
                    </tr>
                    <tr>
                        <td>Created:</td>
                        <td>{timeAgoString(project?.timestampCreated)}</td>
                    </tr>
                    <tr>
                        <td>Modified:</td>
                        <td>{timeAgoString(project?.timestampModified)}</td>
                    </tr>
                    <tr>
                        <td>Num. files:</td>
                        <td>{files?.length} (<Hyperlink onClick={() => setRoute({page: 'project', projectId, tab: 'project-files'})}>view files</Hyperlink>)</td>
                    </tr>
                    <tr>
                        <td>Num. jobs:</td>
                        <td>{jobs?.length} (<Hyperlink onClick={() => setRoute({page: 'project', projectId, tab: 'project-jobs'})}>view jobs</Hyperlink>)</td>
                    </tr>
                </tbody>
            </table>

            <div>&nbsp;</div><hr /><div>&nbsp;</div>

            <div style={headingStyle}>Project description</div>
            <div>
                {project?.description}
            </div>
            
            <div>&nbsp;</div><hr /><div>&nbsp;</div>

            <div style={headingStyle}>Compute resource</div>

            <ComputeResourceSection />
            
            <div>&nbsp;</div><hr /><div>&nbsp;</div>

            <div style={{paddingTop: 10}}>
                <button onClick={openSettingsWindow} title="Project settings"><SmallIconButton icon={<Settings />} /> Project Settings</button>
            </div>

            <div>&nbsp;</div><hr /><div>&nbsp;</div>
            
            
            <ModalWindow
                open={settingsWindowVisible}
                onClose={closeSettingsWindow}
            >
                <ProjectSettingsWindow />
            </ModalWindow>
        </div>
    )
}

export default ProjectHome