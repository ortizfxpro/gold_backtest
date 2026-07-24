export interface Provider {
  id:number;
  name:string;
  score:number;
  profitFactor:number;
  recoveryFactor:number;
  maxDrawdown:number;
  winRate:number;
  risk:"LOW"|"MEDIUM"|"HIGH";
}


export const provider = {
  id: 1,
  name: "Alpha Trend EA",
  strategy: "Trend Following",

  riskScore: 88,

  riskLevel: "LOW",

  maxDrawdown: 6.5,

  winRate: 68,

  profitFactor: 1.85,

  recoveryFactor: 4.2,

  monthlyReturn: 7.4
};