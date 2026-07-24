import {
calculateProviderRisk,
riskLabel
}
from "@/utils/providerRisk";


import RiskBadge
from "./RiskBadge";



export default function ProviderRiskMonitor(){


const score =
calculateProviderRisk({

identityChanged:true,

strategyChanged:false,

performanceDeviation:10

});



return(

<div className="
rounded-xl
border
bg-white
dark:bg-gray-800
p-6
">


<h2 className="font-semibold">

Provider Change Detection

</h2>


<div className="
flex
items-center
gap-4
mt-5
">


<h1 className="
text-5xl
font-bold
">

{score}

</h1>


<RiskBadge
level={riskLabel(score) as any}
/>


</div>



<div className="mt-5 space-y-2">


<p>
Identity Change:
❌ Detected
</p>


<p>
Strategy Change:
✓ Stable
</p>


<p>
Performance Deviation:
✓ Normal
</p>


</div>



</div>

)

}