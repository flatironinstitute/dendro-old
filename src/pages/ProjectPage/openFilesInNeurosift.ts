import { DendroFile } from "../../types/dendro-types";

const openFilesInNeurosift = async (files: DendroFile[], dendroProjectId: string) => {
    const urls = files.map((file) => urlFromFileContent(file.content));
    const urlQuery = urls.map((url) => `url=${url}`).join('&');
    const fileNameQuery = files.map((file) => `fileName=${file.fileName}`).join('&');
    const neurosiftUrl = `https://flatironinstitute.github.io/neurosift/?p=/nwb&${urlQuery}&dendroProjectId=${dendroProjectId}&${fileNameQuery}`;
    window.open(neurosiftUrl, '_blank');
}

const urlFromFileContent = (content: string) => {
    if (!content.startsWith('url:')) {
        throw new Error('Invalid file content: ' + content);
    }
    return content.substring('url:'.length);
}

export default openFilesInNeurosift;