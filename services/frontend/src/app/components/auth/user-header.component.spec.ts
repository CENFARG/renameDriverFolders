import { describe, it, expect, vi, beforeEach } from 'vitest';
import { UserHeaderComponent } from './user-header.component';
import { AuthService } from '../../services/auth.service';
import { Subject } from 'rxjs';

describe('UserHeaderComponent', () => {
  let component: UserHeaderComponent;
  let authService: any;

  beforeEach(() => {
    authService = {
      user$: new Subject(),
      signOut: vi.fn(),
    };
    component = new UserHeaderComponent(authService, { detectChanges: vi.fn() } as any);
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should call signOut on AuthService', () => {
    component.signOut();
    expect(authService.signOut).toHaveBeenCalled();
  });

  it('should toggle theme', () => {
    component.isDark = true;
    component.toggleTheme();
    expect(component.isDark).toBe(false);
    expect(localStorage.getItem('theme')).toBe('light');
  });
});
