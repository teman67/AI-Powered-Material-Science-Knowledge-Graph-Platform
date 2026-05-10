import type { Metadata } from "next";
import type { ReactNode } from "react";

import Providers from "./providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "Material Science KG Platform",
  description: "AI-powered material science knowledge graph platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
