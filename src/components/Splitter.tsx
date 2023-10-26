import React, { FunctionComponent, PropsWithChildren, ReactElement, useEffect, useState } from 'react';
import Draggable, { DraggableData, DraggableEvent } from 'react-draggable';

interface Props {
    // width: number
    // height: number
    initialPosition: number // Ratio?
    positionFromRight?: boolean
    onChange?: (newPosition: number) => void
    gripThickness?: number
    gripInnerThickness?: number
    gripMargin?: number
    adjustable?: boolean
    direction?: 'horizontal' | 'vertical'
    hideSecondChild?: boolean
}

const defaultGripThickness = 10
const defaultGripInnerThickness = 4
const defaultGripMargin = 2

// see: https://github.com/react-grid-layout/react-draggable/issues/652
const Draggable1: any = Draggable

const Splitter: FunctionComponent<PropsWithChildren<Props>> = (props) => {
    const { width, height, initialPosition, onChange, adjustable=true, positionFromRight=false, direction='horizontal', hideSecondChild} = props

    const size1 = direction === 'horizontal' ? width : height
    // const size2 = direction === 'horizontal' ? height : width

    const [gripPosition, setGripPosition] = useState<number>(initialPosition)
    useEffect(() => {

        if (gripPosition > size1 - 4) {
            setGripPosition(size1 - 4)
        }
        else if ((gripPosition < 4) && (size1 > 20)) {
            setGripPosition(4)
        }
    }, [gripPosition, width, size1])

    // See: https://stackoverflow.com/questions/63603902/finddomnode-is-deprecated-in-strictmode-finddomnode-was-passed-an-instance-of-d
    // const draggableNodeRef = React.useRef(null)
    // this was actually causing an error with Draggable

    if (!props.children) throw Error('Unexpected: no props.children')

    let child1: ReactElement | null | undefined
    let child2: ReactElement | null | undefined
    if (!Array.isArray(props.children)) {
        child1 = props.children as any as ReactElement
        child2 = null
    }
    else {
        const children = props.children.filter(c => (c !== undefined))
        child1 = children[0] as any as ReactElement || null
        child2 = (children[1] as any as ReactElement) || null
    }
    if (!child1) {
        child1 = child2
        child2 = null
    }

    if (!child1) {
        throw Error('Splitter must have at least one child.')
    }

    if (!child2) {
        return <child1.type {...child1.props}/>
    }

    let gripPositionFromLeft = positionFromRight ? size1 - gripPosition : gripPosition
    if (hideSecondChild) {
        gripPositionFromLeft = size1
    }

    const gripThickness = adjustable ? (props.gripThickness ?? defaultGripThickness) : 0
    const gripInnerThickness = adjustable ? (props.gripInnerThickness ?? defaultGripInnerThickness) : 0
    const gripMargin = adjustable ? (props.gripMargin ?? defaultGripMargin) : 0
    const size1A = gripPositionFromLeft - gripThickness / 2 - gripMargin
    const size1B = size1 - size1A - gripThickness - 2 * gripMargin

    const styleGripOuter: React.CSSProperties = {
        left: 0,
        top: 0,
        backgroundColor: 'transparent',
        cursor: direction === 'horizontal' ? 'col-resize' : 'row-resize',
        zIndex: 9998
    };
    const styleGrip: React.CSSProperties = {
        left: direction === 'horizontal' ? gripMargin : 0,
        top: direction === 'horizontal' ? 0 : gripMargin,
        background: 'rgb(230, 230, 230)',
        cursor: direction === 'horizontal' ? 'col-resize' : 'row-resize'
    };
    const styleGripInner: React.CSSProperties = {
        top: direction === 'horizontal' ? 0 : (gripThickness - gripInnerThickness) / 2,
        left: direction === 'horizontal' ? (gripThickness - gripInnerThickness) / 2 : 0,
        background: 'gray',
        cursor: direction === 'horizontal' ? 'col-resize' : 'row-resize'
    };
    const _handleGripDrag = (evt: DraggableEvent, ui: DraggableData) => {
    }
    const _handleGripDragStop = (evt: DraggableEvent, ui: DraggableData) => {
        const newGripPositionFromLeft = direction === 'horizontal' ? ui.x : ui.y;
        if (newGripPositionFromLeft === gripPositionFromLeft) {
            return;
        }
        const newGripPosition = positionFromRight ? size1 - newGripPositionFromLeft : newGripPositionFromLeft
        setGripPosition(newGripPosition)
        onChange && onChange(newGripPosition)
    }

    console.log('HIEE!', hideSecondChild)
    return (
        <div style={{ 
            position: 'relative', 
            display: 'flex', 
            height: '100%',
            overflow: 'hidden'
        }}>
            <div key="child1" className="splitterChild" style={{ overflow: 'auto' }}>
                <child1.type {...child1.props} />
            </div>
            {
                adjustable && !hideSecondChild && (
                    <Draggable1
                        // nodeRef={draggableNodeRef} // this was actually causing an error with Draggable
                        key="drag"
                        position={{ x: direction === 'horizontal' ? gripPositionFromLeft - gripThickness / 2 - gripMargin : 0, y: direction === 'horizontal' ? 0 : gripPositionFromLeft - gripThickness / 2 - gripMargin }}
                        axis={direction === 'horizontal' ? "x" : "y"}
                        onDrag={(evt: DraggableEvent, ui: DraggableData) => _handleGripDrag(evt, ui)}
                        onStop={(evt: DraggableEvent, ui: DraggableData) => _handleGripDragStop(evt, ui)}
                    >
                        <div style={{...styleGripOuter, position: 'absolute'}}>
                            <div style={{...styleGrip, position: 'absolute'}}>
                                <div style={{...styleGripInner, position: 'absolute'}} />
                            </div>
                        </div>
                    </Draggable1>
                )
            }

            {
                !hideSecondChild && <div key="child2" className="splitterChild" style={{ overflow: 'auto' }}>
                    {/* <child2.type ref={ref} {...child2.props} width={direction === 'horizontal' ? size1B : width} height={direction === 'horizontal' ? height : size1B} /> */}
                    <child2.type {...child2.props} />
                </div>
            }
        </div>
    )
}

export default Splitter