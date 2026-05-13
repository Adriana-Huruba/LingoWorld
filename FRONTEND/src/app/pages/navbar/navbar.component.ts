import { Component, inject } from '@angular/core';
import { AuthService } from '../../core/services/auth.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [],
  templateUrl: './navbar.component.html',
  styleUrl: './navbar.component.scss'
})

export class NavbarComponent {
  public authService = inject(AuthService);
  router: Router = inject(Router);

  isUserDropdownOpen = false;
  isDropdownOpen = false;

  languageOptions = [
    { id: 'en', name: 'English', flag: 'uk-flag.svg' },
    { id: 'ro', name: 'Română', flag: 'romania-flag.svg' },
    { id: 'fr', name: 'Français', flag: 'france-flag.svg' },
    { id: 'es', name: 'Español', flag: 'spain-flag.svg' }
  ];

  NavigateToDashboard() {
    this.router.navigate(['/']);
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
    this.router.navigate(['/login']);
  }

  toggleDropdown() {
    this.isDropdownOpen = !this.isDropdownOpen;
  }

  selectLanguage(lang: string) {
    this.authService.updateTargetLanguage(lang);
    this.isDropdownOpen = false;
  }
}
