"use client";

import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export default function Home() {
  const [activeSection, setActiveSection] = useState("");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      const sections = ["hero", "about", "experience", "work", "contact"];
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
    };
  }, [mobileMenuOpen]);

  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: "smooth" });
      setMobileMenuOpen(false); // Close mobile menu after navigation
      document.body.style.overflow = 'unset'; // Restore body scroll
    }
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
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-background/95 border-b border-border elegant-glow">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="font-display text-xl font-medium gradient-text">
              Abdullah Ahmed
            </div>
            
            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center space-x-8">
              {[
                { id: "hero", label: "Home" },
                { id: "about", label: "About" },
                { id: "experience", label: "Experience" },
                { id: "work", label: "Work" },
                { id: "contact", label: "Contact" },
              ].map((item) => (
                <button
                  key={item.id}
                  onClick={() => scrollToSection(item.id)}
                  className={`text-sm transition-all duration-300 hover:text-primary relative ${
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
              className={`md:hidden hamburger text-foreground ${mobileMenuOpen ? 'open' : ''}`}
              aria-label="Toggle mobile menu"
            >
              <span></span>
              <span></span>
              <span></span>
              <span></span>
            </button>
          </div>

          {/* Mobile Navigation Menu */}
          {mobileMenuOpen && (
            <div className="md:hidden mobile-menu open mt-4 pb-4 border-t border-border/50 bg-background rounded-lg mx-2">
              <div className="flex flex-col space-y-1 pt-4 px-2">
                {[
                  { id: "hero", label: "Home" },
                  { id: "about", label: "About" },
                  { id: "experience", label: "Experience" },
                  { id: "work", label: "Work" },
                  { id: "contact", label: "Contact" },
                ].map((item) => (
                  <button
                    key={item.id}
                    onClick={() => scrollToSection(item.id)}
                    className={`text-left px-4 py-3 text-base font-medium transition-all duration-300 hover:text-primary rounded-lg ${
                      activeSection === item.id ? "text-primary bg-primary/10" : "text-foreground hover:bg-muted/10"
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>
          )}
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
              Crafting sophisticated digital experiences with timeless elegance, where classical aesthetics meet modern innovation, and every detail serves a greater purpose.
            </p>
          </div>
          <div className="flex flex-col sm:flex-row gap-6 justify-center items-center">
            <Button
              onClick={() => scrollToSection("work")}
              variant="primary"
              size="lg"
              className="w-48 font-display"
            >
              Explore My Work
            </Button>
            <Button
              onClick={() => scrollToSection("contact")}
              variant="luxury"
              size="lg"
              className="w-48 font-display"
            >
              Begin Conversation
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
              About Abdullah
            </h2>
            <div className="ornamental-divider mb-12" />
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
              A craftsman dedicated to the intersection of timeless design and cutting-edge technology
            </p>
          </div>
          
          <div className="grid lg:grid-cols-3 gap-12 mb-16">
            <div className="lg:col-span-2">
              <Card className="p-10 sophisticated-card">
                <h3 className="font-display text-3xl font-medium mb-8 gradient-text">
                  Philosophy & Vision
                </h3>
                <div className="space-y-6 text-muted-foreground leading-relaxed">
                  <p className="text-lg">
                    I believe in the power of understated elegance—where every element serves a purpose, 
                    and beauty emerges from restraint rather than excess. My work reflects a commitment 
                    to timeless design principles while embracing the possibilities of modern innovation.
                  </p>
                  <p>
                    Drawing inspiration from classical aesthetics, architectural principles, and the refined 
                    sensibilities of old-world craftsmanship, I create digital experiences that transcend 
                    trends and stand the test of time.
                  </p>
                  <p>
                    Each project is approached with meticulous attention to detail, from the macro vision 
                    down to the smallest interactive element, ensuring that form and function exist in 
                    perfect harmony.
                  </p>
                </div>
              </Card>
            </div>
            
            <div className="space-y-8">
              <Card className="p-8 sophisticated-card">
                <h4 className="font-display text-xl font-medium mb-6 text-primary">Core Expertise</h4>
                <div className="space-y-4">
                  {[
                    { skill: "Frontend Architecture", years: "5+" },
                    { skill: "UI/UX Design", years: "4+" },
                    { skill: "Brand Identity", years: "3+" },
                    { skill: "Digital Strategy", years: "3+" },
                    { skill: "Creative Direction", years: "2+" },
                  ].map((item) => (
                    <div key={item.skill} className="expertise-item rounded-lg">
                      <div className="flex justify-between items-center relative z-10">
                        <span className="text-foreground font-medium">{item.skill}</span>
                        <span className="text-primary text-sm font-display">{item.years}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
              
             
            </div>
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
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
              A curated chronicle of impactful roles and transformative projects
            </p>
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
              Selected Works
            </h2>
            <div className="ornamental-divider mb-12" />
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
              A curated collection of projects that define excellence in digital craftsmanship
            </p>
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
                  <div className="w-full h-64 bg-gradient-to-br from-primary/10 via-primary/5 to-background rounded-xl mb-6 relative overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-br from-primary/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                    <div className="absolute bottom-4 right-4 text-xs text-primary font-display tracking-widest">
                      {project.year}
                    </div>
                  </div>
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
                            className="font-display text-xs"
                          >
                            <a
                              href={project.links.live}
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              Live Demo
                              <span className="ml-1">↗</span>
                            </a>
                          </Button>
                        )}
                        {project.links.github && (
                          <Button
                            asChild
                            variant="primary"
                            size="sm"
                            className="font-display text-xs"
                          >
                            <a
                              href={project.links.github}
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              GitHub
                              <span className="ml-1">↗</span>
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
          
          <div className="grid md:grid-cols-3 gap-8 mb-16">
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
            
            <Card className="p-8 sophisticated-card text-center">
              <div className="w-12 h-12 bg-primary/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <div className="w-6 h-6 bg-primary rounded-full" />
              </div>
              <h3 className="font-display text-lg font-medium mb-2 text-primary">
                Consultation
              </h3>
              <p className="text-sm text-muted-foreground">
                Strategic guidance for digital transformation and design excellence
              </p>
            </Card>
          </div>
          
          <div className="space-y-8">
            <div className="flex flex-col sm:flex-row gap-6 justify-center items-center">
              <Button 
                variant="primary"
                size="lg" 
                className="font-display w-48"
              >
                Begin Our Conversation
              </Button>
              <Button 
                variant="luxury"
                size="lg" 
                className="font-display w-48"
              >
                Download CV
              </Button>
            </div>
            
            <div className="flex items-center justify-center gap-10">
              <div className="h-px bg-gradient-to-r from-transparent via-primary/60 to-transparent w-32" />
              <span className="font-display text-primary text-base tracking-widest bg-primary/5 px-4 py-2 rounded-lg border border-primary/20">CONNECT</span>
              <div className="h-px bg-gradient-to-r from-transparent via-primary/60 to-transparent w-32" />
            </div>
            
            <div className="flex items-center justify-center gap-4">
              <Button
                asChild
                variant="link"
                className="font-display tracking-wider"
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
                className="font-display tracking-wider"
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
                className="font-display tracking-wider"
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
              <p className="text-muted-foreground text-sm">
                Crafting digital experiences with timeless elegance
              </p>
            </div>
            <div className="flex items-center justify-center gap-4 text-xs text-muted-foreground">
              <span>© 2024</span>
              <div className="w-1 h-1 bg-primary rounded-full" />
              <span>All rights reserved</span>
              <div className="w-1 h-1 bg-primary rounded-full" />
              <span>Designed & Developed with precision</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
