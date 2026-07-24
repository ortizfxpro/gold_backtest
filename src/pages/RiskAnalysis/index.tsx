import {
riskScore,
getRiskLevel
}
from "@/data/risk";


import RiskBadge
from "@/components/trading/RiskBadge";


export default function RiskAnalysis(){


const total =
riskScore.providerChange+
riskScore.strategyDrift+
riskScore.performanceDeviation+
riskScore.correlationRisk;



const level =
getRiskLevel(total/4);



return(

<div className="space-y-6">


<h1 className="text-2xl font-bold">
Risk Analysis
</h1>



<div className="
rounded-xl
border
p-6
bg-white
dark:bg-gray-800
">


<h2>
Overall Risk
</h2>


<div className="
flex
items-center
gap-5
mt-4
">


<p className="
text-5xl
font-bold
">

{total/4}

</p>


<RiskBadge
level={level}
/>


</div>


</div>



<div className="
grid
md:grid-cols-4
gap-5
">


<RiskCard
title="Provider Change"
value={riskScore.providerChange}
/>


<RiskCard
title="Strategy Drift"
value={riskScore.strategyDrift}
/>


<RiskCard
title="Performance Deviation"
value={riskScore.performanceDeviation}
/>


<RiskCard
title="Correlation"
value={riskScore.correlationRisk}
/>



</div>


</div>

)

}



function RiskCard(
{
title,
value
}:{
title:string,
value:number
}
){

return(

<div className="
rounded-xl
border
p-5
bg-white
dark:bg-gray-800
">

<p>{title}</p>

<h2 className="text-3xl font-bold">

{value}%

</h2>


</div>

)

}