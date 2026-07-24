import { useState } from "react";
import Chart from "react-apexcharts";
import type { ApexOptions } from "apexcharts";

import { monthlyPerformance } from "@/data/monthlyPerformance";

export default function PerformanceChart({
  selectedMonth,
}: {
  selectedMonth: string;
}) {
  const [chartView, setChartView] = useState<"weekly" | "daily">("weekly");

  const [selectedWeek, setSelectedWeek] = useState("");

  const selectedData = monthlyPerformance.find(
    (x) => x.month === selectedMonth,
  );

  const selectedWeekData = selectedData?.weeks.find(
    (x) => x.week === selectedWeek,
  ) as
    | {
        week: string;
        return: number;
        days: {
          day: string;
          return: number;
        }[];
      }
    | undefined;
  let chartData = [];

  // Monthly overview
  if (selectedMonth === "All") {
    chartData = monthlyPerformance.map((x) => ({
      label: x.month,
      value: x.weeks.reduce((sum, w) => sum + w.return, 0),
    }));
  }

  // Weekly chart
  else if (chartView === "weekly") {
    chartData =
      selectedData?.weeks.map((w) => ({
        label: w.week,
        value: w.return,
      })) || [];
  }

  // Daily chart
  else {
    chartData =
      selectedWeekData?.days.map((d) => ({
        label: d.day,
        value: d.return,
      })) || [];
  }

  const options: ApexOptions = {
    chart: {
      type: "bar",

      toolbar: {
        show: false,
      },

      events: {
        dataPointSelection: (event, chartContext, config) => {
          // Only weekly chart can be clicked
          if (selectedMonth !== "All" && chartView === "weekly") {
            const clickedWeek = selectedData?.weeks[config.dataPointIndex].week;

            if (clickedWeek) {
              setSelectedWeek(clickedWeek);
              setChartView("daily");
            }
          }
        },
      },
    },

    plotOptions: {
      bar: {
        borderRadius: 5,
        columnWidth: "45%",
      },
    },

    dataLabels: {
      enabled: true,

      formatter: (value) => {
        const num = Number(value);

        return `${num > 0 ? "+" : ""}${num}pips`;
      },

      style: {
        fontSize: "18px",
        colors: ["#fff"],
        fontWeight: 600,
      },
    },

    xaxis: {
      categories: chartData.map((x) => x.label),
    },

    yaxis: {
      labels: {
        formatter: (value) => `${value}pips`,
      },
    },
  };

  const series = [
    {
      name: "Return %",
      data: chartData.map((x) => x.value),
    },
  ];

  return (
    <div
      className="
      rounded-xl
      border
      bg-white
      p-5
      dark:bg-gray-800
      "
    >
      <div className="flex justify-between mb-4">
        <h3 className="font-semibold">
          {selectedMonth === "All"
            ? "Monthly Return"
            : chartView === "weekly"
              ? `${selectedMonth} Weekly Return`
              : `${selectedMonth} ${selectedWeek} Daily Return`}
        </h3>

        {chartView === "daily" && (
          <button
            className="
            rounded
            border
            px-3
            py-1
            text-sm
            "
            onClick={() => {
              setChartView("weekly");
              setSelectedWeek("");
            }}
          >
            ← Back
          </button>
        )}
      </div>

      <Chart options={options} series={series} type="bar" height={300} />
    </div>
  );
}
