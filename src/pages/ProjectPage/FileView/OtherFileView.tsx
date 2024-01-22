import { FunctionComponent } from "react";
import FileViewTable from "./FileViewTable";


type Props = {
    fileName: string
    width: number
    height: number
}

const OtherFileView: FunctionComponent<Props> = ({fileName, width, height}) => {
    return (
        <div style={{position: 'absolute', width, height, background: 'white'}}>
            <hr />
            <FileViewTable fileName={fileName} additionalRows={[]} />
            <div>&nbsp;</div>
            <div>...</div>
            <div>&nbsp;</div>
        </div>
    )
}

export default OtherFileView