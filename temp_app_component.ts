import { Component, OnInit, AfterViewInit, ElementRef, ViewChild, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Observable } from 'rxjs';
import { AuthService } from './services/auth.service';
import { ApiService } from './services/api.service';
import { User, Job } from './models/job.model';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="bg-slate-50 min-h-screen font-sans flex flex-col">
      <!-- Header -->
      <header class="bg-white shadow-md">
        <div class="container mx-auto px-4 md:px-8 py-3 flex justify-between items-center">
          <div class="flex items-center gap-4">
            <span class="text-3xl">­ƒôé</span>
            <div>
              <h1 class="text-xl md:text-2xl font-bold text-slate-800">Renombrador de Carpetas</h1>
              <p class="text-slate-500 text-sm">Automatizaci├│n con IA para Google Drive</p>
            </div>
          </div>
          <div *ngIf="user$ | async as user" class="flex items-center gap-4">
            <div class="hidden md:flex flex-col items-end">
              <span class="text-sm font-semibold text-slate-700">{{user.name}}</span>
              <span class="text-xs text-slate-500">{{user.email}}</span>
            </div>
            <img [src]="user.picture" alt="User" class="w-10 h-10 rounded-full border border-slate-200">
            <button (click)="signOut()" class="text-slate-500 hover:text-red-500 transition-colors">
              <span class="text-xl">­ƒÜ¬</span>
            </button>
          </div>
        </div>
      </header>

      <!-- Main Content -->
      <main class="container mx-auto px-4 md:px-8 py-8 flex-grow">
        
        <!-- Login View -->
        <div *ngIf="!(user$ | async)" class="max-w-md mx-auto mt-20">
          <div class="bg-white p-10 rounded-2xl shadow-2xl border border-slate-100 text-center">
            <div class="text-6xl mb-6">­ƒôé</div>
            <h2 class="text-2xl font-bold text-slate-800 mb-2">Bienvenido</h2>
            <p class="text-slate-500 mb-8">Accede con tu cuenta autorizada para gestionar el procesamiento de archivos.</p>
            <div #googleButton class="flex justify-center"></div>
          </div>
        </div>

        <!-- Authenticated Dashboard -->
        <div *ngIf="user$ | async as user">
          
          <!-- Admin Tabs -->
          <div *ngIf="isAdmin" class="flex border-b border-slate-200 mb-8 gap-1">
            <button (click)="setView('dashboard')" 
              [class]="view === 'dashboard' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'"
              class="px-6 py-3 border-b-2 font-medium transition-all">
              Dashboard
            </button>
            <button (click)="setView('config')" 
              [class]="view === 'config' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'"
              class="px-6 py-3 border-b-2 font-medium transition-all">
              Configuraciones
            </button>
            <button (click)="setView('audit')" 
              [class]="view === 'audit' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'"
              class="px-6 py-3 border-b-2 font-medium transition-all">
              Auditor├¡a (Caja Negra)
            </button>
          </div>

          <!-- View: Dashboard -->
          <div *ngIf="view === 'dashboard'" class="max-w-3xl mx-auto">
            <div class="bg-white p-8 rounded-xl shadow-lg border border-slate-200">
              <h2 class="text-xl font-semibold text-slate-800 mb-4">Paso 1: Procesar Carpeta</h2>
              <p class="text-slate-500 mb-6">Ingresa el ID de la carpeta de Google Drive que deseas que la IA procese y renombre.</p>
              
              <form (ngSubmit)="submitJob()" class="space-y-6">
                <div>
                  <label for="folderId" class="block text-sm font-medium text-slate-700 mb-1">ID de Carpeta *</label>
                  <input id="folderId" [(ngModel)]="folderId" name="folderId" type="text" required
                    class="block w-full border border-slate-300 rounded-lg shadow-sm py-3 px-4 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                    placeholder="Ej: 1ABC-123xyz...">
                </div>

                <div>
                  <label for="jobType" class="block text-sm font-medium text-slate-700 mb-1">Tipo de Trabajo</label>
                  <select id="jobType" [(ngModel)]="jobType" name="jobType"
                    class="block w-full border border-slate-300 rounded-lg shadow-sm py-3 px-4 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all cursor-pointer">
                    <option value="generic">Gen├®rico (Detecci├│n Autom├ítica)</option>
                    <option *ngFor="let job of jobs" [value]="job.id">{{job.name}}</option>
                  </select>
                </div>

                <div class="pt-4">
                  <button type="submit" [disabled]="isSubmitting"
                    class="w-full flex justify-center py-4 px-4 border border-transparent rounded-lg shadow-md text-base font-bold text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-slate-300 disabled:cursor-not-allowed transition-all">
                    {{isSubmitting ? 'Procesando con IA...' : 'Ejecutar Renombrado con IA'}}
                  </button>
                </div>
              </form>

              <div *ngIf="result" [class]="result === 'error' ? 'bg-red-50 text-red-700 border-red-100' : 'bg-green-50 text-green-700 border-green-100'" 
                class="mt-6 p-4 rounded-lg border flex items-center gap-3">
                <span class="text-xl">{{result === 'error' ? 'ÔØî' : 'Ô£à'}}</span>
                <span class="font-medium text-sm">{{resultMessage}}</span>
              </div>
            </div>
          </div>

          <!-- View: Audit Logs -->
          <div *ngIf="view === 'audit'" class="max-w-5xl mx-auto animate-fade-in">
            <div class="bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden">
              <div class="p-6 border-b border-slate-100 flex justify-between items-center bg-slate-50">
                <h2 class="text-xl font-bold text-slate-800 flex items-center gap-2">
                  <span>­ƒûñ</span> Historial de Auditor├¡a (Caja Negra)
                </h2>
                <button (click)="loadAuditLogs()" class="bg-slate-200 hover:bg-slate-300 text-slate-700 px-4 py-2 rounded-lg text-sm font-bold transition-all">Refrescar</button>
              </div>
              <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                  <thead>
                    <tr class="bg-slate-50 text-slate-500 text-xs uppercase tracking-wider">
                      <th class="px-6 py-4 font-semibold">Fecha/Hora</th>
                      <th class="px-6 py-4 font-semibold">Usuario</th>
                      <th class="px-6 py-4 font-semibold">Acci├│n</th>
                      <th class="px-6 py-4 font-semibold">Estado</th>
                      <th class="px-6 py-4 font-semibold">Detalles</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-slate-100">
                    <tr *ngFor="let log of auditLogs; trackBy: trackById" class="hover:bg-slate-50 transition-colors">
                      <td class="px-6 py-4 text-xs text-slate-500">{{log.timestamp | date:'short'}}</td>
                      <td class="px-6 py-4 text-sm font-medium text-slate-700">{{log.user_email}}</td>
                      <td class="px-6 py-4"><span class="px-2 py-1 rounded-full text-[10px] uppercase font-bold bg-slate-100 text-slate-600">{{log.action}}</span></td>
                      <td class="px-6 py-4">
                        <span [class]="log.status === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'" class="px-2 py-1 rounded-full text-[10px] uppercase font-bold">
                          {{log.status}}
                        </span>
                      </td>
                      <td class="px-6 py-4 text-xs text-slate-500 max-w-xs truncate">{{log.details}}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <!-- View: Config -->
          <div *ngIf="view === 'config'" class="max-w-5xl mx-auto animate-fade-in text-slate-800">
            <div *ngIf="!showEditor" class="bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden">
              <div class="p-6 border-b border-slate-100 flex justify-between items-center bg-slate-50">
                <h2 class="text-xl font-bold text-slate-800 flex items-center gap-2">
                  <span>ÔÜÖ´©Å</span> Gesti├│n de Configuraciones (Jobs)
                </h2>
                <button (click)="newJob()" class="bg-blue-600 text-white px-4 py-2 rounded-lg font-bold text-sm hover:bg-blue-700 transition-all shadow-md active:scale-95">
                  + Nuevo Job
                </button>
              </div>
              <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                  <thead>
                    <tr class="bg-slate-50 text-slate-500 text-xs uppercase tracking-wider">
                      <th class="px-6 py-4 font-semibold text-slate-600">Nombre</th>
                      <th class="px-6 py-4 font-semibold text-slate-600">Estado</th>
                      <th class="px-6 py-4 font-semibold text-slate-600">Trigger</th>
                      <th class="px-6 py-4 font-semibold text-slate-600">Acciones</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-slate-100">
                    <tr *ngFor="let job of jobs; trackBy: trackById" class="hover:bg-slate-50 transition-colors">
                      <td class="px-6 py-4">
                        <div class="text-sm font-bold text-slate-800">{{job.name}}</div>
                        <div class="text-xs text-slate-500">{{job.description}}</div>
                      </td>
                      <td class="px-6 py-4">
                        <span [class]="job.active ? 'bg-green-100 text-green-700' : 'bg-slate-200 text-slate-500'" class="px-2 py-1 rounded-full text-[10px] uppercase font-bold shadow-sm">
                          {{job.active ? 'Activo' : 'Inactivo'}}
                        </span>
                      </td>
                      <td class="px-6 py-4 text-sm text-slate-600 uppercase font-medium">{{job.trigger_type}}</td>
                      <td class="px-6 py-4">
                        <div class="flex gap-4">
                          <button (click)="editJob(job)" class="text-blue-600 hover:text-blue-800 font-bold text-xs uppercase transition-colors">Editar</button>
                          <button (click)="deleteJob(job.id)" class="text-red-500 hover:text-red-700 font-bold text-xs uppercase transition-colors">Eliminar</button>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Job Editor Form -->
            <div *ngIf="showEditor" class="bg-white rounded-xl shadow-2xl border border-slate-200 overflow-hidden animate-slide-up max-w-2xl mx-auto">
              <div class="p-6 border-b border-slate-100 bg-slate-50 flex justify-between items-center">
                <h2 class="text-xl font-bold">{{isEditing ? 'Editar' : 'Nueva'}} Configuraci├│n</h2>
                <button (click)="showEditor = false" class="text-slate-400 hover:text-slate-600 text-2xl">&times;</button>
              </div>
              <div class="p-8 space-y-6 overflow-y-auto max-h-[70vh]">
                <div class="grid grid-cols-2 gap-6">
                  <div class="col-span-2">
                    <label class="block text-xs font-bold text-slate-500 uppercase mb-1">ID ├Ünico del Job *</label>
                    <input [(ngModel)]="currentJob.id" [disabled]="isEditing" type="text" placeholder="ej: retenciones-v1" class="w-full border rounded-lg p-3 outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-slate-100">
                  </div>
                  <div class="col-span-2">
                    <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Nombre Descriptivo *</label>
                    <input [(ngModel)]="currentJob.name" type="text" placeholder="ej: Retenciones RG 830" class="w-full border rounded-lg p-3 outline-none focus:ring-2 focus:ring-blue-500">
                  </div>
                  <div class="col-span-2">
                    <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Descripci├│n</label>
                    <textarea [(ngModel)]="currentJob.description" class="w-full border rounded-lg p-3 outline-none focus:ring-2 focus:ring-blue-500" rows="2"></textarea>
                  </div>
                  <div>
                    <label class="block text-xs font-bold text-slate-500 uppercase mb-1">ID Carpeta Origen (Drive) *</label>
                    <input [(ngModel)]="currentJob.source_folder_id" type="text" class="w-full border rounded-lg p-3 outline-none focus:ring-2 focus:ring-blue-500">
                  </div>
                  <div>
                    <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Trigger</label>
                    <select [(ngModel)]="currentJob.trigger_type" class="w-full border rounded-lg p-3 outline-none focus:ring-2 focus:ring-blue-500">
                      <option value="manual">Manual</option>
                      <option value="scheduled">Programado (Scheduled)</option>
                    </select>
                  </div>
                </div>

                <div class="border-t pt-6">
                  <h3 class="font-bold text-slate-800 mb-4 flex items-center gap-2">­ƒÜÇ Configuraci├│n de IA (Grama Brain)</h3>
                  <div class="space-y-4">
                    <div class="grid grid-cols-2 gap-4">
                      <div>
                        <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Modelo</label>
                        <select [(ngModel)]="currentJob.agent_config.model.name" class="w-full border rounded-lg p-3 outline-none focus:ring-2 focus:ring-blue-500">
                          <option value="gemini-1.5-flash">Gemini 1.5 Flash (R├ípido)</option>
                          <option value="gemini-1.5-pro">Gemini 1.5 Pro (Potente)</option>
                          <option value="gemini-2.0-flash-exp">Gemini 2.0 Flash (Next Gen)</option>
                        </select>
                      </div>
                      <div>
                        <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Formato Nombre Salida</label>
                        <input [(ngModel)]="currentJob.agent_config.filename_format" type="text" placeholder="ej: FACTURA_{date}_{id}.pdf" class="w-full border rounded-lg p-3 outline-none focus:ring-2 focus:ring-blue-500">
                      </div>
                    </div>
                    <div>
                      <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Instrucciones del Agente (System Prompt)</label>
                      <textarea [(ngModel)]="currentJob.agent_config.instructions" class="w-full border rounded-lg p-3 outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm" rows="4" placeholder="Eres un asistente legal..."></textarea>
                    </div>
                  </div>
                </div>
              </div>
              <div class="p-6 bg-slate-50 border-t flex justify-end gap-4">
                <button (click)="showEditor = false" class="px-6 py-2 text-slate-600 font-bold hover:bg-slate-200 rounded-lg transition-all">Cancelar</button>
                <button (click)="saveJob()" class="px-8 py-2 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700 shadow-lg active:scale-95 transition-all">
                  Guardar configuraci├│n
                </button>
              </div>
            </div>
          </div>

        </div>
      </main>

      <!-- Footer -->
      <footer class="bg-white mt-8 py-6 border-t border-slate-200">
        <div class="container mx-auto px-4 md:px-8 text-center text-slate-500 text-sm">
          <p>┬® 2026 Renovador de Carpetas - amBotHsOS Enterprise. Powered by Gemini Pro</p>
          <div class="mt-2 space-x-4">
            <a href="https://estudioanc.com.ar" target="_blank" class="text-blue-600 hover:underline">Estudio Cutignola</a>
            <span>ÔÇó</span>
            <a href="#" class="text-blue-600 hover:underline">Documentaci├│n</a>
          </div>
        </div>
      </footer>
    </div>
  `,
  styles: []
})
export class AppComponent implements OnInit, AfterViewInit {
  @ViewChild('googleButton') googleButton!: ElementRef;

  user$: Observable<any | null>;
  folderId = '';
  jobType = 'generic';
  isSubmitting = false;
  result = '';
  resultMessage = '';
  view = 'dashboard';
  isAdmin = false;
  jobs: any[] = [];
  auditLogs: any[] = [];

  private readonly ADMIN_EMAILS = [
    'cutignolad@estudioanc.com.ar',
    'gonzalo.f.recalde@gmail.com'
  ];

  constructor(
    private authService: AuthService,
    private apiService: ApiService,
    private cdr: ChangeDetectorRef
  ) {
    this.user$ = this.authService.user$;
  }

  ngOnInit(): void {
    this.authService.initializeGoogleSignIn();

    this.user$.subscribe(user => {
      console.log('­ƒæñ User state changed:', user ? user.email : 'Logged out');
      if (user) {
        this.isAdmin = this.ADMIN_EMAILS.includes(user.email);
        this.loadJobs();
        if (this.isAdmin) this.loadAuditLogs();
      } else {
        this.isAdmin = false;
        this.view = 'dashboard';
        setTimeout(() => this.initializeLoginButton(), 100);
      }
    });
  }

  ngAfterViewInit(): void {
    setTimeout(() => this.initializeLoginButton(), 100);
  }

  setView(view: string): void {
    this.view = view;
    if (view === 'dashboard') this.loadJobs();
    if (view === 'audit') this.loadAuditLogs();
    if (view === 'config') this.loadJobs();
  }

  loadJobs(): void {
    this.apiService.listJobs().subscribe({
      next: (res) => this.jobs = res.jobs,
      error: (e) => console.error('Failed to load jobs', e)
    });
  }

  loadAuditLogs(): void {
    this.apiService.getAuditLogs().subscribe({
      next: (res) => this.auditLogs = res.logs || [],
      error: (e) => console.error('Failed to load audit logs', e)
    });
  }

  initializeLoginButton(): void {
    if (this.googleButton && !this.authService.isAuthenticated()) {
      this.authService.renderButton(this.googleButton.nativeElement);
      this.cdr.detectChanges();
    }
  }

  submitJob(): void {
    if (!this.folderId) return;

    this.isSubmitting = true;
    this.result = '';
    this.cdr.detectChanges();

    const job = {
      folder_id: this.folderId,
      job_type: this.jobType
    };

    this.apiService.submitJob(job).subscribe({
      next: (response) => {
        this.result = 'success';
        this.resultMessage = response.message || 'Tarea encolada correctamente';
        this.folderId = '';
        if (this.isAdmin) this.loadAuditLogs();
      },
      error: (error) => {
        this.result = 'error';
        this.resultMessage = error.error?.detail || 'Error al procesar';
      },
      complete: () => {
        this.isSubmitting = false;
        this.cdr.detectChanges();
        setTimeout(() => { this.result = ''; this.cdr.detectChanges(); }, 8000);
      }
    });
  }

  showEditor = false;
  isEditing = false;
  currentJob: any = this.resetJob();

  private resetJob() {
    return {
      id: '',
      name: '',
      description: '',
      active: true,
      trigger_type: 'manual',
      source_folder_id: '',
      target_folder_names: ['Procesados'],
      agent_config: {
        model: { name: 'gemini-1.5-flash', temperature: 0.1, max_tokens: 2048 },
        instructions: 'Analiza el documento y extrae el tipo, n├║mero y fecha para renombrar.',
        prompt_template: 'Contenido del documento: {{content}}',
        filename_format: 'DOC_{date}_{id}.pdf'
      }
    };
  }

  newJob(): void {
    this.isEditing = false;
    this.currentJob = this.resetJob();
    this.showEditor = true;
  }

  editJob(job: any): void {
    this.isEditing = true;
    this.apiService.getJob(job.id).subscribe({
      next: (res) => {
        this.currentJob = res;
        this.showEditor = true;
      },
      error: (e) => alert('Error al cargar configuraci├│n: ' + e.message)
    });
  }

  saveJob(): void {
    const action = this.isEditing ?
      this.apiService.updateJob(this.currentJob.id, this.currentJob) :
      this.apiService.createJob(this.currentJob);

    action.subscribe({
      next: () => {
        this.showEditor = false;
        this.loadJobs();
      },
      error: (e) => alert('Error al guardar: ' + (e.error?.detail || e.message))
    });
  }

  trackById(index: number, item: any): string {
    return item.id || index;
  }

  deleteJob(id: string): void {
    if (confirm('┬┐Est├ís seguro de eliminar esta configuraci├│n?')) {
      this.apiService.deleteJob(id).subscribe({
        next: () => this.loadJobs(),
        error: (e) => alert('Error al eliminar: ' + e.message)
      });
    }
  }

  signOut(): void {
    this.authService.signOut();
    this.cdr.detectChanges();
  }
}
