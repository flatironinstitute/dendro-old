export type FileAction = {
    name: string
    label: string
    processorName: string
    outputFileBaseName: string
    icon: any
}

export const fileActions: FileAction[] = [
    // {
    //     name: 'spike_sorting_summary',
    //     label: 'SS Summary',
    //     processorName: 'dandi-vis-1.spike_sorting_summary',
    //     outputFileBaseName: 'spike_sorting_summary.nh5',
    //     icon: <Settings />
    // },
    // {
    //     name: 'ecephys_summary',
    //     label: 'Ecephys Summary',
    //     processorName: 'dandi-vis-1.ecephys_summary',
    //     outputFileBaseName: 'ecephys_summary.nh5',
    //     icon: <Settings />
    // }
]
