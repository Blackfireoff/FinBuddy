import type { Metadata } from "next";
import { Inter, Space_Grotesk } from "next/font/google";
import "./globals.css";
import SettingsFab from "./components/SettingsFab";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });
const grotesk = Space_Grotesk({ subsets: ["latin"], variable: "--font-display" });

export const metadata: Metadata = {
  title: "FinBuddy",
  description: "Analyze wallet health and transactions",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} ${grotesk.variable}`}>
        {children}
        <SettingsFab />
      </body>
    </html>
  );
}
