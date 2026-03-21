import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Pancreatic Signal",
  description: "Research-first pancreatic report triage worklist"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
