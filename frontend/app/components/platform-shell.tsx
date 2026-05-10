"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { AuthPanel } from "./auth-panel";

const links = [
  { href: "/", label: "Dashboard" },
  { href: "/chat", label: "Chat" },
  { href: "/graph", label: "Graph View" },
  { href: "/rdf", label: "RDF Viewer" },
];

export function PlatformShell({ title, subtitle, children }: { title: string; subtitle: string; children: ReactNode }) {
  const pathname = usePathname();

  return (
    <main className="platform-page fade-in">
      <section className="top-shell">
        <div>
          <p className="eyebrow">Productization Phase 4</p>
          <h1>{title}</h1>
          <p className="subtitle">{subtitle}</p>
        </div>
        <nav className="nav-row" aria-label="Primary">
          {links.map((link) => (
            <Link key={link.href} href={link.href} className={pathname === link.href ? "active" : ""}>
              {link.label}
            </Link>
          ))}
        </nav>
      </section>

      <section className="content-grid">
        <div className="content-panel">{children}</div>
        <AuthPanel />
      </section>
    </main>
  );
}
