import { useEffect, useState } from "react";
import { provider } from "@/data/providers";
import RiskBadge from "@/components/trading/RiskBadge";
import * as XLSX from "xlsx";

export default function ProviderPerformance() {
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
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
        Provider Performance Analysis
      </h1>

      {/* Risk Score Breakdown */}

      <div
        className="
grid
grid-cols-1
md:grid-cols-5
gap-5
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

      {/* Provider Performance Table */}

      <div
        className="
rounded-xl
border
bg-white
dark:bg-gray-800
overflow-hidden
"
      >
        <table className="w-full">
          <thead>
            <tr className="border-b text-left">
              <th className="p-4">Provider</th>

              <th>Profit (Max Pips)</th>

              <th>Loss (Max Pips)</th>

              <th>Result Pips</th>

              <th>Loss Streak</th>
            </tr>
          </thead>

          <tbody>
            <tr className="border-b">
              <td className="p-4 font-medium text-gray-900 dark:text-white">
                {provider.name}
              </td>

              <td>{performance.profitMax}</td>

              <td>{performance.lossMax}</td>

              <td>{performance.result}</td>

              <td>{performance.lossStreak}</td>

              <td>
                <RiskBadge level={provider.riskLevel} />
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Provider Detail */}

      <div
        className="
rounded-xl
border
bg-white
dark:bg-gray-800
p-5
"
      >
        <h3
          className="
mb-4
font-semibold
text-gray-900
dark:text-white
"
        >
          Provider Details
        </h3>

        <div
          className="
grid
grid-cols-2
md:grid-cols-4
gap-5
"
        >
          <div>
            <p className="text-gray-500">Strategy</p>

            <p className="font-semibold">{provider.strategy}</p>
          </div>

          <div>
            <p className="text-gray-500">Profit Factor</p>

            <p className="font-semibold">{provider.profitFactor}</p>
          </div>

          <div>
            <p className="text-gray-500">Recovery Factor</p>

            <p className="font-semibold">{provider.recoveryFactor}</p>
          </div>

          <div>
            <p className="text-gray-500">Monthly Return</p>

            <p className="font-semibold text-green-500">
              +{provider.monthlyReturn}%
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
