import ClonedRepo, { joinPaths } from "./ClonedRepo";

class AnalysisSourceClient {
    constructor(private url: string, private path: string, private clonedRepo: ClonedRepo) {
    }
    static async create(url: string, setStatus: (status: string) => void) {
        const {repoUrl, branch, path} = parseAnalysisSourceUrl(url);
        setStatus(`Cloning repo ${repoUrl}`)
        const clonedRepo = new ClonedRepo({url: repoUrl, branch})
        await clonedRepo.initialize(setStatus)
        return new AnalysisSourceClient(url, path, clonedRepo);
    }
    async readDirectory(path: string) {
        const fullPath = joinPaths(this.path, path);
        const {subdirectories, files} = await this.clonedRepo.readDirectory(fullPath);
        return {subdirectories, files};
    }
    async readTextFile(path: string) {
        const fullPath = joinPaths(this.path, path);
        const txt = await this.clonedRepo.readTextFile(fullPath);
        return txt;
    }
}

export const parseAnalysisSourceUrl = (url: string) => {
    // for example, url = https://github.com/magland/dendro_analysis/tree/main/projects/eb87e88a
    if (!url.startsWith('https://github.com')) {
        throw new Error('Invalid url: ' + url);
    }
    const parts = url.split('/');
    const owner = parts[3];
    const repo = parts[4];
    const a = parts[5];
    if (a === 'tree') {
        const branch = parts[6];
        const path = parts.slice(7).join('/');
        if (!branch) throw new Error('Invalid url: ' + url);
        if (!path) throw new Error('Invalid url: ' + url);
        return {
            repoUrl: `https://github.com/${owner}/${repo}`,
            branch,
            path,
            repoName: repo
        };
    }
    else if (!a) {
        return {
            repoUrl: url,
            branch: '',
            path: '',
            repoName: repo
        };
    }
    else {
        throw new Error('Invalid url: ' + url);
    }
}

export default AnalysisSourceClient;