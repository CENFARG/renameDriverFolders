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
    private tokenExpiryKey = 'auth_token_expiry';
    private sessionTimeoutKey = 'session_last_activity';
    private readonly SESSION_DURATION = 60 * 60 * 1000; // 1 hora en ms
    private readonly WARNING_THRESHOLD = 5 * 60 * 1000; // 5 minutos en ms
    private refreshTimer: any;

    constructor(private http: HttpClient) {
        this.loadUserFromStorage();
        this.checkIapAuth();
        this.initializeSessionMonitoring();
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
                callback: this.handleCredentialResponse.bind(this),
                // Auto-select account if user has one active session
                auto_select: true,
                // Use approved login hint to avoid re-login
                login_hint: this.getLoginHint()
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

        // Decode JWT to get user info and expiry
        const payload = JSON.parse(atob(token.split('.')[1]));
        const user: User = {
            email: payload.email,
            name: payload.name,
            picture: payload.picture
        };

        this.userSubject.next(user);
        localStorage.setItem('user', JSON.stringify(user));

        // Guardar login hint para auto-select en el futuro
        localStorage.setItem('login_hint', payload.email);

        // Calcular expiración del token (Google tokens duran 1 hora)
        const exp = payload.exp * 1000; // Convertir a ms
        localStorage.setItem(this.tokenExpiryKey, exp.toString());

        // Actualizar actividad de sesión
        this.updateSessionActivity();
    }

    private loadUserFromStorage(): void {
        const userStr = localStorage.getItem('user');
        const token = this.getToken();

        if (userStr && token) {
            // Verificar si el token expiró
            if (this.isTokenExpired()) {
                console.log('⚠️ Token expired, clearing session');
                this.clearSession();
                return;
            }

            // Verificar si la sesión expiró por inactividad
            if (this.isSessionExpired()) {
                console.log('⚠️ Session expired by inactivity');
                this.clearSession();
                return;
            }

            try {
                const user = JSON.parse(userStr);
                this.userSubject.next(user);
                // Iniciar monitoreo de sesión
                this.initializeSessionMonitoring();
            } catch (e) {
                console.error('Error loading user from storage', e);
            }
        }
    }

    setToken(token: string): void {
        localStorage.setItem(this.tokenKey, token);
    }

    getToken(): string | null {
        // Verificar expiración antes de retornar el token
        if (this.isTokenExpired()) {
            console.log('⚠️ Token expired, clearing session');
            this.clearSession();
            return null;
        }
        return localStorage.getItem(this.tokenKey);
    }

    isAuthenticated(): boolean {
        const token = this.getToken();
        return token !== null && !this.isTokenExpired() && !this.isSessionExpired();
    }

    private isTokenExpired(): boolean {
        const expiryStr = localStorage.getItem(this.tokenExpiryKey);
        if (!expiryStr) return false; // No hay expiración guardada, asumir válido

        const expiry = parseInt(expiryStr, 10);
        const now = Date.now();

        // Token expiró si el tiempo actual es mayor que la expiración menos el threshold
        // Esto da 5 minutos de margen para refresh
        return now > (expiry - this.WARNING_THRESHOLD);
    }

    private isSessionExpired(): boolean {
        const lastActivityStr = localStorage.getItem(this.sessionTimeoutKey);
        if (!lastActivityStr) return false;

        const lastActivity = parseInt(lastActivityStr, 10);
        const now = Date.now();

        // Sesión expiró si pasaron más de SESSION_DURATION desde la última actividad
        return (now - lastActivity) > this.SESSION_DURATION;
    }

    private updateSessionActivity(): void {
        localStorage.setItem(this.sessionTimeoutKey, Date.now().toString());
    }

    private initializeSessionMonitoring(): void {
        // Actualizar actividad en cada interacción del usuario
        if (typeof window !== 'undefined') {
            ['click', 'keypress', 'scroll', 'mousemove'].forEach(event => {
                window.addEventListener(event, () => this.updateSessionActivity());
            });
        }

        // Verificar expiración cada minuto
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }

        this.refreshTimer = setInterval(() => {
            if (this.isAuthenticated()) {
                this.updateSessionActivity();
            } else if (this.getToken()) {
                // Token existe pero expiró
                console.log('⚠️ Session expired, user needs to re-login');
                this.clearSession();
                this.userSubject.next(null);
            }
        }, 60000); // Cada minuto
    }

    private getLoginHint(): string | null {
        return localStorage.getItem('login_hint');
    }

    private clearSession(): void {
        localStorage.removeItem(this.tokenKey);
        localStorage.removeItem(this.tokenExpiryKey);
        localStorage.removeItem(this.sessionTimeoutKey);
        localStorage.removeItem('user');
        localStorage.removeItem('login_hint');
        localStorage.removeItem('auth_type');
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }
    }

    signOut(): void {
        this.clearSession();
        this.userSubject.next(null);
        if (typeof google !== 'undefined') {
            google.accounts.id.disableAutoSelect();
        }
    }

    getCurrentUser(): User | null {
        return this.userSubject.value;
    }

    // Obtener tiempo restante de sesión en minutos
    getSessionTimeRemaining(): number {
        const expiryStr = localStorage.getItem(this.tokenExpiryKey);
        if (!expiryStr) return 0;

        const expiry = parseInt(expiryStr, 10);
        const now = Date.now();
        const remaining = Math.max(0, expiry - now);

        return Math.floor(remaining / (60 * 1000)); // Retornar en minutos
    }
}
