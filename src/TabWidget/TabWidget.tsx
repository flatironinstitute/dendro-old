import { FunctionComponent, PropsWithChildren, useCallback, useEffect, useMemo, useState } from "react";
import TabWidgetTabBar from "./TabWidgetTabBar";

type Props = {
    tabs: {
        id: string
        label: string
        closeable: boolean
        icon?: any
    }[]
    currentTabId: string | undefined
    setCurrentTabId: (id: string) => void
    onCloseTab: (id: string) => void
}

const tabBarHeight = 30

const TabWidget: FunctionComponent<PropsWithChildren<Props>> = ({children, tabs, currentTabId, setCurrentTabId, onCloseTab}) => {
    const currentTabIndex = useMemo(() => {
        if (!currentTabId) return undefined
        const index = tabs.findIndex(t => t.id === currentTabId)
        if (index < 0) return undefined
        return index
    }, [currentTabId, tabs])
    const children2 = Array.isArray(children) ? (children as React.ReactElement[]) : ([children] as React.ReactElement[])
    if ((children2 || []).length !== tabs.length) {
        throw Error(`TabWidget: incorrect number of tabs ${(children2 || []).length} <> ${tabs.length}`)
    }

    const [hasBeenVisible, setHasBeenVisible] = useState<number[]>([])
    useEffect(() => {
        if (currentTabIndex === undefined) return
        if (!hasBeenVisible.includes(currentTabIndex)) {
            setHasBeenVisible([...hasBeenVisible, currentTabIndex])
        }
    }, [currentTabIndex, hasBeenVisible])
    const handleSetCurrentTabIndex = useCallback((index: number) => {
        if (index < 0 || index >= tabs.length) return
        setCurrentTabId(tabs[index].id)
    }, [setCurrentTabId, tabs])
    return (
        <div
            style={{overflow: 'hidden'}}
            className="TabWidget"
        >
            <div key="tabwidget-bar" style={{ height: tabBarHeight }}>
                <TabWidgetTabBar
                    tabs={tabs}
                    currentTabIndex={currentTabIndex}
                    onCurrentTabIndexChanged={handleSetCurrentTabIndex}
                    onCloseTab={onCloseTab}
                />
            </div>
            {
                children2.map((c, i) => {
                    const visible = i === currentTabIndex
                    return (
                        <div key={`child-${i}`} style={{visibility: visible ? undefined : 'hidden', overflowY: 'hidden', overflowX: 'hidden', position: 'absolute', left: 0, top: tabBarHeight, width: W, height: H, background: 'white'}}>
                            {(visible || hasBeenVisible.includes(i)) && (
                                <c.type {...c.props}/>
                            )}
                        </div>
                    )
                })
            }
        </div>
    )
}

export default TabWidget