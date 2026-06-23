import { Component, ElementRef, inject, HostListener, OnInit, effect } from '@angular/core';
import { AuthService } from '../../core/services/auth.service';
import { Router } from '@angular/router';
import { ExerciseService } from '../../core/services/exercise.service';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [],
  templateUrl: './navbar.component.html',
  styleUrl: './navbar.component.scss'
})

export class NavbarComponent{
  public authService = inject(AuthService);
  exerciseService = inject(ExerciseService);
  eRef = inject(ElementRef);
  router: Router = inject(Router);

  isUserDropdownOpen = false;
  isDropdownOpen = false;
  userRole = this.authService.userRole;
  userXp = this.authService.userXp;
  userElo = this.authService.userElo;

  languageOptions = [
    { id: 'en', name: 'English', flag: 'uk-flag.svg' },
    { id: 'ro', name: 'Română', flag: 'romania-flag.svg' },
    { id: 'fr', name: 'Français', flag: 'france-flag.svg' },
    { id: 'es', name: 'Español', flag: 'spain-flag.svg' }
  ];
  
  constructor(){
    effect(() => {
      const loggedIn = this.authService.isLoggedIn();
      const role = this.authService.userRole();

      if (loggedIn && role !== 'teacher') {
        this.loadUserStats();
      }
    });
  }

  loadUserStats(): void {
    const userId = this.authService.userId;
    const lang = this.authService.targetLanguageFull;

    this.exerciseService.getUserProgress(userId, lang).subscribe({
      next: (data) => {
        this.authService.userXp.set(data.xp);
        this.authService.userElo.set(data.current_elo);
      }
    });
  }

  @HostListener('document:click', ['$event'])
  clickout(event: Event) {
    if (!this.eRef.nativeElement.contains(event.target)) {
      this.isDropdownOpen = false;
      this.isUserDropdownOpen = false;
    }
  }

  navigateToDashboard() {
    this.isUserDropdownOpen = false;
    this.router.navigate(['/']);
  }

  navigateToVocabulary() {
    this.router.navigate(['/my-vocabulary']);
  }

  navigateToProgress() {
    this.isUserDropdownOpen = false;
    this.router.navigate(['/progress']);
  }

  navigateToSettings() {
    this.isUserDropdownOpen = false;
    this.router.navigate(['/settings']);
  }
  
  get targetLanguage() {
    return this.authService.targetLanguage();
  }

  get currentFlag() {
    return this.languageOptions.find(lang => lang.id === this.targetLanguage)?.flag || 'uk-flag.svg';
  }

  get currentLanguageName() {
    return this.languageOptions.find(lang => lang.id === this.targetLanguage)?.name || 'English';
  }

  get otherLanguages() {
    return this.languageOptions.filter(lang => lang.id !== this.targetLanguage);
  }

  logout() {
    this.authService.logout();
    this.isUserDropdownOpen = false;
    this.router.navigate(['/login']);
  }

  toggleUserDropdown(event: Event) {
    event.stopPropagation();
    this.isUserDropdownOpen = !this.isUserDropdownOpen;
    this.isDropdownOpen = false;
  }

  toggleDropdown(event: Event) {
    event.stopPropagation();
    this.isDropdownOpen = !this.isDropdownOpen;
    this.isUserDropdownOpen = false;
  }

  selectLanguage(lang: string) {
    this.authService.updateTargetLanguage(lang);
    this.isDropdownOpen = false;
  }
}
