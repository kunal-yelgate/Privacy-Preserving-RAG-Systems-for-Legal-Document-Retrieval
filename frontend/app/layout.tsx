import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Casewise | Private legal research",
  description: "Upload case documents and ask grounded questions securely.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
