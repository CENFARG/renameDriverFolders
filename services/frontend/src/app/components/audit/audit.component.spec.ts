import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AuditComponent } from './audit.component';
import { ApiService } from '../../services/api.service';
import { of } from 'rxjs';

describe('AuditComponent', () => {
  let component: AuditComponent;
  let apiService: any;

  beforeEach(() => {
    apiService = {
      getAuditLogs: vi.fn().mockReturnValue(of([
        { user_email: 'a@test.com', action: 'login', timestamp: '2025-01-01' },
        { user_email: 'a@test.com', action: 'submit', timestamp: '2025-01-02' },
        { user_email: 'b@test.com', action: 'login', timestamp: '2025-01-01' },
      ])),
    };
    component = new AuditComponent(apiService, { detectChanges: vi.fn() } as any);
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load and group logs by email', () => {
    component.ngOnInit();
    expect(component.groupedLogs.length).toBe(2);
    expect(component.groupedLogs[0].entries.length).toBe(2); // a@test.com
    expect(component.groupedLogs[1].entries.length).toBe(1); // b@test.com
  });

  it('should toggle group expansion', () => {
    component.ngOnInit();
    expect(component.groupedLogs[0].expanded).toBe(false);
    component.toggleGroup('a@test.com');
    expect(component.groupedLogs[0].expanded).toBe(true);
  });

  it('should track by email', () => {
    expect(component.trackByEmail(0, { email: 'x@y.com' })).toBe('x@y.com');
  });
});
