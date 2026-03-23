import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Pancreatic Signal",
  description: "Explainable pancreatic report triage with reviewer workflow and benchmark proof.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
