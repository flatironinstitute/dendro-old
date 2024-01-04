import fs from "./fs"
import git from 'isomorphic-git'
import http from 'isomorphic-git/http/web'

class ClonedRepo {
    #initialized = false
    #dir: string
    constructor(private a: {url: string, branch: string}) {
        this.#dir = '/repos/' + toBase64StringSuitableForFolderName(a.url + '||' + a.branch)
    }
    async clear() {
        await removeDirectoryRecursive(this.#dir)
    }
    async initialize(setStatus: (status: string) => void) {
        if (this.#initialized) {
            return
        }
        if (!(await checkDirectoryExists('/repos'))) {
            await fs.promises.mkdir('/repos')
        }
        const {url, branch} = this.a
        let exists = await checkDirectoryExists(this.#dir)
        if (exists) {
            if (!checkValidRepo(this.#dir)) {
                await removeDirectoryRecursive(this.#dir)
                exists = false
            }
        }
        if (!exists) {
            console.info(`Cloning ${url} to ${this.#dir}`)
            setStatus(`Cloning ${url}`)
            await git.clone({ fs, http, dir: this.#dir, ref: branch, singleBranch: true, depth: 1, url, corsProxy: 'https://cors.isomorphic-git.org' })
        }
        exists = await checkDirectoryExists(this.#dir)
        if (!exists) {
            console.warn('Unexpected: directory does not exist after clone.')
            return
        }
        console.info(`Pulling`)
        setStatus(`Pulling ${url}`)
        await git.pull({fs, http, dir: this.#dir, author: {name: 'undefined'}})
        this.#initialized = true
    }
    async readDirectory(d: string) {
        const subdirectories: string[] = []
        const files: string[] = []
        const fullPath = joinPaths(this.#dir, d)
        const a = await fs.promises.readdir(fullPath)
        for (const f of a) {
            const p = joinPaths(fullPath, f)
            const s = await fs.promises.stat(p)
            if (s.isDirectory()) {
                subdirectories.push(f)
            }
            else if (s.isFile()) {
                files.push(f)
            }
        }
        return {subdirectories, files}
    }
    async readTextFile(p: string): Promise<string> {
        const fullPath = joinPaths(this.#dir, p)
        const a = await fs.promises.readFile(fullPath, 'utf8')
        return a as string
    }
}

const checkValidRepo = async (dir: string): Promise<boolean> => {
    if (!(await checkDirectoryExists(`${dir}/.git`))) return false
    if (!(await checkFileExists(`${dir}/.git/index`))) return false
    if (!(await checkFileExists(`${dir}/.git/refs/heads/main`))) return false
    return true
}

const checkFileExists = async (f: string): Promise<boolean> => {
	try {
		const s = await fs.promises.stat(f)
		return s.isFile()
	}
	catch(err) {
		return false
	}
}

const checkDirectoryExists = async (dir: string): Promise<boolean> => {
	try {
		const s = await fs.promises.stat(dir)
		return s.isDirectory()
	}
	catch(err) {
		return false
	}
}

export const joinPaths = (a: string, b: string) => {
    if (!a) return b;
    if (!b) return a;
    if (a.endsWith('/')) {
        return a + b;
    }
    else {
        return a + '/' + b;
    }
}

const removeDirectoryRecursive = async (dir: string) => {
	console.info(`Removing directory: ${dir}`)
	if (!dir.endsWith('/')) dir = dir + '/'
	const files = await fs.promises.readdir(dir)
	for (const f of files) {
		const path = `${dir}${f}`
		const ss = await fs.promises.stat(path)
		if (ss.isDirectory()) {
			await removeDirectoryRecursive(path)
		}
		else {
			console.info(`Removing ${path}`)
			await fs.promises.unlink(path)
		}
	}
	if ((dir !== '') && (dir !== '/')) {
		await fs.promises.rmdir(dir)
	}
}

const toBase64StringSuitableForFolderName = (str: string) => {
    const a = btoa(str)
    return a.replace(/\//g, '_')
}

export default ClonedRepo