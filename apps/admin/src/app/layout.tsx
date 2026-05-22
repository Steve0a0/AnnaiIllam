import type { Metadata } from "next";
import Providers from "@/components/shared/providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "Annai Illam Admin",
  description: "Admin panel for manpower operations",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full scroll-smooth antialiased">
      <body className="min-h-full" suppressHydrationWarning>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
