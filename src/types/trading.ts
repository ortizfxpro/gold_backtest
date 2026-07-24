export type RiskLevel =
  | "LOW"
  | "MEDIUM"
  | "HIGH";


export type SignalDirection =
  | "BUY"
  | "SELL";


export interface Signal {

  date: string;

  provider: string;

  strategy: string;

  symbol: string;

  direction: SignalDirection;

  profit: number;

  risk: RiskLevel;

}