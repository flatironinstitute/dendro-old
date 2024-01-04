import { useCallback, useMemo } from "react"
import { useLocation, useNavigate } from "react-router-dom"

export type Route = {
    page: 'dandisets'
} | {
    page: 'dandiset'
    dandisetId?: string
} | {
    page: 'project'
    projectId: string
    tab?: string
} | {
    page: 'compute-resource'
    computeResourceId: string
} | {
    page: 'compute-resources'
} | {
    page: 'projects'
} | {
    page: 'register-compute-resource'
    computeResourceId: string
    resourceCode: string
} | {
    page: 'github-auth'
} | {
    page: 'about'
} | {
    page: 'admin'
} | {
    page: 'importDandiAsset'
    dandisetId: string
    dandisetVersion: string
    assetPath: string
    assetUrl: string
    projectName: string
}

const useRoute = () => {
    const location = useLocation()
    const navigate = useNavigate()
    const p = location.pathname
    const search = location.search
    const searchParams = useMemo(() => new URLSearchParams(search), [search])
    const staging = searchParams.get('staging') === '1'
    const deployedApi = searchParams.get('deployed-api') === '1'
    const route: Route = useMemo(() => {
        if (p === '/about') {
            return {
                page: 'about'
            }
        }
        else if ((p === '/dandisets') || (p === '/dandiset/')) {
            return {
                page: 'dandisets'
            }
        }
        else if (p.startsWith('/dandiset/')) {
            const dandisetId = p.slice('/dandiset/'.length)
            return {
                page: 'dandiset',
                dandisetId
            }
        }
        else if (p.startsWith('/project/')) {
            const projectId = p.slice('/project/'.length)
            return {
                page: 'project',
                projectId,
                tab: searchParams.get('tab') || undefined
            }
        }
        else if (p.startsWith('/compute-resource/')) {
            const computeResourceId = p.slice('/compute-resource/'.length)
            return {
                page: 'compute-resource',
                computeResourceId
            }
        }
        else if (p === '/compute-resources') {
            return {
                page: 'compute-resources'
            }
        }
        else if (p === '/projects') {
            return {
                page: 'projects'
            }
        }
        else if (p === '/admin') {
            return {
                page: 'admin'
            }
        }
        else if (p.startsWith('/register-compute-resource/')) {
            const a = p.split('/')
            const computeResourceId = a[2]
            const resourceCode = a[3]
            return {
                page: 'register-compute-resource',
                computeResourceId,
                resourceCode
            }
        }
        else if (p === '/importDandiAsset') {
            const dandisetId = searchParams.get('dandisetId')
            const dandisetVersion = searchParams.get('dandisetVersion')
            const assetPath = searchParams.get('assetPath')
            const assetUrl = searchParams.get('assetUrl')
            const projectName = searchParams.get('projectName')
            if (!dandisetId || !dandisetVersion || !assetUrl || !assetPath || !projectName) {
                throw new Error('Missing required query parameters')
            }
            return {
                page: 'importDandiAsset',
                dandisetId,
                dandisetVersion,
                assetPath,
                assetUrl,
                projectName
            }
        }
        else if (p === '/github/auth') {
            return {
                page: 'github-auth'
            }
        }
        else {
            return {
                page: 'dandisets'
            }
        }
    }, [p, searchParams])

    const setRoute = useCallback((r: Route, useStaging?: boolean) => {
        const queries = []
        if (useStaging !== undefined) {
            if (useStaging) {
                queries.push(`staging=1`)
            }
        }
        else if (staging) {
            queries.push(`staging=1`)
        }
        if (deployedApi) {
            queries.push(`deployed-api=1`)
        }
        if (r.page === 'project') {
            if (r.tab) queries.push(`tab=${r.tab}`)
        }
        const queryString = queries.length > 0 ? `?${queries.join('&')}` : ''
        if (r.page === 'dandisets') {
            navigate('/dandisets' + queryString)
        }
        else if (r.page === 'dandiset') {
            let p = '/'
            if (r.dandisetId) p = `/dandiset/${r.dandisetId}`
            navigate(p + queryString)
        }
        else if (r.page === 'project') {
            navigate(`/project/${r.projectId}` + queryString)
        }
        else if (r.page === 'compute-resource') {
            navigate(`/compute-resource/${r.computeResourceId}` + queryString)
        }
        else if (r.page === 'compute-resources') {
            navigate('/compute-resources' + queryString)
        }
        else if (r.page === 'projects') {
            navigate('/projects' + queryString)
        }
        else if (r.page === 'register-compute-resource') {
            navigate(`/register-compute-resource/${r.computeResourceId}/${r.resourceCode}` + queryString)
        }
        else if (r.page === 'importDandiAsset') {
            navigate(`/importDandiAsset?dandisetId=${r.dandisetId}&dandisetVersion=${r.dandisetVersion}&assetPath=${r.assetPath}&assetUrl=${r.assetUrl}&projectName=${r.projectName}`)
        }
        else if (r.page === 'github-auth') {
            navigate('/github/auth' + queryString)
        }
        else if (r.page === 'about') {
            navigate('/about' + queryString)
        }
        else if (r.page === 'admin') {
            navigate('/admin' + queryString)
        }
    }, [navigate, staging, deployedApi])

    const toggleStaging = useCallback(() => {
        if (staging) {
            searchParams.delete('staging')
        }
        else {
            searchParams.set('staging', '1')
        }
        let p2 = p
        if (p2.startsWith('/dandiset/')) {
            p2 = '/'
        }
        navigate(`${p2}?${searchParams.toString()}`)
    }, [navigate, p, searchParams, staging])

    return {
        route,
        setRoute,
        staging,
        toggleStaging
    }    
}

export default useRoute