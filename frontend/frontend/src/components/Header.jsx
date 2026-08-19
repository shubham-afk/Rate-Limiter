import { useEffect, useState } from "react";

import { getHealth } from "../api/healthApi";

function Header() {

    const [isConnected, setIsConnected] = useState(false);
    const [isChecking, setIsChecking] = useState(true);

    useEffect(() => {

        const checkBackend = async () => {

            try {

                await getHealth();

                setIsConnected(true);

            } catch (error) {

                console.error("Backend health check failed:", error);

                setIsConnected(false);

            } finally {

                setIsChecking(false);

            }
        };

        checkBackend();

    }, []);

    return (
        <header className="header">

            <div>
                <span className="header-label">
                    ADMIN CONSOLE
                </span>

                <h1>Rate Limiter</h1>
            </div>

            <div className="header-right">

                <div className="connection-status">

                    <span
                        className={`status-dot ${
                            isConnected ? "connected" : "disconnected"
                        }`}
                    ></span>

                    {isChecking
                        ? "Checking backend..."
                        : isConnected
                            ? "Backend Connected"
                            : "Backend Unavailable"
                    }

                </div>

                <div className="admin-avatar">
                    A
                </div>

            </div>

        </header>
    );
}

export default Header;