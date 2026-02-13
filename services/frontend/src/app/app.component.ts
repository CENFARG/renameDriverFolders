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
  templateUrl: './app.component.html',
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
      schedule: '',
      source_folder_id: '',
      target_folder_names: ['Procesados'],
      agent_config: {
        model: { name: 'gemini-2.5-flash', temperature: 0.1, max_tokens: 4096 },
        instructions: 'Analiza el documento y extrae el tipo, número y fecha para renombrar.',
        prompt_template: 'Contenido del documento: {{content}}',
        filename_format: 'DOC_{date}_{id}.pdf'
      }
    };
  }

  // --- UI Helpers ---
  scheduledDate: string = '';
  showScheduleHelp = false;
  showModelHelp = false;
  showConfigTutorial = false;

  updateCronFromDate(): void {
    if (!this.scheduledDate) return;
    const date = new Date(this.scheduledDate);
    // Google Cloud Scheduler expects: minute hour day month dayOfWeek
    const min = date.getMinutes();
    const hour = date.getHours();
    const day = date.getDate();
    const month = date.getMonth() + 1; // 1-12
    const cron = `${min} ${hour} ${day} ${month} *`;
    this.currentJob.schedule = cron;
    console.log('🔄 CRON Generated:', cron);
  }

  newJob(): void {
    this.isEditing = false;
    this.currentJob = this.resetJob();
    this.showEditor = true;
  }

  editJob(job: any): void {
    if (!job.id) {
      alert('Error: La configuración seleccionada no tiene un ID válido. No se puede editar.');
      return;
    }
    this.isEditing = true;
    this.apiService.getJob(job.id).subscribe({
      next: (res) => {
        this.currentJob = res;
        this.showEditor = true;
      },
      error: (e) => alert('Error al cargar configuración: ' + e.message)
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
    if (!id) {
      alert('Error: No se pudo identificar el ID de la configuración para eliminar.');
      return;
    }
    if (confirm('¿Estás seguro de eliminar esta configuración?')) {
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
