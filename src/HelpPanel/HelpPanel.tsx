import { Hyperlink } from "@fi-sci/misc"
import nunjucks from "nunjucks"
import { FunctionComponent, useEffect, useMemo, useState } from "react"
import { useGithubAuth } from "../GithubAuth/useGithubAuth"
import Markdown from "../Markdown/Markdown"
import { DendroProject } from "../types/dendro-types"
import useRoute from "../useRoute"
import { parseAnalysisSourceUrl } from "../pages/ProjectPage/ProjectAnalysis/AnalysisSourceClient"

nunjucks.configure({ autoescape: true })

type HelpPanelProps = {
    width: number
    height: number
    expanded: boolean
    setExpanded: (helpExpanded: boolean) => void
    currentProject: DendroProject | undefined
}

const HelpPanel: FunctionComponent<HelpPanelProps> = ({width, height, expanded, setExpanded, currentProject}) => {
    const {route, staging} = useRoute()
    const [markdownSource, setMarkdownSource] = useState('')
    const [commonMarkdownSource, setCommonMarkdownSource] = useState('')

    const auth = useGithubAuth()
    const signedIn = auth.signedIn

    useEffect(() => {
        setMarkdownSource('')
        let sourcePath = ''
        if (route.page === 'home') {
            sourcePath = '/help/home.md'
        }
        else if (route.page === 'dandisets') {
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
            else if (tab === 'project-linked-analysis') {
                sourcePath = '/help/project-project-linked-analysis.md'
            }
            else if (tab === 'project-scripts') {
                sourcePath = '/help/project-project-scripts.md'
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

    const projectInfo = useMemo(() => {
        if (!currentProject) return {}
        const ret: any = {
            ...currentProject
        }
        if (currentProject.analysisSourceUrl) {
            const {repoUrl, repoName, branch, path} = parseAnalysisSourceUrl(currentProject.analysisSourceUrl)
            ret['analysisSource'] = {
                repoUrl,
                branch,
                path,
                repoName
            }
        }
        return ret
    }, [currentProject])

    const processedMarkdownSource = useMemo(() => {
        let x = nunjucks.renderString(markdownSource, {staging, route, signedIn, project: projectInfo})
        x = x + `\n\n---\n${commonMarkdownSource}`
        return x
    }, [markdownSource, staging, route, signedIn, commonMarkdownSource, projectInfo])

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
                    <span title="Collapse help panel">
                        <Hyperlink
                            onClick={() => setHelpExpanded(false)}
                            
                        >
                            {/* Arrow pointing to the right */}
                            &rarr;
                        </Hyperlink>
                    </span>
                ) : (
                    <span title="Expand help panel">
                        <Hyperlink
                            onClick={() => setHelpExpanded(true)}
                        >
                            {/* Arrow pointing to the left */}
                            &larr;
                        </Hyperlink>
                    </span>
                )
            }
        </div>
    )
}

export default HelpPanel