import { NavLink } from "react-router-dom";

function Sidebar() {

    const navItems = [
        {
            name: "Dashboard",
            path: "/",
        },
        {
            name: "API Keys",
            path: "/api-keys",
        },
        {
            name: "Playground",
            path: "/playground",
        },
        {
            name: "IP Fallback",
            path: "/ip-fallback",
        },
    ];

    return (
        <aside className="sidebar">

            <div className="sidebar-brand">
                <div className="brand-icon">
                    ⚡
                </div>

                <div>
                    <h2>Gatekeeper</h2>
                    <span>Rate Limiter</span>
                </div>
            </div>

            <nav className="sidebar-nav">

                <div className="nav-section-title">
                    MANAGEMENT
                </div>

                {navItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) =>
                            `nav-item ${isActive ? "active" : ""}`
                        }
                    >
                        {item.name}
                    </NavLink>
                ))}

            </nav>

            <div className="sidebar-footer">
                <div className="system-status">
                    <span className="status-dot"></span>

                    <div>
                        <strong>System</strong>
                        <span>Operational</span>
                    </div>
                </div>
            </div>

        </aside>
    );
}

export default Sidebar;