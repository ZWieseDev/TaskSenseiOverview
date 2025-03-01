document.addEventListener("DOMContentLoaded", async function () {
    // Extract authorization code from URL
    const urlParams = new URLSearchParams(window.location.search);
    const authorizationCode = urlParams.get("code");

    if (!authorizationCode) {
        return;
    }

    // Generate PKCE Code Verifier & Challenge
    const codeVerifier = generateRandomString(128);
    const codeChallenge = await sha256(codeVerifier);

    // Store values for future use
    localStorage.setItem("code_verifier", codeVerifier);
    localStorage.setItem("code_challenge", codeChallenge);

    // API Endpoint (Placeholder for security)
    const authUrl = "<AUTH_API_ENDPOINT>";

    try {
        const requestOptions = {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Origin": window.location.origin,
            },
            body: JSON.stringify({
                authorization_code: authorizationCode,
                code_verifier: codeVerifier
            }),
            credentials: "include" 
        };

        const response = await fetch(authUrl, requestOptions);
        const data = await response.json();

        // Store refresh token as a normal cookie
        if (data.refresh_token) {
            document.cookie = `refresh_token=${data.refresh_token}; path=/; max-age=2592000; SameSite=None; Secure`;
            document.cookie = `has_refresh_token=true; path=/; max-age=2592000; SameSite=None; Secure`;
        }

        // Store Access Token in sessionStorage
        if (data.access_token) {
            sessionStorage.setItem("access_token", data.access_token);
        }

        // Store username as a cookie
        if (data.user_id) {
            document.cookie = `username=${data.user_id}; path=/; max-age=2592000; SameSite=None; Secure`;
        }

        // Redirect to dashboard
        setTimeout(() => {
            window.location.href = "<DASHBOARD_URL>";
        }, 3000);
    } catch (error) {
        alert("Authentication failed. Please try again.");
    }
});

// Function to generate a random string (PKCE Code Verifier)
function generateRandomString(length) {
    const possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~";
    let randomString = "";
    const randomValues = new Uint8Array(length);
    window.crypto.getRandomValues(randomValues);
    randomValues.forEach(value => {
        randomString += possible.charAt(value % possible.length);
    });
    return randomString;
}

// Function to hash the code verifier for PKCE
async function sha256(plain) {
    const encoder = new TextEncoder();
    const data = encoder.encode(plain);
    const hash = await crypto.subtle.digest('SHA-256', data);
    return btoa(String.fromCharCode(...new Uint8Array(hash)))
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=+$/, '');
}
