"use client";

import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { Search, Filter, RefreshCw, Mail } from "lucide-react";
import { format } from "date-fns";

interface Email {
  id: string;
  subject: string;
  sender: string;
  date: string;
  content: string;
}

export default function EmailsPage() {
  const [emails, setEmails] = useState<Email[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [sortBy, setSortBy] = useState<"date" | "sender" | "subject">("date");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  const { register, handleSubmit } = useForm({
    defaultValues: {
      search: "",
      filter: "all",
    },
  });

  useEffect(() => {
    // Simulated email fetch
    setTimeout(() => {
      setEmails([
        {
          id: "1",
          subject: "Project Proposal Request",
          sender: "client@example.com",
          date: new Date().toISOString(),
          content: "We need a proposal for our upcoming project...",
        },
        // Add more sample emails
      ]);
      setIsLoading(false);
    }, 1000);
  }, []);

  const handleRefresh = () => {
    setIsLoading(true);
    // Implement refresh logic
    setTimeout(() => setIsLoading(false), 1000);
  };

  return (
    <div className="pt-24 min-h-screen">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold">Email Management</h1>
          <button
            onClick={handleRefresh}
            className="flex items-center gap-2 bg-[#FF4D4D] hover:bg-[#FF6B6B] text-white px-4 py-2 rounded-lg transition-colors duration-300"
          >
            <RefreshCw size={18} />
            Refresh
          </button>
        </div>

        <div className="bg-[#222222] rounded-xl border border-gray-800 overflow-hidden shadow-xl">
          {/* Search and Filter Bar */}
          <div className="p-4 border-b border-gray-800 bg-[#1D1D1D] flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
                <input
                  type="text"
                  placeholder="Search emails..."
                  className="w-full bg-[#2A2A2A] border border-gray-800 rounded-lg pl-10 pr-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#FF4D4D]/50 focus:border-[#FF4D4D]"
                  {...register("search")}
                />
              </div>
            </div>

            <div className="flex gap-4">
              <select
                className="bg-[#2A2A2A] border border-gray-800 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-[#FF4D4D]/50 focus:border-[#FF4D4D]"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as "date" | "sender" | "subject")}
              >
                <option value="date">Sort by Date</option>
                <option value="sender">Sort by Sender</option>
                <option value="subject">Sort by Subject</option>
              </select>

              <button
                onClick={() => setSortOrder(sortOrder === "asc" ? "desc" : "asc")}
                className="bg-[#2A2A2A] border border-gray-800 rounded-lg px-4 py-2 text-white hover:bg-[#333333] transition-colors duration-300"
              >
                {sortOrder === "asc" ? "↑" : "↓"}
              </button>
            </div>
          </div>

          {/* Email List */}
          <div className="divide-y divide-gray-800">
            {isLoading ? (
              <div className="p-8 text-center">
                <div className="animate-spin inline-block w-8 h-8 border-4 border-[#FF4D4D] border-t-transparent rounded-full mb-4"></div>
                <p className="text-gray-400">Loading emails...</p>
              </div>
            ) : emails.length === 0 ? (
              <div className="p-8 text-center">
                <Mail size={48} className="text-gray-400 mx-auto mb-4" />
                <p className="text-gray-400">No emails found</p>
              </div>
            ) : (
              emails.map((email) => (
                <div
                  key={email.id}
                  className="p-4 hover:bg-[#2A2A2A] transition-colors duration-300 cursor-pointer"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <p className="font-semibold text-white truncate">{email.subject}</p>
                      <p className="text-sm text-gray-400 truncate">{email.sender}</p>
                    </div>
                    <p className="text-sm text-gray-400 whitespace-nowrap">
                      {format(new Date(email.date), "MMM d, yyyy")}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Pagination */}
          <div className="p-4 border-t border-gray-800 bg-[#1D1D1D] flex justify-between items-center">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-4 py-2 rounded-lg bg-[#2A2A2A] text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[#333333] transition-colors duration-300"
            >
              Previous
            </button>
            <span className="text-gray-400">Page {currentPage}</span>
            <button
              onClick={() => setCurrentPage((p) => p + 1)}
              disabled={emails.length < 10}
              className="px-4 py-2 rounded-lg bg-[#2A2A2A] text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[#333333] transition-colors duration-300"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}