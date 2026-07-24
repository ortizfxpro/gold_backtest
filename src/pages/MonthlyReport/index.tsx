import { monthlyReports } from "@/data/reports";

export default function MonthlyReport() {
  const report = monthlyReports[0];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Monthly Trading Report</h1>

      <div
        className="
rounded-xl
border
bg-white
dark:bg-gray-800
p-6
"
      >
        <h2 className="text-xl font-semibold">{report.month}</h2>

        <p className="mt-4 text-gray-500">{report.summary}</p>
      </div>

      <div
        className="
grid
md:grid-cols-5
gap-5
"
      >
        {Object.entries(report.metrics).map(([key, value]) => (
          <div
            key={key}
            className="
rounded-xl
border
p-5
bg-white
dark:bg-gray-800
"
          >
            <p className="capitalize">{key}</p>

            <h2 className="text-2xl font-bold">{value}</h2>
          </div>
        ))}
      </div>

      <div
        className="
rounded-xl
border
p-6
bg-white
dark:bg-gray-800
"
      >
        <h2 className="font-semibold">AI Evaluation</h2>

        <ul className="mt-4 space-y-2">
          {report.analysis.map((item) => (
            <li key={item}>✓ {item}</li>
          ))}
        </ul>

        <h3
          className="
mt-6
font-semibold
"
        >
          Recommendation
        </h3>

        <p>{report.recommendation}</p>
      </div>
    </div>
  );
}
