import { useState } from "react";

import { checkRateLimit } from "../api/playgroundApi";

function Playground() {

    const [apiKey, setApiKey] = useState("");
    const [endpoint, setEndpoint] = useState("/api/data");

    const [result, setResult] = useState(null);

    const [history, setHistory] = useState([]);

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const handleCheck = async () => {

        if (!apiKey.trim()) {
            setError("Please enter an API key.");
            return;
        }

        setLoading(true);
        setError("");

        const requestNumber = history.length + 1;
        const timestamp = new Date();

        try {

            const response = await checkRateLimit(
                apiKey.trim(),
                endpoint
            );

            const data = response.data;

            setResult(data);

            setHistory((previous) => [
                ...previous,
                {
                    id: requestNumber,
                    timestamp,
                    allowed: data.allowed,
                    remaining: data.remaining,
                    resetAt: data.resetAt,
                },
            ]);

        } catch (error) {

            console.error(
                "Rate-limit check failed:",
                error
            );

            /*
             * 429 is an expected response when the
             * rate limit has been exceeded.
             */

            if (error.response?.status === 429) {

                const data = error.response.data;

                setResult(data);

                setHistory((previous) => [
                    ...previous,
                    {
                        id: requestNumber,
                        timestamp,
                        allowed: false,
                        remaining: data.remaining,
                        resetAt: data.resetAt,
                    },
                ]);

            } else {

                setError(
                    error.response?.data?.detail ||
                    "Failed to check rate limit."
                );

            }

        } finally {

            setLoading(false);

        }
    };


    const resetPlayground = () => {

        setResult(null);
        setHistory([]);
        setError("");

    };


    const formatTime = (timestamp) => {

        return timestamp.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
        });

    };


    const formatResetTime = (resetAt) => {

        if (!resetAt) {
            return "—";
        }

        return new Date(
            resetAt * 1000
        ).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
        });

    };


    return (
        <div className="playground-page">

            {/* PAGE HEADER */}

            <div className="page-heading">

                <div>

                    <h1>Rate Limit Playground</h1>

                    <p>
                        Send requests through the rate limiter
                        and inspect each decision.
                    </p>

                </div>

            </div>


            <div className="playground-grid">

                {/* REQUEST PANEL */}

                <section className="panel">

                    <div className="panel-header">

                        <h2>Test Request</h2>

                        <p>
                            Use an API key created from the
                            API Keys page.
                        </p>

                    </div>


                    <div className="playground-form">

                        <div className="form-group">

                            <label htmlFor="playground-api-key">
                                API Key
                            </label>

                            <input
                                id="playground-api-key"
                                type="text"
                                value={apiKey}
                                onChange={(event) =>
                                    setApiKey(event.target.value)
                                }
                                placeholder="Paste your API key"
                            />

                        </div>


                        <div className="form-group">

                            <label htmlFor="playground-endpoint">
                                Endpoint
                            </label>

                            <input
                                id="playground-endpoint"
                                type="text"
                                value={endpoint}
                                onChange={(event) =>
                                    setEndpoint(event.target.value)
                                }
                                placeholder="/api/data"
                            />

                        </div>


                        {error && (

                            <div className="error-message">
                                {error}
                            </div>

                        )}


                        <div className="playground-actions">

                            <button
                                className="primary-button"
                                onClick={handleCheck}
                                disabled={loading}
                            >
                                {loading
                                    ? "Sending..."
                                    : "Send Request"
                                }
                            </button>


                            <button
                                className="secondary-button"
                                onClick={resetPlayground}
                                type="button"
                            >
                                Clear
                            </button>

                        </div>

                    </div>

                </section>


                {/* CURRENT DECISION */}

                <section className="panel result-panel">

                    <div className="panel-header">

                        <h2>Latest Decision</h2>

                        <p>
                            Result from the most recent request.
                        </p>

                    </div>


                    {!result && (

                        <div className="empty-result">

                            <div className="empty-icon">
                                →
                            </div>

                            <p>
                                Send a request to see the
                                rate-limit decision.
                            </p>

                        </div>

                    )}


                    {result && (

                        <div
                            className={`decision-card ${
                                result.allowed
                                    ? "allowed"
                                    : "blocked"
                            }`}
                        >

                            <div className="decision-header">

                                <div>

                                    <span className="decision-label">
                                        REQUEST
                                    </span>

                                    <h3>
                                        {result.allowed
                                            ? "Allowed"
                                            : "Rate Limited"
                                        }
                                    </h3>

                                </div>


                                <div className="decision-icon">

                                    {result.allowed
                                        ? "✓"
                                        : "×"
                                    }

                                </div>

                            </div>


                            <div className="decision-stats">

                                <div className="stat">

                                    <span>
                                        Remaining
                                    </span>

                                    <strong>
                                        {result.remaining}
                                    </strong>

                                </div>


                                <div className="stat">

                                    <span>
                                        Reset At
                                    </span>

                                    <strong>
                                        {formatResetTime(
                                            result.resetAt
                                        )}
                                    </strong>

                                </div>

                            </div>

                        </div>

                    )}

                </section>


                {/* REQUEST HISTORY */}

                <section className="panel history-panel">

                    <div className="panel-header history-header">

                        <div>

                            <h2>Request History</h2>

                            <p>
                                Requests sent during this
                                playground session.
                            </p>

                        </div>

                        {history.length > 0 && (

                            <span className="request-count">
                                {history.length} request
                                {history.length !== 1 ? "s" : ""}
                            </span>

                        )}

                    </div>


                    {history.length === 0 ? (

                        <div className="history-empty">

                            <p>
                                No requests yet.
                            </p>

                        </div>

                    ) : (

                        <div className="history-table">

                            <div className="history-row history-table-header">

                                <span>#</span>
                                <span>Time</span>
                                <span>Status</span>
                                <span>Remaining</span>
                                <span>Reset</span>

                            </div>


                            {[...history]
                                .reverse()
                                .map((request) => (

                                    <div
                                        className="history-row"
                                        key={request.id}
                                    >

                                        <span className="request-number">
                                            #{request.id}
                                        </span>

                                        <span className="request-time">
                                            {formatTime(
                                                request.timestamp
                                            )}
                                        </span>

                                        <span>

                                            <span
                                                className={`request-status ${
                                                    request.allowed
                                                        ? "status-allowed"
                                                        : "status-blocked"
                                                }`}
                                            >

                                                <span className="mini-dot"></span>

                                                {request.allowed
                                                    ? "Allowed"
                                                    : "Rate Limited"
                                                }

                                            </span>

                                        </span>

                                        <span className="remaining-value">
                                            {request.remaining}
                                        </span>

                                        <span className="reset-value">
                                            {formatResetTime(
                                                request.resetAt
                                            )}
                                        </span>

                                    </div>

                                ))}

                        </div>

                    )}

                </section>

            </div>

        </div>
    );
}

export default Playground;