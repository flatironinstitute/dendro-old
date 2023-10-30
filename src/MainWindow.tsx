import { FunctionComponent } from "react";
import ApplicationBar, { applicationBarHeight } from "./ApplicationBar";
import AboutPage from "./pages/AboutPage/AboutPage";
import HomePage from "./pages/HomePage/HomePage";
import useRoute from "./useRoute";
import useWindowDimensions from "./useWindowDimensions";
import DandiBrowser from "./pages/DandiBrowser/DandiBrowser";
import ProjectPage from "./pages/ProjectPage/ProjectPage";
import RegisterComputeResourcePage from "./pages/RegisterComputeResourcePage/RegisterComputeResourcePage";
import ComputeResourcePage from "./pages/ComputeResourcePage/ComputeResourcePage";
import ComputeResourcesPage from "./pages/ComputeResourcesPage/ComputeResourcesPage";
import GitHubAuthPage from "./GitHub/GitHubAuthPage";
import ProjectsPage from "./pages/ProjectsPage/ProjectsPage";
import VBoxLayout from "./components/VBoxLayout";

type Props = {
    // none
}

const MainWindow: FunctionComponent<Props> = () => {
    const {route} = useRoute()
    const {width, height} = useWindowDimensions()
    const H1 = applicationBarHeight
    const H2 = height - applicationBarHeight
    return (
        <VBoxLayout
            width={width}
            heights={[H1, H2]}
        >
            <ApplicationBar />
            <>{
                route.page === 'home' ? (
                    <HomePage width={width} height={H2} />
                ) : (route.page === 'dandisets' || route.page === 'dandiset') ? (
                    <DandiBrowser width={width} height={H2} />
                ) : route.page === 'project' ? (
                    <ProjectPage width={width} height={H2} />
                ) : route.page === 'about' ? (
                    <AboutPage width={width} height={H2} />
                ) : route.page === 'compute-resource' ? (
                    <ComputeResourcePage
                        width={width}
                        height={H2}
                        computeResourceId={route.computeResourceId}
                    />
                ) : route.page === 'compute-resources' ? (
                    <ComputeResourcesPage width={width} height={height} />
                ) : route.page === 'projects' ? (
                    <ProjectsPage width={width} height={height} />
                ) : route.page === 'register-compute-resource' ? (
                    <RegisterComputeResourcePage />
                ) : route.page === 'github-auth' ? (
                    <GitHubAuthPage />
                ) : (
                    <div>404</div>
                )
            }</>
        </VBoxLayout>
    )
}

export default MainWindow