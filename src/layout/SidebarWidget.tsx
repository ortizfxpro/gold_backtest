export default function SidebarWidget() {
  return (
    <div
      className="
      mx-auto mb-10 w-full max-w-60 rounded-2xl 
      bg-gray-50 px-4 py-5 text-center 
      dark:bg-white/[0.03]"
    >

      <h3 className="
      mb-2 font-semibold 
      text-gray-900 
      dark:text-white
      ">
        Trading System Status
      </h3>


      <p className="
      mb-4 text-sm 
      text-gray-500 
      dark:text-gray-400
      ">
        All providers are operating normally.
      </p>


      <div
      className="
      rounded-lg
      bg-green-100
      px-3
      py-2
      text-sm
      font-medium
      text-green-700
      "
      >
        System Online
      </div>


    </div>
  );
}