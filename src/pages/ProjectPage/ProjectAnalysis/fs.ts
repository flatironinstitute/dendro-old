import FS from "@isomorphic-git/lightning-fs"
import {Buffer} from 'buffer'

window.Buffer = Buffer

const fs = new FS('default')

export default fs