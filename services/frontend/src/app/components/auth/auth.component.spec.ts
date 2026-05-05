import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AuthComponent } from './auth.component';
import { AuthService } from '../../services/auth.service';
import { Subject } from 'rxjs';

describe('AuthComponent', () => {
  let component: AuthComponent;
  let authService: any;

  beforeEach(() => {
    authService = {
      user$: new Subject(),
      initializeGoogleSignIn: vi.fn(),
      renderButton: vi.fn(),
    };
    component = new AuthComponent(authService, { detectChanges: vi.fn() } as any);
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize Google Sign-In on init', () => {
    component.ngOnInit();
    expect(authService.initializeGoogleSignIn).toHaveBeenCalled();
  });
});
