import { describe, it, expect, vi, beforeEach } from 'vitest';
import { DashboardComponent } from './dashboard.component';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { Subject } from 'rxjs';

describe('DashboardComponent', () => {
  let component: DashboardComponent;
  let apiService: any;
  let authService: any;

  beforeEach(() => {
    apiService = {
      submitJob: vi.fn().mockReturnValue(new Subject()),
    };
    authService = {
      getToken: vi.fn().mockReturnValue('test-token'),
    };
    component = new DashboardComponent(apiService, authService, { detectChanges: vi.fn() } as any);
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should not submit without folderId', () => {
    component.folderId = '';
    component.submitJob();
    expect(apiService.submitJob).not.toHaveBeenCalled();
  });

  it('should submit with folderId', () => {
    component.folderId = 'folder123';
    component.submitJob();
    expect(apiService.submitJob).toHaveBeenCalledWith(
      { folder_id: 'folder123', job_type: 'auto-classify' },
      'test-token',
    );
  });

  it('should show loading state while submitting', () => {
    component.folderId = 'folder123';
    component.submitJob();
    expect(component.isSubmitting).toBe(true);
  });
});
