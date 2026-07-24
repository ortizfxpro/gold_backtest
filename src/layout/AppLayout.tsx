import { useSidebar } from "../context/SidebarContext";
import { Outlet } from "react-router-dom";
import Backdrop from "./Backdrop";
import AppSidebar from "./AppSidebar";
import AppHeader from "./AppHeader";


const LayoutContent: React.FC = () => {

  const {
    isExpanded,
    isHovered,
    isMobileOpen
  } = useSidebar();


  return (
    <div
      className="relative min-h-screen xl:flex bg-cover bg-center"
      style={{
        backgroundImage: "url('/images/background_logo.jpg')",
      }}
      
    >

      {/* Dark overlay */}
      <div className="absolute inset-0 bg-black/70"></div>


      {/* Main content */}
      <div className="relative z-10 min-h-screen xl:flex w-full">

        <div>
          <AppSidebar />
          <Backdrop />
        </div>


        <div
          className={`
          flex-1
          transition-all
          duration-300
          ease-in-out

          ${
            isExpanded || isHovered
            ? "lg:ml-[290px]"
            : "lg:ml-[90px]"
          }

          ${isMobileOpen ? "ml-0" : ""}
          `}
        >

          <AppHeader />

          <div className="p-4 mx-auto max-w-(--breakpoint-2xl) md:p-6">
            <Outlet />
          </div>

        </div>

      </div>

    </div>
  );
};



const AppLayout = () => {

  return (
    <LayoutContent />
  );

};


export default AppLayout;