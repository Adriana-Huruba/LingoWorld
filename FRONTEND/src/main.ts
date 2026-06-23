import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { AppComponent } from './app/app.component';
import {
  Chart,
  LineController, BarController,
  LineElement, BarElement, PointElement,
  CategoryScale, LinearScale,
  Filler, Tooltip, Legend
} from 'chart.js';

Chart.register(
  LineController, BarController,
  LineElement, BarElement, PointElement,
  CategoryScale, LinearScale,
  Filler, Tooltip, Legend
);

bootstrapApplication(AppComponent, appConfig)
  .catch((err) => console.error(err));
