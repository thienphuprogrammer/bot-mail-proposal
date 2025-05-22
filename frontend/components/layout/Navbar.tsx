"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { Menu, X, Mail, FileText, MessageSquare, Home } from "lucide-react";

const Navbar = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <header
      className={cn(
        "fixed top-0 w-full z-50 transition-all duration-300 ease-in-out py-4 px-6 md:px-8",
        isScrolled
          ? "bg-[#1A1A1A]/95 backdrop-blur-sm shadow-md"
          : "bg-transparent"
      )}
    >
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <Link 
          href="/" 
          className="flex items-center space-x-2 transition-transform duration-300 hover:scale-105"
        >
          <div className="bg-[#FF4D4D] rounded-lg p-1">
            <span className="text-white font-bold text-sm">AI</span>
          </div>
          <span className="font-bold text-lg">Enterprise Hub</span>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center space-x-8">
          <NavLink href="/" icon={<Home size={18} />}>Home</NavLink>
          <NavLink href="/emails" icon={<Mail size={18} />}>Emails</NavLink>
          <NavLink href="/proposals" icon={<FileText size={18} />}>Proposals</NavLink>
          <NavLink href="/chat" icon={<MessageSquare size={18} />}>Chat</NavLink>
        </nav>

        {/* Mobile Menu Button */}
        <button
          className="md:hidden text-white"
          onClick={() => setIsMenuOpen(!isMenuOpen)}
        >
          {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Mobile Navigation */}
      <div
        className={cn(
          "fixed left-0 right-0 top-[72px] bg-[#1A1A1A] shadow-lg md:hidden transition-all duration-300 ease-in-out z-40",
          isMenuOpen ? "translate-y-0 opacity-100" : "-translate-y-full opacity-0"
        )}
      >
        <div className="p-6 flex flex-col space-y-6">
          <MobileNavLink href="/" icon={<Home size={18} />}>Home</MobileNavLink>
          <MobileNavLink href="/emails" icon={<Mail size={18} />}>Emails</MobileNavLink>
          <MobileNavLink href="/proposals" icon={<FileText size={18} />}>Proposals</MobileNavLink>
          <MobileNavLink href="/chat" icon={<MessageSquare size={18} />}>Chat</MobileNavLink>
        </div>
      </div>
    </header>
  );
};

const NavLink = ({ href, children, icon }: { href: string; children: React.ReactNode; icon: React.ReactNode }) => (
  <Link
    href={href}
    className="flex items-center space-x-2 text-gray-300 hover:text-white transition-all duration-300 ease-in-out relative group"
  >
    {icon}
    <span>{children}</span>
    <span className="absolute left-0 bottom-0 w-0 h-0.5 bg-[#FF4D4D] transition-all duration-300 ease-in-out group-hover:w-full" />
  </Link>
);

const MobileNavLink = ({ 
  href, 
  children,
  icon
}: { 
  href: string; 
  children: React.ReactNode;
  icon: React.ReactNode;
}) => (
  <Link
    href={href}
    className="flex items-center space-x-3 text-gray-300 hover:text-white transition-all duration-300 ease-in-out px-2 py-3 rounded-lg hover:bg-white/5"
  >
    {icon}
    <span>{children}</span>
  </Link>
);

export default Navbar;