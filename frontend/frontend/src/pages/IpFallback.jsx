import { useEffect, useState } from "react";

import {
    getIpFallbackRule,
    updateIpFallbackRule,
} from "../api/ipFallbackApi";

function IpFallback() {

    const [form, setForm] = useState({
        enabled: false,
        algorithm: "fixed_window",
        limit: 60,
        windowSeconds: 60,
    });

    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");

    useEffect(() => {

        const loadRule = async () => {

            setLoading(true);
            setError("");

            try {

                const response = await getIpFallbackRule();

                const rule = response.data.rule || response.data;

                setForm({
                    enabled: rule.enabled ?? false,
                    algorithm:
                        rule.algorithm || "fixed_window",
                    limit: rule.limit || 60,
                    windowSeconds:
                        rule.windowSeconds || 60,
                });

            } catch (error) {

                console.error(
                    "Failed to load IP fallback rule:",
                    error
                );

                setError(
                    error.response?.data?.detail ||
                    "Failed to load IP fallback configuration."
                );

            } finally {

                setLoading(false);

            }
        };

        loadRule();

    }, []);


    const handleChange = (event) => {

        const { name, value, type, checked } = event.target;

        setForm((previous) => ({
            ...previous,

            [name]:
                type === "checkbox"
                    ? checked
                    : name === "limit" ||
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

            const response =
                await updateIpFallbackRule(form);

            const rule =
                response.data.rule || response.data;

            setForm({
                enabled: rule.enabled ?? form.enabled,
                algorithm:
                    rule.algorithm || form.algorithm,
                limit:
                    rule.limit ?? form.limit,
                windowSeconds:
                    rule.windowSeconds ??
                    form.windowSeconds,
            });

            setSuccess(
                "IP fallback configuration saved successfully."
            );

        } catch (error) {

            console.error(
                "Failed to save IP fallback rule:",
                error
            );

            setError(
                error.response?.data?.detail ||
                "Failed to save IP fallback configuration."
            );

        } finally {

            setSaving(false);

        }
    };


    if (loading) {

        return (
            <div className="ip-fallback-page">

                <div className="loading-state">
                    Loading IP fallback configuration...
                </div>

            </div>
        );

    }


    return (
        <div className="ip-fallback-page">

            <div className="page-heading">

                <div>

                    <h1>IP Fallback</h1>

                    <p>
                        Configure rate limiting for requests
                        that do not provide an API key.
                    </p>

                </div>

                <div
                    className={`fallback-status ${
                        form.enabled
                            ? "enabled"
                            : "disabled"
                    }`}
                >

                    <span className="status-dot"></span>

                    {form.enabled
                        ? "Enabled"
                        : "Disabled"}

                </div>

            </div>


            <div className="ip-fallback-grid">

                {/* CONFIGURATION */}

                <section className="panel">

                    <div className="panel-header">

                        <h2>Fallback Configuration</h2>

                        <p>
                            Requests without an API key can
                            be limited using their IP address.
                        </p>

                    </div>


                    <form
                        className="api-form"
                        onSubmit={handleSave}
                    >

                        <div className="fallback-toggle">

                            <div>

                                <strong>
                                    Enable IP fallback
                                </strong>

                                <span>
                                    Apply a rate limit to
                                    unidentified clients.
                                </span>

                            </div>

                            <label className="toggle">

                                <input
                                    type="checkbox"
                                    name="enabled"
                                    checked={form.enabled}
                                    onChange={handleChange}
                                />

                                <span className="toggle-slider"></span>

                            </label>

                        </div>


                        <div className="form-group">

                            <label htmlFor="fallback-algorithm">
                                Algorithm
                            </label>

                            <select
                                id="fallback-algorithm"
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


                        <div className="form-row">

                            <div className="form-group">

                                <label htmlFor="fallback-limit">
                                    Request Limit
                                </label>

                                <input
                                    id="fallback-limit"
                                    name="limit"
                                    type="number"
                                    min="1"
                                    value={form.limit}
                                    onChange={handleChange}
                                    required
                                />

                            </div>


                            <div className="form-group">

                                <label htmlFor="fallback-window">
                                    Window
                                </label>

                                <input
                                    id="fallback-window"
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
                                : "Save Configuration"
                            }
                        </button>

                    </form>

                </section>


                {/* HOW IT WORKS */}

                <section className="panel">

                    <div className="panel-header">

                        <h2>How It Works</h2>

                        <p>
                            IP fallback is used when the
                            request doesn't identify itself
                            with an API key.
                        </p>

                    </div>


                    <div className="fallback-flow">

                        <div className="flow-step">

                            <div className="flow-number">
                                1
                            </div>

                            <div>

                                <strong>
                                    Incoming request
                                </strong>

                                <span>
                                    Client calls the API.
                                </span>

                            </div>

                        </div>


                        <div className="flow-line"></div>


                        <div className="flow-step">

                            <div className="flow-number">
                                2
                            </div>

                            <div>

                                <strong>
                                    API key check
                                </strong>

                                <span>
                                    No API key is provided.
                                </span>

                            </div>

                        </div>


                        <div className="flow-line"></div>


                        <div className="flow-step">

                            <div className="flow-number">
                                3
                            </div>

                            <div>

                                <strong>
                                    IP identification
                                </strong>

                                <span>
                                    Client is identified by IP.
                                </span>

                            </div>

                        </div>


                        <div className="flow-line"></div>


                        <div className="flow-step">

                            <div className="flow-number">
                                4
                            </div>

                            <div>

                                <strong>
                                    Rate limit
                                </strong>

                                <span>
                                    The fallback rule is applied.
                                </span>

                            </div>

                        </div>

                    </div>

                </section>

            </div>


            {/* CURRENT RULE */}

            <section className="panel current-fallback-panel">

                <div className="panel-header">

                    <h2>Current Rule</h2>

                    <p>
                        The configuration currently applied
                        to IP fallback requests.
                    </p>

                </div>


                <div className="fallback-stats">

                    <div className="fallback-stat">

                        <span>Status</span>

                        <strong>
                            {form.enabled
                                ? "Enabled"
                                : "Disabled"}
                        </strong>

                    </div>


                    <div className="fallback-stat">

                        <span>Algorithm</span>

                        <strong>
                            {form.algorithm}
                        </strong>

                    </div>


                    <div className="fallback-stat">

                        <span>Limit</span>

                        <strong>
                            {form.limit}
                        </strong>

                    </div>


                    <div className="fallback-stat">

                        <span>Window</span>

                        <strong>
                            {form.windowSeconds}s
                        </strong>

                    </div>

                </div>

            </section>

        </div>
    );
}

export default IpFallback;