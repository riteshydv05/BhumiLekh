"use client";

import React from "react";
import Link from "next/link";
import {
  Sparkles,
  ArrowRight,
  Check,
  ShieldCheck,
  FileText,
  Map,
  UploadCloud,
  CheckCircle,
  Database,
  Cpu,
  Layers,
  Globe2,
  Activity,
  AlertTriangle,
  Scale,
  Clock,
  Search,
  BarChart3,
  Building,
  ScanText,
  Users
} from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white text-gray-900">
      {/* 1. Official Government Rolling Bulletin */}
      <div className="bg-amber-100 border-b border-amber-300 text-amber-950 py-1.5 px-3 overflow-hidden">
        <div className="max-w-7xl mx-auto flex items-center gap-2 text-xs">
          <span className="bg-amber-700 text-white text-[10px] font-bold px-2 py-0.5 rounded shrink-0 uppercase tracking-wider flex items-center gap-1 shadow-xs">
            <Activity className="w-3 h-3" />
            Official Bulletin
          </span>

          <div className="overflow-hidden relative w-full">
            <div className="animate-marquee font-medium text-[11px] space-x-8 text-amber-900">
              <span>
                <strong>National Initiative:</strong> Implementing Intelligent Land Record Digitization and Validation across regional revenue departments.
              </span>
              <span>•</span>
              <span>
                <strong>System Update:</strong> Multilingual OCR support now includes extensive training on historical Devanagari and English cadastral documents.
              </span>
              <span>•</span>
              <span>
                <strong>Security:</strong> All operations are conducted within secure, sovereign infrastructure ensuring data privacy and compliance.
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Hero Section Matching the Bhumilekh Design */}
      <section className="relative overflow-hidden bg-[#F8F9FA] border-b border-gray-200">
        {/* Farm & Countryside Background Image with Gradient Overlay */}
        <div 
          className="absolute inset-0 z-0 opacity-45 pointer-events-none"
          style={{
            backgroundImage: "linear-gradient(to right, rgba(248, 249, 250, 0.96) 0%, rgba(248, 249, 250, 0.82) 48%, rgba(248, 249, 250, 0.35) 100%), url('https://images.unsplash.com/photo-1500382017468-9049fed747ef?q=80&w=2532&auto=format&fit=crop')",
            backgroundSize: "cover",
            backgroundPosition: "center",
          }}
        />

        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-12 pb-20 lg:pt-20 lg:pb-28 flex flex-col lg:flex-row items-center gap-12 lg:gap-10">
          {/* Left Column: Hero Text & Call to Actions */}
          <div className="w-full lg:w-1/2 space-y-6">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-bold uppercase tracking-wider shadow-xs">
              <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
              <span>AI-Powered Land Record Intelligence</span>
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-[54px] leading-[1.12] font-black text-[#1A365D] tracking-tight">
              Transforming Legacy <br className="hidden sm:block" />
              Land Records <br />
              <span className="text-[#2F855A]">Into Trusted Digital<br /> Records</span>
            </h1>

            <p className="text-base sm:text-lg text-gray-600 leading-relaxed max-w-xl font-medium">
              Bhumilekh uses AI to digitize, extract, validate and verify information from legacy land records, helping transform unstructured documents into reliable digital records.
            </p>

            <div className="flex flex-wrap items-center gap-2 text-[12px] sm:text-[13px] font-bold text-gray-500 uppercase tracking-widest pt-1">
              <span>DIGITIZE</span>
              <span>•</span>
              <span>EXTRACT</span>
              <span>•</span>
              <span>VALIDATE</span>
              <span>•</span>
              <span>VERIFY</span>
              <span>•</span>
              <span>MAP</span>
            </div>

            <div className="flex flex-wrap items-center gap-4 pt-4">
              <Link
                href="/upload"
                className="px-7 py-3.5 bg-[#E05A10] hover:bg-[#C2410C] text-white font-bold rounded-md shadow-lg shadow-orange-600/25 transition-all flex items-center gap-2.5 text-sm uppercase tracking-wider"
              >
                <span>Get Started</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                href="/documents"
                className="px-6 py-3.5 bg-white/90 backdrop-blur-xs border-2 border-[#1A365D] text-[#1A365D] hover:bg-[#1A365D] hover:text-white font-bold rounded-md transition-all flex items-center gap-2 text-sm uppercase tracking-wider shadow-xs"
              >
                <span>Explore How It Works</span>
              </Link>
            </div>
          </div>

          {/* Right Column: AI Digitization Visual Showcase Image */}
          <div className="w-full lg:w-1/2 relative lg:pl-4 flex justify-center items-center">
            <div className="absolute -inset-4 bg-gradient-to-r from-emerald-100/50 to-amber-100/50 blur-3xl -z-10 rounded-3xl" />
            
            <div className="relative rounded-2xl overflow-hidden shadow-2xl border border-gray-200/80 bg-white p-1.5 transition-all duration-300 hover:shadow-3xl">
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

      {/* 3. Why It Matters: Problems with Manual Digitization */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="p-6 sm:p-8 bg-slate-50 border border-gray-200 rounded-lg">
          <div className="mb-6">
            <h2 className="text-lg font-bold text-gray-900 uppercase tracking-wide border-b-2 border-amber-600 inline-block pb-1">
              Why It Matters
            </h2>
            <p className="text-sm text-gray-600 mt-2">
              The inherent limitations of manual land record administration and why technological intervention is necessary.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white p-5 border border-gray-200 rounded shadow-xs">
              <AlertTriangle className="w-6 h-6 text-amber-600 mb-2" />
              <h3 className="text-sm font-bold text-gray-900">Physical Degradation</h3>
              <p className="text-xs text-gray-600 mt-1 leading-relaxed">
                Decades-old documents are brittle and prone to decay, risking the permanent loss of vital ownership histories.
              </p>
            </div>
            <div className="bg-white p-5 border border-gray-200 rounded shadow-xs">
              <Clock className="w-6 h-6 text-amber-600 mb-2" />
              <h3 className="text-sm font-bold text-gray-900">Processing Delays</h3>
              <p className="text-xs text-gray-600 mt-1 leading-relaxed">
                Manual transcription of complex cadastral documents is severely time-consuming, causing massive administrative backlogs.
              </p>
            </div>
            <div className="bg-white p-5 border border-gray-200 rounded shadow-xs">
              <Globe2 className="w-6 h-6 text-amber-600 mb-2" />
              <h3 className="text-sm font-bold text-gray-900">Linguistic Barriers</h3>
              <p className="text-xs text-gray-600 mt-1 leading-relaxed">
                Records are often recorded in legacy scripts and localized terminology, requiring specialized personnel to decipher.
              </p>
            </div>
            <div className="bg-white p-5 border border-gray-200 rounded shadow-xs">
              <ShieldCheck className="w-6 h-6 text-amber-600 mb-2" />
              <h3 className="text-sm font-bold text-gray-900">Human Error & Fraud</h3>
              <p className="text-xs text-gray-600 mt-1 leading-relaxed">
                Manual data entry is prone to clerical errors and lacks the automated spatial cross-referencing needed to prevent overlapping claims.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 4. System Capabilities: Continuous Process Flow (Without Tech Jargon) */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="mb-6">
          <h2 className="text-lg font-bold text-gray-900 uppercase tracking-wide border-b-2 border-amber-600 inline-block pb-1">
            System Capabilities & Operational Flow
          </h2>
          <p className="text-sm text-gray-600 mt-2">
            Step-by-step pipeline for end-to-end digitization, parsing, validation, and archival of historical land deeds.
          </p>
        </div>

        <div className="relative border-l-2 border-amber-300 ml-4 md:ml-6 space-y-6 pb-2">
          {[
            { 
              icon: FileText, 
              title: "1. Document Ingestion", 
              desc: "Secure intake of historical physical scans (PDF, TIFF, JPEG) into the automated processing queue." 
            },
            { 
              icon: ScanText, 
              title: "2. Multilingual OCR & HTR", 
              desc: "Recognizes printed typography and cursive handwritten scripts across English and Devanagari records." 
            },
            { 
              icon: Cpu, 
              title: "3. Intelligent Entity Extraction", 
              desc: "Intelligently parses tabular layouts and unstructured legal text to isolate key fields like Khasra, Khatauni, and Area." 
            },
            { 
              icon: AlertTriangle, 
              title: "4. Confidence Scoring", 
              desc: "Calculates mathematical certainty scores for every extracted token, flagging low-confidence values for mandatory review." 
            },
            { 
              icon: CheckCircle, 
              title: "5. Semantic & Mathematical Validation", 
              desc: "Cross-checks numeric formats, dates, boundary descriptions, and parcel areas to ensure strict internal consistency." 
            },
            { 
              icon: Map, 
              title: "6. Cadastral GIS Alignment", 
              desc: "Connects textual deeds with spatial parcel maps to verify boundaries and prevent fraudulent overlapping registrations." 
            },
            { 
              icon: Users, 
              title: "7. Revenue Officer Verification", 
              desc: "Enables authorized revenue officers to audit flagged records side-by-side with original scanned documents." 
            },
            { 
              icon: Database, 
              title: "8. Sovereign Digital Registry", 
              desc: "Secures finalized records in an immutable, legally verifiable digital repository accessible across departmental nodes." 
            }
          ].map((step, idx) => (
            <div key={idx} className="relative pl-8 md:pl-10">
              <div className="absolute -left-[17px] top-1.5 w-8 h-8 bg-white border-2 border-amber-600 rounded-full flex items-center justify-center shadow-xs">
                <step.icon className="w-4 h-4 text-amber-700" />
              </div>
              <div className="bg-white border border-gray-200 p-4 rounded-lg shadow-xs hover:border-amber-400 transition-colors">
                <h3 className="text-base font-bold text-gray-900 mb-1">{step.title}</h3>
                <p className="text-sm text-gray-600 leading-relaxed">{step.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 5. What We Built (Full Width Platform Architecture - No Tech Stack) */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-slate-50 border border-gray-200 p-6 sm:p-8 rounded-lg">
          <h2 className="text-lg font-bold text-gray-900 uppercase tracking-wide border-b-2 border-amber-600 inline-block pb-1 mb-4">
            What We Built
          </h2>
          <p className="text-sm text-gray-700 leading-relaxed mb-6 max-w-4xl">
            An institutional-grade platform engineered to digitize, index, and validate complex regional land registries. Designed specifically for offline or air-gapped sovereign deployment inside state and national data centers.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {[
              {
                title: "Asynchronous Processing Engine",
                desc: "Handles large-scale historical document archives and multi-page deed batches without bottlenecking frontline operations."
              },
              {
                title: "Specialized Document Understanding",
                desc: "Models tailored for regional cadastral nomenclature, non-standard tabular formats, and legacy handwriting."
              },
              {
                title: "Tehsildar Audit Station",
                desc: "Interactive split-screen interface allowing officers to verify original scans against extracted values with single-click sign-off."
              },
              {
                title: "Cadastral GIS Cross-Referencing",
                desc: "Direct integration between textual legal deeds and digitized village maps to immediately detect overlapping boundary disputes."
              },
              {
                title: "Role-Based Administrative Control",
                desc: "Strict compartmentalization separating citizen viewing, verification officer auditing, and administrative governance."
              },
              {
                title: "Tamper-Evident Digital Repository",
                desc: "Permanent record storage ensuring chain-of-custody tracking, cryptographic audit trails, and instant legal retrieval."
              }
            ].map((item, idx) => (
              <div key={idx} className="bg-white p-4 border border-gray-200 rounded shadow-xs">
                <div className="flex items-center gap-2 mb-2 text-emerald-700 font-bold text-sm">
                  <CheckCircle className="w-4 h-4 shrink-0" />
                  <span>{item.title}</span>
                </div>
                <p className="text-xs text-gray-600 leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 6. Visual Section: Information Extraction Demo */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-amber-50/70 border border-amber-200 p-6 sm:p-8 rounded-lg">
          <div className="mb-6 text-center">
            <h2 className="text-lg font-bold text-gray-900 uppercase tracking-wide">
              Automated Information Extraction
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              Translating complex, tabular physical records into structured digital data.
            </p>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Example 1: Hindi Document */}
            <div className="bg-white border border-gray-200 rounded shadow-xs overflow-hidden flex flex-col">
              <div className="bg-gray-100 px-4 py-2.5 text-xs font-bold text-gray-700 border-b border-gray-200">
                Sample Regional Record (Hindi)
              </div>
              <div className="p-5 grid grid-cols-1 sm:grid-cols-2 gap-4 flex-1">
                <div className="bg-gray-50 border border-gray-200 rounded flex items-center justify-center p-4">
                  <div className="text-gray-500 font-mono text-xs text-center leading-relaxed">
                    [Scanned Document Sample]<br/><br/>
                    खाता संख्या: १५<br/>
                    खातेदार: राम कुमार<br/>
                    खसरा: १२३/४<br/>
                    क्षेत्रफल: ०.५० हेक्ट.
                  </div>
                </div>
                <div className="flex flex-col justify-center space-y-2.5 text-xs">
                  <div className="flex justify-between border-b border-gray-100 pb-1.5">
                    <span className="text-gray-500">Khata No.</span>
                    <span className="font-bold text-gray-900 font-mono">15</span>
                  </div>
                  <div className="flex justify-between border-b border-gray-100 pb-1.5">
                    <span className="text-gray-500">Owner</span>
                    <span className="font-bold text-gray-900">Ram Kumar</span>
                  </div>
                  <div className="flex justify-between border-b border-gray-100 pb-1.5">
                    <span className="text-gray-500">Khasra/Survey</span>
                    <span className="font-bold text-gray-900 font-mono">123/4</span>
                  </div>
                  <div className="flex justify-between pb-1">
                    <span className="text-gray-500">Area</span>
                    <span className="font-bold text-gray-900 font-mono">0.50 Hectares</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Example 2: English Document */}
            <div className="bg-white border border-gray-200 rounded shadow-xs overflow-hidden flex flex-col">
              <div className="bg-gray-100 px-4 py-2.5 text-xs font-bold text-gray-700 border-b border-gray-200">
                Sample Cadastral Record (English)
              </div>
              <div className="p-5 grid grid-cols-1 sm:grid-cols-2 gap-4 flex-1">
                <div className="bg-gray-50 border border-gray-200 rounded flex items-center justify-center p-4">
                  <div className="text-gray-500 font-mono text-xs text-center leading-relaxed">
                    [Scanned Document Sample]<br/><br/>
                    Survey No: 45A<br/>
                    Title Holder: S. Patel<br/>
                    Sub-Division: 2<br/>
                    Extent: 1.2 Acres
                  </div>
                </div>
                <div className="flex flex-col justify-center space-y-2.5 text-xs">
                  <div className="flex justify-between border-b border-gray-100 pb-1.5">
                    <span className="text-gray-500">Survey No.</span>
                    <span className="font-bold text-gray-900 font-mono">45A</span>
                  </div>
                  <div className="flex justify-between border-b border-gray-100 pb-1.5">
                    <span className="text-gray-500">Title Holder</span>
                    <span className="font-bold text-gray-900">S. Patel</span>
                  </div>
                  <div className="flex justify-between border-b border-gray-100 pb-1.5">
                    <span className="text-gray-500">Sub-Division</span>
                    <span className="font-bold text-gray-900 font-mono">2</span>
                  </div>
                  <div className="flex justify-between pb-1">
                    <span className="text-gray-500">Area (Extent)</span>
                    <span className="font-bold text-gray-900 font-mono">1.2 Acres</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 7. Impact & Benefits */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <h2 className="text-lg font-bold text-gray-900 uppercase tracking-wide border-b-2 border-amber-600 inline-block pb-1">
            Impact & Benefits
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white p-6 border border-gray-200 rounded-lg shadow-xs">
            <div className="flex items-center gap-2 mb-3">
              <Building className="w-5 h-5 text-amber-700" />
              <h3 className="text-base font-bold text-gray-900">For Government Departments</h3>
            </div>
            <ul className="space-y-2.5 text-sm text-gray-700">
              <li>• Drastic reduction in manual data entry backlogs across revenue offices.</li>
              <li>• Automated detection of spatial overlaps and fraudulent registrations.</li>
              <li>• Establishment of a centralized, auditable, and secure document archive.</li>
              <li>• Enhanced capability to monitor revenue operations via dashboard analytics.</li>
            </ul>
          </div>
          <div className="bg-white p-6 border border-gray-200 rounded-lg shadow-xs">
            <div className="flex items-center gap-2 mb-3">
              <Users className="w-5 h-5 text-amber-700" />
              <h3 className="text-base font-bold text-gray-900">For Citizens</h3>
            </div>
            <ul className="space-y-2.5 text-sm text-gray-700">
              <li>• Faster processing of mutation requests and property transfers.</li>
              <li>• Increased transparency and direct accessibility to verified land records.</li>
              <li>• Significant reduction in protracted land disputes and litigation.</li>
              <li>• Assurance of clear ownership through cross-validated digital registries.</li>
            </ul>
          </div>
        </div>
      </section>
    </div>
  );
}
