"use client";

import React, { useState, useEffect, useRef } from "react";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { initSmoothScroll, scrollTo, destroySmoothScroll } from "@/lib/smooth-scroll";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

export default function Home() {
  const [activeSection, setActiveSection] = useState("");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  // GSAP refs
  const heroRef = useRef<HTMLDivElement>(null);
  const nameRef = useRef<HTMLHeadingElement>(null);
  const subtitleRef = useRef<HTMLParagraphElement>(null);
  const descriptionRef = useRef<HTMLParagraphElement>(null);
  const buttonsRef = useRef<HTMLDivElement>(null);
  const scrollIndicatorRef = useRef<HTMLDivElement>(null);
  const aboutRef = useRef<HTMLElement>(null);
  const skillsRef = useRef<HTMLElement>(null);
  const experienceRef = useRef<HTMLElement>(null);
  const workRef = useRef<HTMLElement>(null);
  const contactRef = useRef<HTMLElement>(null);

  useEffect(() => {
    // Initialize GSAP ScrollTrigger
    gsap.registerPlugin(ScrollTrigger);
    
    // Initialize smooth scroll
    initSmoothScroll();

    // Hero section animations
    const heroTl = gsap.timeline();
    const isMobile = window.innerWidth < 768;
    const mobileOffset = isMobile ? 0.6 : 1; // Reduce animation intensity on mobile
    
    heroTl
      .fromTo(nameRef.current, 
        { y: isMobile ? 60 : 100, opacity: 0 },
        { y: 0, opacity: 1, duration: 1.2 * mobileOffset, ease: "power3.out" }
      )
      .fromTo(subtitleRef.current,
        { y: isMobile ? 30 : 50, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.8 * mobileOffset, ease: "power2.out" },
        "-=0.6"
      )
      .fromTo(descriptionRef.current,
        { y: isMobile ? 30 : 50, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.8 * mobileOffset, ease: "power2.out" },
        "-=0.4"
      )
      .fromTo(buttonsRef.current,
        { y: isMobile ? 20 : 30, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.8 * mobileOffset, ease: "power2.out" },
        "-=0.2"
      )
      .fromTo(scrollIndicatorRef.current,
        { y: isMobile ? 15 : 20, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.6 * mobileOffset, ease: "power2.out" },
        "-=0.4"
      );

    // Section reveal animations
    const sections = [aboutRef, skillsRef, experienceRef, workRef, contactRef];
    sections.forEach((sectionRef, index) => {
      if (sectionRef.current) {
        gsap.fromTo(sectionRef.current,
          { y: 60, opacity: 0 },
          {
            y: 0,
            opacity: 1,
            duration: 1,
            ease: "power2.out",
            scrollTrigger: {
              trigger: sectionRef.current,
              start: "top 85%",
              end: "bottom 15%",
              toggleActions: "play none none reverse"
            }
          }
        );
      }
    });

    // Section heading animations
    const sectionHeadings = document.querySelectorAll('h2.gradient-text');
    sectionHeadings.forEach((heading, index) => {
      gsap.fromTo(heading,
        { y: 30, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.8,
          ease: "power2.out",
          scrollTrigger: {
            trigger: heading,
            start: "top 85%",
            toggleActions: "play none none reverse"
          },
          delay: index * 0.1
        }
      );
    });

    // Skills grid animations with stagger
    const skillCards = document.querySelectorAll('#skills .sophisticated-card');
    gsap.fromTo(skillCards,
      { y: 40, opacity: 0, scale: 0.95 },
      {
        y: 0,
        opacity: 1,
        scale: 1,
        duration: 0.8,
        ease: "power2.out",
        stagger: 0.15,
        scrollTrigger: {
          trigger: '#skills',
          start: "top 80%",
          toggleActions: "play none none reverse"
        }
      }
    );

    // Experience timeline animations
    const timelineItems = document.querySelectorAll('.experience-timeline .sophisticated-card');
    timelineItems.forEach((item, index) => {
      gsap.fromTo(item,
        { x: -60, opacity: 0 },
        {
          x: 0,
          opacity: 1,
          duration: 0.8,
          ease: "power2.out",
          scrollTrigger: {
            trigger: item,
            start: "top 80%",
            toggleActions: "play none none reverse"
          },
          delay: index * 0.2
        }
      );
    });

    // Work project animations
    const projectCards = document.querySelectorAll('#work .sophisticated-card');
    projectCards.forEach((card, index) => {
      gsap.fromTo(card,
        { y: 60, opacity: 0, scale: 0.95 },
        {
          y: 0,
          opacity: 1,
          scale: 1,
          duration: 1,
          ease: "power2.out",
          scrollTrigger: {
            trigger: card,
            start: "top 80%",
            toggleActions: "play none none reverse"
          },
          delay: index * 0.3
        }
      );
    });

    // Contact section animations
    const contactCards = document.querySelectorAll('#contact .sophisticated-card');
    contactCards.forEach((card, index) => {
      gsap.fromTo(card,
        { y: 40, opacity: 0, scale: 0.95 },
        {
          y: 0,
          opacity: 1,
          scale: 1,
          duration: 0.8,
          ease: "power2.out",
          scrollTrigger: {
            trigger: card,
            start: "top 80%",
            toggleActions: "play none none reverse"
          },
          delay: index * 0.1
        }
      );
    });

    // Floating animation for scroll indicator
    gsap.to(scrollIndicatorRef.current, {
      y: isMobile ? -6 : -10,
      duration: isMobile ? 2.5 : 2,
      ease: "power2.inOut",
      repeat: -1,
      yoyo: true
    });

    // Button hover animations
    const buttons = document.querySelectorAll('button, .elegant-button');
    buttons.forEach(button => {
      button.addEventListener('mouseenter', () => {
        gsap.to(button, {
          scale: 1.05,
          duration: 0.3,
          ease: "power2.out"
        });
      });
      
      button.addEventListener('mouseleave', () => {
        gsap.to(button, {
          scale: 1,
          duration: 0.3,
          ease: "power2.out"
        });
      });
    });

    // Card hover animations
    const cards = document.querySelectorAll('.sophisticated-card');
    cards.forEach(card => {
      card.addEventListener('mouseenter', () => {
        gsap.to(card, {
          y: -5,
          scale: 1.02,
          duration: 0.4,
          ease: "power2.out"
        });
      });
      
      card.addEventListener('mouseleave', () => {
        gsap.to(card, {
          y: 0,
          scale: 1,
          duration: 0.4,
          ease: "power2.out"
        });
      });
    });

    // Navigation link hover animations
    const navLinks = document.querySelectorAll('nav button');
    navLinks.forEach(link => {
      link.addEventListener('mouseenter', () => {
        gsap.to(link, {
          y: -2,
          duration: 0.2,
          ease: "power2.out"
        });
      });
      
      link.addEventListener('mouseleave', () => {
        gsap.to(link, {
          y: 0,
          duration: 0.2,
          ease: "power2.out"
        });
      });
    });

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

    // Handle window resize for mobile optimization
    const handleResize = () => {
      const newIsMobile = window.innerWidth < 768;
      if (newIsMobile !== isMobile) {
        // Refresh ScrollTrigger on orientation change
        ScrollTrigger.refresh();
      }
    };

    window.addEventListener("scroll", handleScroll);
    window.addEventListener("resize", handleResize);
    document.addEventListener("mousedown", handleClickOutside);
    
    return () => {
      window.removeEventListener("scroll", handleScroll);
      window.removeEventListener("resize", handleResize);
      document.removeEventListener("mousedown", handleClickOutside);
      destroySmoothScroll();
      
      // Clean up GSAP ScrollTrigger and animations
      ScrollTrigger.getAll().forEach(trigger => trigger.kill());
      
      // Remove event listeners
      const buttons = document.querySelectorAll('button, .elegant-button');
      const cards = document.querySelectorAll('.sophisticated-card');
      const navLinks = document.querySelectorAll('nav button');
      
      buttons.forEach(button => {
        button.removeEventListener('mouseenter', () => {});
        button.removeEventListener('mouseleave', () => {});
      });
      
      cards.forEach(card => {
        card.removeEventListener('mouseenter', () => {});
        card.removeEventListener('mouseleave', () => {});
      });
      
      navLinks.forEach(link => {
        link.removeEventListener('mouseenter', () => {});
        link.removeEventListener('mouseleave', () => {});
      });
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
      <section ref={heroRef} id="hero" className="min-h-screen flex items-center justify-center px-4 sm:px-6 relative overflow-hidden">
        {/* Subtle Background Elements */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-primary/3 pointer-events-none" />
        <div className="absolute inset-0 parallax-bg pointer-events-none" />
        
        {/* Enhanced Content */}
        <div className="max-w-6xl mx-auto text-center relative z-10 px-4 sm:px-0">
          <div className="mb-12 sm:mb-16 md:mb-20">
            {/* Elegant Name with Subtle Animation */}
            <div className="mb-6 sm:mb-8">
              <h1 ref={nameRef} className="font-display text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-light leading-tight mb-4 sm:mb-6 text-balance gradient-text text-shadow-elegant elegant-reveal px-2">
                Abdullah Ahmed
              </h1>
            </div>
            
            {/* Sophisticated Subtitle */}
            <div className="mb-6 sm:mb-8 elegant-fade-in">
              <p ref={subtitleRef} className="text-base sm:text-lg md:text-xl text-muted-foreground font-light tracking-wide px-2">
                Computer Science Student & Software Developer
              </p>
            </div>
            
            {/* Enhanced Description */}
            <div className="elegant-fade-in-delayed">
              <p ref={descriptionRef} className="text-sm sm:text-base md:text-lg text-muted-foreground font-light leading-relaxed max-w-4xl sm:max-w-5xl mx-auto text-balance mb-6 sm:mb-8 px-2">
                Building innovative software solutions with modern technologies, where clean code meets intelligent design and every project solves real-world problems.
              </p>
            </div>
            
            {/* Elegant Divider */}
            <div className="flex items-center justify-center my-8 sm:my-12 md:my-16 elegant-fade-in-delayed px-4">
              <div className="h-px bg-gradient-to-r from-transparent via-primary/60 to-transparent w-32 sm:w-48 md:w-64"></div>
              <div className="mx-4 sm:mx-6 md:mx-8 w-1.5 h-1.5 bg-primary/70 rounded-full subtle-pulse"></div>
              <div className="h-px bg-gradient-to-r from-transparent via-primary/60 to-transparent w-32 sm:w-48 md:w-64"></div>
            </div>
          </div>
          
          {/* Refined Buttons */}
          <div ref={buttonsRef} className="flex flex-col sm:flex-row gap-4 sm:gap-6 justify-center items-center elegant-slide-up px-4">
            <Button
              asChild
              variant="primary"
              size="lg"
              className="w-full sm:w-48"
            >
              <a href="#work" onClick={(e) => { e.preventDefault(); scrollToSection("work"); }}>
                Explore My Work
              </a>
            </Button>
            <Button
              asChild
              variant="luxury"
              size="lg"
              className="w-full sm:w-48"
            >
              <a href="mailto:contactabdullahahmed@gmail.com">
                Begin Conversation
              </a>
            </Button>
          </div>
          
          {/* Elegant Scroll Indicator */}
          <div ref={scrollIndicatorRef} className="absolute bottom-8 sm:bottom-12 md:bottom-16 left-1/2 transform -translate-x-1/2 elegant-fade-in-final">
            <div className="flex flex-col items-center text-muted-foreground hover:text-primary transition-all duration-500 cursor-pointer group"
                 onClick={() => scrollToSection("about")}>
              <span className="text-xs mb-2 sm:mb-4 tracking-[0.2em] font-light uppercase">Discover More</span>
              <div className="w-px h-12 sm:h-16 bg-gradient-to-b from-muted-foreground/50 to-transparent group-hover:from-primary/70 transition-all duration-500"></div>
              <svg className="w-3 h-3 mt-2 sm:mt-3 animate-bounce opacity-60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7" />
              </svg>
            </div>
          </div>
        </div>
      </section>

      {/* About Section */}
      <section ref={aboutRef} id="about" className="py-32 px-6 relative">
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
      <section ref={skillsRef} id="skills" className="pt-24 pb-32 px-6 relative">
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
      <section ref={experienceRef} id="experience" className="py-32 px-6 bg-gradient-to-b from-background via-card/10 to-background">
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
      <section ref={workRef} id="work" className="py-32 px-6 relative">
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
      <section ref={contactRef} id="contact" className="py-32 px-6 relative overflow-hidden">
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
