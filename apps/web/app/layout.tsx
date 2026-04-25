import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Pancreatic Signal",
  description: "Open pancreatic oncology discovery software with cited research intelligence and explainable workflow surfaces.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
