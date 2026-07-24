import {provider} from "@/data/providers";
import RiskBadge from "./RiskBadge";


export default function ProviderTable(){

return(

<div className="
overflow-hidden
rounded-xl
border
bg-white
dark:bg-gray-800
">


<table className="w-full">

<thead>

<tr
className="
border-b
text-left
text-sm
text-gray-500
">

<th className="p-4">
Provider
</th>

<th>
Score
</th>

<th>
PF
</th>

<th>
RF
</th>

<th>
Risk
</th>


</tr>

</thead>


<tbody>
<tr
className="border-b"
>

<td className="p-4">
{provider.name}
</td>

<td>
{provider.riskScore}/100
</td>

<td>
{provider.maxDrawdown}%
</td>

<td>
{provider.winRate}%
</td>

<td>
<RiskBadge
level={provider.riskLevel}
/>
</td>

</tr>


</tbody>


</table>


</div>

)

}