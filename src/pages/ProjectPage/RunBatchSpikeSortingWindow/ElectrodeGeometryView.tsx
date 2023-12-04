import { FunctionComponent, useEffect, useState } from "react"
import { RemoteH5File } from "../../../RemoteH5File/RemoteH5File"
import ElectrodeGeometryWidget, {ElectrodeLocation} from "@hodj/electrode-geometry-widget"

type ElectrodeGeometryViewProps = {
    width: number
    height: number
    nwbFile: RemoteH5File
}

const ElectrodeGeometryView: FunctionComponent<ElectrodeGeometryViewProps> = ({width, height, nwbFile}) => {
    const [electrodeLocations, setElectrodeLocations] = useState<ElectrodeLocation[] | undefined>(undefined)
    useEffect(() => {
        (async () => {
            setElectrodeLocations(undefined)
            const grp = await nwbFile.getGroup('/general/extracellular_ephys/electrodes')
            if (!grp) return
            if (!grp.datasets) return
            let xDatasetPath = ''
            let yDatasetPath = ''
            if (grp.datasets.find(ds => (ds.name === 'rel_x'))) {
                xDatasetPath = '/general/extracellular_ephys/electrodes/rel_x'
                yDatasetPath = '/general/extracellular_ephys/electrodes/rel_y'
            }
            else if (grp.datasets.find(ds => (ds.name === 'x'))) {
                xDatasetPath = '/general/extracellular_ephys/electrodes/x'
                yDatasetPath = '/general/extracellular_ephys/electrodes/y'
            }
            else {
                return
            }
            if ((!xDatasetPath) || (!yDatasetPath)) return
            const x = await nwbFile.getDatasetData(xDatasetPath, {})
            const y = await nwbFile.getDatasetData(yDatasetPath, {})
            const locations: ElectrodeLocation[] = []
            for (let i = 0; i < x.length; i++) {
                locations.push({x: x[i], y: y[i]})
            }
            setElectrodeLocations(locations)
        })()
    }, [nwbFile])
    if (!electrodeLocations) return <div />
    return (
        <ElectrodeGeometryWidget
            width={width}
            height={height}
            electrodeLocations={electrodeLocations}
        />
    )
}

export default ElectrodeGeometryView