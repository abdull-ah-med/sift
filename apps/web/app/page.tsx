import { CtaBand } from "@/components/marketing/CtaBand";
import { FeatureBento } from "@/components/marketing/FeatureBento";
import { HowItWorks } from "@/components/marketing/HowItWorks";
import { MarketingHero } from "@/components/marketing/MarketingHero";
import { SiteFooter } from "@/components/marketing/SiteFooter";
import { SiteHeader } from "@/components/marketing/SiteHeader";

export default function HomePage() {
  return (
    <div className="flex min-h-[100dvh] flex-col">
      <SiteHeader />
      <main id="main" className="sift-app-main flex-1">
        <MarketingHero />
        <FeatureBento />
        <HowItWorks />
        <CtaBand />
      </main>
      <SiteFooter />
    </div>
  );
}
