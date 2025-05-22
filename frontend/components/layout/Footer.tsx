import Link from "next/link";
import { cn } from "@/lib/utils";
import { Github, Twitter, Linkedin, Mail } from "lucide-react";

const Footer = () => {
  return (
    <footer className="bg-[#111111] pt-16 pb-8 mt-12">
      <div className="max-w-7xl mx-auto px-6 md:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10 mb-12">
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <div className="bg-[#FF4D4D] rounded-lg p-1">
                <span className="text-white font-bold text-sm">AI</span>
              </div>
              <span className="font-bold text-lg">Enterprise Hub</span>
            </div>
            <p className="text-gray-400 text-sm">
              AI-powered solutions helping businesses transform their operations and improve efficiency.
            </p>
            <div className="flex space-x-4 pt-2">
              <SocialIcon icon={<Github size={18} />} href="#" />
              <SocialIcon icon={<Twitter size={18} />} href="#" />
              <SocialIcon icon={<Linkedin size={18} />} href="#" />
              <SocialIcon icon={<Mail size={18} />} href="#" />
            </div>
          </div>

          <FooterLinks
            title="Products"
            links={[
              { label: "Ivy Chat", href: "/chat" },
              { label: "Ivy Sales", href: "#" },
              { label: "Ivy RM", href: "#" },
              { label: "Ivy Analytics", href: "#" },
            ]}
          />

          <FooterLinks
            title="Company"
            links={[
              { label: "About", href: "#" },
              { label: "Careers", href: "#" },
              { label: "Blog", href: "#" },
              { label: "Contact", href: "#" },
            ]}
          />

          <FooterLinks
            title="Resources"
            links={[
              { label: "Documentation", href: "#" },
              { label: "API Reference", href: "#" },
              { label: "Tutorials", href: "#" },
              { label: "Community", href: "#" },
            ]}
          />
        </div>

        <div className="border-t border-gray-800 pt-8 mt-8 text-center text-gray-500 text-sm">
          <p>© {new Date().getFullYear()} AI Enterprise Hub. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};

const SocialIcon = ({ icon, href }: { icon: React.ReactNode; href: string }) => (
  <Link
    href={href}
    className="bg-gray-800 p-2 rounded-full hover:bg-[#FF4D4D] transition-all duration-300 ease-in-out transform hover:scale-110"
  >
    {icon}
  </Link>
);

const FooterLinks = ({
  title,
  links,
}: {
  title: string;
  links: { label: string; href: string }[];
}) => (
  <div className="space-y-4">
    <h3 className="font-semibold text-white">{title}</h3>
    <ul className="space-y-3">
      {links.map((link) => (
        <li key={link.label}>
          <Link
            href={link.href}
            className="text-gray-400 hover:text-white transition-colors duration-300 ease-in-out text-sm"
          >
            {link.label}
          </Link>
        </li>
      ))}
    </ul>
  </div>
);

export default Footer;