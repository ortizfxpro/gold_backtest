import { useEffect, useState } from "react";
import Chart from "react-apexcharts";
import type { ApexOptions } from "apexcharts";
import * as XLSX from "xlsx";

interface BacktestData {
  Month: string;
  "Total Signals": number;
  "SL Level": string | number;
  "TP Level": string;
  "Profit (Max)": number;
  "Loss (Max)": number;
  Result: number;
  "Return %": number;
  "Loss Streak": number;
}

export default function BacktestReport() {
  const [data, setData] = useState<BacktestData[]>([]);
  const [selectedMonth, setSelectedMonth] = useState("All");
  useEffect(() => {
    fetch("/backtest_report.xlsx")
      .then((res) => res.arrayBuffer())
      .then((buffer) => {
        const workbook = XLSX.read(buffer);

        const sheet = workbook.Sheets["Result"];

        const rawRows = XLSX.utils.sheet_to_json<any>(sheet, {
          header: 1,
          defval: "",
        });

        let currentMonth = "";

        const cleanRows = rawRows
          .map((row: any[]) => {
            // detect month
            if (
              row.includes("July") ||
              row.includes("June") ||
              row.includes("May")
            ) {
              currentMonth = row.includes("July")
                ? "July"
                : row.includes("June")
                  ? "June"
                  : "May";

              return null;
            }

            // TP column position
            const tpLevel = row[2];

            if (tpLevel && tpLevel.toString().startsWith("TP")) {
              return {
                Month: currentMonth,
                "Total Signals": row[1],
                "TP Level": row[2],
                "SL Level": row[3],
                "Profit (Max)": row[4],
                "Loss (Max)": row[6],
                Result: row[8],
                "Return %": row[9],
                "Loss Streak": row[10],
              };
            }

            return null;
          })
          .filter(Boolean);

        console.log("Clean data:", cleanRows);

        setData(cleanRows as BacktestData[]);
      });
  }, []);

  const months = ["All", ...new Set(data.map((item) => item.Month))];
  const filteredData =
    selectedMonth === "All"
      ? data
      : data.filter((item) => item.Month === selectedMonth);
  const summary =
    selectedMonth === "All"
      ? {
          "Total Signals": filteredData.reduce(
            (sum, item) => sum + Number(item["Total Signals"] || 0),
            0,
          ),

          "Profit (Max)": Math.max(
            ...filteredData.map((item) => Number(item["Profit (Max)"] || 0)),
          ),

          "Loss (Max)": Math.min(
            ...filteredData.map((item) => Number(item["Loss (Max)"] || 0)),
          ),

          Result: filteredData.reduce(
            (sum, item) => sum + Number(item.Result || 0),
            0,
          ),

          "Loss Streak": Math.max(
            ...filteredData.map((item) => Number(item["Loss Streak"] || 0)),
          ),
        }
      : filteredData[0];

  const chartSeries = [
    {
      name: "Profit",
      data: filteredData.map((item) => Number(item["Profit (Max)"] || 0)),
    },
    {
      name: "Loss",
      data: filteredData.map(
        (item) => -Math.abs(Number(item["Loss (Max)"] || 0)),
      ),
    },
  ];
  const createMonthGroups = () => {
    const groups: {
      title: string;
      cols: number;
    }[] = [];

    let currentMonth = "";
    let count = 0;

    filteredData.forEach((item) => {
      if (item.Month !== currentMonth) {
        if (count > 0) {
          groups.push({
            title: currentMonth,
            cols: count,
          });
        }

        currentMonth = item.Month;
        count = 1;
      } else {
        count++;
      }
    });

    if (count > 0) {
      groups.push({
        title: currentMonth,
        cols: count,
      });
    }

    return groups;
  };
  const chartOptions: ApexOptions = {
    chart: {
      type: "bar",

      toolbar: {
        show: false,
      },

      stacked: true,
    },

    plotOptions: {
      bar: {
        columnWidth: "45%",
        borderRadius: 5,
      },
    },

    colors: [
      "#16a34a", // Profit
      "#dc2626", // Loss
    ],

    dataLabels: {
      enabled: true,

      formatter: (value) => {
        return `${value} pips`;
      },
    },

    xaxis: {
      categories: filteredData.map((item) => item["TP Level"]),

      group: {
        style: {
          fontSize: "12px",
          fontWeight: 700,
        },

        groups: createMonthGroups(),
      },
    },
    yaxis: {
      labels: {
        formatter: (value) => `${value} pips`,
      },
    },

    annotations: {
      yaxis: [
        {
          y: 0,
          borderColor: "#000",
        },
      ],

      points: filteredData.map((item) => {
        const profit = Number(item["Profit (Max)"] || 0);

        const loss = Number(item["Loss (Max)"] || 0);

        return {
          x: item["TP Level"],

          y: profit + 20,

          marker: {
            size: 0,
          },

          label: {
            text: `Result ${item.Result > 0 ? "+" : ""}${item.Result} pips`,

            borderColor: "transparent",

            style: {
              background: "transparent",

              color: item.Result >= 0 ? "#16a34a" : "#dc2626",

              fontSize: "12px",

              fontWeight: 700,
            },
          },
        };
      }),
    },

    tooltip: {
      y: {
        formatter: (value) => `${value} pips`,
      },
    },

    legend: {
      position: "top",
    },
  };

  return (
    <div className="space-y-6">
      <h1
        className="
        text-2xl
        font-bold
      "
      >
        Backtest Report
      </h1>

      {/* Month Selector */}

      <select
        value={selectedMonth}

        onChange={(e) => setSelectedMonth(e.target.value)}

        className="
          rounded-lg
          border
          px-3
          py-2
        "
      >
        {months.map((month) => (
          <option key={month}>{month}</option>
        ))}
      </select>

      {/* Summary Cards */}

      {summary && (
        <div
          className="
          grid
          grid-cols-1
          md:grid-cols-5
          gap-5
        "
        >
          <Card title="Total Signals" value={summary["Total Signals"]} />

          <Card title="Profit Max" value={`${summary["Profit (Max)"]} pips`} />

          <Card title="Loss Max" value={`${summary["Loss (Max)"]} pips`} />

          <Card title="Result" value={`${summary.Result} pips`} />

          <Card title="Loss Streak" value={summary["Loss Streak"]} />
        </div>
      )}

      {/* TP Result Chart */}

      <div
        className="
        rounded-xl
        border
        bg-white
        p-5
        dark:bg-gray-800
        "
      >
        <h2
          className="
          mb-4
          font-semibold
        "
        >
          {selectedMonth} TP Performance
        </h2>

        <Chart
          options={chartOptions}
          series={chartSeries}
          type="bar"
          height={300}
        />
      </div>

      {/* Detail Table */}

      <div
        className="
        rounded-xl
        border
        bg-white
        p-5
        overflow-x-auto
        dark:bg-gray-800
        "
      >
        <h2
          className="
          mb-4
          font-semibold
        "
        >
          TP Detail
        </h2>

        <table
          className="
          w-full
          text-sm
          "
        >
          <thead>
            <tr
              className="
              border-b
              "
            >
              <th>TP</th>
              <th>Profit</th>
              <th>Loss</th>
              <th>Result</th>
              <th>Return</th>
              <th>Loss Streak</th>
            </tr>
          </thead>

          <tbody>
            {filteredData.map((item, index) => (
              <tr
                key={index}
                className="
                border-b
                text-center
                "
              >
                <td>{item["TP Level"]}</td>

                <td>{item["Profit (Max)"]}</td>

                <td>{item["Loss (Max)"]}</td>

                <td>{item.Result}</td>

                <td>{item["Return %"]}%</td>

                <td>{item["Loss Streak"]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Card({ title, value }: { title: string; value: any }) {
  return (
    <div
      className="
rounded-xl
border
p-5
bg-white
text-center
dark:bg-gray-800
"
    >
      <p className="text-gray-500">{title}</p>

      <h2
        className="
text-3xl
font-bold
dark:text-white
"
      >
        {value}
      </h2>
    </div>
  );
}
