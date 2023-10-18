import { FunctionComponent } from "react";
import TextEditor from "./TextEditor";

type Props = {
    fileName: string
    fileContent: string
    onSaveContent: (text: string) => void
    editedFileContent: string
    setEditedFileContent: (text: string) => void
    readOnly: boolean
    width: number
    height: number
}

const TextFileEditor: FunctionComponent<Props> = ({fileName, fileContent, onSaveContent, editedFileContent, setEditedFileContent, readOnly, width, height}) => {
    const language = fileName.endsWith('.json') ? (
        'json'
    ) : fileName.endsWith('.yaml') ? (
        'yaml'
    ) : fileName.endsWith('.yml') ? (
        'yaml'
    ) : fileName.endsWith('.py') ? (
        'python'
    ) : fileName.endsWith('.js') ? (
        'javascript'
    ) : fileName.endsWith('.md') ? (
        'markdown'
    ) : 'text'

    const wordWrap = language === 'json' || language === 'markdown'

    return (
        <TextEditor
            width={width}
            height={height}
            language={language}
            label={fileName}
            text={fileContent}
            onSaveText={onSaveContent}
            editedText={editedFileContent}
            onSetEditedText={setEditedFileContent}
            wordWrap={wordWrap}
            // onReload=
            readOnly={readOnly}
        />
    )
}

export default TextFileEditor