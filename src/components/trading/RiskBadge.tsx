type RiskBadgeProps = {
  level: string;
};


export default function RiskBadge({
  level
}: RiskBadgeProps) {


const style =
  level === "LOW"
    ? "bg-green-100 text-green-700"
    : level === "MEDIUM"
    ? "bg-yellow-100 text-yellow-700"
    : "bg-red-100 text-red-700";


return (

<span
className={`
rounded-full
px-3
py-1
text-xs
font-medium
${style}
`}
>

{level}

</span>

);

}