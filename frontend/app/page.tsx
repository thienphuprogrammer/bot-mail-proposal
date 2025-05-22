import Link from "next/link";
import Image from "next/image";
import { cn } from "@/lib/utils";
import ProductCard from "@/components/ui/ProductCard";

export default function Home() {
  return (
    <div className="pt-24">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-radial from-[#FF4D4D]/10 via-transparent to-transparent opacity-70 pointer-events-none" />
        
        <div className="max-w-7xl mx-auto px-6 md:px-8 py-16 md:py-24">
          <div className="text-center max-w-3xl mx-auto">
            <h1 className="text-4xl md:text-6xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
              AI-Powered Enterprise Hub
            </h1>
            <p className="text-gray-400 text-lg md:text-xl mb-10">
              AI Model Tool Hub offers pre-trained and customizable models for tasks like data analysis, 
              image recognition, natural language processing (NLP), and predictive forecasting.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                href="/chat"
                className="bg-[#FF4D4D] hover:bg-[#FF6B6B] text-white px-8 py-3 rounded-xl transition-all duration-300 ease-in-out transform hover:scale-105 hover:shadow-lg w-full sm:w-auto"
              >
                Try Ivy Chat
              </Link>
              <Link
                href="#products"
                className="bg-transparent border border-gray-700 hover:border-gray-500 text-white px-8 py-3 rounded-xl transition-all duration-300 ease-in-out hover:bg-white/5 w-full sm:w-auto"
              >
                Explore Products
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Products Grid Section */}
      <section id="products" className="max-w-7xl mx-auto px-6 md:px-8 py-16">
        <h2 className="text-3xl font-bold mb-2">Our AI Products</h2>
        <p className="text-gray-400 mb-10">Explore our suite of AI-powered tools for enterprise</p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <ProductCard
            title="Ivy Chat"
            icon="MessageSquare"
            description="Smart Q&A with your documents, SQL Agent data insights, and AI-powered translation."
            features={[
              "Direct Q&A with documents",
              "Data insights via SQL Agent",
              "AI translation between multiple languages"
            ]}
            color="#FF4D4D"
            href="/chat"
            available={true}
          />
          
          <ProductCard
            title="Ivy Sales"
            icon="Target"
            description="Identifies potential leads and auto-generates outreach requests."
            features={[
              "Opportunity detection",
              "Request management and categorization"
            ]}
            color="#4D79FF"
            href="#"
            available={true}
          />
          
          <ProductCard
            title="Ivy RM"
            icon="Users"
            description="Generate job descriptions, suggest roles, and match people to positions."
            features={[
              "AI job description generator",
              "Role suggestions for employers",
              "Candidate-position matchmaking"
            ]}
            color="#4DFF91"
            href="#"
            available={true}
          />
          
          <ProductCard
            title="Ivy Intranet"
            icon="FileText"
            description="Internal agents for document access, legal risk scanning, and invoice verification."
            features={[
              "Internal agents - SharePoint integration",
              "IP Risk Search Agent",
              "OCR/Form Agent"
            ]}
            color="#FFB54D"
            href="#"
            available={true}
          />
          
          <ProductCard
            title="Ivy Analytics"
            icon="BarChart2"
            description="Ensure data quality, build models, chat with SQL, and integrate with dashboards."
            features={[
              "AI data quality & profiling",
              "Advanced ML model training",
              "No-code dashboard builder"
            ]}
            color="#B64DFF"
            href="#"
            available={true}
          />
          
          <ProductCard
            title="Ivy HR"
            icon="Award"
            description="Ivy HR is your AI-powered HR partner, providing employee tracking, career planning, and employee churn management."
            features={[
              "Visualize data to aid management decisions",
              "Predict employee turnover risks",
              "Enhanced onboarding and data management"
            ]}
            color="#FF4D8B"
            href="#"
            available={false}
          />
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-gradient-to-r from-[#1A1A1A] to-[#292929] mt-12">
        <div className="max-w-7xl mx-auto px-6 md:px-8 py-16 md:py-24">
          <div className="bg-[#222222] rounded-2xl p-8 md:p-12 shadow-xl relative overflow-hidden">
            <div className="absolute top-0 right-0 w-64 h-64 bg-[#FF4D4D]/10 rounded-full blur-3xl transform translate-x-1/4 -translate-y-1/4"></div>
            
            <div className="relative z-10 max-w-2xl">
              <h2 className="text-3xl md:text-4xl font-bold mb-6">
                Ready to transform your enterprise with AI?
              </h2>
              <p className="text-gray-300 mb-10">
                Join thousands of businesses that are leveraging our AI tools to streamline operations, 
                increase productivity, and drive innovation.
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <Link
                  href="/chat"
                  className="bg-[#FF4D4D] hover:bg-[#FF6B6B] text-white px-8 py-3 rounded-xl transition-all duration-300 ease-in-out transform hover:scale-105 hover:shadow-lg text-center"
                >
                  Get Started Now
                </Link>
                <Link
                  href="#"
                  className="bg-transparent border border-gray-700 hover:border-gray-500 text-white px-8 py-3 rounded-xl transition-all duration-300 ease-in-out hover:bg-white/5 text-center"
                >
                  Contact Sales
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}