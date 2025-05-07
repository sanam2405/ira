"use client";

import { useScreenSize } from "@/hooks";
import { usePathname } from "next/navigation";

export default function Footer() {
  const screenSize = useScreenSize();
  const pathname = usePathname();
  const isMobile = screenSize === "mobile";
  const isLyricRoute = pathname.startsWith("/lyric/");

  return (
    <footer
      className={`w-full text-center text-md pb-2 ${
        isLyricRoute && isMobile
          ? "backdrop-blur-sm bg-white/40"
          : "md:bg-transparent md:backdrop-blur-none"
      }`}
    >
      <p className="english">Ira, one lyric at a time</p>
    </footer>
  );
}
