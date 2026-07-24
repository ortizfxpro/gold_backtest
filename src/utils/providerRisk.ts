export interface ProviderChange{

identityChanged:boolean;

strategyChanged:boolean;

performanceDeviation:number;

}



export function calculateProviderRisk(
change:ProviderChange
){

let score=0;



// highest risk

if(change.identityChanged)
score+=40;



// medium risk

if(change.strategyChanged)
score+=25;



// performance consistency

if(
change.performanceDeviation>20
)
score+=20;



return score;



}



export function riskLabel(score:number){


if(score>=70)
return "CRITICAL";


if(score>=40)
return "HIGH";


if(score>=20)
return "MEDIUM";


return "LOW";


}