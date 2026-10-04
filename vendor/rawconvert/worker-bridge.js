export class WorkerBridge {
    constructor(worker) {
        this.nextId = 0;
        this.pending = new Map();
        this.worker = worker;
        this.worker.onmessage = (e) => {
            const { id, type, result, error } = e.data;
            const handler = this.pending.get(id);
            if (!handler)
                return;
            this.pending.delete(id);
            if (type === 'error') {
                handler.reject(new Error(error || 'Worker error'));
            }
            else {
                handler.resolve(result);
            }
        };
    }
    send(request, transfer) {
        return new Promise((resolve, reject) => {
            const id = this.nextId++;
            this.pending.set(id, { resolve, reject });
            this.worker.postMessage({ ...request, id }, transfer || []);
        });
    }
    terminate() {
        this.pending.forEach(({ reject }) => reject(new Error('Worker terminated')));
        this.pending.clear();
        this.worker.terminate();
    }
}
