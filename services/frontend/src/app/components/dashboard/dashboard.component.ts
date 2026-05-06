import { Component, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';

declare const google: any;
declare const gapi: any;

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <h2 class="text-lg font-semibold text-slate-800 mb-4">Procesar Carpeta</h2>

      <!-- Folder Selection -->
      <div class="mb-4">
        <label class="block text-sm font-medium text-slate-700 mb-2">Carpeta de Google Drive</label>
        <div class="flex gap-2">
          <input [(ngModel)]="folderId" placeholder="Selecciona una carpeta..."
            class="flex-1 border border-slate-300 rounded-lg px-4 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" readonly>
          <button (click)="openPicker()"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium transition-colors">
            Seleccionar
          </button>
        </div>
      </div>

      <!-- Submit Button -->
      <button (click)="submitJob()" [disabled]="!folderId || isSubmitting"
        class="w-full py-3 px-4 rounded-lg font-medium text-sm transition-colors"
        [class]="folderId && !isSubmitting ? 'bg-blue-600 text-white hover:bg-blue-700' : 'bg-slate-200 text-slate-500 cursor-not-allowed'">
        {{ isSubmitting ? 'Procesando...' : 'Ejecutar renombrado con IA' }}
      </button>

      <!-- Result Message -->
      <div *ngIf="resultMessage" class="mt-4 p-3 rounded-lg text-sm"
        [class]="result === 'success' ? 'bg-green-50 text-green-700' : result === 'error' ? 'bg-red-50 text-red-700' : 'bg-blue-50 text-blue-700'">
        {{ resultMessage }}
      </div>
    </div>
  `,
})
export class DashboardComponent {
  folderId = '';
  jobType = 'auto-classify';
  isSubmitting = false;
  result = '';
  resultMessage = '';

  private accessToken: string | null = null;
  private pickerApiLoaded = false;

  constructor(
    private apiService: ApiService,
    private authService: AuthService,
    private cdr: ChangeDetectorRef,
  ) {}

  openPicker(): void {
    const token = this.authService.getToken();
    if (!token) return;

    if (typeof gapi !== 'undefined' && gapi.picker) {
      this.showPicker(token);
    }
  }

  private showPicker(token: string): void {
    const view = new google.picker.DocsView(google.picker.ViewId.FOLDERS)
      .setSelectFolderEnabled(true)
      .setMode(google.picker.DocsViewMode.LIST);

    new google.picker.PickerBuilder()
      .addView(view)
      .setOAuthToken(token)
      .setCallback((data: any) => {
        if (data.action === google.picker.Action.PICKED) {
          const doc = data.docs[0];
          this.folderId = doc.id;
          this.cdr.detectChanges();
        }
      })
      .build()
      .setVisible(true);
  }

  submitJob(): void {
    if (!this.folderId) return;
    this.isSubmitting = true;
    this.result = '';
    this.cdr.detectChanges();

    const job = { folder_id: this.folderId, job_type: this.jobType };
    const token = this.authService.getToken();
    if (!token) return;

    this.apiService.submitJob(job, token).subscribe({
      next: (response: any) => {
        this.result = 'success';
        this.resultMessage = response.message || 'Tarea encolada correctamente';
        this.folderId = '';
      },
      error: (error: any) => {
        this.result = 'error';
        this.resultMessage = error.error?.detail || error.message || 'Error desconocido';
      },
    }).add(() => {
      this.isSubmitting = false;
      this.cdr.detectChanges();
    });
  }
}
