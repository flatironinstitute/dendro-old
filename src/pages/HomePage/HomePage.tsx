import { FunctionComponent, useEffect } from "react";
import './HomePage.css'
import { Hyperlink } from "@fi-sci/misc";
import useRoute from "../../useRoute";

type Props = {
    width: number
    height: number
}

const HomePage: FunctionComponent<Props> = ({width, height}) => {
    const {setRoute} = useRoute()
    return (
        <div className="HomePage">
            <h1>Welcome to Dendro!</h1>
            <p>
                <Hyperlink onClick={() => setRoute({page: 'dandisets'})}>
                    Import from DANDI
                </Hyperlink>
            </p>
            <p>
                <Hyperlink onClick={() => setRoute({page: 'projects'})}>
                    Manage projects
                </Hyperlink>
            </p>
            <p>
                <Hyperlink onClick={() => setRoute({page: 'compute-resources'})}>
                    Configure compute
                </Hyperlink>
            </p>
            <p>
                <Hyperlink onClick={() => {
                    window.open('https://github.com/flatironinstitute/dendro', '_blank')
                }}>
                    Star us on GitHub
                </Hyperlink>
            </p>
            <p>
                <Hyperlink onClick={() => {
                    window.open('https://flatironinstitute.github.io/dendro-docs/docs/intro', '_blank')
                }}>
                    View the documentation
                </Hyperlink>
            </p>
        </div>
    )
}

export default HomePage