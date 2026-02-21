import { Routes } from '@angular/router';

export const routes: Routes = [
    {path: '', redirectTo:'homepage', pathMatch: 'full' },
    { path: 'homepage', loadComponent: () => import('./homepage/homepage.component').then((component) => component.HomepageComponent) },
    // { path: 'voice-assistant', loadChildren: () => import('./voice-assistant/voice-assistant.component').then((child) => child.VoiceAssistantComponent) }
    { path : 'login', loadComponent: () => import('./login/login.component').then((component) => component.LoginComponent)},
    { path : 'register', loadComponent: () => import('./register/register.component').then((component) => component.RegisterComponent)},
    { path: 'voice-assistant', loadComponent: () => import('./voice-assistant/voice-assistant.component').then((component) => component.VoiceAssistantComponent) }

];
