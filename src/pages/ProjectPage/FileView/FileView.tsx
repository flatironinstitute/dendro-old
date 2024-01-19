import { FunctionComponent } from "react";
import FigurlFileView from "./FigurlFileView";
import NwbFileView from "./NwbFileView";
import OtherFileView from "./OtherFileView";
import Nh5FileView from "./Nh5FileView";
import { Splitter } from "@fi-sci/splitter";
import JobsWindow from "../JobsWindow/JobsWindow";

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
    if (fileName.endsWith('.nwb')) {
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