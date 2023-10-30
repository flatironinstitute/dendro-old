import { Computer, Help, Key, Login, Logout, Work } from "@mui/icons-material";
import { AppBar, Toolbar } from "@mui/material";
import { FunctionComponent, useCallback, useMemo, useState } from "react";
import ApiKeysWindow from "./ApiKeysWindow/ApiKeysWindow";
import GitHubLoginWindow from "./GitHub/GitHubLoginWindow";
import { useGithubAuth } from "./GithubAuth/useGithubAuth";
import UserIdComponent from "./UserIdComponent";
import ModalWindow from "./components/ModalWindow/ModalWindow";
import SmallIconButton from "./components/SmallIconButton";
import useRoute from "./useRoute";

type Props = {
    // none
}

export const applicationBarHeight = 45
export const applicationBarColor = '#bac'
export const applicationBarColorDarkened = '#546'

const ApplicationBar: FunctionComponent<Props> = () => {
    const {setRoute} = useRoute()
    const {signedIn, userId} = useGithubAuth()

    const {visible: githubAccessWindowVisible, handleOpen: openGitHubAccessWindow, handleClose: closeGitHubAccessWindow} = useModalDialog()
    const {visible: apiKeysWindowVisible, handleOpen: openApiKeysWindow, handleClose: closeApiKeysWindow} = useModalDialog()

    const onHome = useCallback(() => {
        setRoute({page: 'home'})
    }, [setRoute])

    const onHelp = useCallback(() => {
        window.open('https://github.com/flatironinstitute/dendro/blob/main/README.md', '_blank')
    }, [])

    return (
        <span>
            <AppBar position="static" style={{height: applicationBarHeight - 10, color: 'black', background: applicationBarColor}}>
                <Toolbar style={{minHeight: applicationBarHeight - 10}}>
                    <img src="/dendro.png" alt="logo" height={30} style={{paddingBottom: 3, cursor: 'pointer'}} onClick={onHome} />
                    <div onClick={onHome} style={{cursor: 'pointer'}}>&nbsp;&nbsp;&nbsp;dendro (prototype v3)</div>
                    <span style={{marginLeft: 'auto'}} />
                    <span>
                        <SmallIconButton
                            icon={<Help />}
                            onClick={onHelp}
                            title={`View the documentation`}
                        />
                    </span>
                    &nbsp;&nbsp;
                    <span>
                        <SmallIconButton
                            icon={<Computer />}
                            onClick={() => setRoute({page: 'compute-resources'})}
                            title={`Configure compute resources`}
                        />
                    </span>
                    &nbsp;&nbsp;
                    <span>
                        <SmallIconButton
                            icon={<Work />}
                            onClick={() => setRoute({page: 'projects'})}
                            title={`Manage projects`}
                        />
                    </span>
                    &nbsp;&nbsp;
                    <span style={{color: 'yellow'}}>
                        <SmallIconButton
                            icon={<Key />}
                            onClick={openApiKeysWindow}
                            title={`Set DANDI API key`}
                        />
                    </span>
                    &nbsp;&nbsp;
                    {
                        signedIn && (
                            <span style={{fontFamily: 'courier', color: 'lightgray', cursor: 'pointer'}} title={`Signed in as ${userId}`} onClick={openGitHubAccessWindow}><UserIdComponent userId={userId} />&nbsp;&nbsp;</span>
                        )
                    }
                    <span style={{paddingBottom: 0, cursor: 'pointer'}} onClick={openGitHubAccessWindow} title={signedIn ? "Manage log in" : "Log in"}>
                        {
                            signedIn ? (
                                <Logout />
                            ) : (
                                <Login />
                            )
                        }
                        &nbsp;
                        {
                            !signedIn && (
                                <span style={{position: 'relative', top: -5}}>Log in</span>
                            )
                        }
                    </span>
                </Toolbar>
            </AppBar>
            <ModalWindow
                open={githubAccessWindowVisible}
                // onClose={closeGitHubAccessWindow}
            >
                <GitHubLoginWindow
                    onClose={() => closeGitHubAccessWindow()}
                />
            </ModalWindow>
            <ModalWindow
                open={apiKeysWindowVisible}
                // onClose={closeApiKeysWindow}
            >
                <ApiKeysWindow
                    onClose={() => closeApiKeysWindow()}
                />
            </ModalWindow>
        </span>
    )
}

export const useModalDialog = () => {
    const [visible, setVisible] = useState<boolean>(false)
    const handleOpen = useCallback(() => {
        setVisible(true)
    }, [])
    const handleClose = useCallback(() => {
        setVisible(false)
    }, [])
    return useMemo(() => ({
        visible,
        handleOpen,
        handleClose
    }), [visible, handleOpen, handleClose])
}


export default ApplicationBar