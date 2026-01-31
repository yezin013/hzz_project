"use client";

import { useState, Suspense } from "react";
import styles from "./page.module.css";
import HeroSection from "./components/HeroSection";
import BodySection from "./components/BodySection";
import MainSecondPage from "./components/MainSecondPage";
import SideDock from "./components/SideDock";

export default function Home() {
  const [searchQuery, setSearchQuery] = useState("");

  const scrollToBody = () => {
    const bodySection = document.getElementById("body-section");
    if (bodySection) {
      bodySection.scrollIntoView({ behavior: "smooth" });
    }
  };

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    scrollToBody();
  };

  return (
    <div className={styles.container}>
      <SideDock />

      {/* 1. Hero Section */}
      <div id="hero-section" className={styles.snapSection}>
        <HeroSection onSearch={handleSearch} onScrollDown={scrollToBody} />
      </div>

      {/* 2. Body Section (Tabs: Grid / Map) */}
      <div id="body-section" className={styles.snapSection}>
        <Suspense fallback={<div style={{ height: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>Loading...</div>}>
          <BodySection searchQuery={searchQuery} />
        </Suspense>
      </div>

      {/* 3. Info Section (Previously Second Page) */}
      <div id="info-section" className={`${styles.snapSection} ${styles.infoSection}`}>
        <section style={{ width: '100%', height: '100%' }}>
          <MainSecondPage />
        </section>
      </div>
    </div>
  );
}
