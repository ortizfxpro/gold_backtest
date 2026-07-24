import Chart from "react-apexcharts";
import type { ApexOptions } from "apexcharts";
import { monthlyPerformance } from "@/data/monthlyPerformance";

export default function PerformanceChart() {
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
          position: "top",
        },
      },
    },

    dataLabels: {
      enabled: true,
      formatter: (value) => {
        return `${value > 0 ? "+" : ""}${value}%`;
      },
      position: "center",
      offsetY: 0,
      style: {
        fontSize: "18px",
        colors: ["#fff"],
        fontWeight: 600,
      },
    },

    xaxis: {
      categories: monthlyPerformance.map((x) => x.month),
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
      data: monthlyPerformance.map((x) => x.return),
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
      <h3 className="mb-4 font-semibold">Monthly Return</h3>

      <Chart options={options} series={series} type="bar" height={300} />
    </div>
  );
}
