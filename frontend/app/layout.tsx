import "./globals.css";
import type { Metadata } from "next";
import { AccessibilityProvider } from "@/context/AccessibilityContext";
import { AuthProvider } from "@/context/AuthContext";
import TopUtilityBar from "@/components/layout/TopUtilityBar";
import Header from "@/components/layout/Header";
import Navigation from "@/components/layout/Navigation";
import Footer from "@/components/layout/Footer";

export const metadata: Metadata = {
  title: "BhumiLekh (भूमिलेख) — National Land Record Portal",
  description:
    "BhumiLekh: Indian Government Digital Land Records Management Portal for Multilingual OCR, Entity Extraction, Land Validation, and Anomaly Detection.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="text-size-normal">
      <head>
        <link
          rel="stylesheet"
          href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
          integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
          crossOrigin=""
        />
      </head>
      <body className="min-h-screen flex flex-col bg-gray-50 text-gray-900 antialiased">
        <AccessibilityProvider>
          <AuthProvider>
            <TopUtilityBar />
            <Header />
            <Navigation />
            <main id="main-content" className="flex-1 flex flex-col">
              {children}
            </main>
            <Footer />
          </AuthProvider>
        </AccessibilityProvider>
      </body>
    </html>
  );
}
