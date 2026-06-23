import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../core/services/auth.service';
import { ExerciseService } from '../../core/services/exercise.service';
import { ChartConfiguration, ChartData, ChartOptions } from 'chart.js';
import { BaseChartDirective } from 'ng2-charts';

@Component({
  selector: 'app-progress',
  standalone: true,
  imports: [CommonModule, BaseChartDirective],
  templateUrl: './progress.component.html',
  styleUrl: './progress.component.scss'
})

export class ProgressComponent implements OnInit {
  authService = inject(AuthService);
  private exerciseService = inject(ExerciseService);

  selectedLanguage = this.authService.selectedLanguage;
  isLoading = true;
  error = false;

  currentElo = 0;
  currentLevel = '';
  totalResponses = 0;
  xp = 0;

  eloChartData: ChartData<'line'> = { labels: [], datasets: [] };
  eloChartOptions: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: { callbacks: { label: (ctx) => `ELO: ${ctx.parsed.y}` } }
    },
    scales: {
      x: { grid: { display: false } },
      y: { beginAtZero: false, ticks: { stepSize: 50 } }
    }
  };

  accuracyChartData: ChartData<'bar'> = { labels: [], datasets: [] };
  accuracyChartOptions: ChartOptions<'bar'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: true, position: 'top' } },
    scales: {
      x: { grid: { display: false } },
      y: { beginAtZero: true }
    }
  };

  ngOnInit(): void {
    this.loadProgress();
  }

  loadProgress(): void {
    const userId = this.authService.userId;
    const lang = this.authService.targetLanguageFull;

    this.exerciseService.getUserProgress(userId, lang).subscribe({
      next: (data) => {
        this.currentElo = data.current_elo;
        this.currentLevel = data.current_level;
        this.totalResponses = data.total_responses;
        this.xp = data.xp;

        this.eloChartData = {
          labels: data.elo_history.map((d: any) => this.formatDay(d.day)),
          datasets: [{
            data: data.elo_history.map((d: any) => d.elo),
            label: 'ELO',
            borderColor: '#1890ff',
            backgroundColor: 'rgba(24,144,255,0.08)',
            pointBackgroundColor: '#1890ff',
            fill: true,
            tension: 0.3
          }]
        };

        this.accuracyChartData = {
          labels: data.accuracy_history.map((d: any) => this.formatDay(d.day)),
          datasets: [
            {
              data: data.accuracy_history.map((d: any) => d.correct),
              label: 'Correct',
              backgroundColor: 'rgba(82,196,26,0.7)',
              borderRadius: 4,
            } as any,
            {
              data: data.accuracy_history.map((d: any) => d.total),
              label: 'Total',
              backgroundColor: 'rgba(217,217,217,0.7)',
              borderRadius: 4,
            } as any
          ]
        };

        this.isLoading = false;
      },
      error: () => {
        this.isLoading = false;
        this.error = true;
      }
    });
  }

  private formatDay(dateStr: string): string {
    const d = new Date(dateStr);
    return `${d.getDate()}/${d.getMonth() + 1}`;
  }

  getLevelColor(level: string): string {
    const map: Record<string, string> = {
      A1: '#bfbfbf', A2: '#8c8c8c',
      B1: '#1890ff', B2: '#096dd9',
      C1: '#52c41a', C2: '#237804'
    };
    return map[level] ?? '#1890ff';
  }
}