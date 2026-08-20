import { useState } from "react";

import { createApiKey, getApiKey } from "../api/keysApi";

import { Link } from "react-router-dom";

function ApiKeys() {

    const [form, setForm] = useState({
        name: "",
        tier: "free",
        algorithm: "fixed_window",
        limit: 60,
        windowSeconds: 60,
        scope: "api_key",
        endpoint: "/api/data",
    });

    const [createdKey, setCreatedKey] = useState(null);

    const [lookupKey, setLookupKey] = useState("");
    const [lookupResult, setLookupResult] = useState(null);

    const [loading, setLoading] = useState(false);
    const [lookupLoading, setLookupLoading] = useState(false);

    const [error, setError] = useState("");

    const handleChange = (event) => {

        const { name, value } = event.target;

        setForm((previous) => ({
            ...previous,
            [name]:
                name === "limit" || name === "windowSeconds"
                    ? Number(value)
                    : value,
        }));
    };

    const handleCreate = async (event) => {

        event.preventDefault();

        setLoading(true);
        setError("");
        setCreatedKey(null);

        try {

            const response = await createApiKey(form);

            setCreatedKey(response.data);

        } catch (error) {

            console.error("Failed to create API key:", error);

            setError(
                error.response?.data?.detail ||
                "Failed to create API key."
            );

        } finally {

            setLoading(false);
        }
    };

    const handleLookup = async (event) => {

        event.preventDefault();

        if (!lookupKey.trim()) {
            return;
        }

        setLookupLoading(true);
        setError("");
        setLookupResult(null);

        try {

            const response = await getApiKey(lookupKey.trim());

            setLookupResult(response.data);

        } catch (error) {

            console.error("Failed to fetch API key:", error);

            setError(
                error.response?.data?.detail ||
                "Failed to fetch API key."
            );

        } finally {

            setLookupLoading(false);
        }
    };

    return (
        <div className="api-keys-page">

            <div className="page-heading">

                <div>
                    <h1>API Keys</h1>

                    <p>
                        Create and inspect API keys and their
                        rate-limit rules.
                    </p>
                </div>

            </div>


            <div className="api-keys-grid">

                {/* CREATE API KEY */}

                <section className="panel">

                    <div className="panel-header">

                        <div>
                            <h2>Create API Key</h2>

                            <p>
                                Configure a new client and its
                                rate-limit policy.
                            </p>
                        </div>

                    </div>


                    <form
                        className="api-form"
                        onSubmit={handleCreate}
                    >

                        <div className="form-group">

                            <label htmlFor="name">
                                Name
                            </label>

                            <input
                                id="name"
                                name="name"
                                value={form.name}
                                onChange={handleChange}
                                placeholder="Mobile App"
                                required
                            />

                        </div>


                        <div className="form-row">

                            <div className="form-group">

                                <label htmlFor="tier">
                                    Tier
                                </label>

                                <select
                                    id="tier"
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

                                <label htmlFor="algorithm">
                                    Algorithm
                                </label>

                                <select
                                    id="algorithm"
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

                                <label htmlFor="limit">
                                    Request Limit
                                </label>

                                <input
                                    id="limit"
                                    name="limit"
                                    type="number"
                                    min="1"
                                    value={form.limit}
                                    onChange={handleChange}
                                    required
                                />

                            </div>


                            <div className="form-group">

                                <label htmlFor="windowSeconds">
                                    Window
                                </label>

                                <input
                                    id="windowSeconds"
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

                                <label htmlFor="scope">
                                    Scope
                                </label>

                                <select
                                    id="scope"
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

                                    {/* <option value="ip">
                                        IP
                                    </option>

                                    <option value="user">
                                        User
                                    </option> */}
                                </select>

                            </div>


                            <div className="form-group">

                                <label htmlFor="endpoint">
                                    Endpoint
                                </label>

                                <input
                                    id="endpoint"
                                    name="endpoint"
                                    value={form.endpoint}
                                    onChange={handleChange}
                                    placeholder="/api/data"
                                />

                            </div>

                        </div>


                        {error && (
                            <div className="error-message">
                                {error}
                            </div>
                        )}


                        <button
                            className="primary-button"
                            type="submit"
                            disabled={loading}
                        >
                            {loading
                                ? "Creating..."
                                : "Create API Key"
                            }
                        </button>

                    </form>

                </section>


                {/* CREATED KEY */}

                {createdKey && (

                    <section className="panel success-panel">

                        <div className="success-icon">
                            ✓
                        </div>

                        <h2>API Key Created</h2>

                        <p>
                            Your API key has been created
                            successfully.
                        </p>

                        <div className="key-display">

                            <span>
                                {createdKey.key}
                            </span>

                            <button
                                type="button"
                                onClick={() =>
                                    navigator.clipboard.writeText(
                                        createdKey.key
                                    )
                                }
                            >
                                Copy
                            </button>

                            <Link
                                to={`/api-keys/${encodeURIComponent(createdKey.key)}`}
                                className="secondary-button key-details-link"
                            >
                                Details
                            </Link>

                        </div>

                        <div className="created-details">

                            <div>
                                <span>Algorithm</span>
                                <strong>
                                    {createdKey.algorithm}
                                </strong>
                            </div>

                            <div>
                                <span>Limit</span>
                                <strong>
                                    {createdKey.limit}
                                </strong>
                            </div>

                            <div>
                                <span>Window</span>
                                <strong>
                                    {createdKey.windowSeconds}s
                                </strong>
                            </div>

                        </div>

                    </section>

                )}


                {/* LOOKUP */}

                <section className="panel lookup-panel">

                    <div className="panel-header">

                        <div>
                            <h2>Find API Key</h2>

                            <p>
                                Look up an existing API key
                                by its credential.
                            </p>
                        </div>

                    </div>


                    <form
                        className="lookup-form"
                        onSubmit={handleLookup}
                    >

                        <input
                            value={lookupKey}
                            onChange={(event) =>
                                setLookupKey(event.target.value)
                            }
                            placeholder="Paste API key"
                        />

                        <button
                            className="secondary-button"
                            type="submit"
                            disabled={lookupLoading}
                        >
                            {lookupLoading
                                ? "Loading..."
                                : "Lookup"
                            }
                        </button>

                    </form>


                    {lookupResult && (

                        <div className="lookup-result">

                            <div className="detail-row">
                                <span>Name</span>
                                <strong>
                                    {lookupResult.rule.name}
                                </strong>
                            </div>

                            <div className="detail-row">
                                <span>Tier</span>
                                <strong>
                                    {lookupResult.rule.tier}
                                </strong>
                            </div>

                            <div className="detail-row">
                                <span>Algorithm</span>
                                <strong>
                                    {lookupResult.rule.algorithm}
                                </strong>
                            </div>

                            <div className="detail-row">
                                <span>Limit</span>
                                <strong>
                                    {lookupResult.rule.limit}
                                </strong>
                            </div>

                            <div className="detail-row">
                                <span>Window</span>
                                <strong>
                                    {lookupResult.rule.windowSeconds}s
                                </strong>
                            </div>

                            <div className="detail-row">
                                <span>Scope</span>
                                <strong>
                                    {lookupResult.rule.scope}
                                </strong>
                            </div>

                            <div className="detail-row">
                                <span>Endpoint</span>
                                <strong>
                                    {lookupResult.rule.endpoint || "—"}
                                </strong>
                            </div>

                            <div className="detail-row">
                                <span>Usage</span>
                                <strong>
                                    Analytics coming in Phase 5
                                </strong>
                            </div>

                        </div>

                    )}

                </section>

            </div>

        </div>
    );
}

export default ApiKeys;