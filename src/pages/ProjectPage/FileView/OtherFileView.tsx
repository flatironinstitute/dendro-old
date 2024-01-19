import { Hyperlink } from "@fi-sci/misc";
import { FunctionComponent, useEffect, useMemo, useState } from "react";
import { RemoteNH5Group } from "../../../nh5";
import { useProject } from "../ProjectPageContext";
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