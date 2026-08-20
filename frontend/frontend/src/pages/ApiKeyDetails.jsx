import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
    getApiKey,
    updateApiKey,
} from "../api/keysApi";

function ApiKeyDetails() {

    const { key } = useParams();

    const [rule, setRule] = useState(null);

    const [form, setForm] = useState({
        name: "",
        tier: "free",
        algorithm: "fixed_window",
        limit: 60,
        windowSeconds: 60,
        scope: "api_key",
        endpoint: "/api/data",
    });

    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");

    useEffect(() => {

        const loadKey = async () => {

            setLoading(true);
            setError("");

            try {

                const response = await getApiKey(key);

                const data = response.data;

                setRule(data.rule);

                setForm({
                    name: data.rule.name || "",
                    tier: data.rule.tier || "free",
                    algorithm:
                        data.rule.algorithm || "fixed_window",
                    limit: data.rule.limit || 60,
                    windowSeconds:
                        data.rule.windowSeconds || 60,
                    scope:
                        data.rule.scope || "api_key",
                    endpoint:
                        data.rule.endpoint || "/api/data",
                });

            } catch (error) {

                console.error(
                    "Failed to load API key:",
                    error
                );

                setError(
                    error.response?.data?.detail ||
                    "Failed to load API key."
                );

            } finally {

                setLoading(false);

            }
        };

        loadKey();

    }, [key]);


    const handleChange = (event) => {

        const { name, value } = event.target;

        setForm((previous) => ({
            ...previous,
            [name]:
                name === "limit" ||
                name === "windowSeconds"
                    ? Number(value)
                    : value,
        }));

        setSuccess("");

    };


    const handleSave = async (event) => {

        event.preventDefault();

        setSaving(true);
        setError("");
        setSuccess("");

        try {

            const response = await updateApiKey(
                key,
                form
            );

            setRule(response.data.rule);

            setSuccess(
                "Rate-limit rule updated successfully."
            );

        } catch (error) {

            console.error(
                "Failed to update API key:",
                error
            );

            setError(
                error.response?.data?.detail ||
                "Failed to update API key."
            );

        } finally {

            setSaving(false);

        }
    };


    if (loading) {

        return (
            <div className="details-page">

                <div className="loading-state">
                    Loading API key...
                </div>

            </div>
        );

    }


    if (error && !rule) {

        return (
            <div className="details-page">

                <Link
                    to="/api-keys"
                    className="back-link"
                >
                    ← Back to API Keys
                </Link>

                <div className="error-message">
                    {error}
                </div>

            </div>
        );

    }


    return (
        <div className="details-page">

            <div className="details-top">

                <div>

                    <Link
                        to="/api-keys"
                        className="back-link"
                    >
                        ← Back to API Keys
                    </Link>

                    <h1>API Key Details</h1>

                    <p>
                        Manage the rate-limit configuration
                        for this API key.
                    </p>

                </div>

            </div>


            {/* KEY INFORMATION */}

            <section className="panel key-info-panel">

                <div className="panel-header">

                    <h2>API Key</h2>

                    <p>
                        This credential identifies the
                        client making requests.
                    </p>

                </div>


                <div className="full-key-display">

                    <code>{key}</code>

                    <button
                        type="button"
                        onClick={() =>
                            navigator.clipboard.writeText(key)
                        }
                    >
                        Copy
                    </button>

                </div>

            </section>


            <div className="details-grid">

                {/* RULE CONFIGURATION */}

                <section className="panel">

                    <div className="panel-header">

                        <h2>Rate Limit Rule</h2>

                        <p>
                            Change how requests from this
                            API key are limited.
                        </p>

                    </div>


                    <form
                        className="api-form"
                        onSubmit={handleSave}
                    >

                        <div className="form-group">

                            <label htmlFor="details-name">
                                Name
                            </label>

                            <input
                                id="details-name"
                                name="name"
                                value={form.name}
                                onChange={handleChange}
                                required
                            />

                        </div>


                        <div className="form-row">

                            <div className="form-group">

                                <label htmlFor="details-tier">
                                    Tier
                                </label>

                                <select
                                    id="details-tier"
                                    name="tier"
                                    value={form.tier}
                                    onChange={handleChange}
                                >

                                    <option value="free">
                                        Free
                                    </option>

                                    <option value="pro">
                                        Pro
                                    </option>

                                    <option value="enterprise">
                                        Enterprise
                                    </option>

                                </select>

                            </div>


                            <div className="form-group">

                                <label htmlFor="details-algorithm">
                                    Algorithm
                                </label>

                                <select
                                    id="details-algorithm"
                                    name="algorithm"
                                    value={form.algorithm}
                                    onChange={handleChange}
                                >

                                    <option value="fixed_window">
                                        Fixed Window
                                    </option>

                                    <option value="token_bucket">
                                        Token Bucket
                                    </option>

                                    <option value="sliding_window_counter">
                                        Sliding Window Counter
                                    </option>

                                </select>

                            </div>

                        </div>


                        <div className="form-row">

                            <div className="form-group">

                                <label htmlFor="details-limit">
                                    Request Limit
                                </label>

                                <input
                                    id="details-limit"
                                    name="limit"
                                    type="number"
                                    min="1"
                                    value={form.limit}
                                    onChange={handleChange}
                                    required
                                />

                            </div>


                            <div className="form-group">

                                <label htmlFor="details-window">
                                    Window
                                </label>

                                <input
                                    id="details-window"
                                    name="windowSeconds"
                                    type="number"
                                    min="1"
                                    value={form.windowSeconds}
                                    onChange={handleChange}
                                    required
                                />

                                <span className="input-hint">
                                    seconds
                                </span>

                            </div>

                        </div>


                        <div className="form-row">

                            <div className="form-group">

                                <label htmlFor="details-scope">
                                    Scope
                                </label>

                                <select
                                    id="details-scope"
                                    name="scope"
                                    value={form.scope}
                                    onChange={handleChange}
                                >

                                    <option value="api_key">
                                        API Key
                                    </option>

                                    <option value="endpoint">
                                        Endpoint
                                    </option>

                                </select>

                            </div>


                            <div className="form-group">

                                <label htmlFor="details-endpoint">
                                    Endpoint
                                </label>

                                <input
                                    id="details-endpoint"
                                    name="endpoint"
                                    value={form.endpoint}
                                    onChange={handleChange}
                                />

                            </div>

                        </div>


                        {error && (

                            <div className="error-message">
                                {error}
                            </div>

                        )}


                        {success && (

                            <div className="success-message">
                                {success}
                            </div>

                        )}


                        <button
                            className="primary-button"
                            type="submit"
                            disabled={saving}
                        >
                            {saving
                                ? "Saving..."
                                : "Save Changes"
                            }
                        </button>

                    </form>

                </section>


                {/* CURRENT CONFIGURATION */}

                <section className="panel">

                    <div className="panel-header">

                        <h2>Current Configuration</h2>

                        <p>
                            Configuration currently stored
                            for this API key.
                        </p>

                    </div>


                    <div className="configuration-list">

                        <div className="configuration-row">

                            <span>Name</span>

                            <strong>
                                {rule?.name}
                            </strong>

                        </div>


                        <div className="configuration-row">

                            <span>Tier</span>

                            <strong>
                                {rule?.tier}
                            </strong>

                        </div>


                        <div className="configuration-row">

                            <span>Algorithm</span>

                            <strong>
                                {rule?.algorithm}
                            </strong>

                        </div>


                        <div className="configuration-row">

                            <span>Limit</span>

                            <strong>
                                {rule?.limit}
                            </strong>

                        </div>


                        <div className="configuration-row">

                            <span>Window</span>

                            <strong>
                                {rule?.windowSeconds}s
                            </strong>

                        </div>


                        <div className="configuration-row">

                            <span>Scope</span>

                            <strong>
                                {rule?.scope}
                            </strong>

                        </div>


                        <div className="configuration-row">

                            <span>Endpoint</span>

                            <strong>
                                {rule?.endpoint || "—"}
                            </strong>

                        </div>


                        <div className="configuration-row">

                            <span>Created</span>

                            <strong>
                                {rule?.createdAt
                                    ? new Date(
                                        rule.createdAt
                                    ).toLocaleString()
                                    : "—"
                                }
                            </strong>

                        </div>


                        <div className="configuration-row">

                            <span>Updated</span>

                            <strong>
                                {rule?.updatedAt
                                    ? new Date(
                                        rule.updatedAt
                                    ).toLocaleString()
                                    : "—"
                                }
                            </strong>

                        </div>

                    </div>

                </section>

            </div>

        </div>
    );
}

export default ApiKeyDetails;