import Chart from "react-apexcharts";
import type { ApexOptions } from "apexcharts";
import {monthlyPerformance} from "@/data/monthlyPerformance";


export default function PerformanceChart(){

const options={

chart:{
 type:"line",
 toolbar:{
  show:false
 }
},

xaxis:{
 categories:
 monthlyPerformance.map(
 x=>x.month
 )
},


stroke:{
 curve:"smooth"
}
}satisfies ApexOptions;


const series=[
{
 name:"Return %",
 data: monthlyPerformance.map(
   x=>x.return
 )
}
];


return(

<div
className="
rounded-xl
border
bg-white
p-5
dark:bg-gray-800
">

<h3 className="
mb-4
font-semibold
">
Monthly Return
</h3>


<Chart
  options={options}
  series={series}
  type="line"
  height={300}
/>


</div>

)

}