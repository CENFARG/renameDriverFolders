import { Component, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <h2 class="text-lg font-semibold text-slate-800 mb-4">Configuracion</h2>

      <!-- Connection Status -->
      <div class="space-y-3">
        <div class="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
          <span class="text-sm text-slate-700">Estado de sesion</span>
          <span [class]="isAuthenticated ? 'text-green-600' : 'text-red-600'" class="text-sm font-medium">
            {{ isAuthenticated ? 'Autenticado' : 'No autenticado' }}
          </span>
        </div>

        <div class="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
          <span class="text-sm text-slate-700">Token de acceso</span>
          <span class="text-sm text-slate-500">
            {{ hasToken ? 'Disponible' : 'No disponible' }}
          </span>
        </div>

        <div class="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
          <span class="text-sm text-slate-700">Tema</span>
          <span class="text-sm text-slate-500">
            {{ isDark ? 'Oscuro' : 'Claro' }}
          </span>
        </div>
      </div>
    </div>
  `,
})
export class SettingsComponent {
  isDark = true;

  constructor(
    private authService: AuthService,
    private cdr: ChangeDetectorRef,
  ) {
    this.isDark = localStorage.getItem('theme') !== 'light';
  }

  get isAuthenticated(): boolean {
    return this.authService.isAuthenticated();
  }

  get hasToken(): boolean {
    return !!this.authService.getToken();
  }
}
