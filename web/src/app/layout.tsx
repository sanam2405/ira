import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import Image from "next/image";

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
    <html
      lang="en"
      className={`${mina.variable} ${tagesschrift.variable}`}
    >
      <body>
        <div
          className="flex flex-col min-h-screen items-center bg-cover bg-center bg-no-repeat bg-fixed"
          style={{
            backgroundImage: "url(/cover.jpg)",
            backgroundPosition: "center 45%",
          }}
        >
          <div className="flex-1 flex flex-col items-center justify-end w-full">
            {children}
          </div>
          <footer className="w-full text-center text-2xl pb-4">
            <p className="english">Ira, one lyric at a time</p>
          </footer>
        </div>
      </body>
    </html>
  );
}
