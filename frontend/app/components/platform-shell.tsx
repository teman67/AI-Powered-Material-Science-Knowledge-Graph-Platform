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
      <header className="top-shell">
        <div className="top-shell-left">
          <div className="brand-pill">
            <span className="brand-pill-dot" />
            Material Science Knowledge Platform
          </div>
          <h1 className="shell-title">{title}</h1>
          <p className="subtitle">{subtitle}</p>
        </div>
        <div className="top-shell-right">
          <nav className="nav-row" aria-label="Primary">
            {links.map((link) => (
              <Link key={link.href} href={link.href} className={pathname === link.href ? "active" : ""}>
                {link.label}
              </Link>
            ))}
          </nav>
          <AuthPanel />
        </div>
      </header>

      <div className="content-panel full-width">{children}</div>
    </main>
  );
}
