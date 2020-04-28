CallbackQueue = function(eventName) {
    this._queue = [];
    this._eventName = eventName;
};

CallbackQueue.prototype = {
    push: function(callback) {
        this._queue.push(callback);
    },
    process: function(div) {
        while (cb = this._queue.pop()) {
            cb(div);
        }
        this.trigger(div);
    },
    trigger: function(div) {
        if (this._eventName) $(document).trigger(this._eventName, [div]);
        $(document).off(this._eventName);
    }
}
