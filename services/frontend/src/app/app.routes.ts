import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  { path: 'dashboard', loadComponent: () => import('./components/dashboard/dashboard.component').then(m => m.DashboardComponent) },
  { path: 'algorithms', loadComponent: () => import('./components/algorithms/algorithms.component').then(m => m.AlgorithmsComponent) },
  { path: 'audit', loadComponent: () => import('./components/audit/audit.component').then(m => m.AuditComponent) },
];
