import { Component, ElementRef, inject, HostListener } from '@angular/core';
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
  eRef = inject(ElementRef);
  router: Router = inject(Router);

  isUserDropdownOpen = false;
  isDropdownOpen = false;

  languageOptions = [
    { id: 'en', name: 'English', flag: 'uk-flag.svg' },
    { id: 'ro', name: 'Română', flag: 'romania-flag.svg' },
    { id: 'fr', name: 'Français', flag: 'france-flag.svg' },
    { id: 'es', name: 'Español', flag: 'spain-flag.svg' }
  ];

  @HostListener('document:click', ['$event'])
  clickout(event: Event) {
    if (!this.eRef.nativeElement.contains(event.target)) {
      this.isDropdownOpen = false;
      this.isUserDropdownOpen = false;
    }
  }

  NavigateToDashboard() {
    this.router.navigate(['/']);
  }

  NavigateToVocabulary() {
    this.router.navigate(['/my-vocabulary']);
  }

  NavigateToProgres() {
    this.router.navigate(['/progress']); //TODO
  }
  NavigateToSettings() {
    this.router.navigate(['/settings']); //TODO
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
