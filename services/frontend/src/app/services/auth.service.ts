import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
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

    constructor() {
        this.loadUserFromStorage();
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
