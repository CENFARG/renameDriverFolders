import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Observable } from 'rxjs';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-user-header',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div *ngIf="user$ | async as user" class="flex items-center gap-4">
      <div class="hidden md:flex flex-col items-end">
        <span class="text-sm font-semibold text-slate-700">{{ user.name }}</span>
        <span class="text-xs text-slate-500">{{ user.email }}</span>
      </div>
      <img [src]="user.picture" alt="User" class="w-10 h-10 rounded-full border border-slate-200">
      <button (click)="toggleTheme()"
        class="text-slate-500 hover:text-blue-500 transition-colors"
        title="Cambiar tema">
        <span class="text-xl">{{ isDark ? '&#127769;' : '&#9728;&#65039;' }}</span>
      </button>
      <button (click)="signOut()" class="text-slate-500 hover:text-red-500 transition-colors">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24"
          stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
        </svg>
      </button>
    </div>
  `,
})
export class UserHeaderComponent implements OnInit, OnDestroy {
  user$: Observable<any | null>;
  isDark = true;

  constructor(
    private authService: AuthService,
    private cdr: ChangeDetectorRef,
  ) {
    this.user$ = this.authService.user$;
  }

  ngOnInit(): void {
    this.initializeTheme();
  }

  ngOnDestroy(): void {}

  signOut(): void {
    this.authService.signOut();
  }

  toggleTheme(): void {
    this.isDark = !this.isDark;
    localStorage.setItem('theme', this.isDark ? 'dark' : 'light');
    this.applyTheme();
  }

  private initializeTheme(): void {
    const savedTheme = localStorage.getItem('theme');
    this.isDark = savedTheme !== 'light';
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
}
