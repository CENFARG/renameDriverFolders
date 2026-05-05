import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-algorithms',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <div class="flex justify-between items-center mb-6">
        <h2 class="text-lg font-semibold text-slate-800">Algoritmos del Estudio</h2>
        <button (click)="loadAlgorithms()"
          class="px-4 py-2 text-sm border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors">
          Recargar
        </button>
      </div>

      <!-- Loading -->
      <div *ngIf="isLoading" class="text-center py-8 text-slate-500">
        Cargando algoritmos...
      </div>

      <!-- Algorithm List -->
      <div *ngIf="!isLoading && algorithms.length > 0" class="space-y-3">
        <div *ngFor="let algo of algorithms; trackBy: trackById"
          class="p-4 border border-slate-200 rounded-lg hover:border-blue-300 transition-colors">
          <div class="flex justify-between items-start">
            <div>
              <h3 class="font-medium text-slate-800">{{ algo.name }}</h3>
              <p class="text-sm text-slate-500 mt-1">{{ algo.description || 'Sin descripcion' }}</p>
            </div>
            <span [class]="algo.is_active !== false ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-500'"
              class="px-2 py-1 text-xs rounded-full">
              {{ algo.is_active !== false ? 'Activo' : 'Inactivo' }}
            </span>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div *ngIf="!isLoading && algorithms.length === 0"
        class="text-center py-8 text-slate-500">
        No se encontraron algoritmos.
      </div>
    </div>
  `,
})
export class AlgorithmsComponent implements OnInit {
  algorithms: any[] = [];
  isLoading = false;

  constructor(
    private apiService: ApiService,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.loadAlgorithms();
  }

  loadAlgorithms(): void {
    this.isLoading = true;
    this.apiService.getAlgorithms().subscribe({
      next: (data: any) => {
        this.algorithms = data;
      },
      error: (err: any) => {
        console.error('Failed to load algorithms:', err);
      },
    }).add(() => {
      this.isLoading = false;
      this.cdr.detectChanges();
    });
  }

  trackById(index: number, item: any): string {
    return item.id || index.toString();
  }
}
