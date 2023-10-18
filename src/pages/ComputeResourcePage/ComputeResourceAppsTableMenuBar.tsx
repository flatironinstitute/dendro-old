import { Add, Delete, Edit } from "@mui/icons-material"
import { FunctionComponent, useCallback } from "react"
import SmallIconButton from "../../components/SmallIconButton"
import { confirm } from "../../confirm_prompt_alert"

type ComputeResourceAppsTableMenuBarProps = {
    width: number
    height: number
    selectedAppNames: string[]
    onDeleteApps: (appNames: string[]) => void
    onAddApp: () => void
    onEditApp: () => void
}

const ComputeResourceAppsTableMenuBar: FunctionComponent<ComputeResourceAppsTableMenuBarProps> = ({width, height, selectedAppNames, onAddApp, onDeleteApps, onEditApp}) => {
    const handleDelete = useCallback(async () => {
        const okay = await confirm(`Are you sure you want to delete these ${selectedAppNames.length} apps?`)
        if (!okay) return
        onDeleteApps(selectedAppNames)
    }, [selectedAppNames, onDeleteApps])

    return (
        <div>
            <span>
                <SmallIconButton
                    icon={<Add />}
                    title={"Add an app"}
                    label="Add app"
                    onClick={onAddApp}
                />
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            </span>
            <SmallIconButton
                icon={<Delete />}
                disabled={(selectedAppNames.length === 0)}
                title={selectedAppNames.length > 0 ? `Delete these ${selectedAppNames.length} apps` : ''}
                onClick={handleDelete}
            />
            &nbsp;&nbsp;&nbsp;
            <SmallIconButton
                icon={<Edit />}
                disabled={(selectedAppNames.length !== 1)}
                title={selectedAppNames.length === 1 ? `Edit app ${selectedAppNames[0]}` : ''}
                onClick={onEditApp}
            />
        </div>
    )
}

export default ComputeResourceAppsTableMenuBar