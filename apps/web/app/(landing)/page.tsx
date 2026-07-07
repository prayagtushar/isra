import {
  Navbar,
  Hero,
  Stats,
  Marquee,
  Features,
  Bento,
  FAQ,
  CTA,
  Footer,
} from "@/components/landing";

export default function LandingPage() {
  return (
    <>
      <Navbar />
      <Hero />
      <Stats />
      <Marquee />
      <Features />
      <Bento />
      <FAQ />
      <CTA />
      <Footer />
    </>
  );
}
