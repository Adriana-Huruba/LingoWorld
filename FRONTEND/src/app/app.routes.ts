import { Routes } from '@angular/router';
import { roleGuard } from './core/guards/auth.guard';

export const routes: Routes = [
    { path: '', redirectTo: 'homepage', pathMatch: 'full' },

    { path: 'homepage',  loadComponent: () => import('./pages/homepage/homepage.component').then(c => c.HomepageComponent) },
    { path: 'login',     loadComponent: () => import('./pages/login/login.component').then(c => c.LoginComponent) },
    { path: 'register',  loadComponent: () => import('./pages/register/register.component').then(c => c.RegisterComponent) },

    { path: 'quiz', canActivate: [roleGuard], data: { roles: ['adult_learner'] },
      loadComponent: () => import('./pages/quiz/quiz.component').then(c => c.QuizComponent) },

    { path: 'class/:id', canActivate: [roleGuard], data: { roles: ['student'] },
      loadComponent: () => import('./pages/student/student-classroom/student-classroom.component').then(c => c.StudentClassroomComponent) },

    { path: 'classroom/:id', canActivate: [roleGuard], data: { roles: ['teacher'] },
      loadComponent: () => import('./pages/teacher/classroom/classroom.component').then(c => c.ClassroomComponent) },

    { path: 'generator', canActivate: [roleGuard], data: { roles: ['adult_learner'] },
      loadComponent: () => import('./pages/generator/generator.component').then(c => c.GeneratorComponent) },

    { path: 'my-vocabulary', canActivate: [roleGuard], data: { roles: ['student', 'adult_learner'] },
      loadComponent: () => import('./pages/my-vocabulary/my-vocabulary.component').then(c => c.MyVocabularyComponent) },
    { path: 'progress', canActivate: [roleGuard], data: { roles: ['student', 'adult_learner'] },
      loadComponent: () => import('./pages/progress/progress.component').then(c => c.ProgressComponent) },


    { path: 'settings', canActivate: [roleGuard], data: { roles: ['student', 'teacher', 'adult_learner'] },
      loadComponent: () => import('./pages/settings/settings.component').then(c => c.SettingsComponent) },

    { path: '**', redirectTo: 'login' },
];
