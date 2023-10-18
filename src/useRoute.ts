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
                projectId
            }
        }
        else {
            return {
                page: 'home'
            }
        }
    }, [p])

    const setRoute = useCallback((r: Route) => {
        if (r.page === 'home') {
            if (staging) {
                navigate('/?staging=1')
            }
            else {
                navigate('/')
            }
        }
        else if (r.page === 'dandisets') {
            if (staging) {
                navigate('/dandisets?staging=1')
            }
            else {
                navigate('/dandisets')
            }
        }
        else if (r.page === 'dandiset') {
            let p = '/'
            if (r.dandisetId) p = `/dandiset/${r.dandisetId}`
            if (staging) {
                navigate(p + '?staging=1')
            }
            else {
                navigate(p)
            }
        }
        else if (r.page === 'project') {
            if (staging) {
                navigate(`/project/${r.projectId}?staging=1`)
            }
            else {
                navigate(`/project/${r.projectId}`)
            }
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