import adminClient from "./adminClient";

export const createApiKey = (data) => {
    return adminClient.post("/admin/keys", data);
};

export const getApiKey = (key) => {
    return adminClient.get(`/admin/keys/${encodeURIComponent(key)}`);
};

export const updateApiKey = (key, data) => {
    return adminClient.put(
        `/admin/keys/${encodeURIComponent(key)}`,
        data
    );
};