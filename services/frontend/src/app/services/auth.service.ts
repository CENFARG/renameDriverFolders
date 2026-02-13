import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, tap, catchError, of } from 'rxjs';
import { User } from '../models/job.model';
import { environment } from '../../environments/environment';

declare const google: any;

@Injectable({
    providedIn: 'root'
})
export class AuthService {
    private userSubject = new BehaviorSubject<User | null>(null);
    public user$: Observable<User | null> = this.userSubject.asObservable();
    private tokenKey = 'auth_token';

    constructor(private http: HttpClient) {
        this.loadUserFromStorage();
        this.checkIapAuth();
    }

    /**
     * Attempts to identify the user via IAP (Identity-Aware Proxy)
     * Useful when running in Google Cloud.
     */
    private checkIapAuth(): void {
        const url = `${environment.apiUrl}/api/v1/auth/whoami`;
        console.log('🔍 Checking IAP Auth:', url);

        this.http.get<any>(url).subscribe({
            next: (response) => {
                if (response.status === 'success' && response.authenticated && response.user) {
                    console.log('✅ IAP User Detected:', response.user.email);
                    const user: User = {
                        email: response.user.email,
                        name: response.user.name || response.user.email.split('@')[0],
                        picture: ''
                    };
                    this.userSubject.next(user);
                    localStorage.setItem('user', JSON.stringify(user));
                    localStorage.setItem('auth_type', 'iap');
                } else {
                    console.log('ℹ️ IAP Auth check: Not authenticated via proxy.');
                }
            },
            error: (err) => {
                console.log('ℹ️ IAP Auth check failed:', err.message);
            }
        });
    }

    initializeGoogleSignIn(): void {
        if (typeof google !== 'undefined') {
            google.accounts.id.initialize({
                client_id: environment.oauthClientId,
                callback: this.handleCredentialResponse.bind(this)
            });
        }
    }

    renderButton(element: HTMLElement): void {
        if (typeof google !== 'undefined') {
            google.accounts.id.renderButton(element, {
                theme: 'outline',
                size: 'large',
                text: 'signin_with',
                shape: 'rectangular'
            });
        }
    }

    private handleCredentialResponse(response: any): void {
        const token = response.credential;
        this.setToken(token);

        // Decode JWT to get user info
        const payload = JSON.parse(atob(token.split('.')[1]));
        const user: User = {
            email: payload.email,
            name: payload.name,
            picture: payload.picture
        };

        this.userSubject.next(user);
        localStorage.setItem('user', JSON.stringify(user));
    }

    private loadUserFromStorage(): void {
        const userStr = localStorage.getItem('user');
        if (userStr) {
            try {
                const user = JSON.parse(userStr);
                this.userSubject.next(user);
            } catch (e) {
                console.error('Error loading user from storage', e);
            }
        }
    }

    setToken(token: string): void {
        localStorage.setItem(this.tokenKey, token);
    }

    getToken(): string | null {
        return localStorage.getItem(this.tokenKey);
    }

    isAuthenticated(): boolean {
        return this.getToken() !== null;
    }

    signOut(): void {
        localStorage.removeItem(this.tokenKey);
        localStorage.removeItem('user');
        this.userSubject.next(null);
        if (typeof google !== 'undefined') {
            google.accounts.id.disableAutoSelect();
        }
    }

    getCurrentUser(): User | null {
        return this.userSubject.value;
    }
}
