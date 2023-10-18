import React, { PropsWithChildren } from "react"
import { ReactElement } from "react-markdown/lib/react-markdown"

type HBoxLayoutProps = {
    widths: number[]
    height: number
}

const HBoxLayout: React.FunctionComponent<PropsWithChildren<HBoxLayoutProps>> = ({widths, height, children}) => {
    const totalWidth = widths.reduce((a, b) => (a + b), 0)
    const children2 = React.Children.toArray(children).map(ch => (ch as any as ReactElement))
    return (
        <div style={{position: 'relative', width: totalWidth, height}}>
            {
                children2.map((child: ReactElement, i) => {
                    return child ? (
                        <div key={i} style={{position: 'absolute', left: widths.slice(0, i).reduce((a, b) => (a + b), 0), top: 0, width: widths[i], height}}>
                            <child.type {...child.props} width={widths[i]} height={height} />
                        </div>
                    ) : <span />
                })
            }
        </div>
    )
}

export default HBoxLayout