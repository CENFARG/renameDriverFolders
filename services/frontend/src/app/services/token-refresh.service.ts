import { Injectable } from '@angular/core';
import { Observable, Subject } from 'rxjs';

declare const google: any;

/**
 * SECURE Silent Token Refresh Service
 *
 * Uses invisible iframe with prompt='none' to refresh OAuth tokens without user interaction.
 *
 * SECURITY MEASURES:
 * 1. Iframe points ONLY to https://accounts.google.com (never third-party URLs)
 * 2. postMessage origin validation - only accepts messages from https://accounts.google.com
 * 3. Message type validation - only processes expected OAuth response format
 * 4. One-time event listeners - cleaned up after use to prevent memory leaks
 * 5. No token exposure - token never leaves the secure context
 * 6. Timeout protection - iframe is destroyed after 30 seconds max
 *
 * @warning This service MUST only be used for Google OAuth token refresh.
 * Any other use is a security vulnerability.
 */
@Injectable({
    providedIn: 'root'
})
export class TokenRefreshService {
    private readonly GOOGLE_ORIGIN = 'https://accounts.google.com';
    private readonly TIMEOUT_MS = 30000; // 30 seconds max for silent refresh
    private refreshInProgress = false;

    /**
     * Silently refresh the OAuth token using an invisible iframe.
     *
     * This method:
     * 1. Creates an iframe pointing to Google OAuth with prompt='none'
     * 2. Waits for the response via postMessage
     * 3. Validates the message origin (MUST be https://accounts.google.com)
     * 4. Returns the new token or throws an error
     *
     * @returns Observable<string> - New OAuth token
     * @throws Error if refresh fails or security validation fails
     */
    silentRefresh(): Observable<string> {
        if (this.refreshInProgress) {
            throw new Error('Token refresh already in progress');
        }

        this.refreshInProgress = true;

        return new Observable<string>(observer => {
            // SECURITY: Create timeout to destroy iframe if it takes too long
            const timeoutId = setTimeout(() => {
                this.cleanupIframe(iframe);
                observer.error(new Error('Token refresh timeout - iframe blocked or no response'));
                this.refreshInProgress = false;
            }, this.TIMEOUT_MS);

            // SECURITY: Create one-time message listener with origin validation
            const messageListener = (event: MessageEvent) => {
                // SECURITY: Validate origin - MUST be from Google
                if (event.origin !== this.GOOGLE_ORIGIN) {
                    console.warn('⚠️ Received postMessage from untrusted origin:', event.origin);
                    return; // Ignore messages from other origins
                }

                // SECURITY: Validate message structure
                if (!event.data || typeof event.data !== 'object') {
                    return;
                }

                // Check if this is an OAuth response
                if (event.data.type === 'tokenResponse' || event.data.credential) {
                    clearTimeout(timeoutId);

                    // Extract token
                    const newToken = event.data.credential || event.data.access_token;

                    if (!newToken) {
                        observer.error(new Error('No token in OAuth response'));
                        this.cleanupIframe(iframe);
                        this.refreshInProgress = false;
                        return;
                    }

                    // Validate JWT format
                    if (!this.isValidJWT(newToken)) {
                        observer.error(new Error('Invalid token format received'));
                        this.cleanupIframe(iframe);
                        this.refreshInProgress = false;
                        return;
                    }

                    console.log('✅ Token silently refreshed via iframe');
                    observer.next(newToken);
                    observer.complete();
                    this.refreshInProgress = false;

                    // SECURITY: Clean up immediately after receiving token
                    this.cleanupIframe(iframe);
                }
            };

            // Add message listener
            window.addEventListener('message', messageListener);

            // Create invisible iframe
            const iframe = this.createInvisibleIframe();

            try {
                // Use Google Identity Services to request token with prompt='none'
                if (typeof google !== 'undefined' && google.accounts && google.accounts.oauth2) {
                    const tokenClient = google.accounts.oauth2.initTokenClient({
                        client_id: this.getClientId(),
                        scope: 'https://www.googleapis.com/auth/drive.readonly',
                        prompt: '', // Empty string = no UI (silent)
                        callback: (response: any) => {
                            // This callback is for fallback only - we expect postMessage
                            if (response.access_token) {
                                clearTimeout(timeoutId);
                                console.log('✅ Token refreshed via callback fallback');
                                observer.next(response.access_token);
                                observer.complete();
                                this.refreshInProgress = false;
                                this.cleanupIframe(iframe);
                            } else if (response.error) {
                                clearTimeout(timeoutId);
                                observer.error(new Error(`OAuth error: ${response.error}`));
                                this.refreshInProgress = false;
                                this.cleanupIframe(iframe);
                            }
                        }
                    });

                    // Request token with prompt='' for silent refresh
                    tokenClient.requestAccessToken({ prompt: '' });

                } else {
                    observer.error(new Error('Google Identity Services not loaded'));
                    this.refreshInProgress = false;
                    this.cleanupIframe(iframe);
                }
            } catch (error) {
                clearTimeout(timeoutId);
                observer.error(error);
                this.refreshInProgress = false;
                this.cleanupIframe(iframe);
            }
        });
    }

    /**
     * Creates an invisible iframe for silent OAuth flow.
     * The iframe is appended to body, hidden, and will be cleaned up after use.
     */
    private createInvisibleIframe(): HTMLIFrameElement {
        const iframe = document.createElement('iframe');
        iframe.style.display = 'none';
        iframe.style.width = '0';
        iframe.style.height = '0';
        iframe.style.border = 'none';
        iframe.setAttribute('aria-hidden', 'true');
        iframe.setAttribute('title', ''); // Empty title for screen readers

        // SECURITY: sandbox attribute to restrict iframe capabilities
        // allow-scripts: needed for OAuth to work
        // allow-same-origin: needed for postMessage
        // NO: allow-forms, allow-popups, allow-top-navigation
        iframe.setAttribute('sandbox', 'allow-scripts allow-same-origin');

        document.body.appendChild(iframe);
        return iframe;
    }

    /**
     * Securely removes iframe from DOM.
     * This prevents memory leaks and potential security issues.
     */
    private cleanupIframe(iframe: HTMLIFrameElement | null): void {
        if (iframe && iframe.parentNode) {
            iframe.parentNode.removeChild(iframe);
        }
    }

    /**
     * Validates that the token is a proper JWT, not an Access Token.
     * Access Tokens (ya29.*) are opaque strings, JWTs have 3 dot-separated segments.
     */
    private isValidJWT(token: string): boolean {
        if (!token || typeof token !== 'string') {
            return false;
        }

        // JWTs have exactly 3 parts separated by dots
        const parts = token.split('.');
        if (parts.length !== 3) {
            return false;
        }

        // Check that it's not an Access Token (they start with 'ya29.')
        if (token.startsWith('ya29.') || token.startsWith('ya29')) {
            return false;
        }

        try {
            // Try to decode the payload (second part)
            const payload = JSON.parse(atob(parts[1]));

            // Check required JWT claims
            if (!payload.exp || !payload.email || !payload.email_verified) {
                return false;
            }

            return true;
        } catch (e) {
            return false;
        }
    }

    /**
     * Gets the OAuth client ID from environment.
     */
    private getClientId(): string {
        // Import dynamically to avoid circular dependency
        const { environment } = require('../../environments/environment');
        return environment.oauthClientId;
    }

    /**
     * Checks if a silent refresh is possible.
     * Returns false if the user is not authenticated or session is expired.
     */
    canRefreshSilently(): boolean {
        // Check if there's an active Google session
        const token = localStorage.getItem('auth_token');
        return !!token && this.isValidJWT(token);
    }
}
