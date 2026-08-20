import adminClient from "./adminClient";

export const getIpFallbackRule = () => {
    return adminClient.get("/admin/rules/ip-fallback");
};

export const updateIpFallbackRule = (data) => {
    return adminClient.put(
        "/admin/rules/ip-fallback",
        data
    );
};