import { useEffect, useState } from "react";

import ProviderTable from "@/components/trading/ProviderTable";

import PerformanceChart from "@/components/trading/PerformanceChart";
import * as XLSX from "xlsx";

export default function Dashboard() {
  const [performance, setPerformance] = useState({
    totalSignals: 0,
    profitMax: 0,
    lossMax: 0,
    result: 0,
    lossStreak: 0,
  });
  useEffect(() => {
    fetch("/signal_history_july.xlsx?t=" + Date.now())
      .then((res) => res.arrayBuffer())
      .then((buffer) => {
        const workbook = XLSX.read(buffer);

        console.log("Sheets:", workbook.SheetNames);

        const resultSheet = workbook.Sheets["Result"];

        console.log("Result sheet:", resultSheet);

        const resultData = {
          totalSignals: resultSheet["E7"]?.v || 0,
          profitMax: resultSheet["F7"]?.v || 0,
          lossMax: resultSheet["G7"]?.v || 0,
          result: resultSheet["H7"]?.v || 0,
          lossStreak: resultSheet["I7"]?.v || 0,
        };

        console.log("Performance data:", resultData);

        setPerformance(resultData);
      })
      .catch((error) => {
        console.error("Excel loading error:", error);
      });
  }, []);

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
md:grid-cols-5
"
      >
        <div
          className="
rounded-xl
border
p-5
bg-white
dark:bg-gray-800
text-center

"
        >
          <p className="text-gray-500">Total Signals</p>

          <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
            {performance.totalSignals}
          </h2>
        </div>

        <div
          className="
rounded-xl
border
p-5
bg-white
dark:bg-gray-800
text-center

"
        >
          <p className="text-gray-500">Profit (Max)</p>

          <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
            {performance.profitMax} pips
          </h2>
        </div>

        <div
          className="
rounded-xl
border
p-5
bg-white
dark:bg-gray-800
text-center

"
        >
          <p className="text-gray-500">Loss (Max)</p>

          <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
            {performance.lossMax} pips
          </h2>
        </div>

        <div
          className="
rounded-xl
border
p-5
bg-white
dark:bg-gray-800
text-center

"
        >
          <p className="text-gray-500">Result</p>

          <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
            {performance.result} pips
          </h2>
        </div>

        <div
          className="
rounded-xl
border
p-5
bg-white
dark:bg-gray-800
text-center

"
        >
          <p className="text-gray-500">Loss Streak</p>

          <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
            {performance.lossStreak}
          </h2>
        </div>
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
