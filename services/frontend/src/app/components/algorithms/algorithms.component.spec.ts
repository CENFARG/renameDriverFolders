import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AlgorithmsComponent } from './algorithms.component';
import { ApiService } from '../../services/api.service';
import { of } from 'rxjs';

describe('AlgorithmsComponent', () => {
  let component: AlgorithmsComponent;
  let apiService: any;

  beforeEach(() => {
    apiService = {
      getAlgorithms: vi.fn().mockReturnValue(of([
        { id: 'algo1', name: 'Facturas', is_active: true },
        { id: 'algo2', name: 'Sueldos', is_active: false },
      ])),
    };
    component = new AlgorithmsComponent(apiService, { detectChanges: vi.fn() } as any);
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load algorithms on init', () => {
    component.ngOnInit();
    expect(apiService.getAlgorithms).toHaveBeenCalled();
    expect(component.algorithms.length).toBe(2);
  });

  it('should track by id', () => {
    expect(component.trackById(0, { id: 'a1' })).toBe('a1');
    expect(component.trackById(1, {})).toBe('1');
  });
});
