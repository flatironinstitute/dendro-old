import { FunctionComponent } from "react";

type Props = {
    width: number
    height: number
}

const AboutPage: FunctionComponent<Props> = ({width, height}) => {
    return (
        <div>
            This is dendro.
        </div>
    )
}

export default AboutPage