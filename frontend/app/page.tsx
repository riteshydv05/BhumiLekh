"use client";

import React from "react";
import Link from "next/link";
import {
  Sparkles,
  ArrowRight,
  ShieldCheck,
  FileText,
  Map,
  CheckCircle,
  Database,
  Cpu,
  Globe2,
  Activity,
  AlertTriangle,
  Clock,
  Building,
  ScanText,
  Users,
  LogIn,
} from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white dark:bg-gray-950 text-gray-900 dark:text-slate-100">

      {/* 1. Official Government Rolling Bulletin */}
      <div className="bg-amber-50 dark:bg-amber-950/60 border-b border-amber-200 dark:border-amber-800 text-amber-950 dark:text-amber-100 py-1.5 px-3 overflow-hidden">
        <div className="max-w-7xl mx-auto flex items-center gap-2 text-xs">
          <span className="bg-amber-700 dark:bg-amber-600 text-white text-[10px] font-bold px-2.5 py-0.5 rounded shrink-0 uppercase tracking-wider flex items-center gap-1 shadow-sm">
            <Activity className="w-3 h-3" />
            Official Bulletin
          </span>
          <div className="overflow-hidden relative w-full">
            <div className="animate-marquee font-medium text-[11px] text-amber-900 dark:text-amber-200">
              <span><strong>National Initiative:</strong> Implementing Intelligent Land Record Digitization and Validation across regional revenue departments.</span>
              <span className="mx-6 text-amber-400">•</span>
              <span><strong>System Update:</strong> Multilingual OCR support now includes extensive training on historical Devanagari and English cadastral documents.</span>
              <span className="mx-6 text-amber-400">•</span>
              <span><strong>Security:</strong> All operations are conducted within secure, sovereign NIC MeghRaj infrastructure ensuring data privacy and compliance.</span>
              <span className="mx-6 text-amber-400">•</span>
              <span><strong>National Initiative:</strong> Implementing Intelligent Land Record Digitization and Validation across regional revenue departments.</span>
              <span className="mx-6 text-amber-400">•</span>
              <span><strong>System Update:</strong> Multilingual OCR support now includes extensive training on historical Devanagari and English cadastral documents.</span>
              <span className="mx-6 text-amber-400">•</span>
              <span><strong>Security:</strong> All operations are conducted within secure, sovereign NIC MeghRaj infrastructure ensuring data privacy and compliance.</span>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Hero Section */}
      <section className="relative overflow-hidden bg-[#F8F9FA] dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
        {/* LIGHT: Farm & countryside background with warm gradient */}
        <div
          className="absolute inset-0 z-0 pointer-events-none block dark:hidden"
          style={{
            backgroundImage:
              "linear-gradient(to right, rgba(248, 249, 250, 0.97) 0%, rgba(248, 249, 250, 0.88) 48%, rgba(248, 249, 250, 0.40) 100%), url('https://images.unsplash.com/photo-1500382017468-9049fed747ef?q=80&w=2532&auto=format&fit=crop')",
            backgroundSize: "cover",
            backgroundPosition: "center",
          }}
        />
        {/* DARK: subtle grid */}
        <div className="absolute inset-0 z-0 pointer-events-none hidden dark:block opacity-[0.03]"
          style={{ backgroundImage: "url(\"data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%23F59E0B' fill-opacity='1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/svg%3E\")" }} />

        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-12 pb-20 lg:pt-20 lg:pb-28 flex flex-col lg:flex-row items-center gap-12 lg:gap-10">
          {/* Left Column */}
          <div className="w-full lg:w-1/2 space-y-6">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider shadow-sm
              bg-emerald-50 dark:bg-emerald-900/30
              text-emerald-800 dark:text-emerald-300
              border border-emerald-200 dark:border-emerald-700/60">
              <Sparkles className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
              <span>AI-Powered Land Record Intelligence</span>
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-[54px] leading-[1.12] font-black tracking-tight
              text-[#1A365D] dark:text-white">
              Transforming Legacy <br className="hidden sm:block" />
              Land Records <br />
              <span className="text-[#2F855A] dark:text-emerald-400">Into Trusted Digital<br />Records</span>
            </h1>

            <p className="text-base sm:text-lg leading-relaxed max-w-xl font-medium
              text-gray-600 dark:text-slate-300">
              Bhumilekh uses AI to digitize, extract, validate and verify information from legacy land records,
              helping transform unstructured documents into reliable digital records.
            </p>

            <div className="flex flex-wrap items-center gap-2 text-[12px] sm:text-[13px] font-bold uppercase tracking-widest pt-1
              text-gray-400 dark:text-slate-500">
              {["DIGITIZE", "EXTRACT", "VALIDATE", "VERIFY", "MAP"].map((w, i, arr) => (
                <React.Fragment key={w}>
                  <span className="text-gray-600 dark:text-slate-400">{w}</span>
                  {i < arr.length - 1 && <span className="text-amber-400">•</span>}
                </React.Fragment>
              ))}
            </div>

            <div className="flex flex-wrap items-center gap-4 pt-4">
              {/* LIGHT: rich orange CTA with glow | DARK: amber */}
              <Link href="/login" prefetch={true}
                className="group relative px-7 py-3.5 font-bold rounded-md text-sm uppercase tracking-wider flex items-center gap-2.5 transition-all overflow-hidden
                  bg-[#E05A10] hover:bg-[#C2410C] text-white
                  shadow-[0_4px_14px_rgba(224,90,16,0.35)] hover:shadow-[0_6px_20px_rgba(224,90,16,0.45)]">
                <LogIn className="w-4 h-4" />
                <span>Get Started</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
              </Link>
              <Link href="/documents" prefetch={true}
                className="px-6 py-3.5 font-bold rounded-md transition-all flex items-center gap-2 text-sm uppercase tracking-wider
                  bg-white/90 dark:bg-slate-800
                  border-2 border-[#1A365D] dark:border-slate-600
                  text-[#1A365D] dark:text-slate-200
                  hover:bg-[#1A365D] dark:hover:bg-slate-700
                  hover:text-white dark:hover:text-white
                  shadow-sm">
                <span>Explore How It Works</span>
              </Link>
            </div>
          </div>

          {/* Right Column */}
          <div className="w-full lg:w-1/2 relative lg:pl-4 flex justify-center items-center">
            <div className="absolute -inset-4 bg-gradient-to-r from-emerald-100/60 to-amber-100/60 dark:from-emerald-900/20 dark:to-amber-900/15 blur-3xl -z-10 rounded-3xl" />
            <div className="relative rounded-2xl overflow-hidden transition-all duration-300
              shadow-[0_8px_32px_rgba(0,0,0,0.12)] hover:shadow-[0_12px_48px_rgba(0,0,0,0.16)]
              border border-gray-200/80 dark:border-slate-700
              bg-white dark:bg-slate-800 p-1.5">
              <img
                src="/hero-record-preview.png"
                alt="From Paper Records to Actionable Data — AI Land Record Digitization and Extraction"
                className="w-full h-auto object-contain rounded-xl"
                loading="eager"
              />
            </div>
          </div>
        </div>
      </section>

      {/* 3. Why It Matters */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="p-6 sm:p-8 rounded-xl
          bg-slate-50 dark:bg-slate-900
          border border-gray-200 dark:border-slate-800
          shadow-[0_2px_8px_rgba(0,0,0,0.04)] dark:shadow-none">
          <div className="mb-6">
            <h2 className="text-lg font-bold uppercase tracking-wide inline-block pb-1 border-b-2 border-amber-600
              text-gray-900 dark:text-white">
              Why It Matters
            </h2>
            <p className="text-sm mt-2 text-gray-500 dark:text-slate-400">
              The inherent limitations of manual land record administration and why technological intervention is necessary.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              {
                icon: AlertTriangle, title: "Physical Degradation",
                desc: "Decades-old documents are brittle and prone to decay, risking the permanent loss of vital ownership histories.",
                lightIcon: "text-amber-600 bg-amber-100", darkIcon: "dark:text-amber-400 dark:bg-amber-500/15",
                lightBorder: "hover:border-amber-300", darkBorder: "dark:hover:border-amber-600/50",
              },
              {
                icon: Clock, title: "Processing Delays",
                desc: "Manual transcription of complex cadastral documents is severely time-consuming, causing massive administrative backlogs.",
                lightIcon: "text-orange-600 bg-orange-100", darkIcon: "dark:text-orange-400 dark:bg-orange-500/15",
                lightBorder: "hover:border-orange-300", darkBorder: "dark:hover:border-orange-600/50",
              },
              {
                icon: Globe2, title: "Linguistic Barriers",
                desc: "Records are often recorded in legacy scripts and localized terminology, requiring specialized personnel to decipher.",
                lightIcon: "text-blue-600 bg-blue-100", darkIcon: "dark:text-blue-400 dark:bg-blue-500/15",
                lightBorder: "hover:border-blue-300", darkBorder: "dark:hover:border-blue-600/50",
              },
              {
                icon: ShieldCheck, title: "Human Error & Fraud",
                desc: "Manual data entry is prone to clerical errors and lacks the automated spatial cross-referencing needed to prevent overlapping claims.",
                lightIcon: "text-red-600 bg-red-100", darkIcon: "dark:text-red-400 dark:bg-red-500/15",
                lightBorder: "hover:border-red-300", darkBorder: "dark:hover:border-red-600/50",
              },
            ].map(({ icon: Icon, title, desc, lightIcon, darkIcon, lightBorder, darkBorder }) => (
              <div key={title} className={`p-5 rounded-lg border transition-all duration-200 group
                bg-white dark:bg-slate-800
                border-gray-200 dark:border-slate-700
                shadow-[0_1px_4px_rgba(0,0,0,0.05)] dark:shadow-none
                hover:shadow-[0_4px_16px_rgba(0,0,0,0.08)] dark:hover:shadow-none
                ${lightBorder} ${darkBorder}`}>
                {/* Enhanced: colored icon background in light mode */}
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 ${lightIcon} ${darkIcon}`}>
                  <Icon className="w-5 h-5" />
                </div>
                <h3 className="text-sm font-bold text-gray-900 dark:text-white">{title}</h3>
                <p className="text-xs mt-1 leading-relaxed text-gray-500 dark:text-slate-400">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 4. System Capabilities: Timeline */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="mb-6">
          <h2 className="text-lg font-bold uppercase tracking-wide inline-block pb-1 border-b-2 border-amber-600
            text-gray-900 dark:text-white">
            System Capabilities &amp; Operational Flow
          </h2>
          <p className="text-sm mt-2 text-gray-500 dark:text-slate-400">
            Step-by-step pipeline for end-to-end digitization, parsing, validation, and archival of historical land deeds.
          </p>
        </div>

        <div className="relative border-l-2 border-amber-300 dark:border-amber-700 ml-4 md:ml-6 space-y-5 pb-2">
          {[
            { icon: FileText,      title: "1. Document Ingestion",                 desc: "Secure intake of historical physical scans (PDF, TIFF, JPEG) into the automated processing queue.",                                                            iconColor: "text-amber-700 dark:text-amber-400" },
            { icon: ScanText,      title: "2. Multilingual OCR & HTR",             desc: "Recognizes printed typography and cursive handwritten scripts across English and Devanagari records.",                                                            iconColor: "text-orange-700 dark:text-orange-400" },
            { icon: Cpu,           title: "3. Intelligent Entity Extraction",       desc: "Intelligently parses tabular layouts and unstructured legal text to isolate key fields like Khasra, Khatauni, and Area.",                                          iconColor: "text-blue-700 dark:text-blue-400" },
            { icon: AlertTriangle, title: "4. Confidence Scoring",                  desc: "Calculates mathematical certainty scores for every extracted token, flagging low-confidence values for mandatory review.",                                           iconColor: "text-purple-700 dark:text-purple-400" },
            { icon: CheckCircle,   title: "5. Semantic & Mathematical Validation", desc: "Cross-checks numeric formats, dates, boundary descriptions, and parcel areas to ensure strict internal consistency.",                                                 iconColor: "text-emerald-700 dark:text-emerald-400" },
            { icon: Map,           title: "6. Cadastral GIS Alignment",             desc: "Connects textual deeds with spatial parcel maps to verify boundaries and prevent fraudulent overlapping registrations.",                                              iconColor: "text-teal-700 dark:text-teal-400" },
            { icon: Users,         title: "7. Revenue Officer Verification",        desc: "Enables authorized revenue officers to audit flagged records side-by-side with original scanned documents.",                                                         iconColor: "text-rose-700 dark:text-rose-400" },
            { icon: Database,      title: "8. Sovereign Digital Registry",          desc: "Secures finalized records in an immutable, legally verifiable digital repository accessible across departmental nodes.",                                              iconColor: "text-slate-700 dark:text-slate-400" },
          ].map((step, idx) => (
            <div key={idx} className="relative pl-8 md:pl-10">
              {/* Enhanced bubble in light mode */}
              <div className="absolute -left-[17px] top-2 w-8 h-8 rounded-full flex items-center justify-center
                bg-white dark:bg-slate-800
                border-2 border-amber-500 dark:border-amber-600
                shadow-[0_2px_8px_rgba(245,158,11,0.25)] dark:shadow-none">
                <step.icon className={`w-4 h-4 ${step.iconColor}`} />
              </div>
              <div className="p-4 rounded-lg transition-all duration-200
                bg-white dark:bg-slate-800/80
                border border-gray-200 dark:border-slate-700
                shadow-[0_1px_4px_rgba(0,0,0,0.05)] dark:shadow-none
                hover:border-amber-300 dark:hover:border-amber-700
                hover:shadow-[0_4px_16px_rgba(0,0,0,0.07)] dark:hover:shadow-none">
                <h3 className="text-base font-bold mb-1 text-gray-900 dark:text-white">{step.title}</h3>
                <p className="text-sm leading-relaxed text-gray-500 dark:text-slate-400">{step.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 5. What We Built */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="p-6 sm:p-8 rounded-xl
          bg-slate-50 dark:bg-slate-900
          border border-gray-200 dark:border-slate-800
          shadow-[0_2px_8px_rgba(0,0,0,0.04)] dark:shadow-none">
          <h2 className="text-lg font-bold uppercase tracking-wide inline-block pb-1 mb-4 border-b-2 border-amber-600
            text-gray-900 dark:text-white">
            What We Built
          </h2>
          <p className="text-sm leading-relaxed mb-6 max-w-4xl text-gray-600 dark:text-slate-300">
            An institutional-grade platform engineered to digitize, index, and validate complex regional land registries.
            Designed specifically for offline or air-gapped sovereign deployment inside state and national data centers.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              { title: "Asynchronous Processing Engine",     desc: "Handles large-scale historical document archives and multi-page deed batches without bottlenecking frontline operations." },
              { title: "Specialized Document Understanding", desc: "Models tailored for regional cadastral nomenclature, non-standard tabular formats, and legacy handwriting." },
              { title: "Tehsildar Audit Station",            desc: "Interactive split-screen interface allowing officers to verify original scans against extracted values with single-click sign-off." },
              { title: "Cadastral GIS Cross-Referencing",   desc: "Direct integration between textual legal deeds and digitized village maps to immediately detect overlapping boundary disputes." },
              { title: "Role-Based Administrative Control", desc: "Strict compartmentalization separating citizen viewing, verification officer auditing, and administrative governance." },
              { title: "Tamper-Evident Digital Repository", desc: "Permanent record storage ensuring chain-of-custody tracking, cryptographic audit trails, and instant legal retrieval." },
            ].map((item, idx) => (
              <div key={idx} className="p-4 rounded-lg border transition-all duration-200
                bg-white dark:bg-slate-800
                border-gray-200 dark:border-slate-700
                shadow-[0_1px_4px_rgba(0,0,0,0.05)] dark:shadow-none
                hover:border-emerald-300 dark:hover:border-emerald-700
                hover:shadow-[0_4px_16px_rgba(0,0,0,0.08)] dark:hover:shadow-none">
                {/* Enhanced: green icon bubble in light mode */}
                <div className="flex items-start gap-3 mb-2">
                  <div className="w-7 h-7 rounded-md flex items-center justify-center shrink-0 mt-0.5
                    bg-emerald-100 dark:bg-emerald-500/15">
                    <CheckCircle className="w-4 h-4 text-emerald-700 dark:text-emerald-400" />
                  </div>
                  <span className="text-sm font-bold text-emerald-800 dark:text-emerald-400 leading-tight">{item.title}</span>
                </div>
                <p className="text-xs leading-relaxed ml-10 text-gray-500 dark:text-slate-400">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 6. Automated Information Extraction Demo */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="p-6 sm:p-8 rounded-xl border
          bg-amber-50 dark:bg-amber-950/20
          border-amber-200 dark:border-amber-800/40
          shadow-[0_2px_8px_rgba(0,0,0,0.04)] dark:shadow-none">
          <div className="mb-6 text-center">
            <h2 className="text-lg font-bold uppercase tracking-wide text-gray-900 dark:text-white">
              Automated Information Extraction
            </h2>
            <p className="text-sm mt-1 text-gray-500 dark:text-slate-400">
              Translating complex, tabular physical records into structured digital data.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Hindi Record */}
            <div className="rounded-lg overflow-hidden flex flex-col
              bg-white dark:bg-slate-800
              border border-gray-200 dark:border-slate-700
              shadow-[0_2px_8px_rgba(0,0,0,0.06)] dark:shadow-none">
              {/* Enhanced header with amber tint in light mode */}
              <div className="px-4 py-3 text-xs font-bold border-b flex items-center gap-2
                bg-gradient-to-r from-amber-50 to-gray-50 dark:bg-slate-700
                text-gray-700 dark:text-slate-200
                border-amber-200 dark:border-slate-600">
                <div className="w-5 h-5 rounded bg-amber-100 dark:bg-amber-500/20 flex items-center justify-center">
                  <FileText className="w-3 h-3 text-amber-700 dark:text-amber-400" />
                </div>
                Sample Regional Record (Hindi)
              </div>
              <div className="p-5 grid grid-cols-1 sm:grid-cols-2 gap-4 flex-1">
                <div className="rounded-lg flex items-center justify-center p-4
                  bg-gray-50 dark:bg-slate-900
                  border border-dashed border-gray-300 dark:border-slate-600">
                  <div className="font-mono text-xs text-center leading-relaxed text-gray-500 dark:text-slate-400">
                    [Scanned Document Sample]<br /><br />
                    खाता संख्या: १५<br />
                    खातेदार: राम कुमार<br />
                    खसरा: १२३/४<br />
                    क्षेत्रफल: ०.५० हेक्ट.
                  </div>
                </div>
                <div className="flex flex-col justify-center space-y-2.5 text-xs">
                  {[["Khata No.", "15"], ["Owner", "Ram Kumar"], ["Khasra/Survey", "123/4"], ["Area", "0.50 Hectares"]].map(([k, v]) => (
                    <div key={k} className="flex justify-between border-b pb-1.5
                      border-gray-100 dark:border-slate-700">
                      <span className="text-gray-500 dark:text-slate-500">{k}</span>
                      <span className="font-bold font-mono text-emerald-700 dark:text-emerald-300">{v}</span>
                    </div>
                  ))}
                  <div className="mt-1 text-center text-[10px] font-bold py-1 rounded
                    bg-emerald-50 dark:bg-emerald-900/30
                    text-emerald-700 dark:text-emerald-400
                    border border-emerald-200 dark:border-emerald-700/40">
                    ✓ Confidence: 97.3%
                  </div>
                </div>
              </div>
            </div>

            {/* English Record */}
            <div className="rounded-lg overflow-hidden flex flex-col
              bg-white dark:bg-slate-800
              border border-gray-200 dark:border-slate-700
              shadow-[0_2px_8px_rgba(0,0,0,0.06)] dark:shadow-none">
              {/* Enhanced header */}
              <div className="px-4 py-3 text-xs font-bold border-b flex items-center gap-2
                bg-gradient-to-r from-blue-50 to-gray-50 dark:bg-slate-700
                text-gray-700 dark:text-slate-200
                border-blue-200 dark:border-slate-600">
                <div className="w-5 h-5 rounded bg-blue-100 dark:bg-blue-500/20 flex items-center justify-center">
                  <FileText className="w-3 h-3 text-blue-700 dark:text-blue-400" />
                </div>
                Sample Cadastral Record (English)
              </div>
              <div className="p-5 grid grid-cols-1 sm:grid-cols-2 gap-4 flex-1">
                <div className="rounded-lg flex items-center justify-center p-4
                  bg-gray-50 dark:bg-slate-900
                  border border-dashed border-gray-300 dark:border-slate-600">
                  <div className="font-mono text-xs text-center leading-relaxed text-gray-500 dark:text-slate-400">
                    [Scanned Document Sample]<br /><br />
                    Survey No: 45A<br />
                    Title Holder: S. Patel<br />
                    Sub-Division: 2<br />
                    Extent: 1.2 Acres
                  </div>
                </div>
                <div className="flex flex-col justify-center space-y-2.5 text-xs">
                  {[["Survey No.", "45A"], ["Title Holder", "S. Patel"], ["Sub-Division", "2"], ["Area (Extent)", "1.2 Acres"]].map(([k, v]) => (
                    <div key={k} className="flex justify-between border-b pb-1.5
                      border-gray-100 dark:border-slate-700">
                      <span className="text-gray-500 dark:text-slate-500">{k}</span>
                      <span className="font-bold font-mono text-blue-700 dark:text-blue-300">{v}</span>
                    </div>
                  ))}
                  <div className="mt-1 text-center text-[10px] font-bold py-1 rounded
                    bg-blue-50 dark:bg-blue-900/30
                    text-blue-700 dark:text-blue-400
                    border border-blue-200 dark:border-blue-700/40">
                    ✓ Confidence: 98.1%
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 7. Impact & Benefits */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pb-12">
        <div className="mb-6">
          <h2 className="text-lg font-bold uppercase tracking-wide inline-block pb-1 border-b-2 border-amber-600
            text-gray-900 dark:text-white">
            Impact &amp; Benefits
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Government */}
          <div className="p-6 rounded-xl border transition-all
            bg-white dark:bg-slate-800/80
            border-gray-200 dark:border-slate-700
            shadow-[0_2px_10px_rgba(0,0,0,0.06)] dark:shadow-none
            hover:shadow-[0_6px_24px_rgba(0,0,0,0.09)] dark:hover:shadow-none
            hover:border-amber-200 dark:hover:border-amber-700/50">
            <div className="flex items-center gap-3 mb-4">
              {/* Light: amber icon with warm background */}
              <div className="w-10 h-10 rounded-lg flex items-center justify-center
                bg-amber-100 dark:bg-amber-500/15">
                <Building className="w-5 h-5 text-amber-700 dark:text-amber-400" />
              </div>
              <h3 className="text-base font-bold text-gray-900 dark:text-white">For Government Departments</h3>
            </div>
            <ul className="space-y-2.5 text-sm text-gray-600 dark:text-slate-300">
              {[
                "Drastic reduction in manual data entry backlogs across revenue offices.",
                "Automated detection of spatial overlaps and fraudulent registrations.",
                "Establishment of a centralized, auditable, and secure document archive.",
                "Enhanced capability to monitor revenue operations via dashboard analytics.",
              ].map((item) => (
                <li key={item} className="flex items-start gap-2">
                  <span className="text-amber-500 font-bold mt-0.5">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Citizens */}
          <div className="p-6 rounded-xl border transition-all
            bg-white dark:bg-slate-800/80
            border-gray-200 dark:border-slate-700
            shadow-[0_2px_10px_rgba(0,0,0,0.06)] dark:shadow-none
            hover:shadow-[0_6px_24px_rgba(0,0,0,0.09)] dark:hover:shadow-none
            hover:border-emerald-200 dark:hover:border-emerald-700/50">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg flex items-center justify-center
                bg-emerald-100 dark:bg-emerald-500/15">
                <Users className="w-5 h-5 text-emerald-700 dark:text-emerald-400" />
              </div>
              <h3 className="text-base font-bold text-gray-900 dark:text-white">For Citizens</h3>
            </div>
            <ul className="space-y-2.5 text-sm text-gray-600 dark:text-slate-300">
              {[
                "Faster processing of mutation requests and property transfers.",
                "Increased transparency and direct accessibility to verified land records.",
                "Significant reduction in protracted land disputes and litigation.",
                "Assurance of clear ownership through cross-validated digital registries.",
              ].map((item) => (
                <li key={item} className="flex items-start gap-2">
                  <span className="text-emerald-500 font-bold mt-0.5">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

    </div>
  );
}
