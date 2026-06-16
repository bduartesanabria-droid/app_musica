import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";
import { useState } from "react";

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-full bg-background dark:bg-gray-900">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="flex-1 flex flex-col min-w-0 lg:ml-64">
        <TopBar onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 overflow-auto p-4 md:p-6 lg:p-8">
          <div className="max-w-7xl mx-auto animate-in">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
