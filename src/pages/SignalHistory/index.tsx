import { useEffect, useState } from "react";
import * as XLSX from "xlsx";

//import RiskBadge from "@/components/trading/RiskBadge";

export default function SignalHistory() {
  const [signals, setSignals] = useState<any[]>([]);
  const [resultFilter, setResultFilter] = useState("All");
  const [weeklyFilter, setWeeklyFilter] = useState("All");

  const filteredSignals = signals.filter((signal) => {
    if (resultFilter !== "All" && signal.Result !== resultFilter) {
      return false;
    }

    if (weeklyFilter !== "All" && signal.Weekly !== weeklyFilter) {
      return false;
    }

    return true;
  });

  function formatExcelTime(value: any) {
    // already formatted text
    if (typeof value === "string") {
      return value;
    }

    // Excel stores time as fraction of a day
    if (typeof value === "number") {
      const totalMinutes = Math.round(value * 24 * 60);

      const hours = Math.floor(totalMinutes / 60);

      const minutes = totalMinutes % 60;

      return `${hours.toString().padStart(2, "0")}:${minutes
        .toString()
        .padStart(2, "0")}`;
    }

    return "";
  }

  function getResultStyle(result: string) {
    switch (result) {
      case "Win":
        return "bg-green-100 text-green-700";

      case "Loss":
        return "bg-red-100 text-red-700";

      case "No take place":
        return "bg-yellow-100 text-yellow-700";

      default:
        return "bg-gray-100 text-gray-700";
    }
  }

  useEffect(() => {
    fetch("/signal_history_july.xlsx?t=" + Date.now())
      .then((res) => res.arrayBuffer())
      .then((buffer) => {
        const workbook = XLSX.read(buffer);

        console.log("Sheets:", workbook.SheetNames);

        // Load July sheet for Signal History
        const sheetName = workbook.SheetNames[0];

        const worksheet = workbook.Sheets[sheetName];

        const data = XLSX.utils.sheet_to_json(worksheet);

        console.log("Signal data:", data.slice(0, 5));

        setSignals(data);

        // Load Result sheet for performance data
      })
      .catch((error) => {
        console.error("Excel loading error:", error);
      });
  }, []);
  return (
    <div className="space-y-6">
      <div className="flex gap-4">
        <select
          className="
            border
            rounded
            px-3
            py-2
    "
          value={resultFilter}
          onChange={(e) => setResultFilter(e.target.value)}
        >
          <option value="All">All Results</option>

          <option value="Win">Win</option>

          <option value="Loss">Loss</option>

          <option value="No take place">No take place</option>
        </select>

        <select
          className="
    border
    rounded
    px-3
    py-2
  "
          value={weeklyFilter}
          onChange={(e) => setWeeklyFilter(e.target.value)}
        >
          <option value="All">All Weeks</option>

          <option value="July-1st">July-1st</option>

          <option value="July-2nd">July-2nd</option>

          <option value="July-3rd">July-3rd</option>

          <option value="July-4th">July-4th</option>
        </select>
      </div>
      <h1 className="text-2xl font-bold">Signal History</h1>

      <div
        className="
              rounded-xl
              border
              bg-white    
              dark:bg-gray-800
              overflow-hidden
              "
      >
        <table className="w-full" table-fixed>
          <thead>
            <tr className="border-b">
              <th className="p-4 w-[100px]">Weekly</th>

              <th className="w-[110px]">Date</th>

              <th className="w-[80px]">Time</th>

              <th className="w-[120px]">Direction</th>

              <th className="w-[100px]">Entry Price</th>

              <th className="w-[80px]">TP3</th>

              <th className="w-[80px]">Result</th>

              <th className="w-[110px]">Exit Price</th>

              <th className="w-[100px]">Result Pips</th>

              <th className="w-[100px]">Deviation</th>
            </tr>
          </thead>

          <tbody>
            {filteredSignals.map((signal, index) => (
              <tr key={index} className="border-b">
                <td className="p-4 text-center">{signal.Weekly}</td>

                <td className="text-center">{signal.Date}</td>

                <td className="text-center">{formatExcelTime(signal.Time)}</td>

                <td className="text-center">{signal.Direction}</td>

                <td className="text-center">{signal["Entry Price"]}</td>

                <td className="text-center">{signal.TP3}</td>

                <td className="text-center">
                  <span
                    className={`
                        px-3
                        py-1
                        rounded-full 
                        text-sm
                        font-semibold
                        ${getResultStyle(signal.Result)}
                      `}
                  >
                    {signal.Result}
                  </span>
                </td>

                <td className="text-center">{signal["Closed Price"]}</td>

                <td className="text-center">
                  {signal["Result Pips"].toFixed(1)}
                </td>

                <td className="text-center">{signal.Deviation}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
