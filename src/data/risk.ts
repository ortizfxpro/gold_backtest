export const riskScore={
 providerChange:80,
 strategyDrift:40,
 performanceDeviation:30,
 correlationRisk:50
};


export function getRiskLevel(score:number){

 if(score>=75)
  return "CRITICAL";

 if(score>=50)
  return "HIGH";

 if(score>=25)
  return "MEDIUM";

 return "LOW";
}
