import { useCallback, useMemo } from "react"
import { useLocation, useNavigate } from "react-router-dom"

export type Route = {
    page: 'home'
} | {
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
    page: 'about'
}

const useRoute = () => {
    const location = useLocation()
    const navigate = useNavigate()
    const p = location.pathname
    const search = location.search
    const searchParams = useMemo(() => new URLSearchParams(search), [search])
    const staging = searchParams.get('staging') === '1'
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
        else {
            return {
                page: 'home'
            }
        }
    }, [p, searchParams])

    const setRoute = useCallback((r: Route) => {
        const queries = []
        if (staging) queries.push(`staging=1`)
        if (r.page === 'project') {
            if (r.tab) queries.push(`tab=${r.tab}`)
        }
        const queryString = queries.length > 0 ? `?${queries.join('&')}` : ''
        if (r.page === 'home') {
            navigate('/' + queryString)
        }
        else if (r.page === 'dandisets') {
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
        else if (r.page === 'about') {
            if (staging) {
                navigate('/about?staging=1')
            }
            else {
                navigate('/about')
            }
        }
    }, [navigate, staging])

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