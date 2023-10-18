import { FunctionComponent } from "react";
import FigurlFileEditor from "./FigurlFileEditor";
import NwbFileEditor from "./NwbFileEditor";

type Props = {
    fileName: string
    width: number
    height: number
}

const FileEditor: FunctionComponent<Props> = ({fileName, width, height}) => {
    if (fileName.endsWith('.nwb')) {
        return (
            <NwbFileEditor
                fileName={fileName}
                width={width}
                height={height}
            />
        )
    }
    else if (fileName.endsWith('.figurl')) {
        return (
            <FigurlFileEditor
                fileName={fileName}
                width={width}
                height={height}
            />
        )
    }
    else {
        return (
            <div>Unsupported file type: {fileName}</div>
        )
    }
}

export default FileEditor