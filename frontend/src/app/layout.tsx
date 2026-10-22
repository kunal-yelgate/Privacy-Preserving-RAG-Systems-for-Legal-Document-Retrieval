import "./globals.css";
import Navbar from "@/components/layout/Navbar";
import Sidebar from "@/components/layout/Sidebar";

export const metadata = {
  title: "Veritas | Privacy-Preserving Offline Legal RAG",
  description: "Offline-first, matter-isolated legal research and verification assistant.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 flex flex-col text-slate-900">
        <Navbar />
        <div className="flex-1 flex">
          <Sidebar />
          <main className="flex-1 p-8 overflow-y-auto max-w-7xl mx-auto w-full">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
