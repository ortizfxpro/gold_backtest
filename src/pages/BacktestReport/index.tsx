import { monthlyPerformance } from "@/data/monthlyPerformance";

export default function BacktestReport() {
  return (
    <div>
      <h1
        className="
text-2xl
font-bold
mb-6
"
      >
        Backtest Report
      </h1>

      <table
        className="
w-full
rounded-xl
border
bg-white
dark:bg-gray-800
"
      >
        <thead>
          <tr>
            <th className="p-4">Month</th>

            <th>Return</th>

            <th>PF</th>

            <th>RF</th>

            <th>DD</th>
          </tr>
        </thead>

        <tbody>
          {monthlyPerformance.map((row) => (
            <tr key={row.month} className="border-b">
              <td className="p-4">{row.month}</td>

              <td>{row.return}%</td>

              <td>{row.pf}</td>

              <td>{row.rf}</td>

              <td>{row.dd}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
