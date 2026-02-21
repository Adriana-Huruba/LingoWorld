import { Component } from '@angular/core';
import { NzBreadCrumbModule } from 'ng-zorro-antd/breadcrumb';
import { NzIconModule } from 'ng-zorro-antd/icon';
import { NzLayoutModule } from 'ng-zorro-antd/layout';
import { NzMenuModule } from 'ng-zorro-antd/menu';
import { NavbarVoiceComponent } from '../navbar-voice/navbar-voice.component';

@Component({
  selector: 'app-voice-assistant',
  standalone: true,
  imports: [NzBreadCrumbModule, NzIconModule, NzMenuModule, NzLayoutModule, NavbarVoiceComponent, NavbarVoiceComponent],
  templateUrl: './voice-assistant.component.html',
  styleUrl: './voice-assistant.component.scss'
})

export class VoiceAssistantComponent {

  toggleRecording() {
    throw new Error('Method not implemented.');
  }
  isCollapsed = false;
  protected readonly date = new Date();
}
