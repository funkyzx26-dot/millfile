"use strict";
// Worker script — runs in a dedicated Worker context
// Uses importScripts for classic worker compatibility
const workerSelf = self;
const COLOR_SPACE_MAP = {
    raw: 0, srgb: 1, adobe: 2, 'wide-gamut': 3, prophoto: 4, xyz: 5,
};
const INTERPOLATION_MAP = {
    linear: 0, vng: 1, ppg: 2, ahd: 3, dcb: 4, dht: 11, aahd: 12,
};
let module = null;
let processor = null;
function respond(id, result, transfer) {
    const msg = { id, type: 'result', result };
    workerSelf.postMessage(msg, transfer || []);
}
function respondError(id, error) {
    const msg = { id, type: 'error', error };
    workerSelf.postMessage(msg);
}
function toInternalOptions(opts) {
    return {
        colorSpace: COLOR_SPACE_MAP[opts?.colorSpace ?? 'srgb'] ?? 1,
        interpolation: INTERPOLATION_MAP[opts?.interpolation ?? 'ahd'] ?? 3,
        outputBps: opts?.outputBps ?? 8,
        halfSize: opts?.halfSize ?? false,
        autoWhiteBalance: opts?.autoWhiteBalance ?? false,
        cameraWhiteBalance: opts?.cameraWhiteBalance ?? true,
        brightness: opts?.brightness ?? 1.0,
        highlightMode: opts?.highlightMode ?? 0,
        noiseReduction: opts?.noiseReduction ?? 0,
        medianPasses: opts?.medianPasses ?? 0,
    };
}
function loadFile(data, filename) {
    if (!module || !processor)
        throw new Error('Not initialized');
    const uint8 = new Uint8Array(data);
    const ext = filename?.split('.').pop()?.toLowerCase() || 'raw';
    const path = `/tmp/input.${ext}`;
    try {
        module.FS.writeFile(path, uint8);
        const ok = processor.loadFromFile(path);
        if (!ok)
            throw new Error(processor.getLastError() || 'Failed to load RAW file');
        return processor.getMetadata();
    }
    finally {
        try {
            module.FS.unlink(path);
        }
        catch { /* ignore */ }
    }
}
function extractThumbnail() {
    if (!module || !processor)
        throw new Error('Not initialized');
    if (!processor.isLoaded())
        throw new Error('No file loaded');
    const thumbPath = '/tmp/thumbnail.jpg';
    const ok = processor.extractThumbnail(thumbPath);
    if (!ok)
        throw new Error(processor.getLastError() || 'Failed to extract thumbnail');
    try {
        const thumbData = module.FS.readFile(thumbPath);
        const thumbInfo = processor.getThumbnailInfo();
        return {
            width: thumbInfo.width,
            height: thumbInfo.height,
            format: thumbInfo.format === 0 ? 'jpeg' : 'bitmap',
            data: new Uint8Array(thumbData),
        };
    }
    finally {
        try {
            module.FS.unlink(thumbPath);
        }
        catch { /* ignore */ }
    }
}
function processImage(opts) {
    if (!module || !processor)
        throw new Error('Not initialized');
    if (!processor.isLoaded())
        throw new Error('No file loaded');
    const internalOpts = toInternalOptions(opts);
    const ok = processor.process(internalOpts);
    if (!ok)
        throw new Error(processor.getLastError() || 'Failed to process RAW file');
    const pixelsPath = '/tmp/pixels.bin';
    const exported = processor.exportRawPixels(pixelsPath);
    if (!exported)
        throw new Error(processor.getLastError() || 'Failed to export pixels');
    try {
        const rawData = module.FS.readFile(pixelsPath);
        const view = new DataView(rawData.buffer, rawData.byteOffset, rawData.byteLength);
        const width = view.getUint32(0, true);
        const height = view.getUint32(4, true);
        const bps = view.getUint16(8, true);
        const colors = view.getUint8(10);
        const pixelData = rawData.slice(11);
        let data;
        if (bps === 16) {
            data = new Uint16Array(pixelData.buffer, pixelData.byteOffset, pixelData.byteLength / 2);
        }
        else {
            data = new Uint8Array(pixelData);
        }
        return { width, height, colors, bitsPerSample: bps, data };
    }
    finally {
        try {
            module.FS.unlink(pixelsPath);
        }
        catch { /* ignore */ }
    }
}
workerSelf.onmessage = async (e) => {
    const { id, type, data, filename, options, coreUrl, wasmUrl } = e.data;
    try {
        switch (type) {
            case 'init': {
                const url = coreUrl || 'rawconvert-core.js';
                importScripts(url);
                const moduleArgs = {};
                if (wasmUrl) {
                    moduleArgs.locateFile = (path) => path.endsWith('.wasm') ? wasmUrl : path;
                }
                module = await createRawConvertCore(moduleArgs);
                processor = new module.RawProcessor();
                respond(id, null);
                break;
            }
            case 'load': {
                if (!data)
                    throw new Error('No data provided');
                const metadata = loadFile(data, filename);
                respond(id, metadata);
                break;
            }
            case 'getMetadata': {
                if (!processor)
                    throw new Error('Not initialized');
                respond(id, processor.getMetadata());
                break;
            }
            case 'getThumbnail': {
                const thumb = extractThumbnail();
                const buffer = thumb.data.buffer;
                thumb.data = new Uint8Array(buffer);
                respond(id, thumb, [buffer]);
                break;
            }
            case 'process': {
                const result = processImage(options);
                const buffer = result.data.buffer;
                result.data = result.data instanceof Uint16Array
                    ? new Uint16Array(buffer)
                    : new Uint8Array(buffer);
                respond(id, result, [buffer]);
                break;
            }
            case 'convert': {
                if (!data)
                    throw new Error('No data provided');
                loadFile(data, filename);
                const result = processImage(options);
                const buffer = result.data.buffer;
                result.data = result.data instanceof Uint16Array
                    ? new Uint16Array(buffer)
                    : new Uint8Array(buffer);
                respond(id, result, [buffer]);
                break;
            }
            case 'reset': {
                if (processor)
                    processor.reset();
                respond(id, null);
                break;
            }
            case 'dispose': {
                if (processor) {
                    processor.delete();
                    processor = null;
                }
                module = null;
                respond(id, null);
                break;
            }
            default:
                respondError(id, `Unknown request type: ${type}`);
        }
    }
    catch (err) {
        respondError(id, err.message || String(err));
    }
};
