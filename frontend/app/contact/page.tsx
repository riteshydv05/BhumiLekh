"use client";

import React from "react";
import Breadcrumb from "@/components/layout/Breadcrumb";
import { Mail, Phone, MapPin, Send } from "lucide-react";

export default function ContactPage() {
  return (
    <div>
      <Breadcrumb items={[{ label: "Contact Us" }]} />

      <div className="max-w-4xl mx-auto px-4 py-8 sm:px-6 lg:px-8 space-y-6">
        <div className="border-b border-gray-200 pb-4">
          <h1 className="text-xl font-bold text-gray-950 uppercase tracking-tight flex items-center gap-2">
            <Mail className="w-5 h-5 text-amber-700" />
            <span>Contact & Support Information</span>
          </h1>
          <p className="text-xs text-gray-600 mt-1">
            Reach out to the technical support team and Nodal Officers for land digitization queries.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Contact Details */}
          <div className="gov-card p-6 space-y-4 text-xs text-gray-700">
            <h2 className="text-sm font-bold text-gray-900 border-b border-gray-100 pb-2">
              Nodal Office Coordinates
            </h2>

            <div className="space-y-3">
              <div className="flex items-start gap-2.5">
                <MapPin className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-gray-900">National Land Record Center</p>
                  <p className="text-gray-600">Department of Land Resources</p>
                  <p className="text-gray-600">New Delhi - 110001, India</p>
                </div>
              </div>

              <div className="flex items-center gap-2.5">
                <Phone className="w-4 h-4 text-amber-700 shrink-0" />
                <div>
                  <p className="font-semibold text-gray-900">Toll-Free Helpline</p>
                  <p className="text-gray-600">1800-11-LAND (1800-11-5263)</p>
                </div>
              </div>

              <div className="flex items-center gap-2.5">
                <Mail className="w-4 h-4 text-amber-700 shrink-0" />
                <div>
                  <p className="font-semibold text-gray-900">Support Email</p>
                  <p className="text-gray-600">support.landrecords@nic.in</p>
                </div>
              </div>
            </div>
          </div>

          {/* Inquiry Form */}
          <div className="gov-card p-6 space-y-4">
            <h2 className="text-sm font-bold text-gray-900 border-b border-gray-100 pb-2">
              Send Technical Feedback / Inquiry
            </h2>

            <form onSubmit={(e) => { e.preventDefault(); alert("Inquiry submitted successfully."); }} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-gray-700 mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  placeholder="Officer / Citizen Name"
                  className="w-full px-3 py-1.5 border border-gray-300 rounded focus:outline-none focus:border-amber-600 text-xs"
                />
              </div>

              <div>
                <label className="block font-semibold text-gray-700 mb-1">Official Email Address</label>
                <input
                  type="email"
                  required
                  placeholder="name@gov.in"
                  className="w-full px-3 py-1.5 border border-gray-300 rounded focus:outline-none focus:border-amber-600 text-xs"
                />
              </div>

              <div>
                <label className="block font-semibold text-gray-700 mb-1">Message / Issue Details</label>
                <textarea
                  rows={3}
                  required
                  placeholder="Specify land record ID or system inquiry..."
                  className="w-full px-3 py-1.5 border border-gray-300 rounded focus:outline-none focus:border-amber-600 text-xs"
                />
              </div>

              <button
                type="submit"
                className="w-full py-2 bg-amber-600 hover:bg-amber-700 text-white font-semibold rounded text-xs uppercase tracking-wider flex items-center justify-center gap-1.5"
              >
                <Send className="w-3.5 h-3.5" />
                <span>Submit Inquiry</span>
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
