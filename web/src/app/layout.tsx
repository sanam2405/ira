import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import Providers from "./providers";

// Mina for Bengali
const mina = localFont({
  src: [
    {
      path: "../fonts/Mina-Regular.ttf",
      weight: "400",
      style: "normal",
    },
    {
      path: "../fonts/Mina-Bold.ttf",
      weight: "700",
      style: "bold",
    },
  ],
  display: "swap",
  variable: "--font-mina",
});

// Tagesschrift for English
const tagesschrift = localFont({
  src: [
    {
      path: "../fonts/Tagesschrift-Regular.ttf",
      weight: "400",
      style: "normal",
    },
    {
      path: "../fonts/Tagesschrift-Regular.ttf",
      weight: "700",
      style: "bold",
    },
  ],
  display: "swap",
  variable: "--font-tagesschrift",
});

export const metadata: Metadata = {
  title: "Ira",
  description: "Ira, one lyric at a time",
  icons: {
    icon: "/logo.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${mina.variable} ${tagesschrift.variable}`}>
      <body>
        <Providers>
          <div
            className="fixed inset-0 bg-cover bg-center bg-no-repeat"
            style={{
              backgroundImage: "url(/cover.jpg)",
              backgroundPosition: "center 0",
            }}
          />
          <div className="relative min-h-screen flex flex-col items-center">
            <div className="flex-1 flex flex-col items-center justify-end w-full">
              {children}
            </div>
            <footer className="w-full text-center text-md pb-2">
              <p className="english">Ira, one lyric at a time</p>
            </footer>
          </div>
        </Providers>
      </body>
    </html>
  );
}
