import { Component, inject, OnInit, Signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { NzInputModule } from 'ng-zorro-antd/input';
import { NzButtonModule } from 'ng-zorro-antd/button';
import { NzSelectModule } from 'ng-zorro-antd/select';
import { NzIconModule } from 'ng-zorro-antd/icon';
import { NzMessageService } from 'ng-zorro-antd/message';
import { NzPopconfirmModule } from 'ng-zorro-antd/popconfirm';
import { AuthService } from '../../core/services/auth.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule, FormsModule, NzInputModule, NzButtonModule, NzSelectModule, NzIconModule, NzPopconfirmModule],
  templateUrl: './settings.component.html',
  styleUrl: './settings.component.scss'
})

export class SettingsComponent implements OnInit {
  private authService = inject(AuthService);
  private message = inject(NzMessageService);
  private router = inject(Router);

  userName = '';
  userEmail = '';
  userLevel = '';
  targetLanguage = '';
  role= '';

  ngOnInit() {
    this.userName = this.authService.userName();
    this.userLevel = this.authService.userLevel;
    this.targetLanguage = this.authService.targetLanguageFull;
  }

  saveChanges() {
    this.message.success('Settings saved');
  }

  confirmLogout() {
    this.router.navigate(['/login']);
  }
}
