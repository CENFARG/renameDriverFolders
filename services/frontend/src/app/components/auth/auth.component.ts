import { Component, OnInit, AfterViewInit, OnDestroy, ElementRef, ViewChild, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Observable } from 'rxjs';
import { AuthService } from '../../services/auth.service';

declare const google: any;

@Component({
  selector: 'app-auth',
  standalone: true,
  imports: [CommonModule],
  template: `
    <!-- Login View -->
    <div *ngIf="!(user$ | async)" class="max-w-md mx-auto mt-20">
      <div class="bg-white p-10 rounded-2xl shadow-2xl border border-slate-100 text-center">
        <img src="/logo_cutignola.png" alt="Estudio Cutignola" class="h-16 mx-auto mb-6">
        <h2 class="text-2xl font-bold text-slate-800 mb-2">Bienvenido</h2>
        <p class="text-slate-500 mb-8">Accede con tu cuenta autorizada para gestionar el procesamiento de archivos.</p>
        <div #googleButton class="flex justify-center"></div>
      </div>
    </div>
  `,
})
export class AuthComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('googleButton') googleButton!: ElementRef;
  user$: Observable<any | null>;

  constructor(
    private authService: AuthService,
    private cdr: ChangeDetectorRef,
  ) {
    this.user$ = this.authService.user$;
  }

  ngOnInit(): void {
    this.authService.initializeGoogleSignIn();
  }

  ngAfterViewInit(): void {
    this.initializeLoginButton();
  }

  ngOnDestroy(): void {}

  initializeLoginButton(): void {
    setTimeout(() => {
      if (this.googleButton?.nativeElement) {
        this.authService.renderButton(this.googleButton.nativeElement);
      }
    }, 500);
  }
}
