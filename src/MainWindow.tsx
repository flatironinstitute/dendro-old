import { FunctionComponent } from "react";
import ApplicationBar from "./ApplicationBar";
import AboutPage from "./pages/AboutPage/AboutPage";
import HomePage from "./pages/HomePage/HomePage";
import useRoute from "./useRoute";
import DandiBrowser from "./pages/DandiBrowser/DandiBrowser";
import ProjectPage from "./pages/ProjectPage/ProjectPage";
import RegisterComputeResourcePage from "./pages/RegisterComputeResourcePage/RegisterComputeResourcePage";
import ComputeResourcePage from "./pages/ComputeResourcePage/ComputeResourcePage";
import ComputeResourcesPage from "./pages/ComputeResourcesPage/ComputeResourcesPage";
import GitHubAuthPage from "./GitHub/GitHubAuthPage";
import ProjectsPage from "./pages/ProjectsPage/ProjectsPage";

type Props = {
    // none
}

const MainWindow: FunctionComponent<Props> = () => {
    const {route} = useRoute()
    return (
        <div id="main-window">
            <ApplicationBar />
            {
                route.page === 'home' ? (
                    <HomePage />
                ) : (route.page === 'dandisets' || route.page === 'dandiset') ? (
                    <DandiBrowser/>
                ) : route.page === 'project' ? (
                    <ProjectPage/>
                ) : route.page === 'about' ? (
                    <AboutPage/>
                ) : route.page === 'compute-resource' ? (
                    <ComputeResourcePage
                        computeResourceId={route.computeResourceId}
                    />
                ) : route.page === 'compute-resources' ? (
                    <ComputeResourcesPage />
                ) : route.page === 'projects' ? (
                    <ProjectsPage />
                ) : route.page === 'register-compute-resource' ? (
                    <RegisterComputeResourcePage />
                ) : route.page === 'github-auth' ? (
                    <GitHubAuthPage />
                ) : (
                    <div>404</div>
                )
            }
        </div>
    )
}

export default MainWindow