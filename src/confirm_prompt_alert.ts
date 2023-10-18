export const confirm = async (message: string): Promise<boolean> => {
    return window.confirm(message)
}

export const prompt = async (message: string, defaultValue: string): Promise<string | null> => {
    return window.prompt(message, defaultValue)
}

export const alert = async (message: string): Promise<void> => {
    return window.alert(message)
}