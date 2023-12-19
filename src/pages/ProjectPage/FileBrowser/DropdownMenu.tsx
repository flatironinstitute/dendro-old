import { Menu } from '@mui/icons-material';
import React, { useState } from 'react';
import { SmallIconButton } from "@fi-sci/misc";
import './DropdownMenu.css';

type Option = {
    label: string;
    onClick?: () => void;
};

type MinimalDropdownProps = {
    options: Option[];
};

const DropdownMenu: React.FC<MinimalDropdownProps> = ({ options }) => {
    const [isOpen, setIsOpen] = useState(false)

    return (
        <div className='DropdownMenu'>
            <SmallIconButton icon={<Menu />} onClick={() => setIsOpen(!isOpen)} />
            {isOpen && (
                <ul
                    style={{
                        listStyle: 'none',
                        margin: 0,
                        padding: '5px 0',
                        position: 'absolute',
                        backgroundColor: '#fff',
                        boxShadow: '0px 2px 5px rgba(0,0,0,0.2)',
                        width: '200px',
                        zIndex: 100
                    }}
                >
                    {options.map(option => (
                        <li
                            className={option.onClick ? 'enabled' : 'disabled'}
                            key={option.label}
                            onClick={() => {
                                option.onClick?.();
                                setIsOpen(false);
                            }}
                            style={{
                                padding: '5px 10px',
                                cursor: 'pointer',
                                textAlign: 'left',
                                color: option.onClick ? '#000' : '#999'
                            }}
                        >
                            {option.label}
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
};

export default DropdownMenu;
