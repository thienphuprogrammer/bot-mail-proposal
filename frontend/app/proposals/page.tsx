"use client";

import { useState } from "react";
import { FileText, Download, Mail, Clock, Edit2 } from "lucide-react";
import { format } from "date-fns";

interface Proposal {
  id: string;
  title: string;
  client: string;
  createdAt: string;
  status: "draft" | "sent" | "approved" | "rejected";
  versions: number;
}

export default function ProposalsPage() {
  const [proposals, setProposals] = useState<Proposal[]>([
    {
      id: "1",
      title: "Website Redesign Proposal",
      client: "Tech Corp",
      createdAt: new Date().toISOString(),
      status: "draft",
      versions: 2,
    },
    // Add more sample proposals
  ]);

  return (
    <div className="pt-24 min-h-screen">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold">Proposals</h1>
          <button className="bg-[#FF4D4D] hover:bg-[#FF6B6B] text-white px-6 py-2 rounded-lg transition-colors duration-300">
            New Proposal
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {proposals.map((proposal) => (
            <div
              key={proposal.id}
              className="bg-[#222222] rounded-xl border border-gray-800 overflow-hidden shadow-xl hover:border-[#FF4D4D]/50 transition-colors duration-300"
            >
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="font-semibold text-lg mb-1">{proposal.title}</h3>
                    <p className="text-gray-400 text-sm">{proposal.client}</p>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium ${
                      proposal.status === "draft"
                        ? "bg-yellow-500/20 text-yellow-500"
                        : proposal.status === "sent"
                        ? "bg-blue-500/20 text-blue-500"
                        : proposal.status === "approved"
                        ? "bg-green-500/20 text-green-500"
                        : "bg-red-500/20 text-red-500"
                    }`}
                  >
                    {proposal.status.charAt(0).toUpperCase() + proposal.status.slice(1)}
                  </span>
                </div>

                <div className="flex items-center gap-4 text-sm text-gray-400 mb-6">
                  <div className="flex items-center gap-1">
                    <Clock size={14} />
                    {format(new Date(proposal.createdAt), "MMM d, yyyy")}
                  </div>
                  <div className="flex items-center gap-1">
                    <Edit2 size={14} />
                    {proposal.versions} versions
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button className="flex-1 flex items-center justify-center gap-2 bg-[#2A2A2A] hover:bg-[#333333] text-white px-4 py-2 rounded-lg transition-colors duration-300">
                    <Download size={16} />
                    PDF
                  </button>
                  <button className="flex-1 flex items-center justify-center gap-2 bg-[#2A2A2A] hover:bg-[#333333] text-white px-4 py-2 rounded-lg transition-colors duration-300">
                    <Mail size={16} />
                    Share
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}