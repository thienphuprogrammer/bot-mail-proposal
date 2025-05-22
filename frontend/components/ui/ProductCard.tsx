"use client";

import Link from "next/link";
import { cn } from "@/lib/utils";
import { 
  MessageSquare, 
  Target, 
  Users, 
  FileText, 
  BarChart2, 
  Award,
  ArrowRight
} from "lucide-react";
import { useState } from "react";

type IconName = "MessageSquare" | "Target" | "Users" | "FileText" | "BarChart2" | "Award";

interface ProductCardProps {
  title: string;
  icon: IconName;
  description: string;
  features: string[];
  color: string;
  href: string;
  available: boolean;
}

const ProductCard = ({
  title,
  icon,
  description,
  features,
  color,
  href,
  available
}: ProductCardProps) => {
  const [isHovered, setIsHovered] = useState(false);

  const IconComponent = () => {
    switch (icon) {
      case "MessageSquare":
        return <MessageSquare size={24} />;
      case "Target":
        return <Target size={24} />;
      case "Users":
        return <Users size={24} />;
      case "FileText":
        return <FileText size={24} />;
      case "BarChart2":
        return <BarChart2 size={24} />;
      case "Award":
        return <Award size={24} />;
      default:
        return <MessageSquare size={24} />;
    }
  };

  return (
    <div 
      className={cn(
        "bg-[#222222] rounded-xl overflow-hidden transition-all duration-300 ease-in-out border border-gray-800 hover:border-gray-700",
        isHovered ? "shadow-lg transform scale-[1.02]" : "shadow-md"
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div 
            className="w-10 h-10 rounded-lg flex items-center justify-center" 
            style={{ backgroundColor: color }}
          >
            <IconComponent />
          </div>
          {!available && (
            <span className="bg-gray-800 text-gray-300 text-xs px-2 py-1 rounded-lg">
              Coming soon
            </span>
          )}
        </div>
        
        <h3 className="text-xl font-semibold mb-2">{title}</h3>
        <p className="text-gray-400 text-sm mb-4">{description}</p>
        
        <ul className="space-y-2 mb-6">
          {features.map((feature, index) => (
            <li key={index} className="flex items-start">
              <span className="text-green-400 mr-2">•</span>
              <span className="text-gray-300 text-sm">{feature}</span>
            </li>
          ))}
        </ul>
        
        {available ? (
          <Link 
            href={href}
            className={cn(
              "w-full flex items-center justify-center py-2 rounded-lg text-white transition-all duration-300 ease-in-out",
              "hover:opacity-90 group"
            )}
            style={{ backgroundColor: color }}
          >
            <span>Start engine</span>
            <ArrowRight 
              size={16} 
              className="ml-2 transition-transform duration-300 group-hover:translate-x-1" 
            />
          </Link>
        ) : (
          <button
            className="w-full flex items-center justify-center py-2 rounded-lg bg-gray-800 text-gray-400 cursor-not-allowed"
            disabled
          >
            Coming soon
          </button>
        )}
      </div>
    </div>
  );
};

export default ProductCard;