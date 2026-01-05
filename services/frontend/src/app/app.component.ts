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
    <div class="app-container">
      <!-- Login View -->
      <div *ngIf="!(user$ | async)" class="login-container">
        <div class="login-card">
          <h1>📂 Renovador de Carpetas</h1>
          <p>Renombra archivos automáticamente usando IA</p>
          <div #googleButton class="google-button"></div>
        </div>
      </div>

      <!-- Dashboard View -->
      <div *ngIf="user$ | async as user" class="dashboard-container">
        <header class="header">
          <h1>📂 Renovador de Carpetas</h1>
          <div class="user-info">
            <img [src]="user.picture" alt="User" class="user-avatar">
            <span>{{user.email}}</span>
            <button (click)="signOut()" class="btn-secondary">Cerrar Sesión</button>
          </div>
        </header>

        <main class="main-content">
          <div class="job-form-card">
            <h2>Procesar Carpeta</h2>
            <form (ngSubmit)="submitJob()">
              <div class="form-group">
                <label for="folderId">ID de Carpeta de Google Drive</label>
                <input 
                  type="text" 
                  id="folderId" 
                  [(ngModel)]="folderId" 
                  name="folderId"
                  placeholder="Ej: 1ABC-123xyz..."
                  required>
              </div>
              
              <div class="form-group">
                <label for="jobType">Tipo de Trabajo</label>
                <select id="jobType" [(ngModel)]="jobType" name="jobType">
                  <option value="generic">Genérico</option>
                  <option value="invoice">Facturas</option>
                  <option value="report">Reportes</option>
                </select>
              </div>

              <button type="submit" class="btn-primary" [disabled]="isSubmitting">
                {{isSubmitting ? 'Procesando...' : 'Procesar Carpeta'}}
              </button>
            </form>

            <div *ngIf="result" [class]="resultClass" class="result-message">
              {{result}}
            </div>
          </div>
        </main>
      </div>
    </div>
  `,
  styles: [`
    .app-container {
      min-height: 100vh;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }

    .login-container {
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
    }

    .login-card {
      background: white;
      padding: 3rem;
      border-radius: 12px;
      box-shadow: 0 10px 40px rgba(0,0,0,0.2);
      text-align: center;
      max-width: 400px;
    }

    .login-card h1 {
      color: #667eea;
      margin-bottom: 1rem;
    }

    .login-card p {
      color: #666;
      margin-bottom: 2rem;
    }

    .google-button {
      display: flex;
      justify-content: center;
    }

    .dashboard-container {
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }

    .header {
      background: white;
      padding: 1rem 2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .header h1 {
      color: #667eea;
      margin: 0;
      font-size: 1.5rem;
    }

    .user-info {
      display: flex;
      align-items: center;
      gap: 1rem;
    }

    .user-avatar {
      width: 40px;
      height: 40px;
      border-radius: 50%;
    }

    .main-content {
      flex: 1;
      padding: 2rem;
      display: flex;
      justify-content: center;
      align-items: flex-start;
    }

    .job-form-card {
      background: white;
      padding: 2rem;
      border-radius: 12px;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
      width: 100%;
      max-width: 600px;
    }

    .job-form-card h2 {
      color: #333;
      margin-bottom: 1.5rem;
    }

    .form-group {
      margin-bottom: 1.5rem;
    }

    .form-group label {
      display: block;
      margin-bottom: 0.5rem;
      color: #555;
      font-weight: 500;
    }

    .form-group input,
    .form-group select {
      width: 100%;
      padding: 0.75rem;
      border: 1px solid #ddd;
      border-radius: 6px;
      font-size: 1rem;
      box-sizing: border-box;
    }

    .form-group input:focus,
    .form-group select:focus {
      outline: none;
      border-color: #667eea;
    }

    .btn-primary {
      background: #667eea;
      color: white;
      border: none;
      padding: 0.75rem 2rem;
      border-radius: 6px;
      font-size: 1rem;
      cursor: pointer;
      width: 100%;
      transition: background 0.3s;
    }

    .btn-primary:hover:not(:disabled) {
      background: #5568d3;
    }

    .btn-primary:disabled {
      background: #ccc;
      cursor: not-allowed;
    }

    .btn-secondary {
      background: #ef4444;
      color: white;
      border: none;
      padding: 0.5rem 1rem;
      border-radius: 6px;
      cursor: pointer;
      transition: background 0.3s;
    }

    .btn-secondary:hover {
      background: #dc2626;
    }

    .result-message {
      margin-top: 1rem;
      padding: 1rem;
      border-radius: 6px;
      font-weight: 500;
    }

    .success {
      background: #d1fae5;
      color: #065f46;
      border: 1px solid #6ee7b7;
    }

    .error {
      background: #fee2e2;
      color: #991b1b;
      border: 1px solid #fecaca;
    }
  `]
})
export class AppComponent implements OnInit, AfterViewInit {
  @ViewChild('googleButton') googleButton!: ElementRef;

  user$: Observable<User | null>;
  folderId = '';
  jobType = 'generic';
  isSubmitting = false;
  result = '';
  resultClass = '';

  constructor(
    private authService: AuthService,
    private apiService: ApiService,
    private cdr: ChangeDetectorRef
  ) {
    this.user$ = this.authService.user$;
  }

  ngOnInit(): void {
    this.authService.initializeGoogleSignIn();

    // Subscribe to user changes to handle re-rendering of login button
    this.user$.subscribe(user => {
      console.log('👤 User state changed:', user ? user.email : 'Logged out');
      if (!user) {
        // Use a small timeout to ensure DOM is ready after logout
        setTimeout(() => this.initializeLoginButton(), 100);
      }
    });
  }

  ngAfterViewInit(): void {
    setTimeout(() => this.initializeLoginButton(), 100);
  }

  initializeLoginButton(): void {
    if (this.googleButton && !this.authService.isAuthenticated()) {
      console.log('🔘 Rendering Google Sign-In button...');
      this.authService.renderButton(this.googleButton.nativeElement);
      this.cdr.detectChanges();
    }
  }

  submitJob(): void {
    if (!this.folderId) {
      this.showError('Por favor ingresa un ID de carpeta');
      return;
    }

    console.log('🚀 Iniciando submitJob...', { folderId: this.folderId, jobType: this.jobType });
    this.isSubmitting = true;
    this.result = '';
    this.cdr.detectChanges();

    const job: Job = {
      folder_id: this.folderId,
      job_type: this.jobType
    };

    this.apiService.submitJob(job)
      .subscribe({
        next: (response) => {
          console.log('✅ Respuesta exitosa recibida:', response);
          this.showSuccess(`✅ ${response.message || 'Tarea creada exitosamente'}`);
          this.folderId = '';
        },
        error: (error) => {
          console.error('❌ Error en submitJob:', error);
          const message = error.error?.detail || error.message || 'Error al procesar la solicitud';
          this.showError(`❌ ${message}`);
        },
        complete: () => {
          console.log('🏁 Observable completado');
          this.isSubmitting = false;
          this.cdr.detectChanges();

          // Auto-clear result after 10 seconds (extended)
          setTimeout(() => {
            if (!this.isSubmitting) {
              this.result = '';
              this.resultClass = '';
              this.cdr.detectChanges();
            }
          }, 10000);
        }
      });
  }

  showSuccess(message: string): void {
    this.result = message;
    this.resultClass = 'success';
  }

  showError(message: string): void {
    this.result = message;
    this.resultClass = 'error';
  }

  signOut(): void {
    this.authService.signOut();
    // Force change detection to update UI immediately
    this.cdr.detectChanges();
  }
}
