window.$docsify = window.$docsify || {};
window.$docsify.mustache = window.$docsify.mustache || {};
window.$docsify.mustache.data = window.$docsify.mustache.data || [];

window.$docsify.mustache.data.push({
    hostname: window.parent.location.hostname,
    isBrev: window.parent.location.hostname.endsWith('brevlab.com'),
    brevId: window.parent.location.hostname.split('.')[0].split('-').slice(1).join('-') || ''
});
