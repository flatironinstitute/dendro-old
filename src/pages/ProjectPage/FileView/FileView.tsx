import { FunctionComponent, useMemo } from "react";
import FigurlFileView from "./FigurlFileView";
import NwbFileView from "./NwbFileView";
import OtherFileView from "./OtherFileView";
import Nh5FileView from "./Nh5FileView";
import { Splitter } from "@fi-sci/splitter";
import JobsWindow from "../JobsWindow/JobsWindow";
import { useProject } from "../ProjectPageContext";
import FolderFileView from "./FolderFileView";

type Props = {
    fileName: string
    width: number
    height: number
}

const FileView: FunctionComponent<Props> = ({fileName, width, height}) => {
    return (
        <Splitter
            width={width}
            height={height}
            initialPosition={height * 2 / 3}
            direction="vertical"
        >
            <FileViewChild
                width={0}
                height={0}
                fileName={fileName}
            />
            <JobsWindow
                width={0}
                height={0}
                fileName={fileName}
            />
        </Splitter>
    )
}

type FileViewChildProps = {
    fileName: string
    width: number
    height: number
}

const FileViewChild: FunctionComponent<FileViewChildProps> = ({fileName, width, height}) => {
    const {files} = useProject()
    const theFile = useMemo(() => {
        if (!files) return undefined
        return files.find(f => (f.fileName === fileName))
    }, [files, fileName])
    if ((fileName.endsWith('.nwb')) || (fileName.endsWith('.nwb.zarr.json')) || (fileName.endsWith('.nwb.json')) || (fileName.endsWith('.lindi.json'))) {
        return (
            <NwbFileView
                fileName={fileName}
                width={width}
                height={height}
            />
        )
    }
    else if (fileName.endsWith('.nh5')) {
        return (
            <Nh5FileView
                fileName={fileName}
                width={width}
                height={height}
            />
        )
    }
    else if (fileName.endsWith('.figurl')) {
        return (
            <FigurlFileView
                fileName={fileName}
                width={width}
                height={height}
            />
        )
    }
    else if (theFile?.isFolder) {
        return (
            <FolderFileView
                fileName={fileName}
                width={width}
                height={height}
            />
        )
    }
    else {
        return (
            <OtherFileView
                fileName={fileName}
                width={width}
                height={height}
            />
        )
    }
}

export default FileView