import { FunctionComponent, useEffect } from "react";
import useRoute from "../../useRoute";

type Props = {

}

const HomePage: FunctionComponent<Props> = ({ }) => {
    const {setRoute} = useRoute()
    useEffect(() => {
        setRoute({page: 'dandisets'})
    }, [setRoute])
    return (
        <div>...</div>
    )
}

export default HomePage