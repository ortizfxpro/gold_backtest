import Chart from "react-apexcharts";
import type { ApexOptions } from "apexcharts";
import { monthlyPerformance } from "@/data/monthlyPerformance";

export default function PerformanceChart({
  selectedMonth,
}: {
  selectedMonth: string;
}) {
  const selectedData = monthlyPerformance.find(
    (x) => x.month === selectedMonth,
  );

  const chartData =
    selectedMonth === "All"
      ? monthlyPerformance.map((x) => ({
          label: x.month,
          value: x.weeks.reduce((sum, w) => sum + w.return, 0),
        }))
      : selectedData?.weeks.map((w) => ({
          label: w.week,
          value: w.return,
        })) || [];

  const options: ApexOptions = {
    chart: {
      type: "bar",
      toolbar: {
        show: false,
      },
    },

    plotOptions: {
      bar: {
        borderRadius: 5,
        columnWidth: "45%",
        dataLabels: {
          position: "center",
        },
      },
    },

    dataLabels: {
      enabled: true,
      formatter: (value) => {
        const num = Number(value);

        return `${num > 0 ? "+" : ""}${num}%`;
      },
      offsetY: 0,
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
        formatter: (value) => `${value}%`,
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
      <h3 className="mb-4 font-semibold">
        {selectedMonth === "All"
          ? "Monthly Return"
          : `${selectedMonth} Weekly Return`}
      </h3>

      <Chart options={options} series={series} type="bar" height={300} />
    </div>
  );
}
