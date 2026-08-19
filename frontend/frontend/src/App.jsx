import {
    BrowserRouter,
    Routes,
    Route
} from "react-router-dom";

import Layout from "./components/Layout";

import Dashboard from "./pages/Dashboard";
import ApiKeys from "./pages/ApiKeys";
import ApiKeyDetails from "./pages/ApiKeyDetails";
import Playground from "./pages/Playground";
import IpFallback from "./pages/IpFallback";

function App() {

    return (
        <BrowserRouter>

            <Routes>

                <Route element={<Layout />}>

                    <Route
                        path="/"
                        element={<Dashboard />}
                    />

                    <Route
                        path="/api-keys"
                        element={<ApiKeys />}
                    />

                    <Route
                        path="/api-keys/:key"
                        element={<ApiKeyDetails />}
                    />

                    <Route
                        path="/playground"
                        element={<Playground />}
                    />

                    <Route
                        path="/ip-fallback"
                        element={<IpFallback />}
                    />

                </Route>

            </Routes>

        </BrowserRouter>
    );
}

export default App;