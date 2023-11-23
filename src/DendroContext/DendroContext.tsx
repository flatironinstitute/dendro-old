import React, { FunctionComponent, PropsWithChildren, useCallback, useMemo } from 'react';
import { DendroProject } from '../types/dendro-types';

type Props = {
    // none
}

type DendroState = {
    loadedProjects: DendroProject[]
}

type DendroAction = {
    type: 'reportLoadedProject'
    project: DendroProject
}

const dendroReducer = (state: DendroState, action: DendroAction) => {
    switch (action.type) {
        case 'reportLoadedProject':
            return {
                ...state,
                loadedProjects: [...state.loadedProjects.filter(x => x.projectId !== action.project.projectId), action.project]
            }
    }
}

type DendroContextType = {
    loadedProjects: DendroProject[]
    reportLoadedProject: (project: DendroProject) => void
}

const DendroContext = React.createContext<DendroContextType>({
    loadedProjects: [],
    reportLoadedProject: () => {}
})

export const SetupDendro: FunctionComponent<PropsWithChildren<Props>> = ({children}) => {
    const [state, dispatch] = React.useReducer(dendroReducer, {
        loadedProjects: []
    })

    const value = {
        loadedProjects: state.loadedProjects,
        reportLoadedProject: useCallback((project: DendroProject) => {
            dispatch({
                type: 'reportLoadedProject',
                project
            })
        }, [])
    }
    
    return (
        <DendroContext.Provider value={value}>
            {children}
        </DendroContext.Provider>
    )
}

export const useDendro = () => {
    return React.useContext(DendroContext)
}