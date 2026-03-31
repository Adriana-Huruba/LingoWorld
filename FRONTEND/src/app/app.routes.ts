import { Routes } from '@angular/router';

export const routes: Routes = [
    { path: '', redirectTo:'homepage', pathMatch: 'full' },
    { path: 'homepage', loadComponent: () => import('./pages/homepage/homepage.component').then((component) => component.HomepageComponent) },
    // { path: 'voice-assistant', loadChildren: () => import('./pages/voice-assistant/voice-assistant.component').then((child) => child.VoiceAssistantComponent) }
    { path : 'login', loadComponent: () => import('./pages/login/login.component').then((component) => component.LoginComponent)},
    { path : 'register', loadComponent: () => import('./pages/register/register.component').then((component) => component.RegisterComponent)},
    { path: 'quiz', loadComponent: () => import('./pages/quiz/quiz.component').then((component) => component.QuizComponent)},
    { path: 'voice-assistant', loadComponent: () => import('./pages/voice-assistant/voice-assistant.component').then((component) => component.VoiceAssistantComponent) },
    { path: 'my-vocabulary', loadComponent: () => import('./pages/my-vocabulary/my-vocabulary.component').then((component) => component.MyVocabularyComponent)},
    { path: 'generator', loadComponent: () => import('./pages/generator/generator.component').then((component) => component.GeneratorComponent) }
];
