import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-audit',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <div class="flex justify-between items-center mb-6">
        <h2 class="text-lg font-semibold text-slate-800">Auditoria (Caja Negra)</h2>
        <button (click)="loadAuditLogs()"
          class="px-4 py-2 text-sm border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors">
          Actualizar
        </button>
      </div>

      <!-- Loading -->
      <div *ngIf="isLoading" class="text-center py-8 text-slate-500">
        Cargando logs...
      </div>

      <!-- Grouped Audit Logs -->
      <div *ngIf="!isLoading" class="space-y-4">
        <div *ngFor="let group of groupedLogs; trackBy: trackByEmail"
          class="border border-slate-200 rounded-lg overflow-hidden">
          <!-- User Header -->
          <button (click)="toggleGroup(group.email)"
            class="w-full flex justify-between items-center p-4 bg-slate-50 hover:bg-slate-100 transition-colors">
            <div class="flex items-center gap-3">
              <span class="font-medium text-slate-700">{{ group.email }}</span>
              <span class="text-xs text-slate-500">{{ group.entries.length }} actividades</span>
            </div>
            <span class="text-slate-400">{{ group.expanded ? '&#9650;' : '&#9660;' }}</span>
          </button>

          <!-- Activity Entries -->
          <div *ngIf="group.expanded" class="p-4 space-y-2">
            <div *ngFor="let entry of group.entries"
              class="text-sm p-2 rounded bg-slate-50 text-slate-600">
              <span class="font-mono text-xs text-slate-400">{{ entry.timestamp | date:'short' }}</span>
              <span class="ml-2">{{ entry.action }}</span>
              <span *ngIf="entry.details" class="text-slate-400 ml-1">- {{ entry.details }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div *ngIf="!isLoading && groupedLogs.length === 0"
        class="text-center py-8 text-slate-500">
        No hay registros de auditoria.
      </div>
    </div>
  `,
})
export class AuditComponent implements OnInit {
  auditLogs: any[] = [];
  groupedLogs: any[] = [];
  isLoading = false;

  constructor(
    private apiService: ApiService,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.loadAuditLogs();
  }

  loadAuditLogs(): void {
    this.isLoading = true;
    this.apiService.getAuditLogs().subscribe({
      next: (data: any) => {
        this.auditLogs = data;
        this.groupLogs();
      },
      error: (err: any) => {
        console.error('Failed to load audit logs:', err);
      },
    }).add(() => {
      this.isLoading = false;
      this.cdr.detectChanges();
    });
  }

  groupLogs(): void {
    const groups = new Map<string, any>();
    for (const log of this.auditLogs) {
      const email = log.user_email || log.email || 'unknown';
      if (!groups.has(email)) {
        groups.set(email, { email, entries: [], expanded: false });
      }
      groups.get(email)!.entries.push(log);
    }
    this.groupedLogs = Array.from(groups.values());
  }

  toggleGroup(email: string): void {
    const group = this.groupedLogs.find(g => g.email === email);
    if (group) {
      group.expanded = !group.expanded;
    }
  }

  trackByEmail(index: number, item: any): string {
    return item.email;
  }
}
