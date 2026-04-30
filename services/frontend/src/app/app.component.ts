import { Component, OnInit, AfterViewInit, OnDestroy, ElementRef, ViewChild, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Observable } from 'rxjs';
import { AuthService } from './services/auth.service';
import { ApiService } from './services/api.service';
import { User, Job } from './models/job.model';
import { environment } from '../environments/environment';

declare const google: any;
declare const gapi: any;

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './app.component.html',
  styles: []
})
export class AppComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('googleButton') googleButton!: ElementRef;

  user$: Observable<any | null>;
  folderId = '';
  jobType = 'auto-classify';
  isSubmitting = false;
  result = '';
  resultMessage = '';
  view = 'dashboard';
  isAdmin = false;
  jobs: any[] = [];
  auditLogs: any[] = [];
  predefinedAlgorithms: any[] = [];

  private readonly ADMIN_EMAILS = [
    'cutignolad@estudioanc.com.ar',
    'gonzalo.f.recalde@gmail.com'
  ];

  private accessToken: string | null = null;
  private pickerApiLoaded = false;
  private isLoadingAuditLogs = false;
  private auditLogsTimeout: any = null;
  private auditLogsInterval: any = null;
  isDark = true; // Dark theme by default
  selectedDays: number[] = [1, 2, 3, 4, 5]; // Default: Lunes a Viernes
  selectedTime = '09:00'; // Default: 9 AM
  weekDays = [
    { label: 'Lun', value: 1 },
    { label: 'Mar', value: 2 },
    { label: 'Mié', value: 3 },
    { label: 'Jue', value: 4 },
    { label: 'Vie', value: 5 },
    { label: 'Sáb', value: 6 },
    { label: 'Dom', value: 0 }
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
    this.loadPickerApi();
    this.initializeTheme();

    this.user$.subscribe(user => {
      console.log('👤 User state changed:', user ? user.email : 'Logged out');
      if (user) {
        this.isAdmin = this.ADMIN_EMAILS.includes(user.email);
        this.loadJobs();
        // loadAlgorithms() is called inside loadJobs() to ensure jobs are loaded first
        // Load auto-classify config for job templates
        this.loadAutoClassifyConfig();
        if (this.isAdmin) {
          this.loadAuditLogs();
        }
        // Solicitar OAuth token INMEDIATAMENTE después del login (acción directa del usuario)
        // No necesitamos delay - el usuario ya hizo clic en "Sign in with Google"
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
    // Check if we already have a valid token stored
    const storedToken = localStorage.getItem('drive_access_token');
    const tokenExpiry = localStorage.getItem('drive_token_expiry');

    if (storedToken && tokenExpiry) {
      const expiryTime = parseInt(tokenExpiry);
      if (Date.now() < expiryTime) {
        // Token is still valid, reuse it
        this.accessToken = storedToken;
        console.log('✅ Reusing existing valid Access Token');
        return;
      } else {
        // Token expired, clear it
        console.log('⚠️ Previous token expired, requesting new one');
        localStorage.removeItem('drive_access_token');
        localStorage.removeItem('drive_token_expiry');
      }
    }

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
        scope: 'https://www.googleapis.com/auth/drive',
        callback: (response: any) => {
          if (response.access_token) {
            this.accessToken = response.access_token;
            console.log('✅ Access Token acquired for Drive API');

            // Store token with expiry (default 1 hour from Google)
            const expiryTime = Date.now() + (55 * 60 * 1000); // 55 minutes (safe margin)
            localStorage.setItem('drive_access_token', response.access_token);
            localStorage.setItem('drive_token_expiry', expiryTime.toString());
            console.log('💾 Token stored for reuse');

            // Clear any error messages if token was successfully acquired
            if (this.result === 'error' && this.resultMessage.includes('token de acceso')) {
              this.result = '';
              this.cdr.detectChanges();
            }
          } else if (response.error === 'popup_blocked') {
            console.warn('⚠️ Popup was blocked by browser. Please allow popups for this site.');
            this.result = 'error';
            this.resultMessage = 'El navegador bloqueó la ventana de autorización. Por favor, permite popups para este sitio.';
            this.cdr.detectChanges();
          }
        },
      });
      // Use 'select' mode to avoid popup blocker (shows dropdown instead)
      // 'consent' ensures user sees authorization screen
      tokenClient.requestAccessToken({ prompt: 'consent', mode: 'select' });
    } catch (e) {
      console.error('Error initializing token client:', e);
    }
  }

  openPicker(target: 'dashboard' | 'config'): void {
    // Solicitar token solo si no existe (el usuario hizo clic - acción directa)
    if (!this.accessToken) {
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
          console.log('📂 Picker returned doc.id:', doc.id);
          console.log('📂 ID length:', doc.id.length);
          console.log('📂 ID starts with:', doc.id.substring(0, 5));

          if (target === 'dashboard') {
            this.folderId = doc.id;
            console.log('✅ Dashboard folderId set to:', this.folderId);
          } else {
            this.currentJob.source_folder_id = doc.id;
            console.log('✅ Config source_folder_id set to:', this.currentJob.source_folder_id);
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

  initializeTheme(): void {
    // Check for saved theme preference or default to dark
    const savedTheme = localStorage.getItem('theme');
    this.isDark = savedTheme !== 'light'; // Default to true if not set
    this.applyTheme();
  }

  toggleTheme(): void {
    this.isDark = !this.isDark;
    localStorage.setItem('theme', this.isDark ? 'dark' : 'light');
    this.applyTheme();
  }

  private applyTheme(): void {
    const body = document.body;
    if (this.isDark) {
      body.classList.add('dark');
    } else {
      body.classList.remove('dark');
    }
    this.cdr.detectChanges();
  }

  ngOnDestroy(): void {
    // Clean up audit logs refresh interval
    if (this.auditLogsInterval) {
      clearInterval(this.auditLogsInterval);
      this.auditLogsInterval = null;
    }

    // Clean up audit logs timeout
    if (this.auditLogsTimeout) {
      clearTimeout(this.auditLogsTimeout);
      this.auditLogsTimeout = null;
    }
  }

  setView(view: string): void {
    this.view = view;

    // Clear any existing audit refresh interval
    if (this.auditLogsInterval) {
      clearInterval(this.auditLogsInterval);
      this.auditLogsInterval = null;
    }

    if (view === 'dashboard') this.loadJobs();
    if (view === 'audit') {
      if (this.isAdmin) {
        this.loadAuditLogs();
        // Auto-refresh audit logs every 10 minutes while in audit view (600000ms)
        this.auditLogsInterval = setInterval(() => {
          this.loadAuditLogs();
        }, 600000); // 10 minutes instead of 10 seconds
        console.log('✅ Auto-refresh enabled for audit logs (every 10 minutes)');
      } else {
        console.warn('⚠️ User is not admin, cannot load audit logs');
        this.auditLogs = [];
      }
    }
    if (view === 'config') this.loadJobs();
  }

  loadJobs(): void {
    this.apiService.listJobs().subscribe({
      next: (res) => {
        this.jobs = res.jobs;
        // Combine with predefined algorithms after jobs are loaded
        this.loadAlgorithms();
      },
      error: (e) => console.error('Failed to load jobs', e)
    });
  }

  loadAlgorithms(): void {
    this.apiService.getAlgorithms().subscribe({
      next: (algorithms) => {
        console.log('📚 Loaded', algorithms.length, 'predefined algorithms from Supabase');
        // Store predefined algorithms separately
        this.predefinedAlgorithms = algorithms;
      },
      error: (e) => {
        console.warn('⚠️ Failed to load predefined algorithms:', e);
        this.predefinedAlgorithms = [];
      }
    });
  }

  get allJobs(): any[] {
    // Combine user jobs with predefined algorithms
    return [...this.jobs, ...this.predefinedAlgorithms];
  }

  get groupedAuditLogs(): any[] {
    if (!this.auditLogs || this.auditLogs.length === 0) {
      return [];
    }

    // Group by user email
    const grouped: { [key: string]: { email: string; logs: any[]; lastActivity: Date } } = {};
    this.auditLogs.forEach(log => {
      const email = log.user_email || 'unknown';
      if (!grouped[email]) {
        grouped[email] = {
          email: email,
          logs: [],
          lastActivity: new Date(0)
        };
      }
      grouped[email].logs.push(log);

      // Update last activity
      const logDate = new Date(log.timestamp);
      if (logDate > grouped[email].lastActivity) {
        grouped[email].lastActivity = logDate;
      }
    });

    // Convert to array and sort by last activity
    return Object.values(grouped).sort((a: any, b: any) => b.lastActivity - a.lastActivity);
  }

  expandedUserEmails: string[] = [];

  toggleUserAuditExpansion(email: string): void {
    const index = this.expandedUserEmails.indexOf(email);
    if (index > -1) {
      this.expandedUserEmails.splice(index, 1);
    } else {
      this.expandedUserEmails.push(email);
    }
  }

  trackByEmail(index: number, group: any): string {
    return group.email;
  }

  loadAuditLogs(): void {
    // Debounce: Cancel previous load if pending
    if (this.auditLogsTimeout) {
      clearTimeout(this.auditLogsTimeout);
    }

    // Skip if already loading
    if (this.isLoadingAuditLogs) {
      console.log('⏸️ Audit logs already loading, skipping duplicate request');
      return;
    }

    this.auditLogsTimeout = setTimeout(() => {
      console.log('🔄 Loading audit logs...');
      this.isLoadingAuditLogs = true;

      this.apiService.getAuditLogs().subscribe({
        next: (res) => {
          this.auditLogs = res.logs || [];
          console.log(`✅ Loaded ${this.auditLogs.length} audit logs`);
        },
        error: (e) => {
          console.error('❌ Failed to load audit logs:', e);
          this.auditLogs = [];
        }
      }).add(() => {
        this.isLoadingAuditLogs = false;
      });
    }, 500); // 500ms debounce to avoid rapid calls
  }

  initializeLoginButton(): void {
    if (this.googleButton && !this.authService.isAuthenticated()) {
      this.authService.renderButton(this.googleButton.nativeElement);
      this.cdr.detectChanges();
    }
  }

  submitJob(): void {
    if (!this.folderId) return;

    // If we don't have an OAuth Access Token, request it first
    if (!this.accessToken) {
      console.warn('⚠️ No OAuth Access Token available. Requesting one...');
      this.isSubmitting = true; // Show loading state while requesting token
      this.cdr.detectChanges();

      // Request the token and continue submission after callback
      this.requestAccessToken();

      // Don't show error - token request will trigger consent screen
      // After user authorizes, they need to click submit again
      setTimeout(() => {
        this.isSubmitting = false;
        this.result = 'info';
        this.resultMessage = 'Por favor, autoriza el acceso a Google Drive y luego vuelve a hacer clic en "Ejecutar renombrado con IA".';
        this.cdr.detectChanges();

        // Clear message after 10 seconds
        setTimeout(() => {
          this.result = '';
          this.cdr.detectChanges();
        }, 10000);
      }, 2000);
      return;
    }

    this.isSubmitting = true;
    this.result = '';
    this.cdr.detectChanges();

    console.log('🚀 Submitting job with folder_id:', this.folderId);
    console.log('🚀 folder_id length:', this.folderId.length);
    console.log('🚀 folder_id starts with:', this.folderId.substring(0, 5));

    const job = {
      folder_id: this.folderId,
      job_type: this.jobType
    };

    console.log('📦 Job payload:', job);
    console.log('🔑 Including OAuth access_token for Worker: [MASKED]');

    this.apiService.submitJob(job, this.accessToken).subscribe({
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

  private autoClassifyConfig: any = null; // Cache the auto-classify config

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
      agent_config: this.autoClassifyConfig || {
        // Fallback if not loaded yet - will be replaced with auto-classify config
        model: { name: 'gemini-2.5-flash', temperature: 0.1, max_tokens: 4096 },
        instructions: 'Auto-classification with 10 algorithms - loading...',
        prompt_template: 'Loading...',
        filename_format: 'auto_classified.{ext}'
      }
    };
  }

  private loadAutoClassifyConfig(): void {
    // Load the auto-classify job config to use as template
    this.apiService.getJob('job-manual-auto-classify').subscribe({
      next: (job) => {
        this.autoClassifyConfig = job.agent_config;
        console.log('✅ Auto-classify config loaded for templates');
      },
      error: (e) => {
        console.warn('⚠️ Failed to load auto-classify config:', e);
        // Will use fallback from resetJob()
      }
    });
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

  updateScheduleFromUI(): void {
    // Ensure selectedDays is initialized
    if (!this.selectedDays || !Array.isArray(this.selectedDays)) {
      this.selectedDays = [1, 2, 3, 4, 5]; // Default: Lunes a Viernes
    }

    if (this.selectedDays.length === 0) {
      this.currentJob.schedule = '';
      return;
    }

    // Parse time (HH:MM)
    const [hour, minute] = this.selectedTime.split(':').map(Number);

    // Build day of week part for CRON
    let daysPart = '';
    if (this.selectedDays.length === 7) {
      daysPart = '*'; // Todos los días
    } else {
      // Sort and join days
      const sortedDays = [...this.selectedDays].sort((a, b) => a - b);
      daysPart = sortedDays.join(',');
    }

    // CRON format: minute hour day month dayOfWeek
    const cron = `${minute} ${hour} * * ${daysPart}`;
    this.currentJob.schedule = cron;
    console.log('🔄 Schedule updated:', cron);
    this.cdr.detectChanges();
  }

  toggleDay(dayValue: number): void {
    // Ensure selectedDays is initialized
    if (!this.selectedDays || !Array.isArray(this.selectedDays)) {
      this.selectedDays = [1, 2, 3, 4, 5];
    }

    const index = this.selectedDays.indexOf(dayValue);
    if (index > -1) {
      // Remove day if already selected
      this.selectedDays.splice(index, 1);
    } else {
      // Add day if not selected
      this.selectedDays.push(dayValue);
    }

    // Update schedule
    this.updateScheduleFromUI();
  }

  getScheduleDescription(): string {
    if (!this.currentJob.schedule) {
      return 'No configurado';
    }

    try {
      const parts = this.currentJob.schedule.split(' ');
      if (parts.length !== 5) {
        return this.currentJob.schedule; // Return raw if can't parse
      }

      const [minute, hour, , , dayOfWeek] = parts;
      const time = `${hour}:${minute}`;

      // Parse day of week
      if (dayOfWeek === '*') {
        return `Todos los días a las ${time}`;
      }

      // Check if it's a range (1-5) or specific days (1,2,3)
      if (dayOfWeek.includes('-')) {
        const [start, end] = dayOfWeek.split('-').map(Number);
        if (start === 1 && end === 5) {
          return `Lunes a Viernes a las ${time}`;
        }
        return `Días ${start} a ${end} a las ${time}`;
      }

      // Specific days
      const days = dayOfWeek.split(',').map(Number);
      if (days.length === 1) {
        const dayName = this.weekDays.find(d => d.value === days[0])?.label || '';
        return `Cada ${dayName} a las ${time}`;
      }

      const dayNames = days.map((d: number) => this.weekDays.find(wd => wd.value === d)?.label).join(', ');
      return `Cada ${dayNames} a las ${time}`;
    } catch (e) {
      return this.currentJob.schedule; // Return raw if error
    }
  }

  setSchedule(frequency: 'daily' | 'weekdays' | 'weekly', dayOfWeek?: number, hour?: number): void {
    const h = hour || 9; // Default 9 AM
    const cronMinute = '0'; // Siempre en el minuto 0

    let cron = '';

    switch (frequency) {
      case 'daily':
        // Todos los días a las X:00
        cron = `${cronMinute} ${h} * * *`;
        break;
      case 'weekdays':
        // Lunes a viernes (1-5) a las X:00
        cron = `${cronMinute} ${h} * * 1-5`;
        break;
      case 'weekly':
        // Día específico de la semana (1=Lunes, 7=Domingo)
        const dow = dayOfWeek || 1;
        cron = `${cronMinute} ${h} * * ${dow}`;
        break;
    }

    this.currentJob.schedule = cron;
    console.log('🔄 Schedule preset applied:', cron);
    this.cdr.detectChanges();
  }

  newJob(): void {
    this.isEditing = false;
    this.currentJob = this.resetJob();
    this.selectedDays = [1, 2, 3, 4, 5]; // Default: Lunes a Viernes
    this.selectedTime = '09:00'; // Default: 9 AM
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
        // Parse CRON to populate UI
        this.parseCronToUI(res.schedule);
        this.showEditor = true;
      },
      error: (e) => {
        console.error('Error loading job:', e);
        const errorMsg = e.error?.detail || e.message || 'Error desconocido';
        alert(`Error al cargar configuración: ${errorMsg}\n\nID: ${job.id}`);
      }
    });
  }

  private parseCronToUI(cron: string): void {
    if (!cron) {
      this.selectedDays = [1, 2, 3, 4, 5];
      this.selectedTime = '09:00';
      return;
    }

    try {
      const parts = cron.split(' ');
      if (parts.length !== 5) return;

      const [minute, hour, , , dayOfWeek] = parts;

      // Set time
      this.selectedTime = `${hour.padStart(2, '0')}:${minute.padStart(2, '0')}`;

      // Parse days
      if (dayOfWeek === '*') {
        this.selectedDays = [0, 1, 2, 3, 4, 5, 6]; // All days
      } else if (dayOfWeek.includes('-')) {
        // Range (1-5)
        const [start, end] = dayOfWeek.split('-').map(Number);
        this.selectedDays = [];
        for (let i = start; i <= end; i++) {
          this.selectedDays.push(i);
        }
      } else {
        // Specific days (1,2,3)
        this.selectedDays = dayOfWeek.split(',').map(Number);
      }
    } catch (e) {
      console.error('Error parsing CRON:', e);
      this.selectedDays = [1, 2, 3, 4, 5];
      this.selectedTime = '09:00';
    }
  }

  saveJob(): void {
    // Validation: name and source_folder_id are required
    if (!this.currentJob.name || this.currentJob.name.trim() === '') {
      alert('El nombre descriptivo es obligatorio');
      return;
    }
    if (!this.currentJob.source_folder_id || this.currentJob.source_folder_id.trim() === '') {
      alert('La carpeta de origen es obligatoria');
      return;
    }

    // Clean UI-only fields before sending to backend
    const jobPayload = {
      id: this.currentJob.id,
      name: this.currentJob.name.trim(),
      description: this.currentJob.description,
      active: this.currentJob.active,
      trigger_type: this.currentJob.trigger_type,
      schedule: this.currentJob.schedule,
      source_folder_id: this.currentJob.source_folder_id,
      target_folder_names: this.currentJob.target_folder_names,
      agent_config: this.currentJob.agent_config
    };

    const action = this.isEditing ?
      this.apiService.updateJob(this.currentJob.id, jobPayload) :
      this.apiService.createJob(jobPayload);

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
        console.error('Error status:', e.status);
        console.error('Error body:', e.error);
        const errorMsg = e.error?.detail || e.error?.message || JSON.stringify(e.error) || e.message || 'Error desconocido';
        alert(`Error al guardar: ${errorMsg}\n\n${this.isEditing ? 'Acción: Actualizar' : 'Acción: Crear'}\nID: ${this.currentJob.id || 'N/A'}\n\nStatus: ${e.status}`);
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
