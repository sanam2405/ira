"use client";

import { useScreenSize } from "@/hooks";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { PostHogProvider } from "./PostHogProvider";

export default function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient());
  const screenSize = useScreenSize();
  const pathname = usePathname();
  const isMobile = screenSize === "mobile";
  const isLyricRoute = pathname.startsWith("/lyric/");

  return (
    <PostHogProvider>
      <QueryClientProvider client={queryClient}>
        <div
          className={`fixed inset-0 bg-cover bg-center bg-no-repeat ${
            isLyricRoute && isMobile
              ? "blur-sm transition-all duration-300"
              : ""
          }`}
          style={{
            backgroundImage: "url(/cover.jpg)",
            backgroundPosition: "center 0",
          }}
        />
        {children}
      </QueryClientProvider>
    </PostHogProvider>
  );
}
