/**
 * Zook UI Logger
 *
 * Provides consistent event fields while keeping console format.
 */
(function createZookLogger() {
    function formatValue(value) {
        if (value === null || value === undefined) {
            return null;
        }
        if (typeof value === 'boolean') {
            return value ? 'true' : 'false';
        }
        if (typeof value === 'number') {
            return String(value);
        }
        const text = String(value);
        if (/\s|"/.test(text)) {
            return `"${text.replace(/"/g, '\\"')}"`;
        }
        return text;
    }

    function formatFields(fields) {
        const parts = [];
        Object.keys(fields || {}).sort().forEach((key) => {
            const formatted = formatValue(fields[key]);
            if (formatted !== null) {
                parts.push(`${key}=${formatted}`);
            }
        });
        return parts.join(' ');
    }

    function log(level, event, fields, message) {
        const context = formatFields(Object.assign({ event }, fields || {}));
        const base = message || event;
        const output = context ? `${base} | ${context}` : base;
        const handler = console[level] || console.log;
        handler(output);
    }

    window.ZookLogger = {
        log,
        info: (event, fields, message) => log('log', event, fields, message),
        warn: (event, fields, message) => log('warn', event, fields, message),
        error: (event, fields, message) => log('error', event, fields, message),
        debug: (event, fields, message) => {
            if (window.ZookConfig && window.ZookConfig.DEBUG) {
                log('debug', event, fields, message);
            }
        }
    };
})();
