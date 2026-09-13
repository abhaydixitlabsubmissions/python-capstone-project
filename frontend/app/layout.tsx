import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BookMind - AI Knowledge & Book Platform",
  description: "Personal AI book and knowledge platform with context-grounded RAG, intelligent notes, and library discovery.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full bg-slate-50">
      <body className="h-full flex flex-col antialiased text-slate-900 selection:bg-indigo-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}
