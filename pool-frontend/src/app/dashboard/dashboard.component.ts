import { Component } from '@angular/core';
import { map } from 'rxjs/operators';
import { Breakpoints, BreakpointObserver } from '@angular/cdk/layout';
import { HttpClient } from '@angular/common/http';
import ConfigJson from '../../assets/config.json';
import PoolLogsJson from '../../assets/poollogs.json';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent {
  config: any = ConfigJson;
  poolLogs: any = PoolLogsJson;
  balances: any = [];
  displayedHistoryColumns = ['date', 'userPaid', 'rewards'];
  displayedBalanceColumns = ['address', 'pending', 'rewards'];

  /** Based on the screen size, switch from standard to one column per row */
  cards = this.breakpointObserver.observe(Breakpoints.Handset).pipe(
    map(({ matches }) => {
      if (matches) {
        return {
          s1: { cols: 2, rows: 1 },
          s2: { cols: 2, rows: 1 },
          s3: { cols: 2, rows: 1 },
          history: { cols: 2, rows: 1 },
          balances: { cols: 2, rows: 1 },
        };
      }

      return {
        s1: { cols: 1, rows: 1 },
        s2: { cols: 1, rows: 1 },
        s3: { cols: 1, rows: 1 },
        history: { cols: 1, rows: 1 },
        balances: { cols: 1, rows: 1 },
      };
    })
  );

  constructor(
    private breakpointObserver: BreakpointObserver
  ) {
    this.poolLogs.history.reverse();

    for (let k in this.poolLogs.pending) {
      let c = {
        address: k,
        pending: this.poolLogs.pending[k],
        rewards: 0
      };

      if (k in this.poolLogs.paid)
        c.rewards = this.poolLogs.paid[k];

      this.balances.push(c);
    }

    for (let k in this.poolLogs.paid) {
      if (k in this.poolLogs.pending)
        continue;

      let c = {
        address: k,
        rewards: this.poolLogs.paid[k],
        pending: 0
      };

      this.balances.push(c);
    }
  }
}
