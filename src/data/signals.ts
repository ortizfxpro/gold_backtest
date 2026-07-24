import type { Signal } from "@/types/trading";


export const signals: Signal[] = [

{
  date:"2026-07-01",
  provider:"Alpha EA",
  strategy:"Trend Follow",
  symbol:"EURUSD",
  direction:"BUY",
  profit:35,
  risk:"LOW"
},

{
  date:"2026-07-02",
  provider:"Beta Signal",
  strategy:"Scalping",
  symbol:"XAUUSD",
  direction:"SELL",
  profit:-20,
  risk:"HIGH"
}

];