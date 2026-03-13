import { Component, OnInit, AfterViewInit, ElementRef, ViewChild, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Observable } from 'rxjs';
import { AuthService } from './services/auth.service';
import { ApiService } from './services/api.service';
import { User, Job } from './models/job.model';

declare const google: any;
declare const gapi: any;

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

  private accessToken: string | null = null;
  private pickerApiLoaded = false;

  constructor(
    private authService: AuthService,
    private apiService: ApiService,
    private cdr: ChangeDetectorRef
  ) {
    this.user$ = this.authService.user$;
  }

  ngOnInit(): void {
    this.authService.initializeGoogleSignIn();
    this.loadPickerApi();

    this.user$.subscribe(user => {
      console.log('👤 User state changed:', user ? user.email : 'Logged out');
      if (user) {
        this.isAdmin = this.ADMIN_EMAILS.includes(user.email);
        this.loadJobs();
        if (this.isAdmin) this.loadAuditLogs();
        // Request token for picker
        this.requestAccessToken();
      } else {
        this.isAdmin = false;
        this.view = 'dashboard';
        setTimeout(() => this.initializeLoginButton(), 100);
      }
    });
  }

  loadPickerApi(): void {
    const script = document.createElement('script');
    script.src = 'https://apis.google.com/js/api.js';
    script.onload = () => {
      gapi.load('picker', () => {
        this.pickerApiLoaded = true;
        console.log('✅ Google Picker API loaded');
      });
    };
    document.body.appendChild(script);
  }

  requestAccessToken(retryCount = 0): void {
    if (typeof google === 'undefined' || !google.accounts) {
      if (retryCount < 5) {
        console.warn(`⚠️ Google Identity Services not ready. Retrying... (${retryCount + 1}/5)`);
        setTimeout(() => this.requestAccessToken(retryCount + 1), 1000);
      } else {
        console.error('❌ Google Identity Services failed to load after 5 retries.');
      }
      return;
    }

    try {
      const tokenClient = google.accounts.oauth2.initTokenClient({
        client_id: '702567224563-74i4orff38l8afk39j4hsc411mm3d1ma.apps.googleusercontent.com',
        scope: 'https://www.googleapis.com/auth/drive.readonly',
        callback: (response: any) => {
          if (response.access_token) {
            this.accessToken = response.access_token;
            console.log('✅ Access Token acquired for Picker');
          }
        },
      });
      tokenClient.requestAccessToken({ prompt: '' });
    } catch (e) {
      console.error('Error initializing token client:', e);
    }
  }

  openPicker(target: 'dashboard' | 'config'): void {
    if (!this.pickerApiLoaded || !this.accessToken) {
      this.requestAccessToken();
      return;
    }

    const view = new google.picker.DocsView(google.picker.ViewId.FOLDERS)
      .setSelectFolderEnabled(true)
      .setMimeTypes('application/vnd.google-apps.folder');

    const pickerBuilder = new google.picker.PickerBuilder()
      .addView(view)
      .setOAuthToken(this.accessToken)
      .setCallback((data: any) => {
        if (data.action === google.picker.Action.PICKED) {
          const doc = data.docs[0];
          if (target === 'dashboard') {
            this.folderId = doc.id;
          } else {
            this.currentJob.source_folder_id = doc.id;
          }
          this.cdr.detectChanges();
        }
      });

    // Agregar API key si está configurada (elimina mensaje "Solo para desarrolladores")
    // @ts-ignore - googleApiKey es una propiedad custom del environment
    if (environment.googleApiKey) {
      // @ts-ignore
      pickerBuilder.setDeveloperKey(environment.googleApiKey);
      console.log('✅ Using Google API Key for Picker (production mode)');
    } else {
      console.log('⚠️ No Google API Key configured - Picker may show developer warning');
    }

    const picker = pickerBuilder.build();
    picker.setVisible(true);
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
        // Ensure resultMessage is a string and not [object Object]
        const detail = error.error?.detail;
        this.resultMessage = typeof detail === 'string' ? detail :
          (detail?.message || error.message || 'Error desconocido al procesar');
        console.error('Submission error:', error);
      }
    }).add(() => {
      // Always reset submitting state (finally equivalent)
      this.isSubmitting = false;
      this.cdr.detectChanges();
      setTimeout(() => { this.result = ''; this.cdr.detectChanges(); }, 8000);
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
  showFormatHelp = false;

  appendTag(tag: string): void {
    const current = this.currentJob.agent_config.filename_format || '';
    // Append or replace? Let's just append for now but smart-ish
    if (current.endsWith('_') || current === '') {
      this.currentJob.agent_config.filename_format = current + tag;
    } else {
      this.currentJob.agent_config.filename_format = current + '_' + tag;
    }
    this.cdr.detectChanges();
  }

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
      error: (e) => {
        console.error('Error loading job:', e);
        const errorMsg = e.error?.detail || e.message || 'Error desconocido';
        alert(`Error al cargar configuración: ${errorMsg}\n\nID: ${job.id}`);
      }
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
        // Show success message
        this.result = 'success';
        this.resultMessage = this.isEditing ?
          'Algoritmo actualizado correctamente' :
          'Algoritmo creado correctamente';
        setTimeout(() => { this.result = ''; this.cdr.detectChanges(); }, 5000);
      },
      error: (e) => {
        console.error('Error saving job:', e);
        const errorMsg = e.error?.detail || e.message || 'Error desconocido';
        alert(`Error al guardar: ${errorMsg}\n\n${this.isEditing ? 'Acción: Actualizar' : 'Acción: Crear'}\nID: ${this.currentJob.id || 'N/A'}`);
      }
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
    if (confirm('¿Estás seguro de eliminar esta configuración? Esta acción no se puede deshacer.')) {
      this.apiService.deleteJob(id).subscribe({
        next: () => {
          this.loadJobs();
          // Show success message
          this.result = 'success';
          this.resultMessage = 'Algoritmo eliminado correctamente';
          setTimeout(() => { this.result = ''; this.cdr.detectChanges(); }, 5000);
        },
        error: (e) => {
          console.error('Error deleting job:', e);
          const errorMsg = e.error?.detail || e.message || 'Error desconocido';
          alert(`Error al eliminar: ${errorMsg}\n\nID: ${id}`);
        }
      });
    }
  }

  duplicateJob(job: any): void {
    if (!job.id) {
      alert('Error: La configuración seleccionada no tiene un ID válido. No se puede duplicar.');
      return;
    }

    // Create a copy of the job with a new name and no ID
    const duplicatedJob = {
      ...job,
      id: undefined,
      name: `${job.name} [COPIA]`,
      created_at: new Date().toISOString()
    };

    this.apiService.createJob(duplicatedJob).subscribe({
      next: () => {
        this.loadJobs();
        // Show success message
        this.result = 'success';
        this.resultMessage = `Algoritmo "${job.name}" duplicado correctamente como "${duplicatedJob.name}"`;
        setTimeout(() => { this.result = ''; this.cdr.detectChanges(); }, 5000);
      },
      error: (e) => alert('Error al duplicar: ' + (e.error?.detail || e.message))
    });
  }

  signOut(): void {
    this.authService.signOut();
    this.cdr.detectChanges();
  }
}
