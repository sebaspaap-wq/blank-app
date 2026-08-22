import Hero from "@/components/home/Hero";
import Collection from "@/components/home/Collection";
import About from "@/components/home/About";
import Values from "@/components/home/Values";
import EditorialSection from "@/components/home/EditorialSection";
import Gallery from "@/components/home/Gallery";

export default function HomePage() {
  return (
    <>
      <Hero />
      <Collection />
      <About />
      <Values />
      <EditorialSection />
      <Gallery />
    </>
  );
}
