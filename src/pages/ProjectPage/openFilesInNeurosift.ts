import { url } from "inspector";
import { DendroFile } from "../../types/dendro-types";

const openFilesInNeurosift = async (files: DendroFile[], dendroProjectId: string) => {
    const urls = files.map((file) => urlFromFileContent(file.content));
    let urlQuery = urls.map((url) => `url=${url}`).join('&');
    // const fileNameQuery = files.map((file) => `fileName=${file.fileName}`).join('&');
    // const neurosiftUrl = `https://flatironinstitute.github.io/neurosift/?p=/nwb&${urlQuery}&dendroProjectId=${dendroProjectId}&${fileNameQuery}`;
    const dandisetId = files[0]?.metadata.dandisetId;
    const dandisetVersion = files[0]?.metadata.dandisetVersion;
    const dandiAssetId = files[0]?.metadata.dandiAssetId;
    if (dandisetId) urlQuery += `&dandisetId=${dandisetId}`;
    if (dandisetVersion) urlQuery += `&dandisetVersion=${dandisetVersion}`;
    if (dandiAssetId) urlQuery += `&dandiAssetId=${dandiAssetId}`;
    const neurosiftUrl = `https://flatironinstitute.github.io/neurosift/?p=/nwb&${urlQuery}`;
    window.open(neurosiftUrl, '_blank');
}

const urlFromFileContent = (content: string) => {
    if (!content.startsWith('url:')) {
        throw new Error('Invalid file content: ' + content);
    }
    return content.substring('url:'.length);
}

export default openFilesInNeurosift;