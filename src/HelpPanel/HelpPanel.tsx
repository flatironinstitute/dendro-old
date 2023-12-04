import { FunctionComponent, useEffect, useMemo, useState } from "react"
import useRoute from "../useRoute"
import Markdown from "../Markdown/Markdown"
import nunjucks from "nunjucks"
import { useGithubAuth } from "../GithubAuth/useGithubAuth"
import { Hyperlink } from "@hodj/misc";

nunjucks.configure({ autoescape: true })

type HelpPanelProps = {
    width: number
    height: number
    expanded: boolean
    setExpanded: (helpExpanded: boolean) => void
}

const HelpPanel: FunctionComponent<HelpPanelProps> = ({width, height, expanded, setExpanded}) => {
    const {route, staging} = useRoute()
    const [markdownSource, setMarkdownSource] = useState('')
    const [commonMarkdownSource, setCommonMarkdownSource] = useState('')

    const auth = useGithubAuth()
    const signedIn = auth.signedIn

    useEffect(() => {
        setMarkdownSource('')
        let sourcePath = ''
        if (route.page === 'dandisets') {
            sourcePath = '/help/dandisets.md'
        }
        else if (route.page === 'dandiset') {
            sourcePath = '/help/dandiset.md'
        }
        else if (route.page === 'project') {
            const tab = route.tab || 'project-home'
            if (tab === 'project-home') {
                sourcePath = '/help/project-project-home.md'
            }
            else if (tab === 'project-files') {
                sourcePath = '/help/project-project-files.md'
            }
            else if (tab === 'project-jobs') {
                sourcePath = '/help/project-project-jobs.md'
            }
            else if (tab === 'dandi-import') {
                sourcePath = '/help/project-dandi-import.md'
            }
            else if (tab === 'processors') {
                sourcePath = '/help/project-processors.md'
            }
        }
        (async () => {
            if (!sourcePath) return
            const resp = await fetch(sourcePath)
            const text = await resp.text()
            setMarkdownSource(text)
        })()
    }, [route])

    useEffect(() => {
        (async () => {
            const resp = await fetch('/help/common.md')
            const text = await resp.text()
            setCommonMarkdownSource(text)
        })()
    }, [])

    const processedMarkdownSource = useMemo(() => {
        let x = nunjucks.renderString(markdownSource, {staging, route, signedIn})
        x = x + `\n\n---\n${commonMarkdownSource}`
        return x
    }, [markdownSource, staging, route, signedIn, commonMarkdownSource])

    // if not expanded, we don't show the main content (because it looks bad if only a small portion is showing)
    // but we do render the component so that it can show the top bar

    return (
        <div style={{position: 'absolute', width, height, overflowY: 'auto'}}>
            <TopBar
                helpExpanded={expanded}
                setHelpExpanded={setExpanded}
            />
            {
                expanded && (
                    <div style={{padding: 15}}>
                        <Markdown
                            source={processedMarkdownSource}
                        />
                    </div>
                )
            }
        </div>
    )
}

type TopBarProps = {
    helpExpanded: boolean
    setHelpExpanded: (helpExpanded: boolean) => void
}

const TopBar: FunctionComponent<TopBarProps> = ({helpExpanded, setHelpExpanded}) => {
    // bar with collapse / expand button
    return (
        <div style={{fontSize: 30}}>
            {
                helpExpanded ? (
                    <Hyperlink
                        onClick={() => setHelpExpanded(false)}
                    >
                        {/* Arrow pointing to the right */}
                        &rarr;
                    </Hyperlink>
                ) : (
                    <Hyperlink
                        onClick={() => setHelpExpanded(true)}
                    >
                        {/* Arrow pointing to the left */}
                        &larr;
                    </Hyperlink>
                )
            }
        </div>
    )
}

export default HelpPanel