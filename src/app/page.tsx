"use client";

import React, { useState, useEffect } from "react";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { initSmoothScroll, scrollTo, destroySmoothScroll } from "@/lib/smooth-scroll";

export default function Home() {
  const [activeSection, setActiveSection] = useState("");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    // Initialize smooth scroll
    initSmoothScroll();

    const handleScroll = () => {
      const sections = ["hero", "about", "skills", "experience", "work", "contact"];
      const scrollPosition = window.scrollY + 100;

      for (const section of sections) {
        const element = document.getElementById(section);
        if (element) {
          const { offsetTop, offsetHeight } = element;
          if (scrollPosition >= offsetTop && scrollPosition < offsetTop + offsetHeight) {
            setActiveSection(section);
            break;
          }
        }
      }
    };

    const handleClickOutside = (event: MouseEvent) => {
      const nav = document.querySelector('nav');
      if (nav && !nav.contains(event.target as Node) && mobileMenuOpen) {
        setMobileMenuOpen(false);
      }
    };

    window.addEventListener("scroll", handleScroll);
    document.addEventListener("mousedown", handleClickOutside);
    
    return () => {
      window.removeEventListener("scroll", handleScroll);
      document.removeEventListener("mousedown", handleClickOutside);
      destroySmoothScroll();
    };
  }, [mobileMenuOpen]);

  const scrollToSection = (sectionId: string) => {
    setMobileMenuOpen(false); // Close mobile menu after navigation
    document.body.style.overflow = 'unset'; // Restore body scroll
    
    // Small delay to ensure smooth menu closure
    setTimeout(() => {
      scrollTo(`#${sectionId}`);
    }, 50);
  };

  const toggleMobileMenu = () => {
    setMobileMenuOpen(!mobileMenuOpen);
    // Prevent body scroll when mobile menu is open
    if (!mobileMenuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
  };

  // Clean up body scroll lock on component unmount
  useEffect(() => {
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, []);

  return (
    <div className="min-h-screen bg-background parallax-bg">
      {/* Mobile Menu Backdrop */}
      {mobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-black/20 z-40 md:hidden mobile-backdrop"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-background/95 border-b border-border elegant-glow">
        <div className="max-w-6xl mx-auto px-6 py-3 md:py-4">
          <div className="flex items-center justify-between">
            <div className="font-display text-xl font-medium gradient-text">
              Abdullah Ahmed
            </div>
            
            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center space-x-8">
              {[
                { id: "hero", label: "Home" },
                { id: "about", label: "About" },
                { id: "skills", label: "Skills" },
                { id: "experience", label: "Experience" },
                { id: "work", label: "Work" },
                { id: "contact", label: "Contact" },
              ].map((item) => (
                <button
                  key={item.id}
                  onClick={() => scrollToSection(item.id)}
                  className={`font-display text-sm transition-all duration-300 hover:text-primary relative cursor-pointer ${
                    activeSection === item.id ? "text-primary" : "text-muted-foreground"
                  }`}
                >
                  {item.label}
                  {activeSection === item.id && (
                    <div className="absolute -bottom-1 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary to-transparent" />
                  )}
                </button>
              ))}
            </div>

            {/* Mobile Hamburger */}
            <button
              onClick={toggleMobileMenu}
              className={`md:hidden hamburger text-foreground cursor-pointer ${mobileMenuOpen ? 'open' : ''}`}
              aria-label="Toggle mobile menu"
            >
              <span></span>
              <span></span>
              <span></span>
              <span></span>
            </button>
          </div>

          {/* Mobile Navigation Menu */}
          <div className={`md:hidden mobile-menu ${mobileMenuOpen ? 'open' : ''} mt-2 pb-2 border-t border-border/50 bg-background rounded-lg mx-2`}>
            <div className="flex flex-col items-center space-y-1 pt-2 px-2">
              {[
                { id: "hero", label: "Home" },
                { id: "about", label: "About" },
                { id: "skills", label: "Skills" },
                { id: "experience", label: "Experience" },
                { id: "work", label: "Work" },
                { id: "contact", label: "Contact" },
              ].map((item, index) => (
                <button
                  key={item.id}
                  onClick={() => scrollToSection(item.id)}
                  className={`mobile-menu-item font-display text-center px-4 py-3 text-base font-medium transition-all duration-300 hover:text-primary relative cursor-pointer ${
                    activeSection === item.id ? "text-primary" : "text-muted-foreground"
                  }`}
                  style={{ '--delay': `${index * 0.1}s` } as React.CSSProperties}
                >
                  {item.label}
                  {activeSection === item.id && (
                    <div className="absolute -bottom-1 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary to-transparent" />
                  )}
                </button>
              ))}
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section id="hero" className="min-h-screen flex items-center justify-center px-6 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-primary/3 pointer-events-none" />
        <div className="max-w-5xl mx-auto text-center relative z-10">
          <div className="mb-12">
            <div className="mb-6">
            
              <h1 className="font-display text-6xl md:text-8xl font-light leading-tight mb-8 text-balance gradient-text text-shadow-elegant">
                Abdullah Ahmed
              </h1>
            </div>
            {/* Removed ornamental divider */}
            <p className="text-xl md:text-2xl text-foreground font-light leading-relaxed max-w-3xl mx-auto text-balance mb-8">
              Computer Science student building innovative software solutions with modern technologies, where clean code meets intelligent design and every project solves real-world problems.
            </p>
          </div>
          <div className="flex flex-col sm:flex-row gap-6 justify-center items-center">
            <Button
              onClick={() => scrollToSection("work")}
              variant="primary"
              size="lg"
              className="w-48"
            >
              Explore My Work
            </Button>
            <Button
              asChild
              variant="luxury"
              size="lg"
              className="w-48"
            >
              <a href="mailto:contactabdullahahmed@gmail.com">
                Begin Conversation
              </a>
            </Button>
          </div>
        </div>
      </section>

      {/* About Section */}
      <section id="about" className="py-32 px-6 relative">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-card/20 to-transparent" />
        <div className="max-w-6xl mx-auto relative z-10">
          <div className="mb-20 text-center">
            <h2 className="font-display text-5xl md:text-6xl font-light mb-8 gradient-text">
              About me
            </h2>
            
          </div>
          
          <div className="max-w-4xl mx-auto mb-16">
            <Card className="p-10 sophisticated-card">
              
              <div className="space-y-6 text-muted-foreground leading-relaxed">
                <p>
                  As a Computer Science undergraduate, I&apos;m passionate about exploring the intersection 
                  of technology and creative problem-solving. My journey in software development has 
                  been driven by curiosity and a desire to build meaningful digital solutions.
                </p>
                <p>
                  Through academic projects and internships, I&apos;ve developed a strong foundation in 
                  full-stack development, working with modern technologies like React, TypeScript, 
                  and .NET. I enjoy tackling complex challenges and learning new frameworks that 
                  push the boundaries of what&apos;s possible.
                </p>
                <p>
                  I believe in writing clean, maintainable code and creating user experiences that 
                  are both functional and intuitive. Every project is an opportunity to grow, learn, 
                  and contribute to the evolving landscape of software development.
                </p>
              </div>
            </Card>
          </div>
        </div>
      </section>

      {/* Skills Section */}
      <section id="skills" className="pt-24 pb-32 px-6 relative">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-primary/5 to-transparent" />
        <div className="max-w-6xl mx-auto relative z-10">
          <div className="mb-20 text-center">
            <h2 className="font-display text-5xl md:text-6xl font-light mb-8 gradient-text">
              Technical Expertise
            </h2>
            <div className="ornamental-divider mb-12" />
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
              A comprehensive toolkit for crafting exceptional digital experiences
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {/* Languages */}
            <Card className="p-6 sophisticated-card rounded-2xl">
              <h3 className="font-display text-xl font-medium text-center mb-6 text-primary">
                Languages
              </h3>
              <div className="grid grid-cols-2 gap-4">
                {[
                  { name: "TypeScript", logo: "/typescript-svgrepo-com.svg" },
                  { name: "JavaScript", logo: "/js01-svgrepo-com.svg" },
                  { name: "C#", logo: "/icons8-c-sharp-logo.svg" },
                  { name: "C++", logo: "/icons8-c++.svg" }
                ].map((tech, index) => (
                  <div key={index} className="flex flex-col items-center p-3 rounded-lg hover:bg-primary/5 transition-colors duration-200">
                    <Image
                      src={tech.logo}
                      alt={tech.name}
                      width={32}
                      height={32}
                      className="w-8 h-8 object-contain mb-2"
                    />
                    <span className="text-xs text-center text-muted-foreground font-medium">
                      {tech.name}
                    </span>
                  </div>
                ))}
              </div>
            </Card>

            {/* Frameworks */}
            <Card className="p-6 sophisticated-card rounded-2xl">
              <h3 className="font-display text-xl font-medium text-center mb-6 text-primary">
                Frameworks
              </h3>
              <div className="grid grid-cols-2 gap-4">
                {[
                  { name: "React", logo: "/react-svgrepo-com.svg" },
                  { name: "Next.js", logo: "/nextjs-icon-svgrepo-com.svg" },
                  { name: "ASP .NET", logo: "/dotnet-svgrepo-com (3).svg" },
                  { name: "Tailwind", logo: "/tailwind-svgrepo-com.svg" }
                ].map((tech, index) => (
                  <div key={index} className="flex flex-col items-center p-3 rounded-lg hover:bg-primary/5 transition-colors duration-200">
                    <Image
                      src={tech.logo}
                      alt={tech.name}
                      width={32}
                      height={32}
                      className="w-8 h-8 object-contain mb-2"
                    />
                    <span className="text-xs text-center text-muted-foreground font-medium">
                      {tech.name}
                    </span>
                  </div>
                ))}
              </div>
            </Card>

            {/* Tools & Platforms */}
            <Card className="p-6 sophisticated-card rounded-2xl">
              <h3 className="font-display text-xl font-medium text-center mb-6 text-primary">
                Tools & Platforms
              </h3>
              <div className="grid grid-cols-2 gap-4">
                {[
                  { name: "PostgreSQL", logo: "/postgresql-svgrepo-com.svg" },
                  { name: "MongoDB", logo: "/mongodb-svgrepo-com.svg" },
                  { name: "Vite", logo: "/vite-svgrepo-com.svg" },
                  { name: "Vercel", logo: "/vercel-svgrepo-com.svg" }
                ].map((tech, index) => (
                  <div key={index} className="flex flex-col items-center p-3 rounded-lg hover:bg-primary/5 transition-colors duration-200">
                    <Image
                      src={tech.logo}
                      alt={tech.name}
                      width={32}
                      height={32}
                      className="w-8 h-8 object-contain mb-2"
                    />
                    <span className="text-xs text-center text-muted-foreground font-medium">
                      {tech.name}
                    </span>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </div>
      </section>

      {/* Experience Section */}
      <section id="experience" className="py-32 px-6 bg-gradient-to-b from-background via-card/10 to-background">
        <div className="max-w-6xl mx-auto">
          <div className="mb-20 text-center">
            <h2 className="font-display text-5xl md:text-6xl font-light mb-8 gradient-text">
              Professional Journey
            </h2>
            <div className="ornamental-divider mb-12" />
            
          </div>

          <div className="experience-timeline pl-8">
            {[
              {
                period: "2025",
                role: "Software Engineer Intern",
                company: "DirectFN",
                description: "Contributed to full-stack development of financial technology solutions, working with modern web technologies to build scalable and efficient applications for financial services.",
                achievements: [
                  "Developed responsive web interfaces using React and TypeScript",
                  "Built backend services with .NET and Node.js",
                  "Implemented database solutions with PostgreSQL and MongoDB",
                  "Collaborated with cross-functional teams on agile development cycles"
                ],
                technologies: ["React", "TypeScript", ".NET", "Node.js", "PostgreSQL", "MongoDB"]
              }
            ].map((job, index) => (
              <div key={index} className="relative mb-16 last:mb-0">
                <div className="timeline-dot" style={{ top: '1.5rem' }} />
                <Card className="ml-8 p-8 sophisticated-card">
                  <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between mb-6">
                    <div>
                      <h3 className="font-display text-2xl font-medium mb-2 text-primary">
                        {job.role}
                      </h3>
                      <p className="text-lg text-muted-foreground mb-1">{job.company}</p>
                      <p className="text-sm text-primary font-display tracking-wider">{job.period}</p>
                    </div>
                  </div>
                  
                  <p className="text-muted-foreground leading-relaxed mb-6">
                    {job.description}
                  </p>
                  
                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-display text-lg font-medium mb-4 text-foreground">
                        Key Achievements
                      </h4>
                      <ul className="space-y-2">
                        {job.achievements.map((achievement, i) => (
                          <li key={i} className="flex items-start gap-3 text-sm text-muted-foreground">
                            <div className="w-1.5 h-1.5 bg-primary rounded-full mt-2 flex-shrink-0" />
                            <span>{achievement}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                    
                    <div>
                      <h4 className="font-display text-lg font-medium mb-4 text-foreground">
                        Technologies
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {job.technologies.map((tech) => (
                          <span
                            key={tech}
                            className="px-3 py-1 text-xs bg-primary/10 text-primary border border-primary/20 rounded-full font-medium"
                          >
                            {tech}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </Card>
              </div>
            ))}
          </div>

         
        </div>
      </section>

      {/* Work Section */}
      <section id="work" className="py-32 px-6 relative">
        <div className="absolute inset-0 bg-gradient-to-b from-background via-card/30 to-background" />
        <div className="max-w-6xl mx-auto relative z-10">
          <div className="mb-20 text-center">
            <h2 className="font-display text-5xl md:text-6xl font-light mb-8 gradient-text">
              Projects
            </h2>
            <div className="ornamental-divider mb-12" />
            
          </div>
          
          <div className="grid lg:grid-cols-1 gap-12">
            {([
              {
                title: "Formai",
                subtitle: "AI-Powered Form Generator",
                description: "A sophisticated full-stack application that leverages Claude to generate Google Forms from natural language prompts. Features comprehensive authentication, iterative form revision, and seamless Google Forms API integration.",
                tags: ["AI/ML", "Full-Stack", "SaaS"],
                features: ["Natural Language Processing", "Google Forms API Integration", "JWT Authentication", "Real-time Form Preview", "Google OAuth 2.0", "Captcha"],
                year: "2025",
                links: {
                  live: "https://formai-frontend-one.vercel.app/",
                  github: "https://github.com/abdull-ah-med/Formai"
                }
              }
            ] as const).map((project, index) => (
              <Card key={index} className="group sophisticated-card p-8">
                <div className="mb-8">
                  <a 
                    href={project.links.live}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block w-full h-64 rounded-xl mb-6 relative overflow-hidden cursor-pointer"
                  >
                    <Image 
                      src="/formai-screenshot.png" 
                      alt="Formai AI-Powered Form Generator Screenshot"
                      fill
                      className="object-contain"
                    />
                    <div className="absolute bottom-4 right-4 text-xs text-primary font-display tracking-widest bg-black/50 px-2 py-1 rounded">
                      {project.year}
                    </div>
                  </a>
                </div>

                <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between mb-6">
                  <div>
                    <h3 className="font-display text-2xl font-medium mb-2 text-primary">
                      {project.title}
                    </h3>
                    <p className="text-lg text-muted-foreground mb-1">{project.subtitle}</p>
                  </div>
                </div>
                
                <p className="text-muted-foreground leading-relaxed mb-6">
                  {project.description}
                </p>
                
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-display text-lg font-medium mb-4 text-foreground">
                      Key Features
                    </h4>
                    <ul className="space-y-2">
                      {project.features.map((feature, i) => (
                        <li key={i} className="flex items-start gap-3 text-sm text-muted-foreground">
                          <div className="w-1.5 h-1.5 bg-primary rounded-full mt-2 flex-shrink-0" />
                          <span>{feature}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  
                  <div>
                    <h4 className="font-display text-lg font-medium mb-4 text-foreground">
                      Technologies
                    </h4>
                    <div className="flex flex-wrap gap-2 mb-6">
                      {project.tags.map((tag) => (
                        <span
                          key={tag}
                          className="px-3 py-1 text-xs bg-primary/10 text-primary border border-primary/20 rounded-full font-medium"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                    
                    {project.links && (
                      <div className="flex gap-3">
                        {project.links.live && (
                          <Button
                            asChild
                            variant="primary"
                            size="sm"
                            className="text-sm"
                          >
                            <a
                              href={project.links.live}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center gap-2"
                            >
                              <span>Live Demo</span>
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M7 17L17 7M17 7H7M17 7V17"/>
                              </svg>
                            </a>
                          </Button>
                        )}
                        {project.links.github && (
                          <Button
                            asChild
                            variant="primary"
                            size="sm"
                            className="text-sm"
                          >
                            <a
                              href={project.links.github}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center gap-2"
                            >
                              <span>GitHub</span>
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M7 17L17 7M17 7H7M17 7V17"/>
                              </svg>
                            </a>
                          </Button>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <section id="contact" className="py-32 px-6 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-primary/3" />
        <div className="max-w-5xl mx-auto text-center relative z-10">
          <div className="mb-20">
            <h2 className="font-display text-5xl md:text-6xl font-light mb-8 gradient-text">
              Let&apos;s Create Together
            </h2>
            <div className="ornamental-divider mb-12" />
            <p className="text-xl text-muted-foreground mb-8 leading-relaxed max-w-3xl mx-auto text-balance">
                I&apos;m always interested in discussing new opportunities, meaningful collaborations, 
              and innovative projects that push the boundaries of digital excellence.
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 gap-8 mb-16 max-w-2xl mx-auto">
            <Card className="p-8 sophisticated-card text-center">
              <div className="w-12 h-12 bg-primary/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <div className="w-6 h-6 bg-primary rounded-full" />
              </div>
              <h3 className="font-display text-lg font-medium mb-2 text-primary">
                New Projects
              </h3>
              <p className="text-sm text-muted-foreground">
                Looking for sophisticated digital solutions and elegant user experiences
              </p>
            </Card>
            
            <Card className="p-8 sophisticated-card text-center">
              <div className="w-12 h-12 bg-primary/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <div className="w-6 h-6 bg-primary rounded-full" />
              </div>
              <h3 className="font-display text-lg font-medium mb-2 text-primary">
                Collaborations
              </h3>
              <p className="text-sm text-muted-foreground">
                Open to partnerships with like-minded creatives and forward-thinking brands
              </p>
            </Card>
          </div>
          
          <div className="space-y-8">
            <div className="flex flex-col sm:flex-row gap-6 justify-center items-center">
              <Button 
                asChild
                variant="primary"
                size="lg" 
                className="w-48"
              >
                <a href="mailto:contactabdullahahmed@gmail.com">
                  Begin Our Conversation
                </a>
              </Button>
              <Button 
                asChild
                variant="luxury"
                size="lg" 
                className="w-48"
              >
                <a href="/CV.pdf" download="Abdullah_Ahmed_CV.pdf">
                  Download CV
                </a>
              </Button>
            </div>
            
            <div className="flex items-center justify-center gap-8 mb-6">
              <div className="h-px bg-gradient-to-r from-transparent via-primary/60 to-transparent w-28" />
              <span className="font-display text-primary text-base tracking-widest">CONNECT</span>
              <div className="h-px bg-gradient-to-r from-transparent via-primary/60 to-transparent w-28" />
            </div>
            
            <div className="flex items-center justify-center gap-8">
              <Button
                asChild
                variant="link"
                className="tracking-wider text-base hover:scale-105 transition-transform duration-200"
              >
                <a
                  href="https://www.linkedin.com/feed/"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  LinkedIn
                </a>
              </Button>
              <Button
                asChild
                variant="link"
                className="tracking-wider text-base hover:scale-105 transition-transform duration-200"
              >
                <a
                  href="https://github.com/abdull-ah-med"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  GitHub
                </a>
              </Button>
              <Button
                asChild
                variant="link"
                className="tracking-wider text-base hover:scale-105 transition-transform duration-200"
              >
                <a
                  href="https://leetcode.com/u/abdull-ah-med/"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  LeetCode
                </a>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-16 px-6 border-t border-primary/20 bg-gradient-to-t from-card/20 to-transparent">
        <div className="max-w-6xl mx-auto">
          <div className="text-center space-y-6">
            <div className="ornamental-divider" />
            <div className="space-y-2">
              <p className="font-display text-primary text-lg">
                Abdullah Ahmed
              </p>
            </div>
            <div className="flex items-center justify-center gap-4 text-xs text-muted-foreground">
              <span>© 2025</span>
              <div className="w-1 h-1 bg-primary rounded-full" />
              <span>All rights reserved</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
