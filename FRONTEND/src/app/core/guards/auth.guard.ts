import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const roleGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (!authService.isLoggedIn()) {
    return router.parseUrl('/login');
  }

  const allowedRoles = route.data['roles'] as Array<string>;
  const currentUserRole = authService.userRole();

  if (allowedRoles && !allowedRoles.includes(currentUserRole || '')) {
    console.error('Acces denied for {currentUserRole} role', currentUserRole);
    return router.parseUrl('/');
  }

  return true;
};