export const apiCall = async (endpoint, method = 'GET', body = null, includeToken = false) => {
    const options = { method };
    if (includeToken) {
        options.headers = { 'x-access-token': localStorage.getItem('token') };
    }
    if (body) {
        if (body instanceof FormData) {
            options.body = body;
        } else {
            if (!options.headers) options.headers = {};
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(body);
        }
    }
    const res = await fetch(endpoint, options);
    if (!res.ok) throw new Error(`${method} failed: ${res.status}`);
    return await res.json();
};