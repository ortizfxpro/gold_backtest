interface Props {
  title:string;
  value:string;
  change?:string;
}

export default function KPICard({
 title,
 value,
 change
}:Props){

return (
<div className="
rounded-xl
border
bg-white
p-5
shadow-sm
dark:bg-gray-800
">

<p className="text-sm text-gray-500">
{title}
</p>

<h2 className="
mt-2
text-3xl
font-bold
text-gray-900
dark:text-white
">
{value}
</h2>


{
change &&
<p className="
mt-2
text-sm
text-green-500
">
{change}
</p>
}

</div>
)

}