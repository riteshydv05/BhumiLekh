import "./globals.css";
import type { Metadata } from "next";
import { Suspense } from "react";
import { AccessibilityProvider } from "@/context/AccessibilityContext";
import { AuthProvider } from "@/context/AuthContext";
import { ThemeProvider } from "@/context/ThemeContext";
import TopUtilityBar from "@/components/layout/TopUtilityBar";
import Header from "@/components/layout/Header";
import Navigation from "@/components/layout/Navigation";
import Footer from "@/components/layout/Footer";
import PageTransitionBar from "@/components/layout/PageTransitionBar";

export const metadata: Metadata = {
  title: "BhumiLekh (भूमिलेख) — National Land Record Portal",
  description:
    "BhumiLekh: Indian Government Digital Land Records Management Portal for Multilingual OCR, Entity Extraction, Land Validation, and Anomaly Detection.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="text-size-normal">
      <head>
        <link
          rel="stylesheet"
          href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
          integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
          crossOrigin=""
        />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap"
          rel="stylesheet"
        />
      </head>
      {/* 
        bg-gray-50 = light default
        dark:bg-gray-950 = dark default
        Both work because ThemeProvider sets html.dark and Tailwind darkMode:'class' picks it up
      */}
      <body className="min-h-screen flex flex-col antialiased bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-slate-100">
        <ThemeProvider>
          {/* Page transition loading bar — instant feedback on link clicks */}
          <Suspense fallback={null}>
            <PageTransitionBar />
          </Suspense>
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
        </ThemeProvider>
      </body>
    </html>
  );
}
