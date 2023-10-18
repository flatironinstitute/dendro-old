import { FunctionComponent, useEffect } from "react";
import useRoute from "../../useRoute";

type Props = {
    width: number
    height: number
}

const HomePage: FunctionComponent<Props> = ({width, height}) => {
    const {setRoute} = useRoute()
    useEffect(() => {
        setRoute({page: 'dandisets'})
    }, [setRoute])
    return (
        <div>...</div>
    )
}

export default HomePage