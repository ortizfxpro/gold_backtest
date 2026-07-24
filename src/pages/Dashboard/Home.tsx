import KPICard from "@/components/trading/KPICard";

import ProviderTable from "@/components/trading/ProviderTable";

import PerformanceChart from "@/components/trading/PerformanceChart";

export default function Dashboard() {
  return (
    <div className="space-y-6">
      <h1
        className="
text-2xl
font-bold
"
      >
        Trading System Dashboard
      </h1>

      <div
        className="
grid
grid-cols-1
gap-5
md:grid-cols-3
"
      >
        <KPICard
          title="Total Return"

          value="+9.4%"

          change="July Performance"
        />

        <KPICard
          title="Profit Factor"

          value="1.76"
        />

        <KPICard
          title="Recovery Factor"

          value="3.7"
        />

        <KPICard
          title="Max Drawdown"

          value="-6.1%"
        />

        <KPICard
          title="Win Rate"

          value="64%"
        />

        <KPICard
          title="Risk Score"

          value="LOW"
        />
      </div>

      <PerformanceChart />

      <div>
        <h2
          className="
mb-4
text-xl
font-semibold
"
        >
          Provider Ranking
        </h2>

        <ProviderTable />
      </div>
    </div>
  );
}
