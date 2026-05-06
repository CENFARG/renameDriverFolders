import { describe, it, expect, vi, beforeEach } from 'vitest';
import { SettingsComponent } from './settings.component';
import { AuthService } from '../../services/auth.service';

describe('SettingsComponent', () => {
  let component: SettingsComponent;
  let authService: any;

  beforeEach(() => {
    authService = {
      isAuthenticated: vi.fn().mockReturnValue(true),
      getToken: vi.fn().mockReturnValue('token123'),
    };
    component = new SettingsComponent(authService, { detectChanges: vi.fn() } as any);
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should report authenticated status', () => {
    expect(component.isAuthenticated).toBe(true);
  });

  it('should report token availability', () => {
    expect(component.hasToken).toBe(true);
  });
});
