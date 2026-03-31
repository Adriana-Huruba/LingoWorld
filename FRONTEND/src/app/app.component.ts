import { Component, inject } from '@angular/core';
import { Router, RouterOutlet } from '@angular/router';
import { NavbarComponent } from './pages/navbar/navbar.component';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, NavbarComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})

export class AppComponent {
  title = 'lingoworld';
//   constructor(private router: Router) {}

//   shouldShowNavbar(): boolean {
//     const hiddenRoutes = ['/login', '/register'];
//     return !hiddenRoutes.includes(this.router.url);
// }
}

