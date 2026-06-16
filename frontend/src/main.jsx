import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";
import App from "./App";
import "./index.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 5 * 60 * 1000,
      refetchOnWindowFocus: false,
    },
  },
});

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 3000,
          style: {
            background: "#1E3A8A",
            color: "#fff",
            fontFamily: "Inter, sans-serif",
            borderRadius: "12px",
          },
          success: { iconTheme: { primary: "#F59E0B", secondary: "#fff" } },
          error: { style: { background: "#DC2626" } },
        }}
      />
    </QueryClientProvider>
  </React.StrictMode>
);
