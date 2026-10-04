import { WorkerBridge } from './worker-bridge.js';
export class RawConvertWorker {
    constructor(bridge) {
        this.bridge = bridge;
    }
    static async init(options) {
        const workerUrl = options?.workerUrl || new URL('./worker.js', import.meta.url);
        const worker = new Worker(workerUrl, { type: 'classic' });
        const bridge = new WorkerBridge(worker);
        await bridge.send({
            type: 'init',
            coreUrl: options?.coreUrl,
            wasmUrl: options?.wasmUrl,
        });
        return new RawConvertWorker(bridge);
    }
    async load(data, filename) {
        return this.bridge.send({ type: 'load', data, filename }, [data]);
    }
    async getMetadata() {
        return this.bridge.send({ type: 'getMetadata' });
    }
    async getThumbnail() {
        return this.bridge.send({ type: 'getThumbnail' });
    }
    async process(options) {
        return this.bridge.send({ type: 'process', options });
    }
    async convert(data, options) {
        return this.bridge.send({ type: 'convert', data, filename: undefined, options }, [data]);
    }
    async reset() {
        return this.bridge.send({ type: 'reset' });
    }
    dispose() {
        this.bridge.terminate();
    }
}
