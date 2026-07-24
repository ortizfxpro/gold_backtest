import { useEffect, useState } from "react";

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

  const [selectedMonth, setSelectedMonth] = useState("July");
  const months = ["All", "July", "June"];

  useEffect(() => {
    // Do not search Excel for "All"
    if (selectedMonth === "All") {
      return;
    }

    fetch("/signal_history_july.xlsx?t=" + Date.now())
      .then((res) => res.arrayBuffer())
      .then((buffer) => {
        const workbook = XLSX.read(buffer);

        const resultSheet = workbook.Sheets["Result"];

        if (!resultSheet) {
          console.error("Result sheet not found");
          return;
        }

        const rows = XLSX.utils.sheet_to_json<any[]>(resultSheet, {
          header: 1,
          defval: "",
        });

        console.log("Excel rows:", rows);

        let targetRow = -1;

        let currentMonth = "";

        for (let i = 0; i < rows.length; i++) {
          const row = rows[i];

          // Save month when column A has value
          if (row[0]) {
            currentMonth = row[0];
          }

          // Find PnL (pips) row
          if (currentMonth === selectedMonth && row[1] === "PnL (pips)") {
            targetRow = i;
            break;
          }
        }

        if (targetRow === -1) {
          console.error("Month data not found:", selectedMonth);
          return;
        }

        const resultData = {
          totalSignals: rows[targetRow][2],
          profitMax: rows[targetRow][3],
          lossMax: rows[targetRow][4],
          result: rows[targetRow][5],
          lossStreak: rows[targetRow][6],
        };

        console.log("Loaded:", selectedMonth, resultData);

        setPerformance(resultData);
      })
      .catch((error) => {
        console.error("Excel loading error:", error);
      });
  }, [selectedMonth]);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Trading System Dashboard</h1>

      <div
        className="
        grid
        grid-cols-1
        gap-5
        md:grid-cols-5
      "
      >
        <KpiCard title="Total Signals" value={performance.totalSignals} />

        <KpiCard title="Profit (Max)" value={`${performance.profitMax} pips`} />

        <KpiCard title="Loss (Max)" value={`${performance.lossMax} pips`} />

        <KpiCard title="Result" value={`${performance.result} pips`} />

        <KpiCard title="Loss Streak" value={performance.lossStreak} />
      </div>

      <select
        value={selectedMonth}
        onChange={(e) => setSelectedMonth(e.target.value)}
        className="
          rounded-lg
          border
          px-3
          py-2
          mb-5
        "
      >
        {months.map((month) => (
          <option key={month}>{month}</option>
        ))}
      </select>

      <PerformanceChart selectedMonth={selectedMonth} />
    </div>
  );
}

function KpiCard({ title, value }: { title: string; value: string | number }) {
  return (
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
      <p className="text-gray-500">{title}</p>

      <h2
        className="
          text-3xl
          font-bold
          text-gray-900
          dark:text-white
        "
      >
        {value}
      </h2>
    </div>
  );
}
