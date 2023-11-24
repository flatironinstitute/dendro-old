import { FunctionComponent, useCallback } from "react"
import { createFileAndInitiateUpload } from "../../../dbInterface/dbInterface"
import { useProject } from "../ProjectPageContext"
import { useGithubAuth } from "../../../GithubAuth/useGithubAuth"

type UploadSmallFileWindowProps = {
    onClose: () => void
}

const UploadSmallFileWindow: FunctionComponent<UploadSmallFileWindowProps> = ({ onClose }) => {
    const {projectId, refreshFiles} = useProject()
    const auth = useGithubAuth()
    const handleSelectFile = useCallback(() => {
        if (!auth) return
        const fileInput = document.createElement("input")
        fileInput.type = "file"
        fileInput.addEventListener("change", () => {
            const file = fileInput.files?.[0]
            if (!file) return
            // get the binary content of the file
            const reader = new FileReader()
            reader.readAsBinaryString(file)
            reader.addEventListener("load", () => {
                const content = reader.result
                if (!content) return
                ; (async () => {
                    const {uploadUrl} = await createFileAndInitiateUpload(
                        projectId,
                        `uploads/${file.name}`,
                        contentSize(content),
                        auth
                    )
                    const uploadRequest = new XMLHttpRequest()
                    uploadRequest.open("PUT", uploadUrl)
                    uploadRequest.setRequestHeader("Content-Type", "application/octet-stream")
                    uploadRequest.send(content)
                    uploadRequest.addEventListener("load", () => {
                        refreshFiles()
                        onClose()
                    })
                    uploadRequest.addEventListener("error", (e) => {
                        console.error(e)
                        alert("Upload failed")
                    }, {once: true})
                })()
            })
        })
        fileInput.click()
    }, [auth, projectId, onClose, refreshFiles])
    if (!auth) {
        return <div>Please login first.</div>
    }
    return (
        <div>
            <button onClick={handleSelectFile}>
                Select a small file from from your computer
            </button>
        </div>
    )
}

const contentSize = (content: string | ArrayBuffer) => {
    if (typeof content === "string") {
        return content.length
    }
    return content.byteLength
}

export default UploadSmallFileWindow
