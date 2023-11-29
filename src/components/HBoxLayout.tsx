import React, { PropsWithChildren, useMemo } from "react"
import { ReactElement } from "react-markdown/lib/react-markdown"

type HBoxLayoutProps = {
    widths: number[]
    height: number
    spacing?: number
}

const HBoxLayout: React.FunctionComponent<PropsWithChildren<HBoxLayoutProps>> = ({widths, height, spacing = 0, children}) => {
    const totalWidth = widths.reduce((a, b) => (a + b), 0)
    const children2 = React.Children.toArray(children).map(ch => (ch as any as ReactElement))
    const lefts = useMemo(() => {
        const lefts: number[] = []
        let left = 0
        for (const width of widths) {
            lefts.push(left)
            left += width + spacing
        }
        return lefts
    }, [widths, spacing])
    return (
        <div className="HBoxLayout" style={{position: 'relative', width: totalWidth, height}}>
            {
                children2.map((child: ReactElement, i) => {
                    return child ? (
                        <div key={i} style={{position: 'absolute', overflow: 'hidden', background: 'white', left: lefts[i], top: 0, width: widths[i], height}}>
                            <child.type {...child.props} width={widths[i]} height={height} />
                        </div>
                    ) : <span />
                })
            }
        </div>
    )
}

export default HBoxLayout