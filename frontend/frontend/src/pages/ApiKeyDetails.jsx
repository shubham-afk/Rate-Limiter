import { useParams } from "react-router-dom";

function ApiKeyDetails() {
    const { key } = useParams();

    return (
        <div>
            <h1>API Key Details</h1>

            <p>
                API Key: <strong>{key}</strong>
            </p>
        </div>
    );
}

export default ApiKeyDetails;