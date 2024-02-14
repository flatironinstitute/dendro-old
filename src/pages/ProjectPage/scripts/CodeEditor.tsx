import { Editor } from "@monaco-editor/react"
import { editor as editor0 } from 'monaco-editor';
import * as monaco from 'monaco-editor/esm/vs/editor/editor.api';
import { FunctionComponent, useCallback, useEffect, useState } from "react"

type Monaco = typeof monaco

type CodeEditorProps = {
    width: number
    height: number
    content: string
    readOnly: boolean
    onContentChanged: (content: string) => void
    onSave: () => void
}

const CodeEditor: FunctionComponent<CodeEditorProps> = ({width, height, content, readOnly, onContentChanged, onSave}) => {
    const handleChange = useCallback((value: string | undefined) => {
        if (value === undefined) return
        onContentChanged(value)
    }, [onContentChanged])
    const wordWrap = false

    const [editor, setEditor] = useState<editor0.IStandaloneCodeEditor | undefined>(undefined)
    useEffect(() => {
        if (!editor) return
        if (editor.getValue() === content) return
        editor.setValue(content || '')
    }, [editor, content])
    const handleEditorDidMount = useCallback((editor: editor0.IStandaloneCodeEditor, monaco: Monaco) => {
        (async () => {
            // fancy stuff would go here
            setEditor(editor)
        })()
    }, [])
    // Can't do this in the usual way with monaco editor:
    // See: https://github.com/microsoft/monaco-editor/issues/2947
    const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLDivElement>) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault()
            if (readOnly) return
            if (!readOnly) {
                onSave()
            }
        }
    }, [onSave, readOnly])
    return (
        <div style={{position: 'absolute', width, height}} onKeyDown={handleKeyDown}>
            <Editor
                height={height}
                width={width}
                defaultLanguage="javascript"
                onChange={handleChange}
                onMount={handleEditorDidMount}
                options={{
                    readOnly,
                    domReadOnly: readOnly,
                    wordWrap: wordWrap ? 'on' : 'off',
                    theme: 'vs-dark' // unfortunately we cannot do this on a per-editor basis - it's a global setting
                }}
            />
        </div>
    )
}

export default CodeEditor