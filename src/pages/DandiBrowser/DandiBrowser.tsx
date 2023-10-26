import { Search } from "@mui/icons-material"
import { FunctionComponent, useCallback, useEffect, useState } from "react"
import SearchResults from "./SearchResults"
import { AssetResponse, AssetsResponseItem, DandisetSearchResultItem, DandisetsResponse } from "./types"
import SmallIconButton from "../../components/SmallIconButton"
import useRoute from "../../useRoute"
import Hyperlink from "../../components/Hyperlink"

type Props = {
  
}

export const getDandiApiHeaders = (useStaging: boolean): {[key: string]: string} => {
    const headers: {[key: string]: string} = {}
    const dandiApiKey = useStaging ? (
        localStorage.getItem('dandiStagingApiKey') || ''
    ) : (
        localStorage.getItem('dandiApiKey') || ''
    )
    if (dandiApiKey) {
        headers['Authorization'] = `token ${dandiApiKey}`
    }
    return headers
}


const topBarHeight = 12
const searchBarHeight = 50
const DandiBrowser: FunctionComponent<Props> = ({ }) => {
    const {staging, toggleStaging} = useRoute()
    const [searchText, setSearchText] = useState<string>('')
    const [searchResult, setSearchResults] = useState<DandisetSearchResultItem[]>([])
    const stagingStr = staging ? '-staging' : ''
    useEffect(() => {
        let canceled = false
        setSearchResults([])
        ; (async () => {
            const headers = getDandiApiHeaders(staging)
            const response = await fetch(
                `https://api${stagingStr}.dandiarchive.org/api/dandisets/?page=1&page_size=50&ordering=-modified&search=${searchText}&draft=true&empty=false&embargoed=true`,
                {
                    headers
                }
            )
            if (canceled) return
            if (response.status === 200) {
                const json = await response.json()
                const dandisetResponse = json as DandisetsResponse
                setSearchResults(dandisetResponse.results)
            }
        })()
        return () => {canceled = true}
    }, [searchText, stagingStr, staging])

    return (
        <div className="main">
            <div style={{height: topBarHeight, background: 'white', display: 'flex', justifyContent: 'right'}}>
                {/* <Checkbox checked={staging} onClick={toggleStaging} label="use staging site" /> */}
                <span style={{fontSize: 10}}><Hyperlink onClick={toggleStaging}>use {staging ? 'main site' : 'staging site'}</Hyperlink></span>
                <div style={{width: 50}} />
            </div>
            <div style={{height: searchBarHeight, top: topBarHeight, background: 'white'}}>
                <SearchBar
                    height={searchBarHeight}
                    onSearch={setSearchText}
                />
            </div>
            <SearchResults
                searchResults={searchResult}
                useStaging={staging}
            />
        </div>
    )
}

type SearchBarProps = {
    height: number
    onSearch: (searchText: string) => void
}

const SearchBar: FunctionComponent<SearchBarProps> = ({ height, onSearch }) => {
    const [searchText, setSearchText] = useState<string>('')
    const searchButtonWidth = height
    
    return (
        <div style={{padding: '0px 15px', width: '100%', display: 'flex', flexWrap: 'wrap', alignItems: 'center'}}>
            <SearchButton width={searchButtonWidth} height={height} onClick={() => onSearch(searchText)} />
            <input
                style={{ height: 30, flexGrow: '1', fontSize: 20, padding: 5 }}
                type="text" placeholder="Search DANDI"
                onChange={e => setSearchText(e.target.value)}
                // when enter is pressed
                onKeyDown={e => {
                    if (e.key === 'Enter') {
                        onSearch(searchText)
                    }
                }}
                // do not spell check
                spellCheck={false}
            />
        </div>
    )
}

// const Checkbox: FunctionComponent<{checked: boolean, onClick: () => void, label: string}> = ({checked, onClick, label}) => {
//     return (
//         <div style={{display: 'flex', alignItems: 'center', cursor: 'pointer'}} onClick={onClick}>
//             <div style={{width: 20, height: 20, borderRadius: 3, border: '1px solid black', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
//                 {checked && <div style={{width: 10, height: 10, borderRadius: 2, background: 'black'}} />}
//             </div>
//             <div style={{marginLeft: 5}}>{label}</div>
//         </div>
//     )
// }

type SearchButtonProps = {
    onClick: () => void
    width: number
    height: number
}

const SearchButton: FunctionComponent<SearchButtonProps> = ({onClick, height}) => {
    return (
        <SmallIconButton
            icon={<Search />}
            label=""
            fontSize={height - 5}
        />
    )
}

export default DandiBrowser