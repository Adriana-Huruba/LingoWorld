import { Component } from '@angular/core';

@Component({
  selector: 'app-navbar',
  imports: [],
  templateUrl: './navbar.component.html',
  styleUrl: './navbar.component.scss'
})

export class NavbarComponent {
  
  isUserDropdownOpen: boolean = false;
  isDropdownOpen: boolean = false;
  currentFlag = 'assets/uk-flag.svg';

  logout() {
    window.location.href= '/login';
  }

  isUserLoggedIn(): boolean {
    throw new Error('Method not implemented.');
  }
  toggleDropdown() {
    this.isDropdownOpen = !this.isDropdownOpen;
  }

  languages : { [key: string]: string }= {
    'RO':'romania-flag.svg',
    'FR': 'france-flag.svg',
    'ES': 'spain-flag.svg',
    'UK': 'assets/uk-flag.svg'
  };

  selectLanguage(lang: string) {
    console.log('Selected language:', lang);

    this.currentFlag = this.languages[lang];
    this.isDropdownOpen = false;
  }
}
