import { FunctionComponent, useCallback } from "react"
import { applicationBarColorDarkened } from "../../ApplicationBar"
import Hyperlink from "../../components/Hyperlink"
import Splitter from "../../components/Splitter"
import useRoute from "../../useRoute"
import DandisetView from "./DandisetView"
import formatByteCount from "./formatByteCount"
import { DandisetSearchResultItem } from "./types"

type SearchResultsProps = {
    searchResults: DandisetSearchResultItem[]
    useStaging?: boolean
}

const defaultMinLeft = 200
const defaultMaxLeft = 500

const SearchResults: FunctionComponent<SearchResultsProps> = ({searchResults, useStaging}) => {
    // const [selectedDandisetItem, setSelectedDandisetItem] = useState<DandisetSearchResultItem | null>(null)
    const {route, setRoute} = useRoute()
    const dandisetId = route.page === 'dandiset' ? route.dandisetId : undefined
    // useEffect(() => {
    //     // reset the selected item when the useStaging changes
    //     // setSelectedDandisetItem(null)
    //     setRoute({page: 'home'})
    // }, [useStaging, setRoute])
    // const handleImportAssets = useCallback(async (assetItems: AssetsResponseItem[]) => {
    //     if (!selectedDandisetItem) return
    //     const {identifier, most_recent_published_version, draft_version} = selectedDandisetItem
    //     const dandisetId = identifier
    //     const dandisetVersion = most_recent_published_version?.version || draft_version?.version || ''
    //     const items = assetItems.map(assetItem => ({dandisetId, dandisetVersion, assetItem}))
    //     await onImportItems(items)
    // }, [selectedDandisetItem, onImportItems])

    const setSelectedDandisetItem = useCallback((item: DandisetSearchResultItem) => {
        setRoute({page: 'dandiset', dandisetId: item.identifier})
    }, [setRoute])

    return (
        <Splitter
            direction='horizontal'
            hideSecondChild={!dandisetId}
        >
            <SearchResultsLeft
                searchResults={searchResults}
                setSelectedItem={setSelectedDandisetItem}
                // onImportItems={onImportItems} // not actually needed
                // onClickAsset={onClickAsset} // not actually needed
            />
            <DandisetView
                dandisetId={dandisetId || ''}
                // onClickAsset={(assetItem: AssetsResponseItem) => {onClickAsset(selectedItem?.identifier || '', selectedItem?.most_recent_published_version?.version || 'draft', assetItem)}}
                useStaging={useStaging}
                onImportItems={undefined}
            />
        </Splitter>
    )
}

const SearchResultsLeft: FunctionComponent<SearchResultsProps & {setSelectedItem: (item: DandisetSearchResultItem) => void}> = ({width, height, searchResults, setSelectedItem}) => {
    return (
        <div style={{
            overflowY: 'auto', 
            height: '100%',
            minWidth: defaultMinLeft
        }}>
            {
                searchResults.map((result, i) => (
                    <SearchResultItem
                        key={i}
                        result={result}
                        width={width}
                        onClick={() => setSelectedItem(result)}
                    />
                ))
            }
        </div>
    )
}

type SearchResultItemProps = {
    result: DandisetSearchResultItem
    onClick: () => void
}

const SearchResultItem: FunctionComponent<SearchResultItemProps> = ({result, onClick}) => {
    const {identifier, created, modified, contact_person, most_recent_published_version, draft_version} = result
    const X = most_recent_published_version || draft_version
    if (!X) return <div>Unexpected error: no version</div>

    return (
        <div style={{padding: 10, borderBottom: 'solid 1px #ccc'}}>
            <div style={{fontSize: 18, fontWeight: 'bold'}}>
                <Hyperlink color={applicationBarColorDarkened} onClick={onClick}>
                    {identifier} ({X.version}): {X.name}
                </Hyperlink>
            </div>
            <div style={{fontSize: 14, color: '#666'}}>Contact: {contact_person}</div>
            <div style={{fontSize: 14, color: '#666'}}>Created {formatTime(created)} | Modified {formatTime(modified)}</div>
            {
                X && (
                    <div style={{fontSize: 14, color: '#666'}}>
                        {X.asset_count} assets, {formatByteCount(X.size)}, status: {X.status}
                    </div>
                )
            }
        </div>
    )
}

export const formatTime = (time: string) => {
    const timestamp = Date.parse(time)
    return new Date(timestamp).toLocaleString()
}

export default SearchResults